#!/usr/bin/env python3
"""
Direct test of the enhanced homepage functionality
"""
import sqlite3
import os
import sys
from flask import Flask, render_template, jsonify
import json

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'enhanced_hn_articles.db')

def test_database():
    """Test database connectivity and data availability"""
    print("🔍 Testing Database Connection")
    print("=" * 40)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Found tables: {tables}")
        
        # Check data counts
        if 'article_analyses' in tables:
            cursor.execute('SELECT COUNT(*) FROM article_analyses')
            articles = cursor.fetchone()[0]
            print(f"✅ Articles with analysis: {articles}")
        
        if 'comment_analyses' in tables:
            cursor.execute('SELECT COUNT(*) FROM comment_analyses')
            comments = cursor.fetchone()[0]
            print(f"✅ Analyzed comments: {comments}")
        
        if 'enhanced_comments' in tables:
            cursor.execute('SELECT COUNT(*) FROM enhanced_comments')
            enhanced = cursor.fetchone()[0]
            print(f"✅ Enhanced comments: {enhanced}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def get_sample_data():
    """Get sample data for testing the homepage"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute('SELECT COUNT(*) FROM article_analyses')
        total_articles = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM comment_analyses')
        analyzed_comments = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM enhanced_comments')
        total_comments = cursor.fetchone()[0]
        
        # Get average quality
        cursor.execute('SELECT AVG(discussion_quality_score) FROM article_analyses WHERE discussion_quality_score IS NOT NULL')
        avg_quality = cursor.fetchone()[0] or 0
        
        # Get top domains
        cursor.execute('SELECT domain, COUNT(*) as count FROM article_analyses GROUP BY domain ORDER BY count DESC LIMIT 5')
        top_domains = [{'domain': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Get sample articles
        cursor.execute('''
            SELECT hn_id, title, url, domain, summary, key_insights,
                   discussion_quality_score, sentiment_analysis, controversy_level
            FROM article_analyses
            ORDER BY discussion_quality_score DESC
            LIMIT 10
        ''')
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'hn_id': row[0],
                'title': row[1],
                'url': row[2],
                'domain': row[3],
                'summary': row[4] or 'No summary available',
                'key_insights': row[5] or 'No insights available',
                'quality_score': row[6] or 0,
                'sentiment': row[7] or 'neutral',
                'controversy': row[8] or 'low'
            })
        
        conn.close()
        
        return {
            'stats': {
                'total_articles': total_articles,
                'analyzed_comments': analyzed_comments,
                'total_comments': total_comments,
                'avg_discussion_quality': round(avg_quality, 2),
                'top_domains': top_domains
            },
            'articles': articles
        }
        
    except Exception as e:
        print(f"Error getting sample data: {e}")
        return None

def test_homepage_render():
    """Test if the homepage template can be rendered with sample data"""
    print("\n🎨 Testing Homepage Template Rendering")
    print("=" * 40)
    
    try:
        app = Flask(__name__, template_folder='templates')
        
        with app.app_context():
            sample_data = get_sample_data()
            if not sample_data:
                print("❌ Could not get sample data")
                return False
            
            # Try to render the template
            rendered = render_template('index.html', 
                                     articles=sample_data['articles'],
                                     stats=sample_data['stats'])
            
            print(f"✅ Template rendered successfully ({len(rendered)} characters)")
            print(f"✅ Found {len(sample_data['articles'])} articles for display")
            print(f"✅ Stats: {sample_data['stats']['total_articles']} articles, {sample_data['stats']['analyzed_comments']} analyzed comments")
            
            return True
            
    except Exception as e:
        print(f"❌ Template rendering error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_test_server():
    """Create a simple test server for the enhanced homepage"""
    print("\n🚀 Creating Test Server")
    print("=" * 25)
    
    app = Flask(__name__, template_folder='templates')
    app.secret_key = 'test-key'
    
    @app.route('/')
    def index():
        sample_data = get_sample_data()
        if not sample_data:
            return "Database error - could not load data", 500
        
        return render_template('index.html',
                             articles=sample_data['articles'],
                             stats=sample_data['stats'],
                             search_query='',
                             selected_domain='all')
    
    @app.route('/api/stats')
    def api_stats():
        sample_data = get_sample_data()
        if not sample_data:
            return jsonify({'error': 'Database error'}), 500
        return jsonify(sample_data['stats'])
    
    print("✅ Test server created")
    print("🌐 Starting server on http://localhost:5001")
    
    try:
        app.run(host='0.0.0.0', port=5001, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    print("🧪 Enhanced Homepage Direct Test")
    print("=" * 50)
    
    # Test database
    db_ok = test_database()
    
    if not db_ok:
        print("\n❌ Database test failed - cannot proceed")
        sys.exit(1)
    
    # Test template rendering
    template_ok = test_homepage_render()
    
    if not template_ok:
        print("\n❌ Template test failed - check template syntax")
        sys.exit(1)
    
    print("\n✅ All tests passed!")
    print("\n🚀 Starting test server...")
    create_test_server()
