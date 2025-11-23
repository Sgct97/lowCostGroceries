"""
Check SerpAPI caching behavior
"""

from serpapi import GoogleSearch
import time

API_KEY = "caaa674f50f87741ec1d523cf908d540b9538ef0b4426db9ddc175303c165c69"

def test_cache_behavior():
    print("=" * 80)
    print("🔍 TESTING SERPAPI CACHE BEHAVIOR")
    print("=" * 80)
    
    query = "test eggs, 33773 nearby"
    
    # First request - should hit Google
    print(f"\n1️⃣ First request (should be NEW):")
    params1 = {
        "engine": "google_shopping",
        "q": query,
        "location": "33773, Florida, United States",
        "api_key": API_KEY
    }
    
    start = time.time()
    search1 = GoogleSearch(params1)
    results1 = search1.get_dict()
    elapsed1 = time.time() - start
    
    search_meta1 = results1.get("search_metadata", {})
    print(f"   Time: {elapsed1:.2f}s")
    print(f"   ID: {search_meta1.get('id', 'N/A')}")
    print(f"   Created: {search_meta1.get('created_at', 'N/A')}")
    
    # Second request - should be cached
    print(f"\n2️⃣ Immediate second request (should be CACHED):")
    time.sleep(1)  # Brief pause
    
    start = time.time()
    search2 = GoogleSearch(params1)  # Same params
    results2 = search2.get_dict()
    elapsed2 = time.time() - start
    
    search_meta2 = results2.get("search_metadata", {})
    print(f"   Time: {elapsed2:.2f}s")
    print(f"   ID: {search_meta2.get('id', 'N/A')}")
    print(f"   Created: {search_meta2.get('created_at', 'N/A')}")
    
    # Compare
    if search_meta1.get('id') == search_meta2.get('id'):
        print(f"\n   ✅ CACHED! Same search ID")
        print(f"   ⚡ Speed improvement: {elapsed1/elapsed2:.1f}x faster")
    else:
        print(f"\n   ⚠️  NOT cached (different IDs)")
    
    # Test no_cache parameter
    print(f"\n3️⃣ Request with no_cache=True (should bypass cache):")
    params3 = params1.copy()
    params3["no_cache"] = True
    
    start = time.time()
    search3 = GoogleSearch(params3)
    results3 = search3.get_dict()
    elapsed3 = time.time() - start
    
    search_meta3 = results3.get("search_metadata", {})
    print(f"   Time: {elapsed3:.2f}s")
    print(f"   ID: {search_meta3.get('id', 'N/A')}")
    
    if search_meta3.get('id') != search_meta2.get('id'):
        print(f"   ✅ New search (bypassed cache)")
    
    # Documentation check
    print(f"\n" + "=" * 80)
    print("📚 FROM SERPAPI DOCUMENTATION:")
    print("=" * 80)
    print("""
no_cache parameter:
   "A cache is served only if the query and all parameters 
    are exactly the same. Cache expires after 1h. 
    Cached searches are free, and are not counted towards 
    your searches per month."
    
Key points:
   ✅ Cache duration: 1 hour
   ✅ Cached searches: FREE (don't count against quota)
   ✅ Cache key: Exact query + all parameters
   ✅ Can force fresh: no_cache=True
    """)
    
    print(f"\n💡 FOR GROCERY SHOPPING:")
    print("""
This is actually GOOD for you:
   • Egg prices don't change every minute
   • Multiple users in same ZIP = shared cache = FREE
   • 1 hour is fresh enough for grocery shopping
   • Your $50/month goes further with caching
   
Example:
   • 10 users search "eggs 33773" in 1 hour
   • You only pay for 1 search
   • Other 9 are FREE
   • Effective cost: $0.001 per user instead of $0.01
    """)

if __name__ == "__main__":
    test_cache_behavior()
    print("\n✅ Cache test complete!")
