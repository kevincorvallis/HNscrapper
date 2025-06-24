#!/usr/bin/env python3
"""
Serverless scraping function for Vercel.
Handles HN scraping in a serverless environment.
"""

import json
import os
import sqlite3
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import tldextract

def handler(request):
    """Vercel function handler for scraping."""
    
    # Verify authorization
    auth_header = request.headers.get('Authorization', '')
    expected_auth = f"Bearer {os.environ.get('CRON_SECRET', 'default-secret')}"
    
    if auth_header != expected_auth:
        return {
            'statusCode': 401,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Unauthorized'})
        }
    
    try:
        if request.method == 'POST':
            # Trigger scraping
            results = scrape_hn_articles()
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': True,
                    'articles_scraped': len(results),
                    'timestamp': datetime.now().isoformat()
                })
            }
        else:
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def scrape_hn_articles(limit=20):
    """Scrape HN articles for serverless environment."""
    
    # HN best articles URL
    url = "https://news.ycombinator.com/best"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; HN-Scraper-Vercel/1.0)'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []
    
    # Find article rows
    for i, item in enumerate(soup.find_all('tr', class_='athing')[:limit]):
        try:
            # Get article details
            title_elem = item.find('span', class_='titleline')
            if not title_elem:
                continue
                
            link_elem = title_elem.find('a')
            if not link_elem:
                continue
                
            title = link_elem.text.strip()
            url = link_elem.get('href', '')
            
            # Extract domain
            if url.startswith('item?'):
                url = f"https://news.ycombinator.com/{url}"
                domain = "news.ycombinator.com"
            else:
                domain = tldextract.extract(url).registered_domain
            
            article_data = {
                'hn_id': f"scraped_{int(datetime.now().timestamp())}_{i}",
                'title': title,
                'url': url,
                'domain': domain,
                'scraped_at': datetime.now().isoformat()
            }
            
            articles.append(article_data)
            
        except Exception as e:
            print(f"Error processing article {i}: {e}")
            continue
    
    # Store articles (you might want to use external storage like Supabase)
    store_articles(articles)
    
    return articles

def store_articles(articles):
    """Store articles in database (temporary SQLite for demo)."""
    try:
        # In production, you'd use external storage like Supabase or Vercel KV
        db_path = '/tmp/enhanced_hn_articles.db'
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS article_analyses (
                hn_id TEXT PRIMARY KEY,
                title TEXT,
                url TEXT,
                domain TEXT,
                summary TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert articles
        for article in articles:
            cursor.execute('''
                INSERT OR REPLACE INTO article_analyses 
                (hn_id, title, url, domain, summary, generated_at) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                article['hn_id'],
                article['title'],
                article['url'],
                article['domain'],
                f"Scraped from HN: {article['title'][:100]}...",
                article['scraped_at']
            ))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error storing articles: {e}")

# For local testing
if __name__ == "__main__":
    class MockRequest:
        def __init__(self):
            self.method = 'POST'
            self.headers = {'Authorization': f"Bearer {os.environ.get('CRON_SECRET', 'test')}"}
    
    result = handler(MockRequest())
    print(json.dumps(result, indent=2))
