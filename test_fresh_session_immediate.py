"""
CRITICAL TEST: UC loads page, extract params, IMMEDIATELY test with curl_cffi

If this works: Hybrid architecture is viable
If this fails: UC is required for every scrape (user rejects this)
"""

import sys
import os
import re
import time
from curl_cffi import requests as curl_requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("\n" + "="*80)
print("FRESH SESSION TEST: UC → Extract Params → curl_cffi IMMEDIATELY")
print("="*80 + "\n")

driver = None
try:
    print("STEP 1: UC loading Google Shopping search...")
    driver = uc.Chrome()
    driver.get('https://www.google.com/search?q=milk&udm=28&hl=en&gl=us')
    
    # Wait for products to start loading
    time.sleep(5)
    
    print("STEP 2: Extracting session parameters from page source...")
    page_source = driver.page_source
    
    # Look for session params in the HTML
    gsessionid = re.search(r'gsessionid=([^&"\']+)', page_source)
    ei = re.search(r'[&?]ei=([^&"\']+)', page_source)
    sstk = re.search(r'sstk=([^&"\']+)', page_source)
    
    print(f"  gsessionid: {'✅ ' + gsessionid.group(1)[:30] + '...' if gsessionid else '❌'}")
    print(f"  ei: {'✅ ' + ei.group(1) if ei else '❌'}")
    print(f"  sstk: {'✅ ' + sstk.group(1)[:30] + '...' if sstk else '❌'}")
    
    if not (gsessionid and ei):
        print("\n❌ Session params not found in HTML")
        exit(1)
    
    # Get cookies from UC
    cookies_dict = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
    
    print(f"\nSTEP 3: Building pagination URL with extracted params...")
    pagination_url = f"https://www.google.com/search?q=milk&udm=28&hl=en&gl=us&start=10&sa=N&gsessionid={gsessionid.group(1)}&ei={ei.group(1)}"
    
    if sstk:
        pagination_url += f"&sstk={sstk.group(1)}"
    
    pagination_url += "&async=arc_id:test,_fmt:pc"
    
    print(f"  URL: {pagination_url[:100]}...")
    
    print("\nSTEP 4: IMMEDIATELY calling with curl_cffi (while session is FRESH)...")
    
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
    
    print(f"\nRESULT:")
    print(f"  Status: {r.status_code}")
    print(f"  Size: {len(r.text):,} bytes")
    
    # Look for prices
    prices = re.findall(r'\$([0-9]+\.[0-9]{2})', r.text)
    print(f"  Prices found: {len(prices)}")
    
    if len(prices) > 0:
        print(f"  ✅ Sample: ${prices[0]}, ${prices[1]}, ${prices[2]}")
        print("\n" + "="*80)
        print("🎉 SUCCESS! HYBRID ARCHITECTURE WORKS!")
        print("="*80)
        print("\n1. UC loads initial page")
        print("2. Extract session params from HTML")
        print("3. curl_cffi uses those params for pagination")
        print("4. FAST scraping for same query!")
    else:
        print("\n" + "="*80)
        print("❌ FAILED: Even fresh session doesn't work with curl_cffi")
        print("="*80)
        print("\nGoogle requires FULL browser state, not just params/cookies")
        print("Conclusion: UC required for EVERY scrape")
        
        # Check if blocked
        if 'robot' in r.text.lower() or 'javascript' in r.text.lower():
            print("\nBlocked/redirected. First 500 chars:")
            print(r.text[:500])

finally:
    if driver:
        driver.quit()

