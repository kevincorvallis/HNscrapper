#!/usr/bin/env python3
"""
Podcast-Optimized Daily Scraper
Focuses on high-quality comments and discussions for podcast generation
"""

import requests
import time
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse
from dynamodb_manager import DynamoDBManager
from dotenv import load_dotenv
import re

load_dotenv()

class PodcastOptimizedScraper:
    """HN Scraper optimized for podcast-quality content."""
    
    def __init__(self):
        self.db = DynamoDBManager()
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'HN-Podcast-Scraper/1.0'})
        
        # Podcast-optimized settings
        self.min_article_score = 50  # Only articles with 50+ upvotes
        self.min_article_comments = 10  # Must have at least 10 comments
        self.min_comment_score = 3  # Only comments with 3+ upvotes
        self.max_comments_per_article = 20  # Focus on best comments
        self.max_comment_length = 1000  # Longer comments for context
        
        print("🎙️ Initialized podcast-optimized scraper")
        print(f"   Min article score: {self.min_article_score}")
        print(f"   Min comment score: {self.min_comment_score}")
        print(f"   Max comments per article: {self.max_comments_per_article}")
    
    def is_podcast_worthy_article(self, story_data: Dict) -> bool:
        """Check if article is worth including in podcast."""
        score = story_data.get('score', 0)
        comment_count = len(story_data.get('kids', []))
        
        # Must meet minimum thresholds
        if score < self.min_article_score or comment_count < self.min_article_comments:
            return False
        
        # Skip job posts and other non-discussion content
        title = story_data.get('title', '').lower()
        if any(keyword in title for keyword in ['hiring', 'job', 'jobs', 'who is hiring']):
            return False
        
        return True
    
    def is_podcast_worthy_comment(self, comment_data: Dict, level: int) -> bool:
        """Check if comment is worth storing for podcast."""
        # Check score (key quality indicator)
        score = comment_data.get('score', 0)
        if score < self.min_comment_score:
            return False
        
        # Skip deleted/dead comments
        if comment_data.get('deleted') or comment_data.get('dead'):
            return False
        
        # Content quality checks
        content = comment_data.get('text', '')
        if len(content) < 100:  # Substantial content required
            return False
        
        # Skip pure links or very technical/code-heavy comments
        if content.count('http') > 3:
            return False
        
        # Skip comments that are mostly code
        code_indicators = ['```', 'def ', 'function', 'import ', '#!/']
        if sum(1 for indicator in code_indicators if indicator in content) > 2:
            return False
        
        return True
    
    def get_item_with_retry(self, item_id: int, max_retries: int = 3) -> Optional[Dict]:
        """Get item with retry logic for reliability."""
        for attempt in range(max_retries):
            try:
                response = self.session.get(f"{self.base_url}/item/{item_id}.json", timeout=10)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"❌ Failed to fetch item {item_id} after {max_retries} attempts: {e}")
                    return None
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
    
    def scrape_podcast_optimized_comments(self, story_id: str, comment_ids: List[int]) -> Dict:
        """Scrape comments optimized for podcast quality."""
        if not comment_ids:
            return {'comments_stored': 0, 'threads_found': 0}
        
        comments_stored = 0
        threads_found = 0
        comment_scores = []  # Track scores for analysis
        
        print(f"    📊 Analyzing {len(comment_ids)} comments for podcast quality...")
        
        # First pass: get all comment data and scores
        comment_data_cache = {}
        for comment_id in comment_ids:
            data = self.get_item_with_retry(comment_id)
            if data:
                comment_data_cache[comment_id] = data
                comment_scores.append(data.get('score', 0))
        
        # Sort comments by score (best first)
        sorted_comments = sorted(
            comment_data_cache.items(), 
            key=lambda x: x[1].get('score', 0), 
            reverse=True
        )
        
        # Store top-quality comments
        for comment_id, comment_data in sorted_comments[:self.max_comments_per_article]:
            if self.is_podcast_worthy_comment(comment_data, 0):
                # Store the comment
                comment_record = {
                    'comment_id': str(comment_id),
                    'article_id': story_id,
                    'parent_id': str(comment_data.get('parent', '')),
                    'author': comment_data.get('by', 'unknown'),
                    'content': self.clean_html(comment_data.get('text', ''))[:self.max_comment_length],
                    'time_posted': comment_data.get('time', 0),
                    'level': 0,
                    'score': comment_data.get('score', 0),  # Store score for analysis
                    'scraped_at': datetime.now().isoformat()
                }
                
                if self.db.insert_comment(comment_record):
                    comments_stored += 1
                
                # Check for high-quality reply threads
                kids = comment_data.get('kids', [])
                if kids and comment_data.get('score', 0) > 10:  # Popular comments
                    thread_replies = 0
                    
                    for reply_id in kids[:5]:  # Top 5 replies
                        reply_data = self.get_item_with_retry(reply_id)
                        if reply_data and self.is_podcast_worthy_comment(reply_data, 1):
                            reply_record = {
                                'comment_id': str(reply_id),
                                'article_id': story_id,
                                'parent_id': str(comment_id),
                                'author': reply_data.get('by', 'unknown'),
                                'content': self.clean_html(reply_data.get('text', ''))[:self.max_comment_length],
                                'time_posted': reply_data.get('time', 0),
                                'level': 1,
                                'score': reply_data.get('score', 0),
                                'scraped_at': datetime.now().isoformat()
                            }
                            
                            if self.db.insert_comment(reply_record):
                                comments_stored += 1
                                thread_replies += 1
                    
                    if thread_replies > 0:
                        threads_found += 1
        
        # Analysis
        if comment_scores:
            avg_score = sum(comment_scores) / len(comment_scores)
            max_score = max(comment_scores)
            quality_comments = len([s for s in comment_scores if s >= self.min_comment_score])
            
            print(f"    📈 Comment quality analysis:")
            print(f"       Avg score: {avg_score:.1f}")
            print(f"       Max score: {max_score}")
            print(f"       High quality: {quality_comments}/{len(comment_scores)} ({quality_comments/len(comment_scores)*100:.1f}%)")
        
        return {
            'comments_stored': comments_stored,
            'threads_found': threads_found,
            'total_analyzed': len(comment_data_cache)
        }
    
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
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            if not url:
                return 'news.ycombinator.com'
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return 'unknown'
    
    def scrape_podcast_optimized_articles(self, limit: int = 10) -> Dict:
        """Scrape articles optimized for podcast generation."""
        print(f"🎙️ Starting podcast-optimized scraping (limit: {limit})")
        
        # Get top stories
        try:
            response = self.session.get(f"{self.base_url}/topstories.json", timeout=10)
            response.raise_for_status()
            story_ids = response.json()[:50]  # Check more stories to find quality ones
        except Exception as e:
            print(f"❌ Error fetching stories: {e}")
            return {'success': False}
        
        stats = {
            'articles_analyzed': 0,
            'articles_stored': 0,
            'comments_stored': 0,
            'discussion_threads': 0,
            'articles_skipped_existing': 0,
            'articles_skipped_quality': 0
        }
        
        articles_processed = 0
        
        for story_id in story_ids:
            if articles_processed >= limit:
                break
            
            try:
                # Check if already exists
                if self.db.article_exists(str(story_id)):
                    stats['articles_skipped_existing'] += 1
                    continue
                
                # Get article data
                story_data = self.get_item_with_retry(story_id)
                if not story_data:
                    continue
                
                stats['articles_analyzed'] += 1
                
                # Check if podcast-worthy
                if not self.is_podcast_worthy_article(story_data):
                    stats['articles_skipped_quality'] += 1
                    continue
                
                print(f"\n📰 Processing: {story_data.get('title', '')[:60]}...")
                print(f"    Score: {story_data.get('score', 0)}, Comments: {len(story_data.get('kids', []))}")
                
                # Store article
                article = {
                    'hn_id': str(story_id),
                    'title': story_data.get('title', ''),
                    'url': story_data.get('url', ''),
                    'domain': self.extract_domain(story_data.get('url')),
                    'score': story_data.get('score', 0),
                    'author': story_data.get('by', 'unknown'),
                    'time_posted': story_data.get('time', 0),
                    'num_comments': len(story_data.get('kids', [])),
                    'story_text': self.clean_html(story_data.get('text', ''))[:2000],
                    'story_type': story_data.get('type', 'story'),
                    'scraped_at': datetime.now().isoformat()
                }
                
                if self.db.insert_article(article):
                    stats['articles_stored'] += 1
                    articles_processed += 1
                    
                    # Process comments
                    comment_ids = story_data.get('kids', [])
                    if comment_ids:
                        comment_stats = self.scrape_podcast_optimized_comments(str(story_id), comment_ids)
                        stats['comments_stored'] += comment_stats['comments_stored']
                        stats['discussion_threads'] += comment_stats['threads_found']
                        
                        print(f"    ✅ Stored {comment_stats['comments_stored']} comments in {comment_stats['threads_found']} threads")
                
                # Be respectful to the API
                time.sleep(0.2)
                
            except Exception as e:
                print(f"❌ Error processing story {story_id}: {e}")
                continue
        
        # Final report
        print(f"\n🎉 Podcast-optimized scraping complete!")
        print(f"📊 Statistics:")
        print(f"   Articles analyzed: {stats['articles_analyzed']}")
        print(f"   Articles stored: {stats['articles_stored']}")
        print(f"   Comments stored: {stats['comments_stored']}")
        print(f"   Discussion threads: {stats['discussion_threads']}")
        print(f"   Skipped (existing): {stats['articles_skipped_existing']}")
        print(f"   Skipped (quality): {stats['articles_skipped_quality']}")
        
        if stats['articles_stored'] > 0:
            avg_comments = stats['comments_stored'] / stats['articles_stored']
            print(f"   Avg comments per article: {avg_comments:.1f}")
        
        stats['success'] = True
        return stats

if __name__ == "__main__":
    scraper = PodcastOptimizedScraper()
    result = scraper.scrape_podcast_optimized_articles(limit=5)
