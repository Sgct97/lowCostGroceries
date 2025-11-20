#!/usr/bin/env python3
"""
SCALE TEST: 5 persistent browsers in parallel
Each searches 2-3 items, staggered start to avoid conflicts
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import re
import zipfile
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = "lowCostGroceris_26SVt"
PROXY_PASS = "AppleID_1234"


def create_proxy_extension(browser_id):
    """Create unique proxy extension"""
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Proxy Auth",
        "permissions": [
            "proxy", "tabs", "unlimitedStorage", "storage",
            "<all_urls>", "webRequest", "webRequestBlocking"
        ],
        "background": {"scripts": ["background.js"]},
        "minimum_chrome_version":"22.0.0"
    }
    """
    
    background_js = """
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
            },
            bypassList: ["localhost"]
        }
    };
    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
    
    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }
    
    chrome.webRequest.onAuthRequired.addListener(
        callbackFn, {urls: ["<all_urls>"]}, ['blocking']
    );
    """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
    
    plugin_file = f'proxy_auth_{browser_id}_{os.getpid()}.zip'
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_file


def parse_products(html, max_products=50):
    """Parse products from HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    containers = soup.find_all('div', class_='gkQHve')
    
    products = []
    for title_elem in containers[:max_products]:
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
                products.append({'title': title[:50], 'price': price, 'merchant': merchant})
        except:
            pass
    
    return products


def persistent_browser_worker(browser_id, queries, zipcode, start_delay=0):
    """
    Persistent browser that searches multiple products
    zipcode: User's ZIP code for location-specific results
    start_delay: seconds to wait before starting (for staggering)
    """
    if start_delay > 0:
        time.sleep(start_delay)
    
    print(f"[Browser {browser_id}] Starting with {len(queries)} products (ZIP: {zipcode})")
    start_total = time.time()
    results = {}
    
    try:
        proxy_ext = create_proxy_extension(browser_id)
        options = uc.ChromeOptions()
        options.add_extension(proxy_ext)
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Unique isolation
        timestamp = int(time.time() * 1000) + browser_id
        user_data = f'/tmp/uc_5_{browser_id}_{timestamp}'
        debug_port = 9222 + browser_id
        options.add_argument(f'--user-data-dir={user_data}')
        options.add_argument(f'--remote-debugging-port={debug_port}')
        
        driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
        
        # Load Google Shopping with user's location
        driver.get(f'https://shopping.google.com/?hl=en&gl=us&near={zipcode}')
        time.sleep(0.5)
        
        # Search each product
        for query in queries:
            search_start = time.time()
            
            search_box = driver.find_element(By.NAME, "q")
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.ENTER)
            time.sleep(1)
            
            driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(0.5)
            
            html = driver.page_source
            products = parse_products(html)
            
            elapsed = time.time() - search_start
            results[query] = {
                'products': products,
                'count': len(products),
                'time': elapsed
            }
            
            print(f"[Browser {browser_id}] {query:10} → {len(products)} products in {elapsed:.1f}s")
        
        driver.quit()
        
        try:
            os.remove(proxy_ext)
        except:
            pass
        
        total_time = time.time() - start_total
        print(f"[Browser {browser_id}] ✅ DONE in {total_time:.1f}s")
        
        return {
            'browser_id': browser_id,
            'success': True,
            'results': results,
            'total_time': total_time
        }
        
    except Exception as e:
        print(f"[Browser {browser_id}] ❌ ERROR: {e}")
        try:
            driver.quit()
        except:
            pass
        return {
            'browser_id': browser_id,
            'success': False,
            'error': str(e)
        }


def test_5_browsers(zipcode="10001"):
    """Test 5 browsers in parallel with location"""
    
    print("\n" + "="*80)
    print(f"TEST: 5 PERSISTENT BROWSERS IN PARALLEL (Location: {zipcode})")
    print("="*80 + "\n")
    
    # 50 items total - 10 per browser to test scale
    all_items = [
        'milk', 'eggs', 'bread', 'butter', 'cheese', 'yogurt', 'chicken', 'beef', 'pork', 'fish',
        'apples', 'bananas', 'oranges', 'carrots', 'broccoli', 'lettuce', 'tomatoes', 'onions', 'potatoes', 'rice',
        'pasta', 'cereal', 'oatmeal', 'coffee', 'tea', 'juice', 'water', 'soda', 'chips', 'crackers',
        'cookies', 'candy', 'ice cream', 'frozen pizza', 'frozen vegetables', 'canned soup', 'canned beans', 'peanut butter', 'jam', 'honey',
        'olive oil', 'vinegar', 'salt', 'pepper', 'sugar', 'flour', 'baking soda', 'vanilla', 'chocolate', 'nuts'
    ]
    
    # Split items - 10 per browser
    items_per_browser = [
        all_items[0:10],   # Browser 1: 10 items
        all_items[10:20],  # Browser 2: 10 items
        all_items[20:30],  # Browser 3: 10 items
        all_items[30:40],  # Browser 4: 10 items
        all_items[40:50],  # Browser 5: 10 items
    ]
    
    for i, items in enumerate(items_per_browser, 1):
        print(f"Browser {i}: {items}")
    print()
    
    start = time.time()
    
    # Launch all 5 browsers with staggered starts
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        
        for browser_id, items in enumerate(items_per_browser, 1):
            # Stagger each browser by 3 seconds to avoid chromedriver conflicts
            delay = (browser_id - 1) * 3
            future = executor.submit(persistent_browser_worker, browser_id, items, zipcode, delay)
            futures.append((browser_id, future))
        
        # Collect results as they complete
        results = {}
        for browser_id, future in futures:
            result = future.result()
            results[browser_id] = result
    
    total_time = time.time() - start
    
    # Print results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80 + "\n")
    
    successful = [r for r in results.values() if r['success']]
    
    if len(successful) == 5:
        print("🎉 ALL 5 BROWSERS SUCCEEDED!\n")
        
        total_products = 0
        all_search_results = {}
        
        for result in successful:
            all_search_results.update(result['results'])
            total_products += sum(r['count'] for r in result['results'].values())
        
        # Show all items with sample merchants
        for item, data in all_search_results.items():
            merchants = list(set([p['merchant'] for p in data['products'] if p.get('merchant')]))[:3]
            merchant_str = ', '.join(merchants) if merchants else 'N/A'
            print(f"{item:12} → {data['count']:3} products in {data['time']:.1f}s")
            print(f"             Stores: {merchant_str}")
        
        print(f"\n📊 Statistics:")
        print(f"   Total items: {len(all_items)}")
        print(f"   Total products: {total_products}")
        print(f"   Total time (parallel): {total_time:.1f}s")
        print(f"   Average per item: {total_time / len(all_items):.1f}s")
        
        browser_times = [r['total_time'] for r in successful]
        print(f"   Fastest browser: {min(browser_times):.1f}s")
        print(f"   Slowest browser: {max(browser_times):.1f}s")
        
        print(f"\n💡 PRODUCTION:")
        print(f"   5 browsers handled {len(all_items)} items in {total_time:.1f}s")
        print(f"   For 10 items: ~{(10/len(all_items)) * total_time:.0f}s")
        print(f"   Average products per item: {total_products / len(all_items):.0f}")
        print(f"   Total products captured: {total_products}")
        
    else:
        failed = len(results) - len(successful)
        print(f"⚠️  {len(successful)}/5 succeeded, {failed} failed\n")
        
        for browser_id, result in results.items():
            if not result['success']:
                print(f"Browser {browser_id} failed: {result.get('error')}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    import sys
    # Allow passing zipcode as command line arg
    zipcode = sys.argv[1] if len(sys.argv) > 1 else "10001"  # Default: NYC
    print(f"\n🌍 Testing with ZIP code: {zipcode}")
    test_5_browsers(zipcode)

