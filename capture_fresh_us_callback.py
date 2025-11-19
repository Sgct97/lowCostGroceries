"""
CAPTURE FRESH US CALLBACK URL

This will get us $ prices, not € prices!
We'll manually inspect the browser to get the callback URL.
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
import zipfile

PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")

SEARCH_QUERY = "laptop"
# CRITICAL: US locale for $ prices
INITIAL_URL = "https://shopping.google.com/?hl=en&gl=us"


def create_proxy_extension():
    manifest_json = '{"version": "1.0.0", "manifest_version": 2, "name": "Proxy Auth", "permissions": ["proxy","tabs","unlimitedStorage","storage","<all_urls>","webRequest","webRequestBlocking"], "background": {"scripts": ["background.js"]}, "minimum_chrome_version":"22.0.0"}'
    
    background_js = """
    var config = {mode: "fixed_servers", rules: {singleProxy: {scheme: "http", host: "%s", port: parseInt(%s)}, bypassList: ["localhost"]}};
    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
    function callbackFn(details) {return {authCredentials: {username: "%s", password: "%s"}};}
    chrome.webRequest.onAuthRequired.addListener(callbackFn, {urls: ["<all_urls>"]}, ['blocking']);
    """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
    
    plugin_file = 'proxy_auth_plugin.zip'
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_file


print("\n" + "="*80)
print("🇺🇸 CAPTURING FRESH US CALLBACK URL ($ not €!)".center(80))
print("="*80 + "\n")
print("This will open Chrome with US locale.")
print("We'll scroll to load products with $ prices.")
print("Then you can manually check DevTools Network tab for /async/callback URLs\n")

proxy_plugin = create_proxy_extension() if PROXY_USER and PROXY_PASS else None

driver = None

try:
    print("🚀 Launching Chrome with US settings...")
    options = uc.ChromeOptions()
    if proxy_plugin:
        options.add_extension(proxy_plugin)
    
    # Force US locale
    options.add_argument('--lang=en-US')
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en-US,en'})
    
    driver = uc.Chrome(options=options, use_subprocess=True)
    print("✅ Launched!\n")
    
    print(f"📍 Loading {INITIAL_URL}...")
    driver.get(INITIAL_URL)
    time.sleep(3)
    
    print(f"🔍 Searching for '{SEARCH_QUERY}'...")
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(SEARCH_QUERY)
    search_box.send_keys(Keys.ENTER)
    time.sleep(5)
    
    print("\n🔥 SCROLLING to trigger product loads...")
    for i in range(1, 6):
        driver.execute_script(f"window.scrollTo(0, {i * 800});")
        print(f"   Scroll {i}...")
        time.sleep(2)
    
    # Check currency in page
    html = driver.page_source
    dollar_count = html.count('$')
    euro_count = html.count('€')
    
    print("\n" + "="*80)
    print("CURRENCY CHECK")
    print("="*80)
    print(f"\n💵 Dollar signs: {dollar_count}")
    print(f"💶 Euro signs: {euro_count}")
    
    if dollar_count > euro_count:
        print("\n✅ CONFIRMED: Page has $ prices!\n")
    else:
        print("\n⚠️  WARNING: Page might have € prices\n")
    
    # Save HTML for parsing as backup
    with open("us_products_from_uc.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("📄 Saved HTML to: us_products_from_uc.html")
    
    print("\n" + "="*80)
    print("📋 MANUAL STEP: Copy Callback URL".center(80))
    print("="*80)
    print("""
1. Press F12 to open DevTools
2. Go to the 'Network' tab
3. Filter by "callback" in the search box
4. Look for URLs like: /async/callback:XXXX?fc=...
5. Right-click → Copy → Copy URL
6. Save it to us_callback_url.txt

IMPORTANT: The callback URL should have hl=en&gl=us in it!

Browser will stay open for 60 seconds...
    """)
    
    time.sleep(60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if driver:
        print("\n🔴 Closing browser...")
        driver.quit()
    if proxy_plugin and os.path.exists(proxy_plugin):
        os.remove(proxy_plugin)

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("""
1. If you copied a callback URL:
   - Save it to: us_callback_url.txt
   - Run: python3 test_us_callback_with_curl.py

2. If no callback URL found:
   - We can parse the saved HTML directly
   - It already has all the product data with $ prices!
""")
print("="*80 + "\n")

