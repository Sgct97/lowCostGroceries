"""
Test Token Capture

Test if we can capture callback URLs using Playwright.
This validates the core assumption of our architecture.
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from token_service import TokenService
from proxy_manager import ProxyPool, Proxy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_without_proxy():
    """Test capturing callback URL without proxy."""
    print("\n" + "="*80)
    print("TEST 1: Capture Callback WITHOUT Proxy")
    print("="*80)
    
    service = TokenService(proxy_pool=None)
    
    callback_url = service.capture_callback_url(
        region="US",
        test_query="macbook pro"
    )
    
    if callback_url:
        print(f"\n✅ SUCCESS! Captured callback URL:")
        print(f"   {callback_url[:120]}...")
        print(f"\n   Full URL length: {len(callback_url)} characters")
        
        # Check if it has the expected components
        has_fc = 'fc=' in callback_url
        has_ei = 'ei=' in callback_url
        has_udm = 'udm=' in callback_url
        has_callback = '/async/callback' in callback_url
        
        print(f"\n   URL Components:")
        print(f"   - Has /async/callback: {has_callback} {'✅' if has_callback else '❌'}")
        print(f"   - Has fc= token: {has_fc} {'✅' if has_fc else '❌'}")
        print(f"   - Has ei= token: {has_ei} {'✅' if has_ei else '❌'}")
        print(f"   - Has udm= param: {has_udm} {'✅' if has_udm else '❌'}")
        
        return True
    else:
        print("\n❌ FAILED to capture callback URL")
        return False


def test_with_oxylabs():
    """Test capturing callback URL with Oxylabs proxy."""
    print("\n" + "="*80)
    print("TEST 2: Capture Callback WITH Oxylabs Proxy")
    print("="*80)
    
    # Setup Oxylabs proxy
    oxylabs_proxies = [
        Proxy(
            host="isp.oxylabs.io",
            port=8001,
            username="lowCostGroceris_26SVt",
            password="AppleID_1234"
        )
    ]
    
    proxy_pool = ProxyPool(proxies=oxylabs_proxies)
    service = TokenService(proxy_pool=proxy_pool)
    
    callback_url = service.capture_callback_url(
        region="US-West",
        test_query="laptop"
    )
    
    if callback_url:
        print(f"\n✅ SUCCESS! Captured callback URL with proxy:")
        print(f"   {callback_url[:120]}...")
        return True
    else:
        print("\n❌ FAILED to capture callback URL with proxy")
        return False


def test_create_session():
    """Test creating a complete session (capture + store)."""
    print("\n" + "="*80)
    print("TEST 3: Create Complete Session (Capture + Store)")
    print("="*80)
    
    service = TokenService(proxy_pool=None)
    
    session = service.create_session(
        region="US",
        test_query="laptop"
    )
    
    if session:
        print(f"\n✅ SUCCESS! Created session:")
        print(f"   Session ID: {session.id}")
        print(f"   Region: {session.region}")
        print(f"   URL: {session.url[:100]}...")
        print(f"   Created: {session.created_at}")
        print(f"   Is Valid: {session.is_valid}")
        print(f"   Is Healthy: {session.is_healthy()}")
        return True
    else:
        print("\n❌ FAILED to create session")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("TESTING TOKEN CAPTURE WITH PLAYWRIGHT")
    print("="*80)
    print("\nThis will:")
    print("1. Test capturing callback URL without proxy")
    print("2. Test capturing callback URL with Oxylabs proxy")
    print("3. Test creating and storing a complete session")
    print("\n⚠️  NOTE: Playwright will download Chromium on first run (~100MB)")
    print("="*80)
    
    input("\nPress Enter to start tests...")
    
    results = {}
    
    # Test 1: Without proxy
    try:
        results['no_proxy'] = test_without_proxy()
    except Exception as e:
        print(f"\n❌ Test 1 crashed: {e}")
        logger.exception("Test 1 error:")
        results['no_proxy'] = False
    
    # Test 2: With Oxylabs
    try:
        results['with_proxy'] = test_with_oxylabs()
    except Exception as e:
        print(f"\n❌ Test 2 crashed: {e}")
        logger.exception("Test 2 error:")
        results['with_proxy'] = False
    
    # Test 3: Create session
    try:
        results['create_session'] = test_create_session()
    except Exception as e:
        print(f"\n❌ Test 3 crashed: {e}")
        logger.exception("Test 3 error:")
        results['create_session'] = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! The TokenService works!")
        print("\n✅ We can proceed with building the full system.")
    elif total_passed > 0:
        print("\n⚠️  SOME TESTS PASSED - TokenService partially works")
        print("   You may need to debug the failing tests.")
    else:
        print("\n❌ ALL TESTS FAILED - TokenService not working")
        print("   Need to debug Playwright setup or Google blocking.")
    
    print("="*80)


if __name__ == "__main__":
    main()

