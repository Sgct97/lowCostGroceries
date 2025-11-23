#!/usr/bin/env python3
import undetected_chromedriver as uc
import time, os, shutil

PROXY_HOST = 'isp.oxylabs.io'
PROXY_PORT = '8001'
PROXY_USER = 'lowCostGroceris_26SVt-country-us'
PROXY_PASS = 'AppleID_1234'

manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 3,
    "name": "Proxy Auth",
    "permissions": ["proxy", "webRequest", "webRequestAuthProvider"],
    "host_permissions": ["<all_urls>"],
    "background": {"service_worker": "background.js"}
}
"""

background_js = """
var config = {
    mode: "fixed_servers",
    rules: {
      singleProxy: {scheme: "http", host: "%s", port: parseInt(%s)},
      bypassList: ["localhost"]
    }
};
chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

chrome.webRequest.onAuthRequired.addListener(
    function(details) {
        return {authCredentials: {username: "%s", password: "%s"}};
    },
    {urls: ["<all_urls>"]},
    ['blocking']
);
""" % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

ext_dir = 'proxy_test_us'
if os.path.exists(ext_dir):
    shutil.rmtree(ext_dir)
os.makedirs(ext_dir)

with open(f'{ext_dir}/manifest.json', 'w') as f:
    f.write(manifest_json)
with open(f'{ext_dir}/background.js', 'w') as f:
    f.write(background_js)

opts = uc.ChromeOptions()
opts.add_argument(f'--load-extension={ext_dir}')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')

print('🚀 Starting Chrome with US-targeted proxy...')
driver = uc.Chrome(options=opts, use_subprocess=False, version_main=None)
time.sleep(3)

print('\n📍 Checking IP geolocation...')
driver.get('https://api.ipify.org')
time.sleep(2)
ip = driver.find_element('tag name', 'body').text.strip()
print(f'IP: {ip}')

print('\n🛒 Loading Google Shopping...')
driver.get('https://www.google.com/search?q=milk&udm=28&gl=us&hl=en')
time.sleep(4)

html = driver.page_source
has_consent = ('Accept all' in html or 'Reject all' in html or 'Aceptar' in html or 'Before you continue' in html)
has_dollars = '$' in html
has_euros = '€' in html

print(f'\n📊 RESULTS:')
print(f'   Cookie consent popup: {"❌ YES" if has_consent else "✅ NO"}')
print(f'   Has $ (US currency): {"✅ YES" if has_dollars else "❌ NO"}')
print(f'   Has € (EU currency): {"❌ YES" if has_euros else "✅ NO"}')
print(f'   Title: {driver.title}')

driver.quit()
shutil.rmtree(ext_dir)

if not has_consent and has_dollars and not has_euros:
    print('\n✅ SUCCESS - Pure US proxy, no popup!')
    exit(0)
elif has_consent:
    print('\n❌ STILL GETTING EU COOKIE POPUP - proxy not routing through US')
    exit(1)
else:
    print('\n⚠️  Mixed results')
    exit(1)

