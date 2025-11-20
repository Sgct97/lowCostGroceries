#!/usr/bin/env python3
"""
CRITICAL TEST: Try all known methods to override Google Shopping location
Based on successful Google Maps coordinate approach
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import zipfile
import pgeocode

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
    
    plugin_file = 'location_override_test.zip'
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_file


def test_url_pattern(url_name, url, target_zip, target_city, target_state):
    """Test a single URL pattern and check if location override works"""
    
    print(f"\n{'='*80}")
    print(f"Testing: {url_name}")
    print(f"URL: {url}")
    print('='*80)
    
    proxy_ext = create_proxy_extension()
    options = uc.ChromeOptions()
    options.add_extension(proxy_ext)
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Force headful (visible browser)
    options.headless = False
    
    driver = uc.Chrome(options=options, use_subprocess=True, version_main=None, headless=False)
    
    try:
        driver.get(url)
        time.sleep(2)  # Wait for page load
        
        # Search for "milk"
        print("   Searching for 'milk'...")
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys("milk")
        search_box.send_keys(Keys.ENTER)
        time.sleep(2)  # Wait for results
        
        # Scroll to load products
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)
        
        # Get HTML
        html = driver.page_source
        
        # Save HTML
        filename = f"location_test_{url_name.replace(' ', '_')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Check for location indicators
        checks = {
            'target_zip': target_zip in html,
            'target_city': target_city.lower() in html.lower(),
            'target_state': target_state in html,
            'has_products': '$' in html or 'price' in html.lower(),
            'has_nearby_filter': 'nearby' in html.lower() or 'near' in html.lower(),
        }
        
        # Look for IP location (competing indicator)
        # Our proxy shows Largo, FL (33776)
        proxy_location_indicators = ['33776', 'Largo', 'From your IP address']
        proxy_location_found = any(indicator in html for indicator in proxy_location_indicators)
        
        # Print results
        print(f"\n✅ Location Checks:")
        for check, result in checks.items():
            symbol = "✅" if result else "❌"
            print(f"   {symbol} {check}: {result}")
        
        print(f"\n⚠️  Proxy Location Indicators:")
        print(f"   {'❌' if not proxy_location_found else '✅'} Proxy location found: {proxy_location_found}")
        
        print(f"\n📄 Saved HTML to: {filename}")
        
        driver.quit()
        
        # Calculate success score
        success_score = sum(checks.values())
        location_override_success = checks['target_zip'] or checks['target_city']
        
        return {
            'name': url_name,
            'url': url,
            'checks': checks,
            'proxy_location_found': proxy_location_found,
            'success_score': success_score,
            'location_override_works': location_override_success and not proxy_location_found,
            'filename': filename
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            driver.quit()
        except:
            pass
        return {
            'name': url_name,
            'error': str(e)
        }


if __name__ == "__main__":
    print("\n" + "="*80)
    print("GOOGLE SHOPPING LOCATION OVERRIDE TEST")
    print("Testing all known methods to force location (like Google Maps @lat,lon)")
    print("="*80)
    
    # Target location: Miami, FL
    target_zip = "33101"
    target_city = "Miami"
    target_state = "FL"
    
    # Get coordinates
    try:
        nomi = pgeocode.Nominatim('us')
        location = nomi.query_postal_code(target_zip)
        latitude = location.latitude
        longitude = location.longitude
        print(f"\n🎯 Target: {target_city}, {target_state} ({target_zip})")
        print(f"   Coordinates: {latitude}, {longitude}")
    except:
        print("⚠️  pgeocode not installed, using hardcoded coords")
        latitude = 25.7617
        longitude = -80.1918
    
    print(f"\n🌐 Using proxy: {PROXY_HOST} (will show Largo, FL ~33776)")
    print(f"   If test WORKS → We'll see Miami (33101) instead of Largo")
    print(f"   If test FAILS → We'll see Largo (proxy location)")
    
    # Test patterns
    test_cases = [
        {
            "name": "1_Baseline_No_Location",
            "url": "https://shopping.google.com/?hl=en&gl=us"
        },
        {
            "name": "2_Near_Parameter_ZIP",
            "url": f"https://shopping.google.com/?hl=en&gl=us&near={target_zip}"
        },
        {
            "name": "3_Near_Parameter_City",
            "url": f"https://shopping.google.com/?hl=en&gl=us&near={target_city}+{target_state}"
        },
        {
            "name": "4_Coordinates_Like_Maps",
            "url": f"https://shopping.google.com/?hl=en&gl=us@{latitude},{longitude},15z"
        },
        {
            "name": "5_Location_Parameter",
            "url": f"https://shopping.google.com/?hl=en&gl=us&location={latitude},{longitude}"
        },
        {
            "name": "6_LL_Parameter",
            "url": f"https://shopping.google.com/?hl=en&gl=us&ll={latitude},{longitude}"
        },
        {
            "name": "7_Center_Parameter",
            "url": f"https://shopping.google.com/?hl=en&gl=us&center={latitude},{longitude}"
        },
    ]
    
    results = []
    
    for test in test_cases:
        result = test_url_pattern(
            test['name'],
            test['url'],
            target_zip,
            target_city,
            target_state
        )
        results.append(result)
        time.sleep(2)  # Pause between tests
    
    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY: Which methods override proxy location?")
    print("="*80 + "\n")
    
    working_methods = []
    
    for result in results:
        if 'error' not in result:
            name = result['name']
            works = result['location_override_works']
            score = result['success_score']
            
            if works:
                print(f"✅ {name}: LOCATION OVERRIDE WORKS!")
                print(f"   Score: {score}/5")
                working_methods.append(result)
            else:
                proxy_found = result['proxy_location_found']
                if proxy_found:
                    print(f"❌ {name}: Showing proxy location (Largo, FL)")
                else:
                    print(f"⚠️  {name}: No clear location indicators")
        else:
            print(f"❌ {name}: Error")
    
    print("\n" + "="*80)
    
    if working_methods:
        print(f"\n🎉 SUCCESS! {len(working_methods)} method(s) work!")
        print(f"\nWorking methods:")
        for method in working_methods:
            print(f"  ✅ {method['name']}")
            print(f"     URL pattern: {method['url'][:70]}...")
        print(f"\n💡 Use this URL pattern in production!")
    else:
        print(f"\n❌ NO METHODS WORKED")
        print(f"\n💡 Recommendations:")
        print(f"   1. Try Playwright with geolocation override")
        print(f"   2. Use residential proxies in target cities")
        print(f"   3. Scrape individual store websites instead")
    
    print("\n" + "="*80 + "\n")

