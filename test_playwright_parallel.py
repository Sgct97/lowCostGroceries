"""
Test Playwright parallel execution
Playwright is designed for parallel testing with better isolation than UC
"""

import sys
import os
import re
import time
from multiprocessing import Pool, set_start_method

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def search_with_playwright(query):
    """Search one product with Playwright"""
    from playwright.sync_api import sync_playwright
    import time, re
    
    start = time.time()
    
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Navigate to Google Shopping
            page.goto('https://shopping.google.com/?hl=en&gl=us', wait_until='networkidle')
            
            # Search
            page.fill('input[name="q"]', query)
            page.press('input[name="q"]', 'Enter')
            
            # Wait for results
            time.sleep(1.0)
            
            # Get HTML
            html = page.content()
            
            # Parse
            prices = re.findall(r'\$([0-9]+\.[0-9]{2})', html)
            mentions = html.lower().count(query.lower())
            
            browser.close()
            
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
    set_start_method('spawn', force=True)
    
    print("\n" + "="*80)
    print("TESTING PLAYWRIGHT PARALLEL EXECUTION")
    print("="*80 + "\n")
    
    grocery_list = ['milk', 'eggs', 'bread', 'chicken', 'cheese', 'butter', 'yogurt', 'rice', 'pasta', 'tomatoes']
    
    print(f"Searching {len(grocery_list)} items in parallel...\n")
    
    start_time = time.time()
    
    # ALL 10 at once
    with Pool(processes=len(grocery_list)) as pool:
        results = pool.map(search_with_playwright, grocery_list)
    
    total_time = time.time() - start_time
    
    print("Results:")
    print("-" * 60)
    for r in results:
        status = "✅" if r['success'] else "❌"
        error = f" ({r.get('error', '')[:30]}...)" if 'error' in r and r.get('error') else ""
        print(f"{r['query']:12} {r['prices']:3} prices, {r['time']:.1f}s {status}{error}")
    
    print("\n" + "="*80)
    print("PERFORMANCE SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r['success'])
    
    print(f"\nTotal time: {total_time:.1f}s")
    print(f"Success rate: {successful}/{len(results)} ({successful/len(results)*100:.0f}%)")
    
    if successful >= 9:
        print(f"\n🎉🎉🎉 PLAYWRIGHT WORKS IN PARALLEL!")
        print(f"✅ {total_time:.0f}s for 10 items!")
        print(f"✅ {28/total_time:.1f}x faster than sequential UC")
        print(f"✅ Better process isolation")
        print(f"✅ THIS IS THE SOLUTION!")
    elif successful >= 6:
        print(f"\n⚠️  {successful}/10 succeeded - better than UC parallel but needs tuning")
    else:
        print(f"\n❌ {successful}/10 succeeded - not better than UC")

