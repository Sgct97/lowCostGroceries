#!/usr/bin/env python3
"""
FINAL TEST: 2 persistent browsers in parallel, each searching multiple products
Uses FAST timing: 3.8s per search
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import re
import zipfile
import os
from concurrent.futures import ThreadPoolExecutor

PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = "lowCostGroceris_26SVt"
PROXY_PASS = "AppleID_1234"


def create_proxy_extension(browser_id):
    """Create unique proxy extension for each browser"""
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


def persistent_browser_worker(browser_id, queries):
    """
    Launch ONE browser and search for MULTIPLE products sequentially
    Browser stays open the whole time (persistent)
    """
    print(f"[Browser {browser_id}] Starting with {len(queries)} products to search")
    start_total = time.time()
    results = {}
    
    try:
        # Setup unique browser instance
        proxy_ext = create_proxy_extension(browser_id)
        options = uc.ChromeOptions()
        options.add_extension(proxy_ext)
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # CRITICAL: Unique isolation per browser
        timestamp = int(time.time() * 1000)
        user_data = f'/tmp/uc_persist_{browser_id}_{timestamp}'
        debug_port = 9222 + browser_id
        options.add_argument(f'--user-data-dir={user_data}')
        options.add_argument(f'--remote-debugging-port={debug_port}')
        
        print(f"[Browser {browser_id}] Launching UC...")
        driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
        
        # Initial load of Google Shopping (ONE TIME)
        print(f"[Browser {browser_id}] Loading shopping.google.com...")
        driver.get('https://shopping.google.com/?hl=en&gl=us')
        time.sleep(0.5)
        
        # Now search for each product sequentially (FAST!)
        for query in queries:
            search_start = time.time()
            
            print(f"[Browser {browser_id}] Searching '{query}'...")
            
            # Clear search box and search
            search_box = driver.find_element(By.NAME, "q")
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.ENTER)
            time.sleep(1)  # Wait for search results
            
            # Quick scroll
            driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(0.5)
            
            # Parse products
            html = driver.page_source
            products = parse_products(html)
            
            elapsed = time.time() - search_start
            results[query] = {
                'products': products,
                'count': len(products),
                'time': elapsed
            }
            
            print(f"[Browser {browser_id}]   → {len(products)} products in {elapsed:.1f}s")
        
        driver.quit()
        
        # Cleanup
        try:
            os.remove(proxy_ext)
        except:
            pass
        
        total_time = time.time() - start_total
        print(f"[Browser {browser_id}] ✅ DONE: {len(queries)} searches in {total_time:.1f}s")
        
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


def test_parallel_persistent():
    """Test 2 persistent browsers in parallel"""
    
    print("\n" + "="*80)
    print("TEST: 2 PERSISTENT BROWSERS IN PARALLEL")
    print("="*80 + "\n")
    
    # Divide 10 items between 2 browsers
    items = ['milk', 'eggs', 'bread', 'butter', 'cheese', 'chicken', 'apples', 'yogurt', 'rice', 'pasta']
    browser_1_items = items[:5]   # First 5
    browser_2_items = items[5:]   # Last 5
    
    print(f"Browser 1 will search: {browser_1_items}")
    print(f"Browser 2 will search: {browser_2_items}")
    print()
    
    start = time.time()
    
    # Run both browsers in parallel (stagger start to avoid chromedriver race)
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(persistent_browser_worker, 1, browser_1_items)
        
        # CRITICAL: Wait 2 seconds before starting second browser
        # This prevents both from patching chromedriver simultaneously
        time.sleep(2)
        
        future2 = executor.submit(persistent_browser_worker, 2, browser_2_items)
        
        result1 = future1.result()
        result2 = future2.result()
    
    total_time = time.time() - start
    
    # Print results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80 + "\n")
    
    if result1['success'] and result2['success']:
        print("🎉 SUCCESS! Both browsers completed!\n")
        
        total_products = 0
        all_results = {**result1['results'], **result2['results']}
        
        for item, data in all_results.items():
            print(f"{item:12} → {data['count']} products in {data['time']:.1f}s")
            total_products += data['count']
            if data['products']:
                p = data['products'][0]
                print(f"             Sample: {p['title']} - ${p['price']} @ {p['merchant']}")
        
        print(f"\n📊 Statistics:")
        print(f"   Total items searched: {len(items)}")
        print(f"   Total products found: {total_products}")
        print(f"   Total time (parallel): {total_time:.1f}s")
        print(f"   Average per item: {total_time / len(items):.1f}s")
        print(f"   Browser 1 time: {result1['total_time']:.1f}s")
        print(f"   Browser 2 time: {result2['total_time']:.1f}s")
        
        print(f"\n💡 PRODUCTION ESTIMATE:")
        print(f"   With 3 browsers: ~{(len(items) / 3) * 3.8:.0f}s for 10 items")
        print(f"   With 5 browsers: ~{(len(items) / 5) * 3.8:.0f}s for 10 items")
        
    else:
        print("❌ One or both browsers failed")
        if not result1['success']:
            print(f"   Browser 1: {result1.get('error')}")
        if not result2['success']:
            print(f"   Browser 2: {result2.get('error')}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    test_parallel_persistent()

