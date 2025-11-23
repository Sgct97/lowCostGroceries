#!/usr/bin/env python3
"""
PROPER TEST: Multi-tab cart processing vs Sequential cart processing

This tests the REAL use case: Processing multiple user carts
- Multi-tab: 5 tabs, each processes 1 complete cart (5 items)
- Sequential: 1 tab processes 5 complete carts (5 items each)

Each cart = 5 items: milk, eggs, bread, chicken, rice
Max 30 products per item
"""

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import re
import logging
import urllib.parse
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CART_ITEMS = ['milk', 'eggs', 'bread', 'chicken', 'rice']
ZIP_CODE = '33773'
MAX_PRODUCTS = 30

# Use persistent Chrome profile with pre-installed Oxylabs extension
CHROME_PROFILE = "/root/.chrome_scraper_profile"
# Extension already installed - DO NOT load it dynamically!


def parse_products(html):
    """Parse products from HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    
    product_elements = soup.find_all(attrs={'aria-label': True})
    
    for element in product_elements:
        aria_label = element.get('aria-label', '')
        
        if not aria_label or len(aria_label) < 10:
            continue
        if 'filter' in aria_label.lower() or 'button' in aria_label.lower():
            continue
        if '$' not in aria_label:
            continue
        
        try:
            price_match = re.search(r'\$(\d+\.\d+|\d+)', aria_label)
            if not price_match:
                continue
            
            price = float(price_match.group(1))
            parts = aria_label.split('.')
            product_name = parts[0].strip() if len(parts) > 0 else None
            
            if product_name and price:
                products.append({'name': product_name, 'price': price})
        except:
            continue
    
    return products[:MAX_PRODUCTS]


def process_cart_in_tab(driver, cart_id, tab_handle):
    """Process one complete cart (5 items) in a specific tab"""
    logger.info(f"\n{'='*60}")
    logger.info(f"CART {cart_id}: Processing in tab {tab_handle[:8]}...")
    logger.info(f"{'='*60}")
    
    driver.switch_to.window(tab_handle)
    cart_start = time.time()
    cart_results = {}
    
    for i, item in enumerate(CART_ITEMS):
        item_start = time.time()
        
        # Build URL - force US region
        query = f"{item} near zip {ZIP_CODE} nearby"
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}&udm=28&shopmd=4&gl=us&hl=en"
        
        # Load page
        if i == 0:
            driver.get(url)
            time.sleep(2)  # First load takes longer
            # Handle cookie consent popup on first load
            try:
                accept_btn = driver.find_element('xpath', '//button[contains(text(), "Accept") or contains(text(), "Aceptar")]')
                accept_btn.click()
                logger.info("  Dismissed cookie popup")
                time.sleep(1)
            except:
                pass  # No popup
        else:
            driver.get(url)
            time.sleep(1)  # Subsequent loads faster
        
        # Parse products
        html = driver.page_source
        products = parse_products(html)
        cart_results[item] = products
        
        item_elapsed = time.time() - item_start
        logger.info(f"  Cart {cart_id} - Item {i+1}/5 ({item}): {len(products)} products ({item_elapsed:.1f}s)")
    
    cart_elapsed = time.time() - cart_start
    total_products = sum(len(p) for p in cart_results.values())
    
    logger.info(f"✅ Cart {cart_id} COMPLETE: {total_products} total products in {cart_elapsed:.1f}s")
    
    return {
        'cart_id': cart_id,
        'results': cart_results,
        'time': cart_elapsed,
        'total_products': total_products
    }


def test_multi_tab_parallel():
    """Test: Process 5 carts in TRULY parallel using 5 tabs"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: MULTI-TAB TRULY PARALLEL (5 carts in 5 tabs)")
    logger.info("="*80)
    logger.info("✅ Using persistent profile with pre-installed Oxylabs extension!")
    
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE}")
    options.add_argument("--start-maximized")
    # Force US locale to prevent EU cookie popup
    options.add_argument("--lang=en-US")
    options.add_experimental_option('prefs', {
        'intl.accept_languages': 'en-US,en',
        'profile.default_content_setting_values.geolocation': 1
    })
    
    driver = uc.Chrome(options=options, use_subprocess=False, version_main=None)
    logger.info("✅ Using Oxylabs proxy with forced US locale")
    
    start_time = time.time()
    
    # Open 5 tabs
    tabs = []
    for i in range(5):
        if i == 0:
            tab_handle = driver.current_window_handle
        else:
            driver.switch_to.new_window('tab')
            time.sleep(0.3)
            tab_handle = driver.current_window_handle
        
        tabs.append({
            'cart_id': i + 1,
            'handle': tab_handle
        })
        logger.info(f"Tab {i+1} opened for Cart {i+1}")
    
    logger.info(f"\n✅ All 5 tabs opened, starting TRULY PARALLEL processing...")
    
    # TRUE PARALLEL: All tabs load same item at same time
    cart_results = {i: {} for i in range(1, 6)}
    
    for item_idx, item in enumerate(CART_ITEMS):
        logger.info(f"\n--- ALL TABS: Loading '{item}' (item {item_idx+1}/5) ---")
        
        # STEP 1: Start loading item in ALL tabs simultaneously
        query = f"{item} near zip {ZIP_CODE} nearby"
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}&udm=28&shopmd=4&gl=us&hl=en"
        
        item_start = time.time()
        
        # Handle cookie popup on first item only
        if item_idx == 0:
            driver.switch_to.window(tabs[0]['handle'])
            driver.get(url)
            time.sleep(2)
            try:
                accept_btn = driver.find_element('xpath', '//button[contains(text(), "Accept") or contains(text(), "Aceptar")]')
                accept_btn.click()
                logger.info("  Dismissed cookie popup")
                time.sleep(1)
            except:
                pass  # No popup
        
        for tab_info in tabs:
            driver.switch_to.window(tab_info['handle'])
            # Use setTimeout so it returns immediately!
            driver.execute_script(f"setTimeout(function() {{ window.location.href = '{url}'; }}, 1);")
        
        logger.info(f"  All 5 tabs started loading '{item}' simultaneously")
        time.sleep(3)  # Wait for all to load
        
        # STEP 2: Parse from ALL tabs
        for tab_info in tabs:
            driver.switch_to.window(tab_info['handle'])
            html = driver.page_source
            products = parse_products(html)
            cart_results[tab_info['cart_id']][item] = products
            logger.info(f"  Cart {tab_info['cart_id']}: {len(products)} products for '{item}'")
        
        item_elapsed = time.time() - item_start
        logger.info(f"  ✅ All 5 carts got '{item}' in {item_elapsed:.1f}s")
    
    # Build results
    results = []
    for cart_id, items in cart_results.items():
        total_products = sum(len(p) for p in items.values())
        results.append({
            'cart_id': cart_id,
            'results': items,
            'total_products': total_products
        })
    
    total_time = time.time() - start_time
    total_products = sum(r['total_products'] for r in results)
    
    driver.quit()
    
    logger.info(f"\n{'='*80}")
    logger.info(f"MULTI-TAB RESULTS:")
    logger.info(f"  5 carts processed in: {total_time:.1f}s")
    logger.info(f"  Total products: {total_products}")
    logger.info(f"  Average per cart: {total_time/5:.1f}s")
    logger.info(f"{'='*80}\n")
    
    return {
        'method': 'multi-tab',
        'total_time': total_time,
        'total_products': total_products,
        'carts': 5
    }


