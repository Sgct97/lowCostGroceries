#!/usr/bin/env python3
"""
Reverse engineer SerpAPI to understand what they're doing
"""

import urllib.parse
import base64
import requests
from bs4 import BeautifulSoup

def decode_serpapi_url():
    """Analyze the URL that SerpAPI is using"""
    
    print("=" * 80)
    print("🔍 REVERSE ENGINEERING SERPAPI")
    print("=" * 80)
    
    # The URL from SerpAPI response
    serpapi_url = "https://www.google.com/search?udm=28&q=whole+milk+gallon%2C++33773+nearby+&uule=w+CAIQICIbMzM3NzMsRmxvcmlkYSxVbml0ZWQgU3RhdGVz&hl=en&gl=us"
    
    # Parse it
    parsed = urllib.parse.urlparse(serpapi_url)
    params = urllib.parse.parse_qs(parsed.query)
    
    print(f"\n📋 URL BREAKDOWN:")
    print(f"   Base: {parsed.scheme}://{parsed.netloc}{parsed.path}")
    print(f"\n   Parameters:")
    for key, value in params.items():
        print(f"      {key} = {value[0]}")
    
    # The mysterious 'uule' parameter
    uule = params['uule'][0]
    print(f"\n🔐 UULE Parameter Analysis:")
    print(f"   Raw: {uule}")
    print(f"   This is a Google-encoded location string")
    
    # The 'udm' parameter
    print(f"\n📦 UDM Parameter:")
    print(f"   udm=28 means 'Google Shopping' search type")
    print(f"   (udm stands for 'Unified Data Model')")
    
    return {
        'base_url': 'https://www.google.com/search',
        'udm': '28',  # Shopping
        'query': 'whole milk gallon, 33773 nearby',
        'uule': uule,
        'hl': 'en',
        'gl': 'us'
    }


def generate_uule(location: str) -> str:
    """
    Generate Google's UULE (Unsigned URL Encoded Location) parameter
    
    Format: "w+[base64 encoded location string]"
    """
    # The location string format Google expects
    # From the decoded example: "33773,Florida,United States"
    
    # This is a simplified version - real UULE encoding is more complex
    # But we can try the basic format
    location_bytes = location.encode('utf-8')
    encoded = base64.b64encode(location_bytes).decode('utf-8')
    
    # Google's format seems to be: "w+" + custom_encoding
    # Let's try the example pattern
    return f"w+{encoded}"


def test_direct_google_request():
    """Try to hit Google Shopping directly with our own request"""
    
    print("\n\n" + "=" * 80)
    print("🧪 TESTING DIRECT GOOGLE SHOPPING REQUEST")
    print("=" * 80)
    
    # Build our own URL like SerpAPI does
    query = "large eggs, 33773 nearby"
    
    params = {
        'udm': '28',  # Shopping search
        'q': query,
        'uule': 'w+CAIQICIbMzM3NzMsRmxvcmlkYSxVbml0ZWQgU3RhdGVz',  # From SerpAPI
        'hl': 'en',
        'gl': 'us'
    }
    
    url = 'https://www.google.com/search?' + urllib.parse.urlencode(params)
    
    print(f"\n📍 Testing URL:")
    print(f"   {url}")
    
    # Try with realistic browser headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        print(f"\n⏳ Making request...")
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"\n📊 Response:")
        print(f"   Status: {response.status_code}")
        print(f"   Size: {len(response.text)} bytes")
        
        # Save for inspection
        with open('direct_google_shopping.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"   💾 Saved to: direct_google_shopping.html")
        
        # Check for CAPTCHA
        if 'captcha' in response.text.lower():
            print(f"\n   ❌ CAPTCHA detected!")
            return False
        
        # Try to find products
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for product elements (similar to our scraper)
        products_with_aria = soup.find_all(attrs={'aria-label': True})
        products_found = [p for p in products_with_aria if '$' in p.get('aria-label', '')]
        
        print(f"\n   🔍 Found {len(products_found)} potential products")
        
        if products_found:
            print(f"\n   📦 Sample products:")
            for i, p in enumerate(products_found[:3], 1):
                aria = p.get('aria-label', '')
                print(f"      {i}. {aria[:80]}...")
            
            print(f"\n   ✅ SUCCESS! We can scrape Google Shopping directly!")
            return True
        else:
            print(f"\n   ⚠️  No products found - might need different parsing")
            return False
    
    except Exception as e:
        print(f"\n   ❌ Error: {e}")
        return False


def compare_approaches():
    """Compare doing it ourselves vs using SerpAPI"""
    
    print("\n\n" + "=" * 80)
    print("📊 DOING IT OURSELVES VS SERPAPI")
    print("=" * 80)
    
    print(f"\n✅ WHAT WE LEARNED:")
    print(f"   1. Google Shopping uses udm=28 parameter")
    print(f"   2. Query format: 'product, ZIP nearby'")
    print(f"   3. uule parameter encodes location")
    print(f"   4. Standard URL structure we can replicate")
    
    print(f"\n🤔 CHALLENGES TO DOING IT OURSELVES:")
    print(f"   1. ❌ UULE encoding is complex/proprietary")
    print(f"   2. ❌ Google will CAPTCHA/block us without proxies")
    print(f"   3. ❌ HTML structure changes frequently")
    print(f"   4. ❌ Need to handle lazy loading")
    print(f"   5. ❌ Rate limiting issues at scale")
    
    print(f"\n💰 COST COMPARISON:")
    print(f"\n   SERPAPI:")
    print(f"      • $50/month = 5,000 searches")
    print(f"      • ~$0.01 per search")
    print(f"      • Zero maintenance")
    print(f"      • No blocking issues")
    
    print(f"\n   DOING IT OURSELVES:")
    print(f"      • Residential Proxy: ~$75-300/month")
    print(f"      • Worker servers: $20-40/month")
    print(f"      • Your time: Ongoing maintenance")
    print(f"      • Still get blocked sometimes")
    
    print(f"\n💡 RECOMMENDATION:")
    print(f"   Use SerpAPI because:")
    print(f"      1. They've solved the hard problems")
    print(f"      2. Actually CHEAPER when you factor in time")
    print(f"      3. More reliable at scale")
    print(f"      4. Your current scraper proves the concept")
    print(f"      5. You can always switch back if needed")


if __name__ == "__main__":
    # Decode what SerpAPI is doing
    url_info = decode_serpapi_url()
    
    # Try to replicate it
    success = test_direct_google_request()
    
    # Compare options
    compare_approaches()
    
    print("\n" + "=" * 80)
    print("✅ Analysis complete!")
    print("=" * 80)

