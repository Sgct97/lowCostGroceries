#!/usr/bin/env python3
"""
SPEED TEST: Find the FASTEST timing that still gets products
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import re

def parse_products(html):
    """Parse products from HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    containers = soup.find_all('div', class_='gkQHve')
    
    products = []
    for title_elem in containers[:10]:
        try:
            title = title_elem.get_text(strip=True)
            parent = title_elem.find_parent('div', class_='PhALMc')
            if not parent:
                continue
            
            price_elem = parent.find('span', class_='lmQWe')
            price_text = price_elem.get_text(strip=True) if price_elem else None
            price = None
            if price_text:
                match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                if match:
                    price = float(match.group(1).replace(',', ''))
            
            merchant_elem = parent.find('span', class_='WJMUdc')
            merchant = merchant_elem.get_text(strip=True) if merchant_elem else None
            
            if title and price:
                products.append({'title': title, 'price': price, 'merchant': merchant})
        except:
            pass
    
    return products

def test_timing(load_wait, search_wait, scroll_count, scroll_wait):
    """Test a specific timing configuration"""
    driver = uc.Chrome()
    
    try:
        start = time.time()
        
        # Load
        driver.get('https://shopping.google.com/?hl=en&gl=us')
        time.sleep(load_wait)
        
        # Search
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys("milk")
        search_box.send_keys(Keys.ENTER)
        time.sleep(search_wait)
        
        # Scroll
        for i in range(scroll_count):
            driver.execute_script(f"window.scrollTo(0, {(i+1) * 800});")
            time.sleep(scroll_wait)
        
        # Parse
        html = driver.page_source
        products = parse_products(html)
        
        elapsed = time.time() - start
        
        driver.quit()
        
        return {
            'success': len(products) > 0,
            'products': len(products),
            'time': elapsed,
            'config': {
                'load_wait': load_wait,
                'search_wait': search_wait,
                'scroll_count': scroll_count,
                'scroll_wait': scroll_wait
            }
        }
    except Exception as e:
        try:
            driver.quit()
        except:
            pass
        return {'success': False, 'error': str(e)}


print("\n" + "="*80)
print("SPEED TEST: Finding fastest configuration")
print("="*80 + "\n")

# Test different configurations from fastest to slowest
configs = [
    # (load_wait, search_wait, scroll_count, scroll_wait)
    (0.5, 1, 1, 0.5),   # Ultra fast: 3.5s
    (0.5, 1.5, 1, 0.5), # Very fast: 4s
    (1, 1, 1, 0.5),     # Super fast: 4.5s
    (1, 1.5, 1, 1),     # Fast: 5.5s
    (1, 2, 1, 1),       # Proven: 5.7s
]

results = []

for i, (load, search, scrolls, scroll_w) in enumerate(configs, 1):
    print(f"[Test {i}/{len(configs)}] load={load}s, search={search}s, scrolls={scrolls}×{scroll_w}s")
    print(f"  Expected time: ~{load + search + (scrolls * scroll_w) + 3}s")
    
    result = test_timing(load, search, scrolls, scroll_w)
    results.append(result)
    
    if result['success']:
        print(f"  ✅ SUCCESS: {result['products']} products in {result['time']:.1f}s")
    else:
        print(f"  ❌ FAILED: {result.get('error', 'No products')}")
    
    print()
    time.sleep(2)  # Brief pause between tests

print("\n" + "="*80)
print("RESULTS")
print("="*80 + "\n")

successful = [r for r in results if r['success']]

if successful:
    fastest = min(successful, key=lambda x: x['time'])
    
    print(f"🎉 FASTEST WORKING CONFIG:")
    print(f"   Load wait: {fastest['config']['load_wait']}s")
    print(f"   Search wait: {fastest['config']['search_wait']}s")
    print(f"   Scrolls: {fastest['config']['scroll_count']} × {fastest['config']['scroll_wait']}s")
    print(f"   Total time: {fastest['time']:.1f}s")
    print(f"   Products: {fastest['products']}")
    
    print(f"\n📊 All successful configs:")
    for r in successful:
        c = r['config']
        print(f"   {r['time']:.1f}s - load:{c['load_wait']}s search:{c['search_wait']}s scroll:{c['scroll_count']}×{c['scroll_wait']}s → {r['products']} products")
    
    print(f"\n💡 RECOMMENDATION:")
    print(f"   Use fastest config for production: {fastest['time']:.1f}s per search")
    print(f"   For 10 items: ~{fastest['time'] * 10:.0f}s total")
else:
    print("❌ No configurations worked!")

print("\n" + "="*80)

