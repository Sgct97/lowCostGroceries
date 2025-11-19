"""
Test TokenService reliability: Run 5 captures to verify consistency
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from token_service import TokenService
from curl_cffi import requests
import re
import logging

logging.basicConfig(level=logging.WARNING)  # Less verbose

print("\n" + "="*80)
print("RELIABILITY TEST: 5 Consecutive Captures")
print("="*80 + "\n")

service = TokenService()
results = []

for i in range(1, 6):
    print(f"\nTest {i}/5:")
    print("-" * 40)
    
    # Capture callback URL
    callback_url = service.capture_callback_url(region='US', test_query='laptop')
    
    if not callback_url:
        print(f"❌ FAILED to capture")
        results.append({'test': i, 'captured': False, 'prices': 0})
        continue
    
    print(f"✅ Captured: {callback_url[:80]}...")
    
    # Test immediately with curl_cffi
    try:
        r = requests.get(
            callback_url,
            impersonate='chrome120',
            timeout=30,
            headers={'referer': 'https://shopping.google.com/'}
        )
        
        prices = re.findall(r'\$([0-9,]+\.[0-9]{2})', r.text)
        print(f"✅ curl_cffi: {r.status_code}, {len(prices)} prices")
        
        results.append({
            'test': i,
            'captured': True,
            'status': r.status_code,
            'prices': len(prices),
            'success': r.status_code == 200 and len(prices) > 0
        })
    except Exception as e:
        print(f"❌ curl_cffi error: {e}")
        results.append({
            'test': i,
            'captured': True,
            'status': 0,
            'prices': 0,
            'success': False
        })

# Summary
print("\n" + "="*80)
print("RELIABILITY SUMMARY")
print("="*80 + "\n")

captured_count = sum(1 for r in results if r['captured'])
success_count = sum(1 for r in results if r.get('success', False))

print(f"Captured: {captured_count}/5 ({captured_count/5*100:.0f}%)")
print(f"Full Success: {success_count}/5 ({success_count/5*100:.0f}%)")

for r in results:
    if r.get('success'):
        print(f"  Test {r['test']}: ✅ {r['prices']} prices")
    elif r['captured']:
        print(f"  Test {r['test']}: ⚠️  Captured but {r['status']} / {r['prices']} prices")
    else:
        print(f"  Test {r['test']}: ❌ Failed to capture")

print("\n" + "="*80)
if success_count >= 4:
    print("✅ RELIABLE: 80%+ success rate - Production ready!")
elif success_count >= 3:
    print("⚠️  ACCEPTABLE: 60%+ success rate - May need tuning")
else:
    print("❌ UNRELIABLE: <60% success rate - NOT production ready")
print("="*80 + "\n")

stats = service.get_stats()
print(f"Service stats: {stats}")

