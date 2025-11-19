"""
Complete test: Capture callback URL and IMMEDIATELY test it with curl_cffi
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from token_service import TokenService
from curl_cffi import requests
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

print("\n" + "="*80)
print("COMPLETE WORKFLOW TEST: UC Capture → curl_cffi Test")
print("="*80 + "\n")

# STEP 1: Capture callback URL with TokenService
print("STEP 1: Capturing callback URL with TokenService...")
service = TokenService()
callback_url = service.capture_callback_url(region='US', test_query='laptop')

if not callback_url:
    print("❌ FAILED: Could not capture callback URL")
    exit(1)

print(f"✅ Captured: {callback_url[:100]}...")

# STEP 2: IMMEDIATELY test with curl_cffi
print("\nSTEP 2: Testing callback URL with curl_cffi (IMMEDIATELY)...")

try:
    r = requests.get(
        callback_url,
        impersonate='chrome120',
        timeout=30,
        headers={
            'referer': 'https://shopping.google.com/',
            'accept-language': 'en-US,en;q=0.9'
        }
    )
    
    print(f"Status: {r.status_code}")
    print(f"Size: {len(r.text):,} bytes")
    
    prices = re.findall(r'\$([0-9,]+\.[0-9]{2})', r.text)
    print(f"$ prices found: {len(prices)}")
    
    if prices:
        print(f"Sample prices: {', '.join([f'${p}' for p in prices[:10]])}")
    
    print("\n" + "="*80)
    if r.status_code == 200 and len(prices) > 0:
        print("✅✅✅ SUCCESS! HYBRID ARCHITECTURE WORKS! ✅✅✅")
        print(f"   UC captured callback URL")
        print(f"   curl_cffi got {len(prices)} prices")
        print("="*80)
    else:
        print("❌ FAILED: No prices found")
        print("="*80)
        
except Exception as e:
    print(f"❌ ERROR: {e}")

