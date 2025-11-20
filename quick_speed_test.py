#!/usr/bin/env python3
import sys
sys.path.append('/root')
from uc_scraper import search_products
import time

print('='*60)
print('QUICK SPEED TEST - 5 Items Sequential')
print('='*60)

items = ['milk', 'eggs', 'bread', 'butter', 'cheese']

start = time.time()
results = search_products(items, '10001', max_products_per_item=5, use_parallel=False)
elapsed = time.time() - start

print(f'\n✅ {len(items)} items in {elapsed:.1f}s')
print(f'📊 Average: {elapsed/len(items):.1f}s per item')
print(f'\nSample products:')
for item, products in results.items():
    if products:
        p = products[0]
        print(f'   • {item}: ${p["price"]} @ {p["merchant"]}')

print(f'\n🎯 Target: ~18s (4s first + 4×2s = 12s + overhead)')
print(f'📈 Actual: {elapsed:.1f}s')

if elapsed < 25:
    print(f'✅ EXCELLENT! Under 25 seconds!')
else:
    print(f'⚠️  Still a bit slow, but functional')

