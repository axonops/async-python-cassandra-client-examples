#!/usr/bin/env python3
"""
Performance comparison script for async vs sync Cassandra clients.
Runs identical workloads against both applications and generates comparison reports.
"""

import asyncio
import aiohttp
import time
import statistics
import json
from datetime import datetime
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import requests


class PerformanceComparison:
    def __init__(self, async_url="http://localhost:8001", sync_url="http://localhost:8002"):
        self.async_url = async_url
        self.sync_url = sync_url
        self.results = {
            "async": {},
            "sync": {},
            "timestamp": datetime.now().isoformat()
        }
    
    async def test_endpoint_async(self, session: aiohttp.ClientSession, url: str, 
                                 method: str = "GET", json_data: dict = None) -> float:
        """Test a single endpoint and return response time"""
        start = time.time()
        try:
            async with session.request(method, url, json=json_data) as response:
                await response.read()
                return time.time() - start if response.status < 400 else -1
        except Exception as e:
            print(f"Error testing {url}: {e}")
            return -1
    
    def test_endpoint_sync(self, url: str, method: str = "GET", json_data: dict = None) -> float:
        """Test a single endpoint synchronously and return response time"""
        start = time.time()
        try:
            response = requests.request(method, url, json=json_data)
            return time.time() - start if response.status_code < 400 else -1
        except Exception as e:
            print(f"Error testing {url}: {e}")
            return -1
    
    async def run_concurrent_test_async(self, endpoint: str, count: int, 
                                      method: str = "GET", json_data: dict = None) -> Dict:
        """Run concurrent requests against async app"""
        url = f"{self.async_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            
            # Create tasks for concurrent requests
            tasks = [
                self.test_endpoint_async(session, url, method, json_data) 
                for _ in range(count)
            ]
            
            # Execute all requests concurrently
            response_times = await asyncio.gather(*tasks)
            
            total_time = time.time() - start_time
            
        # Filter out errors
        valid_times = [t for t in response_times if t > 0]
        errors = len([t for t in response_times if t <= 0])
        
        return {
            "total_requests": count,
            "successful_requests": len(valid_times),
            "errors": errors,
            "total_time": total_time,
            "requests_per_second": count / total_time,
            "avg_response_time": statistics.mean(valid_times) if valid_times else 0,
            "min_response_time": min(valid_times) if valid_times else 0,
            "max_response_time": max(valid_times) if valid_times else 0,
            "p50_response_time": statistics.median(valid_times) if valid_times else 0,
            "p95_response_time": np.percentile(valid_times, 95) if valid_times else 0,
            "p99_response_time": np.percentile(valid_times, 99) if valid_times else 0,
        }
    
    def run_concurrent_test_sync(self, endpoint: str, count: int, 
                               method: str = "GET", json_data: dict = None) -> Dict:
        """Run concurrent requests against sync app using thread pool"""
        url = f"{self.sync_url}{endpoint}"
        
        start_time = time.time()
        
        # Use thread pool for concurrent sync requests
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(self.test_endpoint_sync, url, method, json_data)
                for _ in range(count)
            ]
            response_times = [f.result() for f in futures]
        
        total_time = time.time() - start_time
        
        # Filter out errors
        valid_times = [t for t in response_times if t > 0]
        errors = len([t for t in response_times if t <= 0])
        
        return {
            "total_requests": count,
            "successful_requests": len(valid_times),
            "errors": errors,
            "total_time": total_time,
            "requests_per_second": count / total_time,
            "avg_response_time": statistics.mean(valid_times) if valid_times else 0,
            "min_response_time": min(valid_times) if valid_times else 0,
            "max_response_time": max(valid_times) if valid_times else 0,
            "p50_response_time": statistics.median(valid_times) if valid_times else 0,
            "p95_response_time": np.percentile(valid_times, 95) if valid_times else 0,
            "p99_response_time": np.percentile(valid_times, 99) if valid_times else 0,
        }
    
    async def compare_endpoint(self, endpoint: str, test_name: str, 
                             concurrent_requests: List[int], 
                             method: str = "GET", json_data: dict = None):
        """Compare performance of an endpoint between async and sync apps"""
        print(f"\n=== Testing: {test_name} ===")
        print(f"Endpoint: {endpoint}")
        
        async_results = []
        sync_results = []
        
        for count in concurrent_requests:
            print(f"\nTesting with {count} concurrent requests...")
            
            # Test async app
            print("Testing async app...")
            async_result = await self.run_concurrent_test_async(endpoint, count, method, json_data)
            async_results.append(async_result)
            print(f"Async RPS: {async_result['requests_per_second']:.2f}")
            
            # Test sync app
            print("Testing sync app...")
            sync_result = self.run_concurrent_test_sync(endpoint, count, method, json_data)
            sync_results.append(sync_result)
            print(f"Sync RPS: {sync_result['requests_per_second']:.2f}")
            
            # Calculate improvement
            improvement = ((async_result['requests_per_second'] - sync_result['requests_per_second']) 
                         / sync_result['requests_per_second'] * 100)
            print(f"Improvement: {improvement:+.1f}%")
        
        self.results["async"][test_name] = async_results
        self.results["sync"][test_name] = sync_results
    
    def generate_report(self):
        """Generate performance comparison report with visualizations"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw results
        with open(f"results/comparison_{timestamp}.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Generate plots
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Async vs Sync Cassandra Client Performance Comparison', fontsize=16)
        
        for test_name in self.results["async"].keys():
            async_data = self.results["async"][test_name]
            sync_data = self.results["sync"][test_name]
            
            if not async_data or not sync_data:
                continue
            
            concurrent_counts = [d["total_requests"] for d in async_data]
            async_rps = [d["requests_per_second"] for d in async_data]
            sync_rps = [d["requests_per_second"] for d in sync_data]
            async_p95 = [d["p95_response_time"] * 1000 for d in async_data]  # Convert to ms
            sync_p95 = [d["p95_response_time"] * 1000 for d in sync_data]
            
            # Plot 1: Requests per second
            ax1 = axes[0, 0]
            ax1.plot(concurrent_counts, async_rps, 'b-o', label='Async', linewidth=2)
            ax1.plot(concurrent_counts, sync_rps, 'r-o', label='Sync', linewidth=2)
            ax1.set_xlabel('Concurrent Requests')
            ax1.set_ylabel('Requests/Second')
            ax1.set_title('Throughput Comparison')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: P95 Response Time
            ax2 = axes[0, 1]
            ax2.plot(concurrent_counts, async_p95, 'b-o', label='Async', linewidth=2)
            ax2.plot(concurrent_counts, sync_p95, 'r-o', label='Sync', linewidth=2)
            ax2.set_xlabel('Concurrent Requests')
            ax2.set_ylabel('P95 Response Time (ms)')
            ax2.set_title('Latency Comparison (P95)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Plot 3: Improvement percentage
            ax3 = axes[1, 0]
            improvements = [(a["requests_per_second"] - s["requests_per_second"]) / s["requests_per_second"] * 100 
                          for a, s in zip(async_data, sync_data)]
            bars = ax3.bar(range(len(concurrent_counts)), improvements, color=['green' if i > 0 else 'red' for i in improvements])
            ax3.set_xticks(range(len(concurrent_counts)))
            ax3.set_xticklabels([str(c) for c in concurrent_counts])
            ax3.set_xlabel('Concurrent Requests')
            ax3.set_ylabel('Improvement %')
            ax3.set_title('Async Performance Improvement over Sync')
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax3.grid(True, alpha=0.3, axis='y')
            
            # Add percentage labels on bars
            for bar, imp in zip(bars, improvements):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{imp:.1f}%', ha='center', va='bottom' if height > 0 else 'top')
            
            # Plot 4: Summary statistics
            ax4 = axes[1, 1]
            ax4.axis('off')
            
            # Calculate average improvements
            avg_throughput_imp = statistics.mean(improvements)
            avg_latency_reduction = statistics.mean([
                (s["p95_response_time"] - a["p95_response_time"]) / s["p95_response_time"] * 100 
                for a, s in zip(async_data, sync_data)
            ])
            
            summary_text = f"""Summary for {test_name}:
            
