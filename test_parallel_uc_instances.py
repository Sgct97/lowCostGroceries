#!/usr/bin/env python3
"""
TEST: Can we run 2-3 UC instances in PARALLEL on the same machine?

Uses the EXACT same setup as capture_xhr_requests.py that WORKS!
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import logging
import zipfile
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = "lowCostGroceris_26SVt"
PROXY_PASS = "AppleID_1234"


def create_proxy_extension(browser_id):
    """Create Chrome extension for Oxylabs auth - SAME AS WORKING SCRIPT"""
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Proxy Auth",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
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
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

    plugin_file = f'proxy_auth_plugin_{browser_id}_{os.getpid()}.zip'
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_file


def get_memory_usage():
    """Get current process memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def search_with_uc(browser_id: int, query: str):
    """
    Run a single UC browser instance and do a search
    EXACT SAME SETUP AS capture_xhr_requests.py
    """
    logger.info(f"[Browser {browser_id}] Starting UC instance for '{query}'")
    start_time = time.time()
    
    try:
        # Create unique proxy extension for this instance
        proxy_extension = create_proxy_extension(browser_id)
        
        # EXACT SAME OPTIONS AS WORKING SCRIPT
        options = uc.ChromeOptions()
        options.add_extension(proxy_extension)
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--lang=en-US')
        options.add_experimental_option('prefs', {'intl.accept_languages': 'en-US,en'})
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        # CRITICAL: Each instance needs completely isolated directories
        timestamp = int(time.time() * 1000)  # Use milliseconds for uniqueness
        user_data_dir = f'/tmp/uc_userdata_{browser_id}_{timestamp}'
        options.add_argument(f'--user-data-dir={user_data_dir}')
        
        # Isolate each instance's process
        options.add_argument(f'--remote-debugging-port={9222 + browser_id}')
        
        mem_before = get_memory_usage()
        logger.info(f"[Browser {browser_id}] Memory before launch: {mem_before:.1f} MB")
        logger.info(f"[Browser {browser_id}] Using user data: {user_data_dir}")
        logger.info(f"[Browser {browser_id}] Using debug port: {9222 + browser_id}")
        
        # Let UC handle its own driver management, but use unique subprocess
        driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            version_main=None
        )
        
        mem_after_launch = get_memory_usage()
        logger.info(f"[Browser {browser_id}] Memory after launch: {mem_after_launch:.1f} MB (+{mem_after_launch - mem_before:.1f} MB)")
        
        # Navigate to Google Shopping
        logger.info(f"[Browser {browser_id}] Loading shopping.google.com...")
        driver.get("https://shopping.google.com/?hl=en&gl=us")
        time.sleep(3)
        
        # Search (SIMPLE AND FAST - like test_uc_session_reuse.py)
        logger.info(f"[Browser {browser_id}] Searching for '{query}'...")
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(query)
        search_box.send_keys(Keys.ENTER)
        
        logger.info(f"[Browser {browser_id}] Waiting for page load...")
        time.sleep(5)
        
        # Scroll 3 times (efficient scrolling like test_uc_session_reuse.py)
        logger.info(f"[Browser {browser_id}] Scrolling...")
        for i in range(1, 4):
            driver.execute_script(f"window.scrollTo(0, {i * 800});")
            time.sleep(2)
        
        # Parse products from HTML using YOUR EXACT PARSING LOGIC
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find product containers (YOUR parsing code from parse_shopping.py)
        product_containers = soup.find_all('div', class_='liKJmf')
        
        products = []
        for container in product_containers[:5]:  # Parse first 5
            try:
                # Title
                title_elem = container.find('div', class_='gkQHve')
                title = title_elem.get_text(strip=True) if title_elem else None
                
                # Price
                price_elem = container.find('span', class_='lmQWe')
                price_text = price_elem.get_text(strip=True) if price_elem else None
                price = None
                if price_text:
                    match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                    if match:
                        price = float(match.group(1).replace(',', ''))
                
                # Merchant
                merchant_elem = container.find('span', class_='WJMUdc')
                merchant = merchant_elem.get_text(strip=True) if merchant_elem else None
                
                if title and price:
                    products.append({
                        'title': title,
                        'price': price,
                        'merchant': merchant
                    })
            except Exception as e:
                logger.debug(f"[Browser {browser_id}] Error parsing product: {e}")
        
        product_count = len(product_containers)
        
        elapsed = time.time() - start_time
        mem_final = get_memory_usage()
        
        logger.info(f"[Browser {browser_id}] ✅ SUCCESS!")
        logger.info(f"[Browser {browser_id}]    Products found: {product_count}")
        logger.info(f"[Browser {browser_id}]    Parsed with prices: {len(products)}")
        if products:
            logger.info(f"[Browser {browser_id}]    Sample: {products[0]['title'][:50]}... ${products[0]['price']} @ {products[0]['merchant']}")
        logger.info(f"[Browser {browser_id}]    Time: {elapsed:.1f}s")
        logger.info(f"[Browser {browser_id}]    Final memory: {mem_final:.1f} MB")
        
        driver.quit()
        
        # Cleanup
        try:
            os.remove(proxy_extension)
        except:
            pass
        
        return {
            'browser_id': browser_id,
            'query': query,
            'success': True,
            'products_found': product_count,
            'products_parsed': len(products),
            'sample_products': products[:3],
            'time_seconds': elapsed,
            'memory_mb': mem_final - mem_before
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[Browser {browser_id}] ❌ FAILED: {e}")
        
        try:
            driver.quit()
        except:
            pass
        
        return {
            'browser_id': browser_id,
            'query': query,
            'success': False,
            'error': str(e),
            'time_seconds': elapsed
        }


def test_parallel_instances(num_browsers=3):
    """Test running multiple UC instances in parallel"""
    
    queries = ['milk', 'eggs', 'bread', 'butter', 'cheese'][:num_browsers]
    
    logger.info("="*80)
    logger.info(f"🧪 TESTING {num_browsers} PARALLEL UC INSTANCES")
    logger.info("="*80)
    logger.info(f"Queries: {queries}")
    logger.info(f"Initial memory: {get_memory_usage():.1f} MB\n")
    
    start_time = time.time()
    results = []
    
    # Run browsers in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=num_browsers) as executor:
        futures = {
            executor.submit(search_with_uc, i, query): (i, query) 
            for i, query in enumerate(queries, 1)
        }
        
        for future in as_completed(futures):
            browser_id, query = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Browser {browser_id} crashed: {e}")
                results.append({
                    'browser_id': browser_id,
                    'query': query,
                    'success': False,
                    'error': f"Crashed: {e}"
                })
    
    total_time = time.time() - start_time
    final_memory = get_memory_usage()
    
    # Print results
    logger.info("\n" + "="*80)
    logger.info("📊 RESULTS")
    logger.info("="*80)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    logger.info(f"\n✅ Successful: {len(successful)}/{num_browsers}")
    logger.info(f"❌ Failed: {len(failed)}/{num_browsers}")
    logger.info(f"\n⏱️  Total time: {total_time:.1f}s")
    logger.info(f"📊 Final memory: {final_memory:.1f} MB")
    
    if successful:
        avg_time = sum(r['time_seconds'] for r in successful) / len(successful)
        max_time = max(r['time_seconds'] for r in successful)
        avg_memory = sum(r.get('memory_mb', 0) for r in successful) / len(successful)
        
        logger.info(f"\n📈 Stats for successful browsers:")
        logger.info(f"   Average time per search: {avg_time:.1f}s")
        logger.info(f"   Slowest search: {max_time:.1f}s")
        logger.info(f"   Average memory per browser: {avg_memory:.1f} MB")
        logger.info(f"   Total memory increase: {final_memory - get_memory_usage():.1f} MB")
    
    logger.info("\n" + "="*80)
    logger.info("DETAILED RESULTS")
    logger.info("="*80)
    
    for r in results:
        status = "✅" if r['success'] else "❌"
        logger.info(f"\n{status} Browser {r['browser_id']} - {r['query']}")
        if r['success']:
            logger.info(f"   Time: {r['time_seconds']:.1f}s")
            logger.info(f"   Products found: {r['products_found']}")
            logger.info(f"   Products with prices: {r['products_parsed']}")
            logger.info(f"   Memory: {r.get('memory_mb', 0):.1f} MB")
            if r.get('sample_products'):
                logger.info(f"   Sample products:")
                for p in r['sample_products'][:2]:
                    logger.info(f"      • {p.get('title', 'N/A')[:40]}... ${p.get('price', 'N/A')} @ {p.get('merchant', 'N/A')}")
        else:
            logger.info(f"   Error: {r.get('error', 'Unknown')}")
    
    # CONCLUSION
    logger.info("\n" + "="*80)
    logger.info("🎯 CONCLUSION")
    logger.info("="*80)
    
    if len(successful) == num_browsers:
        products_parsed = sum(r.get('products_parsed', 0) for r in successful)
        logger.info(f"\n🎉 SUCCESS! All {num_browsers} UC instances ran in parallel!")
        logger.info(f"✅ Total time: {total_time:.1f}s (vs {avg_time * num_browsers:.1f}s sequential)")
        logger.info(f"✅ Speedup: {(avg_time * num_browsers / total_time):.1f}x")
        logger.info(f"✅ Total products parsed: {products_parsed}")
        
        if products_parsed > 0:
            logger.info(f"\n🎉🎉🎉 PERFECT! Parallel scraping with real product data works!")
            logger.info(f"💡 RECOMMENDATION: Use {num_browsers} persistent browsers per droplet")
            logger.info(f"💡 For 10 items: ~{(avg_time * 10 / num_browsers):.0f} seconds with {num_browsers} browsers")
        else:
            logger.info(f"\n⚠️  No products parsed. Possible issues:")
            logger.info(f"    - Proxy blocking")
            logger.info(f"    - HTML structure changed")
            logger.info(f"    - Need longer wait time")
    elif len(successful) > 0:
        logger.info(f"\n⚠️  PARTIAL SUCCESS: {len(successful)}/{num_browsers} worked")
        logger.info(f"💡 RECOMMENDATION: Use {len(successful)} browsers per droplet (safer)")
    else:
        logger.info(f"\n❌ FAILURE: Could not run multiple UC instances in parallel")
        logger.info(f"💡 RECOMMENDATION: Use sequential processing or investigate errors")
    
    return results


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║          TESTING PARALLEL UC INSTANCES                               ║
    ║                                                                      ║
    ║  This will test if we can run 2-3 UC browsers simultaneously        ║
    ║  on the same machine using the EXACT setup that works.              ║
    ║                                                                      ║
    ║  What we're testing:                                                ║
    ║  - Can multiple UC instances run at once?                           ║
    ║  - How much RAM does each use?                                      ║
    ║  - What's the total time vs sequential?                             ║
    ║  - Do they crash or interfere with each other?                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Test with 2 instances first (safer)
    logger.info("Starting with 2 instances...\n")
    test_parallel_instances(num_browsers=2)
    
    time.sleep(5)
    
    # If user wants to test 3
    response = input("\n\nTest with 3 instances? (y/n): ")
    if response.lower() == 'y':
        test_parallel_instances(num_browsers=3)

