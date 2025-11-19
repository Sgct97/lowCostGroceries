"""
Test the TokenService to verify callback URL capture works
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from token_service import TokenService
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

print("\n" + "="*80)
print("TESTING TOKEN SERVICE")
print("="*80 + "\n")

# Test single capture
service = TokenService()
url = service.capture_callback_url(region='US', test_query='laptop')

print("\n" + "="*80)
if url:
    print("🎉 SUCCESS! TokenService captured callback URL")
    print(f"URL: {url[:150]}...")
    print(f"\nStats: {service.get_stats()}")
else:
    print("❌ FAILED to capture callback URL")
print("="*80 + "\n")

