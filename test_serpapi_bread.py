#!/usr/bin/env python3
"""
Test different bread queries with official SerpAPI library
"""

from serpapi import GoogleSearch
import json

API_KEY = "caaa674f50f87741ec1d523cf908d540b9538ef0b4426db9ddc175303c165c69"

def test_bread_queries():
    """Test different ways to search for bread"""
    
    bread_queries = [
        "bread",
        "white bread",
        "sandwich bread",
        "wheat bread",
        "bread loaf",
        "sliced bread",
    ]
    
    location = "33773"
    
    print("=" * 80)
    print("🍞 TESTING DIFFERENT BREAD QUERIES")
    print("=" * 80)
    
    for query in bread_queries:
        print(f"\n{'─' * 80}")
        print(f"🔍 Testing query: '{query}'")
        
        params = {
            "engine": "google_shopping",
            "q": query,
            "location": f"United States, {location}",
            "google_domain": "google.com",
            "hl": "en",
            "gl": "us",
            "num": 40,
            "api_key": API_KEY
        }
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Check for error
            if "error" in results:
                print(f"   ❌ Error: {results['error']}")
                continue
            
            # Get shopping results
            shopping_results = results.get("shopping_results", [])
            
            if not shopping_results:
                print(f"   ⚠️  No results found")
                continue
            
            print(f"   ✅ Found {len(shopping_results)} results")
            
            # Show top 5 with prices
            print(f"\n   📦 Top 5 Results:")
            for i, item in enumerate(shopping_results[:5], 1):
                title = item.get("title", "N/A")
                price = item.get("extracted_price", 0)
                source = item.get("source", "N/A")
                
                print(f"      {i}. ${price:.2f} - {title}")
                print(f"         from {source}")
            
            # Find lowest price
            prices = [item.get("extracted_price", 999) for item in shopping_results if item.get("extracted_price")]
            if prices:
                lowest = min(prices)
                print(f"\n   💰 Lowest Price: ${lowest:.2f}")
        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n{'=' * 80}")
    print("✅ Test complete!")


def test_full_cart_with_official_lib():
    """Test a full cart using official library"""
    
    print("\n" + "=" * 80)
    print("🛒 FULL CART TEST - Official Library")
    print("=" * 80)
    
    cart_items = [
        "whole milk gallon",
        "large eggs",
        "white bread loaf"
    ]
    
    location = "33773"
    all_results = {}
    
    for item in cart_items:
        print(f"\n🔍 Searching for: '{item}'")
        
        params = {
            "engine": "google_shopping",
            "q": item,
            "location": f"United States, {location}",
            "google_domain": "google.com",
            "hl": "en",
            "gl": "us",
            "num": 40,
            "api_key": API_KEY
        }
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            shopping_results = results.get("shopping_results", [])
            
            if shopping_results:
                print(f"   ✅ {len(shopping_results)} products found")
                
                # Parse into our format
                products = []
                for result in shopping_results:
                    if result.get("extracted_price"):
                        products.append({
                            "name": result.get("title", ""),
                            "price": result.get("extracted_price", 0),
                            "merchant": result.get("source", ""),
                            "rating": result.get("rating", None),
                            "review_count": result.get("reviews", None),
                            "link": result.get("link", ""),
                            "thumbnail": result.get("thumbnail", "")
                        })
                
                all_results[item] = products
                
                if products:
                    lowest = min(products, key=lambda x: x['price'])
                    print(f"   💰 Lowest: ${lowest['price']:.2f} at {lowest['merchant']}")
            else:
                print(f"   ⚠️  No results")
                all_results[item] = []
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            all_results[item] = []
    
    # Summary
    print(f"\n{'=' * 80}")
    print("📊 CART SUMMARY")
    print("=" * 80)
    
    total_lowest = 0
    for item, products in all_results.items():
        if products:
            lowest = min(products, key=lambda x: x['price'])
            print(f"\n✅ {item}:")
            print(f"   ${lowest['price']:.2f} at {lowest['merchant']}")
            total_lowest += lowest['price']
        else:
            print(f"\n❌ {item}: No results")
    
    print(f"\n{'─' * 80}")
    print(f"💰 Total Cart (Best Prices): ${total_lowest:.2f}")
    
    # Save
    with open("serpapi_full_cart_test.json", 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Saved to: serpapi_full_cart_test.json")


if __name__ == "__main__":
    # Test different bread queries
    test_bread_queries()
    
    # Test full cart
    test_full_cart_with_official_lib()

