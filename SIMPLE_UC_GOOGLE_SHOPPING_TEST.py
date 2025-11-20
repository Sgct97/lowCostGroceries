#!/usr/bin/env python3
"""
SIMPLEST POSSIBLE TEST: Does UC + Google Shopping + Product Parsing work?
NO callbacks, NO parallel, NO complexity - just ONE search, parse products, done.
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import re

print("\n" + "="*80)
print("SIMPLE TEST: UC → Google Shopping → Parse Products")
print("="*80 + "\n")

driver = uc.Chrome()

try:
    # Step 1: Load Google Shopping
    print("[1] Loading Google Shopping...")
    driver.get('https://shopping.google.com/?hl=en&gl=us')
    time.sleep(3)
    
    # Step 2: Search for milk
    print("[2] Searching for 'milk'...")
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys("milk")
    search_box.send_keys(Keys.ENTER)
    time.sleep(5)
    
    # Step 3: Scroll
    print("[3] Scrolling...")
    for i in range(3):
        driver.execute_script(f"window.scrollTo(0, {(i+1) * 800});")
        time.sleep(2)
    
    # Step 4: Parse products
    print("[4] Parsing products...")
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find product containers - look for divs with product titles
    containers = soup.find_all('div', class_='gkQHve')
    print(f"    Found {len(containers)} product title elements")
    
    products = []
    for title_elem in containers[:10]:
        try:
            # Title is the element itself
            title = title_elem.get_text(strip=True)
            
            # Find parent container to get price and merchant
            parent = title_elem.find_parent('div', class_='PhALMc')
            if not parent:
                continue
            
            # Price
            price_elem = parent.find('span', class_='lmQWe')
            price_text = price_elem.get_text(strip=True) if price_elem else None
            price = None
            if price_text:
                match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                if match:
                    price = float(match.group(1).replace(',', ''))
            
            # Merchant
            merchant_elem = parent.find('span', class_='WJMUdc')
            merchant = merchant_elem.get_text(strip=True) if merchant_elem else None
            
            if title and price:
                products.append({
                    'title': title,
                    'price': price,
                    'merchant': merchant
                })
        except Exception as e:
            pass
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80 + "\n")
    
    print(f"Containers found: {len(containers)}")
    print(f"Products parsed: {len(products)}")
    
    if products:
        print("\n🎉 SUCCESS! Here are the products:\n")
        for i, p in enumerate(products[:5], 1):
            print(f"{i}. {p['title'][:60]}")
            print(f"   ${p['price']} @ {p['merchant']}")
            print()
        
        print("="*80)
        print("✅ PROOF: UC + Google Shopping + Parsing WORKS!")
        print("="*80)
    else:
        print("\n❌ FAILED: No products parsed")
        print("\nDebugging info:")
        print(f"- Page size: {len(html):,} bytes")
        print(f"- Has '$' in HTML: {'Yes' if '$' in html else 'No'}")
        print(f"- Sample HTML:")
        print(html[:500])
        
        # Save HTML for inspection
        with open('failed_parse.html', 'w') as f:
            f.write(html)
        print("\n✓ Saved HTML to failed_parse.html for inspection")

finally:
    driver.quit()

