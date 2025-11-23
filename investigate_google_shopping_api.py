#!/usr/bin/env python3
"""
Investigate if Google Shopping has a hidden JSON API endpoint
"""

import requests
import json
from urllib.parse import quote

def test_google_shopping_json_endpoints():
    """Test various potential JSON API endpoints"""
    
    print("=" * 80)
    print("🔍 HUNTING FOR GOOGLE SHOPPING JSON API")
    print("=" * 80)
    
    query = "large eggs, 33773 nearby"
    
    # Potential JSON endpoints based on common Google API patterns
    test_endpoints = [
        # Standard search with JSON format
        {
            "name": "Search API with JSON output",
            "url": f"https://www.google.com/search?q={quote(query)}&udm=28&output=json"
        },
        # Google Shopping specific
        {
            "name": "Shopping API endpoint",
            "url": f"https://www.google.com/shopping/api/search?q={quote(query)}"
        },
        # RPC/BatchExecute (Google's internal API pattern)
        {
            "name": "BatchExecute RPC",
            "url": "https://www.google.com/_/shopping/api/batchexecute",
            "method": "POST"
        },
        # Async endpoint (common Google pattern)
        {
            "name": "Async Shopping API",
            "url": f"https://www.google.com/async/shopping?q={quote(query)}"
        },
        # Shopping collection (seen in network tab)
        {
            "name": "Shopping Collection",
            "url": f"https://www.google.com/shopping/collection?q={quote(query)}"
        },
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    for endpoint in test_endpoints:
        print(f"\n{'─' * 80}")
        print(f"🧪 Testing: {endpoint['name']}")
        print(f"   URL: {endpoint['url']}")
        
        try:
            if endpoint.get('method') == 'POST':
                response = requests.post(endpoint['url'], headers=headers, timeout=10)
            else:
                response = requests.get(endpoint['url'], headers=headers, timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            # Check if it's JSON
            content_type = response.headers.get('content-type', '')
            print(f"   Content-Type: {content_type}")
            
            if 'json' in content_type.lower():
                print(f"   ✅ JSON response detected!")
                # Save it
                filename = f"google_api_test_{endpoint['name'].replace(' ', '_')}.json"
                with open(filename, 'w') as f:
                    json.dump(response.json(), f, indent=2)
                print(f"   💾 Saved to: {filename}")
            else:
                print(f"   ℹ️  Not JSON (likely HTML)")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")


def analyze_browser_network_traffic():
    """Guide for manual investigation"""
    
    print("\n\n" + "=" * 80)
    print("🔬 MANUAL INVESTIGATION GUIDE")
    print("=" * 80)
    
    print("""
1. Open Chrome DevTools (Network tab)
2. Go to: https://www.google.com/search?udm=28&q=eggs, 33773 nearby
3. Filter by 'Fetch/XHR'
4. Look for endpoints that return JSON with product data

Common patterns to look for:
   • /async/ endpoints
   • /batchexecute endpoints
   • /_/shopping/ endpoints
   • Responses with 'shopping_results' or product data

If you find a JSON endpoint, share the:
   • Full URL
   • Request headers
   • Request payload (if POST)
   • Response structure
    """)


def check_serpapi_documentation():
    """Look for clues in SerpAPI's own docs"""
    
    print("\n" + "=" * 80)
    print("💡 SERPAPI CLUES")
    print("=" * 80)
    
    print("""
From SerpAPI response, they show:
   google_shopping_url: https://www.google.com/search?udm=28&q=...

Key insights:
   1. They're hitting the SAME URL we tried
   2. But getting clean JSON back
   3. Response time: 1-6 seconds
   
This suggests:
   • They've figured out how to parse HTML VERY efficiently
   • OR they're caching aggressively
   • OR they have a special arrangement with Google
   • OR they found an undocumented JSON endpoint

Most likely: They're running scrapers at MASSIVE scale
   • Shared proxy pool across all customers
   • Pre-warming cache for popular queries
   • Distributed parsing infrastructure
   • One request can serve multiple customers
    """)


def economics_analysis():
    """Analyze the economics to understand their approach"""
    
    print("\n" + "=" * 80)
    print("💰 ECONOMICS ANALYSIS")
    print("=" * 80)
    
    print("""
SerpAPI Pricing: $50/month for 5,000 searches = $0.01 per search

If they used residential proxies per request:
   • Residential proxy: $0.01-0.03 per request
   • Already at or over the $0.01 they charge!
   
Therefore, they MUST be:
   1. Amortizing proxy costs across many customers
   2. Using datacenter proxies (cheaper but more blocking)
   3. Caching aggressively
   4. Batch processing requests
   5. OR have found a cheaper data source

The speed (1-2 seconds) suggests:
   • NOT browser automation (too slow)
   • Likely direct HTTP with smart parsing
   • Possibly pre-cached for popular queries
   • High-performance infrastructure

Conclusion:
   • They've optimized at massive scale
   • You'd need 1000s of customers to match their efficiency
   • Better to pay them than replicate their infrastructure
    """)


if __name__ == "__main__":
    # Test potential API endpoints
    test_google_shopping_json_endpoints()
    
    # Manual investigation guide
    analyze_browser_network_traffic()
    
    # Check SerpAPI clues
    check_serpapi_documentation()
    
    # Economics
    economics_analysis()
    
    print("\n" + "=" * 80)
    print("✅ Investigation complete!")
    print("=" * 80)
    print("""
NEXT STEPS:
1. Try the manual Chrome DevTools investigation
2. If you find a JSON endpoint, we can use it directly
3. Otherwise, SerpAPI is likely the most cost-effective solution
    """)

