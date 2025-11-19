"""
SIMPLE: Get US callback URL

We KNOW this works - we got € prices. Now get $ prices.
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
import zipfile

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
print("🇺🇸 GETTING US CALLBACK URL ($ PRICES)".center(80))
print("="*80 + "\n")

proxy_plugin = create_proxy_extension() if PROXY_USER and PROXY_PASS else None
driver = None

try:
    options = uc.ChromeOptions()
    if proxy_plugin:
        options.add_extension(proxy_plugin)
    options.add_argument('--lang=en-US')
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en-US,en'})
    
    print("🚀 Launching Chrome...")
    driver = uc.Chrome(options=options, use_subprocess=True)
    
    # US LOCALE URL
    url = "https://shopping.google.com/?hl=en&gl=us"
    print(f"📍 Loading: {url}\n")
    driver.get(url)
    
    # Wait for search box
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.NAME, "q"))
    )
    
    print("✅ Page loaded")
    print("🔍 Searching for 'laptop'...\n")
    
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys("laptop")
    search_box.send_keys(Keys.ENTER)
    
    # Wait for results
    print("⏳ Waiting for products...")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "liKJmf"))
    )
    print("✅ Products loaded\n")
    
    # SCROLL - ACTUALLY SCROLL THIS TIME
    print("🔥 SCROLLING NOW...")
    for i in range(5):
        scroll_to = (i + 1) * 1000
        driver.execute_script(f"window.scrollTo(0, {scroll_to});")
        print(f"   ↓ Scrolled to {scroll_to}px")
        time.sleep(3)
    
    # Final scroll to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    print("   ↓ Scrolled to BOTTOM\n")
    time.sleep(5)
    
    # Check currency
    html = driver.page_source
    dollars = html.count('$')
    euros = html.count('€')
    
    print("="*80)
    print("CURRENCY CHECK")
    print("="*80)
    print(f"💵 $ signs: {dollars}")
    print(f"💶 € signs: {euros}\n")
    
    if dollars > 100:
        print("✅ CONFIRMED: Page has $ prices!")
        
        # Save HTML as backup
        with open("us_shopping_final.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Saved HTML: us_shopping_final.html\n")
    else:
        print("⚠️  Not enough $ signs - check locale\n")
    
    # Instructions for callback
    print("="*80)
    print("GET THE CALLBACK URL")
    print("="*80)
    print("""
The browser is open with US $ prices.

TO GET THE CALLBACK URL:
1. Press F12 (DevTools)
2. Click 'Network' tab
3. Type 'callback' in filter
4. Look for: /async/callback:XXXX?fc=...
5. Right-click → Copy → Copy URL
6. Paste it here when I ask

Keeping browser open for 2 MINUTES so you can find it...
    """)
    
    time.sleep(120)  # 2 minutes
    
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
print("NEXT: Test callback URL with curl_cffi")
print("="*80 + "\n")

