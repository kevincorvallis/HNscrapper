#!/usr/bin/env python3
"""
Comprehensive test script to verify the complete database integration
and all functionality of the HN Scraper application.
"""

import requests
import json
import time
import subprocess
import signal
import os
import sys
import socket
from typing import Dict, List

class ComprehensiveIntegrationTest:
    def __init__(self):
        # Find a free port
        self.port = self._find_free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.app_process = None
        self.test_results = {}
    
    def _find_free_port(self):
        """Find a free port to use for testing."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
        
    def start_application(self):
        """Start the Flask application."""
        print(f"🚀 Starting Flask application on port {self.port}...")
        try:
            # Set environment variable for port
            env = os.environ.copy()
            env['PORT'] = str(self.port)
            
            self.app_process = subprocess.Popen(
                [sys.executable, "src/web/app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            # Wait for application to start
            time.sleep(5)
            
            # Check if process is still running
            if self.app_process.poll() is not None:
                stdout, stderr = self.app_process.communicate()
                print(f"❌ Application exited early")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False
            
            # Test if application is responding
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200 or response.status_code == 302:
                print("✅ Application started successfully")
                return True
            else:
                print(f"❌ Application not responding: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting application: {e}")
            return False
    
    def stop_application(self):
        """Stop the Flask application."""
        if self.app_process:
            print("🛑 Stopping Flask application...")
            self.app_process.terminate()
            self.app_process.wait()
            print("✅ Application stopped")
    
    def test_comprehensive_stats(self) -> bool:
        """Test comprehensive statistics API."""
        print("\n📊 Testing comprehensive statistics API...")
        try:
            response = requests.get(f"{self.base_url}/api/stats", timeout=10)
            if response.status_code != 200:
                print(f"❌ Stats API failed: {response.status_code}")
                return False
            
            data = response.json()
            required_fields = [
                'total_articles', 'analyzed_comments', 'total_comments',
                'avg_discussion_quality', 'avg_comment_quality', 
                'sentiment_distribution', 'controversy_distribution',
                'top_domains', 'insightful_comments', 'controversial_comments'
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"❌ Missing fields in stats: {missing_fields}")
                return False
            
            print(f"✅ Stats API working - {data['total_articles']} articles, {data['analyzed_comments']} analyzed comments")
            self.test_results['stats'] = data
            return True
            
        except Exception as e:
            print(f"❌ Stats API error: {e}")
            return False
    
    def test_curated_comments(self) -> bool:
        """Test curated comments API."""
        print("\n💬 Testing curated comments API...")
        try:
            response = requests.get(f"{self.base_url}/api/comments/curated?limit=5", timeout=10)
            if response.status_code != 200:
                print(f"❌ Curated comments API failed: {response.status_code}")
                return False
            
            data = response.json()
            if not isinstance(data, list):
                print("❌ Curated comments should return a list")
                return False
            
            if len(data) == 0:
                print("⚠️  No curated comments found")
                return True
            
            # Check first comment structure
            comment = data[0]
            required_fields = ['id', 'article_hn_id', 'author', 'comment_text', 'quality_score']
            missing_fields = [field for field in required_fields if field not in comment]
            if missing_fields:
                print(f"❌ Missing fields in curated comment: {missing_fields}")
                return False
            
            print(f"✅ Curated comments API working - {len(data)} comments retrieved")
            self.test_results['curated_comments'] = len(data)
            return True
            
        except Exception as e:
            print(f"❌ Curated comments API error: {e}")
            return False
    
    def test_comprehensive_search(self) -> bool:
        """Test comprehensive search API."""
        print("\n🔍 Testing comprehensive search API...")
        try:
            # Test AI search
            response = requests.get(f"{self.base_url}/api/search/comprehensive?q=AI", timeout=10)
            if response.status_code != 200:
                print(f"❌ Search API failed: {response.status_code}")
                return False
            
            data = response.json()
            if not isinstance(data, list):
                print("❌ Search should return a list")
                return False
            
            if len(data) == 0:
                print("⚠️  No search results found for 'AI'")
                return True
            
            # Check first result structure
            result = data[0]
            required_fields = ['hn_id', 'title', 'domain', 'summary', 'discussion_quality_score']
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                print(f"❌ Missing fields in search result: {missing_fields}")
                return False
            
            print(f"✅ Search API working - {len(data)} results for 'AI'")
            self.test_results['search_results'] = len(data)
            return True
            
        except Exception as e:
            print(f"❌ Search API error: {e}")
            return False
    
    def test_trending_insights(self) -> bool:
        """Test trending insights API."""
        print("\n📈 Testing trending insights API...")
        try:
            response = requests.get(f"{self.base_url}/api/insights/trending", timeout=10)
            if response.status_code != 200:
                print(f"❌ Trending insights API failed: {response.status_code}")
                return False
            
            data = response.json()
            if 'trending_articles' not in data or 'top_insights' not in data:
                print("❌ Trending insights missing required sections")
                return False
            
            trending_count = len(data['trending_articles'])
            insights_count = len(data['top_insights'])
            
            print(f"✅ Trending insights API working - {trending_count} trending articles, {insights_count} top insights")
            self.test_results['trending'] = {'articles': trending_count, 'insights': insights_count}
            return True
            
        except Exception as e:
            print(f"❌ Trending insights API error: {e}")
            return False
    
    def test_article_detail(self) -> bool:
        """Test comprehensive article detail API."""
        print("\n📄 Testing article detail API...")
        try:
            # Get a sample article ID from stats
            stats_response = requests.get(f"{self.base_url}/api/stats", timeout=5)
            if stats_response.status_code != 200:
                print("❌ Cannot get stats to find article ID")
                return False
            
            # Try with the fractal article we know exists
            article_id = "44063248"
            response = requests.get(f"{self.base_url}/api/article/{article_id}", timeout=10)
            if response.status_code != 200:
                print(f"❌ Article detail API failed: {response.status_code}")
                return False
            
            data = response.json()
            required_fields = ['hn_id', 'title', 'domain', 'summary', 'analyzed_comments', 'enhanced_comments']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"❌ Missing fields in article detail: {missing_fields}")
                return False
            
            analyzed_count = len(data.get('analyzed_comments', []))
            enhanced_count = len(data.get('enhanced_comments', []))
            
            print(f"✅ Article detail API working - {analyzed_count} analyzed comments, {enhanced_count} enhanced comments")
            self.test_results['article_detail'] = {'analyzed': analyzed_count, 'enhanced': enhanced_count}
            return True
            
        except Exception as e:
            print(f"❌ Article detail API error: {e}")
            return False
    
    def test_analysis_summary(self) -> bool:
        """Test analysis summary API."""
        print("\n📋 Testing analysis summary API...")
        try:
            response = requests.get(f"{self.base_url}/api/analysis/summary", timeout=10)
            if response.status_code != 200:
                print(f"❌ Analysis summary API failed: {response.status_code}")
                return False
            
            data = response.json()
            required_sections = ['articles', 'comments', 'sources']
            missing_sections = [section for section in required_sections if section not in data]
            if missing_sections:
                print(f"❌ Missing sections in analysis summary: {missing_sections}")
                return False
            
            # Check articles section
            articles = data['articles']
            if 'total' not in articles or 'avg_quality' not in articles:
                print("❌ Articles section missing required fields")
                return False
            
            # Check comments section
            comments = data['comments']
            if 'total_analyzed' not in comments or 'insightful' not in comments:
                print("❌ Comments section missing required fields")
                return False
            
            print(f"✅ Analysis summary API working - {articles['total']} articles, {comments['total_analyzed']} analyzed comments")
            self.test_results['analysis_summary'] = data
            return True
            
        except Exception as e:
            print(f"❌ Analysis summary API error: {e}")
            return False
    
    def test_web_interface(self) -> bool:
        """Test main web interface."""
        print("\n🌐 Testing web interface...")
        try:
            # Test main page
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code not in [200, 302]:  # 302 for redirect
                print(f"❌ Main page failed: {response.status_code}")
                return False
            
            # Test classic view
            response = requests.get(f"{self.base_url}/classic", timeout=10)
            if response.status_code != 200:
                print(f"❌ Classic view failed: {response.status_code}")
                return False
            
            # Test article detail page
            response = requests.get(f"{self.base_url}/article/44063248", timeout=10)
            if response.status_code != 200:
                print(f"❌ Article detail page failed: {response.status_code}")
                return False
            
            print("✅ Web interface working - main page, classic view, and article detail accessible")
            return True
            
        except Exception as e:
            print(f"❌ Web interface error: {e}")
            return False
    
    def run_all_tests(self) -> Dict:
        """Run all tests and return results."""
        print("=" * 60)
        print("🧪 COMPREHENSIVE DATABASE INTEGRATION TEST")
        print("=" * 60)
        
        if not self.start_application():
            return {'success': False, 'error': 'Failed to start application'}
        
        try:
            tests = [
                ('comprehensive_stats', self.test_comprehensive_stats),
                ('curated_comments', self.test_curated_comments),
                ('comprehensive_search', self.test_comprehensive_search),
                ('trending_insights', self.test_trending_insights),
                ('article_detail', self.test_article_detail),
                ('analysis_summary', self.test_analysis_summary),
                ('web_interface', self.test_web_interface),
            ]
            
            results = {}
            passed = 0
            total = len(tests)
            
            for test_name, test_func in tests:
                if test_func():
                    results[test_name] = 'PASSED'
                    passed += 1
                else:
                    results[test_name] = 'FAILED'
            
            print("\n" + "=" * 60)
            print("📊 TEST RESULTS SUMMARY")
            print("=" * 60)
            
            for test_name, status in results.items():
                status_emoji = "✅" if status == 'PASSED' else "❌"
                print(f"{status_emoji} {test_name}: {status}")
            
            print(f"\n🎯 Overall: {passed}/{total} tests passed")
            
            if passed == total:
                print("🎉 ALL TESTS PASSED! Database integration is complete and functional.")
            else:
                print(f"⚠️  {total - passed} tests failed. Review the issues above.")
            
            return {
                'success': passed == total,
                'passed': passed,
                'total': total,
                'results': results,
                'test_data': self.test_results
            }
            
        finally:
            self.stop_application()

def main():
    """Run the comprehensive integration test."""
    tester = ComprehensiveIntegrationTest()
    results = tester.run_all_tests()
    
    # Save detailed results
    with open('comprehensive_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: comprehensive_test_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)

if __name__ == "__main__":
    main()
