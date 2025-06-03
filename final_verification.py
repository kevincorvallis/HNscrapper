#!/usr/bin/env python3
"""
Final verification of HN scraper cleanup and functionality.
"""
import requests
import json

def test_redirect():
    """Test that root properly redirects."""
    response = requests.get("http://127.0.0.1:8083/", allow_redirects=False)
    return response.status_code == 302

def test_api_endpoints():
    """Test all API endpoints."""
    endpoints = [
        "/api/stats",
        "/api/domains", 
        "/api/search?q=python",
        "/api/search?q=github&sort_by=comments"
    ]
    
    results = {}
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://127.0.0.1:8083{endpoint}")
            results[endpoint] = response.status_code == 200
        except Exception as e:
            results[endpoint] = False
    
    return results

def test_template_rendering():
    """Test that templates render without errors."""
    response = requests.get("http://127.0.0.1:8083/classic")
    return response.status_code == 200 and "count_comments_recursive" not in response.text

def main():
    print("🔍 Final HN Scraper Verification")
    print("=" * 40)
    
    # Test redirect
    print("\n📍 Testing Root Redirect:")
    if test_redirect():
        print("✅ Root route properly redirects (302)")
    else:
        print("❌ Root route redirect failed")
    
    # Test API endpoints
    print("\n🔌 Testing API Endpoints:")
    api_results = test_api_endpoints()
    for endpoint, success in api_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {endpoint}")
    
    # Test template rendering
    print("\n🎨 Testing Template Rendering:")
    if test_template_rendering():
        print("✅ Templates render without undefined function errors")
    else:
        print("❌ Template rendering has issues")
    
    # Summary
    total_tests = 1 + len(api_results) + 1
    passed_tests = (1 if test_redirect() else 0) + sum(api_results.values()) + (1 if test_template_rendering() else 0)
    
    print(f"\n📊 Final Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All systems operational! HN scraper cleanup completed successfully.")
    else:
        print("⚠️  Some issues remain to be addressed.")

if __name__ == "__main__":
    main()
