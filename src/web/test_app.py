#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '../../analyzers')

from flask import Flask, render_template
import json

app = Flask(__name__)
app.secret_key = 'test-key'

# Simple test data
articles_data = []
domains = set()

def load_articles():
    global articles_data, domains
    json_path = os.path.join('..', '..', 'data', 'enhanced_hn_articles.json')
    
    try:
        print(f"Loading articles from: {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            articles_data = json.load(f)
        
        print(f"Loaded {len(articles_data)} articles")
        
        # Extract domains
        for article in articles_data[:10]:  # Limit to first 10 for testing
            if article.get('url'):
                try:
                    import tldextract
                    extracted = tldextract.extract(article['url'])
                    domain = f"{extracted.domain}.{extracted.suffix}"
                    if domain != ".":
                        domains.add(domain)
                        article['domain'] = domain
                except Exception as e:
                    print(f"Domain extraction error: {e}")
                    article['domain'] = 'unknown'
        
        print(f"Processed domains: {len(domains)}")
        
    except Exception as e:
        print(f"Error loading articles: {e}")
        articles_data = []
        domains = set()

@app.route('/')
def index():
    return f"<h1>HN Scraper Test</h1><p>Loaded {len(articles_data)} articles from {len(domains)} domains</p>"

if __name__ == '__main__':
    print("🔧 Loading test data...")
    load_articles()
    print(f"✅ Test app ready with {len(articles_data)} articles")
    print("🌐 Starting test Flask application on http://localhost:5000")
    app.run(debug=True, port=5000)

if __name__ == '__main__':
    print("Starting test Flask app...")
    load_articles()
    print(f"Starting server with {len(articles_data)} articles...")
    app.run(host='0.0.0.0', port=8083, debug=True)
