"""
TEST THE PAGINATION ENDPOINT - THE BREAKTHROUGH!

This URL has q= as a modifiable parameter!
"""

from curl_cffi import requests
import re
import os
from dotenv import load_dotenv

load_dotenv()

PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")

proxies = {
    "http": f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}",
    "https": f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}",
} if PROXY_USER else None

# Simplified version of the pagination URL
base_url = "https://www.google.com/search"

# Key parameters
params = {
    'q': 'QUERY_PLACEHOLDER',
    'udm': '28',
    'hl': 'en',
    'gl': 'us',
    'start': '0',
    'sa': 'N',
    'async': 'arc_id:test,_fmt:pc'
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

print("\n" + "="*80)
print("TESTING PAGINATION ENDPOINT WITH DIFFERENT QUERIES")
print("="*80 + "\n")

test_queries = ['milk', 'eggs', 'bread']

for query in test_queries:
    print(f"\nTesting: {query.upper()}")
    print("-" * 60)
    
    # Build URL with this query
    params['q'] = query
    url = base_url + '?' + '&'.join([f'{k}={v}' for k, v in params.items()])
    
    try:
        response = requests.get(
            url,
            headers=headers,
            proxies=proxies,
            impersonate="chrome120",
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Size: {len(response.text):,} bytes")
        
        # Look for prices
        prices = re.findall(r'\$[0-9,]+\.[0-9]{2}', response.text)
        print(f"Prices found: {len(prices)}")
        
        # Check if query term appears in results
        query_mentions = response.text.lower().count(query.lower())
        print(f"'{query}' mentioned: {query_mentions} times")
        
        if len(prices) > 0:
            print(f"✅ Sample prices: {prices[:5]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80 + "\n")

print("If prices found for all queries:")
print("  🎉 WE CAN SCRAPE ANY PRODUCT WITHOUT BROWSER AUTOMATION!")
print("  🎉 curl_cffi + this endpoint = SCALABLE SOLUTION!")
print("\nIf 0 prices:")
print("  Need to refine parameters or use full URL structure")
print("="*80 + "\n")
