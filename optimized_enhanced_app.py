#!/usr/bin/env python3
"""
Optimized Flask app for the enhanced homepage with better error handling and performance
"""
import json
import os
import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Optional

import tldextract
from flask import Flask, jsonify, render_template, request, redirect

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'enhanced_hn_articles.db')

class OptimizedDatabaseManager:
    """Optimized database manager with connection pooling and timeouts."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.timeout = 10  # 10 second timeout
    
    def get_connection(self):
        """Get database connection with timeout and optimizations."""
        conn = sqlite3.connect(self.db_path, timeout=self.timeout)
        conn.execute('PRAGMA journal_mode=WAL')  # Improve concurrent access
        conn.execute('PRAGMA synchronous=NORMAL')  # Balance safety vs speed
        conn.execute('PRAGMA cache_size=10000')  # Increase cache
        return conn
    
    def get_articles_optimized(self, limit=30) -> List[Dict]:
        """Get articles with optimized query and minimal joins."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Simplified query without complex joins
            cursor.execute('''
                SELECT hn_id, title, url, domain, summary, key_insights,
                       main_themes, sentiment_analysis, discussion_quality_score,
                       controversy_level, generated_at
                FROM article_analyses
                ORDER BY discussion_quality_score DESC, generated_at DESC
                LIMIT ?
            ''', (limit,))
            
            articles = []
            for row in cursor.fetchall():
                article = {
                    'hn_id': row[0],
                    'title': row[1] or 'Untitled',
                    'url': row[2] or '',
                    'domain': row[3] or 'unknown',
                    'summary': row[4] or 'No summary available',
                    'key_insights': row[5] or 'No insights available',
                    'main_themes': row[6] or 'general',
                    'sentiment_analysis': row[7] or 'neutral',
                    'discussion_quality_score': row[8] or 0,
                    'controversy_level': row[9] or 'low',
                    'generated_at': row[10] or datetime.now().isoformat()
                }
                
                # Get comment counts in separate query to avoid hanging joins
                try:
                    cursor.execute('SELECT COUNT(*) FROM comment_analyses WHERE hn_id = ?', (row[0],))
                    article['analyzed_comments'] = cursor.fetchone()[0] or 0
                    
                    cursor.execute('SELECT COUNT(*) FROM enhanced_comments WHERE article_hn_id = ?', (row[0],))
                    article['total_comments'] = cursor.fetchone()[0] or 0
                except:
                    article['analyzed_comments'] = 0
                    article['total_comments'] = 0
                
                articles.append(article)
            
            conn.close()
            return articles
            
        except Exception as e:
            print(f"Error getting articles: {e}")
            return []
    
    def get_stats_optimized(self) -> Dict:
        """Get basic statistics with individual queries to avoid locks."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Get counts with individual queries
            try:
                cursor.execute('SELECT COUNT(*) FROM article_analyses')
                stats['total_articles'] = cursor.fetchone()[0]
            except:
                stats['total_articles'] = 0
            
            try:
                cursor.execute('SELECT COUNT(*) FROM comment_analyses')
                stats['analyzed_comments'] = cursor.fetchone()[0]
            except:
                stats['analyzed_comments'] = 0
            
            try:
                cursor.execute('SELECT COUNT(*) FROM enhanced_comments')
                stats['total_comments'] = cursor.fetchone()[0]
            except:
                stats['total_comments'] = 0
            
            # Get averages
            try:
                cursor.execute('SELECT AVG(discussion_quality_score) FROM article_analyses WHERE discussion_quality_score IS NOT NULL')
                result = cursor.fetchone()[0]
                stats['avg_discussion_quality'] = round(result, 2) if result else 0
            except:
                stats['avg_discussion_quality'] = 0
            
            # Get top domains (limit to prevent hanging)
            try:
                cursor.execute('SELECT domain, COUNT(*) as count FROM article_analyses GROUP BY domain ORDER BY count DESC LIMIT 5')
                stats['top_domains'] = [{'domain': row[0], 'count': row[1]} for row in cursor.fetchall()]
            except:
                stats['top_domains'] = []
            
            # Get sentiment distribution (simplified)
            try:
                cursor.execute('SELECT sentiment_analysis, COUNT(*) FROM article_analyses GROUP BY sentiment_analysis LIMIT 10')
                sentiment_dist = {}
                for row in cursor.fetchall():
                    sentiment_dist[row[0] or 'neutral'] = row[1]
                stats['sentiment_distribution'] = sentiment_dist
            except:
                stats['sentiment_distribution'] = {'neutral': stats['total_articles']}
            
            conn.close()
            return stats
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                'total_articles': 0,
                'analyzed_comments': 0,
                'total_comments': 0,
                'avg_discussion_quality': 0,
                'top_domains': [],
                'sentiment_distribution': {'neutral': 0}
            }
    
    def search_articles(self, query: str, domain: str = None, limit=20) -> List[Dict]:
        """Search articles with simple query to avoid complex joins."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            search_term = f'%{query}%'
            
            if domain and domain != 'all':
                cursor.execute('''
                    SELECT hn_id, title, url, domain, summary, key_insights,
                           discussion_quality_score, sentiment_analysis, controversy_level
                    FROM article_analyses
                    WHERE (title LIKE ? OR summary LIKE ?) AND domain = ?
                    ORDER BY discussion_quality_score DESC
                    LIMIT ?
                ''', (search_term, search_term, domain, limit))
            else:
                cursor.execute('''
                    SELECT hn_id, title, url, domain, summary, key_insights,
                           discussion_quality_score, sentiment_analysis, controversy_level
                    FROM article_analyses
                    WHERE title LIKE ? OR summary LIKE ?
                    ORDER BY discussion_quality_score DESC
                    LIMIT ?
                ''', (search_term, search_term, limit))
            
            results = []
            for row in cursor.fetchall():
                article = {
                    'hn_id': row[0],
                    'title': row[1] or 'Untitled',
                    'url': row[2] or '',
                    'domain': row[3] or 'unknown',
                    'summary': row[4] or 'No summary available',
                    'key_insights': row[5] or 'No insights available',
                    'discussion_quality_score': row[6] or 0,
                    'sentiment_analysis': row[7] or 'neutral',
                    'controversy_level': row[8] or 'low'
                }
                results.append(article)
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error searching articles: {e}")
            return []

