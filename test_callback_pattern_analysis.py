"""
Reverse engineer callback URL pattern by comparing different queries

Capture callbacks for: milk, eggs, bread, laptop, phone
Compare URLs to find:
1. What part encodes the query?
2. Can we modify it predictably?
3. Is there a pattern in the fc= parameter?
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from token_service import TokenService
from curl_cffi import requests
import re
import base64

def test_callback(url, expected_query):
    """Test what a callback URL returns"""
    try:
        r = requests.get(url, impersonate='chrome120', timeout=15, headers={'referer': 'https://shopping.google.com/'})
        if r.status_code != 200:
            return None
        
        prices = re.findall(r'\$[0-9,]+\.[0-9]{2}', r.text)
        query_mentions = r.text.lower().count(expected_query.lower())
        
        return {
            'status': r.status_code,
            'prices': len(prices),
            'query_mentions': query_mentions,
            'size': len(r.text)
        }
    except:
        return None

print("\n" + "="*80)
print("REVERSE ENGINEERING CALLBACK URL PATTERN")
print("="*80 + "\n")

service = TokenService()
test_queries = ['milk', 'eggs', 'bread']

captured_data = []

for query in test_queries:
    print(f"\nCapturing callback for: {query.upper()}")
    print("-" * 60)
    
    callback_url = service.capture_callback_url(region='US', test_query=query)
    
    if not callback_url:
        print(f"❌ Failed to capture for {query}")
        continue
    
    # Test it immediately
    result = test_callback(callback_url, query)
    
    if result:
        print(f"✅ Status: {result['status']}, Prices: {result['prices']}, Mentions: {result['query_mentions']}")
        
        # Extract key parts
        fc_match = re.search(r'fc=([^&]+)', callback_url)
        fc_value = fc_match.group(1) if fc_match else None
        
        captured_data.append({
            'query': query,
            'url': callback_url,
            'fc': fc_value,
            'result': result
        })
    else:
        print(f"⚠️  Callback expired or failed")

# ANALYSIS
print("\n" + "="*80)
print("PATTERN ANALYSIS")
print("="*80 + "\n")

if len(captured_data) < 2:
    print("❌ Need at least 2 successful captures to compare")
    exit(0)

# Compare fc parameters
print("FC Parameter Comparison:")
print("-" * 60)

for data in captured_data:
    fc = data['fc']
    print(f"\n{data['query'].upper()}:")
    print(f"  FC length: {len(fc)}")
    print(f"  First 80 chars: {fc[:80]}...")
    print(f"  Last 40 chars: ...{fc[-40:]}")
    
    # Try to decode if it's base64
    try:
        decoded = base64.b64decode(fc + '==')  # Add padding
        if data['query'].encode() in decoded:
            print(f"  ✅ Query '{data['query']}' found in decoded fc!")
    except:
        pass

# Look for common patterns
print("\n" + "="*80)
print("LOOKING FOR PATTERNS")
print("="*80 + "\n")

if len(captured_data) >= 2:
    fc1 = captured_data[0]['fc']
    fc2 = captured_data[1]['fc']
    
    # Find common prefix
    common_prefix_len = 0
    for i in range(min(len(fc1), len(fc2))):
        if fc1[i] == fc2[i]:
            common_prefix_len += 1
        else:
            break
    
    # Find common suffix
    common_suffix_len = 0
    for i in range(1, min(len(fc1), len(fc2)) + 1):
        if fc1[-i] == fc2[-i]:
            common_suffix_len += 1
        else:
            break
    
    print(f"Common prefix length: {common_prefix_len} chars")
    print(f"Common suffix length: {common_suffix_len} chars")
    
    if common_prefix_len > 0:
        print(f"\nCommon prefix: {fc1[:common_prefix_len]}")
    
    if common_suffix_len > 0:
        print(f"Common suffix: ...{fc1[-common_suffix_len:]}")
    
    # Compare different parts
    print(f"\n{captured_data[0]['query']} UNIQUE part: {fc1[common_prefix_len:-common_suffix_len if common_suffix_len > 0 else len(fc1)][:50]}...")
    print(f"{captured_data[1]['query']} UNIQUE part: {fc2[common_prefix_len:-common_suffix_len if common_suffix_len > 0 else len(fc2)][:50]}...")

# Try swapping fc between queries
print("\n" + "="*80)
print("TESTING FC SWAP")
print("="*80 + "\n")

if len(captured_data) >= 2:
    # Take milk's URL but with eggs' fc parameter
    url1 = captured_data[0]['url']
    fc2_value = captured_data[1]['fc']
    
    swapped_url = re.sub(r'fc=([^&]+)', f'fc={fc2_value}', url1)
    
    print(f"Testing {captured_data[0]['query']}'s URL with {captured_data[1]['query']}'s FC parameter...")
    result = test_callback(swapped_url, captured_data[1]['query'])
    
    if result:
        print(f"Status: {result['status']}, Prices: {result['prices']}")
        print(f"Mentions of '{captured_data[1]['query']}': {result['query_mentions']}")
        
        if result['query_mentions'] > 10:
            print(f"🎉 SUCCESS! FC parameter CONTROLS the query!")
            print(f"We can swap FC values to change queries!")
        else:
            print("⚠️  FC swap didn't change the results")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80 + "\n")

print("If FC parameter controls query:")
print("  ✅ We can build a lookup table: query -> FC value")
print("  ✅ Reuse callback URLs by swapping FC")
print("  ✅ Hybrid architecture WORKS!")
print("\nIf FC is random/session-specific:")
print("  ❌ Each query needs its own callback")
print("  ❌ Must use UC pooling approach")
print("="*80 + "\n")

