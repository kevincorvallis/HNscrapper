# 🔍 Daily Reddit OutOfTheLoop Scraper

A lightweight, modular Reddit scraper that fetches the top 10 most upvoted recent posts from r/OutOfTheLoop each day and saves them to your existing DynamoDB setup.

## 🚀 Features

- **Daily Automation**: Fetches top posts from r/OutOfTheLoop daily at 9:00 AM
- **DynamoDB Integration**: Seamlessly integrates with your existing HN scraper DynamoDB tables
- **Flexible Scheduling**: Built-in scheduler or cron job support
- **Multiple Run Modes**: Test, manual scrape, scheduled, or view recent posts
- **Robust Error Handling**: Comprehensive logging and error recovery
- **Reddit API Compliance**: Uses PRAW library with proper rate limiting

## 📦 Installation

The scraper uses your existing requirements. PRAW has been added to `requirements.txt`:

```bash
pip install praw schedule
```

## 🔧 Configuration

The scraper uses the provided Reddit API credentials:

```python
reddit = praw.Reddit(
    client_id="ctOMq724MQhY4S-AWY2zAQ",
    client_secret="Kj2YrbB3qwHR_I0pG0wwhyS4xIUXlQ",
    user_agent="daily_outoftheloop_scraper by u/Historical_Order7790"
)
```

## 🎯 Usage

### Manual Scrape
```bash
python daily_reddit_scraper.py scrape
```

### Test Mode (No Saving)
```bash
python daily_reddit_scraper.py test
```

### View Recent Posts
```bash
python daily_reddit_scraper.py recent
```

### Scheduled Mode (Runs at 9:00 AM daily)
```bash
python daily_reddit_scraper.py schedule
```

### Default (Manual Scrape)
```bash
python daily_reddit_scraper.py
```

## 📊 Data Structure

Posts are saved to your DynamoDB `HN_article_data` table with these fields:

```python
{
    'reddit_id': 'abc123',                    # Original Reddit post ID
    'hn_id': 'reddit_abc123',                # Prefixed ID for distinction
    'title': 'Post title',
    'url': 'https://example.com',
    'domain': 'example.com',
    'score': 1250,                           # Upvotes
    'author': 'reddit_username',
    'time_posted': 1640995200,               # Unix timestamp
    'num_comments': 45,
    'story_text': 'Post content...',         # For text posts
    'story_type': 'reddit_post',             # Distinguishes from HN posts
    'subreddit': 'OutOfTheLoop',
    'upvote_ratio': 0.95,
    'is_video': false,
    'over_18': false,
    'scraped_at': '2024-01-01T09:00:00',
    'permalink': 'https://reddit.com/r/OutOfTheLoop/...',
    'flair_text': 'Answered'
}
```

## 🕘 Automated Scheduling

### Option 1: Built-in Scheduler
```bash
python daily_reddit_scraper.py schedule
```
Runs continuously and executes scraping at 9:00 AM daily.

### Option 2: Cron Job
Add to your crontab for system-level scheduling:

```bash
# Edit crontab
crontab -e

# Add this line for daily 9:00 AM execution
0 9 * * * /Users/kle/Downloads/HNscrapper/reddit_scraper_cron.sh
```

The included `reddit_scraper_cron.sh` script handles environment setup and logging.

## 📈 Integration with Existing System

The scraper integrates seamlessly with your existing HN system:

1. **Same DynamoDB Tables**: Uses your existing `HN_article_data` table
2. **Compatible Schema**: Reddit posts use the same field structure as HN articles
3. **Distinguishable Data**: Uses `reddit_` prefix and `story_type: 'reddit_post'`
4. **API Compatibility**: Works with your existing API endpoints by filtering `story_type`

## 🔍 Example API Queries

Your existing Flask API can filter Reddit posts:

```python
# Get only Reddit posts
reddit_posts = [
    article for article in articles 
    if article.get('story_type') == 'reddit_post'
]

# Get only HN posts
hn_posts = [
    article for article in articles 
    if article.get('story_type') != 'reddit_post'
]
```

## 🛠️ Troubleshooting

### Common Issues

1. **Reddit API Rate Limits**: PRAW handles this automatically
2. **DynamoDB Connectivity**: Ensure AWS credentials are configured
3. **Missing Dependencies**: Run `pip install -r requirements.txt`

### Debug Commands

```bash
# Test Reddit API connection
python daily_reddit_scraper.py test

# Check recent posts in database
python daily_reddit_scraper.py recent

# View detailed logs
tail -f reddit_scraper.log
```

## 📝 Logs

The scraper creates detailed logs:

- **Console Output**: Real-time progress and status
- **Log File**: `reddit_scraper.log` (when using cron script)
- **DynamoDB Status**: Connection and save success/failure

## 🎨 Customization

### Change Subreddit
Modify the subreddit in `fetch_outoftheloop()`:

```python
subreddit = self.reddit.subreddit("YourSubredditName")
```

### Adjust Post Limit
Change the default limit:

```python
posts = scraper.fetch_outoftheloop(limit=20, time_filter="day")
```

### Modify Schedule Time
Update the schedule time:

```python
schedule.every().day.at("06:00").do(scraper.run_daily_scrape)  # 6:00 AM
```

## 🤝 Contributing

The scraper is modular and extensible:

- Add new subreddits in `fetch_outoftheloop()`
- Extend data fields in the post extraction logic
- Add new scheduling options in `main()`
- Integrate with additional databases

## 📄 License

Uses the same license as your HN scraper project.

---

**🍯 Part of the Pookie B News Daily ecosystem** - Daily tech digest with AI-powered insights!
