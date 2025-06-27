#!/usr/bin/env python3
"""
🔍 Daily Reddit OutOfTheLoop Scraper
Fetches top posts from r/OutOfTheLoop and saves to DynamoDB
"""

import praw
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List
from dynamodb_manager import DynamoDBManager


class RedditOutOfTheLoopScraper:
    """Daily scraper for r/OutOfTheLoop subreddit posts."""
    
    def __init__(self):
        """Initialize Reddit API client and DynamoDB manager."""
        # Initialize Reddit client
        self.reddit = praw.Reddit(
            client_id="ctOMq724MQhY4S-AWY2zAQ",
            client_secret="Kj2YrbB3qwHR_I0pG0wwhyS4xIUXlQ",
            user_agent="daily_outoftheloop_scraper by u/Historical_Order7790"
        )
        
        # Initialize DynamoDB manager
        self.db_manager = DynamoDBManager()
        
        # Test connections
        if not self._test_reddit_connection():
            raise Exception("Failed to connect to Reddit API")
        
        if not self.db_manager.test_connection():
            raise Exception("Failed to connect to DynamoDB")
        
        print("✅ Reddit OutOfTheLoop Scraper initialized successfully")
    
    def _test_reddit_connection(self) -> bool:
        """Test Reddit API connection."""
        try:
            # Test by accessing a simple property
            self.reddit.user.me()
            print("✅ Connected to Reddit API")
            return True
        except Exception as e:
            print(f"❌ Reddit API connection failed: {e}")
            return False
    
    def fetch_outoftheloop(self, limit: int = 10,
                          time_filter: str = "day") -> List[Dict]:
        """
        Fetch the most upvoted recent posts from r/OutOfTheLoop.
        
        Args:
            limit: Number of posts to fetch (default: 10)
            time_filter: Time filter for posts ('day', 'week', 'month')
        
        Returns:
            List of post dictionaries with metadata
        """
        try:
            print(f"🔍 Fetching top {limit} posts from r/OutOfTheLoop "
                  f"(filter: {time_filter})")
            
            # Get the subreddit
            subreddit = self.reddit.subreddit("OutOfTheLoop")
            
            # Fetch top posts from the specified time period
            posts = []
            post_count = 0
            
            # Get top posts with extra buffer for filtering
            for submission in subreddit.top(time_filter=time_filter,
                                          limit=limit * 2):
                
                # Skip if post is older than 24 hours for 'day' filter
                if time_filter == "day":
                    post_time = datetime.fromtimestamp(submission.created_utc)
                    if datetime.now() - post_time > timedelta(days=1):
                        continue
                
                # Extract post metadata
                post_data = {
                    'reddit_id': submission.id,
                    # Use reddit_ prefix to distinguish from HN posts
                    'hn_id': f"reddit_{submission.id}",
                    'title': submission.title,
                    'url': submission.url,
                    'domain': self._extract_domain(submission.url),
                    'score': submission.score,
                    'author': (str(submission.author) if submission.author
                              else 'deleted'),
                    'time_posted': int(submission.created_utc),
                    'num_comments': submission.num_comments,
                    'story_text': (submission.selftext if submission.selftext
                                  else ''),
                    'story_type': 'reddit_post',
                    'subreddit': 'OutOfTheLoop',
                    'upvote_ratio': submission.upvote_ratio,
                    'is_video': submission.is_video,
                    'over_18': submission.over_18,
                    'scraped_at': datetime.now().isoformat(),
                    'permalink': f"https://reddit.com{submission.permalink}",
                    'flair_text': (submission.link_flair_text if
                                  submission.link_flair_text else '')
                }
                
                posts.append(post_data)
                post_count += 1
                
                if post_count >= limit:
                    break
            
            # Sort by score (upvotes) in descending order
            posts.sort(key=lambda x: x['score'], reverse=True)
            
            print(f"✅ Successfully fetched {len(posts)} posts "
                  f"from r/OutOfTheLoop")
            return posts
            
        except Exception as e:
            print(f"❌ Error fetching OutOfTheLoop posts: {e}")
            return []
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or 'reddit.com'
        except Exception:
            return 'unknown'
    
    def save_posts_to_dynamodb(self, posts: List[Dict]) -> int:
        """
        Save Reddit posts to DynamoDB using the existing article schema.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Number of successfully saved posts
        """
        saved_count = 0
        
        for post in posts:
            try:
                # Save to DynamoDB using the article schema
                success = self.db_manager.save_article(post)
                if success:
                    saved_count += 1
                    title_preview = post['title'][:50]
                    print(f"💾 Saved: {title_preview}... "
                          f"(Score: {post['score']})")
                else:
                    title_preview = post['title'][:50]
                    print(f"⚠️  Failed to save: {title_preview}...")
                    
            except Exception as e:
                reddit_id = post.get('reddit_id', 'unknown')
                print(f"❌ Error saving post {reddit_id}: {e}")
        
        print(f"✅ Successfully saved {saved_count}/{len(posts)} "
              f"posts to DynamoDB")
        return saved_count
    
    def run_daily_scrape(self):
        """Run the daily scraping job."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n🚀 Starting daily OutOfTheLoop scrape at {timestamp}")
        
        try:
            # Fetch today's top posts
            posts = self.fetch_outoftheloop(limit=10, time_filter="day")
            
            if not posts:
                print("⚠️  No posts found for today")
                return
            
            # Save to DynamoDB
            saved_count = self.save_posts_to_dynamodb(posts)
            
            # Print summary
            print(f"\n📊 Daily Scrape Summary:")
            print(f"   • Posts fetched: {len(posts)}")
            print(f"   • Posts saved: {saved_count}")
            top_title = posts[0]['title'][:60]
            top_score = posts[0]['score']
            print(f"   • Top post: {top_title}... ({top_score} upvotes)")
            complete_time = datetime.now().strftime('%H:%M:%S')
            print(f"   • Completed at: {complete_time}")
            
        except Exception as e:
            print(f"❌ Daily scrape failed: {e}")
    
    def get_recent_posts(self, limit: int = 10) -> List[Dict]:
        """Get recent Reddit posts from DynamoDB."""
        try:
            # Get recent articles from DynamoDB
            articles = self.db_manager.get_articles(limit=limit * 2,
                                                   sort_by='recent')
            
            # Filter for Reddit posts only
            reddit_posts = [
                article for article in articles
                if (article.get('story_type') == 'reddit_post' or
                    article.get('hn_id', '').startswith('reddit_'))
            ]
            
            return reddit_posts[:limit]
            
        except Exception as e:
            print(f"❌ Error getting recent posts: {e}")
            return []
    
    def print_recent_posts(self, limit: int = 5):
        """Print recent Reddit posts for debugging."""
        posts = self.get_recent_posts(limit)
        
        print(f"\n📰 Recent OutOfTheLoop Posts (Last {len(posts)}):")
        for i, post in enumerate(posts, 1):
            title = post.get('title', 'No title')[:60]
            score = post.get('score', 0)
            comments = post.get('num_comments', 0)
            scraped_time = post.get('scraped_at', 'Unknown time')[:19]
            
            print(f"{i}. {title}...")
            print(f"   Score: {score} | Comments: {comments}")
            print(f"   Posted: {scraped_time}")
            print()


def main():
    """Main function to run the scraper."""
    try:
        scraper = RedditOutOfTheLoopScraper()
        
        # Check command line arguments
        import sys
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "scrape":
                # Run manual scrape
                scraper.run_daily_scrape()
                
            elif command == "schedule":
                # Run scheduled scraper
                print("🕘 Scheduling daily scrapes at 9:00 AM...")
                schedule.every().day.at("09:00").do(scraper.run_daily_scrape)
                
                print("⏰ Scheduler started. Press Ctrl+C to stop.")
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
                    
            elif command == "test":
                # Test mode - fetch and print posts without saving
                posts = scraper.fetch_outoftheloop(limit=5, time_filter="day")
                print(f"\n🧪 Test Mode - Found {len(posts)} posts:")
                for i, post in enumerate(posts, 1):
                    title_preview = post['title'][:60]
                    score = post['score']
                    print(f"{i}. {title_preview}... ({score} upvotes)")
                
            elif command == "recent":
                # Show recent posts from database
                scraper.print_recent_posts(limit=10)
                
            else:
                print("Usage: python daily_reddit_scraper.py "
                      "[scrape|schedule|test|recent]")
        else:
            # Default: run manual scrape
            scraper.run_daily_scrape()
            
    except KeyboardInterrupt:
        print("\n🛑 Scraper stopped by user")
    except Exception as e:
        print(f"❌ Scraper failed: {e}")


if __name__ == "__main__":
    main()
