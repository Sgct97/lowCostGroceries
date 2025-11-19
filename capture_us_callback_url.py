"""
FINAL: Capture US callback URL and test with curl_cffi

This will prove the complete hybrid architecture works with $ prices!
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
import zipfile
import json
from curl_cffi import requests
import re

PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")

SEARCH_QUERY = "laptop"
INITIAL_URL = "https://shopping.google.com/?hl=en&gl=us"  # US locale


def create_proxy_extension():
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Proxy Auth",
        "permissions": ["proxy","tabs","unlimitedStorage","storage","<all_urls>","webRequest","webRequestBlocking"],
        "background": {"scripts": ["background.js"]},
        "minimum_chrome_version":"22.0.0"
    }
    """
    
    background_js = """
    var config = {
        mode: "fixed_servers",
        rules: {singleProxy: {scheme: "http", host: "%s", port: parseInt(%s)}, bypassList: ["localhost"]}
    };
    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
    function callbackFn(details) {
        return {authCredentials: {username: "%s", password: "%s"}};
    }
    chrome.webRequest.onAuthRequired.addListener(callbackFn, {urls: ["<all_urls>"]}, ['blocking']);
    """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
    
    plugin_file = 'proxy_auth_plugin.zip'
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_file


print("\n" + "="*80)
print("🇺🇸 FINAL TEST: US Callback URL + curl_cffi".center(80))
print("="*80 + "\n")

proxy_plugin = create_proxy_extension() if PROXY_USER and PROXY_PASS else None

# STEP 1: Capture callback with UC
print("STEP 1: Capturing callback URL with UC (US locale)")
print("-" * 80 + "\n")

driver = None
callback_url = None

try:
    options = uc.ChromeOptions()
    if proxy_plugin:
        options.add_extension(proxy_plugin)
    options.add_argument('--lang=en-US')
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en-US,en'})
    
    driver = uc.Chrome(options=options, use_subprocess=True)
    driver.get(INITIAL_URL)
    
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(SEARCH_QUERY)
    search_box.send_keys(Keys.ENTER)
    time.sleep(5)
    
    # Scroll to trigger callbacks
    for i in range(3):
        driver.execute_script(f"window.scrollTo(0, {(i+1) * 1000});")
        time.sleep(2)
    
    # Get page HTML and look for callback pattern
    html = driver.page_source
    
    # Search for /async/callback URLs in the page source
    callback_patterns = re.findall(r'https://www\.google\.com/async/callback:\d+\?[^"\']+', html)
    
    if callback_patterns:
        callback_url = callback_patterns[0]
        print(f"✅ Found callback URL!")
        print(f"   {callback_url[:100]}...\n")
        
        with open("us_callback_url.txt", "w") as f:
            f.write(callback_url)
    else:
        print("⚠️  No /async/callback found in HTML")
        print("   Trying to extract from network logs...")
        # Could use CDP here but for now just note it
        
except Exception as e:
    print(f"❌ Error in UC capture: {e}")
finally:
    if driver:
        driver.quit()
    if proxy_plugin and os.path.exists(proxy_plugin):
        os.remove(proxy_plugin)

# STEP 2: Test with curl_cffi
if callback_url:
    print("\n" + "="*80)
    print("STEP 2: Testing callback URL with curl_cffi (NO BROWSER!)".center(80))
    print("="*80 + "\n")
    
    proxy_dict = {
        "http": f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}",
        "https": f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}",
    } if PROXY_USER and PROXY_PASS else None
    
    try:
        response = requests.get(
            callback_url,
            headers={
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "referer": "https://shopping.google.com/",
            },
            proxies=proxy_dict,
            impersonate="chrome120",
            timeout=30
        )
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Size: {len(response.text):,} bytes\n")
        
        html = response.text
        
        # Count currencies
        dollar_count = html.count('$')
        euro_count = html.count('€')
        
        # Extract prices
        dollar_prices = re.findall(r'\$\s*(\d+[\.,]\d+)', html)
        product_containers = html.count('class="liKJmf"')
        
        print("="*80)
        print("RESULTS")
        print("="*80 + "\n")
        print(f"💵 Dollar signs: {dollar_count}")
        print(f"💶 Euro signs: {euro_count}")
        print(f"📦 Product containers: {product_containers}")
        print(f"💰 Prices found: {len(dollar_prices)}\n")
        
        if dollar_prices:
            print("✅ Sample USD prices:")
            for price in dollar_prices[:10]:
                print(f"   ${price}")
        
        if dollar_count > 0 and len(dollar_prices) > 0:
            print("\n" + "="*80)
            print("🎉🎉🎉 SUCCESS! HYBRID ARCHITECTURE WORKS! 🎉🎉🎉".center(80))
            print("="*80 + "\n")
            print("✅ UC captured callback URL")
            print("✅ curl_cffi got product data (NO BROWSER!)")
            print("✅ Prices are in USD ($)")
            print(f"✅ Found {len(dollar_prices)} products\n")
            print("🚀 FOR 25K USERS:")
            print("   1. UC: 100 captures × 10 sec = 17 min")
            print("   2. curl_cffi: 25,000 requests × 0.5 sec = 3.5 hours")
            print("   3. TOTAL: ~4 hours")
            print("   4. Cost: LOW (mostly HTTP)")
            print("="*80)
        else:
            print("\n⚠️  No USD prices found - may need fresh callback URL")
            
    except Exception as e:
        print(f"❌ curl_cffi error: {e}")
else:
    print("\n⚠️  Could not capture callback URL from UC")
    print("   May need to use CDP to intercept network requests")

