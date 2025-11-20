"""
Diagnose WHY parallel UC instances fail
Capture detailed logs, screenshots, HTML for failed attempts
"""

import sys
import os
import re
import time
from multiprocessing import Pool, set_start_method

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def search_product_diagnostic(query):
    """Search with detailed diagnostic info"""
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time, re, traceback
    
    start = time.time()
    result = {
        'query': query,
        'prices': 0,
        'success': False,
        'time': 0,
        'error': None,
        'html_size': 0,
        'search_box_found': False,
        'page_loaded': False,
        'blocked': False
    }
    
    driver = None
    
    try:
        # Step 1: Create driver
        driver = uc.Chrome()
        result['driver_created'] = True
        
        # Step 2: Load page
        driver.get('https://shopping.google.com/?hl=en&gl=us')
        result['page_loaded'] = True
        
        # Step 3: Find search box
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'q'))
        )
        result['search_box_found'] = True
        
        # Step 4: Search
        search_box.send_keys(query)
        search_box.send_keys(Keys.ENTER)
        
        # Step 5: Wait for results
        time.sleep(1.5)
        
        # Step 6: Get HTML
        html = driver.page_source
        result['html_size'] = len(html)
        
        # Step 7: Check for blocking
        if 'robot' in html.lower()[:1000] or 'captcha' in html.lower()[:1000]:
            result['blocked'] = True
            result['error'] = 'CAPTCHA or robot check detected'
        
        # Step 8: Parse results
        prices = re.findall(r'\$([0-9]+\.[0-9]{2})', html)
        mentions = html.lower().count(query.lower())
        
        result['prices'] = len(prices)
        result['mentions'] = mentions
        result['success'] = len(prices) > 50 and mentions > 10
        
        # Save HTML for failed searches
        if not result['success']:
            filename = f"failed_{query}_{int(time.time())}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html[:5000])  # First 5000 chars
            result['html_sample'] = html[:500]
        
    except Exception as e:
        result['error'] = str(e)
        result['traceback'] = traceback.format_exc()
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        
        result['time'] = time.time() - start
    
    return result

if __name__ == '__main__':
    set_start_method('spawn', force=True)
    
    print("\n" + "="*80)
    print("DIAGNOSING PARALLEL UC FAILURES")
    print("="*80 + "\n")
    
    # Test with 4 instances
    test_items = ['milk', 'eggs', 'bread', 'chicken']
    
    print(f"Running {len(test_items)} parallel searches with diagnostics...\n")
    
    with Pool(processes=len(test_items)) as pool:
        results = pool.map(search_product_diagnostic, test_items)
    
    print("\n" + "="*80)
    print("DIAGNOSTIC RESULTS")
    print("="*80 + "\n")
    
    for r in results:
        print(f"\n{r['query'].upper()}:")
        print(f"  Success: {r['success']}")
        print(f"  Prices: {r['prices']}")
        print(f"  Time: {r['time']:.1f}s")
        print(f"  HTML size: {r['html_size']:,} bytes")
        print(f"  Search box found: {r.get('search_box_found', False)}")
        print(f"  Page loaded: {r.get('page_loaded', False)}")
        print(f"  Blocked: {r['blocked']}")
        
        if r['error']:
            print(f"  ERROR: {r['error']}")
        
        if not r['success'] and r['html_size'] > 0:
            print(f"  HTML sample: {r.get('html_sample', '')[:200]}...")
    
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80 + "\n")
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nCommon failure patterns:")
        
        blocked_count = sum(1 for r in failed if r['blocked'])
        small_html = sum(1 for r in failed if r['html_size'] < 10000)
        errors = [r['error'] for r in failed if r['error']]
        
        print(f"  Blocked/CAPTCHA: {blocked_count}")
        print(f"  Small HTML (<10KB): {small_html}")
        print(f"  Errors: {len(errors)}")
        
        if errors:
            print("\nError messages:")
            for err in set(errors):
                print(f"    - {err}")
    
    print("\n" + "="*80)