Avg Throughput Improvement: {avg_throughput_imp:+.1f}%
Avg P95 Latency Reduction: {avg_latency_reduction:+.1f}%

Best Async RPS: {max(async_rps):.2f}
Best Sync RPS: {max(sync_rps):.2f}

Best Async P95: {min(async_p95):.2f}ms
Best Sync P95: {min(sync_p95):.2f}ms
"""
            ax4.text(0.1, 0.5, summary_text, fontsize=12, verticalalignment='center',
                    fontfamily='monospace', bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray"))
        
        plt.tight_layout()
        plt.savefig(f"results/comparison_{timestamp}.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\n✅ Report saved to results/comparison_{timestamp}.json")
        print(f"✅ Visualization saved to results/comparison_{timestamp}.png")
        
        return f"results/comparison_{timestamp}.json"
    
    async def run_full_comparison(self):
        """Run a full performance comparison test suite"""
        print("Starting full performance comparison...")
        print(f"Async URL: {self.async_url}")
        print(f"Sync URL: {self.sync_url}")
        
        # Create test user data
        user_data = {
            "id": "test-user-001",
            "username": "perftest_user",
            "email": "perftest@example.com",
            "profile_data": {"test": True}
        }
        
        # Test scenarios with increasing concurrent requests
        concurrent_levels = [1, 10, 50, 100, 200]
        
        # Test 1: Read operations
        await self.compare_endpoint(
            endpoint="/api/v1/users",
            test_name="List Users",
            concurrent_requests=concurrent_levels,
            method="GET"
        )
        
        # Create a user first for read tests
        requests.post(f"{self.async_url}/api/v1/users", json=user_data)
        requests.post(f"{self.sync_url}/api/v1/users", json=user_data)
        
        # Test 2: Single read operations
        await self.compare_endpoint(
            endpoint="/api/v1/users/test-user-001",
            test_name="Get Single User",
            concurrent_requests=concurrent_levels,
            method="GET"
        )
        
        # Test 3: Write operations
        await self.compare_endpoint(
            endpoint="/api/v1/users",
            test_name="Create User",
            concurrent_requests=[1, 10, 50, 100],  # Less for writes
            method="POST",
            json_data={
                "username": "test_user",
                "email": "test@example.com",
                "profile_data": {"test": True}
            }
        )
        
        # Generate report
        report_path = self.generate_report()
        
        print("\n=== Comparison Complete ===")
        print(f"Full results available in: {report_path}")


async def main():
    # Create results directory
    import os
    os.makedirs("results", exist_ok=True)
    
    # Run comparison
    comparison = PerformanceComparison()
    await comparison.run_full_comparison()


if __name__ == "__main__":
    asyncio.run(main())