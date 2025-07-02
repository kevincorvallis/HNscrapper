#!/usr/bin/env python3
"""
🍯 Pookie B News Daily - Main Vercel API with Dynamic Ranking & Reddit Integration
Combines HN functionality with Reddit OutOfTheLoop posts.
"""

import os
import sys
import sqlite3
from datetime import datetime
from typing import Dict, List
from flask import Flask, jsonify, request, render_template
import asyncio

# Add parent directory to path for ranking engine imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Try to import DynamoDB functionality
try:
    from dynamodb_manager import DynamoDBManager
    DYNAMODB_AVAILABLE = True
    print("✅ DynamoDB manager imported successfully")
except ImportError as e:
    DYNAMODB_AVAILABLE = False
    print(f"⚠️  DynamoDB manager not available: {e}")

# Try to import ranking functionality
try:
    from hn_ranking_engine import HNRankingEngine
    from dynamodb_hn_ranker import DynamoDBHNRanker
    RANKING_AVAILABLE = True
    print("✅ Ranking engine imported successfully")
except ImportError as e:
    RANKING_AVAILABLE = False
    print(f"⚠️  Ranking engine not available: {e}")

# Try to import Reddit functionality
try:
    from reddit_manager import get_reddit_manager
    REDDIT_AVAILABLE = True
    print("✅ Reddit manager imported successfully")
except ImportError as e:
    REDDIT_AVAILABLE = False
    print(f"⚠️  Reddit manager not available: {e}")

# Try to import Popular Stories functionality
try:
    from .popular_stories import get_popular_manager
    POPULAR_AVAILABLE = True
    print("✅ Popular stories manager imported successfully")
except ImportError as e:
    try:
        # Try without relative import for direct execution
        from popular_stories import get_popular_manager
        POPULAR_AVAILABLE = True
        print("✅ Popular stories manager imported successfully")
    except ImportError as e2:
        POPULAR_AVAILABLE = False
        print(f"⚠️  Popular stories manager not available: {e}, {e2}")
except Exception as e:
    # Catch any other errors during import (like module initialization errors)
    POPULAR_AVAILABLE = False
    print(f"⚠️  Popular stories manager failed to initialize: {e}")

# Try to import MCP functionality
try:
    from .mcp_client import mcp_client
    MCP_AVAILABLE = True
    print("✅ MCP client imported successfully")
except ImportError:
    try:
        # Try without relative import for direct execution
        from mcp_client import mcp_client
        MCP_AVAILABLE = True
        print("✅ MCP client imported successfully")
    except ImportError as e:
        MCP_AVAILABLE = False
        print(f"⚠️ MCP client not available: {e}")
except Exception as e:
    MCP_AVAILABLE = False
    print(f"⚠️ MCP client failed to initialize: {e}")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'vercel-production-key')

# Database path for serverless environment
DB_PATH = os.path.join('/tmp', 'enhanced_hn_articles.db')

