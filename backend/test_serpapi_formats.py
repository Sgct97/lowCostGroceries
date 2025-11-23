from serpapi_scraper import SerpAPIGoogleShoppingScraper
import os

os.environ['SERPAPI_KEY'] = 'caaa674f50f87741ec1d523cf908d540b9538ef0b4426db9ddc175303c165c69'

scraper = SerpAPIGoogleShoppingScraper()

# Test different locations
test_cases = [
    ("large eggs", "33773", "Florida"),    # Florida
    ("large eggs", "90210", "California"), # California  
    ("large eggs", "10001", "New York"),   # NYC
]

print("=" * 80)
print("🧪 TESTING QUERY FORMAT ACROSS US")
print("=" * 80)

for query, zipcode, expected_state in test_cases:
    print(f"\n📍 Testing {zipcode} ({expected_state}):")
    print(f"   Query will be: '{query}, {zipcode} nearby'")
    
    results = scraper.search(query, zipcode, prioritize_nearby=True)
    
    if results:
        print(f"   ✅ {len(results)} in-store results")
        print(f"   Lowest: ${results[0]['price']:.2f} at {results[0]['merchant']}")
    else:
        print(f"   ❌ No results!")

print("\n✅ Format verification complete!")
