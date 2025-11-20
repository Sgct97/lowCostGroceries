"""
Test MULTIPROCESSING parallel UC instances
Each product gets its own UC instance simultaneously
"""

import sys
import os
import re
import time
from multiprocessing import Pool, set_start_method

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def search_product(query):
    """Search one product in its own UC instance"""
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time, re
    
    start = time.time()
    
    try:
        driver = uc.Chrome()
        driver.get('https://shopping.google.com/?hl=en&gl=us')
        
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'q'))
        )
        search_box.send_keys(query)
        search_box.send_keys(Keys.ENTER)
        
        time.sleep(1.0)
        
        html = driver.page_source
        prices = re.findall(r'\$([0-9]+\.[0-9]{2})', html)
        mentions = html.lower().count(query.lower())
        
        driver.quit()
        
        elapsed = time.time() - start
        success = len(prices) > 50 and mentions > 10
        
        return {
            'query': query,
            'prices': len(prices),
            'mentions': mentions,
            'time': elapsed,
            'success': success
        }
    except Exception as e:
        return {
            'query': query,
            'prices': 0,
            'mentions': 0,
            'time': time.time() - start,
            'success': False,
            'error': str(e)
        }

if __name__ == '__main__':
    # Required for multiprocessing on macOS
    set_start_method('spawn', force=True)
    
    print("\n" + "="*80)
    print("TESTING MULTIPROCESS PARALLEL UC INSTANCES")
    print("="*80 + "\n")
    
    grocery_list = ['milk', 'eggs', 'bread', 'chicken', 'cheese', 'butter', 'yogurt', 'rice', 'pasta', 'tomatoes']
    
    print(f"Searching {len(grocery_list)} items in PARALLEL...\n")
    
    start_time = time.time()
    
    # Run all searches in parallel
    with Pool(processes=len(grocery_list)) as pool:
        results = pool.map(search_product, grocery_list)
    
    total_time = time.time() - start_time
    
    print("Results:")
    print("-" * 60)
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"{r['query']:12} {r['prices']:3} prices, {r['mentions']:3} mentions, {r['time']:.1f}s {status}")
    
    print("\n" + "="*80)
    print("PERFORMANCE SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r['success'])
    
    print(f"\nTotal time for {len(grocery_list)} items: {total_time:.1f}s")
    print(f"Success rate: {successful}/{len(results)} ({successful/len(results)*100:.0f}%)")
    print(f"Speedup vs sequential: {28/total_time:.1f}x faster")
    
    if successful == len(results):
        print("\n🎉🎉🎉 PERFECT! PARALLEL WORKS!")
        print(f"✅ 10-item grocery list in ~{total_time:.0f}s")
        print(f"✅ Each item gets dedicated UC instance")
        print(f"✅ This is the FASTEST solution!")
    elif successful >= len(results) * 0.8:
        print(f"\n⚠️  {successful/len(results)*100:.0f}% success - might need tuning")
    else:
        print("\n❌ Too unreliable - parallel approach has issues")

