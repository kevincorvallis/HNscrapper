#!/usr/bin/env python3
"""
Enhanced Daily Scraper with Progress Tracking and Optimizations
Includes progress bars, cost-optimized comment storage, and end-to-end testing
"""

import requests
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urlparse
from dynamodb_manager import DynamoDBManager
from dotenv import load_dotenv
import sys
import os

# Load environment variables
load_dotenv()

class ProgressTracker:
    """Simple progress tracker for terminal output."""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
    
    def update(self, increment: int = 1):
        """Update progress."""
        self.current += increment
        self._display()
    
    def _display(self):
        """Display current progress."""
        if self.total == 0:
            return
            
        percentage = (self.current / self.total) * 100
        bar_length = 40
        filled_length = int(bar_length * self.current // self.total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f"ETA: {eta:.0f}s"
        else:
            eta_str = "ETA: --"
        
        print(f'\r{self.description}: |{bar}| {percentage:.1f}% ({self.current}/{self.total}) {eta_str}', end='', flush=True)
        
        if self.current >= self.total:
            print()  # New line when complete

class OptimizedHNScraper:
    """Optimized Hacker News scraper with progress tracking and cost optimizations."""
    
    def __init__(self):
        self.db = DynamoDBManager()
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'HN-Scraper/1.0'})
        
        # Optimization settings
        self.max_articles_per_run = 50  # Limit articles per run
        self.max_comments_per_article = 100  # Limit comments to reduce storage
        self.comment_depth_limit = 3  # Only store comments up to 3 levels deep
        self.min_comment_length = 10  # Skip very short comments
        
        print(f"🚀 Initialized scraper with optimizations:")
        print(f"   Max articles per run: {self.max_articles_per_run}")
        print(f"   Max comments per article: {self.max_comments_per_article}")
        print(f"   Comment depth limit: {self.comment_depth_limit}")
        print(f"   Min comment length: {self.min_comment_length}")
    
    def get_top_stories(self, limit: int = None) -> List[int]:
        """Get top story IDs from HN."""
        if limit is None:
            limit = self.max_articles_per_run
            
        try:
            response = self.session.get(f"{self.base_url}/topstories.json", timeout=10)
            response.raise_for_status()
            story_ids = response.json()
            return story_ids[:limit]
        except Exception as e:
            print(f"❌ Error fetching top stories: {e}")
            return []
    
    def get_item_data(self, item_id: int) -> Optional[Dict]:
        """Get item data from HN API."""
        try:
            response = self.session.get(f"{self.base_url}/item/{item_id}.json", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching item {item_id}: {e}")
            return None
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            if not url:
                return 'news.ycombinator.com'
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return 'unknown'
    
    def clean_html(self, text: str) -> str:
        """Clean HTML from text."""
        if not text:
            return ''
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        text = text.replace('&gt;', '>').replace('&lt;', '<')
        text = text.replace('&amp;', '&').replace('&quot;', '"')
        text = text.replace('&#x27;', "'").replace('&#x2F;', '/')
        return text.strip()
    
    def should_store_comment(self, comment_data: Dict, level: int) -> bool:
        """Determine if comment should be stored based on optimization criteria."""
        # Skip if too deep
        if level > self.comment_depth_limit:
            return False
        
        # Skip if too short
        content = self.clean_html(comment_data.get('text', ''))
        if len(content) < self.min_comment_length:
            return False
        
        # Skip deleted comments
        if comment_data.get('deleted') or comment_data.get('dead'):
            return False
            
        return True
    
    def scrape_comments(self, story_id: str, comment_ids: List[int], progress: ProgressTracker) -> int:
        """Scrape comments for a story with optimization."""
        if not comment_ids:
            return 0
        
        comments_scraped = 0
        comments_to_process = min(len(comment_ids), self.max_comments_per_article)
        
        # Only process top-level comments initially to stay within limits
        for i, comment_id in enumerate(comment_ids[:comments_to_process]):
            if comments_scraped >= self.max_comments_per_article:
                break
                
            try:
                comment_data = self.get_item_data(comment_id)
                if not comment_data:
                    continue
                
                if self.should_store_comment(comment_data, 0):  # Level 0 for top-level
                    # Prepare optimized comment data
                    comment = {
                        'comment_id': str(comment_id),
                        'article_id': story_id,
                        'parent_id': str(comment_data.get('parent', '')),
                        'author': comment_data.get('by', 'unknown'),
                        'content': self.clean_html(comment_data.get('text', ''))[:1000],  # Limit content length
                        'time_posted': comment_data.get('time', 0),
                        'level': 0,
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    if self.db.insert_comment(comment):
                        comments_scraped += 1
                
                # Process one level of replies for popular comments (score > 5)
                if comment_data.get('score', 0) > 5 and comment_data.get('kids'):
                    for reply_id in comment_data['kids'][:5]:  # Max 5 replies per comment
                        if comments_scraped >= self.max_comments_per_article:
                            break
                            
                        reply_data = self.get_item_data(reply_id)
                        if reply_data and self.should_store_comment(reply_data, 1):
                            reply = {
                                'comment_id': str(reply_id),
                                'article_id': story_id,
                                'parent_id': str(comment_id),
                                'author': reply_data.get('by', 'unknown'),
                                'content': self.clean_html(reply_data.get('text', ''))[:1000],
                                'time_posted': reply_data.get('time', 0),
                                'level': 1,
                                'scraped_at': datetime.now().isoformat()
                            }
                            
                            if self.db.insert_comment(reply):
                                comments_scraped += 1
                
                progress.update(1)
                
            except Exception as e:
                print(f"\n❌ Error processing comment {comment_id}: {e}")
                continue
        
        return comments_scraped
    
    def scrape_article(self, story_id: int, progress: ProgressTracker) -> bool:
        """Scrape a single article with optimizations."""
        try:
            # Check if article already exists
            if self.db.article_exists(str(story_id)):
                progress.update(1)
                return False  # Skip existing
            
            # Get article data
            story_data = self.get_item_data(story_id)
            if not story_data:
                progress.update(1)
                return False
            
            # Prepare optimized article data
            article = {
                'hn_id': str(story_id),
                'title': story_data.get('title', ''),
                'url': story_data.get('url', ''),
                'domain': self.extract_domain(story_data.get('url')),
                'score': story_data.get('score', 0),
                'author': story_data.get('by', 'unknown'),
                'time_posted': story_data.get('time', 0),
                'num_comments': len(story_data.get('kids', [])),
                'story_text': self.clean_html(story_data.get('text', ''))[:2000],  # Limit story text
                'story_type': story_data.get('type', 'story'),
                'scraped_at': datetime.now().isoformat()
            }
            
            # Save article
            if not self.db.insert_article(article):
                progress.update(1)
                return False
            
            # Scrape optimized comments
            comment_ids = story_data.get('kids', [])
            if comment_ids:
                comment_progress = ProgressTracker(
                    min(len(comment_ids), self.max_comments_per_article),
                    f"  Comments for {story_id}"
                )
                comments_count = self.scrape_comments(str(story_id), comment_ids, comment_progress)
                print(f"\n    ✅ Saved {comments_count} comments for article {story_id}")
            
            progress.update(1)
            return True
            
        except Exception as e:
            print(f"\n❌ Error scraping article {story_id}: {e}")
            progress.update(1)
            return False
    
    def run_daily_scrape(self) -> Dict:
        """Run the daily scraping with progress tracking."""
        print("🕐 Starting daily HN scrape with optimizations...")
        start_time = time.time()
        
        # Get story IDs
        print("📰 Fetching top stories...")
        story_ids = self.get_top_stories(self.max_articles_per_run)
        
        if not story_ids:
            print("❌ No stories found")
            return {'success': False, 'error': 'No stories found'}
        
        print(f"📊 Found {len(story_ids)} stories to process")
        
        # Initialize statistics
        stats = {
            'articles_processed': 0,
            'articles_new': 0,
            'articles_skipped': 0,
            'total_comments': 0,
            'errors': 0,
            'start_time': start_time
        }
        
        # Progress tracker for articles
        progress = ProgressTracker(len(story_ids), "Scraping articles")
        
        # Process each story
        for story_id in story_ids:
            try:
                was_new = self.scrape_article(story_id, progress)
                stats['articles_processed'] += 1
                
                if was_new:
                    stats['articles_new'] += 1
                else:
                    stats['articles_skipped'] += 1
                
                # Small delay to be respectful
                time.sleep(0.1)
                
            except Exception as e:
                print(f"\n❌ Error processing story {story_id}: {e}")
                stats['errors'] += 1
                progress.update(1)
        
        # Final statistics
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n🎉 Daily scrape completed!")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"📰 Articles processed: {stats['articles_processed']}")
        print(f"🆕 New articles: {stats['articles_new']}")
        print(f"⏭️  Skipped (existing): {stats['articles_skipped']}")
        print(f"❌ Errors: {stats['errors']}")
        
        # Get updated database stats
        db_stats = self.db.get_stats()
        print(f"📊 Total in database: {db_stats['total_articles']} articles, {db_stats['total_comments']} comments")
        
        stats['duration'] = duration
        stats['success'] = True
        return stats

def run_end_to_end_test():
    """Run an end-to-end test of the scraping system."""
    print("🧪 RUNNING END-TO-END TEST")
    print("=" * 50)
    
    try:
        # Initialize scraper with test limits
        scraper = OptimizedHNScraper()
        scraper.max_articles_per_run = 5  # Limit for testing
        scraper.max_comments_per_article = 20  # Limit for testing
        
        # Get initial database stats
        initial_stats = scraper.db.get_stats()
        print(f"📊 Initial: {initial_stats['total_articles']} articles, {initial_stats['total_comments']} comments")
        
        # Run scraping
        result = scraper.run_daily_scrape()
        
        # Get final stats
        final_stats = scraper.db.get_stats()
        print(f"📊 Final: {final_stats['total_articles']} articles, {final_stats['total_comments']} comments")
        
        # Verify results
        articles_added = final_stats['total_articles'] - initial_stats['total_articles']
        comments_added = final_stats['total_comments'] - initial_stats['total_comments']
        
        print(f"\n✅ TEST RESULTS:")
        print(f"   Articles added: {articles_added}")
        print(f"   Comments added: {comments_added}")
        print(f"   Success: {result.get('success', False)}")
        
        if result.get('success') and articles_added > 0:
            print("🎉 End-to-end test PASSED!")
            return True
        else:
            print("❌ End-to-end test FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_end_to_end_test()
    else:
        scraper = OptimizedHNScraper()
        scraper.run_daily_scrape()
