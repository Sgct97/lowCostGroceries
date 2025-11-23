#!/usr/bin/env python3
"""
Test SerpAPI with proper 'nearby' query format
"""

from serpapi import GoogleSearch
import json

API_KEY = "caaa674f50f87741ec1d523cf908d540b9538ef0b4426db9ddc175303c165c69"

def test_nearby_format(query: str, zipcode: str):
    """Test with 'near ZIP nearby' format"""
    
    # SerpAPI format from their docs
    full_query = f"{query}, near {zipcode} nearby"
    
    print("=" * 80)
    print(f"🔍 Testing: '{full_query}'")
    print("=" * 80)
    
    params = {
        "engine": "google_shopping",
        "q": full_query,
        "location": f"{zipcode}, Florida, United States",
        "google_domain": "google.com",
        "hl": "en",
        "gl": "us",
        "api_key": API_KEY
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return []
    
    shopping_results = results.get("shopping_results", [])
    print(f"\n✅ Got {len(shopping_results)} total results")
    
    # Filter for ONLY nearby results
    nearby_results = []
    online_results = []
    
    for item in shopping_results:
        extensions = item.get("extensions", [])
        
        # Check if it has "Nearby" or "Also nearby" in extensions
        is_nearby = any("nearby" in str(ext).lower() for ext in extensions)
        
        product = {
            "title": item.get("title", ""),
            "price": item.get("extracted_price", 0),
            "source": item.get("source", ""),
            "extensions": extensions,
            "rating": item.get("rating", None),
            "reviews": item.get("reviews", None),
        }
        
        if is_nearby:
            nearby_results.append(product)
        else:
            online_results.append(product)
    
    print(f"\n🏪 NEARBY STORES ({len(nearby_results)}):")
    for i, item in enumerate(nearby_results[:10], 1):
        print(f"   {i}. ${item['price']:.2f} - {item['title']}")
        print(f"      from {item['source']} - {item['extensions']}")
    
    print(f"\n🌐 ONLINE/OTHER ({len(online_results)}):")
    for i, item in enumerate(online_results[:5], 1):
        print(f"   {i}. ${item['price']:.2f} - {item['source']}")
    
    if nearby_results:
        lowest = min(nearby_results, key=lambda x: x['price'])
        print(f"\n💰 LOWEST NEARBY: ${lowest['price']:.2f} at {lowest['source']}")
    
    return nearby_results


def test_full_cart_nearby():
    """Test full cart with nearby filtering"""
    
    print("\n\n" + "=" * 80)
    print("🛒 FULL CART TEST - NEARBY ONLY")
    print("=" * 80)
    
    cart_items = [
        "whole milk gallon",
        "large eggs",
        "white bread"
    ]
    
    zipcode = "33773"
    cart_results = {}
    
    for item in cart_items:
        print(f"\n{'─' * 80}")
        nearby = test_nearby_format(item, zipcode)
        cart_results[item] = nearby
    
    # Summary
    print(f"\n\n{'=' * 80}")
    print("📊 CART SUMMARY - NEARBY STORES ONLY")
    print("=" * 80)
    
    total = 0
    for item, results in cart_results.items():
        if results:
            lowest = min(results, key=lambda x: x['price'])
            print(f"\n✅ {item}:")
            print(f"   ${lowest['price']:.2f} at {lowest['source']}")
            print(f"   {lowest['extensions']}")
            print(f"   ({len(results)} nearby options)")
            total += lowest['price']
        else:
            print(f"\n❌ {item}: No nearby results")
    
    print(f"\n{'─' * 80}")
    print(f"💰 Total Cart (Nearby Best Prices): ${total:.2f}")
    print(f"{'=' * 80}")
    
    # Save
    with open("serpapi_nearby_cart.json", 'w') as f:
        json.dump(cart_results, f, indent=2)
    
    print(f"\n💾 Saved to: serpapi_nearby_cart.json")


def compare_with_without_nearby():
    """Compare results with and without nearby filter"""
    
    print("\n\n" + "=" * 80)
    print("📊 COMPARISON: With vs Without 'nearby' query")
    print("=" * 80)
    
    query = "large eggs"
    zipcode = "33773"
    
    # Without 'nearby' in query
    print(f"\n🔴 WITHOUT 'nearby' format:")
    params1 = {
        "engine": "google_shopping",
        "q": query,
        "location": f"{zipcode}, Florida, United States",
        "api_key": API_KEY,
        "num": 40
    }
    search1 = GoogleSearch(params1)
    results1 = search1.get_dict().get("shopping_results", [])
    
    nearby1 = [r for r in results1 if any("nearby" in str(e).lower() for e in r.get("extensions", []))]
    print(f"   Total results: {len(results1)}")
    print(f"   With 'Nearby' tag: {len(nearby1)}")
    
    # With 'nearby' in query
    print(f"\n🟢 WITH 'near {zipcode} nearby' format:")
    params2 = {
        "engine": "google_shopping",
        "q": f"{query}, near {zipcode} nearby",
        "location": f"{zipcode}, Florida, United States",
        "api_key": API_KEY
    }
    search2 = GoogleSearch(params2)
    results2 = search2.get_dict().get("shopping_results", [])
    
    nearby2 = [r for r in results2 if any("nearby" in str(e).lower() for e in r.get("extensions", []))]
    print(f"   Total results: {len(results2)}")
    print(f"   With 'Nearby' tag: {len(nearby2)}")
    
    print(f"\n📈 Improvement: {len(nearby2) - len(nearby1)} more nearby results!")


if __name__ == "__main__":
    # Test the comparison first
    compare_with_without_nearby()
    
    # Test full cart
    test_full_cart_nearby()
    
    print("\n✅ All tests complete!")

