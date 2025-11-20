#!/usr/bin/env python3
"""
Quick test: Is the proxy actually working?
Check what IP/location Google sees
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import zipfile

PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = "lowCostGroceris_26SVt"
PROXY_PASS = "AppleID_1234"


def create_proxy_extension():
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Proxy Auth",
        "permissions": [
            "proxy", "tabs", "unlimitedStorage", "storage",
            "<all_urls>", "webRequest", "webRequestBlocking"
        ],
        "background": {"scripts": ["background.js"]},
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
        callbackFn, {urls: ["<all_urls>"]}, ['blocking']
    );
    """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
    
    plugin_file = 'proxy_check.zip'
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_file


print("Testing proxy connection...")
print(f"Proxy: {PROXY_HOST}:{PROXY_PORT}\n")

proxy_ext = create_proxy_extension()
options = uc.ChromeOptions()
options.add_extension(proxy_ext)
options.headless = False

driver = uc.Chrome(options=options, use_subprocess=True, version_main=None, headless=False)

# Check IP with proxy
print("1. Checking IP address with whatismyip.com...")
driver.get("https://www.whatismyip.com/")
time.sleep(3)

html = driver.page_source

# Save
with open('proxy_ip_check.html', 'w') as f:
    f.write(html)

print("   Saved to: proxy_ip_check.html")
print("   Look for your IP address in the saved file\n")

# Check Google Shopping location
print("2. Checking Google Shopping location detection...")
driver.get("https://shopping.google.com/?hl=en&gl=us")
time.sleep(3)

html2 = driver.page_source

# Look for location indicator
if "From your IP address" in html2:
    # Extract location
    import re
    match = re.search(r'(\d{5}),\s*([^,]+),\s*(\w+)', html2)
    if match:
        zip_code, city, state = match.groups()
        print(f"   Google sees location: {city}, {state} ({zip_code})")
        
        if zip_code == "33776":
            print(f"   ⚠️  This is YOUR home location (Largo, FL) - proxy NOT working!")
        else:
            print(f"   ✅ This is DIFFERENT from your home - proxy IS working!")
    else:
        print("   Could not parse location")
else:
    print("   No location indicator found")

with open('proxy_shopping_location.html', 'w') as f:
    f.write(html2)

print("   Saved to: proxy_shopping_location.html\n")

driver.quit()

print("\n" + "="*80)
print("Check the saved HTML files to see:")
print("  1. proxy_ip_check.html - What IP address is shown?")
print("  2. proxy_shopping_location.html - What location does Google Shopping see?")
print("="*80)

