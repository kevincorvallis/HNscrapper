#!/usr/bin/env python3
"""
Consolidated Flask web application for Pookie B News Daily.
All functionalities integrated into a single homepage with comprehensive database integration.
Features weekly podcast generation and playback.
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

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'enhanced_hn_articles.db')

class DatabaseManager:
    """Comprehensive database manager for all HN scraper data."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def get_all_articles_with_analysis(self) -> List[Dict]:
        """Get all articles with comprehensive analysis data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get articles with analysis data
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
        ''')
        
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
                'analyzed_comments': row[11] or 0,
                'total_comments': row[12] or 0,
                'avg_comment_quality': round(row[13] or 0, 1)
            }
            articles.append(article)
        
        conn.close()
        return articles
    
    def get_article_detail_with_analysis(self, hn_id: str) -> Optional[Dict]:
        """Get comprehensive article detail with all analysis data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get article analysis
        cursor.execute('''
            SELECT hn_id, title, url, domain, summary, key_insights, main_themes,
                   sentiment_analysis, discussion_quality_score, controversy_level, generated_at
            FROM article_analyses WHERE hn_id = ?
        ''', (hn_id,))
        
        article_row = cursor.fetchone()
        if not article_row:
            conn.close()
            return None
        
        article = {
            'hn_id': article_row[0],
            'title': article_row[1],
            'url': article_row[2],
            'domain': article_row[3],
            'summary': article_row[4],
            'key_insights': article_row[5],
            'main_themes': article_row[6],
            'sentiment_analysis': article_row[7],
            'discussion_quality_score': article_row[8] or 0,
            'controversy_level': article_row[9],
            'generated_at': article_row[10]
        }
        
        # Get analyzed comments
        cursor.execute('''
            SELECT comment_id, author, comment_text, analysis_summary, key_points,
                   sentiment, quality_score, is_insightful, is_controversial
            FROM comment_analyses 
            WHERE hn_id = ?
            ORDER BY quality_score DESC, is_insightful DESC
        ''', (hn_id,))
        
        analyzed_comments = []
        for row in cursor.fetchall():
            comment = {
                'comment_id': row[0],
                'author': row[1],
                'comment_text': row[2],
                'analysis_summary': row[3],
                'key_points': row[4],
                'sentiment': row[5],
                'quality_score': row[6] or 0,
                'is_insightful': bool(row[7]),
                'is_controversial': bool(row[8])
            }
            analyzed_comments.append(comment)
        
        article['analyzed_comments'] = analyzed_comments
        
        # Get enhanced comments with threading
        cursor.execute('''
            SELECT source, source_id, author, comment_text, score, depth, parent_id,
                   timestamp, quality_score, sentiment, is_insightful, is_controversial
            FROM enhanced_comments
            WHERE article_hn_id = ?
            ORDER BY depth ASC, score DESC
            LIMIT 100
        ''', (hn_id,))
        
        enhanced_comments = []
        for row in cursor.fetchall():
            comment = {
                'source': row[0],
                'source_id': row[1],
                'author': row[2],
                'comment_text': row[3],
                'score': row[4] or 0,
                'depth': row[5] or 0,
                'parent_id': row[6],
                'timestamp': row[7],
                'quality_score': row[8] or 0,
                'sentiment': row[9],
                'is_insightful': bool(row[10]),
                'is_controversial': bool(row[11])
            }
            enhanced_comments.append(comment)
        
        article['enhanced_comments'] = enhanced_comments
        
        # Get discussion threads
        cursor.execute('''
            SELECT thread_summary, main_debate_points, participant_count,
                   thread_quality_score, is_featured_discussion
            FROM discussion_threads
            WHERE hn_id = ?
        ''', (hn_id,))
        
        thread_row = cursor.fetchone()
        if thread_row:
            article['discussion_thread'] = {
                'thread_summary': thread_row[0],
                'main_debate_points': thread_row[1],
                'participant_count': thread_row[2] or 0,
                'thread_quality_score': thread_row[3] or 0,
                'is_featured_discussion': bool(thread_row[4])
            }
        
        # Get Reddit discussions
        cursor.execute('''
            SELECT post_title, subreddit, reddit_url, post_score, num_comments
            FROM reddit_discussions
            WHERE article_hn_id = ?
            ORDER BY post_score DESC
        ''', (hn_id,))
        
        reddit_discussions = []
        for row in cursor.fetchall():
            discussion = {
                'post_title': row[0],
                'subreddit': row[1],
                'reddit_url': row[2],
                'post_score': row[3] or 0,
                'num_comments': row[4] or 0
            }
            reddit_discussions.append(discussion)
        
        article['reddit_discussions'] = reddit_discussions
        
        # Get enhanced summaries
        cursor.execute('''
            SELECT source_type, summary_text, key_points, credibility_score
            FROM enhanced_summaries
            WHERE article_hn_id = ?
            ORDER BY created_at DESC
            LIMIT 3
        ''', (hn_id,))
        
        enhanced_summaries = []
        for row in cursor.fetchall():
            summary = {
                'source_type': row[0],
                'summary_text': row[1],
                'key_points': row[2],
                'credibility_score': row[3] or 0
            }
            enhanced_summaries.append(summary)
        
        article['enhanced_summaries'] = enhanced_summaries
        
        conn.close()
        return article
    
    def get_curated_comments(self, limit: int = 10) -> List[Dict]:
        """Get curated comments from the smart enhancement system."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if curated_comments table exists and has data
        cursor.execute('''
            SELECT cc.id, cc.article_hn_id, cc.author, cc.comment_text, cc.why_selected,
                   cc.insight_type, cc.quality_score, aa.title, aa.domain
            FROM curated_comments cc
            JOIN article_analyses aa ON cc.article_hn_id = aa.hn_id
            ORDER BY cc.quality_score DESC
            LIMIT ?
        ''', (limit,))
        
        curated = []
        for row in cursor.fetchall():
            comment = {
                'id': row[0],
                'article_hn_id': row[1],
                'author': row[2],
                'comment_text': row[3],
                'why_selected': row[4],
                'insight_type': row[5],
                'quality_score': row[6] or 0,
                'article_title': row[7],
                'article_domain': row[8]
            }
            curated.append(comment)
        
        conn.close()
        return curated
    
    def get_stats_with_analysis(self) -> Dict:
        """Get comprehensive statistics from all database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Basic counts
        cursor.execute('SELECT COUNT(*) FROM article_analyses')
        stats['total_articles'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM comment_analyses')
        stats['analyzed_comments'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM enhanced_comments')
        stats['total_comments'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM discussion_threads')
        stats['discussion_threads'] = cursor.fetchone()[0]
        
        # Quality metrics
        cursor.execute('SELECT AVG(discussion_quality_score) FROM article_analyses WHERE discussion_quality_score IS NOT NULL')
        result = cursor.fetchone()[0]
        stats['avg_discussion_quality'] = round(result, 2) if result else 0
        
        cursor.execute('SELECT AVG(quality_score) FROM comment_analyses WHERE quality_score IS NOT NULL')
        result = cursor.fetchone()[0]
        stats['avg_comment_quality'] = round(result, 2) if result else 0
        
        # Sentiment distribution
        cursor.execute('SELECT sentiment_analysis, COUNT(*) FROM article_analyses GROUP BY sentiment_analysis')
        sentiment_dist = {}
        for row in cursor.fetchall():
            sentiment_dist[row[0] or 'neutral'] = row[1]
        stats['sentiment_distribution'] = sentiment_dist
        
        # Controversy levels
        cursor.execute('SELECT controversy_level, COUNT(*) FROM article_analyses GROUP BY controversy_level')
        controversy_dist = {}
        for row in cursor.fetchall():
            controversy_dist[row[0] or 'low'] = row[1]
        stats['controversy_distribution'] = controversy_dist
        
        # Top domains
        cursor.execute('SELECT domain, COUNT(*) as count FROM article_analyses GROUP BY domain ORDER BY count DESC LIMIT 10')
        stats['top_domains'] = [{'domain': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Insightful vs controversial comments
        cursor.execute('SELECT COUNT(*) FROM comment_analyses WHERE is_insightful = 1')
        stats['insightful_comments'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM comment_analyses WHERE is_controversial = 1')
        stats['controversial_comments'] = cursor.fetchone()[0]
        
        # Source distribution for enhanced comments
        cursor.execute('SELECT source, COUNT(*) FROM enhanced_comments GROUP BY source')
        source_dist = {}
        for row in cursor.fetchall():
            source_dist[row[0]] = row[1]
        stats['comment_sources'] = source_dist
        
        conn.close()
        return stats
    
    def search_comprehensive(self, query: str, domain: str = None) -> List[Dict]:
        """Search across all database tables for comprehensive results."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        search_term = f'%{query}%'
        results = []
        
        # Build the WHERE clause for domain filtering
        domain_filter = ""
        params = [search_term, search_term, search_term]
        
        if domain:
            domain_filter = " AND aa.domain = ?"
            params.append(domain)
        
        # Search articles with analysis
        cursor.execute(f'''
            SELECT aa.hn_id, aa.title, aa.url, aa.domain, aa.summary, aa.key_insights,
                   aa.main_themes, aa.sentiment_analysis, aa.discussion_quality_score,
                   aa.controversy_level, COUNT(DISTINCT ca.comment_id) as analyzed_comments
            FROM article_analyses aa
            LEFT JOIN comment_analyses ca ON aa.hn_id = ca.hn_id
            WHERE (aa.title LIKE ? OR aa.summary LIKE ? OR aa.key_insights LIKE ?)
            {domain_filter}
            GROUP BY aa.hn_id
            ORDER BY aa.discussion_quality_score DESC
            LIMIT 50
        ''', params)
        
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
                'analyzed_comments': row[10] or 0
            }
            results.append(article)
        
        conn.close()
        return results

# Initialize database manager
db_manager = DatabaseManager(DB_PATH)

# Global storage for fallback to JSON if database is unavailable
articles_data = []
domains = set()

# Core utility functions (defined early to ensure availability)
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

# Import analyzer functionality
analyzer_path = os.path.join(os.path.dirname(__file__), '..', 'analyzers')
sys.path.insert(0, analyzer_path)

# Initialize analyzer availability flags
CURATOR_AVAILABLE = False
ANALYZER_AVAILABLE = False
CommentCurator = None
ConversationAnalyzer = None

try:
    # Try to import comment curator (requires OpenAI dependencies)
    import comment_curator
    CommentCurator = comment_curator.CommentCurator
    CURATOR_AVAILABLE = True
    print("✅ Comment curator loaded successfully")
except ImportError as e:
    print(f"⚠️  Comment curator not available (requires OpenAI dependencies): {e}")
except Exception as e:
    print(f"⚠️  Error loading comment curator: {e}")

try:
    # Import conversation analyzer (basic analysis, no external deps)
    import conversation_analyzer
    ConversationAnalyzer = conversation_analyzer.ConversationAnalyzer
    ANALYZER_AVAILABLE = True
    print("✅ Conversation analyzer loaded successfully")
except ImportError as e:
    print(f"⚠️  Conversation analyzer not available: {e}")
except Exception as e:
    print(f"⚠️  Error loading conversation analyzer: {e}")


def load_articles() -> None:
    """Load articles from database with fallback to JSON file."""
    global articles_data, domains
    
    try:
        # Try to load from database first
        articles_data = db_manager.get_all_articles_with_analysis()
        
        # Extract domains from database articles
        domains = set()
        for article in articles_data:
            if article.get('domain'):
                domains.add(article['domain'])
        
        print(f"Loaded {len(articles_data)} analyzed articles from {len(domains)} domains (database)")
        
        # If database is empty, fall back to JSON
        if not articles_data:
            raise Exception("No articles in database, falling back to JSON")
            
    except Exception as e:
        print(f"Database unavailable ({e}), falling back to JSON file...")
        
        json_file = os.environ.get('JSON_OUTPUT', 'enhanced_hn_articles.json')
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        json_path = os.path.join(project_root, 'data', json_file)
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_articles = json.load(f)
                
            # Convert JSON format to match database format
            articles_data = []
            domains = set()
            
            for article in json_articles:
                # Extract domain
                domain = ""
                if article.get('url'):
                    extracted = tldextract.extract(article['url'])
                    domain = f"{extracted.domain}.{extracted.suffix}"
                    if domain != ".":
                        domains.add(domain)
                
                # Convert to database-like format
                converted_article = {
                    'hn_id': article.get('hn_id', str(hash(article.get('title', '')))),
                    'title': article.get('title', 'Unknown Title'),
                    'url': article.get('url', ''),
                    'domain': domain,
                    'summary': 'Article from JSON source (no AI analysis available)',
                    'key_insights': 'Manual review required',
                    'main_themes': 'technology, discussion',
                    'sentiment_analysis': 'neutral',
                    'discussion_quality_score': len(article.get('comments', [])) // 10 + 1,
                    'controversy_level': 'low',
                    'analyzed_comments': 0,
                    'total_comments': count_comments_recursive(article.get('comments', [])),
                    'avg_comment_quality': 0
                }
                articles_data.append(converted_article)
                
            print(f"Loaded {len(articles_data)} articles from {len(domains)} domains (JSON fallback)")
            
        except FileNotFoundError:
            print(f"Warning: {json_path} not found. Run the scraper first.")
            articles_data = []
            domains = set()
        except json.JSONDecodeError as e:
            print(f"Error loading JSON: {e}")
            articles_data = []
            domains = set()


def filter_articles(search_query: Optional[str] = None, 
                   domain_filter: Optional[str] = None,
                   min_content_length: int = 0) -> List[Dict]:
    """Filter articles based on search criteria."""
    filtered = articles_data.copy()
    
    if search_query:
        search_lower = search_query.lower()
        filtered = [
            article for article in filtered
            if (search_lower in (article.get('title') or '').lower() or
                search_lower in (article.get('content') or '').lower())
        ]
    
    if domain_filter and domain_filter != 'all':
        filtered = [
            article for article in filtered
            if article.get('domain') == domain_filter
        ]
    
    if min_content_length > 0:
        filtered = [
            article for article in filtered
            if len(article.get('content') or '') >= min_content_length
        ]
    
    return filtered


def get_statistics():
    """Calculate comprehensive dataset statistics from database and fallback data."""
    try:
        # Try to get comprehensive stats from database
        db_stats = db_manager.get_stats_with_analysis()
        if db_stats and db_stats.get('total_articles', 0) > 0:
            return db_stats
    except Exception as e:
        print(f"Error getting database stats: {e}")
    
    # Fallback to basic stats from loaded articles
    if not articles_data:
        return {}
    
    total_articles = len(articles_data)
    total_domains = len(domains)
    
    # For database articles, use the analysis data
    if articles_data and 'discussion_quality_score' in articles_data[0]:
        # Database-sourced articles
        total_comments = sum(article.get('total_comments', 0) for article in articles_data)
        analyzed_comments = sum(article.get('analyzed_comments', 0) for article in articles_data)
        avg_discussion_quality = sum(article.get('discussion_quality_score', 0) for article in articles_data) / total_articles
        avg_comment_quality = sum(article.get('avg_comment_quality', 0) for article in articles_data) / total_articles
        
        # Domain distribution
        domain_counts = {}
        for article in articles_data:
            domain = article.get('domain', 'unknown')
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        return {
            'total_articles': total_articles,
            'total_domains': total_domains,
            'total_comments': total_comments,
            'analyzed_comments': analyzed_comments,
            'avg_discussion_quality': round(avg_discussion_quality, 2),
            'avg_comment_quality': round(avg_comment_quality, 2),
            'top_domains': [{'domain': k, 'count': v} for k, v in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]]
        }
    else:
        # JSON-sourced articles (legacy format)
        content_lengths = [len(article.get('content') or '') for article in articles_data]
        avg_content_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        
        total_comments = 0
        articles_with_comments = 0
        for article in articles_data:
            comments = article.get('comments', [])
            if comments:
                articles_with_comments += 1
                total_comments += count_comments_recursive(comments)
        
        domain_counts = {}
        for article in articles_data:
            domain = article.get('domain', 'unknown')
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        return {
            'total_articles': total_articles,
            'total_domains': total_domains,
            'total_comments': total_comments,
            'articles_with_comments': articles_with_comments,
            'avg_content_length': round(avg_content_length, 2),
            'avg_comments_per_article': round(total_comments / articles_with_comments if articles_with_comments else 0, 1),
            'top_domains': [{'domain': k, 'count': v} for k, v in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]]
        }


def render_comment_tree(comments, max_depth=3, current_depth=0):
    """Render comment tree as HTML."""
    if current_depth >= max_depth or not comments:
        return ""
    
    html = "<div class='comment-tree ml-4'>"
    for comment in comments[:10]:  # Limit to first 10 comments at each level
        html += f"""
        <div class='comment mb-3 p-3 bg-gray-50 dark:bg-gray-800 rounded border-l-2 border-blue-200'>
            <div class='comment-meta text-xs text-gray-500 mb-2'>
                <span class='author font-medium'>{comment.get('by', 'Anonymous')}</span>
                <span class='time ml-2'>{datetime.fromtimestamp(comment.get('time', 0)).strftime('%Y-%m-%d %H:%M') if comment.get('time') else 'Unknown time'}</span>
            </div>
            <div class='comment-text text-sm text-gray-700 dark:text-gray-300'>
                {(comment.get('text') or 'No content')[:300]}{'...' if len(comment.get('text') or '') > 300 else ''}
            </div>
            {render_comment_tree(comment.get('replies', []), max_depth, current_depth + 1)}
        </div>
        """
    
    if len(comments) > 10:
        html += f"<div class='text-xs text-gray-500 italic'>... and {len(comments) - 10} more comments</div>"
    
    html += "</div>"
    return html


def categorize_articles():
    """Categorize articles for different sections."""
    if not articles_data:
        return {
            'featured': None,
            'trending': [],
            'quality': [],
            'latest': [],
            'by_domain': {}
        }
    
    # Calculate comment counts for sorting
    for article in articles_data:
        article['comment_count_calculated'] = count_comments_recursive(article.get('comments', []))
    
    # Featured article (most comments)
    featured = max(articles_data, key=lambda x: x['comment_count_calculated'])
    
    # Trending (high comment count, good engagement)
    trending = sorted(articles_data, key=lambda x: x['comment_count_calculated'], reverse=True)[:12]
    
    # Quality discussions (articles with substantial comments and content)
    # Debug this part
    quality = []
    for article in articles_data:
        try:
            if (article['comment_count_calculated'] >= 10 and 
                len(article.get('content') or '') >= 500):
                quality.append(article)
                if len(quality) >= 8:
                    break
        except Exception as e:
            print(f"Error processing article {article.get('hn_id', 'unknown')}: {e}")
            print(f"Content type: {type(article.get('content'))}")
            print(f"Content value: {repr(article.get('content'))[:100]}")
            continue
    
    # Latest (most recent by ID)
    latest = sorted(articles_data, key=lambda x: int(x.get('hn_id', '0')), reverse=True)[:15]
    
    # By domain
    from collections import defaultdict
    by_domain = defaultdict(list)
    for article in articles_data:
        domain = article.get('domain', 'unknown')
        by_domain[domain].append(article)
    
    # Sort domains by article count and take top domains
    sorted_domains = dict(sorted(by_domain.items(), key=lambda x: len(x[1]), reverse=True)[:12])
    
    return {
        'featured': featured,
        'trending': trending,
        'quality': quality,
        'latest': latest,
        'by_domain': sorted_domains
    }


def get_article_by_hn_id(hn_id):
    """Get article by HN ID."""
    for article in articles_data:
        if article.get('hn_id') == hn_id:
            return article
    return None


# Add OpenAI for chat functionality
from openai import OpenAI

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY')) if os.environ.get('OPENAI_API_KEY') else None

def generate_chat_response(article, message, chat_history):
    """Generate GPT response for article discussion."""
    if not openai_client:
        return "I'm sorry, but the chat functionality requires OpenAI API configuration."
    
    try:
        # Prepare article context
        article_context = f"""
        Article Title: {article.get('title', 'Unknown')}
        URL: {article.get('url', 'Unknown')}
        Domain: {article.get('domain', 'Unknown')}
        Content: {article.get('content', 'No content available')[:2000]}
        Comment Count: {count_comments_recursive(article.get('comments', []))}
        """
        
        # Prepare comments context
        comments_text = ""
        if article.get('comments'):
            comments_text = "\\n\\nTop Comments:\\n"
            for i, comment in enumerate(article['comments'][:5]):
                comments_text += f"Comment {i+1} by {comment.get('author', 'Anonymous')}: {comment.get('text', '')[:300]}\\n\\n"
        
        # System prompt
        system_prompt = f"""You are an intelligent assistant helping users explore and discuss a Hacker News article. 

        Article Information:
        {article_context}
        {comments_text}
        
        You should:
        1. Provide insightful analysis of the article content
        2. Reference specific comments when relevant
        3. Help users understand different perspectives from the discussion
        4. Answer questions about technical concepts mentioned
        5. Highlight interesting debates or consensus from the comments
        6. Be conversational but informative
        7. Cite specific comments or parts of the article when making points
        
        Keep responses focused, helpful, and engaging. If asked about something not covered in the article or comments, say so clearly."""
        
        # Prepare messages for OpenAI
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add chat history
        for msg in chat_history[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Generate response using the new API
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error generating chat response: {e}")
        return "I encountered an error generating a response. Please try again."


@app.route('/')
def index():
    """Enhanced AI-powered homepage with comprehensive database utilization."""
    # Get filter parameters
    search_query = request.args.get('search', '')
    domain_filter = request.args.get('domain', 'all')
    view_mode = request.args.get('view', 'cards')
    sort_by = request.args.get('sort', 'quality')
    
    try:
        # Get comprehensive articles with AI analysis
        articles_data = db_manager.get_all_articles_with_analysis()
        
        # Apply search filter
        if search_query:
            search_results = db_manager.search_comprehensive(search_query, domain_filter if domain_filter != 'all' else None)
            articles_data = search_results
        elif domain_filter and domain_filter != 'all':
            articles_data = [a for a in articles_data if a.get('domain') == domain_filter]
        
        # Sort articles based on selection
        if sort_by == 'quality':
            articles_data.sort(key=lambda x: x.get('discussion_quality_score', 0), reverse=True)
        elif sort_by == 'comments':
            articles_data.sort(key=lambda x: x.get('total_comments', 0), reverse=True)
        elif sort_by == 'recent':
            articles_data.sort(key=lambda x: x.get('hn_id', '0'), reverse=True)
        elif sort_by == 'controversial':
            articles_data.sort(key=lambda x: (x.get('controversy_level') == 'high', x.get('discussion_quality_score', 0)), reverse=True)
        
        # Get comprehensive statistics
        stats = db_manager.get_stats_with_analysis()
        
        # Get all available domains
        available_domains = list(set(a.get('domain', '') for a in articles_data if a.get('domain')))
        available_domains.sort()
        
        # Limit to first 50 articles for performance
        articles_data = articles_data[:50]
        
    except Exception as e:
        print(f"Database error, falling back to classic view: {e}")
        from flask import redirect
        return redirect('/classic')
    
    return render_template('index.html',
                         articles=articles_data,
                         domains=available_domains,
                         search_query=search_query,
                         domain_filter=domain_filter,
                         sort_by=sort_by,
                         view_mode=view_mode,
                         stats=stats,
                         curator_available=CURATOR_AVAILABLE,
                         analyzer_available=ANALYZER_AVAILABLE)


@app.route('/classic')
def classic_view():
    """Original unified homepage with all functionalities."""
    # Get filter parameters
    search_query = request.args.get('search', '')
    domain_filter = request.args.get('domain', 'all')
    min_length = int(request.args.get('min_length', 0))
    view_mode = request.args.get('view', 'cards')  # cards, list, stats
    
    # Filter articles
    filtered_articles = filter_articles(search_query, domain_filter, min_length)
    
    # Sort articles
    sort_by = request.args.get('sort', 'content_length')
    if sort_by == 'content_length':
        filtered_articles.sort(key=lambda x: len(x.get('content') or ''), reverse=True)
    elif sort_by == 'title':
        filtered_articles.sort(key=lambda x: (x.get('title') or '').lower())
    elif sort_by == 'domain':
        filtered_articles.sort(key=lambda x: x.get('domain') or '')
    elif sort_by == 'comments':
        filtered_articles.sort(key=lambda x: count_comments_recursive(x.get('comments', [])), reverse=True)
    
    # Get statistics
    stats = get_statistics()
    
    return render_template('index.html',
                         articles=filtered_articles,
                         domains=sorted(domains),
                         search_query=search_query,
                         domain_filter=domain_filter,
                         min_length=min_length,
                         sort_by=sort_by,
                         view_mode=view_mode,
                         total_articles=len(articles_data),
                         stats=stats,
                         curator_available=CURATOR_AVAILABLE,
                         analyzer_available=ANALYZER_AVAILABLE,
                         render_comment_tree=render_comment_tree,
                         count_comments_recursive=count_comments_recursive)


@app.route('/api/articles')
def api_articles():
    """API endpoint for articles data."""
    search_query = request.args.get('search', '')
    domain_filter = request.args.get('domain', 'all')
    min_length = int(request.args.get('min_length', 0))
    
    filtered_articles = filter_articles(search_query, domain_filter, min_length)
    
    return jsonify({
        'articles': filtered_articles,
        'total': len(filtered_articles),
        'total_available': len(articles_data)
    })


@app.route('/api/stats')
def api_stats():
    """API endpoint for comprehensive statistics."""
    try:
        stats = db_manager.get_stats_with_analysis()
        return jsonify(stats)
    except Exception as e:
        print(f"Error getting comprehensive stats: {e}")
        # Fallback to basic stats
        return jsonify(get_statistics())


@app.route('/api/article/<hn_id>')
def api_article_detail(hn_id):
    """API endpoint for comprehensive article detail."""
    try:
        article = db_manager.get_article_detail_with_analysis(hn_id)
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        return jsonify(article)
    except Exception as e:
        print(f"Error getting article detail: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/comments/curated')
def api_curated_comments():
    """API endpoint for curated comments."""
    try:
        limit = int(request.args.get('limit', 10))
        curated = db_manager.get_curated_comments(limit)
        return jsonify(curated)
    except Exception as e:
        print(f"Error getting curated comments: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/search/comprehensive')
def api_comprehensive_search():
    """API endpoint for comprehensive search across all data."""
    try:
        query = request.args.get('q', '')
        domain = request.args.get('domain', '')
        
        if not query:
            return jsonify([])
        
        results = db_manager.search_comprehensive(query, domain)
        return jsonify(results)
    except Exception as e:
        print(f"Error in comprehensive search: {e}")
        return jsonify({'error': 'Search failed'}), 500


@app.route('/api/analysis/summary')
def api_analysis_summary():
    """API endpoint for analysis summary across all content."""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get summary metrics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_articles,
                AVG(discussion_quality_score) as avg_quality,
                COUNT(CASE WHEN controversy_level = 'high' THEN 1 END) as high_controversy,
                COUNT(CASE WHEN controversy_level = 'medium' THEN 1 END) as medium_controversy,
                COUNT(CASE WHEN controversy_level = 'low' THEN 1 END) as low_controversy
            FROM article_analyses
        ''')
        
        article_summary = cursor.fetchone()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_comments,
                COUNT(CASE WHEN is_insightful = 1 THEN 1 END) as insightful,
                COUNT(CASE WHEN is_controversial = 1 THEN 1 END) as controversial,
                AVG(quality_score) as avg_quality
            FROM comment_analyses
        ''')
        
        comment_summary = cursor.fetchone()
        
        cursor.execute('''
            SELECT source, COUNT(*) as count
            FROM enhanced_comments 
            GROUP BY source
        ''')
        
        source_breakdown = dict(cursor.fetchall())
        
        conn.close()
        
        return jsonify({
            'articles': {
                'total': article_summary[0],
                'avg_quality': round(article_summary[1] or 0, 2),
                'controversy': {
                    'high': article_summary[2],
                    'medium': article_summary[3],
                    'low': article_summary[4]
                }
            },
            'comments': {
                'total_analyzed': comment_summary[0],
                'insightful': comment_summary[1],
                'controversial': comment_summary[2],
                'avg_quality': round(comment_summary[3] or 0, 2)
            },
            'sources': source_breakdown
        })
        
    except Exception as e:
        print(f"Error getting analysis summary: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/insights/trending')
def api_trending_insights():
    """API endpoint for trending insights and discussions."""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get trending articles (high quality discussions)
        cursor.execute('''
            SELECT aa.hn_id, aa.title, aa.domain, aa.discussion_quality_score,
                   COUNT(ca.comment_id) as analyzed_comments
            FROM article_analyses aa
            LEFT JOIN comment_analyses ca ON aa.hn_id = ca.hn_id
            WHERE aa.discussion_quality_score >= 6
            GROUP BY aa.hn_id
            ORDER BY aa.discussion_quality_score DESC, analyzed_comments DESC
            LIMIT 10
        ''')
        
        trending_articles = []
        for row in cursor.fetchall():
            trending_articles.append({
                'hn_id': row[0],
                'title': row[1],
                'domain': row[2],
                'quality_score': row[3],
                'analyzed_comments': row[4]
            })
        
        # Get top insights from comments
        cursor.execute('''
            SELECT ca.comment_id, ca.hn_id, ca.author, ca.analysis_summary,
                   ca.quality_score, aa.title
            FROM comment_analyses ca
            JOIN article_analyses aa ON ca.hn_id = aa.hn_id
            WHERE ca.is_insightful = 1 AND ca.quality_score >= 7
            ORDER BY ca.quality_score DESC
            LIMIT 10
        ''')
        
        top_insights = []
        for row in cursor.fetchall():
            top_insights.append({
                'comment_id': row[0],
                'hn_id': row[1],
                'author': row[2],
                'analysis_summary': row[3],
                'quality_score': row[4],
                'article_title': row[5]
            })
        
        conn.close()
        
        return jsonify({
            'trending_articles': trending_articles,
            'top_insights': top_insights
        })
        
    except Exception as e:
        print(f"Error getting trending insights: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/domains')
def api_domains():
    """API endpoint for domain statistics."""
    try:
        # Try to get domain stats from database
        stats = db_manager.get_stats_with_analysis()
        if stats and 'top_domains' in stats:
            return jsonify(stats['top_domains'])
    except Exception as e:
        print(f"Error getting domain stats from database: {e}")
    
    # Fallback to calculating from loaded articles
    domain_stats = {}
    for article in articles_data:
        domain = article.get('domain', 'unknown')
        if domain not in domain_stats:
            domain_stats[domain] = {
                'count': 0,
                'total_comments': 0,
                'avg_content_length': 0,
                'content_lengths': []
            }
        
        domain_stats[domain]['count'] += 1
        domain_stats[domain]['total_comments'] += count_comments_recursive(article.get('comments', []))
        content_length = len(article.get('content') or '')
        domain_stats[domain]['content_lengths'].append(content_length)
    
    # Calculate averages
    for domain, stats in domain_stats.items():
        if stats['content_lengths']:
            stats['avg_content_length'] = sum(stats['content_lengths']) // len(stats['content_lengths'])
        del stats['content_lengths']  # Remove raw data
    
    return jsonify(domain_stats)


@app.route('/chat/article/<article_id>', methods=['POST'])
def chat_with_article(article_id):
    """Chat with GPT about a specific article."""
    try:
        data = request.get_json()
        message = data.get('message', '')
        history = data.get('history', [])
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Try to get comprehensive article data from database first
        article = db_manager.get_article_detail_with_analysis(article_id)
        if not article:
            # Fallback to JSON data
            article = get_article_by_hn_id(article_id)
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Generate response
        response = generate_chat_response(article, message, history)
        
        return jsonify({
            'response': response,
            'article_title': article.get('title', 'Unknown')
        })
        
    except Exception as e:
        print(f"Chat API error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/search', methods=['POST'])
def search():
    """Search articles."""
    try:
        data = request.get_json()
        query = data.get('query', '').lower()
        domain = data.get('domain', '')
        sort_by = data.get('sort', 'relevance')
        
        if not query:
            return jsonify([])
        
        # Filter articles
        results = []
        for article in articles_data:
            title = article.get('title', '').lower()
            content = article.get('content', '').lower()
            article_domain = article.get('domain', '')
            
            # Check if query matches
            if query in title or query in content:
                # Check domain filter
                if not domain or domain == article_domain:
                    results.append(article)
        
        # Sort results
        if sort_by == 'comments':
            results.sort(key=lambda x: count_comments_recursive(x.get('comments', [])), reverse=True)
        elif sort_by == 'recent':
            results.sort(key=lambda x: int(x.get('hn_id', '0')), reverse=True)
        # Default is relevance (already filtered by match)
        
        return jsonify(results[:20])  # Limit to 20 results
        
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': 'Search failed'}), 500


@app.route('/stats')
def stats():
    """Statistics dashboard."""
    stats = get_statistics()
    categories = categorize_articles()
    
    return render_template('index.html',
                         view_mode='stats',
                         stats=stats,
                         articles=articles_data,
                         domains=sorted(domains),
                         categories=categories,
                         total_articles=len(articles_data),
                         curator_available=CURATOR_AVAILABLE,
                         analyzer_available=ANALYZER_AVAILABLE,
                         render_comment_tree=render_comment_tree)


@app.route('/article/<hn_id>')
def article_detail(hn_id):
    """Individual article view with comprehensive analysis and comments."""
    try:
        # Try to get comprehensive article data from database
        article = db_manager.get_article_detail_with_analysis(hn_id)
        
        if not article:
            # Fallback to JSON data
            article = get_article_by_hn_id(hn_id)
            if not article:
                return render_template('404.html'), 404
        
        # Calculate additional metrics
        if 'total_comments' not in article:
            article['total_comments'] = count_comments_recursive(article.get('comments', []))
        
        if 'content_length' not in article:
            article['content_length'] = len(article.get('content') or '')
        
        # Show comprehensive article view
        return render_template('index.html',
                             view_mode='article_detail',
                             articles=[article],
                             article=article,  # For detailed view
                             stats=get_statistics(),
                             domains=sorted(domains),
                             search_query='',
                             domain_filter='all',
                             render_comment_tree=render_comment_tree,
                             curator_available=CURATOR_AVAILABLE,
                             analyzer_available=ANALYZER_AVAILABLE)
    
    except Exception as e:
        print(f"Error loading article {hn_id}: {e}")
        return render_template('500.html'), 500


@app.route('/curate')
def curate():
    """Comment curation interface."""
    return render_template('index.html',
                         view_mode='curator',
                         articles=articles_data[:20],  # Show first 20 articles for curation
                         stats=get_statistics(),
                         domains=sorted(domains),
                         total_articles=len(articles_data),
                         render_comment_tree=render_comment_tree,
                         curator_available=CURATOR_AVAILABLE,
                         analyzer_available=ANALYZER_AVAILABLE)


@app.route('/overview')
def overview():
    """Project overview and documentation."""
    stats = get_statistics()
    
    return render_template('index.html',
                         view_mode='stats',  # Use stats view for overview
                         stats=stats,
                         articles=articles_data,
                         domains=sorted(domains),
                         total_articles=len(articles_data),
                         render_comment_tree=render_comment_tree,
                         curator_available=CURATOR_AVAILABLE,
                         analyzer_available=ANALYZER_AVAILABLE)


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for conversation analysis of article content."""
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        if not content:
            return jsonify({'success': False, 'error': 'No content provided'})
        
        # Basic conversation analysis using the analyzer if available
        if ANALYZER_AVAILABLE and ConversationAnalyzer:
            try:
                # Create analyzer instance and analyze content
                analyzer_instance = ConversationAnalyzer()
                analysis_result = analyzer_instance.analyze_text(content[:2000])  # Limit content length
                
                if analysis_result and 'patterns' in analysis_result:
                    patterns = analysis_result['patterns']
                    conversation_analysis = []
                    
                    for pattern in patterns[:5]:  # Limit to 5 patterns
                        conversation_analysis.append({
                            'pattern': pattern.get('type', 'Unknown pattern'),
                            'confidence': pattern.get('confidence', 0.5),
                            'description': pattern.get('description', 'Analysis pattern detected'),
                            'participants': pattern.get('participants', [])
                        })
                    
                    return jsonify({
                        'success': True,
                        'analysis': conversation_analysis
                    })
            except Exception as e:
                print(f"Analyzer error: {e}")
        
        # Fallback: Basic keyword-based analysis
        fallback_analysis = []
        content_lower = content.lower()
        
        # Simple pattern detection
        if any(word in content_lower for word in ['discussion', 'debate', 'argument']):
            fallback_analysis.append({
                'pattern': 'Discussion Pattern',
                'confidence': 0.7,
                'description': 'Content contains discussion-related keywords',
                'participants': ['multiple']
            })
        
        if any(word in content_lower for word in ['question', 'answer', 'reply']):
            fallback_analysis.append({
                'pattern': 'Q&A Pattern',
                'confidence': 0.6,
                'description': 'Content shows question and answer dynamics',
                'participants': ['questioner', 'responder']
            })
        
        if any(word in content_lower for word in ['opinion', 'think', 'believe', 'view']):
            fallback_analysis.append({
                'pattern': 'Opinion Exchange',
                'confidence': 0.5,
                'description': 'Content contains opinion-based language',
                'participants': ['opinion holders']
            })
        
        return jsonify({
            'success': True,
            'analysis': fallback_analysis
        })
        
    except Exception as e:
        print(f"Analysis API error: {e}")
        return jsonify({'success': False, 'error': 'Analysis failed'})


# AI-Powered API Endpoints for Enhanced Homepage

@app.route('/api/trigger-scrape', methods=['POST'])
def api_trigger_scrape():
    """Trigger daily scrape via API."""
    try:
        # Import and run the daily scraper
        import subprocess
        import os
        
        scraper_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scrapers', 'daily_enhanced_scraper.py')
        if os.path.exists(scraper_path):
            # Run scraper in background
            subprocess.Popen(['python', scraper_path], cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            return jsonify({'success': True, 'message': 'Daily scrape triggered successfully'})
        else:
            return jsonify({'success': False, 'message': 'Daily scraper not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error triggering scrape: {str(e)}'})

@app.route('/api/articles/trending')
def api_trending_articles():
    """Get trending articles based on AI analysis."""
    try:
        articles = db_manager.get_all_articles_with_analysis()
        
        # Sort by combination of quality score and comment count
        trending = sorted(articles, 
                         key=lambda x: (x.get('discussion_quality_score', 0) * 0.7 + 
                                      min(x.get('total_comments', 0) / 100, 10) * 0.3), 
                         reverse=True)[:10]
        
        return jsonify({
            'success': True,
            'articles': trending
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/insights/summary')
def api_insights_summary():
    """Get AI-powered insights summary."""
    try:
        stats = db_manager.get_stats_with_analysis()
        articles = db_manager.get_all_articles_with_analysis()
        
        # Generate insights
        insights = {
            'total_articles': stats.get('total_articles', 0),
            'quality_trends': {
                'high_quality': len([a for a in articles if a.get('discussion_quality_score', 0) >= 7]),
                'medium_quality': len([a for a in articles if 4 <= a.get('discussion_quality_score', 0) < 7]),
                'low_quality': len([a for a in articles if a.get('discussion_quality_score', 0) < 4])
            },
            'sentiment_overview': stats.get('sentiment_distribution', {}),
            'top_themes': {},  # Could be enhanced with AI analysis
            'engagement_metrics': {
                'avg_comments_per_article': stats.get('total_comments', 0) / max(stats.get('total_articles', 1), 1),
                'ai_analysis_coverage': (stats.get('analyzed_comments', 0) / max(stats.get('total_comments', 1), 1)) * 100
            }
        }
        
        return jsonify({
            'success': True,
            'insights': insights
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/curated/highlights')
def api_curated_highlights():
    """Get curated highlights from AI analysis."""
    try:
        curated = db_manager.get_curated_comments(limit=5)
        
        highlights = []
        for comment in curated:
            highlights.append({
                'comment_id': comment['id'],
                'article_title': comment['article_title'],
                'author': comment['author'],
                'insight_type': comment['insight_type'],
                'quality_score': comment['quality_score'],
                'preview': comment['comment_text'][:200] + '...' if len(comment['comment_text']) > 200 else comment['comment_text'],
                'why_selected': comment['why_selected']
            })
        
        return jsonify({
            'success': True,
            'highlights': highlights
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analytics/real-time')
def api_real_time_analytics():
    """Get real-time analytics for dashboard."""
    try:
        stats = db_manager.get_stats_with_analysis()
        
        # Calculate additional metrics
        articles = db_manager.get_all_articles_with_analysis()
        
        real_time_data = {
            'metrics': {
                'total_articles': stats.get('total_articles', 0),
                'total_comments': stats.get('total_comments', 0),
                'analyzed_comments': stats.get('analyzed_comments', 0),
                'avg_quality': stats.get('avg_discussion_quality', 0)
            },
            'charts': {
                'sentiment_distribution': stats.get('sentiment_distribution', {}),
                'controversy_distribution': stats.get('controversy_distribution', {}),
                'quality_histogram': {
                    '0-3': len([a for a in articles if 0 <= a.get('discussion_quality_score', 0) < 3]),
                    '3-6': len([a for a in articles if 3 <= a.get('discussion_quality_score', 0) < 6]),
                    '6-8': len([a for a in articles if 6 <= a.get('discussion_quality_score', 0) < 8]),
                    '8-10': len([a for a in articles if 8 <= a.get('discussion_quality_score', 0) <= 10])
                }
            },
            'top_domains': stats.get('top_domains', [])[:5]
        }
        
        return jsonify({
            'success': True,
            'data': real_time_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/search/smart', methods=['POST'])
def api_smart_search():
    """AI-powered smart search with context understanding."""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'success': False, 'error': 'Query required'})
        
        # Perform comprehensive search
        results = db_manager.search_comprehensive(query)
        
        # Enhance results with AI insights
        enhanced_results = []
        for article in results[:10]:  # Limit to 10 results
            enhanced_results.append({
                'hn_id': article['hn_id'],
                'title': article['title'],
                'url': article['url'],
                'domain': article['domain'],
                'summary': article['summary'],
                'quality_score': article['discussion_quality_score'],
                'sentiment': article['sentiment_analysis'],
                'relevance_score': 0.8,  # Could be enhanced with semantic search
                'key_insights': article['key_insights'],
                'comment_count': article.get('total_comments', 0)
            })
        
        return jsonify({
            'success': True,
            'results': enhanced_results,
            'total_found': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    load_articles()
    port = int(os.environ.get('PORT', 8084))
    print(f"Starting Flask app with {len(articles_data)} articles")
    print(f"Available at: http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
