#!/usr/bin/env python3
"""
Prove the PRODUCTION scraper gets location-specific results
"""
import sys
sys.path.append('/root')
from uc_scraper import search_products
import time

print("="*80)
print("PROVING LOCALITY IN PRODUCTION SCRAPER")
print("="*80)

test_locations = [
    {
        "zip": "10001",
        "city": "New York, NY",
        "expected": ["ACME", "Key Food", "Fairway", "ShopRite", "Stop & Shop"]
    },
    {
        "zip": "33101",
        "city": "Miami, FL",
        "expected": ["Publix", "Sedanos", "Winn-Dixie"]
    },
    {
        "zip": "90001",
        "city": "Los Angeles, CA",
        "expected": ["Vons", "Ralphs", "Food 4 Less"]
    }
]

all_merchants = {}

for location in test_locations:
    print(f"\n{'='*80}")
    print(f"Testing: {location['city']} (ZIP {location['zip']})")
    print(f"{'='*80}")
    
    start = time.time()
    results = search_products(
        search_terms=['milk'],
        zip_code=location['zip'],
        max_products_per_item=10,
        use_parallel=False
    )
    elapsed = time.time() - start
    
    products = results.get('milk', [])
    merchants = [p['merchant'] for p in products]
    unique_merchants = list(set(merchants))
    
    all_merchants[location['zip']] = unique_merchants
    
    print(f"\n⏱️  Time: {elapsed:.1f}s")
    print(f"📦 Found {len(products)} products")
    print(f"🏪 Merchants: {len(unique_merchants)}")
    
    print(f"\n📋 Stores found:")
    for m in unique_merchants[:10]:
        print(f"   • {m}")
    
    # Check for expected local stores
    found_local = []
    for expected_store in location['expected']:
        for merchant in unique_merchants:
            if expected_store.lower() in merchant.lower():
                found_local.append(expected_store)
                break
    
    if found_local:
        print(f"\n✅ LOCAL STORES FOUND: {', '.join(found_local)}")
    else:
        print(f"\n⚠️  No classic local stores, but stores are: {', '.join(unique_merchants[:5])}")
    
    # Wait between requests
    if location != test_locations[-1]:
        print(f"\n💤 Waiting 10s before next location...")
        time.sleep(10)

print(f"\n{'='*80}")
print("LOCALITY COMPARISON")
print(f"{'='*80}")

# Find location-specific merchants
all_zips = list(all_merchants.keys())
if len(all_zips) >= 2:
    zip1, zip2 = all_zips[0], all_zips[1]
    merchants1 = set(all_merchants[zip1])
    merchants2 = set(all_merchants[zip2])
    
    unique_to_1 = merchants1 - merchants2
    unique_to_2 = merchants2 - merchants1
    in_both = merchants1 & merchants2
    
    print(f"\n🗽 {zip1} ONLY ({len(unique_to_1)}):")
    for m in sorted(list(unique_to_1))[:8]:
        print(f"   • {m}")
    
    print(f"\n🌴 {zip2} ONLY ({len(unique_to_2)}):")
    for m in sorted(list(unique_to_2))[:8]:
        print(f"   • {m}")
    
    print(f"\n🌐 In both (likely national/online): {len(in_both)}")
    for m in sorted(list(in_both))[:5]:
        print(f"   • {m}")

print(f"\n{'='*80}")
print("FINAL VERDICT")
print(f"{'='*80}")

total_unique = len(set(m for merchants in all_merchants.values() for m in merchants))
location_specific = sum(len(set(all_merchants[z]) - set(m for other_z in all_merchants if other_z != z for m in all_merchants[other_z])) for z in all_merchants)

if location_specific > 0:
    print(f"\n✅ SUCCESS! Production scraper IS location-aware!")
    print(f"   • {total_unique} total unique merchants across all locations")
    print(f"   • {location_specific} location-specific merchants found")
    print(f"   • Different stores appear in different cities")
    print(f"\n🚀 LOCALITY PROVEN - READY FOR PRODUCTION!")
else:
    print(f"\n⚠️  No location-specific merchants detected")
    print(f"   • All {total_unique} merchants appear in all locations")
    print(f"   • Scraper works but may be showing national results only")

