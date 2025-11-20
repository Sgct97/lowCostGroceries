"""
Find which network request URLs contain price data
Then test if curl_cffi can fetch them
"""

import sys
import os
import json
import re
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("\n" + "="*80)
print("FINDING URLs WITH PRICE DATA")
print("="*80 + "\n")

options = uc.ChromeOptions()
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

driver = uc.Chrome(options=options)
driver.get('https://shopping.google.com/?hl=en&gl=us')

time.sleep(2)

print("Searching for 'milk'...\n")
search_box = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, 'q'))
)
search_box.send_keys('milk')
search_box.send_keys(Keys.ENTER)

time.sleep(3)

print("Scrolling...\n")
for i in range(1, 3):
    driver.execute_script(f"window.scrollTo(0, {i * 800});")
    time.sleep(2)

print("Analyzing network requests...\n")

logs = driver.get_log('performance')

# Find all requests
request_urls = []

for entry in logs:
    try:
        message = json.loads(entry['message'])['message']
        
        if message['method'] == 'Network.responseReceived':
            response = message['params']['response']
            url = response['url']
            mime_type = response.get('mimeType', '')
            
            # Look for HTML/JSON responses that might have prices
            if 'google.com' in url and ('text/html' in mime_type or 'json' in mime_type):
                if 'q=milk' in url or 'async' in url or 'search?' in url:
                    request_urls.append({
                        'url': url,
                        'mime': mime_type
                    })
    except:
        pass

print(f"Found {len(request_urls)} candidate URLs\n")

# Get cookies for curl_cffi test
cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}

driver.quit()

print("="*80)
print("TESTING URLs WITH curl_cffi")
print("="*80 + "\n")

from curl_cffi import requests as curl_requests

for i, req in enumerate(request_urls[:5]):  # Test first 5
    print(f"\nURL {i+1}:")
    print(f"  {req['url'][:80]}...")
    print(f"  Type: {req['mime']}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': '*/*',
            'Referer': 'https://shopping.google.com/',
        }
        
        r = curl_requests.get(
            req['url'],
            headers=headers,
            cookies=cookies,
            impersonate='chrome120',
            timeout=10
        )
        
        # Look for prices
        prices = re.findall(r'\$([0-9]+\.[0-9]{2})', r.text)
        
        print(f"  Status: {r.status_code}, Size: {len(r.text):,}")
        print(f"  Prices: {len(prices)}")
        
        if len(prices) > 10:
            print(f"  🎉 FOUND PRICES! ${prices[0]}, ${prices[1]}, ...")
            print(f"\n✅ THIS URL WORKS WITH curl_cffi!")
            print(f"✅ URL: {req['url']}")
            
            # Save for further analysis
            with open('working_url.txt', 'w') as f:
                f.write(req['url'])
            
            print(f"\n🎉 NOW TEST: Can we modify q=milk to q=eggs?")
            break
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:50]}")

print("\n" + "="*80)

