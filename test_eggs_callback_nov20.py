"""
Test the eggs callback captured on Nov 20
This will tell us if new captures last as long as the Nov 13 one
"""
import requests
import re

def test_eggs_callback():
    url = "https://www.google.com/async/callback:6948"
    
    params = {
        'fc': 'EvcBCrcBQUxrdF92R0pOLWZmRUZuZkZ4UUd0d0ZRUGJRTlhDaFItU2l2OWpjSHpobTBjdl9NZ1l5Y0NSbXVrc2hzcXFLaUJMc01yeGhPVGF2MXlNTHo2R0lXSWtQS3oxQ3dJQUN0dzBxcTF0RFdvNmx0SXprNFhNQmdGbmNoYWk3WGdDZWVtYXh3elo1ZUw4Q1Bob054VW0wWVVjVUJGdTZfOUtySEowY0poNTRzLWZlaDRwcG5oSGl2cHVrEhcwMWdlYWZfdUZvcWJ3YmtQci16Q3FRVRoiQUZNQUdHckZ0NWVjZHM1OFZUbnV0RUJSV240SWhfWU0yQQ',
        'fcv': '3',
        'vet': '12ahUKEwi_pP32tP-QAxWKTTABHS-2MFUQ9pcOegQIChAB..i',
        'ei': '01geaf_uFoqbwbkPr-zCqQU',
        'opi': '95576897',
        'sca_esv': '3a898889caaec7e6',
        'shopmd': '1',
        'udm': '28',
        'yv': '3',
        'cs': '0',
        'async': '_fmt:prog,_id:fc_01geaf_uFoqbwbkPr-zCqQU_1'
    }
    
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
    print("TESTING EGGS CALLBACK (Captured Nov 20)")
    print("="*80)
    
    response = requests.get(url, params=params, headers=headers, timeout=15)
    
    print(f"Status: {response.status_code}")
    print(f"Size: {len(response.text):,} bytes")
    
    if len(response.text) > 500:
        prices = re.findall(r'\$([0-9]+\.[0-9]{2})', response.text)
        print(f"✅ WORKS! Found {len(prices)} prices")
        print(f"Sample: {prices[:10]}")
        
        egg_count = response.text.lower().count('egg')
        print(f"'egg' mentions: {egg_count}")
        return True
    else:
        print(f"❌ Expired or invalid")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    test_eggs_callback()

