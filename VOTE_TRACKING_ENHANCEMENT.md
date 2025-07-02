# Enhanced Hacker News Scraper - Vote Tracking Update

## Summary of Changes

Your HN scraper has been enhanced with comprehensive vote tracking and historical data capabilities! Here's what was added:

## 🎯 Key Features Added

### 1. **Vote/Score Tracking**
- ✅ Extracts vote scores from HN pages
- ✅ Captures author information
- ✅ Records article ranking position
- ✅ Tracks comment counts

### 2. **Historical Data Storage**
- ✅ New `article_history` table stores snapshots over time
- ✅ Tracks score changes, comment growth, ranking fluctuations
- ✅ Maintains `first_seen` and `last_updated` timestamps

### 3. **Update Behavior (No More Skipping)**
- ✅ **Default behavior changed**: Articles are now updated instead of skipped
- ✅ New flag `--skip-processed` defaults to `False` (enables vote tracking)
- ✅ Each run captures current metrics and stores historical snapshot

### 4. **Enhanced Database Schema**
```sql
-- Main articles table (current state)
processed_articles:
- url, hn_id, title, domain, author
- content_length, comment_count, score, rank
- first_seen, last_updated

-- Historical tracking table
article_history:
- hn_id, url, score, comment_count, rank
- scraped_at (timestamp for each snapshot)
```

### 5. **New Query Methods**
- `get_article_history(hn_id)` - Get vote history for any article
- `get_trending_articles(hours)` - Find articles with biggest score increases

### 6. **Enhanced Data Output**
- CSV exports now include: `score`, `author`, `rank`
- JSON exports include all new fields
- Console output shows scores in real-time

## 🚀 How It Works Now

### Daily Scraping Behavior:
1. **First Run**: Discovers new articles, captures initial metrics
2. **Subsequent Runs**: Updates existing articles with current scores/comments
3. **Historical Tracking**: Every run stores a snapshot in `article_history`
4. **Trend Analysis**: Query which articles are gaining the most votes

### Example Output:
```
Processing item 1/5: Gemini CLI (Score: 1395)
Updating existing article: Gemini CLI
Captured 764 comments (HN reported 764)
```

### Vote History Example:
```sql
SELECT score, comment_count, scraped_at 
FROM article_history 
WHERE hn_id = '44376919'
ORDER BY scraped_at;

-- Results:
-- Score: 1200, Comments: 650, Time: 2025-06-27 10:00:00
-- Score: 1350, Comments: 720, Time: 2025-06-27 14:00:00  
-- Score: 1395, Comments: 764, Time: 2025-06-27 18:00:00
```

## 🔧 Usage

### Run with Vote Tracking (Default):
```bash
python src/scrapers/hn_scraper.py --pages 3
```

### Run with Old Behavior (Skip Processed):
```bash
python src/scrapers/hn_scraper.py --pages 3 --skip-processed
```

### Query Trending Articles:
```python
scraper = EnhancedHackerNewsScraper()
trending = scraper.get_trending_articles(24)  # Last 24 hours
for article in trending:
    print(f"{article['title']} - Score increase: {article['score_increase']}")
```

## 📊 Benefits for Daily Scraping

1. **Vote Momentum Tracking**: See which articles are gaining traction
2. **Comment Growth**: Track discussion engagement over time  
3. **Ranking Changes**: Monitor how articles move up/down the front page
4. **Trend Detection**: Identify viral content early
5. **Historical Analysis**: Build datasets for HN voting patterns

## 🗃️ Database Files
- Main database: `enhanced_hn_articles.db`
- Test database: `test_enhanced_hn.db` (for testing)

## ✅ Verification
The enhanced scraper has been tested and confirmed working:
- ✅ Vote scores extracted correctly
- ✅ Historical data stored properly
- ✅ Update logic working (no more skipping)
- ✅ Trending analysis functional
- ✅ All existing functionality preserved

Your scraper now provides comprehensive vote tracking for daily monitoring of HN trends! 🎉
