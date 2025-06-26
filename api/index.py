#!/usr/bin/env python3
"""
Main Flask API entry point for Vercel serverless deployment.
Supports both SQLite (local) and DynamoDB (production) storage.
"""

import html
import json
import os
import sqlite3
import sys
import requests
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from flask import Flask, jsonify, render_template, request

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Try to import DynamoDB manager and podcast generator
try:
    from dynamodb_manager import DynamoDBManager
    DYNAMODB_AVAILABLE = True
except ImportError:
    DYNAMODB_AVAILABLE = False
    print("DynamoDB not available, falling back to SQLite")

try:
    from daily_podcast_generator import DailyPodcastGenerator
    from weekly_podcast_generator import WeeklyPodcastGenerator
    PODCAST_AVAILABLE = True
except ImportError:
    PODCAST_AVAILABLE = False
    print("Podcast generator not available")

app = Flask(__name__, 
           template_folder='./templates',
           static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', 'vercel-production-key')

# Database configuration
USE_DYNAMODB = (
    os.environ.get('VERCEL') and 
    DYNAMODB_AVAILABLE and 
    os.environ.get('AWS_ACCESS_KEY_ID') and 
    os.environ.get('AWS_SECRET_ACCESS_KEY')
)

# Database path for SQLite fallback
DB_PATH = '/tmp/enhanced_hn_articles.db' if os.environ.get('VERCEL') else 'enhanced_hn_articles.db'

print(f"Database mode: {'DynamoDB' if USE_DYNAMODB else 'SQLite'}")
print(f"SQLite path: {DB_PATH if not USE_DYNAMODB else 'N/A'}")

class DatabaseManager:
    """Unified database manager supporting both SQLite and DynamoDB."""
    
    def __init__(self, use_dynamodb: bool = False, db_path: str = None):
        self.use_dynamodb = use_dynamodb
        self.db_path = db_path
        
        if self.use_dynamodb:
            self.dynamo_db = DynamoDBManager()
        else:
            self.init_sqlite_db()
    
    def init_sqlite_db(self):
        """Initialize SQLite database with sample data if needed."""
        if not os.path.exists(self.db_path):
            # Create basic tables for demo
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create basic tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    hn_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT,
                    domain TEXT,
                    score INTEGER,
                    author TEXT,
                    time_posted INTEGER,
                    num_comments INTEGER,
                    story_text TEXT,
                    story_type TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comments (
                    comment_id TEXT PRIMARY KEY,
                    article_id TEXT,
                    parent_id TEXT,
                    author TEXT,
                    content TEXT,
                    time_posted INTEGER,
                    level INTEGER DEFAULT 0,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles (hn_id)
                )
            ''')
            
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
                INSERT OR IGNORE INTO articles 
                (hn_id, title, url, domain, score, author, time_posted, num_comments, story_text, story_type) VALUES 
                ('sample1', 'Sample HN Article', 'https://example.com', 'example.com', 100, 'sample_user', 1640995200, 10, 'This is a sample article for demo purposes.', 'story')
            ''')
            
            conn.commit()
            conn.close()
    
    def get_connection(self):
        """Get database connection (SQLite only)."""
        if self.use_dynamodb:
            return None
        return sqlite3.connect(self.db_path)
    
    def get_articles_with_analysis(self, limit: int = 50, sort_by: str = 'score') -> List[Dict]:
        """Get articles with comprehensive data."""
        if self.use_dynamodb:
            return self._get_articles_dynamodb(limit, sort_by)
        else:
            return self._get_articles_sqlite(limit, sort_by)
    
    def _get_articles_dynamodb(self, limit: int, sort_by: str) -> List[Dict]:
        """Get articles from DynamoDB."""
        try:
            items = self.dynamo_db.get_articles(limit, sort_by)
            
            # Convert DynamoDB items to expected format
            articles = []
            for item in items:
                articles.append({
                    'hn_id': item.get('hn_id', ''),
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'domain': item.get('domain', ''),
                    'score': int(item.get('score', 0)),
                    'author': item.get('author', 'unknown'),
                    'time_posted': int(item.get('time_posted', 0)),
                    'num_comments': int(item.get('num_comments', 0)),
                    'story_text': item.get('story_text', ''),
                    'scraped_at': item.get('scraped_at', ''),
                    'summary': f"Score: {item.get('score', 0)}, Comments: {item.get('num_comments', 0)}, Author: {item.get('author', 'unknown')}"
                })
            
            return articles
        except Exception as e:
            print(f"Error getting articles from DynamoDB: {e}")
            return []
    
    def _get_articles_sqlite(self, limit: int, sort_by: str) -> List[Dict]:
        """Get articles from SQLite with comprehensive data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Determine sort order
        sort_orders = {
            'score': 'score DESC, scraped_at DESC',
            'recent': 'scraped_at DESC',
            'comments': 'num_comments DESC',
            'title': 'title ASC'
        }
        order_clause = sort_orders.get(sort_by, 'score DESC, scraped_at DESC')
        
        # Try to get from new articles table first, fallback to legacy table
        cursor.execute(f'''
            SELECT 
                hn_id, title, url, domain, score, author, 
                time_posted, num_comments, story_text, scraped_at
            FROM articles
            ORDER BY {order_clause}
            LIMIT ?
        ''', (limit,))
        
        articles = []
        rows = cursor.fetchall()
        
        if rows:
            # Use new articles table data
            for row in rows:
                articles.append({
                    'hn_id': row[0],
                    'title': row[1],
                    'url': row[2],
                    'domain': row[3],
                    'score': row[4] or 0,
                    'author': row[5] or 'unknown',
                    'time_posted': row[6] or 0,
                    'num_comments': row[7] or 0,
                    'story_text': row[8] or '',
                    'scraped_at': row[9],
                    'summary': f"Score: {row[4] or 0}, Comments: {row[7] or 0}, Author: {row[5] or 'unknown'}"
                })
        else:
            # Fallback to legacy table
            cursor.execute('''
                SELECT hn_id, title, url, domain, summary, generated_at
                FROM article_analyses
                ORDER BY generated_at DESC
                LIMIT ?
            ''', (limit,))
            
            for row in cursor.fetchall():
                articles.append({
                    'hn_id': row[0],
                    'title': row[1],
                    'url': row[2],
                    'domain': row[3],
                    'summary': row[4],
                    'scraped_at': row[5],
                    'score': 0,
                    'author': 'unknown',
                    'num_comments': 0,
                    'story_text': ''
                })
        
        conn.close()
        return articles
    
    def get_single_article(self, article_id: str) -> Optional[Dict]:
        """Get a single article with its comments."""
        if self.use_dynamodb:
            return self._get_single_article_dynamodb(article_id)
        else:
            return self._get_single_article_sqlite(article_id)
    
    def _get_single_article_dynamodb(self, article_id: str) -> Optional[Dict]:
        """Get single article from DynamoDB."""
        try:
            article = self.dynamo_db.get_article(article_id)
            if not article:
                return None
            
            # Get comments
            comments = self.dynamo_db.get_article_comments(article_id)
            
            # Convert to expected format
            formatted_article = {
                'hn_id': article.get('hn_id', ''),
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'domain': article.get('domain', ''),
                'score': int(article.get('score', 0)),
                'author': article.get('author', 'unknown'),
                'time_posted': int(article.get('time_posted', 0)),
                'num_comments': int(article.get('num_comments', 0)),
                'story_text': article.get('story_text', ''),
                'scraped_at': article.get('scraped_at', ''),
                'comments': []
            }
            
            # Format comments
            for comment in comments:
                formatted_article['comments'].append({
                    'comment_id': comment.get('comment_id', ''),
                    'parent_id': comment.get('parent_id', ''),
                    'author': comment.get('author', 'unknown'),
                    'content': comment.get('content', ''),
                    'time_posted': int(comment.get('time_posted', 0)),
                    'level': int(comment.get('level', 0))
                })
            
            return formatted_article
        except Exception as e:
            print(f"Error getting single article from DynamoDB: {e}")
            return None
    
    def _get_single_article_sqlite(self, article_id: str) -> Optional[Dict]:
        """Get single article from SQLite."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get article
        cursor.execute('''
            SELECT 
                hn_id, title, url, domain, score, author, 
                time_posted, num_comments, story_text, scraped_at
            FROM articles
            WHERE hn_id = ?
        ''', (article_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        article = {
            'hn_id': row[0],
            'title': row[1],
            'url': row[2],
            'domain': row[3],
            'score': row[4] or 0,
            'author': row[5] or 'unknown',
            'time_posted': row[6] or 0,
            'num_comments': row[7] or 0,
            'story_text': row[8] or '',
            'scraped_at': row[9]
        }
        
        # Get comments
        comments = self.get_article_comments_sqlite(article_id)
        article['comments'] = comments
        
        conn.close()
        return article
    
    def get_article_comments_sqlite(self, article_id: str) -> List[Dict]:
        """Get comments for a specific article from SQLite."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get all comments for the article
        cursor.execute('''
            SELECT comment_id, parent_id, author, content, time_posted, level
            FROM comments
            WHERE article_id = ?
            ORDER BY level ASC, time_posted ASC
        ''', (article_id,))
        
        comments = []
        for row in cursor.fetchall():
            comments.append({
                'comment_id': row[0],
                'parent_id': row[1],
                'author': row[2],
                'content': row[3],
                'time_posted': row[4],
                'level': row[5]
            })
        
        conn.close()
        return comments
    
    def get_database_stats(self) -> Dict:
        """Get comprehensive database statistics."""
        if self.use_dynamodb:
            return self._get_stats_dynamodb()
        else:
            return self._get_stats_sqlite()
    
    def _get_stats_dynamodb(self) -> Dict:
        """Get stats from DynamoDB."""
        try:
            return self.dynamo_db.get_stats()
        except Exception as e:
            print(f"Error getting DynamoDB stats: {e}")
            return {
                'total_articles': 0,
                'total_comments': 0,
                'avg_score': 0,
                'unique_domains': 0,
                'domains': []
            }
    
    def _get_stats_sqlite(self) -> Dict:
        """Get stats from SQLite."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if new tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
        has_articles_table = cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comments'")
        has_comments_table = cursor.fetchone() is not None
        
        if has_articles_table:
            cursor.execute('SELECT COUNT(*) FROM articles')
            total_articles = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(score) FROM articles WHERE score > 0')
            avg_score = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(DISTINCT domain) FROM articles')
            unique_domains = cursor.fetchone()[0]
        else:
            cursor.execute('SELECT COUNT(*) FROM article_analyses')
            total_articles = cursor.fetchone()[0]
            avg_score = 0
            unique_domains = 3
        
        if has_comments_table:
            cursor.execute('SELECT COUNT(*) FROM comments')
            total_comments = cursor.fetchone()[0]
        else:
            cursor.execute('SELECT COUNT(*) FROM comment_analyses')
            total_comments = cursor.fetchone()[0]
        
        # Get top domains
        if has_articles_table:
            cursor.execute('''
                SELECT domain, COUNT(*) as count 
                FROM articles 
                GROUP BY domain 
                ORDER BY count DESC 
                LIMIT 5
            ''')
            domains = [row[0] for row in cursor.fetchall()]
        else:
            domains = ['example.com', 'github.com', 'techcrunch.com']
        
        conn.close()
        
        return {
            'total_articles': total_articles,
            'total_comments': total_comments,
            'analyzed_comments': total_comments,
            'avg_score': round(avg_score, 1),
            'unique_domains': unique_domains,
            'domains': domains
        }


# Core utility functions for templates
def count_comments_recursive(comments):
    """Recursively count all comments including replies."""
    if not comments:
        return 0
    count = len(comments)
    for comment in comments:
        count += count_comments_recursive(comment.get('replies', []))
    return count

# Register the function as a template global so it's available in all templates
app.jinja_env.globals['count_comments_recursive'] = count_comments_recursive

# Time formatting utilities
def format_time_ago(timestamp):
    """Convert timestamp to human-readable 'time ago' format."""
    if not timestamp:
        return "unknown time"
    
    try:
        # Handle different timestamp formats
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
        else:
            return "unknown time"
        
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "just now"
    except:
        return "unknown time"

def format_scraped_time(timestamp):
    """Format scraped timestamp for display."""
    if not timestamp:
        return "unknown"
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        return timestamp
    except:
        return timestamp

# Register template filters
@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    """Convert Unix timestamp to readable date."""
    try:
        return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M')
    except (ValueError, TypeError):
        return 'unknown time'

# HTML decoder filter for comments
def decode_html_entities(text):
    """Decode HTML entities in text."""
    if not text:
        return text
    return html.unescape(text)

app.jinja_env.filters['time_ago'] = format_time_ago
app.jinja_env.filters['scraped_time'] = format_scraped_time
app.jinja_env.filters['decode_html'] = decode_html_entities

# Initialize database manager
db_manager = DatabaseManager(use_dynamodb=USE_DYNAMODB, db_path=DB_PATH)

def get_article_category(article: Dict) -> str:
    """Determine article category based on domain and title with improved accuracy."""
    domain = article.get('domain', '').lower()
    title = article.get('title', '').lower()
    url = article.get('url', '').lower()
    
    # Technology & Programming
    if any(tech in domain for tech in [
        'github.com', 'stackoverflow.com', 'hacker-news.firebaseio.com', 'ycombinator.com',
        'openai.com', 'anthropic.com', 'google.com', 'microsoft.com', 'apple.com',
        'mozilla.org', 'techcrunch.com', 'arstechnica.com', 'theverge.com', 'wired.com',
        'hackernoon.com', 'dev.to', 'medium.com/@', 'substack.com'
    ]):
        return 'Technology'
    
    if any(tech in title for tech in [
        'ai', 'artificial intelligence', 'machine learning', 'ml', 'programming', 'code',
        'software', 'javascript', 'python', 'react', 'node', 'api', 'database', 'cloud',
        'docker', 'kubernetes', 'blockchain', 'crypto', 'algorithm', 'framework',
        'developer', 'coding', 'tech', 'startup', 'saas', 'open source', 'github'
    ]):
        return 'Technology'
    
    # Science & Research
    if any(sci in domain for sci in [
        'nature.com', 'science.org', 'arxiv.org', 'pubmed.ncbi.nlm.nih.gov',
        'scientificamerican.com', 'newscientist.com', 'nasa.gov', 'mit.edu',
        'stanford.edu', 'harvard.edu', 'berkeley.edu'
    ]):
        return 'Science'
    
    if any(sci in title for sci in [
        'research', 'study', 'scientists', 'discovery', 'experiment', 'medical',
        'health', 'medicine', 'biology', 'physics', 'chemistry', 'space', 'climate',
        'environment', 'covid', 'vaccine', 'drug', 'treatment', 'therapy'
    ]):
        return 'Science'
    
    # Business & Finance
    if any(biz in domain for biz in [
        'bloomberg.com', 'reuters.com', 'wsj.com', 'ft.com', 'forbes.com',
        'fortune.com', 'businessinsider.com', 'cnbc.com', 'marketwatch.com',
        'sec.gov', 'federalreserve.gov'
    ]):
        return 'Business'
    
    if any(biz in title for biz in [
        'economy', 'market', 'stock', 'investment', 'finance', 'money', 'bank',
        'company', 'business', 'revenue', 'profit', 'earnings', 'ipo', 'merger',
        'acquisition', 'venture capital', 'funding', 'valuation', 'trade'
    ]):
        return 'Business'
    
    # Politics & Policy
    if any(pol in domain for pol in [
        'gov', 'congress.gov', 'whitehouse.gov', 'fec.gov', 'supremecourt.gov',
        'politico.com', 'washingtonpost.com', 'nytimes.com', 'cnn.com', 'bbc.com'
    ]):
        return 'Politics'
    
    if any(pol in title for pol in [
        'government', 'congress', 'senate', 'president', 'election', 'vote', 'policy',
        'law', 'legal', 'court', 'supreme court', 'regulation', 'biden', 'trump',
        'politics', 'political', 'democracy', 'republican', 'democrat'
    ]):
        return 'Politics'
    
    # Entertainment & Culture
    if any(ent in domain for ent in [
        'netflix.com', 'disney.com', 'hulu.com', 'youtube.com', 'spotify.com',
        'twitch.tv', 'reddit.com', 'twitter.com', 'instagram.com', 'tiktok.com',
        'variety.com', 'hollywoodreporter.com', 'ign.com', 'gamespot.com'
    ]):
        return 'Entertainment'
    
    if any(ent in title for ent in [
        'movie', 'film', 'tv show', 'series', 'music', 'album', 'song', 'artist',
        'game', 'gaming', 'video game', 'entertainment', 'celebrity', 'actor',
        'actress', 'director', 'streaming', 'netflix', 'disney', 'social media'
    ]):
        return 'Entertainment'
    
    # World News & International
    if any(world in domain for world in [
        'aljazeera.com', 'dw.com', 'france24.com', 'rt.com', 'xinhuanet.com',
        'un.org', 'who.int', 'worldbank.org', 'nato.int'
    ]):
        return 'World News'
    
    if any(world in title for world in [
        'china', 'russia', 'ukraine', 'europe', 'asia', 'africa', 'international',
        'global', 'world', 'country', 'nation', 'war', 'conflict', 'peace',
        'diplomacy', 'embassy', 'foreign', 'immigration', 'refugee'
    ]):
        return 'World News'
    
    # Education & Career
    if any(edu in domain for edu in [
        '.edu', 'coursera.com', 'udemy.com', 'khanacademy.org', 'edx.org',
        'udacity.com', 'skillshare.com', 'linkedin.com/learning'
    ]):
        return 'Education'
    
    if any(edu in title for edu in [
        'education', 'school', 'university', 'college', 'student', 'teacher',
        'learning', 'course', 'degree', 'career', 'job', 'hiring', 'employment',
        'salary', 'interview', 'resume', 'skill'
    ]):
        return 'Education'
    
    # Default to General for diverse HN content
    return 'General'

def extract_article_image(url: str) -> Optional[str]:
    """Extract main image from article URL."""
    if not url or url.startswith('news.ycombinator.com'):
        return None
    
    try:
        # Set user agent to avoid blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try different meta tags for images
        image_selectors = [
            'meta[property="og:image"]',
            'meta[property="twitter:image"]', 
            'meta[name="twitter:image"]',
            'meta[property="article:image"]',
            'link[rel="image_src"]'
        ]
        
        for selector in image_selectors:
            img_tag = soup.select_one(selector)
            if img_tag:
                image_url = img_tag.get('content') or img_tag.get('href')
                if image_url:
                    # Make sure it's a full URL
                    if image_url.startswith('//'):
                        image_url = 'https:' + image_url
                    elif image_url.startswith('/'):
                        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                        image_url = base_url + image_url
                    
                    # Validate image URL
                    if image_url.startswith('http') and any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        return image_url
        
        # Fallback: look for first large image
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src')
            if src and (img.get('width', 0) and int(img.get('width', 0)) > 200) or (img.get('height', 0) and int(img.get('height', 0)) > 200):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                    src = base_url + src
                
                if src.startswith('http'):
                    return src
                    
    except Exception as e:
        print(f"Error extracting image from {url}: {e}")
    
    return None

def generate_daily_briefing(articles: List[Dict], current_date: str) -> str:
    """Generate NPR-style daily briefing paragraph."""
    if not articles:
        return f"Good morning. It's {current_date}, and while today brings a quieter moment in the news cycle, we continue to monitor the latest developments across various industries and communities."
    
    # Count categories
    categories = {}
    for article in articles:
        cat = article.get('category', 'General')
        categories[cat] = categories.get(cat, 0) + 1
    
    # Build briefing
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
    
    category_text = ""
    if len(top_categories) == 1:
        category_text = f"focusing primarily on {top_categories[0][0].lower()}"
    elif len(top_categories) == 2:
        category_text = f"spanning {top_categories[0][0].lower()} and {top_categories[1][0].lower()}"
    else:
        cats = [cat[0].lower() for cat in top_categories]
        category_text = f"spanning {', '.join(cats[:-1])}, and {cats[-1]}"
    
    return f"Good morning. It's {current_date}, and we're covering {len(articles)} significant stories from the community today, {category_text}. From innovative developments to industry insights, these stories represent the conversations shaping our evolving landscape."

@app.route('/')
def home():
    """Enhanced homepage with daily podcast and current date."""
    try:
        # Get basic stats
        stats = db_manager.get_database_stats()
        
        # Get sort parameter
        sort_by = request.args.get('sort', 'score')
        
        # Get articles for homepage (limit to 10 for headlines)
        articles = db_manager.get_articles_with_analysis(limit=10, sort_by=sort_by)
        
        # Add categories to articles
        for article in articles:
            article['category'] = get_article_category(article)
        
        # Get today's podcast episode and this week's episode if available
        today_episode = None
        weekly_episode = None
        try:
            from complete_podcast_runner import CompletePodcastGenerator
            from weekly_podcast_generator import WeeklyPodcastGenerator
            
            # Daily podcast
            daily_generator = CompletePodcastGenerator()
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Try to get today's episode
            recent_daily = daily_generator.get_recent_episodes(1)
            if recent_daily and recent_daily[0].get('date') == today:
                today_episode = recent_daily[0]
                # Ensure audio path is accessible via URL
                if today_episode.get('audio_path'):
                    audio_filename = today_episode['audio_path'].split('/')[-1]
                    today_episode['audio_url'] = f'/audio/{audio_filename}'
            
            # Weekly podcast
            weekly_generator = WeeklyPodcastGenerator()
            recent_weekly = weekly_generator.get_recent_weekly_episodes(1)
            if recent_weekly:
                weekly_episode = recent_weekly[0]
                # Ensure audio path is accessible via URL
                if weekly_episode.get('audio_path'):
                    audio_filename = weekly_episode['audio_path'].split('/')[-1]
                    weekly_episode['audio_url'] = f'/audio/{audio_filename}'
        except Exception as e:
            print(f"Error getting podcast episodes: {e}")
        
        # Get search parameters
        search_query = request.args.get('search', '')
        domain_filter = request.args.get('domain', 'all')
        view_mode = request.args.get('view', 'articles')
        
        # Get current time and date for display
        current_time = datetime.now().strftime('%I:%M %p')
        current_date = datetime.now().strftime('%A, %B %d, %Y')
        
        # Generate daily briefing text
        briefing_text = generate_daily_briefing(articles, current_date)
        
        return render_template('index_homepage.html',
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
        return render_template('error.html', error=str(e)), 500

@app.route('/article/<article_id>')
def article_detail(article_id):
    """Show detailed view of a single article with comments and talking points."""
    try:
        article = db_manager.get_single_article(article_id)
        if not article:
            return render_template('error.html', error='Article not found'), 404
        
        # Add category to article
        article['category'] = get_article_category(article)
        
        # Extract article image if not already present
        if not article.get('image_url') and article.get('url'):
            article['image_url'] = extract_article_image(article['url'])
        
        # Get talking points from top comments
        talking_points = []
        if article.get('comments'):
            # Sort comments by score and extract high-quality ones
            sorted_comments = sorted(
                [c for c in article['comments'] if c.get('score', 0) >= 3],
                key=lambda x: x.get('score', 0),
                reverse=True
            )
            
            for comment in sorted_comments[:5]:  # Top 5 comments
                if comment.get('content') and len(comment.get('content', '')) > 100:
                    talking_points.append({
                        'text': comment['content'][:300] + ('...' if len(comment['content']) > 300 else ''),
                        'author': comment.get('author', 'Anonymous'),
                        'score': comment.get('score', 0)
                    })
        
        return render_template('article_detail.html', 
                             article=article, 
                             talking_points=talking_points)
    
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

@app.route('/api/podcast/episodes')
def api_podcast_episodes():
    """Get recent podcast episodes."""
    try:
        if not PODCAST_AVAILABLE:
            return jsonify({'error': 'Podcast functionality not available'}), 503
        
        days = request.args.get('days', 7, type=int)
        generator = DailyPodcastGenerator()
        episodes = generator.get_recent_episodes(days)
        
        return jsonify({
            'episodes': episodes,
            'count': len(episodes)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/podcast/episode/<date>')
def api_podcast_episode(date):
    """Get specific podcast episode by date."""
    try:
        if not PODCAST_AVAILABLE:
            return jsonify({'error': 'Podcast functionality not available'}), 503
        
        generator = DailyPodcastGenerator()
        
        # Try to get existing episode
        try:
            episode_data = generator.db.get_item('hn_analyses', date)
            if episode_data and episode_data.get('type') == 'podcast_episode':
                return jsonify(episode_data)
        except:
            pass
        
        return jsonify({'error': 'Episode not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/podcast/generate', methods=['POST'])
def api_podcast_generate():
    """Generate a new podcast episode."""
    try:
        if not PODCAST_AVAILABLE:
            return jsonify({'error': 'Podcast functionality not available'}), 503
        
        data = request.get_json() or {}
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        generator = DailyPodcastGenerator()
        episode = generator.generate_daily_episode(date)
        
        if episode:
            return jsonify({
                'success': True,
                'episode': episode.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate episode'
            }), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/podcast')
def podcast_dashboard():
    """Podcast dashboard page."""
    try:
        if not PODCAST_AVAILABLE:
            return render_template('error.html', 
                                 title="Podcast Unavailable",
                                 message="Podcast functionality is not available.")
        
        generator = DailyPodcastGenerator()
        recent_episodes = generator.get_recent_episodes(7)
        
        return render_template('podcast.html', 
                             episodes=recent_episodes,
                             title="Daily Podcast")
    except Exception as e:
        return render_template('error.html', 
                             title="Podcast Error",
                             message=f"Error loading podcast dashboard: {str(e)}")

@app.route('/api/podcast/weekly/episodes')
def api_weekly_podcast_episodes():
    """Get recent weekly podcast episodes."""
    try:
        if not PODCAST_AVAILABLE:
            return jsonify({'error': 'Podcast functionality not available'}), 503
        
        weeks = request.args.get('weeks', 4, type=int)
        from weekly_podcast_generator import WeeklyPodcastGenerator
        generator = WeeklyPodcastGenerator()
        episodes = generator.get_recent_weekly_episodes(weeks)
        
        return jsonify({
            'episodes': episodes,
            'count': len(episodes)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/podcast/weekly/generate', methods=['POST'])
def api_weekly_podcast_generate():
    """Generate a new weekly podcast episode."""
    try:
        if not PODCAST_AVAILABLE:
            return jsonify({'error': 'Podcast functionality not available'}), 503
        
        data = request.get_json() or {}
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        from weekly_podcast_generator import WeeklyPodcastGenerator
        generator = WeeklyPodcastGenerator()
        episode = generator.generate_weekly_episode(date)
        
        if episode:
            return jsonify({
                'success': True,
                'episode': episode.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate weekly episode'
            }), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve audio files from the audio_files directory."""
    try:
        from flask import send_from_directory
        audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'audio_files')
        return send_from_directory(audio_dir, filename, mimetype='audio/mpeg')
    except Exception as e:
        return jsonify({'error': f'Audio file not found: {e}'}), 404

# Vercel requires the app to be named 'app'
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
