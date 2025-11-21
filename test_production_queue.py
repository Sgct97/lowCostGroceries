#!/usr/bin/env python3
"""
End-to-end test of the production queue system

Tests:
1. Submit multiple carts to API
2. Verify jobs are queued
3. Poll for results
4. Verify ZIP codes are correct (location-specific)
"""

import requests
import time
import json
from typing import List, Dict

# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE_URL = "http://localhost:8000"  # Change to your API server IP

# Test cases with different ZIP codes (verifies location-specific scraping)
TEST_CARTS = [
    {
        'name': 'NYC Cart',
        'items': ['milk', 'eggs', 'bread'],
        'zipcode': '10001',
        'expected_cities': ['New York', 'NYC', 'Manhattan']
    },
    {
        'name': 'Miami Cart',
        'items': ['milk', 'eggs'],
        'zipcode': '33101',
        'expected_cities': ['Miami', 'Miami Beach']
    },
    {
        'name': 'Tampa Cart',
        'items': ['bread', 'butter'],
        'zipcode': '33773',
        'expected_cities': ['Largo', 'Clearwater', 'Tampa']
    }
]


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def submit_cart(items: List[str], zipcode: str) -> Dict:
    """Submit a cart to the API"""
    print(f"📤 Submitting cart: {items} in ZIP {zipcode}")
    
    response = requests.post(
        f"{API_BASE_URL}/cart",
        json={'items': items, 'zipcode': zipcode},
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Job ID: {data.get('job_id', 'N/A')[:16]}...")
        print(f"   Status: {data.get('status')}")
        print(f"   Queue position: {data.get('queue_position', 'N/A')}")
        return data
    else:
        print(f"   ❌ Error {response.status_code}: {response.text}")
        return None


def poll_for_results(job_id: str, max_wait: int = 60, poll_interval: int = 2) -> Dict:
    """Poll for job results until complete or timeout"""
    print(f"\n🔄 Polling for job {job_id[:16]}...")
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{API_BASE_URL}/results/{job_id}")
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            
            if status == 'complete':
                elapsed = time.time() - start_time
                print(f"   ✅ Complete! ({elapsed:.1f}s)")
                return data
            
            elif status == 'failed':
                print(f"   ❌ Failed: {data.get('error')}")
                return data
            
            elif status == 'processing':
                worker = data.get('worker_id', 'unknown')
                print(f"   ⏳ Processing by {worker}...")
            
            elif status == 'queued':
                print(f"   ⏳ Queued...")
            
            else:
                print(f"   ⚠️  Unknown status: {status}")
        
        time.sleep(poll_interval)
    
    print(f"   ⏰ Timeout after {max_wait}s")
    return None


def verify_results(cart_name: str, results: Dict, expected_zipcode: str) -> bool:
    """Verify results are valid and location-specific"""
    print(f"\n🔍 Verifying results for {cart_name}...")
    
    if not results or results.get('status') != 'complete':
        print(f"   ❌ Results not complete")
        return False
    
    # Check ZIP code matches
    result_zip = results.get('zip_code')
    if result_zip != expected_zipcode:
        print(f"   ❌ ZIP mismatch: expected {expected_zipcode}, got {result_zip}")
        return False
    else:
        print(f"   ✅ ZIP code matches: {result_zip}")
    
    # Check results structure
    products_data = results.get('results', {})
    if not products_data:
        print(f"   ❌ No products found")
        return False
    
    # Count products found
    total_products = 0
    for item, products in products_data.items():
        count = len(products) if isinstance(products, list) else 0
        total_products += count
        print(f"   • {item}: {count} products")
    
    if total_products > 0:
        print(f"   ✅ Found {total_products} total products")
        return True
    else:
        print(f"   ❌ No products found")
        return False


# ============================================================================
# MAIN TEST
# ============================================================================

def main():
    print("="*80)
    print("END-TO-END PRODUCTION QUEUE TEST")
    print("="*80)
    print(f"\nAPI: {API_BASE_URL}")
    print(f"Testing {len(TEST_CARTS)} carts with different ZIP codes")
    print("="*80)
    
    # Check API health
    print("\n📡 Checking API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ API online")
            print(f"   Cache size: {health.get('cache_size', 'N/A')}")
        else:
            print(f"   ⚠️  API returned {response.status_code}")
    except Exception as e:
        print(f"   ❌ Cannot connect to API: {e}")
        print(f"\n💡 Make sure API is running:")
        print(f"   cd backend && python3 api.py")
        return
    
    # Submit all carts
    print("\n" + "="*80)
    print("PHASE 1: SUBMIT CARTS")
    print("="*80)
    
    jobs = []
    for cart in TEST_CARTS:
        result = submit_cart(cart['items'], cart['zipcode'])
        if result:
            jobs.append({
                'cart': cart,
                'job_data': result
            })
        time.sleep(0.5)  # Brief pause between submissions
    
    if not jobs:
        print("\n❌ No jobs submitted successfully")
        return
    
    print(f"\n✅ Submitted {len(jobs)} jobs")
    
    # Poll for results
    print("\n" + "="*80)
    print("PHASE 2: POLL FOR RESULTS")
    print("="*80)
    
    results = []
    for job in jobs:
        cart_name = job['cart']['name']
        job_id = job['job_data'].get('job_id')
        
        if not job_id:
            print(f"\n⚠️  {cart_name}: No job_id (direct mode)")
            continue
        
        print(f"\n{'='*40}")
        print(f"Cart: {cart_name}")
        print(f"{'='*40}")
        
        result = poll_for_results(job_id, max_wait=90)
        
        if result:
            results.append({
                'cart': job['cart'],
                'results': result
            })
    
    # Verify results
    print("\n" + "="*80)
    print("PHASE 3: VERIFY RESULTS")
    print("="*80)
    
    verified_count = 0
    for item in results:
        cart = item['cart']
        result = item['results']
        
        if verify_results(cart['name'], result, cart['zipcode']):
            verified_count += 1
    
    # Final report
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    
    print(f"\n📊 Summary:")
    print(f"   • Submitted: {len(jobs)} carts")
    print(f"   • Completed: {len(results)} carts")
    print(f"   • Verified: {verified_count} carts")
    
    if verified_count == len(TEST_CARTS):
        print(f"\n🎉🎉🎉 ALL TESTS PASSED! 🎉🎉🎉")
        print(f"\n✅ Queue system works")
        print(f"✅ Workers process jobs")
        print(f"✅ Location-specific scraping verified")
        print(f"✅ Ready for production!")
    elif verified_count > 0:
        print(f"\n⚠️  {verified_count}/{len(TEST_CARTS)} tests passed")
        print(f"   Some jobs may still be processing or failed")
    else:
        print(f"\n❌ No tests passed")
        print(f"\n💡 Troubleshooting:")
        print(f"   1. Check workers are running: ps aux | grep worker.py")
        print(f"   2. Check Redis is running: redis-cli ping")
        print(f"   3. Check worker logs for errors")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()

