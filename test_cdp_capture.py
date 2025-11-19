"""
Capture Callback URLs using Chrome DevTools Protocol (CDP)

CDP is built into Chrome/Selenium and lets us intercept network requests
without needing additional libraries like selenium-wire.
"""

import undetected_chromedriver as uc
import time
import logging
import zipfile
import json

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


def test_cdp_capture():
    """Test callback capture using CDP."""
    
    logger.info("\n" + "="*80)
    logger.info("🚀 TESTING: Network Capture with Chrome DevTools Protocol")
    logger.info("="*80 + "\n")
    
    # Create proxy extension
    logger.info("📦 Creating Oxylabs proxy extension...")
    proxy_extension = create_proxy_extension()
    
    # Setup Chrome
    options = uc.ChromeOptions()
    options.add_extension(proxy_extension)
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Enable performance logging (captures network requests)
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    logger.info("🚀 Launching Chrome with CDP network logging...\n")
    
    driver = uc.Chrome(
        options=options,
        use_subprocess=True,
        version_main=None
    )
    
    logger.info("✅ Browser launched!\n")
    
    # Navigate (USER PROVIDED URL WITH ACTUAL PRODUCTS!)
    search_url = "https://www.google.com/search?q=milk+nearby&udm=28&shopmd=1&shoprs=CAEYAyoEbWlsazIMCAMSBk5lYXJieRgCWJjjH2AC&sa=X&ved=2ahUKEwiZhoXY4P6QAxW9RzABHZhrC18Q268JKAB6BAgYEAU&biw=1512&bih=788&dpr=2"
    logger.info(f"🌐 Loading user-provided URL with actual products:")
    logger.info(f"   {search_url[:100]}...\n")
    
    driver.get(search_url)
    
    # Wait LONGER for page (shopping.google.com is heavy JavaScript)
    logger.info("⏳ Waiting 20 seconds for JavaScript to fully load products...")
    time.sleep(20)
    
    # Scroll
    logger.info("📜 Scrolling...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    # Get performance logs (network requests)
    logger.info("\n" + "="*80)
    logger.info("🔍 ANALYZING NETWORK LOGS")
    logger.info("="*80 + "\n")
    
    logs = driver.get_log('performance')
    logger.info(f"📊 Total performance log entries: {len(logs)}\n")
    
    callback_urls = []
    all_requests = []
    
    for entry in logs:
        try:
            message = json.loads(entry['message'])['message']
            
            # Look for network request events
            if message['method'] == 'Network.requestWillBeSent':
                request = message['params']['request']
                url = request['url']
                all_requests.append(url)
                
                # Check for callback
                if '/async/callback' in url:
                    callback_urls.append(url)
                    logger.info(f"🎉 FOUND CALLBACK URL:")
                    logger.info(f"   {url[:150]}...\n")
                    
        except:
            pass
    
    # Check page
    html = driver.page_source
    has_products = 'sh-dgr__' in html or 'liKJmf' in html
    
    logger.info("\n" + "="*80)
    logger.info("RESULTS")
    logger.info("="*80)
    logger.info(f"✅ Total requests: {len(all_requests)}")
    logger.info(f"🎯 Callback URLs: {len(callback_urls)}")
    logger.info(f"✅ Products visible: {has_products}")
    logger.info(f"📊 Page size: {len(html):,} bytes\n")
    
    if callback_urls:
        logger.info("🎉🎉🎉 SUCCESS! Captured callback URLs with CDP!")
        for i, url in enumerate(callback_urls, 1):
            logger.info(f"\n{i}. {url[:120]}...")
            with open(f"cdp_callback_{i}.txt", "w") as f:
                f.write(url)
    else:
        logger.warning("⚠️  No /async/callback URLs found")
        
        # Show some sample requests
        logger.info("\nSample requests captured:")
        google_requests = [r for r in all_requests if 'google' in r][:10]
        for r in google_requests:
            logger.info(f"  - {r[:100]}...")
    
    # Keep open
    logger.info(f"\n⏳ Keeping browser open for 15 seconds...")
    time.sleep(15)
    
    driver.quit()
    
    return callback_urls, has_products


if __name__ == "__main__":
    callback_urls, has_products = test_cdp_capture()
    
    print("\n" + "="*80)
    print("FINAL VERDICT")
    print("="*80)
    
    if callback_urls:
        print(f"\n✅✅✅ WE DID IT! Captured {len(callback_urls)} callback URL(s)!")
        print("\n🎉 THE HYBRID ARCHITECTURE IS PROVEN!")
        print("   1. ✅ UC + Oxylabs bypasses CAPTCHA")
        print("   2. ✅ CDP captures network requests")
        print("   3. ✅ We got callback URLs programmatically")
        print("   4. ✅ Ready to use curl_cffi for fast scraping")
        
    elif has_products:
        print("\n⚠️  Products visible but no /async/callback found")
        print("\n   Possible explanations:")
        print("   1. Google Shopping changed architecture")
        print("   2. Products are server-side rendered now")
        print("   3. Different callback pattern")
        print("\n   Next: Check the sample requests logged above")
        
    else:
        print("\n❌ No products and no callbacks - check logs")
    
    print("="*80)

