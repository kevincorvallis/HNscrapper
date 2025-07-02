#!/bin/bash
"""
🕘 Reddit OutOfTheLoop Cron Job Script
Runs the daily Reddit scraper at scheduled times
"""

# Navigate to the project directory
cd /Users/kle/Downloads/HNscrapper

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set current date for logging
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Log file path
LOG_FILE="reddit_scraper.log"

echo "[$DATE] Starting Reddit OutOfTheLoop scraper..." >> "$LOG_FILE"

# Run the scraper
python daily_reddit_scraper.py scrape >> "$LOG_FILE" 2>&1

# Log completion
COMPLETE_DATE=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$COMPLETE_DATE] Reddit scraper completed." >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
