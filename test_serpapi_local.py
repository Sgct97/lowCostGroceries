#!/usr/bin/env python3
"""
Test if SerpAPI returns actual NEARBY stores or just online retailers
"""

from serpapi import GoogleSearch
import json

API_KEY = "caaa674f50f87741ec1d523cf908d540b9538ef0b4426db9ddc175303c165c69"

def analyze_store_locality(location_zip):
    """Check what stores are returned and if they're actually local"""
    
    query = "large eggs"
    
    print("=" * 80)
    print(f"🌍 TESTING STORE LOCALITY FOR ZIP {location_zip}")
    print("=" * 80)
    
    params = {
        "engine": "google_shopping",
        "q": query,
        "location": f"United States, {location_zip}",
        "google_domain": "google.com",
        "hl": "en",
        "gl": "us",
        "num": 40,
        "api_key": API_KEY
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    
    shopping_results = results.get("shopping_results", [])
    
    if not shopping_results:
        print("❌ No results found")
        return
    
    print(f"\n✅ Found {len(shopping_results)} results")
    print(f"\n📊 Analyzing stores...\n")
    
    # Categorize stores
    online_keywords = ['walmart - seller', 'instacart', 'gopuff', '.com', 'cooklist']
    local_stores = []
    online_retailers = []
    ambiguous = []
    
    for item in shopping_results:
        source = item.get("source", "").lower()
        title = item.get("title", "")
        price = item.get("extracted_price", 0)
        delivery = item.get("delivery", "")
        
        # Check if it mentions local availability
        is_online = any(keyword in source for keyword in online_keywords)
        
        store_info = {
            "source": item.get("source", ""),
            "price": price,
            "title": title,
            "delivery": delivery,
            "link": item.get("link", "")
        }
        
        if is_online:
            online_retailers.append(store_info)
        elif "walmart" in source or "target" in source or "dollar general" in source:
            ambiguous.append(store_info)
        else:
            local_stores.append(store_info)
    
    # Print results
    print(f"🏪 LIKELY LOCAL STORES ({len(local_stores)}):")
    for store in local_stores[:10]:
        print(f"   ${store['price']:.2f} - {store['source']}")
        if store['delivery']:
            print(f"      Delivery: {store['delivery']}")
    
    print(f"\n🌐 ONLINE RETAILERS ({len(online_retailers)}):")
    for store in online_retailers[:10]:
        print(f"   ${store['price']:.2f} - {store['source']}")
    
    print(f"\n❓ AMBIGUOUS (Could be local or online) ({len(ambiguous)}):")
    for store in ambiguous[:10]:
        print(f"   ${store['price']:.2f} - {store['source']}")
        if store['delivery']:
            print(f"      Delivery: {store['delivery']}")
    
    # Summary
    print(f"\n{'─' * 80}")
    print(f"📈 SUMMARY:")
    print(f"   Likely Local: {len(local_stores)} ({len(local_stores)/len(shopping_results)*100:.1f}%)")
    print(f"   Online Only: {len(online_retailers)} ({len(online_retailers)/len(shopping_results)*100:.1f}%)")
    print(f"   Ambiguous: {len(ambiguous)} ({len(ambiguous)/len(shopping_results)*100:.1f}%)")


def test_with_local_filter():
    """Try different parameters to get ONLY nearby stores"""
    
    print("\n\n" + "=" * 80)
    print("🔬 TESTING DIFFERENT PARAMETERS FOR LOCAL-ONLY RESULTS")
    print("=" * 80)
    
    location_zip = "33773"
    query = "large eggs"
    
    test_configs = [
        {
            "name": "Standard Search",
            "params": {
                "engine": "google_shopping",
                "q": query,
                "location": f"United States, {location_zip}",
                "num": 40,
            }
        },
        {
            "name": "With 'nearby' in query",
            "params": {
                "engine": "google_shopping",
                "q": f"{query} nearby",
                "location": f"United States, {location_zip}",
                "num": 40,
            }
        },
        {
            "name": "With tbs=local_avail:1",
            "params": {
                "engine": "google_shopping",
                "q": query,
                "location": f"United States, {location_zip}",
                "tbs": "local_avail:1",
                "num": 40,
            }
        },
        {
            "name": "With tbs=mr:1,sales:1",
            "params": {
                "engine": "google_shopping",
                "q": query,
                "location": f"United States, {location_zip}",
                "tbs": "mr:1,sales:1",
                "num": 40,
            }
        },
    ]
    
    for config in test_configs:
        print(f"\n{'─' * 80}")
        print(f"🧪 Testing: {config['name']}")
        
        params = config['params'].copy()
        params["api_key"] = API_KEY
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if "error" in results:
                print(f"   ❌ Error: {results['error']}")
                continue
            
            shopping_results = results.get("shopping_results", [])
            
            if not shopping_results:
                print(f"   ⚠️  No results")
                continue
            
            print(f"   ✅ {len(shopping_results)} results")
            
            # Show first 5 stores
            print(f"   First 5 stores:")
            for i, item in enumerate(shopping_results[:5], 1):
                source = item.get("source", "")
                price = item.get("extracted_price", 0)
                print(f"      {i}. ${price:.2f} - {source}")
        
        except Exception as e:
            print(f"   ❌ Exception: {e}")


def compare_to_manual_check():
    """Compare SerpAPI results to what we manually see on Google Shopping"""
    
    print("\n\n" + "=" * 80)
    print("🔍 MANUAL COMPARISON TEST")
    print("=" * 80)
    print("\nGo to Google Shopping and search for 'large eggs' near 33773")
    print("Look at the 'In stores nearby' section")
    print("\nCommon stores you'd expect to see:")
    print("   - Publix (major grocery in Florida)")
    print("   - Walmart")
    print("   - Target")
    print("   - Winn-Dixie")
    print("   - Dollar General")
    print("   - Walgreens/CVS")
    
    print("\n" + "─" * 80)
    print("Now let's see what SerpAPI returns:")
    
    params = {
        "engine": "google_shopping",
        "q": "large eggs",
        "location": "United States, 33773",
        "num": 40,
        "api_key": API_KEY
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    
    shopping_results = results.get("shopping_results", [])
    
    # Get unique stores
    stores = list(set(item.get("source", "") for item in shopping_results))
    stores.sort()
    
    print(f"\n📦 Unique stores in SerpAPI results ({len(stores)}):")
    for store in stores:
        print(f"   • {store}")
    
    # Flag suspicious ones
    print(f"\n⚠️  Stores that are definitely ONLINE-ONLY:")
    online_only = ['Instacart', 'Cooklist', 'gopuff', 'Seller']
    for store in stores:
        if any(keyword in store for keyword in online_only):
            print(f"   ❌ {store}")


if __name__ == "__main__":
    # Test 1: Analyze locality
    analyze_store_locality("33773")
    
    # Test 2: Try different parameters
    test_with_local_filter()
    
    # Test 3: Compare to manual
    compare_to_manual_check()
    
    print("\n" + "=" * 80)
    print("✅ Analysis complete!")
    print("=" * 80)