# Initialize optimized database manager
db_manager = OptimizedDatabaseManager(DB_PATH)

@app.route('/')
def index():
    """Optimized enhanced homepage with better error handling."""
    try:
        # Get filter parameters
        search_query = request.args.get('search', '').strip()
        domain_filter = request.args.get('domain', 'all')
        sort_by = request.args.get('sort', 'quality')
        view_mode = request.args.get('view', 'cards')
        
        print(f"Homepage request: search='{search_query}', domain='{domain_filter}', sort='{sort_by}'")
        
        # Get articles
        if search_query:
            articles = db_manager.search_articles(search_query, domain_filter, 30)
            print(f"Search returned {len(articles)} articles")
        else:
            articles = db_manager.get_articles_optimized(30)
            print(f"Loaded {len(articles)} articles")
            
            # Apply domain filter if specified
            if domain_filter and domain_filter != 'all':
                articles = [a for a in articles if a.get('domain') == domain_filter]
                print(f"Filtered to {len(articles)} articles for domain '{domain_filter}'")
        
        # Sort articles
        if sort_by == 'quality':
            articles.sort(key=lambda x: x.get('discussion_quality_score', 0), reverse=True)
        elif sort_by == 'recent':
            articles.sort(key=lambda x: x.get('hn_id', '0'), reverse=True)
        elif sort_by == 'controversial':
            articles.sort(key=lambda x: (x.get('controversy_level') == 'high', x.get('discussion_quality_score', 0)), reverse=True)
        
        # Get statistics
        stats = db_manager.get_stats_optimized()
        print(f"Stats: {stats['total_articles']} articles, {stats['analyzed_comments']} analyzed comments")
        
        # Get available domains
        available_domains = []
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT domain FROM article_analyses WHERE domain IS NOT NULL ORDER BY domain LIMIT 20')
            available_domains = [row[0] for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print(f"Error getting domains: {e}")
            available_domains = ['github.com', 'ycombinator.com', 'techcrunch.com']
        
        # Render template
        return render_template('index.html',
                             articles=articles,
                             domains=available_domains,
                             search_query=search_query,
                             domain_filter=domain_filter,
                             sort_by=sort_by,
                             view_mode=view_mode,
                             stats=stats,
                             curator_available=False,  # Simplified for testing
                             analyzer_available=False)  # Simplified for testing
        
    except Exception as e:
        print(f"Homepage error: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback error page
        return f"""
        <h1>HN Enhanced Scraper</h1>
        <p>Error loading enhanced homepage: {str(e)}</p>
        <p>Please check the server logs for details.</p>
        <p><a href="/test">Try test page</a></p>
        """, 500

@app.route('/test')
def test_page():
    """Simple test page to verify the application is working."""
    try:
        stats = db_manager.get_stats_optimized()
        articles = db_manager.get_articles_optimized(5)
        
        return f"""
        <h1>HN Enhanced Scraper - Test Page</h1>
        <h2>Database Status</h2>
        <ul>
            <li>Total Articles: {stats['total_articles']}</li>
            <li>Analyzed Comments: {stats['analyzed_comments']}</li>
            <li>Total Comments: {stats['total_comments']}</li>
            <li>Avg Quality: {stats['avg_discussion_quality']}</li>
        </ul>
        
        <h2>Sample Articles ({len(articles)})</h2>
        <ul>
        """ + "".join([f"<li><strong>{article['title']}</strong> - {article['domain']} (Quality: {article['discussion_quality_score']})</li>" for article in articles[:5]]) + """
        </ul>
        
        <p><a href="/">Back to Enhanced Homepage</a></p>
        """
        
    except Exception as e:
        return f"<h1>Test Error</h1><p>{str(e)}</p>"

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics."""
    try:
        stats = db_manager.get_stats_optimized()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles')
def api_articles():
    """API endpoint for articles."""
    try:
        limit = int(request.args.get('limit', 20))
        articles = db_manager.get_articles_optimized(limit)
        return jsonify(articles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def api_search():
    """API endpoint for search."""
    try:
        query = request.args.get('q', '')
        domain = request.args.get('domain', 'all')
        limit = int(request.args.get('limit', 20))
        
        if not query:
            return jsonify([])
        
        results = db_manager.search_articles(query, domain, limit)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Optimized Enhanced Homepage")
    print(f"Database: {DB_PATH}")
    print(f"Templates: {app.template_folder}")
    
    # Test database connection
    try:
        stats = db_manager.get_stats_optimized()
        print(f"✅ Database working: {stats['total_articles']} articles")
        
        # Test loading a few articles
        articles = db_manager.get_articles_optimized(3)
        print(f"✅ Sample articles loaded: {len(articles)}")
        
        if articles:
            print(f"   Sample: '{articles[0]['title'][:50]}...' - {articles[0]['domain']}")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("Starting anyway with error handling...")
    
    port = int(os.environ.get('PORT', 8085))
    print(f"🌐 Available at: http://127.0.0.1:{port}")
    print("📊 Test page: http://127.0.0.1:{port}/test")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
