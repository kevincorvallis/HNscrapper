#!/usr/bin/env python3
"""
Serverless scraping function for Vercel.
Handles HN scraping in a serverless environment.
"""

import json
import os
import sys
import requests
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# Optional DynamoDB support
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from dynamodb_manager import DynamoDBManager
    USE_DYNAMODB = True
except ImportError:
    USE_DYNAMODB = False
    print("DynamoDB not available, using local storage")


def handler(request):
    """Main handler function for Vercel serverless."""

    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json'
    }

    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }

    auth_header = request.headers.get('Authorization', '')
    expected_auth = f"Bearer {os.environ.get('CRON_SECRET', 'default-secret')}"

    if auth_header != expected_auth:
        return {
            'statusCode': 401,
            'headers': headers,
            'body': json.dumps({'error': 'Unauthorized'})
        }

    try:
        results = scrape_hn_articles()
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'articles_scraped': len(results),
                'timestamp': datetime.now().isoformat()
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'success': False, 'error': str(e)})
        }


def scrape_hn_articles(limit=20):
    """Scrape HN articles from the 'best' page."""
    url = "https://news.ycombinator.com/best"
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; HN-Scraper-Vercel/1.0)'}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []

    for i, item in enumerate(soup.find_all('tr', class_='athing')[:limit]):
        try:
            title_elem = item.find('span', class_='titleline')
            link_elem = title_elem.find('a') if title_elem else None
            if not link_elem:
                continue

            title = link_elem.text.strip()
            link = link_elem.get('href', '')

            if link.startswith('item?'):
                link = f"https://news.ycombinator.com/{link}"
                domain = "news.ycombinator.com"
            else:
                parsed = urlparse(link)
                domain = parsed.netloc.replace('www.', '')

            article = {
                'hn_id': f"scraped_{int(datetime.now().timestamp())}_{i}",
                'title': title,
                'url': link,
                'domain': domain,
                'scraped_at': datetime.now().isoformat()
            }

            articles.append(article)
        except Exception as e:
            print(f"Error parsing article {i}: {e}")
            continue

    store_articles(articles)
    return articles


def store_articles(articles):
    """Store scraped articles in DynamoDB or fallback log."""
    try:
        if USE_DYNAMODB:
            db_manager = DynamoDBManager()
            for article in articles:
                db_manager.store_article(
                    hn_id=article['hn_id'],
                    title=article['title'],
                    url=article['url'],
                    domain=article['domain'],
                    scraped_at=article['scraped_at']
                )
            print(f"Successfully stored {len(articles)} articles in DynamoDB.")
        else:
            print(f"Would store {len(articles)} articles:")
            for article in articles:
                print(f"  - {article['title']}")
    except Exception as e:
        print(f"Error storing articles: {e}")
