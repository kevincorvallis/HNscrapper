#!/usr/bin/env python3
"""
Simplified Flask app to test the enhanced homepage without potential hanging issues
"""
import json
import os
import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Optional

import tldextract
from flask import Flask, jsonify, render_template, request

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, template_folder='/Users/kevin/Downloads/HNscrapper/templates')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'enhanced_hn_articles.db')

class SimpleDatabaseManager:
    """Simplified database manager for testing."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_connection(self):
        """Get database connection with timeout."""
        return sqlite3.connect(self.db_path, timeout=10)
    
    def get_basic_articles(self, limit=20) -> List[Dict]:
        """Get basic articles without complex joins."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT hn_id, title, url, domain, summary, key_insights,
                       main_themes, sentiment_analysis, discussion_quality_score,
                       controversy_level, generated_at
                FROM article_analyses
                ORDER BY discussion_quality_score DESC
                LIMIT ?
            ''', (limit,))
            
            articles = []
            for row in cursor.fetchall():
                article = {
                    'hn_id': row[0],
                    'title': row[1],
                    'url': row[2],
                    'domain': row[3],
                    'summary': row[4],
                    'key_insights': row[5],
                    'main_themes': row[6],
                    'sentiment_analysis': row[7],
                    'discussion_quality_score': row[8] or 0,
                    'controversy_level': row[9],
                    'generated_at': row[10],
                    'total_comments': 0,  # Will be filled separately if needed
                    'analyzed_comments': 0
                }
                articles.append(article)
            
            conn.close()
            return articles
            
        except Exception as e:
            print(f"Error getting articles: {e}")
            return []
    
    def get_basic_stats(self) -> Dict:
        """Get basic statistics without complex queries."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Basic counts
            cursor.execute('SELECT COUNT(*) FROM article_analyses')
            total_articles = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM comment_analyses')
            analyzed_comments = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM enhanced_comments')
            total_comments = cursor.fetchone()[0]
            
            # Average quality
            cursor.execute('SELECT AVG(discussion_quality_score) FROM article_analyses WHERE discussion_quality_score IS NOT NULL')
            avg_quality = cursor.fetchone()[0] or 0
            
            # Top domains (simple)
            cursor.execute('SELECT domain, COUNT(*) as count FROM article_analyses GROUP BY domain ORDER BY count DESC LIMIT 5')
            top_domains = [{'domain': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            # Sentiment distribution
            cursor.execute('SELECT sentiment_analysis, COUNT(*) FROM article_analyses GROUP BY sentiment_analysis')
            sentiment_dist = {row[0] or 'neutral': row[1] for row in cursor.fetchall()}
            
            # Controversy distribution
            cursor.execute('SELECT controversy_level, COUNT(*) FROM article_analyses GROUP BY controversy_level')
            controversy_dist = {row[0] or 'low': row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                'total_articles': total_articles,
                'total_comments': total_comments,
                'analyzed_comments': analyzed_comments,
                'avg_discussion_quality': round(avg_quality, 2),
                'top_domains': top_domains,
                'sentiment_distribution': sentiment_dist,
                'controversy_distribution': controversy_dist
            }
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                'total_articles': 0,
                'total_comments': 0,
                'analyzed_comments': 0,
                'avg_discussion_quality': 0,
                'top_domains': [],
                'sentiment_distribution': {},
                'controversy_distribution': {}
            }

# Initialize database manager
db_manager = SimpleDatabaseManager(DB_PATH)

@app.route('/')
def index():
    """Simplified enhanced homepage."""
    try:
        # Get filter parameters
        search_query = request.args.get('search', '')
        domain_filter = request.args.get('domain', 'all')
        sort_by = request.args.get('sort', 'quality')
        view_mode = request.args.get('view', 'cards')
        
        # Get articles
        articles = db_manager.get_basic_articles(50)
        
        # Apply domain filter
        if domain_filter and domain_filter != 'all':
            articles = [a for a in articles if a.get('domain') == domain_filter]
        
        # Apply search filter
        if search_query:
            search_lower = search_query.lower()
            articles = [a for a in articles if (
                search_lower in (a.get('title') or '').lower() or
                search_lower in (a.get('summary') or '').lower()
            )]
        
        # Sort articles
        if sort_by == 'quality':
            articles.sort(key=lambda x: x.get('discussion_quality_score', 0), reverse=True)
        elif sort_by == 'recent':
            articles.sort(key=lambda x: x.get('hn_id', '0'), reverse=True)
        elif sort_by == 'controversial':
            articles.sort(key=lambda x: (x.get('controversy_level') == 'high', x.get('discussion_quality_score', 0)), reverse=True)
        
        # Get statistics
        stats = db_manager.get_basic_stats()
        
        # Get available domains
        domains = list(set(a.get('domain', '') for a in db_manager.get_basic_articles(200) if a.get('domain')))
        domains.sort()
        
        return render_template('index.html',
                             articles=articles[:30],  # Limit display
                             domains=domains[:20],  # Limit domains
                             search_query=search_query,
                             domain_filter=domain_filter,
                             sort_by=sort_by,
                             view_mode=view_mode,
                             stats=stats)
                             
    except Exception as e:
        print(f"Homepage error: {e}")
        return f"<h1>Error loading homepage</h1><p>{str(e)}</p><p>Check server logs for details.</p>", 500

@app.route('/api/analytics/real-time')
def api_real_time_analytics():
    """Simplified real-time analytics."""
    try:
        stats = db_manager.get_basic_stats()
        
        return jsonify({
            'success': True,
            'data': {
                'metrics': {
                    'total_articles': stats.get('total_articles', 0),
                    'total_comments': stats.get('total_comments', 0),
                    'analyzed_comments': stats.get('analyzed_comments', 0),
                    'avg_quality': stats.get('avg_discussion_quality', 0)
                },
                'charts': {
                    'sentiment_distribution': stats.get('sentiment_distribution', {}),
                    'controversy_distribution': stats.get('controversy_distribution', {})
                },
                'top_domains': stats.get('top_domains', [])
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/test')
def api_test():
    """Simple test endpoint."""
    return jsonify({
        'success': True,
        'message': 'API is working',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Simplified Enhanced Homepage")
    print(f"Database: {DB_PATH}")
    print(f"Templates: {app.template_folder}")
    
    # Test database connection
    try:
        stats = db_manager.get_basic_stats()
        articles = db_manager.get_basic_articles(5)
        print(f"✅ Database working: {stats['total_articles']} articles, {len(articles)} loaded")
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    port = int(os.environ.get('PORT', 8084))
    print(f"Available at: http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
