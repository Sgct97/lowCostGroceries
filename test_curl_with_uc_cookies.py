"""
HYBRID: UC gets cookies → curl_cffi uses them!

This is the REAL hybrid architecture!
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from curl_cffi import requests
import re

print("\n" + "="*80)
print("🎯 HYBRID: UC cookies → curl_cffi".center(80))
print("="*80 + "\n")

# STEP 1: Get cookies from UC
print("STEP 1: Getting cookies from UC...")
options = uc.ChromeOptions()
options.add_argument('--lang=en-US')
driver = uc.Chrome(options=options, use_subprocess=True)

driver.get('https://shopping.google.com/?hl=en&gl=us')
time.sleep(3)

search_box = driver.find_element(By.NAME, 'q')
search_box.send_keys('laptop')
search_box.send_keys(Keys.ENTER)
time.sleep(8)

# Extract ALL cookies
cookies = driver.get_cookies()
cookie_dict = {c['name']: c['value'] for c in cookies}
cookie_string = '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])

print(f"✅ Got {len(cookies)} cookies\n")

# Get UC HTML for comparison
uc_html = driver.page_source
uc_prices = re.findall(r'\$[0-9,]+\.[0-9]{2}', uc_html)
print(f"UC HTML prices: {len(uc_prices)}")

driver.quit()

# STEP 2: Use cookies with curl_cffi
print("\n" + "="*80)
print("STEP 2: Using cookies with curl_cffi (NO BROWSER!)".center(80))
print("="*80 + "\n")

url = "https://shopping.google.com/search?q=laptop&hl=en&gl=us"

r = requests.get(
    url,
    headers={
        'cookie': cookie_string,
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'accept-language': 'en-US,en;q=0.9',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    },
    impersonate='chrome120',
    timeout=30
)

print(f"Status: {r.status_code}")
print(f"Size: {len(r.text):,} bytes")

curl_prices = re.findall(r'\$[0-9,]+\.[0-9]{2}', r.text)
print(f"curl_cffi prices: {len(curl_prices)}")

if curl_prices:
    print(f"\n✅ Sample prices: {', '.join(curl_prices[:10])}")

with open('curl_with_cookies.html', 'w') as f:
    f.write(r.text)
print("\nSaved to: curl_with_cookies.html")

print("\n" + "="*80)
if len(curl_prices) > 10:
    print("🎉 SUCCESS! curl_cffi + cookies WORKS!".center(80))
    print("="*80)
    print("\n🚀 FOR 25K USERS:")
    print("  1. UC: Get cookies (~100 times)")
    print("  2. Rotate cookies for curl_cffi requests")
    print("  3. Each cookie good for ~1000 requests")
    print("  4. curl_cffi is FAST (0.5 sec)")
else:
    print("⚠️  Cookies alone not enough".center(80))
    print("="*80)
print("="*80)

