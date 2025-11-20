"""
Capture ACTUAL pagination URLs from UC (not constructed ones)
Then test if we can modify q= and use with curl_cffi
"""

import sys
import os
import re
import time
import json
from curl_cffi import requests as curl_requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("\n" + "="*80)
print("CAPTURING ACTUAL PAGINATION URLs FROM UC")
print("="*80 + "\n")

driver = None
try:
    print("STEP 1: UC loads Google Shopping with CDP logging...")
    
    options = uc.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = uc.Chrome(options=options)
    driver.get('https://shopping.google.com/?hl=en&gl=us')
    
    # Search for milk
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "q"))
    )
    search_box.send_keys('milk')
    search_box.send_keys(Keys.ENTER)
    
    print("  Waiting for page to load...")
    time.sleep(5)
    
    # Scroll to trigger pagination
    print("  Scrolling to trigger pagination URLs...")
    for i in range(1, 6):
        driver.execute_script(f"window.scrollTo(0, {i * 800});")
        time.sleep(2)
    
    print("\nSTEP 2: Analyzing network logs for pagination URLs...")
    
    logs = driver.get_log('performance')
    pagination_urls = []
    
    for entry in logs:
        try:
            message = json.loads(entry['message'])['message']
            if message['method'] == 'Network.requestWillBeSent':
                url = message['params']['request']['url']
                # Look for async search URLs with q=milk
                if '/search?' in url and 'q=milk' in url and 'async=' in url:
                    pagination_urls.append(url)
        except:
            pass
    
    if not pagination_urls:
        print("  ❌ No pagination URLs found")
        exit(1)
    
    # Take the most recent one
    pagination_url = pagination_urls[-1]
    print(f"  ✅ Found pagination URL: {pagination_url[:100]}...")
    
    # Get cookies
    cookies_dict = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
    
    print("\nSTEP 3: Testing with curl_cffi - ORIGINAL query (milk)...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Referer': 'https://www.google.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }
    
    r = curl_requests.get(
        pagination_url,
        headers=headers,
        cookies=cookies_dict,
        impersonate='chrome120',
        timeout=30
    )
    
    prices = re.findall(r'\$([0-9]+\.[0-9]{2})', r.text)
    print(f"  Status: {r.status_code}, Size: {len(r.text):,}")
    print(f"  Prices: {len(prices)}")
    
    if len(prices) > 0:
        print(f"  ✅ Original URL works: ${prices[0]}, ${prices[1]}")
    else:
        print(f"  ❌ Original URL failed")
        exit(1)
    
    print("\nSTEP 4: Modifying URL to q=eggs and testing...")
    
    eggs_url = pagination_url.replace('q=milk', 'q=eggs')
    
    r2 = curl_requests.get(
        eggs_url,
        headers=headers,
        cookies=cookies_dict,
        impersonate='chrome120',
        timeout=30
    )
    
    prices2 = re.findall(r'\$([0-9]+\.[0-9]{2})', r2.text)
    eggs_mentions = r2.text.lower().count('egg')
    
    print(f"  Status: {r2.status_code}, Size: {len(r2.text):,}")
    print(f"  Prices: {len(prices2)}, Egg mentions: {eggs_mentions}")
    
    if len(prices2) > 0 and eggs_mentions > 10:
        print(f"  🎉 MODIFIED URL WORKS: ${prices2[0]}, ${prices2[1]}")
        print("\n" + "="*80)
        print("🎉🎉🎉 BREAKTHROUGH CONFIRMED PROGRAMMATICALLY! 🎉🎉🎉")
        print("="*80)
        print("\n✅ UC generates pagination URL once")
        print("✅ curl_cffi can reuse it for multiple queries")
        print("✅ Just change q= parameter")
        print("✅ SCALABLE HYBRID ARCHITECTURE!")
    else:
        print(f"  ❌ Modified URL failed")
        if len(r2.text) < 10000:
            print(f"  Response: {r2.text[:500]}")

finally:
    if driver:
        driver.quit()

