#!/usr/bin/env python3
"""
Automated Weekly Podcast Runner
Designed to be run as a cron job every Sunday to generate weekly podcast episodes
"""

import os
import sys
from datetime import datetime, timedelta
from weekly_podcast_generator import WeeklyPodcastGenerator

def main():
    """Main function to run weekly podcast generation."""
    print(f"🗓️ Weekly Podcast Runner - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if today is Sunday (weekday 6)
    today = datetime.now()
    if today.weekday() != 6:
        print(f"⚠️  Today is {today.strftime('%A')}, not Sunday. Weekly episodes are generated on Sundays.")
        print("   You can still force generation by passing 'force' as an argument.")
        if len(sys.argv) < 2 or sys.argv[1] != 'force':
            return
        print("   🔄 Forcing generation...")
    
    generator = WeeklyPodcastGenerator()
    
    # Check if this week's episode already exists
    week_start, week_end = generator.get_week_date_range()
    recent_episodes = generator.get_recent_weekly_episodes(1)
    
    if recent_episodes and recent_episodes[0].get('week_start') == week_start:
        print(f"✅ Weekly episode for {week_start} to {week_end} already exists")
        print(f"   Title: {recent_episodes[0].get('title')}")
        if recent_episodes[0].get('audio_path'):
            print(f"   Audio: {recent_episodes[0].get('audio_path')}")
        return
    
    print(f"🎙️ Generating weekly episode for past 7 days ({week_start} to {week_end})")
    
    # Generate the episode
    episode = generator.generate_weekly_episode()
    
    if episode:
        print(f"\n🎉 Weekly episode generated successfully!")
        print(f"   Title: {episode.title}")
        print(f"   Period: {episode.week_start} to {episode.week_end}")
        print(f"   Articles: {len(episode.articles_featured)} featured")
        if episode.audio_path:
            print(f"   Audio: {episode.audio_path}")
            print(f"   Duration: {episode.duration_seconds//60 if episode.duration_seconds else 'Unknown'}:{episode.duration_seconds%60:02d if episode.duration_seconds else '00'}")
    else:
        print("❌ Failed to generate weekly episode")
        sys.exit(1)

if __name__ == "__main__":
    main()
