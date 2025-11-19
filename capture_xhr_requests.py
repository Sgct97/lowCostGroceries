"""
CAPTURE XHR/Fetch requests that load product data!

Products are loaded AFTER initial page via Ajax/XHR.
These are the requests the user manually found!
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import logging
import zipfile
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


logger.info("\n" + "="*80)
logger.info("🎯 CAPTURING XHR/Fetch REQUESTS (Product Load Requests!)")
logger.info("="*80)
logger.info("\nThese are the Ajax calls that load products after scrolling!\n")

proxy_extension = create_proxy_extension()
options = uc.ChromeOptions()
options.add_extension(proxy_extension)
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--lang=en-US')
options.add_experimental_option('prefs', {'intl.accept_languages': 'en-US,en'})
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

logger.info("🚀 Launching Chrome...\n")

driver = uc.Chrome(
    options=options,
    use_subprocess=True,
    version_main=None
)

try:
    logger.info("📍 Loading shopping.google.com with US locale...")
    driver.get("https://shopping.google.com/?hl=en&gl=us")
    time.sleep(3)
    
    logger.info("🔍 Searching for 'laptop'...")
    search_box = driver.find_element(By.CSS_SELECTOR, "textarea[name='q']")
    search_box.send_keys("laptop")
    search_box.submit()
    
    time.sleep(5)
    
    logger.info("\n🔥 SCROLLING (triggers XHR/Fetch for products)...")
    for i in range(1, 6):
        driver.execute_script(f"window.scrollTo(0, {i * 800});")
        time.sleep(3)  # Wait longer per scroll
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    logger.info("⏳ Waiting 10 seconds for ALL product data to load...")
    time.sleep(10)  # Wait MUCH longer for products to fully load
    
    logger.info("\n" + "="*80)
    logger.info("🔍 ANALYZING XHR/Fetch REQUESTS")
    logger.info("="*80)
    
    logs = driver.get_log('performance')
    logger.info(f"\n📊 Total log entries: {len(logs)}\n")
    
    xhr_requests = []
    
    for entry in logs:
        try:
            message = json.loads(entry['message'])['message']
            
            if message['method'] == 'Network.requestWillBeSent':
                request = message['params']['request']
                url = request['url']
                
                # Get resource type
                resource_type = message['params'].get('type', '')
                
                # Look for ALL types if it contains callback or relevant keywords
                if 'google.com' in url:
                    # CRITICAL: Capture ALL async/callback URLs regardless of type!
                    if '/async/callback' in url or '/async/bgasy' in url:
                        xhr_requests.append((url, resource_type))
                        logger.info(f"🎯🎯🎯 {resource_type} REQUEST (CALLBACK):")
                        logger.info(f"   {url[:150]}...\n")
                    # Also capture XHR/Fetch for other endpoints
                    elif resource_type in ['XHR', 'Fetch']:
                        xhr_requests.append((url, resource_type))
                        if any(x in url for x in ['search', 'async', 'shopping', 'udm', 'product']):
                            logger.info(f"🎯 {resource_type} REQUEST:")
                            logger.info(f"   {url[:150]}...\n")
                            
        except:
            pass
    
    logger.info("="*80)
    logger.info("RESULTS")
    logger.info("="*80)
    logger.info(f"\n🎯 XHR/Fetch requests: {len(xhr_requests)}\n")
    
    if xhr_requests:
        logger.info("🎉 FOUND XHR/Fetch REQUESTS (these load product data!):\n")
        
        with open("xhr_product_urls.txt", "w") as f:
            for i, (url, req_type) in enumerate(xhr_requests, 1):
                logger.info(f"{i}. [{req_type}] {url[:120]}...")
                f.write(f"{url}\n")
        
        logger.info(f"\n✅ Saved {len(xhr_requests)} XHR/Fetch URLs to: xhr_product_urls.txt")
        logger.info("\n🚀 NEXT: Test these with curl_cffi!")
    else:
        logger.warning("⚠️  No XHR/Fetch requests found")
    
    # Check final page
    html = driver.page_source
    product_count = html.count('class="liKJmf"')
    logger.info(f"\n✅ Products on final page: {product_count}")
    
    logger.info(f"\n⏳ Keeping browser open for 15 seconds...")
    time.sleep(15)
    
    driver.quit()
    
    print("\n" + "="*80)
    print("BREAKTHROUGH MOMENT")
    print("="*80)
    
    if xhr_requests:
        print(f"\n🎉 Found {len(xhr_requests)} XHR/Fetch requests!")
        print("\n✅ THESE are what load products after scrolling!")
        print("\n🚀 TEST with curl_cffi:")
        print("   - If they work → HYBRID ARCHITECTURE!")
        print("   - curl_cffi can call these directly")
        print("   - No need for UC on every request!")
    else:
        print("\n⚠️  No XHR/Fetch found - products might be in initial HTML")
        print(f"   But we got {product_count} products somehow!")
    
    print("="*80)
    
except Exception as e:
    logger.error(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    try:
        driver.quit()
    except:
        pass