class DatabaseManager:
    """Lightweight database manager for Vercel serverless environment."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database with minimal schema for serverless."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create minimal tables for demo
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY,
                    hn_id TEXT UNIQUE,
                    title TEXT,
                    url TEXT,
                    domain TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert some demo data if empty
            cursor.execute('SELECT COUNT(*) FROM articles')
            if cursor.fetchone()[0] == 0:
                demo_articles = [
                    {
                        'hn_id': '12345',
                        'title': 'Welcome to HN Scraper on Vercel',
                        'url': 'https://news.ycombinator.com/item?id=12345',
                        'domain': 'news.ycombinator.com',
                        'content': 'This is a demo article showing the HN Scraper running on Vercel serverless functions.'
                    },
                    {
                        'hn_id': '12346',
                        'title': 'Vercel Deployment Successful',
                        'url': 'https://vercel.com/docs',
                        'domain': 'vercel.com',
                        'content': 'The Flask application has been successfully deployed to Vercel with serverless functions.'
                    }
                ]
                
                for article in demo_articles:
                    cursor.execute('''
                        INSERT OR IGNORE INTO articles (hn_id, title, url, domain, content)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (article['hn_id'], article['title'], article['url'], article['domain'], article['content']))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    def get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def get_all_articles(self) -> List[Dict]:
        """Get all articles."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT hn_id, title, url, domain, content, created_at
            FROM articles
            ORDER BY created_at DESC
        ''')
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'hn_id': row[0],
                'title': row[1],
                'url': row[2],
                'domain': row[3],
                'content': row[4],
                'created_at': row[5],
                'content_length': len(row[4] or ''),
                'total_comments': 0,  # Demo value
                'discussion_quality_score': 5  # Demo value
            })
        
        conn.close()
        return articles
    
    def get_stats(self) -> Dict:
        """Get basic statistics."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM articles')
        total_articles = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT domain) FROM articles')
        total_domains = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_articles': total_articles,
            'total_domains': total_domains,
            'total_comments': 0,  # Demo
            'avg_discussion_quality': 5.0,  # Demo
            'deployment_status': 'Vercel Serverless Active'
        }

# Initialize database manager
db_manager = DatabaseManager(DB_PATH)

# Initialize DynamoDB manager if available
dynamodb_manager = None
if DYNAMODB_AVAILABLE:
    try:
        dynamodb_manager = DynamoDBManager()
        print("✅ DynamoDB manager initialized")
    except Exception as e:
        print(f"❌ DynamoDB initialization failed: {e}")
        DYNAMODB_AVAILABLE = False

def get_articles_data():
    """Get articles from DynamoDB if available, SQLite as fallback."""
    if DYNAMODB_AVAILABLE and dynamodb_manager:
        try:
            # Get both best and today's articles from DynamoDB
            best_articles = dynamodb_manager.get_best_articles(20)
            todays_articles = dynamodb_manager.get_todays_articles(20)
            stats = dynamodb_manager.get_stats()
            return best_articles, todays_articles, stats
        except Exception as e:
            print(f"DynamoDB error, falling back to SQLite: {e}")
    
    # Fallback to SQLite
    articles = db_manager.get_all_articles()
    stats = db_manager.get_stats()
    # For SQLite, just split articles (best = all, today = empty for demo)
    return articles, [], stats

@app.route('/')
def index():
    """Main homepage with Best Stories and Today's articles sections."""
    # Initialize all variables with safe defaults first
    current_date = datetime.now().strftime('%B %d, %Y')
    current_time = datetime.now().strftime('%I:%M %p')
    current_date_file = datetime.now().strftime('%Y%m%d')
    
    articles = []  # For compatibility
    best_articles = []
    todays_articles = []
    stats = {
        'total_articles': 0, 
        'total_comments': 0, 
        'unique_domains': 0, 
        'avg_score': 0, 
        'domains': []
    }
    
    popular_stories = []
    popular_stats = {
        'status': 'Unavailable',
        'avg_points': 0,
        'total_stories': 0,
        'avg_comments': 0,
        'top_domains': []
    }
    
    reddit_posts = []
    reddit_stats = {
        'status': 'Unavailable', 
        'connected': False
    }
    
    podcast_file = None
    
    try:
        # Get articles data from DynamoDB or SQLite
        best_articles, todays_articles, stats = get_articles_data()
        
        # Get Reddit posts if available
        if REDDIT_AVAILABLE:
            try:
                reddit_mgr = get_reddit_manager()
                reddit_posts = reddit_mgr.fetch_live_posts(limit=5)
                reddit_stats = reddit_mgr.get_stats()
            except Exception as e:
                print(f"Reddit fetch error: {e}")
        
        # Get Popular stories if available
        if POPULAR_AVAILABLE:
            try:
                popular_mgr = get_popular_manager()
                popular_stories = popular_mgr.fetch_popular_stories(limit=5)
                popular_stats = popular_mgr.get_stats()
                popular_stats['status'] = 'Active' if popular_stories else 'No Data'
            except Exception as e:
                print(f"Popular stories fetch error: {e}")
                popular_stats['status'] = 'Error'
        
        # Check for latest podcast file
        audio_dirs = [
            '/tmp/audio_files',  # Vercel temp directory
            os.path.join(os.path.dirname(__file__), '..', 'audio_files'),  # Local
            'audio_files'  # Relative path
        ]
        
        # Try different podcast file names
        possible_files = [
            f'pookie_b_weekly_{current_date_file}.mp3',
            'pookie_b_weekly_latest.mp3',
            f'hn_daily_{current_date_file}.mp3',
            'weekly_podcast_latest.mp3'
        ]
        
        for audio_dir in audio_dirs:
            if os.path.exists(audio_dir):
                for filename in possible_files:
                    if os.path.exists(os.path.join(audio_dir, filename)):
                        podcast_file = filename
                        break
                if podcast_file:
                    break
        
    except Exception as e:
        print(f"Data fetch error: {e}")
    
    # Always render template with safe defaults
    try:
        # Use the clean index.html template
        return render_template('index.html',
            current_date=current_date,
            current_time=current_time,
            articles=best_articles,  # Keep for compatibility
            best_articles=best_articles,  # New: best articles section
            todays_articles=todays_articles,  # New: today's articles section
            stats=stats,
            popular_stories=popular_stories,
            popular_stats=popular_stats,
            reddit_posts=reddit_posts,
            reddit_stats=reddit_stats,
            podcast_file=podcast_file
        )
    except Exception as e:
        print(f"Template render error: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', 
            error_message=f"Template error: {str(e)}",
            error_details="The system encountered an issue rendering the homepage template."
        ), 500

# Enhanced MCP-powered homepage
@app.route('/mcp')
def mcp_homepage():
    """Enhanced homepage powered by MCP servers."""
    # Initialize defaults
    current_date = datetime.now().strftime('%B %d, %Y')
    current_time = datetime.now().strftime('%I:%M %p')
    
    best_articles = []
    todays_articles = []
    daily_insights = []
    trending_topics = []
    mcp_status = "Unavailable"
    
    if MCP_AVAILABLE:
        try:
            # Create event loop for async MCP calls
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Get trending articles via MCP
                trending_data = loop.run_until_complete(
                    mcp_client.call_dynamodb_tool("get_trending_articles", {"limit": 15})
                )
                
                if "trending_articles" in trending_data:
                    best_articles = trending_data["trending_articles"]
                    mcp_status = "Active - DynamoDB"
                
                # Get daily summary via MCP
                summary_data = loop.run_until_complete(
                    mcp_client.call_dynamodb_tool("get_daily_summary", {"date": "today"})
                )
                
                if "todays_highlights" in summary_data:
                    todays_articles = summary_data["todays_highlights"]
                
                # Get trending topics via MCP
                topics_data = loop.run_until_complete(
                    mcp_client.call_scraper_tool("get_trending_topics", {"hours": 24})
                )
                
                if "trending_topics" in topics_data:
                    trending_topics = topics_data["trending_topics"]
                
                # Generate AI insights from the data
                if best_articles:
                    daily_insights = [
                        f"🔥 Top article today: '{best_articles[0].get('title', 'Unknown')[:50]}...'",
                        f"📊 {len(best_articles)} trending articles found",
                        f"⭐ Average score: {sum(a.get('score', 0) for a in best_articles) // len(best_articles)}",
                        f"💬 Most discussed: {max(best_articles, key=lambda x: x.get('num_comments', 0)).get('title', 'Unknown')[:40]}..."
                    ]
                
            finally:
                loop.close()
                
        except Exception as e:
            print(f"MCP error: {e}")
            mcp_status = f"Error: {str(e)}"
            # Fallback to regular data if available
            best_articles, todays_articles, _ = get_articles_data()
    else:
        # Fallback when MCP is not available
        best_articles, todays_articles, _ = get_articles_data()
        daily_insights = ["🔧 MCP servers not available - using fallback data"]
    
    return render_template('index.html',
        current_date=current_date,
        current_time=current_time,
        best_articles=best_articles,
        todays_articles=todays_articles,
        daily_insights=daily_insights,
        trending_topics=trending_topics,
        mcp_status=mcp_status,
        mcp_enabled=True
    )

# Reddit API Endpoints
@app.route('/api/reddit/posts')
def api_reddit_posts():
    """API endpoint for Reddit OutOfTheLoop posts."""
    if not REDDIT_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Reddit integration not available',
            'message': 'Reddit API functionality is disabled',
            'sample_data': True
        }), 503
    
    try:
        reddit_mgr = get_reddit_manager()
        posts = reddit_mgr.fetch_live_posts(limit=10)
        stats = reddit_mgr.get_stats()
        
        return jsonify({
            'success': True,
            'posts': posts,
            'total': len(posts),
            'subreddit': 'OutOfTheLoop',
            'stats': stats,
            'platform': 'Reddit via PRAW'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'platform': 'Reddit via PRAW'
        }), 500

# Popular Stories API Endpoints
@app.route('/api/popular')
def api_popular():
    """API endpoint for Popular HN stories."""
    if not POPULAR_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Popular stories integration not available',
            'message': 'Popular stories functionality is disabled',
            'sample_data': True
        }), 503
    
    try:
        popular_mgr = get_popular_manager()
        stories = popular_mgr.fetch_popular_stories(limit=15)
        stats = popular_mgr.get_stats()
        
        return jsonify({
            'success': True,
            'stories': stories,
            'total': len(stories),
            'source': 'HackerNews /best',
            'stats': stats,
            'platform': 'Serverless Popular Scraper'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'platform': 'Serverless Popular Scraper'
        }), 500

@app.route('/api/combined')
def api_combined():
    """API endpoint for combined HN + Reddit + Popular content."""
    try:
        # Get HN articles
        hn_articles = db_manager.get_all_articles()
        
        # Get Reddit posts if available
        reddit_posts = []
        if REDDIT_AVAILABLE:
            try:
                reddit_mgr = get_reddit_manager()
                reddit_posts = reddit_mgr.fetch_live_posts(limit=5)
            except Exception as e:
                print(f"Reddit API error: {e}")
        
        # Get Popular stories if available
        popular_stories = []
        if POPULAR_AVAILABLE:
            try:
                popular_mgr = get_popular_manager()
                popular_stories = popular_mgr.fetch_popular_stories(limit=5)
            except Exception as e:
                print(f"Popular stories API error: {e}")
        
        # Get search parameters
        search_query = request.args.get('search', '')
        domain_filter = request.args.get('domain', 'all')
        view_mode = request.args.get('view', 'articles')
        
        # Get current time and date for display
        current_time = datetime.now().strftime('%I:%M %p')
        current_date = datetime.now().strftime('%A, %B %d, %Y')
        
        # Generate daily briefing text
        briefing_text = generate_daily_briefing(articles, current_date)
        
        # Use the simplified index template since index_homepage.html was
        # removed in a previous cleanup commit. This restores the homepage on
        # Vercel deployments.
        return render_template('index.html',
                             articles=articles,
                             stats=stats,
                             today_episode=today_episode,
                             weekly_episode=weekly_episode,
                             current_time=current_time,
                             current_date=current_date,
                             briefing_text=briefing_text,
                             search_query=search_query,
                             domain_filter=domain_filter,
                             view_mode=view_mode,
                             sort_by=sort_by,
                             domains=stats.get('domains', []),
                             curator_available=bool(os.environ.get('OPENAI_API_KEY')))
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'platform': 'Vercel Serverless'
        }), 500

@app.route('/audio_files/<filename>')
def serve_audio(filename):
    """Serve audio files for podcast playback."""
    try:
        # Define audio directory paths
        audio_dirs = [
            '/tmp/audio_files',  # Vercel temp directory
            os.path.join(os.path.dirname(__file__), '..', 'audio_files'),  # Local
            'audio_files'  # Relative path
        ]
        
        # Find the audio file
        for audio_dir in audio_dirs:
            if os.path.exists(audio_dir):
                audio_path = os.path.join(audio_dir, filename)
                if os.path.exists(audio_path):
                    return send_file(audio_path, as_attachment=False, 
                                   mimetype='audio/mpeg')
        
        # If file not found, return JSON error
        return jsonify({'error': 'Audio file not found'}), 404
        
    except Exception as e:
        print(f"Error serving audio file {filename}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/articles')
def api_articles():
    """API endpoint for HN articles."""
    try:
        articles = db_manager.get_all_articles()
        return jsonify({
            'success': True,
            'articles': articles,
            'total': len(articles),
            'platform': 'Vercel Serverless'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'platform': 'Vercel Serverless'
        }), 500

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics."""
    try:
        stats = db_manager.get_stats()
        
        # Add Reddit stats if available
        if REDDIT_AVAILABLE:
            try:
                reddit_mgr = get_reddit_manager()
                reddit_stats = reddit_mgr.get_stats()
                stats['reddit'] = reddit_stats
            except Exception:
                stats['reddit'] = {'status': 'Error'}
        else:
            stats['reddit'] = {'status': 'Disabled'}
        
        # Add Popular stories stats if available
        if POPULAR_AVAILABLE:
            try:
                popular_mgr = get_popular_manager()
                popular_stats = popular_mgr.get_stats()
                stats['popular'] = popular_stats
            except Exception:
                stats['popular'] = {'status': 'Error'}
        else:
            stats['popular'] = {'status': 'Disabled'}
        
        stats['platform'] = 'Vercel Serverless'
        stats['timestamp'] = datetime.now().isoformat()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'platform': 'Vercel Serverless'
        }), 500

@app.route('/api/health')
def api_health():
    """Health check endpoint."""
    try:
        # Test database connection
        articles = db_manager.get_all_articles()
        
        # Test Reddit connection
        reddit_status = 'disabled'
        if REDDIT_AVAILABLE:
            try:
                reddit_mgr = get_reddit_manager()
                reddit_status = 'connected' if reddit_mgr.connected else 'error'
            except Exception:
                reddit_status = 'error'
        
        # Test Popular stories connection
        popular_status = 'disabled'
        if POPULAR_AVAILABLE:
            try:
                popular_mgr = get_popular_manager()
                test_stories = popular_mgr.fetch_popular_stories(limit=1)
                popular_status = 'connected' if test_stories else 'error'
            except Exception:
                popular_status = 'error'
        
        return jsonify({
            'status': 'healthy',
            'platform': 'Vercel Serverless',
            'database': 'connected',
            'reddit': reddit_status,
            'popular': popular_status,
            'articles_count': len(articles),
            'timestamp': datetime.now().isoformat(),
            'python_version': '3.9+',
            'flask_version': '3.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'platform': 'Vercel Serverless',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/test')
def test_deployment():
    """Test deployment functionality."""
    tests = []
    
    # Test 1: Database connectivity
    try:
        articles = db_manager.get_all_articles()
        tests.append({
            'test': 'Database Connectivity',
            'status': 'PASS',
            'details': f'Retrieved {len(articles)} articles'
        })
    except Exception as e:
        tests.append({
            'test': 'Database Connectivity',
            'status': 'FAIL',
            'details': str(e)
        })
    
    # Test 2: Reddit integration
    try:
        if REDDIT_AVAILABLE:
            reddit_mgr = get_reddit_manager()
            posts = reddit_mgr.fetch_live_posts(limit=1)
            tests.append({
                'test': 'Reddit Integration',
                'status': 'PASS',
                'details': f'Retrieved {len(posts)} posts, Status: {reddit_mgr.get_stats()["status"]}'
            })
        else:
            tests.append({
                'test': 'Reddit Integration',
                'status': 'SKIP',
                'details': 'Reddit integration disabled'
            })
    except Exception as e:
        tests.append({
            'test': 'Reddit Integration',
            'status': 'FAIL',
            'details': str(e)
        })
    
    # Test 3: Popular Stories integration
    try:
        if POPULAR_AVAILABLE:
            popular_mgr = get_popular_manager()
            stories = popular_mgr.fetch_popular_stories(limit=1)
            tests.append({
                'test': 'Popular Stories Integration',
                'status': 'PASS',
                'details': f'Retrieved {len(stories)} stories, Status: {popular_mgr.get_stats()["status"]}'
            })
        else:
            tests.append({
                'test': 'Popular Stories Integration',
                'status': 'SKIP',
                'details': 'Popular stories integration disabled'
            })
    except Exception as e:
        tests.append({
            'test': 'Popular Stories Integration',
            'status': 'FAIL',
            'details': str(e)
        })
    
    # Test 4: Environment variables
    try:
        flask_env = os.environ.get('FLASK_ENV', 'not set')
        tests.append({
            'test': 'Environment Variables',
            'status': 'PASS',
            'details': f'FLASK_ENV: {flask_env}'
        })
    except Exception as e:
        tests.append({
            'test': 'Environment Variables',
            'status': 'FAIL',
            'details': str(e)
        })
    
    # Test 4: File system access
    try:
        temp_path = '/tmp/test_write.txt'
        with open(temp_path, 'w') as f:
            f.write('test')
        os.remove(temp_path)
        tests.append({
            'test': 'File System Access',
            'status': 'PASS',
            'details': 'Can write to /tmp'
        })
    except Exception as e:
        tests.append({
            'test': 'File System Access',
            'status': 'FAIL',
            'details': str(e)
        })
    
    # Generate HTML report
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Deployment Test Results</title>
        <style>
            body { font-family: sans-serif; margin: 40px; background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%); min-height: 100vh; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 20px; }
            .pass { color: #28a745; }
            .fail { color: #dc3545; }
            .skip { color: #ffc107; }
            .test-result { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧪 Deployment Test Results</h1>
            <p><strong>Platform:</strong> Vercel Serverless with Reddit Integration</p>
            <p><strong>Test Time:</strong> """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC') + """</p>
    """
    
    for test in tests:
        status_class = test['status'].lower()
        html += f"""
        <div class="test-result">
            <h3>{test['test']}: <span class="{status_class}">{test['status']}</span></h3>
            <p>{test['details']}</p>
        </div>
        """
    
    html += """
        <div style="margin-top: 30px;">
            <a href="/">← Back to Home</a>
        </div>
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/debug')
def debug():
    """Debug route to test template variables."""
    try:
        # Simple test data
        current_date = datetime.now().strftime('%B %d, %Y')
        current_time = datetime.now().strftime('%I:%M %p')
        
        test_data = {
            'current_date': current_date,
            'current_time': current_time,
            'articles': [],
            'stats': {'total_articles': 0, 'total_comments': 0, 'unique_domains': 0, 'avg_score': 0, 'domains': []},
            'popular_stories': [],
            'popular_stats': {
                'status': 'Test',
                'avg_points': 42,
                'total_stories': 0,
                'avg_comments': 0,
                'top_domains': []
            },
            'reddit_posts': [],
            'reddit_stats': {'status': 'Test', 'connected': False},
            'podcast_file': None
        };
        
        return render_template('index_organized.html', **test_data);
        
    except Exception as e:
        return f"Debug error: {str(e)}"

# MCP Enhanced Route (Added at end to ensure registration)
@app.route('/mcp')
def mcp_enhanced_homepage():
    """MCP-enhanced homepage with AI insights."""
    current_date = datetime.now().strftime('%B %d, %Y')
    current_time = datetime.now().strftime('%I:%M %p')
    
    # Initialize defaults
    best_articles = []
    todays_articles = []
    daily_insights = ["🤖 MCP-Enhanced View Active"]
    trending_topics = []
    mcp_status = "Testing"
    
    try:
        # Get basic data first
        best_articles, todays_articles, stats = get_articles_data()
        
        # Add MCP-specific insights if available
        if MCP_AVAILABLE:
            try:
                # Create simple event loop for MCP calls
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Test trending topics
                topics_result = loop.run_until_complete(
                    mcp_client.call_scraper_tool("get_trending_topics", {"hours": 24})
                )
                
                if "trending_topics" in topics_result:
                    trending_topics = topics_result["trending_topics"]
                    mcp_status = "Active"
                    daily_insights.extend([
                        f"🔥 {len(trending_topics)} trending topics identified",
                        "📊 AI analysis pipeline operational",
                        "🍯 Enhanced with MCP servers"
                    ])
                else:
                    mcp_status = "Partial"
                    daily_insights.append("⚠️ Some MCP services unavailable")
                
                loop.close()
                
            except Exception as e:
                mcp_status = f"Error: {str(e)[:50]}"
                daily_insights.append(f"❌ MCP Error: {str(e)[:50]}")
        else:
            daily_insights.append("⚠️ MCP not available")
            
    except Exception as e:
        daily_insights = [f"❌ Data Error: {str(e)}"]
    
    return render_template('index.html',
        current_date=current_date,
        current_time=current_time,
        best_articles=best_articles,
        todays_articles=todays_articles,
        daily_insights=daily_insights,
        trending_topics=trending_topics,
        mcp_status=mcp_status,
        mcp_enabled=True,
        stats={}
    )

# Vercel requires a handler function
def handler(request):
    """Vercel handler function."""
    return app(request.environ, lambda status, headers: None)

# For local testing
if __name__ == '__main__':
    app.run(debug=True, port=5003)