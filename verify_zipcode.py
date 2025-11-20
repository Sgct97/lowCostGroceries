#!/usr/bin/env python3
"""
Quick test to verify zipcode location works - shows actual merchants
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
    
    plugin_file = 'verify_proxy.zip'
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_file


def test_zipcode(zipcode, query="milk"):
    """Test a single search with zipcode and show merchants"""
    
    print(f"\n{'='*80}")
    print(f"Testing ZIP {zipcode} - searching for '{query}'")
    print('='*80 + '\n')
    
    proxy_ext = create_proxy_extension()
    options = uc.ChromeOptions()
    options.add_extension(proxy_ext)
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
    
    # Load with zipcode
    url = f'https://shopping.google.com/?hl=en&gl=us&near={zipcode}'
    print(f"Loading: {url}")
    driver.get(url)
    time.sleep(1)
    
    # Search
    print(f"Searching for '{query}'...")
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.send_keys(Keys.ENTER)
    time.sleep(1)
    
    driver.execute_script("window.scrollTo(0, 800);")
    time.sleep(0.5)
    
    # Parse
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    containers = soup.find_all('div', class_='gkQHve')
    
    products = []
    for title_elem in containers[:10]:  # First 10
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
                products.append({'title': title, 'price': price, 'merchant': merchant})
        except:
            pass
    
    driver.quit()
    
    print(f"\n✅ Found {len(products)} products:\n")
    for i, p in enumerate(products, 1):
        print(f"{i:2}. ${p['price']:<6.2f} - {p['title'][:40]:40} @ {p['merchant']}")
    
    # Show unique merchants
    merchants = list(set(p['merchant'] for p in products))
    print(f"\n🏪 Merchants found: {', '.join(merchants)}")
    
    return products


if __name__ == "__main__":
    import sys
    
    zipcode = sys.argv[1] if len(sys.argv) > 1 else "10001"
    products = test_zipcode(zipcode)
    
    print(f"\n{'='*80}\n")

