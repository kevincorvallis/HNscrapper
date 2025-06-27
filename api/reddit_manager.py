#!/usr/bin/env python3
"""
🔍 Lightweight Reddit API for Vercel
Simplified Reddit OutOfTheLoop integration for serverless deployment
"""

import praw
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class VercelRedditManager:
    """Lightweight Reddit manager for Vercel serverless functions."""
    
    def __init__(self):
        """Initialize Reddit client for Vercel environment."""
        try:
            self.reddit = praw.Reddit(
                client_id="ctOMq724MQhY4S-AWY2zAQ",
                client_secret="Kj2YrbB3qwHR_I0pG0wwhyS4xIUXlQ",
                user_agent="vercel_outoftheloop_scraper by u/Historical_Order7790"
            )
            self.connected = True
        except Exception as e:
            print(f"⚠️ Reddit API not available: {e}")
            self.connected = False
    
    def get_sample_posts(self) -> List[Dict]:
        """Get sample OutOfTheLoop posts for demo purposes."""
        sample_posts = [
            {
                'reddit_id': 'demo1',
                'hn_id': 'reddit_demo1',
                'title': 'What\'s the deal with AI replacing human jobs?',
                'url': 'https://reddit.com/r/OutOfTheLoop/demo1',
                'domain': 'reddit.com',
                'score': 1250,
                'author': 'tech_curious',
                'time_posted': int((datetime.now() - timedelta(hours=2)).timestamp()),
                'num_comments': 234,
                'story_text': 'I keep seeing headlines about AI taking over jobs...',
                'story_type': 'reddit_post',
                'subreddit': 'OutOfTheLoop',
                'scraped_at': datetime.now().isoformat(),
                'permalink': 'https://reddit.com/r/OutOfTheLoop/demo1',
                'flair_text': 'Answered'
            },
            {
                'reddit_id': 'demo2',
                'hn_id': 'reddit_demo2',
                'title': 'What\'s going on with the latest tech layoffs?',
                'url': 'https://reddit.com/r/OutOfTheLoop/demo2',
                'domain': 'reddit.com',
                'score': 892,
                'author': 'news_watcher',
                'time_posted': int((datetime.now() - timedelta(hours=4)).timestamp()),
                'num_comments': 156,
                'story_text': 'Multiple tech companies announced layoffs...',
                'story_type': 'reddit_post',
                'subreddit': 'OutOfTheLoop',
                'scraped_at': datetime.now().isoformat(),
                'permalink': 'https://reddit.com/r/OutOfTheLoop/demo2',
                'flair_text': 'Unanswered'
            },
            {
                'reddit_id': 'demo3',
                'hn_id': 'reddit_demo3',
                'title': 'What\'s up with the new social media platform everyone\'s talking about?',
                'url': 'https://reddit.com/r/OutOfTheLoop/demo3',
                'domain': 'reddit.com',
                'score': 567,
                'author': 'social_media_fan',
                'time_posted': int((datetime.now() - timedelta(hours=6)).timestamp()),
                'num_comments': 89,
                'story_text': 'I keep seeing mentions of this new platform...',
                'story_type': 'reddit_post',
                'subreddit': 'OutOfTheLoop',
                'scraped_at': datetime.now().isoformat(),
                'permalink': 'https://reddit.com/r/OutOfTheLoop/demo3',
                'flair_text': 'Answered'
            }
        ]
        return sample_posts
    
    def fetch_live_posts(self, limit: int = 5) -> List[Dict]:
        """Fetch live posts from Reddit API if available."""
        if not self.connected:
            return self.get_sample_posts()[:limit]
        
        try:
            subreddit = self.reddit.subreddit("OutOfTheLoop")
            posts = []
            
            # Get hot posts (more reliable than top for serverless)
            for submission in subreddit.hot(limit=limit * 2):
                # Skip pinned posts
                if submission.stickied:
                    continue
                
                post_data = {
                    'reddit_id': submission.id,
                    'hn_id': f"reddit_{submission.id}",
                    'title': submission.title,
                    'url': submission.url,
                    'domain': self._extract_domain(submission.url),
                    'score': submission.score,
                    'author': str(submission.author) if submission.author else 'deleted',
                    'time_posted': int(submission.created_utc),
                    'num_comments': submission.num_comments,
                    'story_text': submission.selftext[:200] if submission.selftext else '',
                    'story_type': 'reddit_post',
                    'subreddit': 'OutOfTheLoop',
                    'scraped_at': datetime.now().isoformat(),
                    'permalink': f"https://reddit.com{submission.permalink}",
                    'flair_text': submission.link_flair_text if submission.link_flair_text else ''
                }
                
                posts.append(post_data)
                
                if len(posts) >= limit:
                    break
            
            # Sort by score
            posts.sort(key=lambda x: x['score'], reverse=True)
            return posts[:limit]
            
        except Exception as e:
            print(f"⚠️ Error fetching live posts: {e}")
            return self.get_sample_posts()[:limit]
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or 'reddit.com'
        except Exception:
            return 'reddit.com'
    
    def get_stats(self) -> Dict:
        """Get Reddit stats for display."""
        return {
            'subreddit': 'OutOfTheLoop',
            'platform': 'Reddit',
            'connected': self.connected,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Live' if self.connected else 'Demo Mode'
        }

# Global instance for Vercel
reddit_manager = None

def get_reddit_manager():
    """Get or create Reddit manager instance."""
    global reddit_manager
    if reddit_manager is None:
        reddit_manager = VercelRedditManager()
    return reddit_manager
