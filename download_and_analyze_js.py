from curl_cffi import requests
import re

PROXY = "http://lowCostGroceris_26SVt:AppleID_1234@isp.oxylabs.io:8001"

js_url = "https://www.gstatic.com/og/_/js/k=og.asy.en_US.ZB_JWty8yBQ.2019.O/rt=j/m=_ac,_awd,ada,lldp,qads/exm=/d=1/ed=1/rs=AA2YrTuOdAa9YWDd3u-N0sm5Gvsh4Lr-DQ"

print(f"Downloading JavaScript file...")
response = requests.get(
    js_url,
    headers={"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
    proxies={"http": PROXY, "https": PROXY},
    impersonate="chrome120",
    timeout=30
)

print(f"Downloaded {len(response.text):,} bytes")

with open('google_shopping.js', 'w') as f:
    f.write(response.text)

# Search for callback patterns
print("\nSearching for callback logic...\n")

# Look for "/async" strings
async_urls = re.findall(r'["\']/(async/[a-z]+)[^"\']{0,50}["\']', response.text)
print(f"Async URL patterns: {len(set(async_urls))}")
for url in sorted(set(async_urls))[:10]:
    print(f"  {url}")

print()

# Look for URL construction with parameters
url_params = re.findall(r'["\']/(async/\w+)["\'][^;]{0,150}', response.text)
print(f"URL construction patterns: {len(url_params)}")
for pattern in url_params[:3]:
    print(f"  {pattern[:120]}")

print("\nSaved to: google_shopping.js")
