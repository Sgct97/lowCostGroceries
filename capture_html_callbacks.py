"""
FIND THE RIGHT CALLBACKS - HTML with product data, NOT JavaScript!

The user manually found callback URLs with 84 products.
We need to find those EXACT requests - they return HTML, not JS!
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
logger.info("🎯 FINDING HTML CALLBACKS (PRODUCT DATA, NOT JS!)")
logger.info("="*80)
logger.info("\nLooking for the EXACT callbacks the user found manually\n")

proxy_extension = create_proxy_extension()
options = uc.ChromeOptions()
options.add_extension(proxy_extension)
options.add_argument('--disable-blink-features=AutomationControlled')

# Enable performance logging
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

logger.info("🚀 Launching Chrome...\n")

driver = uc.Chrome(
    options=options,
    use_subprocess=True,
    version_main=None
)

try:
    logger.info("📍 Loading shopping.google.com...")
    driver.get("https://shopping.google.com")
    time.sleep(3)
    
    logger.info("🔍 Searching for 'laptop'...")
    search_box = driver.find_element(By.CSS_SELECTOR, "textarea[name='q']")
    search_box.send_keys("laptop")
    search_box.submit()
    
    time.sleep(5)
    
    logger.info("\n🔥 SCROLLING (triggers product loads)...")
    for i in range(1, 6):
        driver.execute_script(f"window.scrollTo(0, {i * 800});")
        time.sleep(2)
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    logger.info("\n" + "="*80)
    logger.info("🔍 ANALYZING ALL NETWORK RESPONSES")
    logger.info("="*80)
    
    logs = driver.get_log('performance')
    logger.info(f"\n📊 Total log entries: {len(logs)}\n")
    
    html_responses = []
    all_google_urls = []
    
    for entry in logs:
        try:
            message = json.loads(entry['message'])['message']
            
            # Look at responses, not just requests
            if message['method'] == 'Network.responseReceived':
                response = message['params']['response']
                url = response['url']
                mime_type = response.get('mimeType', '')
                status = response.get('status', 0)
                
                # Only Google URLs with 200 status
                if 'google.com' in url and status == 200:
                    all_google_urls.append((url, mime_type))
                    
                    # Look for HTML responses (NOT JavaScript!)
                    if 'html' in mime_type.lower() or 'text/html' in mime_type:
                        html_responses.append((url, mime_type))
                        
                        # This could be it!
                        if any(x in url for x in ['async', 'callback', 'shopping', 'udm']):
                            logger.info(f"🎯 HTML RESPONSE FOUND:")
                            logger.info(f"   URL: {url}")
                            logger.info(f"   Type: {mime_type}")
                            logger.info(f"   Status: {status}\n")
        except:
            pass
    
    logger.info("="*80)
    logger.info("RESULTS")
    logger.info("="*80)
    logger.info(f"\n📊 Total Google URLs: {len(all_google_urls)}")
    logger.info(f"🎯 HTML responses: {len(html_responses)}\n")
    
    if html_responses:
        logger.info("🎉 FOUND HTML RESPONSES (these might have product data!):\n")
        
        with open("html_callback_urls.txt", "w") as f:
            for i, (url, mime_type) in enumerate(html_responses, 1):
                logger.info(f"{i}. {mime_type}")
                logger.info(f"   {url[:150]}...")
                logger.info("")
                f.write(f"{url}\n")
        
        logger.info(f"✅ Saved {len(html_responses)} HTML URLs to: html_callback_urls.txt\n")
    
    # Also save ALL Google URLs for analysis
    logger.info("📋 Saving ALL Google URLs for manual analysis...")
    with open("all_google_urls.txt", "w") as f:
        for url, mime_type in all_google_urls:
            f.write(f"{mime_type}|{url}\n")
    logger.info("✅ Saved to: all_google_urls.txt")
    
    # Check final page
    html = driver.page_source
    product_count = html.count('class="liKJmf"')
    logger.info(f"\n✅ Products on final page: {product_count}")
    
    # Save final HTML
    with open("final_page_with_products.html", "w") as f:
        f.write(html)
    logger.info("✅ Saved final HTML: final_page_with_products.html")
    
    logger.info(f"\n⏳ Keeping browser open for manual inspection...")
    time.sleep(15)
    
    driver.quit()
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    
    if html_responses:
        print(f"\n✅ Found {len(html_responses)} HTML response URLs!")
        print("\n🎯 TEST THESE with curl_cffi:")
        print("   1. Open html_callback_urls.txt")
        print("   2. Test each URL with curl_cffi")
        print("   3. Find which ones return product HTML")
        print("\n🚀 If any work → HYBRID ARCHITECTURE PROVEN!")
    else:
        print("\n⚠️  No HTML responses captured")
        print("\n📋 Manual inspection needed:")
        print("   1. Check all_google_urls.txt for patterns")
        print("   2. Look for document/xhr/fetch responses")
        print("   3. The product data IS loading somehow!")
    
    print("="*80)
    
except Exception as e:
    logger.error(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    try:
        driver.quit()
    except:
        pass

