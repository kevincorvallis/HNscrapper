#!/bin/bash
# Cron job script for weekly podcast generation
# Should be run every Sunday at 6 AM
# Add to crontab with: 0 6 * * 0 /path/to/weekly-cron.sh

# Navigate to project directory
cd /Users/kle/Downloads/HNscrapper

# Activate virtual environment
source venv/bin/activate

# Run weekly podcast generation
python auto_weekly_podcast_runner.py

# Log the execution
echo "$(date): Weekly podcast generation attempted" >> /var/log/hn-weekly-podcast.log
