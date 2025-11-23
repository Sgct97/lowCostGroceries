#!/usr/bin/env python3
"""
Production Load Test
Simulates real user traffic to find bottlenecks and breaking points

Tests:
1. Concurrent users submitting carts
2. Response times under load
3. SerpAPI rate limits
4. Redis queue performance
5. Worker processing capacity
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime
from typing import List, Dict
import sys

# Configuration
API_URL = "http://146.190.129.92:8000"
ZIP_CODE = "33773"

# Test scenarios - realistic grocery searches
TEST_CARTS = [
    ["Whole Milk, 1 Gallon", "Large Eggs, 12 Count"],
    ["White Bread, 24 oz", "Butter, 1 lb"],
    ["Orange Juice, 64 oz", "Bananas, 1 lb"],
    ["Ground Beef, 1 lb", "Chicken Breast, 1 lb"],
    ["Cheddar Cheese, 8 oz", "Yogurt, 32 oz"],
]

class LoadTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = {
            'submit_times': [],
            'poll_times': [],
            'total_times': [],
            'errors': [],
            'success_count': 0,
            'failure_count': 0
        }
    
    async def simulate_user(self, session: aiohttp.ClientSession, user_id: int, cart_items: List[str]):
        """Simulate a single user's journey"""
        start_time = time.time()
        
        try:
            # Step 1: Submit cart
            submit_start = time.time()
            async with session.post(
                f"{self.base_url}/api/cart",
                json={
                    "items": cart_items,
                    "zipcode": ZIP_CODE,
                    "prioritize_nearby": True
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    self.results['errors'].append(f"User {user_id}: Submit failed with {response.status}")
                    self.results['failure_count'] += 1
                    return
                
                data = await response.json()
                job_id = data.get('job_id')
                
                if not job_id:
                    self.results['errors'].append(f"User {user_id}: No job_id returned")
                    self.results['failure_count'] += 1
                    return
            
            submit_time = time.time() - submit_start
            self.results['submit_times'].append(submit_time)
            
            # Step 2: Poll for results (max 30 seconds)
            poll_start = time.time()
            max_polls = 30
            poll_count = 0
            
            while poll_count < max_polls:
                await asyncio.sleep(1)
                poll_count += 1
                
                try:
                    async with session.get(
                        f"{self.base_url}/api/results/{job_id}",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status != 200:
                            continue
                        
                        data = await response.json()
                        status = data.get('status')
                        
                        if status == 'complete':
                            poll_time = time.time() - poll_start
                            total_time = time.time() - start_time
                            
                            self.results['poll_times'].append(poll_time)
                            self.results['total_times'].append(total_time)
                            self.results['success_count'] += 1
                            
                            # Count products returned
                            results = data.get('results', {})
                            product_count = sum(len(products) for products in results.values())
                            
                            print(f"✅ User {user_id}: {total_time:.1f}s ({product_count} products)")
                            return
                        
                        elif status == 'failed':
                            error_msg = data.get('error', 'Unknown error')
                            self.results['errors'].append(f"User {user_id}: Job failed - {error_msg}")
                            self.results['failure_count'] += 1
                            return
                
                except asyncio.TimeoutError:
                    continue
            
            # Timeout
            self.results['errors'].append(f"User {user_id}: Timeout after {max_polls}s")
            self.results['failure_count'] += 1
        
        except Exception as e:
            self.results['errors'].append(f"User {user_id}: Exception - {str(e)}")
            self.results['failure_count'] += 1
    
    async def run_wave(self, wave_num: int, concurrent_users: int):
        """Run a wave of concurrent users"""
        print(f"\n{'='*60}")
        print(f"Wave {wave_num}: {concurrent_users} concurrent users")
        print(f"{'='*60}")
        
        connector = aiohttp.TCPConnector(limit=100)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for i in range(concurrent_users):
                cart = TEST_CARTS[i % len(TEST_CARTS)]
                task = self.simulate_user(session, i + 1, cart)
                tasks.append(task)
            
            wave_start = time.time()
            await asyncio.gather(*tasks)
            wave_time = time.time() - wave_start
            
            print(f"\n⏱️  Wave {wave_num} completed in {wave_time:.1f}s")
    
    def print_stats(self):
        """Print comprehensive statistics"""
        print(f"\n{'='*60}")
        print("LOAD TEST RESULTS")
        print(f"{'='*60}")
        
        total_requests = self.results['success_count'] + self.results['failure_count']
        success_rate = (self.results['success_count'] / total_requests * 100) if total_requests > 0 else 0
        
        print(f"\n📊 Summary:")
        print(f"   Total Requests: {total_requests}")
        print(f"   Successful: {self.results['success_count']} ({success_rate:.1f}%)")
        print(f"   Failed: {self.results['failure_count']}")
        
        if self.results['submit_times']:
            print(f"\n⚡ Submit Times:")
            print(f"   Min: {min(self.results['submit_times']):.2f}s")
            print(f"   Max: {max(self.results['submit_times']):.2f}s")
            print(f"   Avg: {statistics.mean(self.results['submit_times']):.2f}s")
            print(f"   Median: {statistics.median(self.results['submit_times']):.2f}s")
        
        if self.results['poll_times']:
            print(f"\n🔄 Poll Times (waiting for results):")
            print(f"   Min: {min(self.results['poll_times']):.2f}s")
            print(f"   Max: {max(self.results['poll_times']):.2f}s")
            print(f"   Avg: {statistics.mean(self.results['poll_times']):.2f}s")
            print(f"   Median: {statistics.median(self.results['poll_times']):.2f}s")
        
        if self.results['total_times']:
            print(f"\n⏱️  Total Times (end-to-end):")
            print(f"   Min: {min(self.results['total_times']):.2f}s")
            print(f"   Max: {max(self.results['total_times']):.2f}s")
            print(f"   Avg: {statistics.mean(self.results['total_times']):.2f}s")
            print(f"   Median: {statistics.median(self.results['total_times']):.2f}s")
            
            # Calculate throughput
            if self.results['total_times']:
                total_test_time = max(self.results['total_times'])
                throughput = self.results['success_count'] / total_test_time
                print(f"\n🚀 Throughput: {throughput:.2f} requests/second")
        
        if self.results['errors']:
            print(f"\n❌ Errors ({len(self.results['errors'])}):")
            for error in self.results['errors'][:10]:  # Show first 10
                print(f"   • {error}")
            if len(self.results['errors']) > 10:
                print(f"   ... and {len(self.results['errors']) - 10} more")
        
        # SerpAPI rate limit estimate
        if self.results['success_count'] > 0:
            avg_items_per_cart = statistics.mean([len(cart) for cart in TEST_CARTS])
            total_serpapi_calls = self.results['success_count'] * avg_items_per_cart
            test_duration = max(self.results['total_times']) if self.results['total_times'] else 0
            
            if test_duration > 0:
                serpapi_rate = total_serpapi_calls / test_duration
                print(f"\n🔑 SerpAPI Usage:")
                print(f"   Total API calls: {int(total_serpapi_calls)}")
                print(f"   Rate: {serpapi_rate:.2f} calls/second")
                print(f"   Note: SerpAPI free tier = 100 calls/month")


async def main():
    """Run progressive load test"""
    print("🚀 Starting Production Load Test")
    print(f"API: {API_URL}")
    print(f"Test Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = LoadTester(API_URL)
    
    # Progressive load test
    waves = [
        (1, 5),   # Wave 1: 5 users
        (2, 10),  # Wave 2: 10 users
        (3, 20),  # Wave 3: 20 users
        (4, 50),  # Wave 4: 50 users (stress test)
    ]
    
    for wave_num, user_count in waves:
        try:
            await tester.run_wave(wave_num, user_count)
            
            # Brief pause between waves
            if wave_num < len(waves):
                print(f"\n⏸️  Pausing 5 seconds before next wave...")
                await asyncio.sleep(5)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            break
    
    # Print final statistics
    tester.print_stats()
    
    # Recommendations
    print(f"\n{'='*60}")
    print("💡 RECOMMENDATIONS")
    print(f"{'='*60}")
    
    if tester.results['success_count'] > 0:
        avg_time = statistics.mean(tester.results['total_times'])
        
        if avg_time < 3:
            print("✅ Excellent: Response times under 3 seconds")
        elif avg_time < 5:
            print("⚠️  Acceptable: Response times 3-5 seconds")
        else:
            print("❌ Slow: Response times over 5 seconds")
            print("   Consider: Adding more workers or using SerpAPI only")
    
    success_rate = (tester.results['success_count'] / (tester.results['success_count'] + tester.results['failure_count']) * 100) if tester.results['success_count'] + tester.results['failure_count'] > 0 else 0
    
    if success_rate >= 99:
        print("✅ Excellent: 99%+ success rate")
    elif success_rate >= 95:
        print("⚠️  Acceptable: 95-99% success rate")
    else:
        print("❌ Poor: <95% success rate")
        print("   Check: Worker health, Redis connection, SerpAPI limits")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled by user")
        sys.exit(0)
