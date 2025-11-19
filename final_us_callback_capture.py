"""
FINAL: Capture US callback URLs using CDP (Chrome DevTools Protocol)

We know the callback URLs work - we just need them with US locale!
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
import zipfile
import json

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
print("🇺🇸 CAPTURING US CALLBACK URLs (Final Version)".center(80))
print("="*80 + "\n")

proxy_plugin = create_proxy_extension() if PROXY_USER and PROXY_PASS else None

driver = None
captured_urls = []

try:
    print("🚀 Launching UC with US locale...")
    options = uc.ChromeOptions()
    if proxy_plugin:
        options.add_extension(proxy_plugin)
    
    # Force US locale
    options.add_argument('--lang=en-US')
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en-US,en'})
    options.add_argument('--enable-logging')
    options.add_argument('--v=1')
    
    driver = uc.Chrome(options=options, use_subprocess=True)
    
    # Enable CDP for network capture
    driver.execute_cdp_cmd("Network.enable", {})
    
    print(f"✅ Launched\n")
    print(f"📍 Loading {INITIAL_URL}...")
    driver.get(INITIAL_URL)
    time.sleep(3)
    
    print(f"🔍 Searching for '{SEARCH_QUERY}'...")
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(SEARCH_QUERY)
    search_box.send_keys(Keys.ENTER)
    time.sleep(5)
    
    print("\n🔥 SCROLLING to trigger callbacks...")
    for i in range(1, 4):
        driver.execute_script(f"window.scrollTo(0, {i * 1000});")
        print(f"   Scroll {i}...")
        time.sleep(3)
    
    # Get performance logs (contains network requests)
    logs = driver.get_log('performance')
    print(f"\n📊 Analyzing {len(logs)} log entries...")
    
    for entry in logs:
        try:
            log = json.loads(entry['message'])['message']
            if log['method'] == 'Network.requestWillBeSent':
                url = log['params']['request']['url']
                
                # Look for callback URLs
                if '/async/callback' in url and 'google.com' in url:
                    captured_urls.append(url)
                    print(f"\n🎯 FOUND: /async/callback URL!")
                    print(f"   {url[:100]}...")
        except:
            pass
    
    # Check HTML for currency
    html = driver.page_source
    dollar_count = html.count('$')
    euro_count = html.count('€')
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80 + "\n")
    print(f"🎯 Callback URLs captured: {len(captured_urls)}")
    print(f"💵 Dollar signs in page: {dollar_count}")
    print(f"💶 Euro signs in page: {euro_count}")
    
    if captured_urls:
        print("\n✅ SUCCESS! Captured callback URLs with US locale!\n")
        with open("us_callback_urls.txt", "w") as f:
            for url in captured_urls:
                f.write(url + "\n")
                print(f"📝 {url[:120]}...")
        print(f"\n✅ Saved to: us_callback_urls.txt")
        
        print("\n" + "="*80)
        print("NEXT STEP: Test with curl_cffi!".center(80))
        print("="*80)
    else:
        print("\n⚠️  No /async/callback URLs found")
        print("   The URLs might have a different pattern")
        print(f"   But we confirmed ${dollar_count} dollar signs in the page!")
    
    time.sleep(5)
    
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
print("SUMMARY".center(80))
print("="*80)

if captured_urls and dollar_count > euro_count:
    print("\n🎉 PERFECT! We have:")
    print("  ✅ Callback URLs captured")
    print("  ✅ US locale ($ prices)")
    print("\n🚀 Next: Test these URLs with curl_cffi!")
elif captured_urls:
    print("\n⚠️  URLs captured but wrong locale")
    print("  ❌ Need to ensure US locale in URLs")
else:
    print("\n⚠️  No callbacks found - may need different capture method")

print("="*80 + "\n")

