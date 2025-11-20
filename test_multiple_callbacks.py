"""
Test multiple callbacks captured Nov 20
"""
import requests
import re

def test_callback(name, params):
    url = "https://www.google.com/async/callback:6948"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }
    
    print(f"\n{'='*80}")
    print(f"TESTING: {name}")
    print(f"{'='*80}")
    
    response = requests.get(url, params=params, headers=headers, timeout=15)
    
    print(f"Status: {response.status_code}")
    print(f"Size: {len(response.text):,} bytes")
    
    if len(response.text) > 500:
        prices = re.findall(r'\$([0-9]+\.[0-9]{2})', response.text)
        print(f"✅ WORKS! Found {len(prices)} prices")
        
        # Check product category
        content = response.text.lower()
        keywords = ['milk', 'bread', 'chicken', 'banana', 'egg', 'beef', 'cheese', 'butter']
        for keyword in keywords:
            count = content.count(keyword)
            if count > 10:
                print(f"Category: {keyword.upper()} ({count} mentions)")
                break
        
        return True, len(prices)
    else:
        print(f"❌ Failed: {response.text[:100]}")
        return False, 0

def main():
    # Callback 1 - MILK
    callback1 = {
        'fc': 'EswCCowCQUxrdF92RkdiNWlYZVhZVEMyak1wZUtMUi1vdVNUQmFBRk9VeERPOTd6S2V1MVdTZEMzVG9jc1l3UUEyYzZicWh4YVVXZ2NkY2JHQUdDVXZKRWNzOGNMSkdXREFyVm5Cek9zS3dDTlRfaU41MEh0Y1hWaG05Z0RvaTR1akk3YTQ1b2ZZRXRDM3duSjhRMmxuYm1ORzhidW9OaEwzTGVqbEN0TjZuQWFuWnZqT0kxX2t2a1puRkNJNGdYM0xMRTdhTnNLTWY1V0k3OFZUeFdkaWpsWlN4M2hEOVlsakR5NFZsRXhrUmFoSzloa3E1V1FWWXpTUzFtVHlkUXVuUUwycUFUNHFjUXd3b3BIcBIXd0ZzZWFkcllHZlhGcDg0UHktV0tnUVUaIkFGTUFHR3JnRkszc1YwcnZvZnR1bFNGU1lZUVl6MmJJNlE',
        'fcv': '3',
        'vet': '12ahUKEwjauJPct_-QAxX14skDHcuyIlAQ9pcOegQIBhAB..i',
        'ei': 'wFseadrYGfXFp84Py-WKgQU',
        'opi': '95576897',
        'sca_esv': '3a898889caaec7e6',
        'shopmd': '1',
        'udm': '28',
        'yv': '3',
        'cs': '0',
        'async': '_fmt:prog,_id:fc_wFseadrYGfXFp84Py-WKgQU_1'
    }
    
    # Callback 2 - BREAD
    callback2 = {
        'fc': 'EswCCowCQUxrdF92SGc4T2V6cGYyWmVuN1ZCREtpdjR3UGRLRHc5X182a1N4NE11V0V1djg5emprNnd1aW9xRXkyVmJPNUpYdl9BcHJWVTg4aXA0SE5kQUk3dENCVXNRWVNhekc4NXkxQV8zUGdYVm9lSWZILTJYMnhkRUVCODc3WkxVQ3hlU1NVeHREMDh6TGd5eUJxbzk0Sll0dEhnRHRfZnVqNmtxMHo1VzZvbGg5aFdWbUd4ZzktaFZTUUlZaE42aEpYSVZHZ2RVRlZyYnNob0xQTWpZYlMyclNJWlVzSmx6Uko4blVMdjk2d2RCZXBUZmhzUElnQ29GS3NIcmx2aG1VZGJOOFBjZkRWT1VQXxIXN1ZzZWFacmtMOWlxd2JrUDFNam9tUTgaIkFGTUFHR3JTak0yYUNsa3JJd2F2M2NPQVpLd1NGaGhDZ1E',
        'fcv': '3',
        'vet': '12ahUKEwjajuTxt_-QAxVYVTABHVQkOvMQ9pcOegQIBxAB..i',
        'ei': '7VseaZrkL9iqwbkP1MjomQ8',
        'opi': '95576897',
        'sca_esv': '3a898889caaec7e6',
        'shopmd': '1',
        'udm': '28',
        'yv': '3',
        'cs': '0',
        'async': '_fmt:prog,_id:fc_7VseaZrkL9iqwbkP1MjomQ8_1'
    }
    
    # Callback 3 - CHICKEN
    callback3 = {
        'fc': 'EqICCuIBQUxrdF92RlBUeHl5V1ZyV3hrM1ZQd3ZqM01RaEVhY0k2aXRNMEJMUC11ZjlYRTNwQlRkeHpxYkF0emhrS083SEpla2ozdnZzVmdNX1lsenA4SmZYa21KeHNSZk5yWTVnSjFrRngtaHdLOEx0TXJqQUZ1dVFnaUg0Q0tIRGw0WlY5Z0ZoR1RvYkh3QnZkVXZ4S3ZsQThXVFkzbmUtRzZPTjd6S1Z0Y0xpNG5LWndrNXpZMEtfQkNSVTFxOTd5MGpKVV80Y1lOU2oyRXo0NEVaX3M4WWw3UXI1dXVVcmd6ZzI2ZxIXQ2x3ZWFiLV9JWkdQd2JrUHA4NmNvUW8aIkFGTUFHR3FCS2pyQ0cwTkx4WmRQRWI4ajl3cWQ0YkxEcmc',
        'fcv': '3',
        'vet': '12ahUKEwi_7L__t_-QAxWRRzABHScnJ6QQ9pcOegQIChAB..i',
        'ei': 'Clweab-_IZGPwbkPp86coQo',
        'opi': '95576897',
        'sca_esv': '3a898889caaec7e6',
        'shopmd': '1',
        'udm': '28',
        'yv': '3',
        'cs': '0',
        'async': '_fmt:prog,_id:fc_Clweab-_IZGPwbkPp86coQo_1'
    }
    
    callbacks = [
        ("MILK", callback1),
        ("BREAD", callback2),
        ("CHICKEN", callback3),
    ]
    
    print("\n" + "="*80)
    print("TESTING ALL NEW CALLBACKS".center(80))
    print("="*80)
    
    results = []
    for name, params in callbacks:
        success, price_count = test_callback(name, params)
        results.append((name, success, price_count))
    
    print("\n" + "="*80)
    print("SUMMARY".center(80))
    print("="*80)
    for name, success, price_count in results:
        status = "✅ WORKS" if success else "❌ FAILED"
        print(f"{name:15s}: {status} ({price_count} prices)")
    
    success_count = sum(1 for _, success, _ in results if success)
    print(f"\n{success_count}/{len(results)} callbacks working!")
    
    if success_count == len(results):
        print("\n🎉🎉🎉 ALL CALLBACKS WORK!")
        print("\n✅ READY FOR 6000+ CATEGORY CAPTURE!")

if __name__ == "__main__":
    main()

