#!/bin/bash
# Cron job script for daily Hacker News scraping
# Should be run every day at 2 AM
# Add to crontab with: 0 2 * * * /path/to/daily_scraper_cron.sh

# Navigate to the project directory
cd /Users/kle/Downloads/HNscrapper

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Log file
LOG_FILE="hn_scraper.log"

DATE=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$DATE] Starting daily HN scrape..." >> "$LOG_FILE"

# Run the DynamoDB-enabled scraper
python daily_scraper_dynamodb.py >> "$LOG_FILE" 2>&1

COMPLETE_DATE=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$COMPLETE_DATE] Daily scrape finished." >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
