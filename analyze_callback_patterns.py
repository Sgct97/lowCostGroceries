"""
Analyze captured callback URLs to reverse engineer the pattern
"""

import json
import base64
import urllib.parse
import re
from difflib import SequenceMatcher

print("\n" + "="*80)
print("CALLBACK URL PATTERN ANALYSIS")
print("="*80 + "\n")

# Load captured data
with open('captured_callbacks.json', 'r') as f:
    data = json.load(f)

if len(data) < 2:
    print("❌ Need at least 2 callback URLs for comparison")
    exit(1)

print(f"Analyzing {len(data)} captured callback URLs:\n")

# Extract and analyze each URL
for item in data:
    query = item['query']
    url = item['url']
    
    print(f"{query.upper()}:")
    print(f"  Full URL length: {len(url)}")
    
    # Extract fc parameter
    fc_match = re.search(r'fc=([^&]+)', url)
    if fc_match:
        fc_encoded = fc_match.group(1)
        fc_decoded_url = urllib.parse.unquote(fc_encoded)
        
        print(f"  FC parameter length: {len(fc_decoded_url)}")
        print(f"  FC (first 60 chars): {fc_decoded_url[:60]}...")
        
        # Try base64 decode
        try:
            decoded = base64.b64decode(fc_decoded_url)
            decoded_str = decoded.decode('utf-8', errors='ignore')
            
            # Check if query appears in decoded string
            if query.lower() in decoded_str.lower():
                print(f"  ✅ FOUND '{query}' in decoded FC!")
                # Show context around the query
                idx = decoded_str.lower().find(query.lower())
                context_start = max(0, idx - 20)
                context_end = min(len(decoded_str), idx + len(query) + 20)
                print(f"     Context: ...{decoded_str[context_start:context_end]}...")
            else:
                print(f"  ❌ Query '{query}' NOT in decoded FC")
                # Show first 100 chars of decoded
                print(f"     Decoded (first 100): {decoded_str[:100]}...")
                
        except Exception as e:
            print(f"  ⚠️  Base64 decode error: {e}")
    
    # Extract other key parameters
    ei_match = re.search(r'ei=([^&]+)', url)
    if ei_match:
        print(f"  ei parameter: {ei_match.group(1)}")
    
    print()

# COMPARE FC PARAMETERS
print("\n" + "="*80)
print("FC PARAMETER COMPARISON")
print("="*80 + "\n")

fc_params = []
for item in data:
    fc_match = re.search(r'fc=([^&]+)', item['url'])
    if fc_match:
        fc_decoded = urllib.parse.unquote(fc_match.group(1))
        fc_params.append({
            'query': item['query'],
            'fc': fc_decoded
        })

if len(fc_params) >= 2:
    # Compare first two
    fc1 = fc_params[0]['fc']
    fc2 = fc_params[1]['fc']
    q1 = fc_params[0]['query']
    q2 = fc_params[1]['query']
    
    # Find similarity
    similarity = SequenceMatcher(None, fc1, fc2).ratio()
    print(f"Similarity between {q1} and {q2}: {similarity*100:.1f}%\n")
    
    # Find common subsequences
    matcher = SequenceMatcher(None, fc1, fc2)
    common_blocks = matcher.get_matching_blocks()
    
    print(f"Common blocks: {len(common_blocks)}")
    for block in common_blocks[:5]:  # Show first 5
        i, j, size = block.a, block.b, block.size
        if size > 10:  # Only show substantial matches
            print(f"  Position {i}-{i+size}: '{fc1[i:i+size][:40]}...'")
    
    print()

# TRY TO FIND QUERY ENCODING
print("\n" + "="*80)
print("LOOKING FOR QUERY ENCODING IN FC")
print("="*80 + "\n")

for fc_param in fc_params:
    query = fc_param['query']
    fc = fc_param['fc']
    
    print(f"\n{query.upper()}:")
    
    # Check if query appears anywhere (case-insensitive)
    if query.lower() in fc.lower():
        idx = fc.lower().find(query.lower())
        print(f"  ✅ Found '{query}' at position {idx} in FC (plaintext!)")
        context = fc[max(0,idx-20):min(len(fc),idx+len(query)+20)]
        print(f"     Context: ...{context}...")
        continue
    
    # Try base64 encoding the query and see if it appears
    query_b64 = base64.b64encode(query.encode()).decode()
    if query_b64 in fc:
        print(f"  ✅ Found base64('{query}') = '{query_b64}' in FC!")
        continue
    
    # Try URL encoding
    query_url = urllib.parse.quote(query)
    if query_url in fc:
        print(f"  ✅ Found url-encoded '{query}' in FC!")
        continue
    
    print(f"  ❌ Query not found in FC (plaintext, base64, or url-encoded)")

# CRITICAL TEST: Can we build a callback URL from scratch?
print("\n" + "="*80)
print("CRITICAL QUESTION")
print("="*80 + "\n")

print("Can we predict/generate FC parameter for a new query?")
print("  - If YES → We can scrape any product without UC")
print("  - If NO → We need UC for each unique query")
print()
print("Next step: Analyze what else is in FC besides the query...")
print("  (session tokens, timestamps, random IDs, etc.)")
print("="*80 + "\n")

