"""
Token Service

Background service that uses Undetected ChromeDriver to capture Google Shopping
callback URLs and create new CallbackSession records.

This is the ONLY component that uses browser automation.
Everything else uses fast requests-only scraping with curl_cffi.
"""

import logging
import time
import zipfile
import os
import json
from typing import Optional, Dict
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from callback_session import CallbackSession
from session_db import get_db
from proxy_manager import ProxyPool, Proxy


logger = logging.getLogger(__name__)


class TokenService:
    """
    Service for capturing callback URLs using Undetected ChromeDriver.
    
    This runs as a background worker and periodically creates new
    callback sessions for the scraper to use.
    """
    
    def __init__(self, proxy_pool: Optional[ProxyPool] = None):
        """
        Initialize token service.
        
        Args:
            proxy_pool: Optional proxy pool for rotating proxies
        """
        self.db = get_db()
        self.proxy_pool = proxy_pool
        self.capture_count = 0
        self.failure_count = 0
    
    def _create_proxy_extension(self, proxy: Proxy) -> str:
        """
        Create Chrome extension for proxy authentication.
        
        Args:
            proxy: Proxy configuration
            
        Returns:
            Path to proxy extension zip file
        """
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Proxy Auth",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """
        
        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                  singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                  },
                  bypassList: ["localhost"]
                }
              };
        
        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
        
        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }
        
        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (proxy.host, proxy.port, proxy.username or "", proxy.password or "")
        
        plugin_file = 'proxy_auth_plugin.zip'
        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        
        return plugin_file
    
    def capture_callback_url(
        self,
        region: str = "US",
        test_query: str = "laptop"
    ) -> Optional[str]:
        """
        Capture a callback URL using Undetected ChromeDriver.
        
        This uses the PROVEN method from capture_xhr_requests.py:
        1. Launch UC with Oxylabs proxy
        2. Navigate to Google Shopping
        3. Search and scroll to trigger product loads
        4. Capture ALL request types for /async/callback URLs via CDP
        
        Args:
            region: Region identifier for this session
            test_query: Search query to use for capturing
            
        Returns:
            Captured callback URL, or None if failed
        """
        callback_url = None
        proxy = None
        proxy_extension_path = None
        driver = None
        
        try:
            # Get proxy if available
            if self.proxy_pool:
                proxy = self.proxy_pool.get_next_proxy()
                if proxy:
                    proxy.mark_used()
                    logger.info(f"Using proxy: {proxy.host}:{proxy.port}")
            
            # Setup Chrome options
            options = uc.ChromeOptions()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--lang=en-US')
            options.add_experimental_option('prefs', {'intl.accept_languages': 'en-US,en'})
            options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            
            # Add proxy extension if using proxy
            if proxy:
                proxy_extension_path = self._create_proxy_extension(proxy)
                options.add_extension(proxy_extension_path)
            
            logger.info("🚀 Launching Chrome...")
            
            # Launch UC
            driver = uc.Chrome(
                options=options,
                use_subprocess=True,
                version_main=None
            )
            
            # Navigate to Google Shopping with US locale
            logger.info("📍 Loading shopping.google.com with US locale...")
            driver.get("https://shopping.google.com/?hl=en&gl=us")
            time.sleep(3)
            
            # Search for test query
            logger.info(f"🔍 Searching for '{test_query}'...")
            search_box = driver.find_element(By.CSS_SELECTOR, "textarea[name='q']")
            search_box.send_keys(test_query)
            search_box.submit()
            
            time.sleep(5)
            
            # Scroll to trigger product loads (CRITICAL!)
            logger.info("🔥 SCROLLING to trigger callbacks...")
            for i in range(1, 6):
                driver.execute_script(f"window.scrollTo(0, {i * 800});")
                time.sleep(3)  # Wait longer per scroll to ensure callbacks fire
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            logger.info("⏳ Waiting 15 seconds for ALL callbacks...")
            time.sleep(15)  # Wait LONGER to ensure callback URLs are captured
            
            # Analyze performance logs for callback URLs
            logger.info("🔍 Analyzing network requests...")
            logs = driver.get_log('performance')
            logger.info(f"📊 Total log entries: {len(logs)}")
            
            # Parse logs for callback URLs
            callback_found_count = 0
            for entry in logs:
                try:
                    message = json.loads(entry['message'])['message']
                    
                    if message['method'] == 'Network.requestWillBeSent':
                        request = message['params']['request']
                        url = request['url']
                        
                        # Debug: Log all google.com async URLs
                        if 'google.com' in url and 'async' in url:
                            logger.info(f"   Found async URL: {url[:120]}...")
                            callback_found_count += 1
                        
                        # CRITICAL: Capture ALL types for /async/callback URLs
                        if '/async/callback' in url and 'google.com' in url:
                            callback_url = url
                            logger.info(f"🎯 CAPTURED CALLBACK: {url[:100]}...")
                            break  # Take first one found
                            
                except Exception as e:
                    pass  # Skip malformed entries
            
            logger.info(f"   Total async URLs found: {callback_found_count}")
            
            if callback_url:
                self.capture_count += 1
                logger.info(f"✅ Successfully captured callback URL (total: {self.capture_count})")
                
                # Report proxy success
                if self.proxy_pool and proxy:
                    self.proxy_pool.report_success(proxy)
                
                return callback_url
            else:
                logger.warning("❌ No callback URL captured")
                self.failure_count += 1
                
                # Report proxy failure
                if self.proxy_pool and proxy:
                    self.proxy_pool.report_failure(proxy)
                
                return None
        
        except Exception as e:
            logger.error(f"❌ Error capturing callback URL: {e}")
            self.failure_count += 1
            
            # Report proxy failure
            if self.proxy_pool and proxy:
                self.proxy_pool.report_failure(proxy)
            
            return None
        
        finally:
            # Cleanup
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
            if proxy_extension_path and os.path.exists(proxy_extension_path):
                try:
                    os.remove(proxy_extension_path)
                except:
                    pass
    
    def create_session(
        self,
        region: str = "US",
        test_query: str = "laptop"
    ) -> Optional[CallbackSession]:
        """
        Create a new callback session.
        
        This captures a callback URL and stores it in the database.
        
        Args:
            region: Region for this session
            test_query: Query to use for capturing
            
        Returns:
            Created CallbackSession, or None if failed
        """
        logger.info(f"🔄 Creating new session for region={region}")
        
        # Capture callback URL
        callback_url = self.capture_callback_url(region=region, test_query=test_query)
        
        if not callback_url:
            return None
        
        # Determine which proxy bucket was used
        proxy_bucket = "no_proxy"
        if self.proxy_pool:
            proxy = self.proxy_pool.get_next_proxy()
            if proxy:
                proxy_bucket = f"proxy_{proxy.host}_{proxy.port}"
        
        # Create session object
        session = CallbackSession(
            url=callback_url,
            region=region,
            proxy_bucket=proxy_bucket
        )
        
        # Store in database
        session = self.db.create_session(session)
        
        logger.info(f"✅ Created session {session.id} for region={region}")
        
        return session
    
    def refresh_region(
        self,
        region: str,
        target_count: int = 3
    ) -> int:
        """
        Refresh sessions for a specific region.
        
        Creates new sessions until target_count healthy sessions exist.
        
        Args:
            region: Region to refresh
            target_count: Target number of healthy sessions
            
        Returns:
            Number of sessions created
        """
        logger.info(f"🔄 Refreshing region={region}, target={target_count}")
        
        # Check current healthy count
        current_sessions = self.db.get_valid_sessions(region=region)
        healthy_count = len([s for s in current_sessions if s.is_healthy()])
        
        logger.info(f"Current healthy sessions for {region}: {healthy_count}")
        
        # Calculate how many to create
        to_create = max(0, target_count - healthy_count)
        
        if to_create == 0:
            logger.info(f"Region {region} already has enough sessions")
            return 0
        
        # Create sessions
        created = 0
        for i in range(to_create):
            logger.info(f"Creating session {i+1}/{to_create} for {region}")
            
            session = self.create_session(region=region)
            
            if session:
                created += 1
            else:
                logger.warning(f"Failed to create session {i+1}/{to_create}")
                # Wait a bit before retry
                time.sleep(5)
        
        logger.info(f"✅ Created {created}/{to_create} sessions for {region}")
        
        return created
    
    def refresh_all_regions(
        self,
        regions: Optional[list] = None,
        target_per_region: int = 3
    ) -> Dict[str, int]:
        """
        Refresh sessions for all regions.
        
        Args:
            regions: List of regions to refresh (default: ["US"])
            target_per_region: Target healthy sessions per region
            
        Returns:
            Dictionary mapping region to number of sessions created
        """
        if regions is None:
            regions = ["US"]
        
        logger.info(f"🔄 Refreshing all regions: {regions}")
        
        results = {}
        for region in regions:
            created = self.refresh_region(region=region, target_count=target_per_region)
            results[region] = created
            
            # Small delay between regions
            if region != regions[-1]:
                time.sleep(2)
        
        total_created = sum(results.values())
        logger.info(f"✅ Refresh complete: {total_created} total sessions created")
        
        return results
    
    def run_forever(
        self,
        refresh_interval_minutes: int = 30,
        regions: Optional[list] = None
    ):
        """
        Run token service continuously.
        
        This will refresh sessions every refresh_interval_minutes.
        
        Args:
            refresh_interval_minutes: How often to refresh
            regions: List of regions to maintain
        """
        if regions is None:
            regions = ["US"]
        
        logger.info(f"🚀 TokenService starting...")
        logger.info(f"   Regions: {regions}")
        logger.info(f"   Refresh interval: {refresh_interval_minutes} minutes")
        
        # Initial refresh
        self.refresh_all_regions(regions=regions)
        
        # Continuous loop
        while True:
            logger.info(f"💤 Sleeping for {refresh_interval_minutes} minutes...")
            time.sleep(refresh_interval_minutes * 60)
            
            logger.info(f"⏰ Refresh interval reached, refreshing sessions...")
            self.refresh_all_regions(regions=regions)
    
    def get_stats(self) -> dict:
        """Get token service statistics."""
        return {
            'captures_successful': self.capture_count,
            'captures_failed': self.failure_count,
            'success_rate': (self.capture_count / (self.capture_count + self.failure_count) * 100) if (self.capture_count + self.failure_count) > 0 else 0
        }


# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create service (with or without proxy pool)
    service = TokenService()
    
    # Test single capture
    logger.info("Testing single callback capture...")
    url = service.capture_callback_url(region="US", test_query="laptop")
    if url:
        logger.info(f"✅ SUCCESS! Captured: {url[:100]}...")
    else:
        logger.error("❌ FAILED to capture callback URL")
