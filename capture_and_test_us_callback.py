"""
CAPTURE US CALLBACK URL AND TEST IMMEDIATELY

URLs expire fast - must test within seconds of capture!
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
import zipfile
import json
from curl_cffi import requests as curl_requests
import re

PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")

def create_proxy_extension():
    manifest = '{"version":"1.0.0","manifest_version":2,"name":"Proxy","permissions":["proxy","tabs","unlimitedStorage","storage","<all_urls>","webRequest","webRequestBlocking"],"background":{"scripts":["background.js"]},"minimum_chrome_version":"22.0.0"}'
    background = 'var config={mode:"fixed_servers",rules:{singleProxy:{scheme:"http",host:"%s",port:parseInt(%s)},bypassList:["localhost"]}};chrome.proxy.settings.set({value:config,scope:"regular"},function(){});function callbackFn(details){return{authCredentials:{username:"%s",password:"%s"}};}chrome.webRequest.onAuthRequired.addListener(callbackFn,{urls:["<all_urls>"]},["blocking"]);' % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
    plugin = 'proxy_auth_plugin.zip'
    with zipfile.ZipFile(plugin, 'w') as zp:
        zp.writestr("manifest.json", manifest)
        zp.writestr("background.js", background)
    return plugin

print("\n" + "="*80)
print("🇺🇸 CAPTURE + TEST IMMEDIATELY ($ PRICES)".center(80))
print("="*80 + "\n")

proxy_plugin = create_proxy_extension() if PROXY_USER and PROXY_PASS else None
driver = None

try:
    options = uc.ChromeOptions()
    if proxy_plugin:
        options.add_extension(proxy_plugin)
    options.add_argument('--lang=en-US')
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en-US,en'})
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    print("🚀 Launching Chrome...")
    driver = uc.Chrome(options=options, use_subprocess=True)
    
    print("📍 Loading shopping.google.com with US locale...")
    driver.get("https://shopping.google.com/?hl=en&gl=us")
    time.sleep(3)
    
    print("🔍 Searching for 'laptop'...")
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys("laptop")
    search_box.send_keys(Keys.ENTER)
    time.sleep(5)
    
    print("\n🔥 SCROLLING to trigger product loads...")
    for i in range(1, 6):
        driver.execute_script(f"window.scrollTo(0, {i * 800});")
        time.sleep(3)
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    print("⏳ Waiting 30 seconds for ALL callbacks...")
    time.sleep(30)  # Wait MUCH longer for all async requests
    
    print("\n📊 Getting network logs...")
    logs = driver.get_log('performance')
    
    callback_urls = []
    for entry in logs:
        try:
            message = json.loads(entry['message'])['message']
            if message['method'] == 'Network.requestWillBeSent':
                url = message['params']['request']['url']
                if '/async/callback:' in url and 'google.com' in url:
                    callback_urls.append(url)
        except:
            pass
    
    print(f"✅ Found {len(callback_urls)} callback URLs\n")
    
    if callback_urls:
        print("="*80)
        print("🚀 TESTING CALLBACK URLs IMMEDIATELY".center(80))
        print("="*80 + "\n")
        
        for i, url in enumerate(callback_urls, 1):
            print(f"\nTesting callback #{i}...")
            print(f"URL: {url[:100]}...")
            
            try:
                # TEST IMMEDIATELY while fresh!
                r = curl_requests.get(
                    url,
                    impersonate='chrome120',
                    timeout=30,
                    headers={
                        'referer': 'https://shopping.google.com/',
                        'accept-language': 'en-US,en;q=0.9',
                        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    }
                )
                
                size = len(r.text)
                dollar_count = r.text.count('$')
                prices = re.findall(r'\$([0-9,]+\.[0-9]{2})', r.text)
                
                print(f"  Status: {r.status_code}")
                print(f"  Size: {size:,} bytes")
                print(f"  $ signs: {dollar_count}")
                print(f"  Prices: {len(prices)}")
                
                if size > 10000 and dollar_count > 0:
                    print(f"\n🎉 CALLBACK #{i} HAS DATA!")
                    if prices:
                        print(f"  Sample prices: {', '.join([f'${p}' for p in prices[:5]])}")
                    
                    # Save the working response
                    with open(f'us_callback_working_{i}.html', 'w') as f:
                        f.write(r.text)
                    print(f"  ✅ Saved to: us_callback_working_{i}.html\n")
                    
                    print("="*80)
                    print("🎉🎉🎉 SUCCESS! FOUND WORKING $ CALLBACK! 🎉🎉🎉".center(80))
                    print("="*80)
                    break
                else:
                    print(f"  ⚠️  Empty or no data\n")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}\n")
    else:
        print("⚠️  No callback URLs found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if driver:
        driver.quit()
    if proxy_plugin and os.path.exists(proxy_plugin):
        os.remove(proxy_plugin)

print("\n" + "="*80)
print("DONE")
print("="*80)

