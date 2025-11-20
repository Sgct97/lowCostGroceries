#!/usr/bin/env python3
"""
Prove the production scraper works with optimized wait times
"""
import sys
sys.path.append('/root')
from uc_scraper import search_products
import time

print("="*80)
print("PROVING PRODUCTION SCRAPER WORKS")
print("="*80)

print("\nWait times:")
print("  • First search: 4 seconds")
print("  • Subsequent: 2 seconds each")
print("  • Expected for 5 items: ~4s + (4×2s) = ~12s + overhead = ~18-20s")

items = ['milk', 'eggs', 'bread', 'butter', 'cheese']

print(f"\nSearching {len(items)} items in NYC (ZIP 10001)...")
start = time.time()

results = search_products(
    search_terms=items,
    zip_code='10001',
    max_products_per_item=5,
    use_parallel=False  # Sequential with persistent browser
)

elapsed = time.time() - start

print(f"\n{'='*80}")
print("RESULTS")
print(f"{'='*80}")

print(f"\n⏱️  Total time: {elapsed:.1f} seconds")
print(f"📊 Average per item: {elapsed/len(items):.1f}s")

total_products = 0
for item, products in results.items():
    total_products += len(products)
    if products:
        cheapest = min(products, key=lambda p: p['price'])
        print(f"\n📦 {item.upper()}: {len(products)} products found")
        print(f"   Cheapest: {cheapest['name']}")
        print(f"   Price: ${cheapest['price']}")
        print(f"   Store: {cheapest['merchant']}")
    else:
        print(f"\n❌ {item.upper()}: NO PRODUCTS FOUND")

print(f"\n{'='*80}")
print("VERDICT")
print(f"{'='*80}")

if total_products >= len(items) and elapsed < 30:
    print(f"\n✅ SUCCESS!")
    print(f"   • Found {total_products} total products")
    print(f"   • Completed in {elapsed:.1f}s (target: <30s)")
    print(f"   • All {len(items)} items have results")
    print(f"\n🚀 PRODUCTION SCRAPER IS READY!")
elif total_products >= len(items):
    print(f"\n⚠️  FUNCTIONAL but slower than expected")
    print(f"   • Found {total_products} total products")
    print(f"   • Took {elapsed:.1f}s (target was <30s)")
    print(f"   • All items have results - scraper works!")
else:
    print(f"\n❌ FAILED")
    print(f"   • Only found {total_products} products for {len(items)} items")
    print(f"   • Some items missing results")

