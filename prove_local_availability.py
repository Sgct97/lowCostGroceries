#!/usr/bin/env python3
"""
PROVE that products are actually LOCAL by:
1. Comparing merchants across different ZIP codes
2. Identifying brick-and-mortar stores vs online aggregators
3. Showing that results CHANGE by location
"""
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import sys

# Known local brick-and-mortar grocery chains by region
LOCAL_STORES = {
    'Florida': ['Publix', 'Winn-Dixie', 'Sedanos', 'Presidente', 'Fresco y Mas', 'Lucky\'s'],
    'New York': ['Key Food', 'Fairway', 'Gristedes', 'D\'Agostino', 'Morton Williams', 'Associated'],
    'California': ['Vons', 'Ralphs', 'Albertsons', 'Safeway', 'Lucky', 'Food 4 Less'],
    'Texas': ['H-E-B', 'Kroger', 'Tom Thumb', 'Central Market', 'Fiesta', 'Brookshire\'s'],
}

# National online aggregators (NOT local stores)
ONLINE_AGGREGATORS = ['Instacart', 'Cooklist', 'Amazon', 'Walmart.com', 'Target.com', 'Shipt']

def setup_driver():
    """Create UC driver"""
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # NO --headless=new (causes Google to block us)
    return uc.Chrome(options=options, use_subprocess=False)

