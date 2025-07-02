#!/usr/bin/env python3
"""
Test script for the enhanced HN scraper with vote tracking
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'scrapers'))

from hn_scraper import EnhancedHackerNewsScraper
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_vote_tracking():
    """Test the vote tracking functionality"""
    print("Testing Enhanced HN Scraper with Vote Tracking...")
    
    # Create scraper
    scraper = EnhancedHackerNewsScraper("test_enhanced_hn.db")
    
    # Test with just 1 page and max 5 articles
    articles = scraper.scrape_articles_with_comments(
        pages=1, 
        max_articles=5, 
        skip_processed=False  # Enable vote tracking
    )
    
    print(f"\nProcessed {len(articles)} articles")
    
    # Display results
    for article in articles:
        print(f"\nTitle: {article['title']}")
        print(f"Score: {article.get('score', 0)}")
        print(f"Author: {article.get('author', 'Unknown')}")
        print(f"Rank: {article.get('rank', 'N/A')}")
        print(f"Comments: {article.get('actual_comment_count', 0)}")
        print(f"Domain: {article['domain']}")
    
    # Test historical data query
    if articles:
        first_article = articles[0]
        hn_id = first_article['hn_id']
        print(f"\nGetting history for article {hn_id}...")
        
        history = scraper.get_article_history(hn_id)
        print(f"Found {len(history)} historical entries")
        for entry in history:
            print(f"  Score: {entry['score']}, Comments: {entry['comment_count']}, Time: {entry['scraped_at']}")
    
    # Test trending articles
    print("\nGetting trending articles (last 24 hours)...")
    trending = scraper.get_trending_articles(24)
    print(f"Found {len(trending)} trending articles")
    
    for trend in trending[:3]:  # Show top 3
        print(f"  {trend['title']} - Score increase: {trend['score_increase']}")

if __name__ == "__main__":
    test_vote_tracking()
