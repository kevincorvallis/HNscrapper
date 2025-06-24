#!/usr/bin/env python3
"""
Main Flask API entry point for Vercel serverless deployment.
Simplified version of the HN scraper for serverless environment.
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

app = Flask(__name__, 
           template_folder='./templates',
           static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', 'vercel-production-key')

# Database path for Vercel (use in-memory or external DB)
DB_PATH = '/tmp/enhanced_hn_articles.db' if os.environ.get('VERCEL') else 'data/enhanced_hn_articles.db'

class DatabaseManager:
    """Simplified database manager for Vercel serverless environment."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database with sample data if needed."""
        if not os.path.exists(self.db_path):
            # Create basic tables for demo
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create basic tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS article_analyses (
                    hn_id TEXT PRIMARY KEY,
                    title TEXT,
                    url TEXT,
                    domain TEXT,
                    summary TEXT,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comment_analyses (
                    comment_id TEXT PRIMARY KEY,
                    content TEXT,
                    quality_score INTEGER,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert sample data
            cursor.execute('''
                INSERT OR IGNORE INTO article_analyses 
                (hn_id, title, url, domain, summary) VALUES 
                ('sample1', 'Sample HN Article', 'https://example.com', 'example.com', 'This is a sample article for demo purposes.')
            ''')
            
            conn.commit()
            conn.close()
    
    def get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def get_articles_with_analysis(self, limit: int = 50) -> List[Dict]:
        """Get articles with analysis data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT hn_id, title, url, domain, summary, generated_at
            FROM article_analyses
            ORDER BY generated_at DESC
            LIMIT ?
        ''', (limit,))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'hn_id': row[0],
                'title': row[1],
                'url': row[2],
                'domain': row[3],
                'summary': row[4],
                'generated_at': row[5]
            })
        
        conn.close()
        return articles
    
    def get_database_stats(self) -> Dict:
        """Get basic database statistics."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM article_analyses')
        total_articles = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM comment_analyses')
        total_comments = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_articles': total_articles,
            'total_comments': total_comments,
            'analyzed_comments': total_comments,
            'avg_comment_quality': 7.5,  # Demo value
            'domains': ['example.com', 'github.com', 'techcrunch.com']  # Demo values
        }

# Initialize database manager
db_manager = DatabaseManager(DB_PATH)

@app.route('/')
def home():
    """Main homepage with unified dashboard."""
    try:
        # Get basic stats
        stats = db_manager.get_database_stats()
        
        # Get articles
        articles = db_manager.get_articles_with_analysis(limit=20)
        
        # Get search parameters
        search_query = request.args.get('search', '')
        domain_filter = request.args.get('domain', 'all')
        view_mode = request.args.get('view', 'articles')
        
        return render_template('index.html',
                             articles=articles,
                             stats=stats,
                             search_query=search_query,
                             domain_filter=domain_filter,
                             view_mode=view_mode,
                             domains=stats['domains'],
                             curator_available=bool(os.environ.get('OPENAI_API_KEY')))
    
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/api/stats')
def api_stats():
    """Get database statistics."""
    try:
        stats = db_manager.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles')
def api_articles():
    """Get articles with optional filtering."""
    try:
        limit = request.args.get('limit', 50, type=int)
        search = request.args.get('search', '')
        
        articles = db_manager.get_articles_with_analysis(limit=limit)
        
        # Simple search filter
        if search:
            articles = [a for a in articles if search.lower() in a.get('title', '').lower()]
        
        return jsonify({
            'success': True,
            'articles': articles,
            'count': len(articles)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def api_search():
    """Search across articles and comments."""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({'results': [], 'count': 0})
        
        articles = db_manager.get_articles_with_analysis(limit=limit)
        
        # Filter articles by search query
        results = []
        for article in articles:
            if query.lower() in article.get('title', '').lower() or \
               query.lower() in article.get('summary', '').lower():
                results.append({
                    'type': 'article',
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'summary': article.get('summary', '')
                })
        
        return jsonify({
            'results': results[:limit],
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    try:
        stats = db_manager.get_database_stats()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'total_articles': stats.get('total_articles', 0),
            'environment': 'vercel' if os.environ.get('VERCEL') else 'local'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# Vercel requires the app to be named 'app'
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
