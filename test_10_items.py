#!/usr/bin/env python3
"""
Test with 10 items - typical user cart
"""
import sys
sys.path.append('/root')
from uc_scraper import search_products
import time

print("="*80)
print("PRODUCTION TEST - 10 ITEM CART (Typical User)")
print("="*80)

items = [
    'milk', 'eggs', 'bread', 'butter', 'cheese',
    'chicken', 'rice', 'pasta', 'apples', 'bananas'
]

print(f"\nSearching {len(items)} items in NYC (ZIP 10001)...")
print("Wait times: 1s first, 0.5s subsequent (PROVEN)")
print("Expected: ~3s + (9 × 1.5s) = ~16-18s")

start = time.time()
results = search_products(
    search_terms=items,
    zip_code='10001',
    max_products_per_item=5,
    use_parallel=False
)
elapsed = time.time() - start

print(f"\n{'='*80}")
print("RESULTS")
print(f"{'='*80}")

print(f"\n⏱️  Total time: {elapsed:.1f} seconds")
print(f"📊 Average per item: {elapsed/len(items):.1f}s")

success_count = 0
stores = set()
for item, products in results.items():
    if products:
        success_count += 1
        cheapest = min(products, key=lambda p: p['price'])
        stores.add(cheapest['merchant'])
        print(f"✅ {item}: ${cheapest['price']} @ {cheapest['merchant']}")

print(f"\n📊 Summary:")
print(f"   • {success_count}/{len(items)} items found products")
print(f"   • {len(stores)} unique stores")
print(f"   • {elapsed:.1f}s total time")

if success_count == len(items) and elapsed < 30:
    print(f"\n🚀 EXCELLENT! All items in under 30 seconds!")
    print(f"\n💡 For production with 25K users:")
    print(f"   • 100 droplets × 3 browsers = 300 concurrent scrapers")
    print(f"   • ~{elapsed:.1f}s per user")
    print(f"   • Can handle 300 users every {elapsed:.1f}s")
    print(f"   • = ~{int(300 / (elapsed/60))}/minute = ~{int(300 * 60 / elapsed)}/hour capacity")
elif success_count == len(items):
    print(f"\n✅ All items found, but slower than ideal ({elapsed:.1f}s)")
else:
    print(f"\n⚠️  Only {success_count}/{len(items)} items have results")

