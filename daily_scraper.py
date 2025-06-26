#!/usr/bin/env python3
"""
Enhanced Hacker News Scraper with proper article and comment separation.
Designed to run daily and store comprehensive data.
"""

import sqlite3
import requests
import json
import time
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

class HNScraper:
    def __init__(self, db_path: str = "enhanced_hn_articles.db"):
        self.db_path = db_path
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.init_database()
    
    def init_database(self):
        """Initialize database with improved schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced articles table
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
        
        # Enhanced comments table with article relationship
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
        
        # Keep existing tables for compatibility
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
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_score ON articles(score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_article_id ON comments(article_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_parent_id ON comments(parent_id)')
        
        conn.commit()
        conn.close()
    
    def get_item(self, item_id: int) -> Optional[Dict]:
        """Get a single item (article or comment) from HN API."""
        try:
            response = requests.get(f"{self.base_url}/item/{item_id}.json", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error fetching item {item_id}: {e}")
        return None
    
    def get_top_stories(self, limit: int = 100) -> List[int]:
        """Get top story IDs from HN."""
        try:
            response = requests.get(f"{self.base_url}/topstories.json", timeout=10)
            if response.status_code == 200:
                return response.json()[:limit]
        except Exception as e:
            print(f"Error fetching top stories: {e}")
        return []
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        if not url:
            return "news.ycombinator.com"
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except:
            return "unknown"
    
    def scrape_comments(self, article_id: str, comment_ids: List[int], level: int = 0, parent_id: str = None) -> int:
        """Recursively scrape comments for an article."""
        if not comment_ids or level > 5:  # Limit depth to prevent infinite recursion
            return 0
        
        comment_count = 0
        
        for comment_id in comment_ids:
            if not comment_id:
                continue
                
            comment_data = self.get_item(comment_id)
            if not comment_data or comment_data.get('deleted') or comment_data.get('dead'):
                continue
            
            # Use a separate connection for each comment to avoid locks
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert comment
            cursor.execute('''
                INSERT OR REPLACE INTO comments 
                (comment_id, article_id, parent_id, author, content, time_posted, level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(comment_id),
                article_id,
                parent_id,
                comment_data.get('by', 'unknown'),
                comment_data.get('text', ''),
                comment_data.get('time', 0),
                level
            ))
            
            conn.commit()
            conn.close()
            comment_count += 1
            
            # Recursively scrape replies
            if 'kids' in comment_data:
                reply_count = self.scrape_comments(
                    article_id, 
                    comment_data['kids'], 
                    level + 1, 
                    str(comment_id)
                )
                comment_count += reply_count
            
            # Rate limiting
            time.sleep(0.1)
        
        return comment_count
    
    def scrape_daily(self, max_articles: int = 15, max_comments_per_article: int = 100) -> Dict:
        """Main scraping function to run daily."""
        print(f"Starting daily HN scrape at {datetime.now()}")
        
        # Get top stories
        story_ids = self.get_top_stories(100)  # Get more to filter from
        print(f"Found {len(story_ids)} top stories")
        
        # Check which articles we already have
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get existing article IDs
        cursor.execute('SELECT hn_id FROM articles')
        existing_ids = {row[0] for row in cursor.fetchall()}
        conn.close()
        print(f"Found {len(existing_ids)} existing articles in database")
        
        # Filter out existing articles
        new_story_ids = [str(sid) for sid in story_ids if str(sid) not in existing_ids]
        print(f"Found {len(new_story_ids)} new articles to scrape")
        
        # Limit to max_articles
        new_story_ids = new_story_ids[:max_articles]
        print(f"Will scrape {len(new_story_ids)} articles")
        
        scraped_articles = 0
        total_comments = 0
        
        for story_id in new_story_ids:
            story_data = self.get_item(story_id)
            if not story_data or story_data.get('deleted') or story_data.get('dead'):
                continue
            
            # Skip if not a story
            if story_data.get('type') != 'story':
                continue
            
            # Extract article info
            title = story_data.get('title', 'No title')
            url = story_data.get('url', '')
            domain = self.extract_domain(url)
            score = story_data.get('score', 0)
            author = story_data.get('by', 'unknown')
            time_posted = story_data.get('time', 0)
            num_comments = story_data.get('descendants', 0)
            story_text = story_data.get('text', '')
            
            # Use separate connection for each article
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert article
            cursor.execute('''
                INSERT OR REPLACE INTO articles 
                (hn_id, title, url, domain, score, author, time_posted, num_comments, story_text, story_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(story_id),
                title,
                url,
                domain,
                score,
                author,
                time_posted,
                num_comments,
                story_text,
                'story'
            ))
            
            # Also insert into legacy table for compatibility
            cursor.execute('''
                INSERT OR REPLACE INTO article_analyses 
                (hn_id, title, url, domain, summary)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                str(story_id),
                title,
                url,
                domain,
                f"Score: {score}, Comments: {num_comments}, Author: {author}"
            ))
            
            conn.commit()
            conn.close()
            
            scraped_articles += 1
            print(f"Scraped article {scraped_articles}: {title[:50]}...")
            
            # Scrape comments if they exist (with proper connection handling)
            if 'kids' in story_data and len(story_data['kids']) > 0:
                comment_ids = story_data['kids'][:20]  # Limit to first 20 top-level comments
                article_comment_count = self.scrape_comments(str(story_id), comment_ids)
                total_comments += article_comment_count
                print(f"  └─ Scraped {article_comment_count} comments")
            
            # Rate limiting
            time.sleep(0.5)
        
        results = {
            'success': True,
            'scraped_articles': scraped_articles,
            'total_comments': total_comments,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"Daily scrape completed: {results}")
        return results
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM articles')
        total_articles = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM comments')
        total_comments = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(score) FROM articles WHERE score > 0')
        avg_score = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(DISTINCT domain) FROM articles')
        unique_domains = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_articles': total_articles,
            'total_comments': total_comments,
            'avg_score': round(avg_score, 1),
            'unique_domains': unique_domains
        }

def main():
    """Run the daily scraper."""
    scraper = HNScraper()
    
    # Run daily scrape with fewer articles to avoid duplicates
    results = scraper.scrape_daily(max_articles=15, max_comments_per_article=50)
    
    # Print stats
    stats = scraper.get_stats()
    print(f"\nDatabase Stats: {stats}")

if __name__ == "__main__":
    main()