def test_sequential():
    """Test: Process 5 carts sequentially in 1 tab"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: SEQUENTIAL (5 carts in 1 tab)")
    logger.info("="*80)
    logger.info("✅ Using persistent profile with pre-installed Oxylabs extension!")
    
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE}")
    options.add_argument("--start-maximized")
    # Force US locale to prevent EU cookie popup
    options.add_argument("--lang=en-US")
    options.add_experimental_option('prefs', {
        'intl.accept_languages': 'en-US,en',
        'profile.default_content_setting_values.geolocation': 1
    })
    
    driver = uc.Chrome(options=options, use_subprocess=False, version_main=None)
    logger.info("✅ Using Oxylabs proxy with forced US locale")
    
    start_time = time.time()
    tab_handle = driver.current_window_handle
    
    results = []
    for cart_id in range(1, 6):
        result = process_cart_in_tab(driver, cart_id, tab_handle)
        results.append(result)
    
    total_time = time.time() - start_time
    total_products = sum(r['total_products'] for r in results)
    
    driver.quit()
    
    logger.info(f"\n{'='*80}")
    logger.info(f"SEQUENTIAL RESULTS:")
    logger.info(f"  5 carts processed in: {total_time:.1f}s")
    logger.info(f"  Total products: {total_products}")
    logger.info(f"  Average per cart: {total_time/5:.1f}s")
    logger.info(f"{'='*80}\n")
    
    return {
        'method': 'sequential',
        'total_time': total_time,
        'total_products': total_products,
        'carts': 5
    }


def main():
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║     MULTI-TAB vs SEQUENTIAL CART PROCESSING TEST                 ║
    ║                                                                  ║
    ║  This tests the REAL question:                                  ║
    ║  Can we process multiple USER CARTS faster using tabs?          ║
    ║                                                                  ║
    ║  Each cart = 5 items (milk, eggs, bread, chicken, rice)        ║
    ║  Testing 5 carts total                                          ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Proxychains handles proxy at system level - no setup needed!
    
    try:
        # Test sequential first (baseline)
        sequential_result = test_sequential()
        
        time.sleep(5)  # Cool down
        
        # Test multi-tab
        multi_tab_result = test_multi_tab_parallel()
        
        # Compare
        print("\n" + "="*80)
        print("🏆 FINAL COMPARISON")
        print("="*80)
        print(f"\nSEQUENTIAL:")
        print(f"  Time: {sequential_result['total_time']:.1f}s")
        print(f"  Products: {sequential_result['total_products']}")
        print(f"  Per cart: {sequential_result['total_time']/5:.1f}s")
        
        print(f"\nMULTI-TAB:")
        print(f"  Time: {multi_tab_result['total_time']:.1f}s")
        print(f"  Products: {multi_tab_result['total_products']}")
        print(f"  Per cart: {multi_tab_result['total_time']/5:.1f}s")
        
        speedup = sequential_result['total_time'] / multi_tab_result['total_time']
        
        print(f"\n📊 VERDICT:")
        if speedup > 1.1:
            print(f"  ✅ Multi-tab is {speedup:.1f}x FASTER!")
            print(f"  ✅ Multi-tab saves {sequential_result['total_time'] - multi_tab_result['total_time']:.1f} seconds!")
            print(f"\n💡 DEPLOY WITH MULTI-TAB!")
        elif speedup < 0.9:
            print(f"  ❌ Multi-tab is {1/speedup:.1f}x SLOWER!")
            print(f"  ❌ Multi-tab wastes {multi_tab_result['total_time'] - sequential_result['total_time']:.1f} seconds!")
            print(f"\n💡 STICK WITH SEQUENTIAL!")
        else:
            print(f"  ⚖️  About the same (difference: {abs(sequential_result['total_time'] - multi_tab_result['total_time']):.1f}s)")
            print(f"\n💡 STICK WITH SEQUENTIAL (simpler)")
        
        print("="*80 + "\n")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    main()

