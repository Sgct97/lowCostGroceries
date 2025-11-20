#!/usr/bin/env python3
"""
Deep dive into Instacart's accessible endpoints
Focus on GraphQL and retailers API that showed promise
"""

import requests
import json
import re
from bs4 import BeautifulSoup

class InstacartDeepDive:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.instacart.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.instacart.com',
            'Referer': 'https://www.instacart.com/',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
    
    def analyze_main_page(self):
        """Extract API details from main page source"""
        print("\n[DEEP DIVE 1] Analyzing main page for API clues...")
        
        response = self.session.get(self.base_url, headers=self.headers)
        html = response.text
        
        # Save for inspection
        with open('instacart_homepage.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Saved homepage to: instacart_homepage.html")
        
        # Look for embedded JSON data
        json_scripts = re.findall(r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', 
                                  html, re.DOTALL)
        print(f"Found {len(json_scripts)} JSON script blocks")
        
        # Look for API configuration
        api_config = re.findall(r'API[_\s]*(?:URL|ENDPOINT|CONFIG|BASE)["\']?\s*[:=]\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
        print(f"Found {len(api_config)} API config strings: {api_config[:5]}")
        
        # Look for GraphQL queries in the page
        graphql_queries = re.findall(r'query\s+(\w+)\s*(?:\([^)]*\))?\s*{[^}]+}', html)
        print(f"Found {len(graphql_queries)} GraphQL queries: {graphql_queries[:5]}")
        
        # Look for window.__INITIAL_STATE__ or similar
        initial_state = re.search(r'window\.__[A-Z_]+__\s*=\s*({.+?});', html, re.DOTALL)
        if initial_state:
            print("Found initial state object")
            try:
                state_data = json.loads(initial_state.group(1))
                with open('instacart_initial_state.json', 'w') as f:
                    json.dump(state_data, f, indent=2)
                print("Saved initial state to: instacart_initial_state.json")
            except:
                print("Could not parse initial state as JSON")
        
        # Look for any Bearer tokens or auth info
        auth_tokens = re.findall(r'["\'](?:token|auth|bearer)["\']?\s*[:=]\s*["\']([^"\']{20,})["\']', html, re.IGNORECASE)
        print(f"Found {len(auth_tokens)} potential auth tokens")
        
        return {
            'json_blocks': len(json_scripts),
            'api_configs': api_config,
            'graphql_queries': graphql_queries,
            'has_initial_state': initial_state is not None
        }
    
    def test_retailers_api(self, zipcode="10001"):
        """Deep dive into retailers API that returned 200"""
        print(f"\n[DEEP DIVE 2] Testing retailers API with zipcode {zipcode}...")
        
        url = f"{self.base_url}/v3/retailers"
        
        # Try different parameter combinations
        param_sets = [
            {'zip': zipcode},
            {'zipcode': zipcode},
            {'postal_code': zipcode},
            {'source': 'web', 'zip': zipcode},
            {},  # No params
        ]
        
        for i, params in enumerate(param_sets, 1):
            print(f"\n  Test {i}: params={params}")
            try:
                response = self.session.get(url, params=params, headers=self.headers, timeout=10)
                print(f"  Status: {response.status_code}, Size: {len(response.text)}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"  JSON keys: {list(data.keys())}")
                        
                        # Save the response
                        with open(f'instacart_retailers_response_{i}.json', 'w') as f:
                            json.dump(data, f, indent=2)
                        print(f"  Saved to: instacart_retailers_response_{i}.json")
                        
                        # Look for useful data
                        if isinstance(data, dict):
                            if 'retailers' in data:
                                print(f"  Found {len(data['retailers'])} retailers")
                            if 'stores' in data:
                                print(f"  Found {len(data['stores'])} stores")
                    except json.JSONDecodeError:
                        print(f"  Not JSON. First 200 chars: {response.text[:200]}")
                        
            except Exception as e:
                print(f"  Error: {e}")
    
    def test_graphql_properly(self):
        """Test GraphQL with proper headers and common query structures"""
        print("\n[DEEP DIVE 3] Testing GraphQL with various query formats...")
        
        url = f"{self.base_url}/graphql"
        
        # Try different GraphQL operations
        queries = [
            # Simple query
            {
                "operationName": "GetProducts",
                "query": "query GetProducts { products { id name } }",
                "variables": {}
            },
            # Search query
            {
                "operationName": "SearchProducts",
                "query": "query SearchProducts($term: String!) { search(term: $term) { id name price } }",
                "variables": {"term": "eggs"}
            },
            # Fragment query
            {
                "query": "{ __type(name: \"Query\") { fields { name } } }"
            },
        ]
        
        graphql_headers = {
            **self.headers,
            'Content-Type': 'application/json',
            'x-client-identifier': 'web',
        }
        
        for i, query in enumerate(queries, 1):
            print(f"\n  Query {i}:")
            try:
                response = self.session.post(
                    url,
                    json=query,
                    headers=graphql_headers,
                    timeout=10
                )
                print(f"  Status: {response.status_code}")
                print(f"  Response: {response.text[:300]}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        with open(f'instacart_graphql_response_{i}.json', 'w') as f:
                            json.dump(data, f, indent=2)
                        print(f"  Saved to: instacart_graphql_response_{i}.json")
                    except:
                        pass
                        
            except Exception as e:
                print(f"  Error: {e}")
    
    def test_store_page(self, store_name="costco"):
        """Try accessing a store page and extracting products"""
        print(f"\n[DEEP DIVE 4] Testing store page for {store_name}...")
        
        store_url = f"{self.base_url}/store/{store_name}/storefront"
        
        try:
            response = self.session.get(store_url, headers=self.headers, timeout=10)
            print(f"Status: {response.status_code}")
            print(f"Response size: {len(response.text)}")
            
            if response.status_code in [200, 202]:
                # Look for embedded product data
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for JSON-LD structured data
                json_ld = soup.find_all('script', type='application/ld+json')
                print(f"Found {len(json_ld)} JSON-LD blocks")
                
                # Look for next-data or similar
                next_data = soup.find('script', id='__NEXT_DATA__')
                if next_data:
                    print("Found __NEXT_DATA__!")
                    try:
                        data = json.loads(next_data.string)
                        with open('instacart_store_nextdata.json', 'w') as f:
                            json.dump(data, f, indent=2)
                        print("Saved to: instacart_store_nextdata.json")
                        
                        # Check for product data
                        data_str = json.dumps(data)
                        if 'price' in data_str.lower():
                            print("✓ Found price data in Next.js data!")
                        if 'product' in data_str.lower():
                            print("✓ Found product data in Next.js data!")
                            
                    except Exception as e:
                        print(f"Error parsing Next data: {e}")
                
                with open('instacart_store_page.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("Saved page to: instacart_store_page.html")
                
        except Exception as e:
            print(f"Error: {e}")
    
    def test_search_page(self, query="eggs"):
        """Try searching and capturing the data"""
        print(f"\n[DEEP DIVE 5] Testing search page for '{query}'...")
        
        search_url = f"{self.base_url}/store/search"
        
        try:
            response = self.session.get(
                search_url,
                params={'q': query, 'query': query},
                headers=self.headers,
                timeout=10
            )
            print(f"Status: {response.status_code}")
            print(f"Response size: {len(response.text)}")
            
            if response.status_code in [200, 202]:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for Next.js data
                next_data = soup.find('script', id='__NEXT_DATA__')
                if next_data:
                    print("Found __NEXT_DATA__!")
                    try:
                        data = json.loads(next_data.string)
                        with open('instacart_search_nextdata.json', 'w') as f:
                            json.dump(data, f, indent=2)
                        print("Saved to: instacart_search_nextdata.json")
                        
                        # Look for products
                        data_str = json.dumps(data)
                        product_count = data_str.lower().count('"name"')
                        price_count = data_str.lower().count('price')
                        print(f"Estimated products: ~{product_count}, price mentions: {price_count}")
                        
                    except Exception as e:
                        print(f"Error: {e}")
                
                with open('instacart_search_page.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("Saved to: instacart_search_page.html")
                
        except Exception as e:
            print(f"Error: {e}")
    
    def run_deep_dive(self):
        """Run comprehensive deep dive"""
        print("="*80)
        print("INSTACART DEEP DIVE ANALYSIS")
        print("="*80)
        
        self.analyze_main_page()
        self.test_retailers_api()
        self.test_graphql_properly()
        self.test_store_page()
        self.test_search_page()
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE - Check generated files for detailed data")
        print("="*80)


if __name__ == "__main__":
    diver = InstacartDeepDive()
    diver.run_deep_dive()

