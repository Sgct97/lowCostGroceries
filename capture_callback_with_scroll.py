"""
CRITICAL: Scroll to trigger callback URLs!

The user found that scrolling triggers the real product data callbacks.
This is the missing piece for the hybrid architecture!
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
logger.info("🚀 CAPTURING CALLBACK URLs WITH SCROLL (THE KEY!)")
logger.info("="*80)
logger.info("\nScrolling triggers the real product data callbacks!")
logger.info("This is the missing piece for 25K user scalability!\n")

proxy_extension = create_proxy_extension()
options = uc.ChromeOptions()
options.add_extension(proxy_extension)
options.add_argument('--disable-blink-features=AutomationControlled')

# Enable CDP logging for network interception
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

logger.info("🚀 Launching Chrome...\n")

driver = uc.Chrome(
    options=options,
    use_subprocess=True,
    version_main=None
)

logger.info("✅ Browser launched!\n")

try:
    # Go to shopping.google.com
    logger.info("📍 Loading shopping.google.com...")
    driver.get("https://shopping.google.com")
    time.sleep(3)
    
    # Search
    logger.info("🔍 Searching for 'laptop'...")
    search_box = driver.find_element(By.CSS_SELECTOR, "textarea[name='q']")
    search_box.send_keys("laptop")
    search_box.submit()
    
    logger.info("⏳ Waiting for initial results...")
    time.sleep(5)
    
    # NOW SCROLL - This is the key!
    logger.info("\n" + "="*80)
    logger.info("🔥 SCROLLING TO TRIGGER CALLBACKS (THE KEY!)")
    logger.info("="*80)
    
    for i in range(1, 6):
        scroll_amount = i * 800
        logger.info(f"\n📜 Scroll {i}: {scroll_amount}px")
        driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
        time.sleep(2)  # Wait for callbacks to fire
    
    # Scroll to bottom
    logger.info(f"\n📜 Scroll to bottom...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    logger.info("\n✅ Scrolling complete! Callbacks should have fired.\n")
    
    # Capture network logs
    logger.info("="*80)
    logger.info("🔍 ANALYZING NETWORK LOGS")
    logger.info("="*80)
    
    logs = driver.get_log('performance')
    logger.info(f"\n📊 Total log entries: {len(logs)}\n")
    
    callback_urls = []
    bgasy_urls = []
    all_async_urls = []
    
    for entry in logs:
        try:
            message = json.loads(entry['message'])['message']
            
            if message['method'] == 'Network.requestWillBeSent':
                request = message['params']['request']
                url = request['url']
                
                # Look for callback patterns
                if '/async/callback' in url:
                    callback_urls.append(url)
                    logger.info(f"🎯 CALLBACK URL:")
                    logger.info(f"   {url}\n")
                
                elif '/async/bgasy' in url or 'bgasy' in url:
                    bgasy_urls.append(url)
                    logger.info(f"📋 BGASY URL:")
                    logger.info(f"   {url}\n")
                
                elif 'async' in url.lower() and 'google' in url and ('udm=28' in url or 'shopping' in url):
                    all_async_urls.append(url)
                    
        except:
            pass
    
    # Results
    logger.info("="*80)
    logger.info("RESULTS")
    logger.info("="*80)
    logger.info(f"\n🎯 Callback URLs (/async/callback): {len(callback_urls)}")
    logger.info(f"📋 Bgasy URLs (/async/bgasy): {len(bgasy_urls)}")
    logger.info(f"📋 Other async URLs: {len(all_async_urls)}")
    
    # Check page for products
    html = driver.page_source
    product_count = html.count('class="liKJmf"')
    logger.info(f"✅ Products on page: {product_count}\n")
    
    # Save all found URLs
    if callback_urls:
        logger.info("🎉🎉🎉 FOUND CALLBACK URLs!")
        with open("callback_urls.txt", "w") as f:
            for i, url in enumerate(callback_urls, 1):
                f.write(f"{url}\n")
                logger.info(f"\n{i}. {url[:120]}...")
        logger.info(f"\n✅ Saved {len(callback_urls)} callback URLs to: callback_urls.txt")
    
    if bgasy_urls:
        logger.info(f"\n📋 FOUND BGASY URLs!")
        with open("bgasy_urls.txt", "w") as f:
            for i, url in enumerate(bgasy_urls, 1):
                f.write(f"{url}\n")
                logger.info(f"\n{i}. {url[:120]}...")
        logger.info(f"\n✅ Saved {len(bgasy_urls)} bgasy URLs to: bgasy_urls.txt")
    
    if all_async_urls:
        logger.info(f"\n📋 Other async URLs:")
        for url in all_async_urls[:5]:
            logger.info(f"   {url[:100]}...")
    
    # Keep browser open
    logger.info(f"\n⏳ Keeping browser open for 15 seconds...")
    logger.info("   Check DevTools Network tab manually!")
    time.sleep(15)
    
    driver.quit()
    
    # Summary
    print("\n" + "="*80)
    print("FINAL VERDICT")
    print("="*80)
    
    if callback_urls or bgasy_urls:
        print(f"\n🎉🎉🎉 SUCCESS! Captured {len(callback_urls) + len(bgasy_urls)} async URLs!")
        print("\n✅ NEXT STEP:")
        print("   Test these URLs with curl_cffi to verify they work")
        print("   If they work → HYBRID ARCHITECTURE IS PROVEN!")
        print("\n🚀 For 25K users:")
        print("   1. UC captures callback patterns (100 times)")
        print("   2. curl_cffi uses callbacks (25,000 times)")
        print("   3. FAST + SCALABLE!")
    else:
        print(f"\n⚠️  No callback/bgasy URLs found")
        print("\nPossible reasons:")
        print("1. Google changed their architecture")
        print("2. Need different scroll/interaction pattern")
        print("3. Check saved HTML manually for products")
        print(f"\n📄 Found {product_count} products in final HTML")
        if product_count > 0:
            print("   → Products ARE in HTML, can parse directly!")
            print("   → Use UC for everything (slower but works)")
    
    print("="*80)
    
except Exception as e:
    logger.error(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    try:
        driver.quit()
    except:
        pass

