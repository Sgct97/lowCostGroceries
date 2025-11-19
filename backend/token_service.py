"""
Token Service

Background service that uses Playwright to capture Google Shopping
callback URLs and create new CallbackSession records.

This is the ONLY component that uses browser automation.
Everything else uses fast requests-only scraping.
"""

import logging
import time
import zipfile
import os
from typing import Optional, Dict
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from callback_session import CallbackSession
from session_db import get_db
from proxy_manager import ProxyPool


logger = logging.getLogger(__name__)


class TokenService:
    """
    Service for capturing callback URLs using Playwright.
    
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
    
    def capture_callback_url(
        self,
        region: str = "US",
        test_query: str = "laptop"
    ) -> Optional[str]:
        """
        Capture a callback URL using Playwright.
        
        Args:
            region: Region identifier for this session
            test_query: Search query to use for capturing
            
        Returns:
            Captured callback URL, or None if failed
        """
        callback_url = None
        proxy_info = None
        
        # Get proxy if available
        if self.proxy_pool:
            proxy = self.proxy_pool.get_next_proxy()
            if proxy:
                proxy_info = {
                    "server": proxy.url,
                    "username": proxy.username,
                    "password": proxy.password
                }
        
        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(
                    headless=True,
                    proxy=proxy_info if proxy_info else None
                )
                
                # Create context with realistic browser profile
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                    java_script_enabled=True
                )
                
                page = context.new_page()
                
                # Apply stealth mode to avoid detection
                stealth.apply_stealth_sync(page)
                logger.info("✅ Stealth mode applied to page")
                
                # Capture callback URL from network
                def handle_response(response: Response):
                    nonlocal callback_url
                    if '/async/callback' in response.url:
                        callback_url = response.url
                        logger.info(f"✅ Captured callback URL: {callback_url[:80]}...")
                
                page.on("response", handle_response)
                
                # Navigate to Google Shopping search
                search_url = f"https://www.google.com/search?udm=28&q={test_query}&hl=en&gl=us"
                logger.info(f"Loading: {search_url}")
                
                page.goto(search_url, wait_until="networkidle", timeout=30000)
                
                # Wait a bit for async requests
                page.wait_for_timeout(3000)
                
                # Close browser
                context.close()
                browser.close()
            
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
                proxy_bucket = proxy.label or f"proxy_{proxy.host}_{proxy.port}"
        
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
            regions: List of regions to refresh (default: ["US-West", "US-East"])
            target_per_region: Target healthy sessions per region
            
        Returns:
            Dictionary mapping region to number of sessions created
        """
        if regions is None:
            regions = ["US-West", "US-East"]
        
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
            regions = ["US-West", "US-East"]
        
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
    
    # Create service
    service = TokenService()
    
    # Run forever (or use refresh_all_regions for one-time refresh)
    service.run_forever(refresh_interval_minutes=30, regions=["US-West", "US-East"])

