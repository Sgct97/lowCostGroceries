import requests
import re
from urllib.parse import urlparse, parse_qs

def test_shampoo_callback():
    """Test the shampoo callback you just captured"""
    
    # Your exact fetch URL
    full_url = 'https://www.google.com/async/callback:6948?fc=EqICCuIBQUxrdF92RlBUeHl5V1ZyV3hrM1ZQd3ZqM01RaEVhY0k2aXRNMEJMUC11ZjlYRTNwQlRkeHpxYkF0emhrS083SEpla2ozdnZzVmdNX1lsenA4SmZYa21KeHNSZk5yWTVnSjFrRngtaHdLOEx0TXJqQUZ1dVFnaUg0Q0tIRGw0WlY5Z0ZoR1RvYkh3QnZkVXZ4S3ZsQThXVFkzbmUtRzZPTjd6S1Z0Y0xpNG5LWndrNXpZMEtfQkNSVTFxOTd5MGpKVV80Y1lOU2oyRXo0NEVaX3M4WWw3UXI1dXVVcmd6ZzI2ZxIXQ2x3ZWFiLV9JWkdQd2JrUHA4NmNvUW8aIkFGTUFHR3FCS2pyQ0cwTkx4WmRQRWI4ajl3cWQ0YkxEcmc&fcv=3&vet=12ahUKEwi_7L__t_-QAxWRRzABHScnJ6QQ9pcOegQIChAB..i&ei=Clweab-_IZGPwbkPp86coQo&opi=95576897&sca_esv=3a898889caaec7e6&shopmd=1&udm=28&yv=3&cs=0&async=_fmt:prog,_id:fc_Clweab-_IZGPwbkPp86coQo_1'
    
    parsed = urlparse(full_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    query_params = parse_qs(parsed.query)
    params = {k: v[0] for k, v in query_params.items()}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }
    
    print("="*80)
    print("TESTING SHAMPOO CALLBACK")
    print("="*80)
    
    response = requests.get(base_url, params=params, headers=headers, timeout=15)
    
    print(f"Status: {response.status_code}")
    print(f"Size: {len(response.text):,} bytes")
    
    if len(response.text) > 500:
        prices = re.findall(r'\$([0-9]+\.[0-9]{2})', response.text)
        print(f"✅ WORKS! Found {len(prices)} prices")
        print(f"Sample: {prices[:10]}")
        
        shampoo_count = response.text.lower().count('shampoo')
        print(f"shampoo mentions: {shampoo_count}")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

if __name__ == "__main__":
    test_shampoo_callback()

