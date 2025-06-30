#!/usr/bin/env python3
"""
Enhanced Hacker News Scraper with DynamoDB support.
Designed to run daily and store comprehensive data in AWS DynamoDB.
"""

import requests
import json
import time
import os
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dynamodb_manager import DynamoDBManager

class HNScrapperDynamoDB:
    def __init__(self):
        self.db = DynamoDBManager()
        self.base_url = "https://hacker-news.firebaseio.com/v0"
    
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
        """Get best story IDs from HN (highest scored articles)."""
        try:
            url = f"{self.base_url}/beststories.json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()[:limit]
        except Exception as e:
            print(f"Error fetching best stories: {e}")
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
        if not comment_ids or level > 3:  # Limit depth
            return 0
        
        comment_count = 0
        
        for comment_id in comment_ids:
            if not comment_id:
                continue
                
            comment_data = self.get_item(comment_id)
            if not comment_data or comment_data.get('deleted') or comment_data.get('dead'):
                continue
            
            # Prepare comment data for DynamoDB
            comment_item = {
                'comment_id': str(comment_id),
                'article_id': article_id,
                'parent_id': parent_id or '',
                'author': comment_data.get('by', 'unknown'),
                'content': comment_data.get('text', ''),
                'time_posted': comment_data.get('time', 0),
                'level': level,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Insert comment
            if self.db.insert_comment(comment_item):
                comment_count += 1
            
            # Recursively scrape replies
            if 'kids' in comment_data and level < 2:  # Limit depth further
                reply_count = self.scrape_comments(
                    article_id, 
                    comment_data['kids'][:10], # Limit reply count
                    level + 1, 
                    str(comment_id)
                )
                comment_count += reply_count
            
            # Rate limiting
            time.sleep(0.1)
        
        return comment_count
    
    def scrape_daily(self, max_articles: int = 15, max_comments_per_article: int = 50) -> Dict:
        """Main scraping function to run daily."""
        print(f"Starting daily HN scrape at {datetime.now()}")
        
        # Get top stories
        story_ids = self.get_top_stories(100)  # Get more to filter from
        print(f"Found {len(story_ids)} top stories")
        
        # Check which articles we already have
        existing_ids = self.db.get_existing_article_ids()
        print(f"Found {len(existing_ids)} existing articles in database")
        
        # Process both new and existing articles for updates
        scraped_articles = 0
        updated_articles = 0
        total_comments = 0
        
        # Process top articles (both new and existing for updates)
        story_ids_to_process = story_ids[:max_articles * 2]  # Process more to ensure we get enough
        
        for story_id in story_ids_to_process:
            if scraped_articles + updated_articles >= max_articles:
                break
                
            story_data = self.get_item(int(story_id))
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
            
            # Prepare article data for DynamoDB
            article_item = {
                'hn_id': str(story_id),
                'title': title,
                'url': url,
                'domain': domain,
                'score': score,
                'author': author,
                'time_posted': time_posted,
                'num_comments': num_comments,
                'story_text': story_text,
                'story_type': 'story',
                'scraped_at': datetime.now().isoformat()
            }
            
            # Check if article exists
            is_existing = str(story_id) in existing_ids
            
            # Insert or update article
            if self.db.insert_article(article_item):
                if is_existing:
                    updated_articles += 1
                    print(f"Updated article {updated_articles}: {title[:50]}... (Score: {score}, Comments: {num_comments})")
                else:
                    scraped_articles += 1
                    print(f"Scraped new article {scraped_articles}: {title[:50]}...")
                
                # Scrape comments if they exist (for both new and updated articles)
                if 'kids' in story_data and len(story_data['kids']) > 0:
                    comment_ids = story_data['kids'][:max_comments_per_article]
                    article_comment_count = self.scrape_comments(str(story_id), comment_ids)
                    total_comments += article_comment_count
                    print(f"  └─ Scraped {article_comment_count} comments")
            
            # Rate limiting
            time.sleep(0.5)
        
        results = {
            'success': True,
            'scraped_articles': scraped_articles,
            'updated_articles': updated_articles,
            'total_comments': total_comments,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"Daily scrape completed: {results}")
        return results
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        return self.db.get_stats()

def main():
    """Run the daily scraper with DynamoDB."""
    # Check if AWS credentials are set
    if not all([os.environ.get('AWS_ACCESS_KEY_ID'), os.environ.get('AWS_SECRET_ACCESS_KEY')]):
        print("❌ AWS credentials not found!")
        print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        return
    
    scraper = HNScrapperDynamoDB()
    
    # Run daily scrape with fewer articles to avoid AWS costs
    results = scraper.scrape_daily(max_articles=10, max_comments_per_article=30)
    
    # Print stats
    stats = scraper.get_stats()
    print(f"\nDatabase Stats: {stats}")

if __name__ == "__main__":
    main()
