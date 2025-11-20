"""
Final test: UC with SMALL batches (2-3 at a time)
The file conflict happens with 10 parallel, but 2-3 might work
"""

import sys
import os
import re
import time
from multiprocessing import Pool, set_start_method

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def search_product(query):
    """Search one product with UC"""
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time, re
    
    start = time.time()
    driver = None
    
    try:
        driver = uc.Chrome()
        driver.get('https://shopping.google.com/?hl=en&gl=us')
        
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'q'))
        )
        search_box.send_keys(query)
        search_box.send_keys(Keys.ENTER)
        
        time.sleep(0.5)
        
        html = driver.page_source
        prices = re.findall(r'\$([0-9]+\.[0-9]{2})', html)
        mentions = html.lower().count(query.lower())
        
        driver.quit()
        
        elapsed = time.time() - start
        success = len(prices) > 50 and mentions > 10
        
        return {
            'query': query,
            'prices': len(prices),
            'time': elapsed,
            'success': success
        }
    
    except Exception as e:
        if driver:
            try:
                driver.quit()
            except:
                pass
        return {
            'query': query,
            'prices': 0,
            'time': time.time() - start,
            'success': False,
            'error': str(e)[:50]
        }

if __name__ == '__main__':
    set_start_method('spawn', force=True)
    
    print("\n" + "="*80)
    print("UC WITH SMALL BATCHES (2 at a time)")
    print("="*80 + "\n")
    
    grocery_list = ['milk', 'eggs', 'bread', 'chicken', 'cheese', 'butter', 'yogurt', 'rice', 'pasta', 'tomatoes']
    
    BATCH_SIZE = 2  # SMALL batches to avoid conflicts
    
    print(f"Processing {len(grocery_list)} items in batches of {BATCH_SIZE}...\n")
    
    total_start = time.time()
    all_results = []
    
    # Process in small batches
    for i in range(0, len(grocery_list), BATCH_SIZE):
        batch = grocery_list[i:i+BATCH_SIZE]
        print(f"Batch {i//BATCH_SIZE + 1}: {', '.join(batch)}")
        
        with Pool(processes=len(batch)) as pool:
            batch_results = pool.map(search_product, batch)
        
        all_results.extend(batch_results)
        
        for r in batch_results:
            status = "✅" if r['success'] else "❌"
            print(f"  {r['query']:12} {r['prices']:3} prices {status}")
    
    total_time = time.time() - total_start
    
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    
    successful = sum(1 for r in all_results if r['success'])
    
    print(f"\nTotal time: {total_time:.1f}s")
    print(f"Success rate: {successful}/{len(all_results)} ({successful/len(all_results)*100:.0f}%)")
    
    if successful == len(all_results):
        print(f"\n🎉 PERFECT! {total_time:.0f}s for 10 items!")
        print(f"✅ Batches of {BATCH_SIZE} avoid file conflicts")
        print(f"✅ Faster than sequential: {23/total_time:.1f}x")
        print(f"✅ THIS WORKS!")
    elif successful >= 8:
        print(f"\n⚠️  {successful}/10 - Good but not perfect")
    else:
        print(f"\n❌ Only {successful}/10 succeeded")

