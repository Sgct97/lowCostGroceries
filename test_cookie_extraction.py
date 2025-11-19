"""
SCALABLE SOLUTION: Extract cookies from UC, reuse with curl_cffi

Strategy for 25K users:
1. UC: 100 times (get fresh cookies)
2. curl_cffi: 25,000 times (using cookies)
3. Total: ~5 hours instead of 70 hours!
"""

import undetected_chromedriver as uc
from curl_cffi import requests
import zipfile
import time
import logging
import re

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
logger.info("🚀 COOKIE EXTRACTION FOR 25K USER SCALABILITY")
logger.info("="*80)
logger.info("\nStep 1: Use UC to get valid cookies")
logger.info("Step 2: Extract cookies")
logger.info("Step 3: Use curl_cffi with cookies (FAST!)\n")

# Step 1: Get cookies with UC
logger.info("="*80)
logger.info("STEP 1: Getting cookies with UC")
logger.info("="*80)

proxy_extension = create_proxy_extension()
options = uc.ChromeOptions()
options.add_extension(proxy_extension)
options.add_argument('--disable-blink-features=AutomationControlled')

logger.info("🚀 Launching Chrome...\n")

driver = uc.Chrome(
    options=options,
    use_subprocess=True,
    version_main=None
)

logger.info("✅ Browser launched!")

try:
    # Go to shopping.google.com and search
    logger.info("\n📍 Loading shopping.google.com...")
    driver.get("https://shopping.google.com")
    time.sleep(3)
    
    # Search for laptop
    logger.info("🔍 Searching for 'laptop'...")
    search_box = driver.find_element("css selector", "textarea[name='q']")
    search_box.send_keys("laptop")
    search_box.submit()
    
    time.sleep(10)  # Wait for results
    
    # Extract cookies
    logger.info("\n" + "="*80)
    logger.info("STEP 2: Extracting cookies")
    logger.info("="*80)
    
    cookies = driver.get_cookies()
    logger.info(f"\n✅ Extracted {len(cookies)} cookies:")
    
    cookie_dict = {}
    for cookie in cookies:
        logger.info(f"   {cookie['name']}: {cookie['value'][:50]}...")
        cookie_dict[cookie['name']] = cookie['value']
    
    # Build cookie string for curl_cffi
    cookie_string = "; ".join([f"{name}={value}" for name, value in cookie_dict.items()])
    
    # Check for products in UC
    html = driver.page_source
    product_count_uc = html.count('class="liKJmf"')
    logger.info(f"\n✅ UC found {product_count_uc} products")
    
    driver.quit()
    
    # Step 3: Use cookies with curl_cffi
    logger.info("\n" + "="*80)
    logger.info("STEP 3: Using cookies with curl_cffi (FAST!)")
    logger.info("="*80)
    
    test_url = "https://www.google.com/search?q=laptop&udm=28"
    
    logger.info(f"\n🚀 Testing curl_cffi with extracted cookies...")
    logger.info(f"URL: {test_url}\n")
    
    response = requests.get(
        test_url,
        headers={
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
            "cookie": cookie_string,
        },
        proxies={
            "http": f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}",
            "https": f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}",
        },
        impersonate="chrome120",
        timeout=30
    )
    
    logger.info(f"✅ Status: {response.status_code}")
    logger.info(f"✅ Size: {len(response.text):,} bytes")
    
    product_count_curl = response.text.count('class="liKJmf"')
    
    has_captcha = 'captcha' in response.text.lower()
    has_sorry = '/sorry/' in response.url
    
    logger.info(f"\n📊 Results with curl_cffi + cookies:")
    logger.info(f"   Products: {product_count_curl}")
    logger.info(f"   CAPTCHA: {has_captcha}")
    logger.info(f"   Sorry page: {has_sorry}")
    
    # Save for inspection
    with open("curl_with_cookies.html", "w") as f:
        f.write(response.text)
    
    logger.info("\n" + "="*80)
    logger.info("FINAL VERDICT")
    logger.info("="*80)
    
    if product_count_curl > 0:
        logger.info(f"\n🎉🎉🎉 SUCCESS! curl_cffi + cookies works!")
        logger.info(f"\n✅ FOUND {product_count_curl} PRODUCTS with curl_cffi!")
        logger.info(f"\n🚀 FOR 25K USERS:")
        logger.info(f"   1. Use UC: ~100 times (get fresh cookies)")
        logger.info(f"      Time: 100 × 10 sec = 17 min")
        logger.info(f"   2. Use curl_cffi: 25,000 times (with cookies)")
        logger.info(f"      Time: 25,000 × 0.5 sec = 3.5 hours")
        logger.info(f"   3. TOTAL: ~4 hours for 25K users")
        logger.info(f"   4. Cost: LOW (mostly HTTP, minimal UC)")
        logger.info(f"\n✅ Cookie TTL: ~1 hour (refresh 100 times/hour)")
        logger.info(f"✅ Parallelism: 250 curl_cffi workers")
        logger.info(f"\n🎉 THIS IS THE SCALABLE SOLUTION!")
        
    elif has_captcha or has_sorry:
        logger.warning(f"\n❌ Cookies didn't work - still blocked")
        logger.info(f"\nFallback: Pure UC (slower)")
        logger.info(f"   - 25K × 10 sec = 70 hours")
        logger.info(f"   - Need 100 parallel UC instances")
        
    else:
        logger.warning(f"\n⚠️  No products but no CAPTCHA")
        logger.info(f"\nPossible issues:")
        logger.info(f"   1. Cookies expired too fast")
        logger.info(f"   2. Need additional headers")
        logger.info(f"   3. Products still JS-rendered")
    
except Exception as e:
    logger.error(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    try:
        driver.quit()
    except:
        pass

logger.info("\n" + "="*80)

