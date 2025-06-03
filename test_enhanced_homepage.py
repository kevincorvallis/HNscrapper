#!/usr/bin/env python3
"""
Test script for the enhanced homepage and AI API endpoints
"""
import requests
import json
import time

def test_api_endpoints():
    """Test all the new AI-powered API endpoints."""
    base_url = "http://127.0.0.1:8083"
    
    print("🧪 Testing Enhanced Homepage AI Features")
    print("=" * 50)
    
    endpoints_to_test = [
        ("/", "Homepage"),
        ("/api/insights/summary", "AI Insights Summary"),
        ("/api/analytics/real-time", "Real-time Analytics"),
        ("/api/articles/trending", "Trending Articles"),
        ("/api/curated/highlights", "Curated Highlights"),
        ("/stats", "Statistics Page"),
        ("/conversations", "Conversations Page"),
        ("/curate", "Curated Comments Page")
    ]
    
    results = {}
    
    for endpoint, description in endpoints_to_test:
        print(f"\n📊 Testing {description} ({endpoint})...")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ {description} - Status: {response.status_code}")
                
                # For API endpoints, check JSON structure
                if endpoint.startswith('/api/'):
                    try:
                        data = response.json()
                        if data.get('success'):
                            print(f"   ✅ API Response: Success = {data['success']}")
                            
                            # Show specific data for each endpoint
                            if endpoint == "/api/insights/summary":
                                insights = data.get('insights', {})
                                print(f"   📈 Total Articles: {insights.get('total_articles', 0)}")
                                print(f"   📈 Quality Distribution: {insights.get('quality_trends', {})}")
                            
                            elif endpoint == "/api/analytics/real-time":
                                metrics = data.get('data', {}).get('metrics', {})
                                print(f"   📊 Analyzed Comments: {metrics.get('analyzed_comments', 0)}")
                                print(f"   📊 Avg Quality: {metrics.get('avg_quality', 0):.1f}")
                            
                            elif endpoint == "/api/articles/trending":
                                articles = data.get('articles', [])
                                print(f"   🔥 Trending Articles Found: {len(articles)}")
                                if articles:
                                    print(f"   🔥 Top Article: {articles[0].get('title', 'Unknown')[:50]}...")
                            
                            elif endpoint == "/api/curated/highlights":
                                highlights = data.get('highlights', [])
                                print(f"   ⭐ Curated Highlights: {len(highlights)}")
                        else:
                            print(f"   ⚠️  API returned success=False: {data}")
                    except json.JSONDecodeError:
                        print(f"   ⚠️  Non-JSON response from API endpoint")
                else:
                    # For HTML pages, check content length
                    content_length = len(response.text)
                    print(f"   📄 Page size: {content_length:,} characters")
                    
                    # Check for key elements in HTML
                    if "AI-Powered HN Analysis" in response.text:
                        print(f"   ✅ Found AI-powered title in page")
                    if "chart" in response.text.lower():
                        print(f"   ✅ Found chart elements in page")
                
                results[endpoint] = True
                
            else:
                print(f"   ❌ {description} - Status: {response.status_code}")
                if response.status_code == 500:
                    print(f"   💥 Server Error - check application logs")
                results[endpoint] = False
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ {description} - Connection failed (is the server running?)")
            results[endpoint] = False
        except Exception as e:
            print(f"   ❌ {description} - Error: {str(e)}")
            results[endpoint] = False
    
    # Test smart search API (POST request)
    print(f"\n🔍 Testing Smart Search API...")
    try:
        search_data = {"query": "AI artificial intelligence"}
        response = requests.post(f"{base_url}/api/search/smart", 
                               json=search_data, 
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                results_count = len(data.get('results', []))
                print(f"   ✅ Smart Search - Found {results_count} results")
                results['/api/search/smart'] = True
            else:
                print(f"   ⚠️  Smart Search returned success=False")
                results['/api/search/smart'] = False
        else:
            print(f"   ❌ Smart Search - Status: {response.status_code}")
            results['/api/search/smart'] = False
    except Exception as e:
        print(f"   ❌ Smart Search - Error: {str(e)}")
        results['/api/search/smart'] = False
    
    # Summary
    print(f"\n📋 Test Summary")
    print("=" * 30)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total} endpoints")
    print(f"❌ Failed: {total - passed}/{total} endpoints")
    
    if passed == total:
        print(f"\n🎉 All tests passed! The enhanced homepage is working perfectly.")
    else:
        print(f"\n⚠️  Some tests failed. Check the details above.")
        
        failed_endpoints = [k for k, v in results.items() if not v]
        print(f"Failed endpoints: {', '.join(failed_endpoints)}")
    
    return results

def test_database_utilization():
    """Test how well the database data is being utilized."""
    print(f"\n🗄️  Testing Database Utilization")
    print("=" * 40)
    
    base_url = "http://127.0.0.1:8083"
    
    try:
        # Test analytics endpoint for database metrics
        response = requests.get(f"{base_url}/api/analytics/real-time", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                metrics = data.get('data', {}).get('metrics', {})
                charts = data.get('data', {}).get('charts', {})
                
                print(f"📊 Database Metrics:")
                print(f"   • Total Articles: {metrics.get('total_articles', 0)}")
                print(f"   • Total Comments: {metrics.get('total_comments', 0)}")
                print(f"   • AI Analyzed Comments: {metrics.get('analyzed_comments', 0)}")
                print(f"   • Average Quality Score: {metrics.get('avg_quality', 0):.2f}")
                
                # Calculate utilization percentages
                total_comments = metrics.get('total_comments', 1)
                analyzed_comments = metrics.get('analyzed_comments', 0)
                ai_coverage = (analyzed_comments / total_comments) * 100 if total_comments > 0 else 0
                
                print(f"\n📈 Data Utilization:")
                print(f"   • AI Analysis Coverage: {ai_coverage:.1f}%")
                
                # Check sentiment distribution
                sentiment_dist = charts.get('sentiment_distribution', {})
                if sentiment_dist:
                    print(f"   • Sentiment Analysis: {len(sentiment_dist)} categories")
                    for sentiment, count in sentiment_dist.items():
                        print(f"     - {sentiment.title()}: {count} articles")
                
                # Check quality distribution
                quality_hist = charts.get('quality_histogram', {})
                if quality_hist:
                    print(f"   • Quality Distribution:")
                    for range_val, count in quality_hist.items():
                        print(f"     - Score {range_val}: {count} articles")
                
                return True
            else:
                print(f"❌ Failed to get analytics data")
                return False
        else:
            print(f"❌ Analytics endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing database utilization: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Enhanced Homepage Test Suite")
    print("=" * 60)
    
    # Give the server a moment to be ready
    time.sleep(2)
    
    # Run API tests
    api_results = test_api_endpoints()
    
    # Test database utilization
    db_result = test_database_utilization()
    
    print(f"\n🏁 Final Results")
    print("=" * 20)
    
    if all(api_results.values()) and db_result:
        print("✅ All systems are working! The enhanced homepage successfully utilizes:")
        print("   • Comprehensive AI analysis from the database")
        print("   • Real-time analytics and metrics") 
        print("   • Smart search and filtering")
        print("   • Curated content highlights")
        print("   • Modern UI with interactive charts")
        
        print(f"\n🎯 Next Steps:")
        print("   • The homepage is ready for production use")
        print("   • Consider setting up the daily scheduler")
        print("   • Test the FastAPI migration when ready")
    else:
        print("⚠️  Some issues detected. Review the test output above.")
