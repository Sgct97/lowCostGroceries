#!/usr/bin/env python3
"""
SerpAPI Test - Check if we can get Google Shopping data more reliably
"""

import requests
import json
from typing import List, Dict

SERPAPI_KEY = "caaa674f50f87741ec1d523cf908d540b9538ef0b4426db9ddc175303c165c69"
SERPAPI_BASE = "https://serpapi.com/search"

def search_serpapi(query: str, location: str = "33773") -> Dict:
    """Search Google Shopping using SerpAPI"""
    
    params = {
        "engine": "google_shopping",
        "q": query,
        "location": f"United States, {location}",
        "api_key": SERPAPI_KEY,
        "num": 40,  # Get up to 40 results
    }
    
    print(f"🔍 Searching SerpAPI for: '{query}' near {location}")
    
    try:
        response = requests.get(SERPAPI_BASE, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check for errors
        if "error" in data:
            print(f"❌ SerpAPI Error: {data['error']}")
            return {"error": data["error"]}
        
        # Extract shopping results
        shopping_results = data.get("shopping_results", [])
        
        print(f"✅ Got {len(shopping_results)} results from SerpAPI")
        
        # Parse into our format
        products = []
        for item in shopping_results:
            product = {
                "name": item.get("title", ""),
                "price": item.get("extracted_price", 0),
                "merchant": item.get("source", ""),
                "rating": item.get("rating", None),
                "review_count": item.get("reviews", None),
                "product_link": item.get("link", ""),
                "thumbnail": item.get("thumbnail", ""),
            }
            
            # Only add if we have price and name
            if product["price"] > 0 and product["name"]:
                products.append(product)
        
        return {
            "query": query,
            "location": location,
            "products": products,
            "total": len(products)
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return {"error": str(e)}


def test_multiple_products():
    """Test with multiple products like our actual use case"""
    
    test_items = [
        "whole milk 1 gallon",
        "large eggs 12 count",
        "whole wheat bread 24 oz"
    ]
    
    print("=" * 80)
    print("🧪 SERPAPI TEST - Multiple Products")
    print("=" * 80)
    
    all_results = {}
    
    for item in test_items:
        print(f"\n{'─' * 80}")
        result = search_serpapi(item, "33773")
        
        if "error" in result:
            print(f"❌ Failed for '{item}': {result['error']}")
            all_results[item] = []
            continue
        
        all_results[item] = result["products"]
        
        # Show top 5 results
        print(f"\n📦 Top 5 Results for '{item}':")
        for i, product in enumerate(result["products"][:5], 1):
            print(f"   {i}. ${product['price']:.2f} - {product['name']}")
            print(f"      from {product['merchant']}")
            if product['rating']:
                print(f"      ⭐ {product['rating']} ({product['review_count']} reviews)")
    
    # Summary
    print(f"\n{'=' * 80}")
    print("📊 SUMMARY")
    print("=" * 80)
    
    for item, products in all_results.items():
        if products:
            lowest = min(products, key=lambda x: x['price'])
            print(f"\n✅ {item}:")
            print(f"   Lowest: ${lowest['price']:.2f} at {lowest['merchant']}")
            print(f"   Total options: {len(products)}")
        else:
            print(f"\n❌ {item}: No results")
    
    # Compare to what we saw with scraping
    print(f"\n{'=' * 80}")
    print("🔬 COMPARISON TO SCRAPING")
    print("=" * 80)
    print("\nSerpAPI Advantages:")
    print("   ✅ No browser needed (much faster)")
    print("   ✅ No blocking/CAPTCHA issues")
    print("   ✅ Consistent data format")
    print("   ✅ Includes product links")
    print("   ✅ Thumbnail images")
    
    print("\nConsiderations:")
    print("   💰 Cost: ~$50/month for 5,000 searches")
    print("   ⚡ Speed: ~1-2 seconds per query vs 10-15 seconds")
    print("   📊 At 3 items per cart: ~1,666 carts/month on base plan")
    
    # Save results
    output_file = "serpapi_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Full results saved to: {output_file}")


def test_location_specificity():
    """Test if 'nearby' results are actually location-specific"""
    
    print("\n" + "=" * 80)
    print("🌍 LOCATION SPECIFICITY TEST")
    print("=" * 80)
    
    test_query = "large eggs 12 count"
    locations = ["33773", "90210", "10001"]  # Florida, California, NYC
    
    for location in locations:
        print(f"\n📍 Testing location: {location}")
        result = search_serpapi(test_query, location)
        
        if "error" not in result and result["products"]:
            print(f"   Got {len(result['products'])} results")
            print(f"   Lowest price: ${min(p['price'] for p in result['products']):.2f}")
            print(f"   Stores: {', '.join(set(p['merchant'] for p in result['products'][:5]))}")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        SERPAPI FEASIBILITY TEST                              ║
║                                                                              ║
║  Testing if SerpAPI can replace our scraping solution                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Main test
    test_multiple_products()
    
    # Location test
    test_location_specificity()
    
    print("\n✅ Test complete!")

