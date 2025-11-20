#!/usr/bin/env python3
"""
Prove that we can get ACTUAL local stores for different ZIP codes
"""
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Known local stores for different regions
EXPECTED_STORES = {
    "33101": ["Publix", "Sedanos", "Winn-Dixie", "Presidente", "Fresco y Mas"],  # Miami
    "10001": ["Key Food", "Fairway", "Gristedes", "D'Agostino", "Morton Williams"],  # NYC
    "90001": ["Vons", "Ralphs", "Northgate", "Food 4 Less", "Superior"],  # LA
    "75201": ["Tom Thumb", "Albertsons", "Kroger", "Fiesta", "El Rancho"],  # Dallas
    "94102": ["Safeway", "Trader Joe's", "Whole Foods", "Mollie Stone", "Rainbow"]  # SF
}

def test_zip_for_local_stores(zip_code, expected_stores):
    """Test a single ZIP code for local stores"""
    print(f"\n{'='*80}")
    print(f"Testing ZIP: {zip_code}")
    print(f"Expected stores: {', '.join(expected_stores[:3])}")
    print(f"{'='*80}")
    
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = uc.Chrome(options=options, use_subprocess=False)
    
    try:
        # Load with near parameter
        url = f"https://shopping.google.com/?hl=en&gl=us&near={zip_code}"
        print(f"\n📍 Loading: {url}")
        driver.get(url)
        time.sleep(3)
        
        # Search for eggs (common grocery item)
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys("eggs")
        search_box.submit()
        time.sleep(5)
        
        # Try to click "Nearby" filter if it exists
        try:
            nearby_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Nearby') or contains(text(), 'Near you')]"))
            )
            print(f"✓ Found 'Nearby' filter, clicking...")
            nearby_button.click()
            time.sleep(3)
        except:
            print(f"⚠️  No 'Nearby' filter found")
        
        # Get all merchants
        html = driver.page_source.lower()
        merchants = driver.find_elements(By.CSS_SELECTOR, "span.WJMUdc.rw5ecc")
        merchant_names = [m.text for m in merchants[:30] if m.text]
        
        print(f"\n📦 Found {len(merchant_names)} merchants:")
        for name in merchant_names[:15]:
            print(f"  - {name}")
        
        # Check for expected local stores
        found_stores = []
        for store in expected_stores:
            if store.lower() in html:
                found_stores.append(store)
        
        print(f"\n{'='*80}")
        if found_stores:
            print(f"✅ SUCCESS! Found {len(found_stores)} local stores:")
            for store in found_stores:
                print(f"  ✓ {store}")
        else:
            print(f"❌ FAILED! No local stores found")
            print(f"   Expected: {', '.join(expected_stores)}")
        print(f"{'='*80}")
        
        # Save HTML for inspection
        filename = f"local_stores_{zip_code}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"\n💾 Saved HTML to: {filename}")
        
        return len(found_stores) > 0, found_stores
        
    finally:
        driver.quit()

def main():
    """Test multiple ZIP codes"""
    print("\n" + "="*80)
    print("TESTING: Can we get ACTUAL local stores for different ZIP codes?")
    print("="*80)
    
    results = {}
    
    for zip_code, expected in EXPECTED_STORES.items():
        try:
            success, found = test_zip_for_local_stores(zip_code, expected)
            results[zip_code] = (success, found)
            time.sleep(2)  # Brief pause between tests
        except Exception as e:
            print(f"\n❌ Error testing {zip_code}: {e}")
            results[zip_code] = (False, [])
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    
    successful = sum(1 for success, _ in results.values() if success)
    
    for zip_code, (success, found) in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {zip_code}: {', '.join(found) if found else 'No local stores found'}")
    
    print(f"\n{'='*80}")
    print(f"SUCCESS RATE: {successful}/{len(results)} ZIP codes")
    print(f"{'='*80}")
    
    if successful >= len(results) * 0.6:  # At least 60% success
        print("\n🎉 PROOF ESTABLISHED: We CAN get local stores for different ZIP codes!")
    else:
        print("\n⚠️  INCONCLUSIVE: More testing needed")

if __name__ == "__main__":
    main()

