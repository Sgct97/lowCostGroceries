"""
Capture callback URLs for multiple queries and save for analysis
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from token_service import TokenService
import json
import time

print("\n" + "="*80)
print("CAPTURING MULTIPLE CALLBACK URLs FOR PATTERN ANALYSIS")
print("="*80 + "\n")

service = TokenService()
test_queries = ['milk', 'eggs', 'bread', 'laptop', 'phone']

captured_data = []

for query in test_queries:
    print(f"\nCapturing callback for: {query.upper()}")
    print("-" * 60)
    
    callback_url = service.capture_callback_url(region='US', test_query=query)
    
    if callback_url:
        print(f"✅ Captured: {callback_url[:80]}...")
        captured_data.append({
            'query': query,
            'url': callback_url,
            'timestamp': time.time()
        })
    else:
        print(f"❌ Failed to capture for {query}")
    
    # Small delay between captures
    if query != test_queries[-1]:
        print("Waiting 2 seconds before next capture...")
        time.sleep(2)

# Save to file
with open('captured_callbacks.json', 'w') as f:
    json.dump(captured_data, f, indent=2)

print("\n" + "="*80)
print(f"✅ Captured {len(captured_data)}/{len(test_queries)} callback URLs")
print("Saved to: captured_callbacks.json")
print("="*80 + "\n")

print(f"Token service stats: {service.get_stats()}")

