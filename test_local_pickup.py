#!/usr/bin/env python3
"""
PROOF TEST: Filter by local pickup/delivery to verify actual local stores
Compare Miami vs LA to see genuinely different regional stores
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import re
import zipfile

PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = "lowCostGroceris_26SVt"
PROXY_PASS = "AppleID_1234"


def create_proxy_extension():
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
    
    plugin_file = 'local_test_proxy.zip'
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_file


def test_local_stores(zipcode, city_name):
    """Test with local pickup filter to prove location works"""
    
    print(f"\n{'='*80}")
    print(f"Testing: {city_name} (ZIP {zipcode})")
    print('='*80 + '\n')
    
    proxy_ext = create_proxy_extension()
    options = uc.ChromeOptions()
    options.add_extension(proxy_ext)
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
    
    try:
        # Load shopping with location
        url = f'https://shopping.google.com/?hl=en&gl=us&near={zipcode}'
        print(f"1. Loading: {url}")
        driver.get(url)
        time.sleep(1)
        
        # Search
        print("2. Searching for 'milk'...")
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys("milk")
        search_box.send_keys(Keys.ENTER)
        time.sleep(2)
        
        # Look for filters - try to click "Nearby" or similar
        print("3. Looking for local/nearby filters...")
        
        # Try to find and click filters
        try:
            # Look for "Nearby" or "Local" buttons/links
            filters = driver.find_elements(By.CSS_SELECTOR, "div[role='button'], button, a")
            for f in filters:
                text = f.text.lower()
                if 'nearby' in text or 'local' in text or 'pickup' in text or 'delivery' in text:
                    print(f"   Found filter: '{f.text}' - clicking...")
                    f.click()
                    time.sleep(2)
                    break
        except Exception as e:
            print(f"   No local filter found: {e}")
        
        # Scroll to load products
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)
        
        # Get page HTML
        html = driver.page_source
        
        # Save for inspection
        filename = f'local_test_{city_name.replace(" ", "_")}.html'
        with open(filename, 'w') as f:
            f.write(html)
        print(f"4. Saved HTML to {filename}")
        
        # Parse products
        soup = BeautifulSoup(html, 'html.parser')
        containers = soup.find_all('div', class_='gkQHve')
        
        products = []
        for title_elem in containers[:15]:
            try:
                title = title_elem.get_text(strip=True)
                parent = title_elem.find_parent('div', class_='PhALMc')
                if not parent:
                    continue
                
                # Get merchant
                merchant_elem = parent.find('span', class_='WJMUdc')
                merchant = merchant_elem.get_text(strip=True) if merchant_elem else None
                
                # Get price
                price_elem = parent.find('span', class_='lmQWe')
                price_text = price_elem.get_text(strip=True) if price_elem else None
                
                # Look for delivery/pickup indicators
                delivery_info = None
                delivery_elems = parent.find_all('span', class_='Ib8pOd')
                for elem in delivery_elems:
                    text = elem.get_text(strip=True)
                    if any(word in text.lower() for word in ['delivery', 'pickup', 'shipping', 'store', 'local']):
                        delivery_info = text
                        break
                
                if title and merchant:
                    products.append({
                        'title': title[:40],
                        'merchant': merchant,
                        'price': price_text,
                        'delivery_info': delivery_info
                    })
            except:
                pass
        
        driver.quit()
        
        # Display results
        print(f"\n5. Found {len(products)} products:\n")
        for i, p in enumerate(products[:10], 1):
            delivery = f" | {p['delivery_info']}" if p['delivery_info'] else ""
            print(f"{i:2}. {p['merchant'][:25]:25} - {p['title']}{delivery}")
        
        # Analyze merchants
        merchants = list(set(p['merchant'] for p in products))
        print(f"\n🏪 Unique merchants: {', '.join(merchants)}\n")
        
        return {
            'success': True,
            'products': products,
            'merchants': merchants,
            'zipcode': zipcode,
            'city': city_name
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            driver.quit()
        except:
            pass
        return {'success': False, 'error': str(e)}


if __name__ == "__main__":
    print("\n" + "="*80)
    print("PROOF TEST: Do different ZIP codes show different LOCAL stores?")
    print("="*80)
    
    # Test 2 very different locations
    locations = [
        {"zip": "33101", "city": "Miami, FL"},
        {"zip": "90210", "city": "Los Angeles, CA"}
    ]
    
    results = []
    for loc in locations:
        result = test_local_stores(loc['zip'], loc['city'])
        results.append(result)
        time.sleep(3)
    
    # Compare
    print("\n" + "="*80)
    print("COMPARISON: Are merchants different?")
    print("="*80 + "\n")
    
    if all(r.get('success') for r in results):
        miami_merchants = set(results[0]['merchants'])
        la_merchants = set(results[1]['merchants'])
        
        print(f"Miami merchants: {', '.join(list(miami_merchants)[:5])}")
        print(f"LA merchants: {', '.join(list(la_merchants)[:5])}")
        
        shared = miami_merchants.intersection(la_merchants)
        miami_only = miami_merchants - la_merchants
        la_only = la_merchants - miami_merchants
        
        print(f"\n📊 Analysis:")
        print(f"   Shared: {len(shared)} ({', '.join(list(shared)[:3])})")
        print(f"   Miami only: {len(miami_only)} ({', '.join(list(miami_only)[:3])})")
        print(f"   LA only: {len(la_only)} ({', '.join(list(la_only)[:3])})")
        
        if len(miami_only) > 0 or len(la_only) > 0:
            print(f"\n✅ VERIFIED: Different locations show different merchants!")
        else:
            print(f"\n⚠️  WARNING: All merchants are the same (national chains only)")
    else:
        print("❌ One or both tests failed")
    
    print("\n💡 Check the saved HTML files to see filter options available")
    print("="*80 + "\n")

