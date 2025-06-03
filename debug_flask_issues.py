#!/usr/bin/env python3
"""
Simple debug test for the Flask app to identify hanging issues
"""
import os
import sys
import sqlite3

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_database_connection():
    """Test if database connection is working properly."""
    print("🔍 Testing Database Connection")
    print("=" * 30)
    
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'enhanced_hn_articles.db')
    print(f"Database path: {db_path}")
    
    try:
        # Test basic connection
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM article_analyses")
        count = cursor.fetchone()[0]
        print(f"✅ Article analyses count: {count}")
        
        # Test more complex query (similar to what the app uses)
        cursor.execute('''
            SELECT aa.hn_id, aa.title, aa.url, aa.domain, aa.summary, 
                   aa.key_insights, aa.main_themes, aa.sentiment_analysis,
                   aa.discussion_quality_score, aa.controversy_level, aa.generated_at,
                   COUNT(DISTINCT ca.comment_id) as analyzed_comments,
                   COUNT(DISTINCT ec.id) as total_comments,
                   AVG(ca.quality_score) as avg_comment_quality
            FROM article_analyses aa
            LEFT JOIN comment_analyses ca ON aa.hn_id = ca.hn_id
            LEFT JOIN enhanced_comments ec ON aa.hn_id = ec.article_hn_id
            GROUP BY aa.hn_id
            ORDER BY aa.discussion_quality_score DESC, aa.generated_at DESC
            LIMIT 5
        ''')
        
        articles = cursor.fetchall()
        print(f"✅ Complex query returned {len(articles)} articles")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False

def test_flask_imports():
    """Test if all Flask imports are working."""
    print("\n🔍 Testing Flask Imports")
    print("=" * 25)
    
    try:
        from src.web.app import DatabaseManager
        print("✅ DatabaseManager import successful")
        
        # Test creating DatabaseManager
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'enhanced_hn_articles.db')
        db_manager = DatabaseManager(db_path)
        print("✅ DatabaseManager creation successful")
        
        # Test getting stats (this might be hanging)
        print("⏳ Testing get_stats_with_analysis...")
        stats = db_manager.get_stats_with_analysis()
        print(f"✅ Stats retrieved: {len(stats)} keys")
        
        return True
        
    except Exception as e:
        print(f"❌ Import/Manager error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_flask_app():
    """Test a minimal Flask app to see if basic routing works."""
    print("\n🔍 Testing Simple Flask App")
    print("=" * 30)
    
    try:
        from flask import Flask
        
        app = Flask(__name__)
        
        @app.route('/test')
        def test_route():
            return "Hello World"
        
        print("✅ Simple Flask app created successfully")
        
        # Test if we can create a test client
        with app.test_client() as client:
            response = client.get('/test')
            if response.status_code == 200:
                print("✅ Test route working")
                return True
            else:
                print(f"❌ Test route failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Simple Flask error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Flask App Debug Test")
    print("=" * 40)
    
    # Run tests in order
    db_ok = test_database_connection()
    imports_ok = test_flask_imports()
    flask_ok = test_simple_flask_app()
    
    print(f"\n📋 Debug Results")
    print("=" * 20)
    print(f"Database: {'✅' if db_ok else '❌'}")
    print(f"Imports: {'✅' if imports_ok else '❌'}")
    print(f"Simple Flask: {'✅' if flask_ok else '❌'}")
    
    if all([db_ok, imports_ok, flask_ok]):
        print("\n✅ All basic tests passed. The hanging issue is likely in the main route logic.")
        print("💡 Try starting the Flask app with simpler routes to isolate the issue.")
    else:
        print("\n❌ Some basic tests failed. Fix these issues first.")
