#!/usr/bin/env python3
"""
Simple Integration Test for HN Enhanced Scraper
Tests core functionality without external HTTP requests
"""

import sys
import os
import sqlite3

def test_database():
    """Test database connectivity and content"""
    print("🔍 Testing database...")
    
    db_path = '/Users/kevin/Downloads/HNscrapper/data/enhanced_hn_articles.db'
    
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute("SELECT COUNT(*) FROM articles")
        articles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM article_analyses")
        analyses = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comments")
        comments = cursor.fetchone()[0]
        
        print(f"   ✅ Articles: {articles}")
        print(f"   ✅ Analyses: {analyses}")
        print(f"   ✅ Comments: {comments}")
        
        # Test sample data
        cursor.execute("""
            SELECT title, domain, discussion_quality_score 
            FROM articles 
            WHERE discussion_quality_score IS NOT NULL 
            LIMIT 3
        """)
        samples = cursor.fetchall()
        print(f"   ✅ Quality-scored articles: {len(samples)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_template():
    """Test template availability"""
    print("\n📄 Testing template...")
    
    template_path = '/Users/kevin/Downloads/HNscrapper/templates/index.html'
    
    if not os.path.exists(template_path):
        print("❌ Template not found!")
        return False
    
    try:
        with open(template_path, 'r') as f:
            content = f.read()
        
        features_found = 0
        checks = [
            ('Analytics Dashboard', 'analytics' in content.lower()),
            ('Chart Integration', 'chart' in content.lower()),
            ('Filter System', 'filter' in content.lower()),
            ('Apple Design', 'backdrop-blur' in content or 'apple' in content.lower())
        ]
        
        for name, found in checks:
            if found:
                features_found += 1
                print(f"   ✅ {name}: Found")
            else:
                print(f"   ⚠️  {name}: Not detected")
        
        print(f"   📊 Template size: {len(content)} chars")
        return features_found >= 2
        
    except Exception as e:
        print(f"❌ Template error: {e}")
        return False

def test_app_import():
    """Test app import"""
    print("\n🐍 Testing app import...")
    
    try:
        sys.path.insert(0, '/Users/kevin/Downloads/HNscrapper')
        import optimized_enhanced_app
        
        # Check key components
        has_app = hasattr(optimized_enhanced_app, 'app')
        has_db_manager = hasattr(optimized_enhanced_app, 'OptimizedDatabaseManager')
        
        print(f"   ✅ Import successful")
        print(f"   ✅ Flask app: {'Found' if has_app else 'Missing'}")
        print(f"   ✅ DB Manager: {'Found' if has_db_manager else 'Missing'}")
        
        return has_app and has_db_manager
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_database_manager():
    """Test the OptimizedDatabaseManager directly"""
    print("\n🗄️ Testing database manager...")
    
    try:
        sys.path.insert(0, '/Users/kevin/Downloads/HNscrapper')
        from optimized_enhanced_app import OptimizedDatabaseManager
        
        db_manager = OptimizedDatabaseManager('/Users/kevin/Downloads/HNscrapper/data/enhanced_hn_articles.db')
        
        # Test basic operations
        stats = db_manager.get_basic_stats()
        print(f"   ✅ Basic stats: {stats}")
        
        articles = db_manager.get_enhanced_articles_safe(limit=3)
        print(f"   ✅ Sample articles: {len(articles)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database manager error: {e}")
        return False

def main():
    """Run simple integration test"""
    print("🚀 HN Enhanced Scraper - Simple Integration Test")
    print("=" * 50)
    
    tests = [
        ("Database", test_database),
        ("Template", test_template), 
        ("App Import", test_app_import),
        ("DB Manager", test_database_manager)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
            print()
        except Exception as e:
            print(f"❌ {name} test failed: {e}")
            print()
    
    print("=" * 50)
    print("📊 RESULTS")
    print("=" * 50)
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("   🎉 All tests passed!")
        print("\n🚀 Ready to start the enhanced homepage:")
        print("   python optimized_enhanced_app.py")
    else:
        print(f"   ⚠️  {total - passed} tests failed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 Test completed: {'SUCCESS' if success else 'FAILURE'}")
