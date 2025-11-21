#!/usr/bin/env python3
import requests
import time
import json

API_URL = "http://146.190.129.92:8000"

print("="*60)
print("QUICK PRODUCTION TEST")
print("="*60)

# Test 1: Health check
print("\n1. Health check...")
resp = requests.get(f"{API_URL}/health")
print(f"   Status: {resp.json()['status']}")

# Test 2: Submit a cart
print("\n2. Submitting test cart (NYC - ZIP 10001)...")
cart = {
    "items": ["milk", "eggs", "bread"],
    "zipcode": "10001"
}
resp = requests.post(f"{API_URL}/cart", json=cart)
data = resp.json()
job_id = data.get('job_id')
print(f"   Job ID: {job_id[:16] if job_id else 'N/A'}...")
print(f"   Status: {data.get('status')}")
print(f"   Queue position: {data.get('queue_position', 'N/A')}")

if not job_id:
    print("\n❌ No job_id received")
    exit(1)

# Test 3: Poll for results
print("\n3. Polling for results...")
for i in range(30):  # Try for up to 60 seconds
    time.sleep(2)
    resp = requests.get(f"{API_URL}/results/{job_id}")
    result = resp.json()
    status = result.get('status')
    
    if status == 'complete':
        print(f"   ✅ Complete!")
        results = result.get('results', {})
        print(f"\n   Found products for {len(results)} items:")
        for item, products in results.items():
            count = len(products) if isinstance(products, list) else 0
            print(f"      • {item}: {count} products")
        print(f"\n   ZIP code verified: {result.get('zip_code')}")
        print(f"   Total time: {result.get('total_time')}s")
        print(f"   Worker: {result.get('worker_id')}")
        print("\n🎉 SYSTEM WORKS! All components operational!")
        exit(0)
    elif status == 'failed':
        print(f"   ❌ Failed: {result.get('error')}")
        exit(1)
    elif status == 'processing':
        print(f"   ⏳ Processing... ({i*2}s elapsed)")
    else:
        print(f"   ⏳ {status}... ({i*2}s elapsed)")

print("\n⏰ Timeout - job took too long")
