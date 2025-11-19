import sys
sys.path.insert(0, 'backend')

from scraper import GoogleShoppingScraper

# Test WITHOUT proxies first
scraper = GoogleShoppingScraper(proxy_pool=None)

print("="*80)
print("TESTING UPDATED SCRAPER WITH REGEX PARSING")
print("="*80)

products = scraper.search("macbook pro", limit=10)

print("\n" + "="*80)
print(f"RESULTS: {len(products)} products")
print("="*80)

for i, p in enumerate(products[:10], 1):
    print(f"\n{i}. {p['title']}")
    print(f"   💰 ${p['price']}")
    if p['merchant']:
        print(f"   🏪 {p['merchant']}")

if products:
    print("\n✅ SUCCESS! Regex parsing WORKS!")
else:
    print("\n❌ No products found. Check latest_search.html")
