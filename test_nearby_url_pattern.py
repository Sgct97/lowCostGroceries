#!/usr/bin/env python3
"""
Test using the ACTUAL nearby URL pattern that Google uses
"""
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import urllib.parse

def test_nearby_url_for_zip(zip_code, search_term="milk"):
    """Test using the nearby URL pattern"""
    print(f"\n{'='*80}")
    print(f"Testing ZIP: {zip_code} with search: {search_term}")
    print(f"{'='*80}")
    
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = uc.Chrome(options=options, use_subprocess=False)
    
    try:
        # Construct the URL like Google does when you click "Nearby"
        # Pattern: q={search_term}+near+zip+{zip_code}+nearby
        query = f"{search_term} near zip {zip_code} nearby"
        encoded_query = urllib.parse.quote(query)
        
        # Use the URL structure from the user's example
        url = f"https://www.google.com/search?q={encoded_query}&udm=28&shopmd=4"
        
        print(f"\n📍 Loading: {url}")
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Get all merchants
        merchants = driver.find_elements(By.CSS_SELECTOR, "span.WJMUdc.rw5ecc")
        merchant_names = [m.text for m in merchants[:30] if m.text]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_merchants = []
        for name in merchant_names:
            if name and name not in seen:
                seen.add(name)
                unique_merchants.append(name)
        
        print(f"\n📦 Found {len(unique_merchants)} unique merchants:")
        for name in unique_merchants[:20]:
            print(f"  - {name}")
        
        # Save HTML
        filename = f"nearby_test_{zip_code}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"\n💾 Saved HTML to: {filename}")
        
        # Check for known local stores based on ZIP
        html_lower = driver.page_source.lower()
        
        local_stores = {
            "33773": ["publix", "winn-dixie", "sedanos", "presidente", "fresco y mas"],  # Largo/Clearwater, FL
            "33101": ["publix", "sedanos", "winn-dixie", "presidente", "fresco y mas"],  # Miami
            "10001": ["key food", "fairway", "gristedes", "trader joe"],  # NYC
            "90001": ["vons", "ralphs", "food 4 less", "superior"],  # LA
            "75201": ["kroger", "tom thumb", "albertsons", "fiesta"],  # Dallas
        }
        
        found_stores = []
        if zip_code in local_stores:
            for store in local_stores[zip_code]:
                if store in html_lower:
                    found_stores.append(store.title())
        
        print(f"\n{'='*80}")
        if found_stores:
            print(f"✅ SUCCESS! Found {len(found_stores)} local stores:")
            for store in found_stores:
                print(f"  ✓ {store}")
        else:
            print(f"⚠️  No classic local grocery stores found in HTML")
            print(f"   But merchants list shows: {', '.join(unique_merchants[:5])}")
        print(f"{'='*80}")
        
        return unique_merchants, found_stores
        
    finally:
        driver.quit()

def main():
    """Test the nearby URL pattern"""
    print("\n" + "="*80)
    print("TESTING: Using Google's actual 'Nearby' URL pattern")
    print("="*80)
    
    # Test multiple ZIP codes
    test_zips = [
        "33773",  # Largo/Clearwater, FL (should have Publix)
        "33101",  # Miami (should have Publix, Sedanos)
        "10001",  # NYC (should have different stores)
    ]
    
    all_results = {}
    
    for zip_code in test_zips:
        try:
            merchants, local_stores = test_nearby_url_for_zip(zip_code)
            all_results[zip_code] = (merchants, local_stores)
            time.sleep(2)
        except Exception as e:
            print(f"\n❌ Error testing {zip_code}: {e}")
            all_results[zip_code] = ([], [])
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    
    for zip_code, (merchants, local_stores) in all_results.items():
        print(f"\nZIP {zip_code}:")
        print(f"  Merchants: {', '.join(merchants[:5])}")
        if local_stores:
            print(f"  ✅ Local stores: {', '.join(local_stores)}")
        else:
            print(f"  ⚠️  No traditional grocery stores found")

if __name__ == "__main__":
    main()

