import sys
sys.path.append('backend')
from proxy_manager import ProxyPool
from scraper import GoogleShoppingScraper

# Your Oxylabs proxies
USERNAME = "lowCostGroceris_26SVt"
PASSWORD = "AppleID_1234"
HOST = "isp.oxylabs.io"

# Create list (ports 8001-8020)
proxy_list = [f"{HOST}:{port}:{USERNAME}:{PASSWORD}" for port in range(8001, 8021)]

# Test
pool = ProxyPool.from_list(proxy_list)
print(f"Created pool: {pool}\n")

scraper = GoogleShoppingScraper(proxy_pool=pool)
products = scraper.search("milk", zipcode="90210", limit=10)

print(f"\n✅ Found {len(products)} products:")
for i, p in enumerate(products[:5], 1):
    print(f"{i}. {p['title']} - ${p['price']} @ {p['merchant']}")

print(f"\nProxy stats: {pool.get_stats()['avg_success_rate']:.1f}% success")
