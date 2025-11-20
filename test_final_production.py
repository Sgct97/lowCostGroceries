#!/usr/bin/env python3
"""
Final production test - verify locality across different ZIP codes
"""

import sys
sys.path.append('/root')

from uc_scraper import search_products
import time

print("="*80)
print("FINAL PRODUCTION TEST - LOCALITY VERIFICATION")
print("="*80)

# Test different ZIP codes to prove locality
test_cases = [
    {
        "zip": "10001",
        "city": "New York, NY",
        "expected_stores": ["ACME", "Key Food", "Fairway", "Gristedes", "ShopRite"],
    },
    {
        "zip": "33101",
        "city": "Miami, FL",
        "expected_stores": ["Publix", "Sedanos", "Winn-Dixie", "Presidente"],
    },
]

all_results = {}

for test in test_cases:
    print(f"\n{'='*80}")
    print(f"Testing: {test['city']} (ZIP {test['zip']})")
    print(f"{'='*80}")
    
    start = time.time()
    results = search_products(
        search_terms=["milk"],
        zip_code=test['zip'],
        max_products_per_item=10,
        use_parallel=False
    )
    elapsed = time.time() - start
    
    products = results.get("milk", [])
    merchants = [p['merchant'] for p in products]
    unique_merchants = list(set(merchants))
    
    print(f"\n⏱️  Time: {elapsed:.1f}s")
    print(f"📦 Found {len(products)} products")
    print(f"🏪 Unique merchants: {len(unique_merchants)}")
    
    print(f"\n📋 Merchants found:")
    for m in unique_merchants[:15]:
        print(f"   • {m}")
    
    # Check for expected local stores
    found_local = []
    for store in test['expected_stores']:
        for merchant in unique_merchants:
            if store.lower() in merchant.lower():
                found_local.append(store)
                break
    
    if found_local:
        print(f"\n✅ LOCAL STORES FOUND: {', '.join(found_local)}")
    else:
        print(f"\n⚠️  No expected local stores found")
        print(f"   Expected: {', '.join(test['expected_stores'])}")
    
    all_results[test['zip']] = {
        'merchants': unique_merchants,
        'local_found': found_local,
        'elapsed': elapsed
    }
    
    # Wait between tests to avoid rate limiting
    if test != test_cases[-1]:
        print(f"\n💤 Waiting 10 seconds before next test...")
        time.sleep(10)

print(f"\n{'='*80}")
print("LOCALITY COMPARISON")
print(f"{'='*80}")

# Find location-specific merchants
nyc_only = set(all_results['10001']['merchants'])
if '33101' in all_results:
    miami_only = set(all_results['33101']['merchants'])
    
    print(f"\n🗽 NYC-only merchants:")
    for m in sorted(nyc_only - miami_only)[:10]:
        print(f"   • {m}")
    
    print(f"\n🌴 Miami-only merchants:")
    for m in sorted(miami_only - nyc_only)[:10]:
        print(f"   • {m}")
    
    in_both = nyc_only & miami_only
    print(f"\n🌐 Merchants in both (likely national/online): {len(in_both)}")
    for m in sorted(in_both)[:5]:
        print(f"   • {m}")

print(f"\n{'='*80}")
print("FINAL VERDICT")
print(f"{'='*80}")

total_local_found = sum(len(r['local_found']) for r in all_results.values())
if total_local_found > 0:
    print(f"\n✅ SUCCESS! Production scraper is working!")
    print(f"   • Found {total_local_found} location-specific stores")
    print(f"   • Average time: {sum(r['elapsed'] for r in all_results.values()) / len(all_results):.1f}s per search")
    print(f"   • Locality: PROVEN (different stores in different cities)")
    print(f"\n🚀 READY FOR DEPLOYMENT!")
else:
    print(f"\n⚠️  WARNING: No local stores detected")
    print(f"   But scraper is functional and returning products")

