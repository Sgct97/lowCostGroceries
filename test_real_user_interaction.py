"""
REAL USER SIMULATION: Type in Search Box on shopping.google.com

This mimics a real human:
1. Go to shopping.google.com homepage (NO CAPTCHA)
2. Find search box
3. Type query
4. Click search
5. Wait for products
6. Capture callback URLs

This should work because we're acting like a real user!
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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


def test_real_user_interaction():
    """Test by acting like a real user."""
    
    logger.info("\n" + "="*80)
    logger.info("🚀 REAL USER SIMULATION: Type in Search Box")
    logger.info("="*80)
    logger.info("\nThis will:")
    logger.info("1. Go to shopping.google.com (no CAPTCHA)")
    logger.info("2. Find and type in search box")
    logger.info("3. Click search")
    logger.info("4. Wait for products")
    logger.info("5. Capture callback URLs\n")
    
    # Create proxy extension
    logger.info("📦 Creating Oxylabs proxy extension...")
    proxy_extension = create_proxy_extension()
    
    # Setup Chrome
    options = uc.ChromeOptions()
    options.add_extension(proxy_extension)
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Enable CDP logging
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    logger.info("🚀 Launching Chrome...\n")
    
    driver = uc.Chrome(
        options=options,
        use_subprocess=True,
        version_main=None
    )
    
    logger.info("✅ Browser launched!\n")
    
    try:
        # Step 1: Go to shopping.google.com homepage
        logger.info("Step 1: Loading shopping.google.com homepage...")
        driver.get("https://shopping.google.com")
        time.sleep(5)
        
        logger.info("✅ Homepage loaded (should have NO CAPTCHA)\n")
        
        # Check for CAPTCHA
        html = driver.page_source
        if 'captcha' in html.lower() or 'recaptcha' in html.lower():
            logger.error("❌ CAPTCHA detected on homepage! Stopping.")
            driver.quit()
            return [], False
        
        # Step 2: Find search box (try multiple selectors)
        logger.info("Step 2: Finding search box...")
        
        search_box = None
        selectors_to_try = [
            "input[name='q']",
            "input[type='search']",
            "input[aria-label*='Search']",
            "textarea[name='q']",
            "#APjFqb",  # Common Google search box ID
            "input.gLFyf",  # Common Google search class
        ]
        
        for selector in selectors_to_try:
            try:
                search_box = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                logger.info(f"✅ Found search box with: {selector}\n")
                break
            except:
                continue
        
        if not search_box:
            logger.error("❌ Could not find search box!")
            logger.info("Saving page source for inspection...")
            with open("homepage_no_searchbox.html", "w") as f:
                f.write(driver.page_source)
            driver.quit()
            return [], False
        
        # Step 3: Type query like a human
        logger.info("Step 3: Typing 'laptop' into search box...")
        query = "laptop"
        for char in query:
            search_box.send_keys(char)
            time.sleep(0.1 + (0.05 * (len(char) % 3)))  # Human-like typing speed
        
        logger.info("✅ Typed query\n")
        
        # Step 4: Press Enter or click search button
        logger.info("Step 4: Submitting search (pressing Enter)...")
        search_box.send_keys(Keys.RETURN)
        
        # Step 5: Wait for results to load
        logger.info("⏳ Waiting 20 seconds for products to load...")
        time.sleep(20)
        
        logger.info("✅ Products should be loaded now\n")
        
        # Scroll like a real user
        logger.info("Step 5: Scrolling to trigger more content...")
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 1500);")
        time.sleep(3)
        
        # Step 6: Analyze network logs
        logger.info("\n" + "="*80)
        logger.info("🔍 ANALYZING NETWORK REQUESTS")
        logger.info("="*80 + "\n")
        
        logs = driver.get_log('performance')
        logger.info(f"📊 Total log entries: {len(logs)}\n")
        
        callback_urls = []
        async_urls = []
        all_requests = []
        
        for entry in logs:
            try:
                message = json.loads(entry['message'])['message']
                
                if message['method'] == 'Network.requestWillBeSent':
                    request = message['params']['request']
                    url = request['url']
                    all_requests.append(url)
                    
                    # Check for callback
                    if '/async/callback' in url:
                        callback_urls.append(url)
                        logger.info(f"🎉 FOUND CALLBACK URL:")
                        logger.info(f"   {url[:150]}...\n")
                    
                    # Check for other async patterns
                    elif 'async' in url.lower() and 'google' in url:
                        async_urls.append(url)
                        
            except:
                pass
        
        # Check page state
        current_url = driver.current_url
        html = driver.page_source
        has_captcha = 'captcha' in html.lower() or 'recaptcha' in html.lower()
        has_products = any(x in html for x in ['sh-dgr__', 'liKJmf', 'pla-unit', 'product'])
        
        logger.info("="*80)
        logger.info("RESULTS")
        logger.info("="*80)
        logger.info(f"🌐 Final URL: {current_url[:100]}")
        logger.info(f"📊 Total requests: {len(all_requests)}")
        logger.info(f"🎯 Callback URLs: {len(callback_urls)}")
        logger.info(f"📋 Other async URLs: {len(async_urls)}")
        logger.info(f"❌ CAPTCHA: {has_captcha}")
        logger.info(f"✅ Products visible: {has_products}")
        logger.info(f"📄 Page size: {len(html):,} bytes\n")
        
        if callback_urls:
            logger.info("🎉🎉🎉 SUCCESS! CAPTURED CALLBACK URLs!")
            for i, url in enumerate(callback_urls, 1):
                logger.info(f"\n{i}. {url[:120]}...")
                with open(f"real_user_callback_{i}.txt", "w") as f:
                    f.write(url)
                logger.info(f"   Saved: real_user_callback_{i}.txt")
        else:
            logger.warning("⚠️  No /async/callback URLs found")
            
            if async_urls:
                logger.info(f"\n📋 But found {len(async_urls)} other async URLs:")
                for url in async_urls[:5]:
                    logger.info(f"   {url[:120]}")
        
        # Save page
        with open("real_user_results.html", "w") as f:
            f.write(html)
        logger.info(f"\nSaved page: real_user_results.html")
        
        # Keep browser open
        logger.info(f"\n⏳ Keeping browser open for 20 seconds...")
        logger.info("   Check the page visually and DevTools Network tab!")
        time.sleep(20)
        
        driver.quit()
        
        return callback_urls, has_products
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            driver.quit()
        except:
            pass
        return [], False


if __name__ == "__main__":
    callback_urls, has_products = test_real_user_interaction()
    
    print("\n" + "="*80)
    print("FINAL VERDICT")
    print("="*80)
    
    if callback_urls:
        print(f"\n🎉🎉🎉 WE DID IT! Captured {len(callback_urls)} callback URL(s)!")
        print("\n✅ THE HYBRID ARCHITECTURE IS PROVEN:")
        print("   1. UC + Oxylabs bypasses CAPTCHA")
        print("   2. Real user interaction avoids detection")
        print("   3. CDP captures callback URLs programmatically")
        print("   4. Can use curl_cffi with these URLs for fast scraping")
        print("\n🚀 READY TO BUILD THE PRODUCTION SYSTEM!")
        
    elif has_products:
        print(f"\n⚠️  Products visible but NO callback URLs")
        print("\nPossible explanations:")
        print("1. Google Shopping doesn't use /async/callback anymore")
        print("2. Products are server-side rendered (in initial HTML)")
        print("3. Different async pattern (check logged async URLs)")
        print("\nNext steps:")
        print("- Check real_user_results.html for product data")
        print("- If products are in HTML, we can use UC directly (no callbacks needed)")
        print("- If no products, different search interaction needed")
        
    else:
        print("\n❌ No products and no callbacks")
        print("   Check logs and saved HTML above")
    
    print("="*80)

