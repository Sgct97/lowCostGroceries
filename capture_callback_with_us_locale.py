"""
CAPTURE CALLBACK URLs WITH US LOCALE (for $ prices, not €)

This is critical - we need to capture URLs with US settings!
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import json
import os
import zipfile

PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")

SEARCH_QUERY = "laptop"
# CRITICAL: Use US English locale
INITIAL_URL = "https://shopping.google.com/?hl=en&gl=us"


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


print("\n" + "="*80)
print("🇺🇸 CAPTURING US CALLBACK URLs ($ not €!)".center(80))
print("="*80)
print(f"\n🌍 URL: {INITIAL_URL}")
print("💰 Expected currency: USD ($)\n")

proxy_plugin = None
if PROXY_USER and PROXY_PASS:
    proxy_plugin = create_proxy_extension()

driver = None
try:
    print("🚀 Launching Chrome with US settings...")
    options = uc.ChromeOptions()
    if proxy_plugin:
        options.add_extension(proxy_plugin)
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Force US locale
    options.add_argument('--lang=en-US')
    options.add_experimental_option('prefs', {
        'intl.accept_languages': 'en-US,en'
    })
    
    driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
    print("✅ Browser launched!\n")
    
    print("📍 Loading US shopping.google.com...")
    driver.get(INITIAL_URL)
    
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.NAME, "q"))
    )
    print("✅ Homepage loaded\n")
    
    print(f"🔍 Searching for '{SEARCH_QUERY}'...")
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(SEARCH_QUERY)
    search_box.send_keys(Keys.ENTER)
    
    print("⏳ Waiting for results...")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "liKJmf"))
    )
    
    print("\n🔥 SCROLLING to trigger product loads...")
    for i in range(1, 6):
        driver.execute_script(f"window.scrollTo(0, {i * 800});")
        time.sleep(2)
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    # Check the HTML for currency
    html = driver.page_source
    has_dollars = html.count('$')
    has_euros = html.count('€')
    
    print("\n" + "="*80)
    print("CURRENCY CHECK".center(80))
    print("="*80)
    print(f"\n💵 Dollar signs ($): {has_dollars}")
    print(f"💶 Euro signs (€): {has_euros}")
    
    if has_dollars > has_euros:
        print("\n✅ SUCCESS! Got US prices ($)")
    else:
        print("\n⚠️  WARNING: Got European prices (€)")
        print("   The locale settings might not have worked")
        print(f"   Current URL: {driver.current_url}")
    
    # Save HTML for inspection
    with open("us_shopping_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n📄 Saved HTML to: us_shopping_page.html")
    
    # Extract a few prices to confirm
    import re
    dollar_prices = re.findall(r'\$\s*(\d+[\.,]\d+)', html)
    euro_prices = re.findall(r'(\d+[\.,]\d+)\s*€', html)
    
    print(f"\n💰 Sample prices:")
    if dollar_prices:
        print(f"   USD: ${', $'.join(dollar_prices[:5])}")
    if euro_prices:
        print(f"   EUR: {', '.join(euro_prices[:5])}€")
    
    print(f"\n⏳ Keeping browser open for 15 seconds...")
    print("   Check if prices are in USD ($)!")
    time.sleep(15)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if driver:
        driver.quit()
    if proxy_plugin and os.path.exists(proxy_plugin):
        os.remove(proxy_plugin)

print("\n" + "="*80)
print("NEXT STEP".center(80))
print("="*80)
print("\nIf we got $ prices:")
print("  ✅ Capture the callback URL and test with curl_cffi")
print("\nIf we got € prices:")
print("  ⚠️  Need to use a US-based proxy or adjust locale settings")
print("="*80 + "\n")

