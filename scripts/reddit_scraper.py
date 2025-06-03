#!/usr/bin/env python3
"""
Reddit Discussion Scraper
Finds and scrapes relevant Reddit discussions for each article.
"""

import sqlite3
import requests
import time
import re
import json
from datetime import datetime
from urllib.parse import quote, urlparse

def clean_html(text):
    """Clean HTML tags and entities from text."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    text = text.replace('&#x27;', "'").replace('&quot;', '"')
    text = text.replace('&nbsp;', ' ')
    return text.strip()

def search_reddit_discussions(title, url):
    """Search Reddit for discussions about an article."""
    print(f"🔍 Searching Reddit for: {title[:50]}...")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    discussions = []
    
    # Search strategies
    search_terms = [
        title,
        urlparse(url).netloc if url else "",
        # Extract key terms from title
        ' '.join([word for word in title.split() if len(word) > 4])[:100]
    ]
    
    for search_term in search_terms:
        if not search_term.strip():
            continue
            
        try:
            # Search Reddit API
            search_url = f"https://www.reddit.com/search.json"
            params = {
                'q': search_term,
                'sort': 'relevance',
                'limit': 10,
                't': 'month'  # Last month
            }
            
            response = session.get(search_url, params=params)
            if response.status_code != 200:
                print(f"⚠️  Reddit search failed: {response.status_code}")
                continue
                
            data = response.json()
            if 'data' not in data or 'children' not in data['data']:
                continue
                
            for post in data['data']['children']:
                post_data = post['data']
                
                # Skip if not relevant enough
                if post_data.get('score', 0) < 5:
                    continue
                    
                discussion = {
                    'reddit_id': post_data.get('id'),
                    'title': post_data.get('title', ''),
                    'subreddit': post_data.get('subreddit', ''),
                    'author': post_data.get('author', ''),
                    'score': post_data.get('score', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'url': f"https://reddit.com{post_data.get('permalink', '')}",
                    'created_utc': post_data.get('created_utc', 0),
                    'selftext': clean_html(post_data.get('selftext', '')),
                    'relevance_score': calculate_relevance(title, post_data.get('title', ''))
                }
                
                # Only add if sufficiently relevant
                if discussion['relevance_score'] > 0.3:
                    discussions.append(discussion)
                    
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"⚠️  Error searching Reddit: {e}")
            continue
    
    # Remove duplicates and sort by relevance
    seen_ids = set()
    unique_discussions = []
    for disc in discussions:
        if disc['reddit_id'] not in seen_ids:
            seen_ids.add(disc['reddit_id'])
            unique_discussions.append(disc)
    
    unique_discussions.sort(key=lambda x: (x['relevance_score'], x['score']), reverse=True)
    return unique_discussions[:5]  # Top 5 most relevant

def calculate_relevance(article_title, reddit_title):
    """Calculate relevance score between article and Reddit post."""
    if not article_title or not reddit_title:
        return 0
    
    article_words = set(re.findall(r'\b\w+\b', article_title.lower()))
    reddit_words = set(re.findall(r'\b\w+\b', reddit_title.lower()))
    
    # Remove common words
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'}
    article_words -= common_words
    reddit_words -= common_words
    
    if not article_words or not reddit_words:
        return 0
    
    intersection = article_words & reddit_words
    union = article_words | reddit_words
    
    return len(intersection) / len(union) if union else 0

def collect_reddit_comments(reddit_id, subreddit):
    """Collect comments from a Reddit post."""
    print(f"💬 Collecting Reddit comments for {reddit_id}...")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    try:
        # Get Reddit post comments
        url = f"https://www.reddit.com/r/{subreddit}/comments/{reddit_id}.json"
        response = session.get(url)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        if len(data) < 2 or 'data' not in data[1] or 'children' not in data[1]['data']:
            return []
        
        comments = []
        
        def process_comment(comment_data, depth=0, parent_id=None):
            if depth > 5 or len(comments) >= 50:  # Limit depth and total
                return
                
            comment = {
                'reddit_comment_id': comment_data.get('id'),
                'author': comment_data.get('author', '[deleted]'),
                'body': clean_html(comment_data.get('body', '')),
                'score': comment_data.get('score', 0),
                'depth': depth,
                'parent_id': parent_id,
                'created_utc': comment_data.get('created_utc', 0),
                'permalink': comment_data.get('permalink', '')
            }
            
            if comment['body'] and comment['body'] not in ['[deleted]', '[removed]']:
                comments.append(comment)
            
            # Process replies
            if 'replies' in comment_data and comment_data['replies']:
                if isinstance(comment_data['replies'], dict):
                    replies_data = comment_data['replies']
                    if 'data' in replies_data and 'children' in replies_data['data']:
                        for reply in replies_data['data']['children']:
                            if reply['kind'] == 't1':  # Comment
                                process_comment(reply['data'], depth + 1, comment['reddit_comment_id'])
        
        # Process all top-level comments
        for comment in data[1]['data']['children']:
            if comment['kind'] == 't1':  # Comment
                process_comment(comment['data'])
        
        print(f"✅ Collected {len(comments)} Reddit comments")
        return comments
        
    except Exception as e:
        print(f"⚠️  Error collecting Reddit comments: {e}")
        return []

def main():
    """Main function to scrape Reddit discussions for all articles."""
    print("🚀 Reddit Discussion Scraper")
    print("=" * 50)
    
    # Connect to database
    conn = sqlite3.connect('/Users/kevin/Downloads/HNscrapper/data/enhanced_hn_articles.db')
    cursor = conn.cursor()
    
    # Get all articles
    cursor.execute("SELECT id, title, url FROM nyt_articles LIMIT 5")
    articles = cursor.fetchall()
    
    total_reddit_posts = 0
    total_reddit_comments = 0
    
    for i, (article_id, title, url) in enumerate(articles, 1):
        print(f"\n📰 Article {i}/{len(articles)}")
        print(f"🚀 Processing: {title}")
        
        # Search for Reddit discussions
        discussions = search_reddit_discussions(title, url)
        
        if not discussions:
            print("❌ No relevant Reddit discussions found")
            continue
        
        print(f"✅ Found {len(discussions)} relevant Reddit discussions")
        
        # Store Reddit discussions
        for discussion in discussions:
            cursor.execute("""
                INSERT OR REPLACE INTO reddit_discussions 
                (article_id, reddit_id, title, subreddit, author, score, num_comments, url, created_utc, selftext, relevance_score, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article_id, discussion['reddit_id'], discussion['title'], discussion['subreddit'],
                discussion['author'], discussion['score'], discussion['num_comments'], discussion['url'],
                discussion['created_utc'], discussion['selftext'], discussion['relevance_score'],
                datetime.now().isoformat()
            ))
            
            # Collect comments for top discussion
            if discussion == discussions[0]:  # Only for most relevant
                reddit_comments = collect_reddit_comments(discussion['reddit_id'], discussion['subreddit'])
                
                for comment in reddit_comments:
                    cursor.execute("""
                        INSERT OR REPLACE INTO enhanced_comments
                        (article_id, source, comment_id, author, text, score, depth, parent_id, created_at, credibility_score, quality_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        article_id, 'reddit', comment['reddit_comment_id'], comment['author'],
                        comment['body'], comment['score'], comment['depth'], comment['parent_id'],
                        datetime.fromtimestamp(comment['created_utc']).isoformat() if comment['created_utc'] else datetime.now().isoformat(),
                        min(comment['score'] / 10, 10),  # Simple credibility score
                        len(comment['body']) / 100  # Simple quality score
                    ))
                
                total_reddit_comments += len(reddit_comments)
        
        total_reddit_posts += len(discussions)
        conn.commit()
        time.sleep(2)  # Rate limiting
    
    print(f"\n🎉 Reddit Scraping Complete!")
    print(f"📊 Total Reddit posts found: {total_reddit_posts}")
    print(f"💬 Total Reddit comments collected: {total_reddit_comments}")
    
    conn.close()

if __name__ == "__main__":
    main()
