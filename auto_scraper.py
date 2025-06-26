#!/usr/bin/env python3
"""
Auto-scraper script that runs the daily scraper at regular intervals.
Only scrapes new articles to avoid duplicates and reduce processing time.
"""

import time
import schedule
from daily_scraper import HNScraper
from datetime import datetime

def run_incremental_scrape():
    """Run an incremental scrape that only gets new articles."""
    print(f"\n{'='*60}")
    print(f"Starting incremental scrape at {datetime.now()}")
    print(f"{'='*60}")
    
    scraper = HNScraper()
    
    # Run with limited articles to reduce load
    results = scraper.scrape_daily(max_articles=10, max_comments_per_article=30)
    
    # Print results
    print(f"\nScrape Results:")
    print(f"  - New articles: {results['scraped_articles']}")
    print(f"  - New comments: {results['total_comments']}")
    print(f"  - Success: {results['success']}")
    
    # Print database stats
    stats = scraper.get_stats()
    print(f"\nDatabase Stats:")
    print(f"  - Total articles: {stats['total_articles']}")
    print(f"  - Total comments: {stats['total_comments']}")
    print(f"  - Average score: {stats['avg_score']}")
    print(f"  - Unique domains: {stats['unique_domains']}")
    
    print(f"\nNext scrape scheduled for 2 hours from now...")
    print(f"{'='*60}\n")

def main():
    """Main scheduler function."""
    print("🚀 HN Auto-Scraper Started!")
    print("⏰ Will scrape every 2 hours for new articles")
    print("💾 Database will grow incrementally without duplicates")
    print("🛑 Press Ctrl+C to stop\n")
    
    # Schedule the scraper to run every 2 hours
    schedule.every(2).hours.do(run_incremental_scrape)
    
    # Run once immediately
    run_incremental_scrape()
    
    # Keep the scheduler running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n🛑 Auto-scraper stopped by user")
        print("✅ Database preserved with all scraped data")

if __name__ == "__main__":
    main()