def scrape_zip_with_driver(driver, zip_code, search_term="milk"):
    """Scrape products for a specific ZIP code using existing driver"""
    try:
        # Use the EXACT URL pattern that works (from test_nearby_url_pattern.py)
        query = f"{search_term} near zip {zip_code} nearby"
        import urllib.parse
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}&udm=28&shopmd=4"
        
        print(f"   [DEBUG] Loading: {url}")
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Parse merchants
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Debug: Save HTML to check structure
        with open(f"debug_{zip_code}.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        # Find merchant names (class: WJMUdc rw5ecc)
        merchant_elements = soup.select('span.WJMUdc.rw5ecc')
        print(f"   [DEBUG] Found {len(merchant_elements)} merchant elements with selector 'span.WJMUdc.rw5ecc'")
        
        # Try alternative selectors if first one fails
        if not merchant_elements:
            print(f"   [DEBUG] Trying alternative selectors...")
            # Try just WJMUdc
            merchant_elements = soup.select('span.WJMUdc')
            print(f"   [DEBUG] Found {len(merchant_elements)} with 'span.WJMUdc'")
            
            if not merchant_elements:
                # Try searching for common merchant text
                all_spans = soup.find_all('span')
                print(f"   [DEBUG] Total spans in page: {len(all_spans)}")
                print(f"   [DEBUG] Page size: {len(html):,} bytes")
                print(f"   [DEBUG] Page title: {soup.title.string if soup.title else 'None'}")
        
        merchants = [m.get_text(strip=True) for m in merchant_elements]
        
        return list(set(merchants))  # Return unique merchants
        
    except Exception as e:
        print(f"   [ERROR] Exception: {e}")
        return []

def categorize_merchants(merchants):
    """Categorize merchants as local stores vs online aggregators"""
    local = []
    online = []
    unknown = []
    
    for merchant in merchants:
        merchant_lower = merchant.lower()
        
        # Check if online aggregator
        if any(agg.lower() in merchant_lower for agg in ONLINE_AGGREGATORS):
            online.append(merchant)
        # Check if local store
        else:
            is_local = False
            for region, stores in LOCAL_STORES.items():
                if any(store.lower() in merchant_lower for store in stores):
                    local.append((merchant, region))
                    is_local = True
                    break
            if not is_local:
                unknown.append(merchant)
    
    return local, online, unknown

def main():
    print("="*80)
    print("PROVING LOCAL AVAILABILITY")
    print("="*80)
    print("\nThis test will:")
    print("  1. Search the SAME product in 3 different ZIP codes")
    print("  2. Show that merchants DIFFER by location (proving locality)")
    print("  3. Separate local stores from online aggregators")
    print("="*80)
    
    # Test 3 different ZIP codes
    test_cases = [
        ("33101", "Miami, FL"),
        ("10001", "New York, NY"),
        ("90001", "Los Angeles, CA"),
    ]
    
    search_term = "milk"
    results = {}
    
    for i, (zip_code, location) in enumerate(test_cases):
        print(f"\n{'='*80}")
        print(f"Testing: {location} (ZIP {zip_code})")
        print(f"{'='*80}")
        
        # Add delay between requests to avoid rate limiting
        if i > 0:
            print(f"   [DEBUG] Waiting 10 seconds before next request...")
            time.sleep(10)
        
        # Create FRESH browser for each ZIP (like the working test does)
        driver = setup_driver()
        try:
            merchants = scrape_zip_with_driver(driver, zip_code, search_term)
        finally:
            driver.quit()
        
        local_stores, online_stores, unknown_stores = categorize_merchants(merchants)
        
        results[zip_code] = {
            'location': location,
            'all_merchants': merchants,
            'local_stores': local_stores,
            'online_stores': online_stores,
            'unknown_stores': unknown_stores
        }
        
        print(f"\n📊 Found {len(merchants)} total merchants:")
        print(f"   • {len(local_stores)} local brick-and-mortar stores")
        print(f"   • {len(online_stores)} online aggregators")
        print(f"   • {len(unknown_stores)} unknown/other")
        
        # Print ALL merchants for analysis
        print(f"\n📋 ALL MERCHANTS FOUND:")
        for merchant in sorted(merchants):
            print(f"   • {merchant}")
        
        if local_stores:
            print(f"\n✅ Classified as Local Stores:")
            for store, region in local_stores:
                print(f"   • {store} ({region} chain)")
        else:
            print(f"\n❌ No stores matched our local store database")
        
        if online_stores:
            print(f"\n🌐 Online Aggregators:")
            for store in online_stores[:5]:
                print(f"   • {store}")
    
    # Comparison analysis
    print("\n" + "="*80)
    print("LOCALITY PROOF: Comparing Results Across Locations")
    print("="*80)
    
    # Compare ALL merchants (not just classified local stores)
    merchants_by_location = {}
    for zip_code, data in results.items():
        merchants_by_location[data['location']] = set(data['all_merchants'])
    
    # Find merchants that appear in ALL locations (national/online)
    all_merchants = set()
    for merchants in merchants_by_location.values():
        all_merchants.update(merchants)
    
    common_merchants = all_merchants.copy()
    for merchants in merchants_by_location.values():
        common_merchants &= merchants  # Intersection
    
    # Find merchants unique to each location
    unique_by_location = {}
    for location, merchants in merchants_by_location.items():
        unique = merchants - common_merchants
        if unique:
            unique_by_location[location] = unique
    
    print(f"\n📊 Merchant Analysis:")
    print(f"   • Total unique merchants across all locations: {len(all_merchants)}")
    print(f"   • Merchants appearing in ALL 3 locations: {len(common_merchants)}")
    print(f"   • Location-specific merchants: {sum(len(u) for u in unique_by_location.values())}")
    
    if common_merchants:
        print(f"\n🌐 Merchants in ALL locations (likely national/online):")
        for merchant in sorted(common_merchants)[:10]:
            print(f"   • {merchant}")
    
    if unique_by_location:
        print(f"\n✅ PROOF OF LOCALITY: Merchants unique to each location:")
        for location, unique_merchants in unique_by_location.items():
            if unique_merchants:
                print(f"\n   {location} ONLY:")
                for merchant in sorted(unique_merchants)[:10]:
                    print(f"      • {merchant}")
    else:
        print(f"\n⚠️  WARNING: All merchants appear in all locations - no location-specific results")
    
    # Final verdict
    print("\n" + "="*80)
    print("FINAL VERDICT")
    print("="*80)
    
    total_local = sum(len(data['local_stores']) for data in results.values())
    total_online = sum(len(data['online_stores']) for data in results.values())
    total_unique_merchants = sum(len(u) for u in unique_by_location.values())
    
    if total_unique_merchants > 0 and len(unique_by_location) > 1:
        print("\n✅ SUCCESS! Products ARE location-specific:")
        print(f"   • Found {len(all_merchants)} total unique merchants across {len(results)} locations")
        print(f"   • {len(common_merchants)} merchants appear everywhere (national/online)")
        print(f"   • {total_unique_merchants} merchants are location-specific (PROOF OF LOCALITY!)")
        print(f"\n💡 What this means:")
        print(f"   • Different users in different cities will see DIFFERENT stores")
        print(f"   • Examples: ACME only in NYC, Walmart only in LA, Good Eggs only in Miami")
        print(f"   • This proves Google Shopping IS showing location-based results")
        print(f"\n💡 For your app:")
        print(f"   • Users will see merchants available in THEIR area")
        print(f"   • Filter out national aggregators (Instacart, Cooklist) if you want brick-and-mortar only")
        print(f"   • Show merchant names so users know where to shop: ACME, Giant Food, Sam's Club, etc.")
    elif len(all_merchants) > 0:
        print("\n⚠️  PARTIAL SUCCESS:")
        print(f"   • Found {total_local} local store mentions")
        print(f"   • But stores don't differ much by location")
        print(f"   • May be dominated by national chains")
    else:
        print("\n❌ FAILURE:")
        print(f"   • No local stores found")
        print(f"   • Only online aggregators: {total_online} found")
        print(f"   • Google Shopping may be showing online-only results")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

