"""
THE REAL SOLUTION: Keep UC session alive and reuse it for multiple queries

If user can paste modified URL in browser and get results,
UC can do THE SAME THING.
"""

import sys
import os
import re
import time
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("\n" + "="*80)
print("UC SESSION REUSE: Load once, query multiple products")
print("="*80 + "\n")

driver = None
try:
    print("STEP 1: UC loads Google Shopping and searches for 'milk'...")
    
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
    
    print("  Waiting for initial page...")
    time.sleep(5)
    
    # Scroll to trigger pagination
    for i in range(1, 4):
        driver.execute_script(f"window.scrollTo(0, {i * 800});")
        time.sleep(2)
    
    print("\nSTEP 2: Capturing pagination URL pattern...")
    
    logs = driver.get_log('performance')
    pagination_url = None
    
    for entry in logs:
        try:
            message = json.loads(entry['message'])['message']
            if message['method'] == 'Network.requestWillBeSent':
                url = message['params']['request']['url']
                if '/search?' in url and 'q=milk' in url and 'async=' in url:
                    pagination_url = url
        except:
            pass
    
    if not pagination_url:
        print("  ❌ No pagination URL found")
        exit(1)
    
    print(f"  ✅ Captured: {pagination_url[:100]}...")
    
    print("\nSTEP 3: Testing with DIFFERENT queries using UC's browser...")
    
    test_queries = ['eggs', 'bread', 'chicken']
    results = []
    
    for query in test_queries:
        print(f"\n  Testing: {query.upper()}")
        
        # Modify the pagination URL for this query
        modified_url = pagination_url.replace('q=milk', f'q={query}')
        
        print(f"    Navigating to modified URL...")
        driver.get(modified_url)
        time.sleep(3)
        
        # Get the page source
        html = driver.page_source
        
        # Look for prices
        prices = re.findall(r'\$([0-9]+\.[0-9]{2})', html)
        query_mentions = html.lower().count(query.lower())
        
        print(f"    Size: {len(html):,}, Prices: {len(prices)}, Query mentions: {query_mentions}")
        
        if len(prices) > 0 and query_mentions > 10:
            print(f"    ✅ SUCCESS: ${prices[0]}, ${prices[1] if len(prices) > 1 else '...'}")
            results.append(True)
        else:
            print(f"    ❌ Failed")
            results.append(False)
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80 + "\n")
    
    successful = sum(results)
    total = len(results)
    
    print(f"Successful: {successful}/{total}")
    
    if successful == total:
        print("\n🎉🎉🎉 PERFECT! UC SESSION REUSE WORKS! 🎉🎉🎉")
        print("\n✅ 1 UC browser session")
        print("✅ Multiple product queries")
        print("✅ Modify URL, navigate, parse")
        print("✅ No curl_cffi needed")
        print("✅ SCALABLE!")
    elif successful > 0:
        print(f"\n⚠️  {successful}/{total} worked - needs refinement")
    else:
        print("\n❌ All failed")

finally:
    if driver:
        print("\nClosing browser...")
        driver.quit()

