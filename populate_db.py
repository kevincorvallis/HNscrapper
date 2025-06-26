#!/usr/bin/env python3
"""
Populate database with sample HN articles for demo purposes.
"""

import sqlite3
import json
from datetime import datetime, timedelta

# Sample articles with realistic HN content
sample_articles = [
    {
        'hn_id': '38745892',
        'title': 'Show HN: I built a tool to analyze Hacker News discussions using AI',
        'url': 'https://github.com/user/hn-analyzer',
        'domain': 'github.com',
        'summary': 'A comprehensive tool that scrapes Hacker News discussions and uses OpenAI to analyze comment sentiment, extract key insights, and identify the most valuable contributions to each thread.',
        'generated_at': (datetime.now() - timedelta(hours=2)).isoformat()
    },
    {
        'hn_id': '38745123',
        'title': 'The State of JavaScript 2024: What 20,000+ Developers Think',
        'url': 'https://stateofjs.com/2024',
        'domain': 'stateofjs.com',
        'summary': 'Annual survey reveals React maintains dominance while new frameworks like Astro and SvelteKit gain significant traction. TypeScript adoption reaches 87% among professional developers.',
        'generated_at': (datetime.now() - timedelta(hours=4)).isoformat()
    },
    {
        'hn_id': '38744567',
        'title': 'Why I Left Google After 8 Years',
        'url': 'https://blog.example.com/leaving-google',
        'domain': 'blog.example.com',
        'summary': 'A senior engineer shares insights on Google\'s changing culture, the impact of layoffs, and why smaller companies offer more meaningful work and faster iteration cycles.',
        'generated_at': (datetime.now() - timedelta(hours=6)).isoformat()
    },
    {
        'hn_id': '38743901',
        'title': 'Scientists Discover Method to Convert CO2 into Fuel Using Sunlight',
        'url': 'https://nature.com/articles/breakthrough-co2-fuel',
        'domain': 'nature.com',
        'summary': 'Breakthrough research demonstrates a novel photocatalytic process that efficiently converts atmospheric CO2 into usable hydrocarbon fuels, potentially revolutionizing carbon capture technology.',
        'generated_at': (datetime.now() - timedelta(hours=8)).isoformat()
    },
    {
        'hn_id': '38743445',
        'title': 'Ask HN: Best practices for scaling from 10 to 100 engineers?',
        'url': 'https://news.ycombinator.com/item?id=38743445',
        'domain': 'news.ycombinator.com',
        'summary': 'Community discussion on engineering management challenges, team structure, communication processes, and technical architecture decisions when rapidly scaling engineering teams.',
        'generated_at': (datetime.now() - timedelta(hours=12)).isoformat()
    },
    {
        'hn_id': '38742889',
        'title': 'Rust in Production: Lessons from Rewriting Our Backend',
        'url': 'https://techblog.company.com/rust-migration',
        'domain': 'techblog.company.com',
        'summary': 'Engineering team shares their 18-month journey migrating from Python to Rust, covering performance gains, developer experience challenges, and key architectural decisions.',
        'generated_at': (datetime.now() - timedelta(hours=16)).isoformat()
    },
    {
        'hn_id': '38742334',
        'title': 'OpenAI Announces GPT-5: Multimodal AI with Video Understanding',
        'url': 'https://openai.com/blog/gpt-5',
        'domain': 'openai.com',
        'summary': 'Next-generation language model introduces native video processing, improved reasoning capabilities, and significantly reduced hallucination rates compared to previous versions.',
        'generated_at': (datetime.now() - timedelta(hours=20)).isoformat()
    },
    {
        'hn_id': '38741778',
        'title': 'The Hidden Costs of Microservices: A 5-Year Retrospective',
        'url': 'https://engineering.bigtech.com/microservices-costs',
        'domain': 'engineering.bigtech.com',
        'summary': 'Detailed analysis of operational overhead, debugging complexity, and infrastructure costs that emerged after migrating to microservices architecture at scale.',
        'generated_at': (datetime.now() - timedelta(hours=24)).isoformat()
    }
]

# Sample comments for some articles
sample_comments = [
    {
        'comment_id': 'comment_001',
        'content': 'This is exactly what I\'ve been looking for! The AI analysis of comment sentiment is particularly interesting. Have you considered adding support for other discussion platforms?',
        'quality_score': 8,
        'analyzed_at': datetime.now().isoformat()
    },
    {
        'comment_id': 'comment_002', 
        'content': 'Great work! The GitHub repo looks solid. One suggestion: it would be helpful to have more documentation on the API endpoints.',
        'quality_score': 7,
        'analyzed_at': datetime.now().isoformat()
    },
    {
        'comment_id': 'comment_003',
        'content': 'The TypeScript numbers don\'t surprise me. What\'s interesting is the growth in build tools - seems like the ecosystem is finally stabilizing.',
        'quality_score': 6,
        'analyzed_at': datetime.now().isoformat()
    },
    {
        'comment_id': 'comment_004',
        'content': 'As someone who went through a similar transition, the points about team communication are spot on. The biggest challenge isn\'t technical.',
        'quality_score': 9,
        'analyzed_at': datetime.now().isoformat()
    },
    {
        'comment_id': 'comment_005',
        'content': 'This could be huge for climate tech. The efficiency numbers look promising, but I\'d love to see more details on the scalability aspects.',
        'quality_score': 7,
        'analyzed_at': datetime.now().isoformat()
    }
]

def populate_database():
    """Populate the database with sample data."""
    conn = sqlite3.connect('enhanced_hn_articles.db')
    cursor = conn.cursor()
    
    # Clear existing data except the original sample
    cursor.execute("DELETE FROM article_analyses WHERE hn_id != 'sample1'")
    cursor.execute("DELETE FROM comment_analyses")
    
    # Insert sample articles
    for article in sample_articles:
        cursor.execute('''
            INSERT OR REPLACE INTO article_analyses 
            (hn_id, title, url, domain, summary, generated_at) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            article['hn_id'],
            article['title'], 
            article['url'],
            article['domain'],
            article['summary'],
            article['generated_at']
        ))
    
    # Insert sample comments
    for comment in sample_comments:
        cursor.execute('''
            INSERT OR REPLACE INTO comment_analyses
            (comment_id, content, quality_score, analyzed_at)
            VALUES (?, ?, ?, ?)
        ''', (
            comment['comment_id'],
            comment['content'],
            comment['quality_score'],
            comment['analyzed_at']
        ))
    
    conn.commit()
    conn.close()
    
    print(f"Successfully populated database with {len(sample_articles)} articles and {len(sample_comments)} comments")

if __name__ == "__main__":
    populate_database()
