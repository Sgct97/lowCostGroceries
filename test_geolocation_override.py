#!/usr/bin/env python3
"""
Test if we can override proxy location with browser geolocation
Tests Miami (should show Publix) vs LA (should show Vons/Ralphs)
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import re
import zipfile
import json

PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = "lowCostGroceris_26SVt"
PROXY_PASS = "AppleID_1234"

# City coordinates for testing
LOCATIONS = {
    "Miami": {
        "latitude": 25.7617,
        "longitude": -80.1918,
        "zip": "33101",
        "expected_stores": ["Publix", "Sedano's", "Presidente", "Winn-Dixie"]
    },
    "Los Angeles": {
        "latitude": 34.0522,
        "longitude": -118.2437,
        "zip": "90210",
        "expected_stores": ["Vons", "Ralphs", "Pavilions", "Trader Joe's"]
    },
    "New York": {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "zip": "10001",
        "expected_stores": ["Whole Foods", "Key Food", "Fairway"]
    }
}


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
    
    plugin_file = 'geo_test_proxy.zip'
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_file


def test_location(city_name, location_data):
    """Test if geolocation override works for a specific city"""
    
    print(f"\n{'='*80}")
    print(f"Testing: {city_name} (ZIP {location_data['zip']})")
    print(f"Coordinates: {location_data['latitude']}, {location_data['longitude']}")
    print('='*80 + '\n')
    
    proxy_ext = create_proxy_extension()
    options = uc.ChromeOptions()
    options.add_extension(proxy_ext)
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
    
    try:
        # Set geolocation using CDP (Chrome DevTools Protocol)
        print("Setting geolocation override...")
        driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
            "latitude": location_data['latitude'],
            "longitude": location_data['longitude'],
            "accuracy": 100
        })
        
        # Use the correct Google Shopping URL format (www.google.com with udm=28)
        url = f"https://www.google.com/search?q=milk&udm=28&near={location_data['zip']}"
        print(f"Loading: {url}")
        driver.get(url)
        time.sleep(2)
        
        # Scroll to load products
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)
        
        # Parse products
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try multiple selectors
        containers = soup.find_all('div', class_='gkQHve')
        if not containers:
            containers = soup.find_all('div', class_='sh-dgr__content')
        
        print(f"Found {len(containers)} product containers\n")
        
        products = []
        for container in containers[:15]:
            try:
                # Try to extract title and merchant
                title_elem = container.find('div', class_='gkQHve') or container.find('h3') or container.find('span', class_='tAxDx')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                
                # Find merchant
                parent = container.find_parent('div', class_='PhALMc')
                if not parent:
                    parent = container
                
                merchant_elem = parent.find('span', class_='WJMUdc') or parent.find('div', class_='aULzUe')
                merchant = merchant_elem.get_text(strip=True) if merchant_elem else None
                
                # Find price
                price_elem = parent.find('span', class_='lmQWe') or parent.find('span', class_='a8Pemb')
                price_text = price_elem.get_text(strip=True) if price_elem else None
                
                if title and merchant:
                    products.append({'title': title[:50], 'merchant': merchant, 'price': price_text})
            except Exception as e:
                continue
        
        # Show results
        if products:
            print(f"✅ Found {len(products)} products:\n")
            for i, p in enumerate(products[:10], 1):
                print(f"{i:2}. {p['merchant']:25} - {p['title'][:40]}")
            
            # Check for expected regional stores
            merchants = [p['merchant'] for p in products]
            found_regional = [store for store in location_data['expected_stores'] if any(store.lower() in m.lower() for m in merchants)]
            
            print(f"\n🏪 All merchants: {', '.join(set(merchants))}")
            
            if found_regional:
                print(f"✅ REGIONAL STORES FOUND: {', '.join(found_regional)}")
                print(f"   → Geolocation override WORKS!")
            else:
                print(f"⚠️  Expected regional stores: {', '.join(location_data['expected_stores'])}")
                print(f"   → Only seeing national chains - geolocation may not be working")
            
            return {'success': True, 'merchants': merchants, 'regional_found': found_regional}
        else:
            print("❌ No products found - possible detection or parsing issue")
            # Save HTML for debugging
            with open(f'geo_test_{city_name.replace(" ", "_")}.html', 'w') as f:
                f.write(html)
            print(f"   Saved HTML to geo_test_{city_name.replace(' ', '_')}.html")
            return {'success': False}
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        driver.quit()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("GEOLOCATION OVERRIDE TEST")
    print("Testing if we can override proxy location for different US cities")
    print("="*80)
    
    results = {}
    
    # Test Miami (should show Publix - major Florida chain)
    results['Miami'] = test_location("Miami", LOCATIONS["Miami"])
    
    time.sleep(2)
    
    # Test Los Angeles (should show Vons/Ralphs - California chains)
    results['Los Angeles'] = test_location("Los Angeles", LOCATIONS["Los Angeles"])
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80 + "\n")
    
    for city, result in results.items():
        if result.get('success'):
            regional = result.get('regional_found', [])
            if regional:
                print(f"✅ {city}: Geolocation WORKS - Found {', '.join(regional)}")
            else:
                print(f"⚠️  {city}: Only national chains - geolocation may not override proxy")
        else:
            print(f"❌ {city}: Failed")
    
    print("\n" + "="*80 + "\n")

