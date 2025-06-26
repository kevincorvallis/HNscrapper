#!/usr/bin/env python3
"""
Comprehensive test script for HN Scraper deployment.
Tests both local and Vercel deployed versions.
"""

import requests
import json
import sys
import time
from datetime import datetime

def test_endpoint(base_url, endpoint, expected_status=200, timeout=10):
    """Test a single endpoint."""
    url = f"{base_url}{endpoint}"
    try:
        print(f"Testing: {url}")
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        end_time = time.time()
        
        result = {
            'url': url,
            'status_code': response.status_code,
            'response_time': round(end_time - start_time, 2),
            'success': response.status_code == expected_status,
            'content_length': len(response.content),
            'content_type': response.headers.get('content-type', 'unknown')
        }
        
        # Try to parse JSON if possible
        if 'application/json' in result['content_type']:
            try:
                result['json_data'] = response.json()
            except:
                result['json_data'] = None
        
        # Get first 200 chars of content for preview
        if result['content_length'] > 0:
            content_preview = response.text[:200].replace('\n', ' ').strip()
            result['content_preview'] = content_preview
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {
            'url': url,
            'status_code': 'ERROR',
            'success': False,
            'error': str(e),
            'response_time': 0
        }

def run_tests():
    """Run comprehensive tests."""
    print("🧪 HN Scraper Deployment Test Suite")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test configurations
    test_configs = [
        {
            'name': 'Local Development',
            'base_url': 'http://127.0.0.1:5001',
            'endpoints': [
                '/',
                '/classic',
                '/stats',
                '/api/articles',
                '/api/stats'
            ]
        },
        {
            'name': 'Vercel Production - Pookie B News Daily',
            'base_url': 'https://hn-scrapper-3bwii3weo-kevin-lees-projects-e0039a73.vercel.app',
            'endpoints': [
                '/',
                '/api/health',
                '/api/articles',
                '/api/stats',
                '/test',
                '/audio_files/pookie_b_weekly_latest.mp3'
            ]
        }
    ]
    
    all_results = []
    
    for config in test_configs:
        print(f"🔍 Testing {config['name']}")
        print(f"Base URL: {config['base_url']}")
        print("-" * 40)
        
        config_results = []
        
        for endpoint in config['endpoints']:
            result = test_endpoint(config['base_url'], endpoint)
            config_results.append(result)
            
            # Print result
            status_icon = "✅" if result['success'] else "❌"
            status_code = result.get('status_code', 'ERROR')
            response_time = result.get('response_time', 0)
            
            print(f"{status_icon} {endpoint} - {status_code} ({response_time}s)")
            
            if not result['success'] and 'error' in result:
                print(f"   Error: {result['error']}")
            elif result.get('content_preview'):
                preview = result['content_preview'][:80] + "..." if len(result['content_preview']) > 80 else result['content_preview']
                print(f"   Preview: {preview}")
        
        all_results.append({
            'config': config['name'],
            'results': config_results
        })
        
        print()
    
    # Summary
    print("📊 Test Summary")
    print("=" * 50)
    
    for test_group in all_results:
        config_name = test_group['config']
        results = test_group['results']
        
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        print(f"{config_name}: {successful}/{total} tests passed ({success_rate:.1f}%)")
        
        # Show failures
        failures = [r for r in results if not r['success']]
        if failures:
            print("  Failures:")
            for failure in failures:
                endpoint = failure['url'].split('/')[-1] or '/'
                status = failure.get('status_code', 'ERROR')
                print(f"    - {endpoint}: {status}")
        
        print()
    
    # Performance summary
    print("⚡ Performance Summary")
    print("-" * 30)
    
    for test_group in all_results:
        config_name = test_group['config']
        results = test_group['results']
        
        successful_results = [r for r in results if r['success'] and r.get('response_time', 0) > 0]
        if successful_results:
            avg_time = sum(r['response_time'] for r in successful_results) / len(successful_results)
            min_time = min(r['response_time'] for r in successful_results)
            max_time = max(r['response_time'] for r in successful_results)
            
            print(f"{config_name}:")
            print(f"  Average: {avg_time:.2f}s")
            print(f"  Min: {min_time:.2f}s")
            print(f"  Max: {max_time:.2f}s")
            print()
    
    # Detailed JSON output
    print("📋 Detailed Results (JSON)")
    print("-" * 30)
    print(json.dumps(all_results, indent=2, default=str))
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    run_tests()
