#!/usr/bin/env python3
"""
Enhanced Multi-Source Discussion Collector
This script will:
1. Expand HN comment collection beyond 10 comments
2. Scrape Reddit discussions for each article
3. Generate proper article summaries
4. Create comprehensive multi-source discussions
5. Update database schema to support multiple sources
"""

import sqlite3
import requests
import time
import re
import json
from urllib.parse import urlparse, quote_plus
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiSourceDiscussionCollector:
    def __init__(self, db_path='data/enhanced_hn_articles.db'):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def setup_enhanced_schema(self):
        """Create enhanced database schema for multi-source discussions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create enhanced comments table with source tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enhanced_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_hn_id TEXT NOT NULL,
                source TEXT NOT NULL,  -- 'hackernews', 'reddit', 'twitter', etc.
                source_id TEXT,        -- Original comment ID from source
                parent_id TEXT,        -- For threading
                author TEXT,
                comment_text TEXT,
                score INTEGER DEFAULT 0,
                timestamp TEXT,
                url TEXT,             -- Link to original comment
                depth INTEGER DEFAULT 0,
                quality_score REAL,
                sentiment TEXT,
                is_insightful BOOLEAN DEFAULT 0,
                is_controversial BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create Reddit discussions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reddit_discussions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_hn_id TEXT NOT NULL,
                reddit_url TEXT,
                subreddit TEXT,
                reddit_post_id TEXT,
                post_title TEXT,
                post_author TEXT,
                post_score INTEGER,
                num_comments INTEGER,
                created_utc INTEGER,
                post_text TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create article summaries table (bringing back summaries)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enhanced_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_hn_id TEXT NOT NULL,
                source_url TEXT,
                summary_text TEXT,
                key_points TEXT,
                source_type TEXT,  -- 'original', 'reddit', 'google_search', etc.
                credibility_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create discussion threads table for better organization
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discussion_threads_enhanced (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_hn_id TEXT NOT NULL,
                source TEXT,
                thread_title TEXT,
                main_topic TEXT,
                participant_count INTEGER,
                total_comments INTEGER,
                avg_quality_score REAL,
                controversy_level REAL,
                sentiment_distribution TEXT,  -- JSON: {"positive": 10, "negative": 5, "neutral": 15}
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Enhanced database schema created successfully")
    
    def search_reddit_discussions(self, article_title, article_url):
        """Search Reddit for discussions about the article."""
        reddit_discussions = []
        
        try:
            # Method 1: Search by title
            search_query = quote_plus(article_title)
            reddit_search_url = f"https://www.reddit.com/search.json?q={search_query}&type=link&limit=10"
            
            response = self.session.get(reddit_search_url)
            if response.status_code == 200:
                data = response.json()
                
                for post in data.get('data', {}).get('children', []):
                    post_data = post['data']
                    reddit_discussions.append({
                        'reddit_url': f"https://www.reddit.com{post_data['permalink']}",
                        'subreddit': post_data['subreddit'],
                        'post_id': post_data['id'],
                        'title': post_data['title'],
                        'author': post_data['author'],
                        'score': post_data['score'],
                        'num_comments': post_data['num_comments'],
                        'created_utc': post_data['created_utc'],
                        'selftext': post_data.get('selftext', '')
                    })
            
            # Method 2: Search by domain if available
            if article_url:
                domain = urlparse(article_url).netloc
                domain_search = quote_plus(f"site:{domain}")
                domain_search_url = f"https://www.reddit.com/search.json?q={domain_search}&type=link&limit=5"
                
                response = self.session.get(domain_search_url)
                if response.status_code == 200:
                    data = response.json()
                    for post in data.get('data', {}).get('children', []):
                        post_data = post['data']
                        if post_data['url'] == article_url or article_title.lower() in post_data['title'].lower():
                            reddit_discussions.append({
                                'reddit_url': f"https://www.reddit.com{post_data['permalink']}",
                                'subreddit': post_data['subreddit'],
                                'post_id': post_data['id'],
                                'title': post_data['title'],
                                'author': post_data['author'],
                                'score': post_data['score'],
                                'num_comments': post_data['num_comments'],
                                'created_utc': post_data['created_utc'],
                                'selftext': post_data.get('selftext', '')
                            })
            
            # Remove duplicates
            seen_ids = set()
            unique_discussions = []
            for disc in reddit_discussions:
                if disc['post_id'] not in seen_ids:
                    seen_ids.add(disc['post_id'])
                    unique_discussions.append(disc)
            
            return unique_discussions[:5]  # Limit to top 5 relevant discussions
            
        except Exception as e:
            logger.error(f"Error searching Reddit: {e}")
            return []
    
    def scrape_reddit_comments(self, reddit_post_id, limit=50):
        """Scrape comments from a Reddit post."""
        try:
            reddit_json_url = f"https://www.reddit.com/comments/{reddit_post_id}.json?limit={limit}"
            response = self.session.get(reddit_json_url)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            comments = []
            
            def extract_comments(comment_data, depth=0, parent_id=None):
                if isinstance(comment_data, dict) and 'data' in comment_data:
                    comment_info = comment_data['data']
                    
                    if comment_info.get('body') and comment_info.get('body') != '[deleted]':
                        comment = {
                            'source_id': comment_info['id'],
                            'parent_id': parent_id,
                            'author': comment_info.get('author', 'deleted'),
                            'comment_text': comment_info['body'],
                            'score': comment_info.get('score', 0),
                            'timestamp': str(comment_info.get('created_utc', 0)),
                            'depth': depth,
                            'url': f"https://www.reddit.com{comment_info.get('permalink', '')}"
                        }
                        comments.append(comment)
                        
                        # Process replies
                        replies = comment_info.get('replies', {})
                        if isinstance(replies, dict) and 'data' in replies:
                            for reply in replies['data'].get('children', []):
                                extract_comments(reply, depth + 1, comment_info['id'])
            
            # Process top-level comments
            if len(data) > 1 and 'data' in data[1] and 'children' in data[1]['data']:
                for comment in data[1]['data']['children']:
                    extract_comments(comment)
            
            return comments
            
        except Exception as e:
            logger.error(f"Error scraping Reddit comments for post {reddit_post_id}: {e}")
            return []
    
    def get_expanded_hn_comments(self, hn_id):
        """Get more comprehensive HN comments using the API."""
        try:
            # Get the HN item details
            hn_api_url = f"https://hacker-news.firebaseio.com/v0/item/{hn_id}.json"
            response = self.session.get(hn_api_url)
            
            if response.status_code != 200:
                return []
            
            item_data = response.json()
            if not item_data or 'kids' not in item_data:
                return []
            
            comments = []
            
            def fetch_comment_recursive(comment_id, depth=0, parent_id=None):
                try:
                    comment_url = f"https://hacker-news.firebaseio.com/v0/item/{comment_id}.json"
                    response = self.session.get(comment_url)
                    
                    if response.status_code == 200:
                        comment_data = response.json()
                        if comment_data and comment_data.get('text'):
                            comment = {
                                'source_id': str(comment_id),
                                'parent_id': str(parent_id) if parent_id else None,
                                'author': comment_data.get('by', 'Anonymous'),
                                'comment_text': self.clean_html(comment_data['text']),
                                'score': 0,  # HN doesn't expose comment scores
                                'timestamp': str(comment_data.get('time', 0)),
                                'depth': depth,
                                'url': f"https://news.ycombinator.com/item?id={comment_id}"
                            }
                            comments.append(comment)
                            
                            # Fetch replies (limit depth to avoid infinite recursion)
                            if depth < 3 and 'kids' in comment_data:
                                for kid_id in comment_data['kids'][:10]:  # Limit to 10 replies per comment
                                    fetch_comment_recursive(kid_id, depth + 1, comment_id)
                    
                    # Rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Error fetching comment {comment_id}: {e}")
            
            # Fetch all top-level comments and their replies
            for kid_id in item_data['kids'][:100]:  # Increased from default limit
                fetch_comment_recursive(kid_id)
            
            return comments
            
        except Exception as e:
            logger.error(f"Error getting expanded HN comments for {hn_id}: {e}")
            return []
    
    def clean_html(self, text):
        """Clean HTML tags from text."""
        if not text:
            return ""
        # Basic HTML cleaning
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        return text.strip()
    
    def generate_article_summary(self, article_url, article_title):
        """Generate article summary by scraping the original content."""
        try:
            response = self.session.get(article_url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to find main content
            content_selectors = [
                'article', '.article-content', '.post-content', 
                '.entry-content', '.content', 'main', '.main-content'
            ]
            
            main_content = None
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.find('body')
            
            if main_content:
                # Extract text
                text = main_content.get_text()
                # Clean and summarize
                paragraphs = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 50]
                
                if paragraphs:
                    # Take first few paragraphs as summary
                    summary = ' '.join(paragraphs[:3])[:500]
                    key_points = paragraphs[:5] if len(paragraphs) >= 5 else paragraphs
                    
                    return {
                        'summary_text': summary,
                        'key_points': ' | '.join(key_points),
                        'source_type': 'original',
                        'credibility_score': 0.9
                    }
            
        except Exception as e:
            logger.error(f"Error generating summary for {article_url}: {e}")
        
        return None
    
    def enhance_article(self, hn_id, title, url):
        """Enhance a single article with multi-source discussions and summary."""
        logger.info(f"Enhancing article {hn_id}: {title}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 1. Generate article summary
            summary = self.generate_article_summary(url, title)
            if summary:
                cursor.execute('''
                    INSERT INTO enhanced_summaries (article_hn_id, source_url, summary_text, key_points, source_type, credibility_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (hn_id, url, summary['summary_text'], summary['key_points'], 
                     summary['source_type'], summary['credibility_score']))
            
            # 2. Get expanded HN comments
            hn_comments = self.get_expanded_hn_comments(hn_id)
            logger.info(f"Found {len(hn_comments)} HN comments for article {hn_id}")
            
            for comment in hn_comments:
                cursor.execute('''
                    INSERT INTO enhanced_comments (
                        article_hn_id, source, source_id, parent_id, author, comment_text, 
                        score, timestamp, url, depth
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (hn_id, 'hackernews', comment['source_id'], comment['parent_id'],
                     comment['author'], comment['comment_text'], comment['score'],
                     comment['timestamp'], comment['url'], comment['depth']))
            
            # 3. Search and scrape Reddit discussions
            reddit_discussions = self.search_reddit_discussions(title, url)
            logger.info(f"Found {len(reddit_discussions)} Reddit discussions for article {hn_id}")
            
            for discussion in reddit_discussions:
                # Store Reddit discussion info
                cursor.execute('''
                    INSERT INTO reddit_discussions (
                        article_hn_id, reddit_url, subreddit, reddit_post_id, post_title,
                        post_author, post_score, num_comments, created_utc, post_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (hn_id, discussion['reddit_url'], discussion['subreddit'],
                     discussion['post_id'], discussion['title'], discussion['author'],
                     discussion['score'], discussion['num_comments'], 
                     discussion['created_utc'], discussion['selftext']))
                
                # Scrape Reddit comments
                reddit_comments = self.scrape_reddit_comments(discussion['post_id'])
                logger.info(f"Scraped {len(reddit_comments)} comments from Reddit post {discussion['post_id']}")
                
                for comment in reddit_comments:
                    cursor.execute('''
                        INSERT INTO enhanced_comments (
                            article_hn_id, source, source_id, parent_id, author, comment_text,
                            score, timestamp, url, depth
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (hn_id, 'reddit', comment['source_id'], comment['parent_id'],
                         comment['author'], comment['comment_text'], comment['score'],
                         comment['timestamp'], comment['url'], comment['depth']))
                
                # Rate limiting between Reddit requests
                time.sleep(2)
            
            conn.commit()
            logger.info(f"Successfully enhanced article {hn_id}")
            
        except Exception as e:
            logger.error(f"Error enhancing article {hn_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def enhance_all_articles(self, limit=None):
        """Enhance all articles in the database that haven't been enhanced yet."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Only get articles that haven't been enhanced yet
        query = """
            SELECT hn_id, title, url 
            FROM article_analyses 
            WHERE hn_id NOT IN (SELECT DISTINCT article_hn_id FROM enhanced_comments)
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        articles = cursor.fetchall()
        conn.close()
        
        logger.info(f"Starting enhancement of {len(articles)} remaining articles")
        
        for i, (hn_id, title, url) in enumerate(articles, 1):
            logger.info(f"Processing article {i}/{len(articles)}: {hn_id}")
            self.enhance_article(hn_id, title, url)
            
            # Progress update and rate limiting
            if i % 5 == 0:
                logger.info(f"Completed {i}/{len(articles)} articles")
                time.sleep(5)  # Longer pause every 5 articles

def main():
    """Main function to run the enhancement."""
    print("🚀 Starting Multi-Source Discussion Enhancement")
    print("=" * 60)
    
    collector = MultiSourceDiscussionCollector()
    
    # Setup enhanced database schema
    print("📊 Setting up enhanced database schema...")
    collector.setup_enhanced_schema()
    
    # Process all remaining articles that haven't been enhanced
    print("🔍 Processing all remaining articles...")
    collector.enhance_all_articles(limit=None)
    
    print("\n✅ Enhancement complete! Check the database for new multi-source discussions.")
    print("\nNew tables created:")
    print("  • enhanced_comments - Multi-source comments with threading")
    print("  • reddit_discussions - Reddit discussion metadata")
    print("  • enhanced_summaries - Article summaries from multiple sources")
    print("  • discussion_threads_enhanced - Organized discussion analytics")

if __name__ == "__main__":
    main()
