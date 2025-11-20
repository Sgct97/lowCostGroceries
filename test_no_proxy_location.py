#!/usr/bin/env python3
"""
Test if near= parameter works WITHOUT proxy
"""
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_location_override():
    """Test location override without proxy interference"""
    
    # Test 1: No location parameter (should show NYC/NJ area stores)
    print("\n" + "="*80)
    print("TEST 1: No location parameter (droplet's IP location)")
    print("="*80)
    
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = uc.Chrome(options=options, use_subprocess=False)
    
    try:
        # Load without location
        driver.get("https://shopping.google.com/?hl=en&gl=us")
        time.sleep(3)
        
        # Search
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys("milk")
        search_box.submit()
        time.sleep(5)
        
        # Get merchants
        merchants = driver.find_elements(By.CSS_SELECTOR, "span.WJMUdc.rw5ecc")
        merchant_names = [m.text for m in merchants[:10] if m.text]
        
        print(f"\n✓ Found {len(merchant_names)} merchants:")
        for name in merchant_names:
            print(f"  - {name}")
        
        # Save HTML
        with open("test_no_location.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("\n✓ Saved HTML to: test_no_location.html")
        
    finally:
        driver.quit()
    
    time.sleep(2)
    
    # Test 2: WITH near=33101 (Miami)
    print("\n" + "="*80)
    print("TEST 2: WITH near=33101 (Miami, FL)")
    print("="*80)
    
    # Create new options for second browser
    options2 = uc.ChromeOptions()
    options2.add_argument("--start-maximized")
    options2.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = uc.Chrome(options=options2, use_subprocess=False)
    
    try:
        # Load WITH Miami location
        driver.get("https://shopping.google.com/?hl=en&gl=us&near=33101")
        time.sleep(3)
        
        # Search
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys("milk")
        search_box.submit()
        time.sleep(5)
        
        # Get merchants
        merchants = driver.find_elements(By.CSS_SELECTOR, "span.WJMUdc.rw5ecc")
        merchant_names = [m.text for m in merchants[:10] if m.text]
        
        print(f"\n✓ Found {len(merchant_names)} merchants:")
        for name in merchant_names:
            print(f"  - {name}")
        
        # Check for Publix (Miami-specific chain)
        html = driver.page_source
        publix_count = html.lower().count("publix")
        sedanos_count = html.lower().count("sedano")
        
        print(f"\n✓ Florida-specific stores:")
        print(f"  - 'Publix' mentions: {publix_count}")
        print(f"  - 'Sedanos' mentions: {sedanos_count}")
        
        # Save HTML
        with open("test_with_miami_location.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("\n✓ Saved HTML to: test_with_miami_location.html")
        
    finally:
        driver.quit()
    
    print("\n" + "="*80)
    print("COMPARISON")
    print("="*80)
    print("\nIf near= parameter works, we should see:")
    print("  1. Different merchants between the two tests")
    print("  2. Publix/Sedanos in Miami test but not in baseline")
    print("  3. NYC/NJ stores in baseline but not in Miami test")

if __name__ == "__main__":
    test_location_override()

