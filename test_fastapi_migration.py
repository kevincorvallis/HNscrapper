#!/usr/bin/env python3
"""
Test script to verify FastAPI migration was successful
"""
import sys
import os
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_fastapi_import():
    """Test if FastAPI app can be imported"""
    print("🧪 Testing FastAPI import...")
    try:
        from fastapi_enhanced_app import app, OptimizedDatabaseManager
        print("✅ FastAPI app imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database_manager():
    """Test database manager functionality"""
    print("🧪 Testing database manager...")
    try:
        from fastapi_enhanced_app import OptimizedDatabaseManager
        
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'enhanced_hn_articles.db')
        if not os.path.exists(db_path):
            print("⚠️ Database file not found - skipping database tests")
            return True
            
        db_manager = OptimizedDatabaseManager(db_path)
        
        # Test basic stats
        stats = db_manager.get_basic_stats()
        print(f"✅ Database stats: {stats}")
        
        # Test article retrieval
        articles = db_manager.get_enhanced_articles_safe(limit=3)
        print(f"✅ Retrieved {len(articles)} sample articles")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_fastapi_endpoints():
    """Test FastAPI endpoints using TestClient"""
    print("🧪 Testing FastAPI endpoints...")
    try:
        from fastapi.testclient import TestClient
        from fastapi_enhanced_app import app
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test homepage
        response = client.get("/")
        if response.status_code == 200:
            print("✅ Homepage endpoint working")
        else:
            print(f"❌ Homepage endpoint failed: {response.status_code}")
            return False
        
        # Test API stats
        response = client.get("/api/stats")
        if response.status_code == 200:
            print("✅ API stats endpoint working")
        else:
            print(f"❌ API stats endpoint failed: {response.status_code}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Endpoint test failed: {e}")
        return False

def test_pydantic_models():
    """Test Pydantic models"""
    print("🧪 Testing Pydantic models...")
    try:
        from fastapi_enhanced_app import ArticleFilter, SearchRequest, StatsResponse, ArticleResponse
        
        # Test ArticleFilter
        filter_data = ArticleFilter(search="test", domain="github.com", limit=10)
        print(f"✅ ArticleFilter model working: {filter_data.search}")
        
        # Test SearchRequest
        search_data = SearchRequest(q="python", limit=5)
        print(f"✅ SearchRequest model working: {search_data.q}")
        
        return True
    except Exception as e:
        print(f"❌ Pydantic models test failed: {e}")
        return False

def main():
    """Run all migration tests"""
    print("🚀 Starting FastAPI Migration Tests")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_fastapi_import),
        ("Database Manager Test", test_database_manager),
        ("Pydantic Models Test", test_pydantic_models),
        ("FastAPI Endpoints Test", test_fastapi_endpoints),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! FastAPI migration successful!")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
