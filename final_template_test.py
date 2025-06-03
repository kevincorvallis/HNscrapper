#!/usr/bin/env python3
"""
Final comprehensive test after template cleanup.
"""
import requests
import json
import time

def test_all_routes():
    """Test all application routes after template cleanup."""
    base_url = "http://127.0.0.1:8083"
    
    routes_to_test = [
        ("/", 302, "Root redirect"),
        ("/classic", 200, "Classic view (main interface)"),
        ("/stats", 200, "Statistics view"),
        ("/curate", 200, "Curator interface"),
        ("/overview", 200, "Overview page"),
        ("/api/stats", 200, "Stats API"),
        ("/api/domains", 200, "Domains API"),
        ("/api/search?q=python", 200, "Search API"),
        ("/nonexistent", 404, "404 error handling"),
    ]
    
    print("🧪 Final Template Cleanup Verification")
    print("=" * 50)
    
    all_passed = True
    
    for route, expected_status, description in routes_to_test:
        try:
            response = requests.get(f"{base_url}{route}", timeout=10)
            if response.status_code == expected_status:
                print(f"✅ PASS: {description} ({route})")
            else:
                print(f"❌ FAIL: {description} ({route}) - Expected {expected_status}, got {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"❌ ERROR: {description} ({route}) - {str(e)}")
            all_passed = False
    
    # Test individual article route
    try:
        search_response = requests.get(f"{base_url}/api/search?q=python")
        if search_response.status_code == 200:
            articles = search_response.json()
            if articles:
                article_id = articles[0]['hn_id']
                article_response = requests.get(f"{base_url}/article/{article_id}")
                if article_response.status_code == 200:
                    print(f"✅ PASS: Individual article view (/article/{article_id})")
                else:
                    print(f"❌ FAIL: Individual article view - Status {article_response.status_code}")
                    all_passed = False
    except Exception as e:
        print(f"❌ ERROR: Individual article test - {str(e)}")
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Template cleanup successful!")
        print("📊 Application is fully operational with clean template structure")
    else:
        print("⚠️  Some tests failed - please check the issues above")
    
    return all_passed

def check_template_structure():
    """Verify the cleaned template structure."""
    import os
    template_dir = "/Users/kevin/Downloads/HNscrapper/src/web/templates"
    
    print("\n📁 Template Directory Structure:")
    if os.path.exists(template_dir):
        files = os.listdir(template_dir)
        for file in sorted(files):
            file_path = os.path.join(template_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"   📄 {file} ({size} bytes)")
            elif os.path.isdir(file_path):
                print(f"   📁 {file}/")
    
    expected_files = {"index.html", "404.html", "500.html"}
    actual_files = {f for f in files if f.endswith('.html')}
    
    if actual_files == expected_files:
        print("✅ Template structure is clean and correct")
        return True
    else:
        print(f"❌ Template structure issue - Expected: {expected_files}, Found: {actual_files}")
        return False

if __name__ == "__main__":
    time.sleep(1)  # Give server time to start
    
    routes_ok = test_all_routes()
    structure_ok = check_template_structure()
    
    if routes_ok and structure_ok:
        print("\n🏆 FINAL RESULT: Template cleanup COMPLETE and SUCCESSFUL!")
    else:
        print("\n🔧 FINAL RESULT: Some issues remain to be addressed")
