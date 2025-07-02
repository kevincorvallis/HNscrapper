"""
🔗 Reddit Integration Example for Flask API
Shows how to integrate Reddit posts with your existing HN scraper API
"""

# Add this to your existing api/index.py file to include Reddit posts

@app.route('/api/reddit/recent')
def api_reddit_recent():
    """API endpoint for recent Reddit posts."""
    try:
        from daily_reddit_scraper import RedditOutOfTheLoopScraper
        
        scraper = RedditOutOfTheLoopScraper()
        posts = scraper.get_recent_posts(limit=20)
        
        return jsonify({
            'success': True,
            'reddit_posts': posts,
            'total': len(posts),
            'subreddit': 'OutOfTheLoop',
            'platform': 'Reddit via PRAW'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'platform': 'Reddit via PRAW'
        }), 500

@app.route('/api/combined/recent')
def api_combined_recent():
    """API endpoint for combined HN + Reddit posts."""
    try:
        # Get HN articles
        hn_articles = db_manager.get_all_articles()
        
        # Get Reddit posts
        from daily_reddit_scraper import RedditOutOfTheLoopScraper
        scraper = RedditOutOfTheLoopScraper()
        reddit_posts = scraper.get_recent_posts(limit=10)
        
        # Combine and sort by score
        all_posts = hn_articles + reddit_posts
        all_posts.sort(key=lambda x: int(x.get('score', 0)), reverse=True)
        
        return jsonify({
            'success': True,
            'articles': all_posts[:30],  # Top 30 combined
            'hn_count': len(hn_articles),
            'reddit_count': len(reddit_posts),
            'total': len(all_posts),
            'sources': ['HackerNews', 'Reddit r/OutOfTheLoop']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Update your main homepage to show Reddit posts
def get_combined_content():
    """Get combined HN and Reddit content for homepage."""
    try:
        # Get HN articles
        hn_articles = db_manager.get_all_articles()
        
        # Get Reddit posts
        from daily_reddit_scraper import RedditOutOfTheLoopScraper
        scraper = RedditOutOfTheLoopScraper()
        reddit_posts = scraper.get_recent_posts(limit=5)
        
        # Combine top posts
        top_posts = []
        
        # Add top HN posts
        hn_sorted = sorted(hn_articles, key=lambda x: int(x.get('score', 0)), reverse=True)
        top_posts.extend(hn_sorted[:3])
        
        # Add top Reddit posts
        reddit_sorted = sorted(reddit_posts, key=lambda x: int(x.get('score', 0)), reverse=True)
        top_posts.extend(reddit_sorted[:2])
        
        return {
            'top_posts': top_posts,
            'hn_count': len(hn_articles),
            'reddit_count': len(reddit_posts)
        }
    except:
        return {
            'top_posts': db_manager.get_all_articles()[:5],
            'hn_count': 0,
            'reddit_count': 0
        }

# Example HTML template update for homepage
COMBINED_HTML_TEMPLATE = """
<div class="content-section">
    <h2 style="color: white; text-align: center; margin-bottom: 30px;">
        📰 Today's Top Stories
    </h2>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
        <div style="background: rgba(255,255,255,0.9); padding: 20px; border-radius: 15px;">
            <h3>🔥 Hacker News</h3>
            <p>{hn_count} articles analyzed</p>
        </div>
        <div style="background: rgba(255,255,255,0.9); padding: 20px; border-radius: 15px;">
            <h3>🤔 Reddit OutOfTheLoop</h3>
            <p>{reddit_count} posts analyzed</p>
        </div>
    </div>
</div>
"""
