#!/usr/bin/env python3
"""
FastAPI-based HN Enhanced Scraper API
Modern async API with better performance and automatic documentation
"""
import json
import os
import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path

import tldextract
from fastapi import FastAPI, HTTPException, Request, Query, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="HN Enhanced Scraper API",
    description="AI-powered Hacker News analysis and curation platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure templates
templates = Jinja2Templates(directory="templates")

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'enhanced_hn_articles.db')

# Pydantic models for request/response validation
class ArticleFilter(BaseModel):
    search: Optional[str] = ""
    domain: Optional[str] = "all"
    sort_by: Optional[str] = "quality"
    view_mode: Optional[str] = "cards"
    limit: Optional[int] = 30

class SearchRequest(BaseModel):
    q: str
    domain: Optional[str] = "all"
    limit: Optional[int] = 20

class StatsResponse(BaseModel):
    total_articles: int
    total_comments: int
    analyzed_comments: int
    avg_discussion_quality: float

class ArticleResponse(BaseModel):
    hn_id: str
    title: str
    url: str
    domain: str
    summary: Optional[str]
    discussion_quality_score: Optional[float]
    controversy_level: Optional[str]
    key_insights: Optional[str]
    main_themes: Optional[str]
    sentiment_analysis: Optional[str]

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
                ORDER BY discussion_quality_score DESC NULLS LAST
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
                    'controversy_level': row[9] or 'low',
                    'generated_at': row[10],
                    'total_comments': 0  # Will be populated if needed
                }
                articles.append(article)
            
            conn.close()
            return articles
            
        except Exception as e:
            print(f"Error getting articles: {e}")
            return []
    
    def get_enhanced_articles_safe(self, limit=30) -> List[Dict]:
        """Safe method to get enhanced articles with fallback."""
        try:
            # Try to get articles with enhanced data
            articles = self.get_articles_optimized(limit)
            if articles:
                return articles
            
            # Fallback to basic articles
            return self.get_basic_articles_fallback(limit)
            
        except Exception as e:
            print(f"Error in get_enhanced_articles_safe: {e}")
            return []
    
    def get_basic_articles_fallback(self, limit=30) -> List[Dict]:
        """Fallback method to get basic articles."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT hn_id, title, url, domain, points, num_comments
                FROM articles
                ORDER BY hn_id DESC
                LIMIT ?
            ''', (limit,))
            
            articles = []
            for row in cursor.fetchall():
                article = {
                    'hn_id': row[0],
                    'title': row[1],
                    'url': row[2],
                    'domain': row[3],
                    'points': row[4] or 0,
                    'num_comments': row[5] or 0,
                    'discussion_quality_score': 0,
                    'controversy_level': 'low',
                    'summary': 'Analysis pending...',
                    'key_insights': None,
                    'main_themes': None,
                    'sentiment_analysis': None
                }
                articles.append(article)
            
            conn.close()
            return articles
            
        except Exception as e:
            print(f"Error in fallback method: {e}")
            return []
    
    def get_basic_stats(self) -> Dict:
        """Get basic statistics safely."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Get article count
            cursor.execute("SELECT COUNT(*) FROM articles")
            stats['total_articles'] = cursor.fetchone()[0]
            
            # Get comment count
            cursor.execute("SELECT COUNT(*) FROM comments")
            stats['total_comments'] = cursor.fetchone()[0]
            
            # Get analyzed comment count
            cursor.execute("SELECT COUNT(*) FROM article_analyses")
            stats['analyzed_comments'] = cursor.fetchone()[0]
            
            # Get average quality score
            cursor.execute("SELECT AVG(discussion_quality_score) FROM article_analyses WHERE discussion_quality_score IS NOT NULL")
            avg_quality = cursor.fetchone()[0]
            stats['avg_discussion_quality'] = round(avg_quality or 0, 2)
            
            conn.close()
            return stats
            
        except Exception as e:
            print(f"Error getting basic stats: {e}")
            return {
                'total_articles': 0,
                'total_comments': 0,
                'analyzed_comments': 0,
                'avg_discussion_quality': 0.0
            }
    
    def get_stats_optimized(self) -> Dict:
        """Get optimized statistics with individual queries."""
        return self.get_basic_stats()
    
    def search_articles(self, query: str, domain: str = "all", limit: int = 20) -> List[Dict]:
        """Search articles with optimized query."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Build query
            base_query = '''
                SELECT hn_id, title, url, domain, summary, discussion_quality_score,
                       controversy_level, key_insights, main_themes
                FROM article_analyses
                WHERE (title LIKE ? OR summary LIKE ?)
            '''
            
            params = [f'%{query}%', f'%{query}%']
            
            if domain != "all":
                base_query += " AND domain = ?"
                params.append(domain)
            
            base_query += " ORDER BY discussion_quality_score DESC NULLS LAST LIMIT ?"
            params.append(limit)
            
            cursor.execute(base_query, params)
            
            articles = []
            for row in cursor.fetchall():
                article = {
                    'hn_id': row[0],
                    'title': row[1],
                    'url': row[2],
                    'domain': row[3],
                    'summary': row[4],
                    'discussion_quality_score': row[5] or 0,
                    'controversy_level': row[6] or 'low',
                    'key_insights': row[7],
                    'main_themes': row[8]
                }
                articles.append(article)
            
            conn.close()
            return articles
            
        except Exception as e:
            print(f"Error searching articles: {e}")
            return []

# Initialize database manager
db_manager = OptimizedDatabaseManager(DB_PATH)

# Dependency to get database manager
def get_db_manager() -> OptimizedDatabaseManager:
    return db_manager

# Routes

@app.get("/", response_class=HTMLResponse)
async def homepage(
    request: Request,
    search: str = Query("", description="Search query"),
    domain: str = Query("all", description="Domain filter"),
    sort_by: str = Query("quality", description="Sort by"),
    view_mode: str = Query("cards", description="View mode")
):
    """Enhanced AI-powered homepage with comprehensive database utilization."""
    try:
        print(f"Homepage request: search='{search}', domain='{domain}', sort='{sort_by}'")
        
        # Get articles
        if search:
            articles = db_manager.search_articles(search, domain, 30)
            print(f"Search returned {len(articles)} articles")
        else:
            articles = db_manager.get_articles_optimized(30)
            print(f"Loaded {len(articles)} articles")
            
            # Apply domain filter if specified
            if domain and domain != 'all':
                articles = [a for a in articles if a.get('domain') == domain]
                print(f"Filtered to {len(articles)} articles for domain '{domain}'")
        
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
        return templates.TemplateResponse("index.html", {
            "request": request,
            "articles": articles,
            "domains": available_domains,
            "search_query": search,
            "domain_filter": domain,
            "sort_by": sort_by,
            "view_mode": view_mode,
            "stats": stats,
            "curator_available": False,  # Simplified for testing
            "analyzer_available": False  # Simplified for testing
        })
        
    except Exception as e:
        print(f"Homepage error: {e}")
        import traceback
        traceback.print_exc()
        
        # Return error response
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>HN Enhanced Scraper - Error</title></head>
        <body>
            <h1>HN Enhanced Scraper</h1>
            <p>Error loading enhanced homepage: {str(e)}</p>
            <p>Please check the server logs for details.</p>
            <p><a href="/test">Try test page</a></p>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Simple test page to verify the application is working."""
    try:
        stats = db_manager.get_stats_optimized()
        articles = db_manager.get_articles_optimized(5)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>HN Enhanced Scraper - Test Page</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 40px; }}
                h1 {{ color: #FF6600; }}
                h2 {{ color: #333; }}
                ul {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
                li {{ margin: 10px 0; }}
                a {{ color: #FF6600; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
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
        """
        
        for article in articles[:5]:
            html_content += f"<li><strong>{article['title']}</strong> - {article['domain']} (Quality: {article['discussion_quality_score']})</li>"
        
        html_content += """
            </ul>
            
            <p><a href="/">← Back to Enhanced Homepage</a></p>
            <p><a href="/docs">📖 API Documentation</a></p>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Test Error</title></head>
        <body>
            <h1>Test Error</h1>
            <p>{str(e)}</p>
            <p><a href="/docs">API Documentation</a></p>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)

# API Routes

@app.get("/api/stats", response_model=StatsResponse)
async def api_stats(db: OptimizedDatabaseManager = Depends(get_db_manager)):
    """API endpoint for statistics."""
    try:
        stats = db.get_stats_optimized()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/articles", response_model=List[ArticleResponse])
async def api_articles(
    limit: int = Query(20, ge=1, le=100, description="Number of articles to return"),
    db: OptimizedDatabaseManager = Depends(get_db_manager)
):
    """API endpoint for articles."""
    try:
        articles = db.get_articles_optimized(limit)
        return [ArticleResponse(**article) for article in articles]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search", response_model=List[ArticleResponse])
async def api_search(
    q: str = Query(..., description="Search query"),
    domain: str = Query("all", description="Domain filter"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    db: OptimizedDatabaseManager = Depends(get_db_manager)
):
    """API endpoint for search."""
    try:
        if not q:
            return []
        
        results = db.search_articles(q, domain, limit)
        return [ArticleResponse(**result) for result in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search", response_model=List[ArticleResponse])
async def api_search_post(
    search_request: SearchRequest,
    db: OptimizedDatabaseManager = Depends(get_db_manager)
):
    """API endpoint for search via POST."""
    try:
        results = db.search_articles(search_request.q, search_request.domain, search_request.limit)
        return [ArticleResponse(**result) for result in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/domains")
async def api_domains(db: OptimizedDatabaseManager = Depends(get_db_manager)):
    """API endpoint for available domains."""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT domain FROM article_analyses WHERE domain IS NOT NULL ORDER BY domain')
        domains = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {"domains": domains}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/real-time")
async def api_real_time_analytics(db: OptimizedDatabaseManager = Depends(get_db_manager)):
    """API endpoint for real-time analytics."""
    try:
        stats = db.get_basic_stats()
        
        return {
            'success': True,
            'data': {
                'metrics': {
                    'total_articles': stats.get('total_articles', 0),
                    'total_comments': stats.get('total_comments', 0),
                    'analyzed_comments': stats.get('analyzed_comments', 0),
                    'avg_quality': stats.get('avg_discussion_quality', 0)
                },
                'charts': {
                    'sentiment_distribution': {},
                    'controversy_distribution': {}
                },
                'top_domains': []
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "framework": "FastAPI"
    }

# Custom error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": str(request.url)}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    print("🚀 Starting HN Enhanced Scraper - FastAPI Edition")
    print(f"📊 Database: {DB_PATH}")
    print(f"📁 Templates: templates/")
    
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

# Main execution
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8085))
    print(f"🌐 Available at: http://127.0.0.1:{port}")
    print(f"📖 API Documentation: http://127.0.0.1:{port}/docs")
    print(f"🧪 Test page: http://127.0.0.1:{port}/test")
    
    uvicorn.run(
        "fastapi_enhanced_app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=True
    )
