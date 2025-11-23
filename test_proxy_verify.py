#!/usr/bin/env python3
import undetected_chromedriver as uc
import zipfile
import time
import os

# EXACT proxy config from token_service.py
PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = "lowCostGroceris_26SVt"
PROXY_PASS = "AppleID_1234"

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

# Create ZIP
plugin_file = 'proxy_auth_plugin.zip'
with zipfile.ZipFile(plugin_file, 'w') as zp:
    zp.writestr("manifest.json", manifest_json)
    zp.writestr("background.js", background_js)

print("✅ Proxy extension created")

# Start Chrome with proxy
options = uc.ChromeOptions()
options.add_extension(plugin_file)
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

print("🚀 Starting Chrome with proxy...")
driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)

try:
    # Check IP
    print("🔍 Checking IP address...")
    driver.get('https://api.ipify.org')
    time.sleep(3)
    ip = driver.find_element('tag name', 'body').text.strip()
    print(f"\n📍 IP ADDRESS: {ip}")

    # Load Google Shopping with US settings
    print("\n🛒 Loading Google Shopping with US locale...")
    driver.get('https://www.google.com/search?q=milk&udm=28&gl=us&hl=en')
    time.sleep(4)

    # Check for $ (US) or € (EU)
    html = driver.page_source
    has_dollars = '$' in html
    has_euros = '€' in html

    print(f"💵 Has $ (US currency): {has_dollars}")
    print(f"💶 Has € (EU currency): {has_euros}")
    print(f"📄 Title: {driver.title}")

    # Verdict
    if ip == '164.92.68.250':
        print("\n❌ PROXY NOT WORKING - using droplet IP")
        exit(1)
    elif has_euros and not has_dollars:
        print(f"\n❌ PROXY ROUTING THROUGH EU (IP: {ip}) - need US proxy")
        exit(1)
    elif has_dollars:
        print(f"\n✅ SUCCESS - US proxy working! (IP: {ip})")
        exit(0)
    else:
        print("\n⚠️  UNKNOWN STATE - check manually")
        exit(1)

finally:
    driver.quit()
    if os.path.exists(plugin_file):
        os.remove(plugin_file)

