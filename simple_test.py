#!/usr/bin/env python3
"""
Simple test script to verify the HN Scraper application functionality.
"""

import requests
import json
import time

def test_app():
    """Test the running Flask application."""
    base_url = "http://127.0.0.1:8083"
    
    print("🧪 Testing HN Scraper Application")
    print("=" * 50)
    
    # Test 1: Homepage
    print("1. Testing homepage redirect...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Homepage loads successfully")
        else:
            print(f"   ❌ Homepage failed with status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Homepage test failed: {e}")
    
    # Test 2: Classic view
    print("2. Testing classic view...")
    try:
        response = requests.get(f"{base_url}/classic", timeout=5)
        if response.status_code == 200:
            print("   ✅ Classic view loads successfully")
        else:
            print(f"   ❌ Classic view failed with status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Classic view test failed: {e}")
    
    # Test 3: API Stats
    print("3. Testing API stats...")
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Stats API working - {data.get('total_articles', 0)} articles")
        else:
            print(f"   ❌ Stats API failed with status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Stats API test failed: {e}")
    
    # Test 4: API Domains
    print("4. Testing API domains...")
    try:
        response = requests.get(f"{base_url}/api/domains", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Domains API working - {len(data)} domains")
        else:
            print(f"   ❌ Domains API failed with status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Domains API test failed: {e}")
    
    # Test 5: Search API
    print("5. Testing search API...")
    try:
        response = requests.get(f"{base_url}/api/search/comprehensive?q=python", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Search API working - found {len(data)} results")
        else:
            print(f"   ❌ Search API failed with status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Search API test failed: {e}")
    
    # Test 6: Analysis Summary
    print("6. Testing analysis summary API...")
    try:
        response = requests.get(f"{base_url}/api/analysis/summary", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Analysis summary working - {data.get('total_articles', 0)} analyzed articles")
        else:
            print(f"   ❌ Analysis summary failed with status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Analysis summary test failed: {e}")
    
    # Test 7: Analyze API
    print("7. Testing analyze API...")
    try:
        analyze_data = {"content": "This is a discussion about AI and machine learning"}
        response = requests.post(f"{base_url}/api/analyze", 
                               json=analyze_data, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Analyze API working - found {len(data.get('analysis', []))} patterns")
            else:
                print(f"   ❌ Analyze API returned error: {data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ Analyze API failed with status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Analyze API test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Test completed! Check results above.")

if __name__ == "__main__":
    test_app()
