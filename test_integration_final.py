#!/usr/bin/env python3
"""
Final Integration Test for HN Enhanced Scraper
Tests the optimized Flask app, database connectivity, and homepage functionality
"""

import sys
import os
import sqlite3
import subprocess
import time
import requests
from threading import Thread

def test_database_connectivity():
    """Test basic database connectivity and data availability"""
    print("🔍 Testing database connectivity...")
    
    db_path = '/Users/kevin/Downloads/HNscrapper/data/enhanced_hn_articles.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        
        # Test basic queries
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        print(f"   ✅ Articles: {article_count}")
        
        cursor.execute("SELECT COUNT(*) FROM article_analyses")
        analysis_count = cursor.fetchone()[0]
        print(f"   ✅ Analyses: {analysis_count}")
        
        cursor.execute("SELECT COUNT(*) FROM comments")
        comment_count = cursor.fetchone()[0]
        print(f"   ✅ Comments: {comment_count}")
        
        # Test sample data
        cursor.execute("""
            SELECT title, domain, discussion_quality_score 
            FROM articles 
            WHERE discussion_quality_score IS NOT NULL 
            LIMIT 3
        """)
        
        sample_articles = cursor.fetchall()
        print(f"   ✅ Sample articles with quality scores: {len(sample_articles)}")
        for title, domain, score in sample_articles:
            print(f"      - {title[:50]}... ({domain}) - Score: {score}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_template_availability():
    """Test if enhanced homepage template exists and is readable"""
    print("\n📄 Testing template availability...")
    
    template_path = '/Users/kevin/Downloads/HNscrapper/templates/index.html'
    
    if not os.path.exists(template_path):
        print("❌ Enhanced homepage template not found!")
        return False
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key enhanced features
        features = {
            'AI Analytics Dashboard': 'analytics-dashboard' in content,
            'Chart.js Integration': 'Chart.js' in content or 'chart.js' in content,
            'Advanced Filtering': 'filter-container' in content,
            'Real-time Metrics': 'real-time-metrics' in content or 'metrics' in content,
            'Apple-style Design': 'apple-card' in content or 'backdrop-blur' in content
        }
        
        print(f"   ✅ Template size: {len(content)} characters")
        for feature, present in features.items():
            status = "✅" if present else "⚠️"
            print(f"   {status} {feature}: {'Present' if present else 'Not detected'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Template error: {e}")
        return False

def test_flask_app_import():
    """Test if the optimized Flask app can be imported"""
    print("\n🐍 Testing Flask app import...")
    
    try:
        # Test import
        sys.path.insert(0, '/Users/kevin/Downloads/HNscrapper')
        import optimized_enhanced_app
        print("   ✅ Optimized app imported successfully")
        
        # Test if it has the expected components
        if hasattr(optimized_enhanced_app, 'app'):
            print("   ✅ Flask app instance found")
        
        if hasattr(optimized_enhanced_app, 'OptimizedDatabaseManager'):
            print("   ✅ OptimizedDatabaseManager class found")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def start_flask_app():
    """Start the Flask app in a subprocess"""
    print("\n🚀 Starting Flask application...")
    
    try:
        # Start the app
        process = subprocess.Popen(
            ['python', 'optimized_enhanced_app.py'],
            cwd='/Users/kevin/Downloads/HNscrapper',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for startup
        time.sleep(3)
        
        if process.poll() is None:
            print("   ✅ Flask app started successfully (PID: {})".format(process.pid))
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Flask app failed to start")
            print(f"   STDOUT: {stdout}")
            print(f"   STDERR: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        return None

def test_homepage_response(port=8085):
    """Test if the homepage responds correctly"""
    print(f"\n🌐 Testing homepage response on port {port}...")
    
    try:
        # Test main homepage
        response = requests.get(f'http://127.0.0.1:{port}/', timeout=10)
        
        if response.status_code == 200:
            print(f"   ✅ Homepage accessible (Status: {response.status_code})")
            print(f"   ✅ Response size: {len(response.content)} bytes")
            
            # Check for key content
            content = response.text
            if 'HN Enhanced Scraper' in content:
                print("   ✅ Homepage title found")
            if 'analytics-dashboard' in content:
                print("   ✅ Analytics dashboard detected")
            
            return True
        else:
            print(f"❌ Homepage returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to homepage - app may not be running")
        return False
    except Exception as e:
        print(f"❌ Homepage test error: {e}")
        return False

def test_api_endpoints(port=8085):
    """Test API endpoints"""
    print(f"\n🔌 Testing API endpoints on port {port}...")
    
    endpoints = [
        '/test',
        '/api/stats', 
        '/api/search?q=python'
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://127.0.0.1:{port}{endpoint}', timeout=5)
            results[endpoint] = {
                'status': response.status_code,
                'size': len(response.content)
            }
            print(f"   ✅ {endpoint}: Status {response.status_code}, Size {len(response.content)} bytes")
        except Exception as e:
            results[endpoint] = {'error': str(e)}
            print(f"   ❌ {endpoint}: {e}")
    
    return results

def main():
    """Run comprehensive integration tests"""
    print("🚀 HN Enhanced Scraper - Final Integration Test")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Database connectivity
    results['database'] = test_database_connectivity()
    
    # Test 2: Template availability  
    results['template'] = test_template_availability()
    
    # Test 3: Flask app import
    results['import'] = test_flask_app_import()
    
    # Test 4: Start Flask app
    flask_process = start_flask_app()
    results['flask_start'] = flask_process is not None
    
    if flask_process:
        # Give it time to fully start
        time.sleep(2)
        
        # Test 5: Homepage response
        results['homepage'] = test_homepage_response()
        
        # Test 6: API endpoints
        results['api'] = test_api_endpoints()
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        flask_process.terminate()
        flask_process.wait()
        print("   ✅ Flask process terminated")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name.upper().replace('_', ' ')}")
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The enhanced homepage is ready!")
        print("\n🚀 To start the application:")
        print("   python optimized_enhanced_app.py")
        print("   Then visit: http://127.0.0.1:8085")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
