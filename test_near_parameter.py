#!/usr/bin/env python3
"""
CRITICAL TEST: Does shopping.google.com respect near=ZIP for ANY user location?
Tests 3 very different locations to see if results change
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

# Test 3 very different US locations
TEST_LOCATIONS = [
    {"name": "Miami, FL", "zip": "33101", "expect": "Publix, Sedano's, Winn-Dixie"},
    {"name": "Los Angeles, CA", "zip": "90210", "expect": "Vons, Ralphs, Pavilions"},
    {"name": "Rural Texas", "zip": "79830", "expect": "H-E-B, Brookshire's"}
]


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
    
    plugin_file = 'near_test_proxy.zip'
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_file


def test_zipcode(location):
    """Test if shopping.google.com respects near= parameter"""
    
    print(f"\n{'='*80}")
    print(f"Testing: {location['name']} (ZIP {location['zip']})")
    print(f"Expected regional stores: {location['expect']}")
    print('='*80 + '\n')
    
    proxy_ext = create_proxy_extension()
    options = uc.ChromeOptions()
    options.add_extension(proxy_ext)
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
    
    try:
        # Use shopping.google.com with near parameter (NO CDP, NO geolocation)
        url = f'https://shopping.google.com/?hl=en&gl=us&near={location["zip"]}'
        print(f"Loading: {url}")
        driver.get(url)
        time.sleep(1)
        
        # Search for milk
        print("Searching for 'milk'...")
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys("milk")
        search_box.send_keys(Keys.ENTER)
        time.sleep(1.5)
        
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(0.5)
        
        # Parse
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        containers = soup.find_all('div', class_='gkQHve')
        
        products = []
        for title_elem in containers[:20]:
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
                
                if title and price and merchant:
                    products.append({
                        'title': title[:45],
                        'price': price,
                        'merchant': merchant
                    })
            except:
                pass
        
        driver.quit()
        
        if products:
            print(f"✅ Found {len(products)} products\n")
            
            # Show first 10
            for i, p in enumerate(products[:10], 1):
                print(f"{i:2}. ${p['price']:<6.2f} {p['merchant'][:20]:20} - {p['title'][:40]}")
            
            # Analyze merchants
            merchants = list(set(p['merchant'] for p in products))
            print(f"\n🏪 ALL MERCHANTS: {', '.join(merchants)}\n")
            
            return {
                'success': True,
                'products': products,
                'merchants': merchants,
                'unique_merchant_count': len(merchants)
            }
        else:
            print("❌ No products found")
            with open(f'near_test_{location["zip"]}.html', 'w') as f:
                f.write(html)
            print(f"Saved HTML to near_test_{location['zip']}.html")
            return {'success': False}
            
    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            driver.quit()
        except:
            pass
        return {'success': False, 'error': str(e)}


if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING: Does 'near=' parameter actually change results?")
    print("="*80)
    
    all_results = {}
    
    for location in TEST_LOCATIONS:
        result = test_zipcode(location)
        all_results[location['zip']] = result
        time.sleep(3)  # Wait between tests
    
    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS: Does location parameter work?")
    print("="*80 + "\n")
    
    successful = [k for k, v in all_results.items() if v.get('success')]
    
    if len(successful) >= 2:
        # Compare merchants between locations
        merchants_by_zip = {
            zip_code: set(result['merchants']) 
            for zip_code, result in all_results.items() 
            if result.get('success')
        }
        
        print("Merchants by ZIP code:")
        for zip_code, merchants in merchants_by_zip.items():
            print(f"  {zip_code}: {', '.join(list(merchants)[:5])}")
        
        # Check if merchants differ
        merchant_lists = list(merchants_by_zip.values())
        if len(merchant_lists) >= 2:
            overlap = merchant_lists[0].intersection(merchant_lists[1])
            unique_to_first = merchant_lists[0] - merchant_lists[1]
            unique_to_second = merchant_lists[1] - merchant_lists[0]
            
            print(f"\n📊 Comparison:")
            print(f"   Shared merchants: {len(overlap)}")
            print(f"   Unique to {list(merchants_by_zip.keys())[0]}: {len(unique_to_first)}")
            print(f"   Unique to {list(merchants_by_zip.keys())[1]}: {len(unique_to_second)}")
            
            if len(unique_to_first) > 0 or len(unique_to_second) > 0:
                print(f"\n✅ LOCATION PARAMETER WORKS!")
                print(f"   Different ZIP codes return different merchants!")
            else:
                print(f"\n⚠️  ALL MERCHANTS ARE THE SAME")
                print(f"   'near=' parameter might not be working")
                print(f"   Google is likely using proxy IP location instead")
    else:
        print("❌ Not enough successful tests to compare")
    
    print("\n" + "="*80 + "\n")

