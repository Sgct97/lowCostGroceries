"""
CRITICAL TEST: Can we reuse ONE callback URL for MULTIPLE queries?

The hybrid architecture ONLY works if:
1. UC captures callback URL ONCE
2. We modify the query parameter 
3. curl_cffi works for ALL queries

If this fails, the hybrid architecture doesn't scale.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from token_service import TokenService
from curl_cffi import requests
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def modify_callback_query(callback_url, new_query):
    """Try to modify the query parameter in callback URL"""
    # Callback URLs look like:
    # https://www.google.com/async/callback:6948?fc=...&q=laptop&...
    
    # Method 1: Simple string replace
    if '&q=' in callback_url:
        modified = re.sub(r'&q=[^&]+', f'&q={new_query}', callback_url)
        return modified
    elif '?q=' in callback_url:
        modified = re.sub(r'\?q=([^&]+)', f'?q={new_query}', callback_url)
        return modified
    else:
        # No query parameter found, return original
        return callback_url

def test_query(url, query_name):
    """Test a query with curl_cffi"""
    try:
        r = requests.get(
            url,
            impersonate='chrome120',
            timeout=30,
            headers={'referer': 'https://shopping.google.com/'}
        )
        
        prices = re.findall(r'\$([0-9,]+\.[0-9]{2})', r.text)
        return {
            'status': r.status_code,
            'prices': len(prices),
            'success': r.status_code == 200 and len(prices) > 0
        }
    except Exception as e:
        return {
            'status': 0,
            'prices': 0,
            'success': False,
            'error': str(e)
        }

print("\n" + "="*80)
print("CRITICAL TEST: Callback URL Reuse for Multiple Queries")
print("="*80 + "\n")

# STEP 1: Capture ONE callback URL with UC (for "laptop")
print("STEP 1: Capturing ONE callback URL with UC (test query: laptop)...")
service = TokenService()
original_callback = service.capture_callback_url(region='US', test_query='laptop')

if not original_callback:
    print("❌ FAILED: Could not capture initial callback URL")
    exit(1)

print(f"✅ Captured: {original_callback[:100]}...")

# STEP 2: Test original query
print("\nSTEP 2: Testing ORIGINAL query (laptop)...")
result_laptop = test_query(original_callback, 'laptop')
print(f"   Status: {result_laptop['status']}, Prices: {result_laptop['prices']}")

# STEP 3: Modify for grocery queries and test with curl_cffi ONLY
grocery_queries = ['milk', 'eggs', 'bread', 'chicken', 'cheese']

print("\n" + "="*80)
print("STEP 3: Testing MODIFIED queries with curl_cffi (NO MORE UC!)")
print("="*80 + "\n")

results = []

for query in grocery_queries:
    print(f"Testing: {query.upper()}")
    
    # Modify callback URL
    modified_url = modify_callback_query(original_callback, query)
    
    if modified_url == original_callback:
        print(f"   ⚠️  Could not modify URL for '{query}'")
        continue
    
    # Test with curl_cffi
    result = test_query(modified_url, query)
    results.append({
        'query': query,
        **result
    })
    
    if result['success']:
        print(f"   ✅ {result['prices']} prices found")
    else:
        print(f"   ❌ Failed: Status {result['status']}, {result['prices']} prices")

# SUMMARY
print("\n" + "="*80)
print("RESULTS")
print("="*80 + "\n")

success_count = sum(1 for r in results if r['success'])
total = len(results)

print(f"Successful queries: {success_count}/{total}")

for r in results:
    status = "✅" if r['success'] else "❌"
    print(f"  {status} {r['query']}: {r['prices']} prices (status {r['status']})")

print("\n" + "="*80)
if success_count == total:
    print("🎉🎉🎉 PERFECT! HYBRID ARCHITECTURE SCALES! 🎉🎉🎉")
    print("   - 1 UC capture works for ALL queries")
    print("   - curl_cffi for everything else")
    print("   - Ready for 25K users!")
elif success_count > 0:
    print(f"⚠️  PARTIAL SUCCESS: {success_count}/{total} queries worked")
    print("   - Some query modification works")
    print("   - Need to debug failed queries")
else:
    print("❌ FAILURE: Cannot reuse callback URLs")
    print("   - Hybrid architecture won't scale")
    print("   - Need different approach")
print("="*80 + "\n")

