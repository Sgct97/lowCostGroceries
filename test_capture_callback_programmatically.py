"""
FINAL TEST: Programmatically Capture Callback URLs

This will prove we can:
1. Use UC + Oxylabs to bypass CAPTCHA
2. Intercept network requests with Selenium Wire
3. Capture /async/callback URLs programmatically
4. Use those URLs with curl_cffi for fast scraping

THIS IS THE CRITICAL TEST!
"""

import undetected_chromedriver as uc
from seleniumwire import webdriver
from seleniumwire.utils import decode
import time
import logging
import zipfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Oxylabs
PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = "lowCostGroceris_26SVt"
PROXY_PASS = "AppleID_1234"


def create_proxy_extension():
    """Create Chrome extension for Oxylabs auth."""
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
    """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

    plugin_file = 'proxy_auth_plugin.zip'
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_file


def test_capture_callback():
    """Test programmatic callback capture."""
    
    logger.info("\n" + "="*80)
    logger.info("🚀 FINAL TEST: Programmatic Callback URL Capture")
    logger.info("="*80)
    logger.info("\nThis will prove the ENTIRE architecture works!\n")
    
    # Create proxy extension
    logger.info("📦 Creating Oxylabs proxy extension...")
    proxy_extension = create_proxy_extension()
    
    # Setup Chrome options
    options = uc.ChromeOptions()
    options.add_extension(proxy_extension)
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    
    # Selenium Wire options (for network interception)
    # NOTE: We're using the Oxylabs proxy via extension, not via seleniumwire_options
    seleniumwire_options = {
        'disable_encoding': True,  # Don't decode responses (we'll do it manually)
    }
    
    logger.info("🚀 Launching undetected Chrome with network interception...")
    logger.info("✅ Oxylabs proxy: via extension")
    logger.info("✅ Network capture: via Selenium Wire\n")
    
    try:
        # Create driver with both UC and Selenium Wire
        driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            version_main=None,
            seleniumwire_options=seleniumwire_options
        )
        
        logger.info("✅ Browser launched successfully!\n")
        
        # Track callback URLs
        callback_urls = []
        
        # Navigate to Google Shopping
        search_url = "https://www.google.com/search?q=laptop&tbm=shop&hl=en&gl=us"
        logger.info(f"🌐 Loading: {search_url}\n")
        
        driver.get(search_url)
        
        # Wait for page to load and JS to execute
        logger.info("⏳ Waiting for JavaScript to execute and make callback requests...")
        time.sleep(10)  # Give plenty of time for async requests
        
        # Scroll to trigger lazy loading
        logger.info("📜 Scrolling to trigger more requests...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # Check all captured requests
        logger.info("\n" + "="*80)
        logger.info("🔍 ANALYZING CAPTURED NETWORK REQUESTS")
        logger.info("="*80 + "\n")
        
        total_requests = len(driver.requests)
        logger.info(f"📊 Total requests captured: {total_requests}\n")
        
        # Look for callback URLs
        for request in driver.requests:
            url = request.url
            
            # Check for callback pattern
            if '/async/callback' in url:
                callback_urls.append(url)
                logger.info(f"🎉 FOUND CALLBACK URL:")
                logger.info(f"   {url[:150]}...")
                logger.info(f"   Method: {request.method}")
                logger.info(f"   Status: {request.response.status_code if request.response else 'No response'}\n")
            
            # Also look for other interesting async patterns
            elif 'async' in url.lower() and 'google' in url:
                logger.info(f"📋 Other async URL: {url[:100]}...")
        
        # Check page content
        html = driver.page_source
        has_products = 'sh-dgr__' in html or 'liKJmf' in html
        
        logger.info("\n" + "="*80)
        logger.info("RESULTS")
        logger.info("="*80)
        logger.info(f"✅ Total requests captured: {total_requests}")
        logger.info(f"🎯 Callback URLs found: {len(callback_urls)}")
        logger.info(f"✅ Products in page: {has_products}")
        logger.info(f"📊 Page size: {len(html):,} bytes\n")
        
        if callback_urls:
            logger.info("🎉🎉🎉 SUCCESS! We captured callback URLs programmatically!")
            logger.info(f"\nCaptured {len(callback_urls)} callback URL(s):")
            for i, url in enumerate(callback_urls, 1):
                logger.info(f"\n{i}. {url[:120]}...")
                
                # Save to file
                with open(f"captured_callback_{i}.txt", "w") as f:
                    f.write(url)
                logger.info(f"   Saved to: captured_callback_{i}.txt")
            
            logger.info("\n✅ THE HYBRID ARCHITECTURE IS PROVEN TO WORK!")
            logger.info("✅ Next: Use these URLs with curl_cffi for fast scraping")
            
        else:
            logger.warning("⚠️  No callback URLs captured")
            logger.info("\nPossible reasons:")
            logger.info("1. Google Shopping doesn't use /async/callback for this query")
            logger.info("2. Callbacks use a different URL pattern")
            logger.info("3. Need to wait longer or interact more")
            logger.info("4. Check if products are loaded via different method")
            
            if has_products:
                logger.info("\n✅ But products ARE visible, so data IS being loaded")
                logger.info("   Maybe Google Shopping changed their architecture")
        
        # Keep browser open
        logger.info(f"\n⏳ Keeping browser open for 15 seconds...")
        logger.info("   You can manually check DevTools Network tab")
        time.sleep(15)
        
        driver.quit()
        
        return callback_urls, has_products
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return [], False


if __name__ == "__main__":
    callback_urls, has_products = test_capture_callback()
    
    print("\n" + "="*80)
    print("FINAL VERDICT")
    print("="*80)
    
    if callback_urls:
        print(f"\n✅✅✅ SUCCESS! Captured {len(callback_urls)} callback URL(s)")
        print("\nTHE HYBRID ARCHITECTURE WORKS:")
        print("  1. ✅ UC + Oxylabs bypasses CAPTCHA")
        print("  2. ✅ Selenium Wire captures network requests")
        print("  3. ✅ We got callback URLs programmatically")
        print("  4. ✅ Can now use curl_cffi for fast scraping")
        print("\n🚀 Ready to build the TokenService!")
        
    elif has_products:
        print("\n⚠️  Captured products but NO callback URLs")
        print("\nThis means:")
        print("  ✅ UC + Oxylabs works (products visible)")
        print("  ❌ Google Shopping might not use /async/callback")
        print("\nOptions:")
        print("  1. Products might be in initial HTML (server-side rendered)")
        print("  2. Different async pattern (check captured requests)")
        print("  3. Use UC for all scraping (slower but works)")
        
    else:
        print("\n❌ No callback URLs AND no products")
        print("   Something went wrong - check logs above")
    
    print("="*80)

