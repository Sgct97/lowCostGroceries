#!/usr/bin/env python3
"""
TEST: Can we process multiple carts in parallel using tabs in ONE browser?

This could 3-5x our capacity if it doesn't trigger bot detection!

Tests:
1. Single tab (baseline)
2. 2 tabs (conservative)
3. 3 tabs (moderate)
4. 5 tabs (aggressive)

For each test we check:
- CAPTCHA detection
- Success rate
- Memory usage
- Time to complete
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import re
import logging
import psutil
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_memory_usage():
    """Get current process memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def parse_products(html):
    """Parse products from Google Shopping HTML using PROVEN method"""
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    
    # Find all product containers with aria-label (proven method)
    product_elements = soup.find_all(attrs={'aria-label': True})
    
    for element in product_elements:
        aria_label = element.get('aria-label', '')
        
        # Skip non-products
        if not aria_label or len(aria_label) < 10:
            continue
        if 'filter' in aria_label.lower() or 'button' in aria_label.lower():
            continue
        if '$' not in aria_label:
            continue
        
        try:
            # Extract price
            price_match = re.search(r'\$(\d+\.\d+|\d+)', aria_label)
            if not price_match:
                continue
            
            price = float(price_match.group(1))
            
            # Extract name
            parts = aria_label.split('.')
            product_name = parts[0].strip() if len(parts) > 0 else None
            
            # Extract merchant
            merchant = None
            for i, part in enumerate(parts):
                if '$' in part and i + 1 < len(parts):
                    candidate = parts[i + 1].strip()
                    if candidate and 'Rated' not in candidate and len(candidate) > 0:
                        merchant = candidate
                        break
            
            if product_name and price and merchant:
                products.append({
                    'name': product_name,
                    'price': price,
                    'merchant': merchant
                })
        
        except Exception as e:
            continue
    
    return products


def check_for_captcha(html):
    """Check if page shows CAPTCHA or bot detection"""
    indicators = [
        'recaptcha',
        'unusual traffic',
        'automated queries',
        'verify you are human',
        'security check'
    ]
    
    html_lower = html.lower()
    for indicator in indicators:
        if indicator in html_lower:
            return True
    
    return False


