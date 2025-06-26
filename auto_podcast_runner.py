#!/usr/bin/env python3
"""
Automated Daily Podcast Runner
Simple script to generate daily podcasts that can be run via cron or task scheduler
"""

import sys
import os
from datetime import datetime, timedelta
import argparse
from daily_podcast_generator import DailyPodcastGenerator

def run_daily_podcast(date_str: str = None, verbose: bool = True):
    """Run the daily podcast generation."""
    try:
        generator = DailyPodcastGenerator()
        
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        if verbose:
            print(f"🚀 Starting daily podcast generation for {date_str}")
        
        episode = generator.generate_daily_episode(date_str)
        
        if episode:
            if verbose:
                print(f"✅ Successfully generated podcast for {date_str}")
                print(f"   Title: {episode.title}")
                print(f"   Duration: ~{episode.duration_seconds//60 if episode.duration_seconds else '?'} minutes")
            return True
        else:
            if verbose:
                print(f"❌ Failed to generate podcast for {date_str}")
            return False
            
    except Exception as e:
        if verbose:
            print(f"💥 Error during podcast generation: {e}")
        return False

def run_backfill(days_back: int = 7, verbose: bool = True):
    """Generate podcasts for the last N days (useful for testing)."""
    success_count = 0
    total_days = days_back
    
    if verbose:
        print(f"📚 Backfilling podcasts for last {days_back} days...")
    
    for i in range(days_back):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        
        if verbose:
            print(f"\n📅 Processing {date} ({i+1}/{total_days})...")
        
        success = run_daily_podcast(date, verbose=False)
        if success:
            success_count += 1
            if verbose:
                print(f"   ✅ Success")
        else:
            if verbose:
                print(f"   ❌ Failed")
    
    if verbose:
        print(f"\n📊 Backfill complete: {success_count}/{total_days} episodes generated")
    
    return success_count

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='Generate daily Hacker News podcasts')
    parser.add_argument('--date', type=str, help='Specific date (YYYY-MM-DD)', default=None)
    parser.add_argument('--backfill', type=int, help='Backfill last N days', default=None)
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    
    args = parser.parse_args()
    
    verbose = not args.quiet
    
    if args.backfill:
        success_count = run_backfill(args.backfill, verbose)
        sys.exit(0 if success_count > 0 else 1)
    else:
        success = run_daily_podcast(args.date, verbose)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
