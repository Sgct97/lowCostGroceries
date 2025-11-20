#!/usr/bin/env python3
"""
Comprehensive Instacart scraping feasibility test
Testing if we can get grocery data at scale without browser automation
"""

import requests
import json
import time
from typing import Dict, List, Optional
import re

class InstacartTester:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.instacart.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.instacart.com',
            'Referer': 'https://www.instacart.com/',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
    def test_basic_access(self) -> Dict:
        """Test if we can access Instacart at all"""
        print("\n[TEST 1] Testing basic HTTP access...")
        try:
            response = self.session.get(self.base_url, headers=self.headers, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Response Size: {len(response.text)} bytes")
            
            # Check for common anti-bot indicators
            indicators = {
                'cloudflare': 'cloudflare' in response.text.lower(),
                'captcha': 'captcha' in response.text.lower(),
                'access_denied': 'access denied' in response.text.lower(),
                'recaptcha': 'recaptcha' in response.text.lower(),
            }
            print(f"Anti-bot indicators: {indicators}")
            
            # Look for API endpoints in the HTML
            api_patterns = re.findall(r'https://[^"\']+api[^"\']+', response.text)
            print(f"Found {len(set(api_patterns))} potential API endpoints")
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'has_content': len(response.text) > 1000,
                'anti_bot': any(indicators.values()),
                'api_endpoints': list(set(api_patterns))[:5]
            }
        except Exception as e:
            print(f"Error: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_search_endpoint(self, query: str = "eggs") -> Dict:
        """Test if we can search for products"""
        print(f"\n[TEST 2] Testing product search for '{query}'...")
        
        # Common API endpoint patterns for grocery sites
        search_urls = [
            f"{self.base_url}/v3/containers/search",
            f"{self.base_url}/api/v2/search",
            f"{self.base_url}/graphql",
            f"{self.base_url}/v2/search",
        ]
        
        results = []
        for url in search_urls:
            try:
                print(f"Trying: {url}")
                response = self.session.get(
                    url,
                    params={'term': query, 'q': query},
                    headers=self.headers,
                    timeout=10
                )
                print(f"  Status: {response.status_code}, Size: {len(response.text)}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        results.append({
                            'url': url,
                            'status': response.status_code,
                            'has_json': True,
                            'keys': list(data.keys()) if isinstance(data, dict) else None
                        })
                    except:
                        results.append({
                            'url': url,
                            'status': response.status_code,
                            'has_json': False
                        })
                        
            except Exception as e:
                print(f"  Error: {e}")
                
        return {'tested_urls': len(search_urls), 'results': results}
    
    def test_graphql(self) -> Dict:
        """Test if Instacart uses GraphQL (easier to work with)"""
        print("\n[TEST 3] Testing GraphQL endpoint...")
        
        graphql_url = f"{self.base_url}/graphql"
        
        # Common introspection query
        introspection_query = {
            "query": "{ __schema { queryType { name } } }"
        }
        
        # Try a simple product search query
        search_query = {
            "query": """
                query SearchProducts($term: String!) {
                    search(term: $term) {
                        products {
                            name
                            price
                        }
                    }
                }
            """,
            "variables": {"term": "eggs"}
        }
        
        results = []
        for name, query in [("introspection", introspection_query), ("search", search_query)]:
            try:
                print(f"Testing {name} query...")
                response = self.session.post(
                    graphql_url,
                    json=query,
                    headers={**self.headers, 'Content-Type': 'application/json'},
                    timeout=10
                )
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"  Response keys: {list(data.keys())}")
                        results.append({
                            'query_type': name,
                            'success': True,
                            'data': data
                        })
                    except:
                        results.append({
                            'query_type': name,
                            'success': False,
                            'raw_response': response.text[:500]
                        })
                        
            except Exception as e:
                print(f"  Error: {e}")
                
        return {'graphql_available': len(results) > 0, 'results': results}
    
    def test_store_api(self, zipcode: str = "10001") -> Dict:
        """Test if we can get store/location data"""
        print(f"\n[TEST 4] Testing store/location API with zipcode {zipcode}...")
        
        location_urls = [
            f"{self.base_url}/api/v2/stores",
            f"{self.base_url}/v3/retailers",
            f"{self.base_url}/api/v3/retailers/search",
        ]
        
        results = []
        for url in location_urls:
            try:
                print(f"Trying: {url}")
                response = self.session.get(
                    url,
                    params={'zip': zipcode, 'zipcode': zipcode, 'postal_code': zipcode},
                    headers=self.headers,
                    timeout=10
                )
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        results.append({
                            'url': url,
                            'has_data': bool(data),
                            'data_preview': str(data)[:200]
                        })
                    except:
                        pass
                        
            except Exception as e:
                print(f"  Error: {e}")
                
        return {'results': results}
    
    def test_mobile_api(self, query: str = "milk") -> Dict:
        """Test mobile API (often less protected)"""
        print(f"\n[TEST 5] Testing mobile API...")
        
        mobile_headers = {
            **self.headers,
            'User-Agent': 'Instacart/1.0 (iPhone; iOS 17.0; Scale/3.00)',
            'X-Instacart-Client': 'mobile-app',
        }
        
        # Mobile apps often use different endpoints
        mobile_urls = [
            f"{self.base_url}/api/mobile/v1/search",
            f"{self.base_url}/mobile/v2/search",
            f"{self.base_url}/api/v1/search",
        ]
        
        results = []
        for url in mobile_urls:
            try:
                print(f"Trying: {url}")
                response = self.session.get(
                    url,
                    params={'q': query, 'term': query},
                    headers=mobile_headers,
                    timeout=10
                )
                print(f"  Status: {response.status_code}")
                
                results.append({
                    'url': url,
                    'status': response.status_code,
                    'accessible': response.status_code == 200
                })
                
            except Exception as e:
                print(f"  Error: {e}")
                
        return {'results': results}
    
    def test_real_product_page(self) -> Dict:
        """Try to access a known product page and extract data"""
        print("\n[TEST 6] Testing product page scraping...")
        
        # Try a generic product URL structure
        product_urls = [
            f"{self.base_url}/products/1234567890",
            f"{self.base_url}/store/items/eggs",
        ]
        
        results = []
        for url in product_urls:
            try:
                print(f"Trying: {url}")
                response = self.session.get(url, headers=self.headers, timeout=10)
                print(f"  Status: {response.status_code}")
                
                # Look for JSON data embedded in the page
                json_pattern = re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', 
                                         response.text, re.DOTALL)
                
                results.append({
                    'url': url,
                    'status': response.status_code,
                    'embedded_json_count': len(json_pattern)
                })
                
            except Exception as e:
                print(f"  Error: {e}")
                
        return {'results': results}
    
    def run_full_assessment(self) -> Dict:
        """Run all tests and provide comprehensive report"""
        print("="*80)
        print("INSTACART SCRAPING FEASIBILITY ASSESSMENT")
        print("="*80)
        
        results = {
            'basic_access': self.test_basic_access(),
            'search_endpoint': self.test_search_endpoint(),
            'graphql': self.test_graphql(),
            'store_api': self.test_store_api(),
            'mobile_api': self.test_mobile_api(),
            'product_page': self.test_real_product_page(),
        }
        
        # Generate feasibility report
        print("\n" + "="*80)
        print("FEASIBILITY REPORT")
        print("="*80)
        
        feasibility_score = 0
        max_score = 6
        
        if results['basic_access'].get('success') and not results['basic_access'].get('anti_bot'):
            feasibility_score += 1
            print("✓ Basic access: PASS")
        else:
            print("✗ Basic access: FAIL (anti-bot detected or blocked)")
            
        if any(r.get('status') == 200 for r in results['search_endpoint'].get('results', [])):
            feasibility_score += 1
            print("✓ Search endpoint: ACCESSIBLE")
        else:
            print("✗ Search endpoint: NOT FOUND")
            
        if results['graphql'].get('graphql_available'):
            feasibility_score += 1
            print("✓ GraphQL: AVAILABLE")
        else:
            print("✗ GraphQL: NOT AVAILABLE")
            
        if results['store_api'].get('results'):
            feasibility_score += 1
            print("✓ Location API: ACCESSIBLE")
        else:
            print("✗ Location API: NOT FOUND")
            
        if any(r.get('accessible') for r in results['mobile_api'].get('results', [])):
            feasibility_score += 1
            print("✓ Mobile API: ACCESSIBLE")
        else:
            print("✗ Mobile API: NOT ACCESSIBLE")
            
        if any(r.get('embedded_json_count', 0) > 0 for r in results['product_page'].get('results', [])):
            feasibility_score += 1
            print("✓ Product page scraping: VIABLE")
        else:
            print("✗ Product page scraping: NOT VIABLE")
        
        print(f"\nFEASIBILITY SCORE: {feasibility_score}/{max_score}")
        
        if feasibility_score >= 4:
            verdict = "HIGH FEASIBILITY - Recommended"
        elif feasibility_score >= 2:
            verdict = "MODERATE FEASIBILITY - Possible but challenging"
        else:
            verdict = "LOW FEASIBILITY - Not recommended"
            
        print(f"VERDICT: {verdict}")
        
        results['feasibility_score'] = feasibility_score
        results['verdict'] = verdict
        
        return results


def main():
    tester = InstacartTester()
    results = tester.run_full_assessment()
    
    # Save detailed results
    with open('instacart_feasibility_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: instacart_feasibility_results.json")
    
    # Additional recommendation
    print("\n" + "="*80)
    print("SCALABILITY ASSESSMENT FOR 25K USERS")
    print("="*80)
    
    if results['feasibility_score'] >= 3:
        print("If APIs are accessible:")
        print("  - Rate limiting will be the main challenge")
        print("  - Estimate: 10 items × 25k users = 250k API calls")
        print("  - With proper caching and request distribution: VIABLE")
        print("  - Recommendation: Implement smart caching, proxy rotation, rate limiting")
    else:
        print("Current assessment shows limited API access")
        print("Would require browser automation or official API partnership")
        print("For 25k users: NOT VIABLE without official API access")


if __name__ == "__main__":
    main()

