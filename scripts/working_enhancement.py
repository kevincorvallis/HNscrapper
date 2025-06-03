#!/usr/bin/env python3
"""
Working script to collect expanded HN comments and basic article summaries.
"""

import sqlite3
import requests
import time
import re
from datetime import datetime

def clean_html(text):
    """Clean HTML tags from text."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    text = text.replace('&#x27;', "'").replace('&quot;', '"')
    return text.strip()

def collect_expanded_comments(hn_id):
    """Collect all HN comments for an article."""
    print(f"🔍 Collecting comments for HN {hn_id}...")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    try:
        # Get article data
        response = session.get(f'https://hacker-news.firebaseio.com/v0/item/{hn_id}.json')
        if response.status_code != 200:
            return []
        
        article_data = response.json()
        if not article_data or 'kids' not in article_data:
            return []
        
        print(f"📊 Found {len(article_data['kids'])} top-level comments")
        comments = []
        processed_count = 0
        
        def fetch_comment_tree(comment_id, depth=0, parent_id=None):
            nonlocal processed_count
            try:
                if processed_count >= 200:  # Limit total comments
                    return
                
                response = session.get(f'https://hacker-news.firebaseio.com/v0/item/{comment_id}.json')
                if response.status_code != 200:
                    return
                
                comment_data = response.json()
                if not comment_data or not comment_data.get('text'):
                    return
                
                # Store comment
                comment = {
                    'source_id': str(comment_id),
                    'parent_id': str(parent_id) if parent_id else None,
                    'author': comment_data.get('by', 'Anonymous'),
                    'comment_text': clean_html(comment_data['text']),
                    'timestamp': str(comment_data.get('time', 0)),
                    'depth': depth,
                    'url': f'https://news.ycombinator.com/item?id={comment_id}'
                }
                comments.append(comment)
                processed_count += 1
                
                # Process replies (limit depth)
                if depth < 4 and 'kids' in comment_data and processed_count < 200:
                    for kid_id in comment_data['kids'][:15]:  # Limit replies per comment
                        fetch_comment_tree(kid_id, depth + 1, comment_id)
                
                # Rate limiting
                time.sleep(0.05)
                
            except Exception as e:
                print(f"⚠️  Error with comment {comment_id}: {e}")
        
        # Process top-level comments
        for kid_id in article_data['kids'][:50]:  # Process up to 50 top-level comments
            fetch_comment_tree(kid_id)
            if processed_count % 20 == 0:
                print(f"   Processed {processed_count} comments...")
        
        print(f"✅ Collected {len(comments)} total comments")
        return comments
        
    except Exception as e:
        print(f"❌ Error collecting comments: {e}")
        return []

def create_simple_summary(title, url):
    """Create a simple summary from title and basic analysis."""
    try:
        # For now, create a basic summary from the title
        # Later we can enhance this with actual content scraping
        
        key_themes = []
        title_lower = title.lower()
        
        # Identify themes from title
        if any(word in title_lower for word in ['ai', 'artificial intelligence', 'machine learning', 'gpt', 'llm']):
            key_themes.append('Artificial Intelligence')
        if any(word in title_lower for word in ['microsoft', 'google', 'apple', 'meta', 'amazon']):
            key_themes.append('Big Tech')
        if any(word in title_lower for word in ['startup', 'funding', 'venture', 'vc']):
            key_themes.append('Startups')
        if any(word in title_lower for word in ['programming', 'code', 'developer', 'software']):
            key_themes.append('Software Development')
        if any(word in title_lower for word in ['security', 'privacy', 'hack', 'breach']):
            key_themes.append('Security')
        
        summary = f"Discussion about {title}. This article explores {', '.join(key_themes) if key_themes else 'technology topics'} and has generated significant community discussion on Hacker News."
        
        return {
            'summary_text': summary,
            'key_points': ' | '.join(key_themes) if key_themes else 'Technology Discussion',
            'source_type': 'generated',
            'credibility_score': 0.7
        }
        
    except Exception as e:
        print(f"⚠️  Error creating summary: {e}")
        return None

def enhance_single_article(hn_id, title, url):
    """Enhance a single article with expanded comments and summary."""
    print(f"\n🚀 Enhancing article: {title}")
    print(f"🔗 URL: {url}")
    
    conn = sqlite3.connect('data/enhanced_hn_articles.db')
    cursor = conn.cursor()
    
    try:
        # 1. Create summary
        summary = create_simple_summary(title, url)
        if summary:
            cursor.execute('''
                INSERT OR REPLACE INTO enhanced_summaries (
                    article_hn_id, source_url, summary_text, key_points, source_type, credibility_score
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (hn_id, url, summary['summary_text'], summary['key_points'],
                 summary['source_type'], summary['credibility_score']))
            print(f"✅ Summary created")
        
        # 2. Collect expanded comments
        comments = collect_expanded_comments(hn_id)
        
        # 3. Store comments
        for comment in comments:
            cursor.execute('''
                INSERT OR REPLACE INTO enhanced_comments (
                    article_hn_id, source, source_id, parent_id, author, comment_text,
                    timestamp, url, depth
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (hn_id, 'hackernews', comment['source_id'], comment['parent_id'],
                 comment['author'], comment['comment_text'], comment['timestamp'],
                 comment['url'], comment['depth']))
        
        conn.commit()
        print(f"✅ Enhanced article {hn_id} with {len(comments)} comments")
        
        return len(comments)
        
    except Exception as e:
        print(f"❌ Error enhancing article: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def main():
    """Main enhancement function."""
    print("🚀 HN Discussion Enhancement")
    print("=" * 50)
    
    # Get first few articles for testing
    conn = sqlite3.connect('data/enhanced_hn_articles.db')
    cursor = conn.cursor()
    cursor.execute('SELECT hn_id, title, url FROM article_analyses LIMIT 5')
    articles = cursor.fetchall()
    conn.close()
    
    total_comments = 0
    for i, (hn_id, title, url) in enumerate(articles, 1):
        print(f"\n📰 Article {i}/5")
        comments_added = enhance_single_article(hn_id, title, url)
        total_comments += comments_added
        
        # Rate limiting between articles
        if i < len(articles):
            print("⏱️  Waiting 3 seconds...")
            time.sleep(3)
    
    print(f"\n🎉 Enhancement Complete!")
    print(f"📊 Total comments collected: {total_comments}")
    print(f"📈 Average per article: {total_comments / len(articles):.1f}")

if __name__ == "__main__":
    main()