def test_single_tab(driver, search_term="milk", zip_code="33773"):
    """Baseline test: Single tab, single search (current working method)"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: SINGLE TAB (Baseline)")
    logger.info("="*80)
    
    mem_start = get_memory_usage()
    start_time = time.time()
    
    # Build URL (proven method from uc_scraper.py)
    query = f"{search_term} near zip {zip_code} nearby"
    import urllib.parse
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}&udm=28&shopmd=4"
    
    logger.info(f"Loading: {url}")
    driver.get(url)
    time.sleep(2)
    
    # Scroll to load products
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(0.5)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(0.5)
    
    # Check for CAPTCHA
    html = driver.page_source
    if check_for_captcha(html):
        logger.error("❌ CAPTCHA detected!")
        return {'success': False, 'captcha': True}
    
    # Parse products
    products = parse_products(html)
    elapsed = time.time() - start_time
    mem_end = get_memory_usage()
    
    logger.info(f"✅ SUCCESS")
    logger.info(f"   Products found: {len(products)}")
    if products:
        logger.info(f"   Sample: {products[0]['name'][:40]}... ${products[0]['price']} @ {products[0]['merchant']}")
    logger.info(f"   Time: {elapsed:.1f}s")
    logger.info(f"   Memory: {mem_end:.1f}MB (delta: +{mem_end - mem_start:.1f}MB)")
    
    return {
        'success': True,
        'captcha': False,
        'products': len(products),
        'time': elapsed,
        'memory_mb': mem_end - mem_start
    }


def test_multi_tab(driver, num_tabs=3, zip_code="33773"):
    """Test multiple tabs processing different searches in parallel"""
    logger.info("\n" + "="*80)
    logger.info(f"TEST: {num_tabs} TABS IN PARALLEL")
    logger.info("="*80)
    
    # Different search terms for each tab
    searches = ['milk', 'eggs', 'bread', 'chicken', 'rice'][:num_tabs]
    
    mem_start = get_memory_usage()
    start_time = time.time()
    
    # STEP 1: Open ALL tabs first (don't load URLs yet)
    logger.info("STEP 1: Opening all tabs...")
    tabs = []
    
    for i, search_term in enumerate(searches):
        if i == 0:
            # Use current window for first tab
            tab_handle = driver.current_window_handle
            logger.info(f"  Tab 1: Using main window (handle: {tab_handle[:8]}...)")
        else:
            # Open new tab
            logger.info(f"  Tab {i+1}: Opening new tab...")
            initial_count = len(driver.window_handles)
            
            driver.switch_to.new_window('tab')
            time.sleep(0.3)
            
            new_count = len(driver.window_handles)
            tab_handle = driver.current_window_handle
            
            if new_count <= initial_count:
                logger.error(f"❌ Failed to open tab {i+1}! Handles: {initial_count} -> {new_count}")
                return {
                    'num_tabs': num_tabs,
                    'success_count': 0,
                    'captcha_count': 0,
                    'total_products': 0,
                    'time': 0,
                    'time_per_search': 0,
                    'memory_delta_mb': 0,
                    'memory_per_tab_mb': 0,
                    'viable': False
                }
            
            logger.info(f"  Tab {i+1}: ✅ Opened (handle: {tab_handle[:8]}..., total tabs: {new_count})")
        
        # Build URL
        query = f"{search_term} near zip {zip_code} nearby"
        import urllib.parse
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}&udm=28&shopmd=4"
        
        tabs.append({
            'handle': tab_handle,
            'search': search_term,
            'url': url
        })
    
    logger.info(f"✅ All {num_tabs} tabs opened!")
    
    # STEP 2: Start loading ALL URLs as fast as possible!
    logger.info("STEP 2: Starting to load all URLs in parallel...")
    load_start = time.time()
    
    for i, tab_info in enumerate(tabs):
        iter_start = time.time()
        driver.switch_to.window(tab_info['handle'])
        switch_time = time.time() - iter_start
        
        # Use setTimeout so JavaScript returns IMMEDIATELY and navigates async!
        driver.execute_script(f"setTimeout(function() {{ window.location.href = '{tab_info['url']}'; }}, 1);")
        nav_time = time.time() - iter_start - switch_time
        
        elapsed_from_start = time.time() - load_start
        logger.info(f"  Tab {i+1} ({tab_info['search']}): Load started at +{elapsed_from_start:.3f}s (switch: {switch_time:.3f}s, nav: {nav_time:.3f}s)")
        # NO SLEEP - start next one immediately!
    
    # STEP 3: Wait for all pages to load
    logger.info(f"STEP 3: All tabs now loading in parallel! Waiting for them to finish...")
    time.sleep(5)  # Give them all time to load
    
    # Wait for all pages to load
    logger.info(f"Waiting for {num_tabs} tabs to load...")
    time.sleep(3)
    
    # Now check each tab for CAPTCHA and parse products
    results = []
    captcha_count = 0
    
    for i, tab_info in enumerate(tabs):
        logger.info(f"\n--- Checking Tab {i+1} ({tab_info['search']}) ---")
        logger.info(f"   Switching to handle: {tab_info['handle'][:8]}...")
        driver.switch_to.window(tab_info['handle'])
        
        # Verify we're on the right tab by checking the URL
        current_url = driver.current_url
        logger.info(f"   Current URL: {current_url[:80]}...")
        
        # Scroll to load lazy products
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(0.3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.3)
        
        html = driver.page_source
        
        # Check for CAPTCHA
        if check_for_captcha(html):
            logger.error(f"❌ Tab {i+1} ({tab_info['search']}): CAPTCHA DETECTED!")
            captcha_count += 1
            results.append({
                'search': tab_info['search'],
                'captcha': True,
                'products': 0
            })
        else:
            # Parse products
            products = parse_products(html)
            logger.info(f"✅ Tab {i+1} ({tab_info['search']}): {len(products)} products")
            if products:
                logger.info(f"      Sample: {products[0]['name'][:35]}... ${products[0]['price']}")
            
            results.append({
                'search': tab_info['search'],
                'captcha': False,
                'products': len(products)
            })
    
    elapsed = time.time() - start_time
    mem_end = get_memory_usage()
    
    # Summary
    success_count = sum(1 for r in results if not r['captcha'] and r['products'] > 0)
    total_products = sum(r['products'] for r in results)
    
    logger.info(f"\n📊 SUMMARY:")
    logger.info(f"   Tabs: {num_tabs}")
    logger.info(f"   Successful: {success_count}/{num_tabs}")
    logger.info(f"   CAPTCHAs: {captcha_count}/{num_tabs}")
    logger.info(f"   Total products: {total_products}")
    logger.info(f"   Time: {elapsed:.1f}s ({elapsed/num_tabs:.1f}s per search)")
    logger.info(f"   Memory: {mem_end:.1f}MB (delta: +{mem_end - mem_start:.1f}MB)")
    logger.info(f"   Memory per tab: {(mem_end - mem_start)/num_tabs:.1f}MB")
    
    # Close extra tabs (keep first one open)
    try:
        current_handles = driver.window_handles
        for i in range(len(tabs) - 1, 0, -1):
            try:
                if tabs[i]['handle'] in current_handles:
                    driver.switch_to.window(tabs[i]['handle'])
                    driver.close()
                    time.sleep(0.2)
            except Exception as e:
                logger.debug(f"Could not close tab {i}: {e}")
        
        # Switch back to main window if it still exists
        current_handles = driver.window_handles
        if len(current_handles) > 0:
            driver.switch_to.window(current_handles[0])
    except Exception as e:
        logger.debug(f"Error during tab cleanup: {e}")
    
    return {
        'num_tabs': num_tabs,
        'success_count': success_count,
        'captcha_count': captcha_count,
        'total_products': total_products,
        'time': elapsed,
        'time_per_search': elapsed / num_tabs,
        'memory_delta_mb': mem_end - mem_start,
        'memory_per_tab_mb': (mem_end - mem_start) / num_tabs,
        'viable': (captcha_count == 0 and success_count == num_tabs)
    }


def main():
    """Run all tests"""
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║          MULTI-TAB PARALLEL PROCESSING TEST                          ║
    ║                                                                      ║
    ║  Testing if we can process multiple carts in parallel using tabs    ║
    ║  in ONE browser without triggering Google's bot detection.          ║
    ║                                                                      ║
    ║  If this works, we can 3-5x our capacity! 🚀                        ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    logger.info(f"Initial memory: {get_memory_usage():.1f}MB")
    logger.info("Starting Chrome...")
    
    # Setup Chrome with proven options
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Check if running on server (use xvfb)
    use_xvfb = os.environ.get('DISPLAY') is None or os.environ.get('XVFB') == '1'
    if use_xvfb:
        logger.info("Running with Xvfb (headless server mode)")
    
    try:
        driver = uc.Chrome(options=options, use_subprocess=False)
        logger.info("✅ Chrome started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start Chrome: {e}")
        return
    
    all_results = []
    
    try:
        # Test 1: Single tab (baseline)
        result_1tab = test_single_tab(driver)
        all_results.append(('1 tab', result_1tab))
        time.sleep(2)
        
        # Test 2: 2 tabs
        result_2tabs = test_multi_tab(driver, num_tabs=2)
        all_results.append(('2 tabs', result_2tabs))
        time.sleep(2)
        
        # Test 3: 3 tabs
        result_3tabs = test_multi_tab(driver, num_tabs=3)
        all_results.append(('3 tabs', result_3tabs))
        time.sleep(2)
        
        # Test 4: 5 tabs (aggressive)
        result_5tabs = test_multi_tab(driver, num_tabs=5)
        all_results.append(('5 tabs', result_5tabs))
        
    finally:
        logger.info("\nClosing browser...")
        driver.quit()
    
    # Final analysis
    print("\n" + "="*80)
    print("🎯 FINAL ANALYSIS")
    print("="*80)
    
    print("\n📊 Results Summary:")
    print(f"{'Configuration':<15} {'Time':<10} {'Products':<12} {'CAPTCHAs':<10} {'Viable?':<10}")
    print("-" * 80)
    
    for config, result in all_results:
        if config == '1 tab':
            time_str = f"{result['time']:.1f}s"
            products_str = str(result['products'])
            captcha_str = "Yes" if result['captcha'] else "No"
            viable_str = "✅ Yes" if result['success'] else "❌ No"
        else:
            time_str = f"{result['time']:.1f}s"
            products_str = str(result['total_products'])
            captcha_str = str(result['captcha_count'])
            viable_str = "✅ Yes" if result['viable'] else "❌ No"
        
        print(f"{config:<15} {time_str:<10} {products_str:<12} {captcha_str:<10} {viable_str:<10}")
    
    # Recommendations
    print("\n" + "="*80)
    print("💡 RECOMMENDATIONS")
    print("="*80)
    
    viable_configs = [(config, result) for config, result in all_results[1:] if result.get('viable', False)]
    
    if not viable_configs:
        print("\n❌ Multi-tab approach FAILED - Google detected it")
        print("   Recommendation: Stick with single-tab sequential processing")
        print("   Deploy: 2 workers per 2GB droplet (proven safe)")
        print("   Cost: 25 droplets × $12 = $300/month for 50 workers")
    else:
        # Find best config
        best_config, best_result = max(viable_configs, key=lambda x: x[1]['num_tabs'])
        
        print(f"\n✅ Multi-tab approach WORKS! Best: {best_config}")
        print(f"   Time per search: {best_result['time_per_search']:.1f}s")
        print(f"   Memory per tab: {best_result['memory_per_tab_mb']:.0f}MB")
        print(f"   No CAPTCHAs detected!")
        
        # Calculate capacity gains
        num_tabs = best_result['num_tabs']
        speedup = num_tabs / best_result['time_per_search']
        
        print(f"\n📈 CAPACITY GAINS:")
        print(f"   Single tab: 1 cart in {best_result['time']:.1f}s")
        print(f"   {num_tabs} tabs: {num_tabs} carts in {best_result['time']:.1f}s")
        print(f"   Speedup: {speedup:.1f}x faster!")
        
        # Memory requirements
        total_mem_mb = 300 + best_result['memory_delta_mb']  # Base Chrome + tabs
        
        if total_mem_mb < 1800:
            print(f"\n💰 DEPLOYMENT RECOMMENDATION:")
            print(f"   Use 2GB droplets with 1 worker and {num_tabs} tabs each")
            print(f"   Total memory: {total_mem_mb:.0f}MB (safe for 2GB)")
            print(f"   Workers needed: 50 / {num_tabs} = {int(50/num_tabs)} workers")
            print(f"   Droplets needed: {int(50/num_tabs)} × $12 = ${int(50/num_tabs)*12}/month")
            print(f"   SAVINGS: ${300 - int(50/num_tabs)*12}/month vs sequential!")
        else:
            print(f"\n💰 DEPLOYMENT RECOMMENDATION:")
            print(f"   Use 4GB droplets with 1 worker and {num_tabs} tabs each")
            print(f"   Total memory: {total_mem_mb:.0f}MB (safe for 4GB)")
            print(f"   Workers needed: 50 / {num_tabs} = {int(50/num_tabs)} workers")
            print(f"   Droplets needed: {int(50/num_tabs)} × $24 = ${int(50/num_tabs)*24}/month")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()

