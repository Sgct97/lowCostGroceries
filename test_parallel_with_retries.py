"""
Parallel UC with optimal batch size + retry for failures
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
        
        time.sleep(1.5)  # Slightly longer for reliability
        
        html = driver.page_source
        prices = re.findall(r'\$([0-9]+\.[0-9]{2})', html)
        mentions = html.lower().count(query.lower())
        
        driver.quit()
        
        elapsed = time.time() - start
        success = len(prices) > 50 and mentions > 10
        
        return {
            'query': query,
            'prices': len(prices),
            'success': success,
            'time': elapsed
        }
    except Exception as e:
        return {
            'query': query,
            'prices': 0,
            'success': False,
            'time': time.time() - start
        }

if __name__ == '__main__':
    set_start_method('spawn', force=True)
    
    print("\n" + "="*80)
    print("PARALLEL UC WITH RETRIES")
    print("="*80 + "\n")
    
    grocery_list = ['milk', 'eggs', 'bread', 'chicken', 'cheese', 'butter', 'yogurt', 'rice', 'pasta', 'tomatoes']
    
    BATCH_SIZE = 4  # Conservative batch size
    
    print(f"Processing {len(grocery_list)} items in batches of {BATCH_SIZE}...\n")
    
    total_start = time.time()
    all_results = []
    
    # Process in batches
    for i in range(0, len(grocery_list), BATCH_SIZE):
        batch = grocery_list[i:i+BATCH_SIZE]
        print(f"Batch {i//BATCH_SIZE + 1}: {', '.join(batch)}")
        
        with Pool(processes=len(batch)) as pool:
            batch_results = pool.map(search_product, batch)
        
        all_results.extend(batch_results)
        
        # Show batch results
        for r in batch_results:
            status = "✅" if r['success'] else "❌"
            print(f"  {r['query']:12} {r['prices']:3} prices {status}")
        print()
    
    # Retry failures
    failures = [r['query'] for r in all_results if not r['success']]
    
    if failures:
        print(f"Retrying {len(failures)} failed items: {', '.join(failures)}\n")
        
        with Pool(processes=len(failures)) as pool:
            retry_results = pool.map(search_product, failures)
        
        # Replace failed results with retries
        for retry in retry_results:
            for i, r in enumerate(all_results):
                if r['query'] == retry['query']:
                    all_results[i] = retry
                    break
            
            status = "✅" if retry['success'] else "❌"
            print(f"  {retry['query']:12} {retry['prices']:3} prices {status}")
        print()
    
    total_time = time.time() - total_start
    
    print("="*80)
    print("FINAL RESULTS")
    print("="*80)
    
    successful = sum(1 for r in all_results if r['success'])
    
    print(f"\nTotal time: {total_time:.1f}s")
    print(f"Success rate: {successful}/{len(all_results)} ({successful/len(all_results)*100:.0f}%)")
    print(f"Speedup: {28/total_time:.1f}x faster than sequential")
    
    if successful >= 9:
        print(f"\n🎉 SUCCESS! {total_time:.0f}s for 10 items!")
        print(f"✅ Batch size {BATCH_SIZE} with retries works!")
        print(f"✅ ~{total_time:.0f}s per grocery list")
    else:
        print(f"\n⚠️  Only {successful}/10 succeeded even with retries")

