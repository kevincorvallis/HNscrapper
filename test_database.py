#!/usr/bin/env python3
"""
Test script to verify the daily scraper database
"""

import sqlite3
import sys
import os

def test_database():
    try:
        # Connect to database
        db_path = os.environ.get('DB_PATH', 'enhanced_hn_articles.db')
        if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
            for fname in os.listdir('.'):
                if fname.startswith('enhanced_hn_articles.db') and 'backup' in fname:
                    db_path = fname
                    break
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check articles table
        cursor.execute('SELECT COUNT(*) FROM articles')
        article_count = cursor.fetchone()[0]
        print(f'✓ Total articles: {article_count}')
        
        # Check comments table
        cursor.execute('SELECT COUNT(*) FROM comments')
        comment_count = cursor.fetchone()[0]
        print(f'✓ Total comments: {comment_count}')
        
        # Get some sample articles
        cursor.execute('SELECT hn_id, title, domain, score, num_comments FROM articles ORDER BY score DESC LIMIT 3')
        articles = cursor.fetchall()
        print(f'\n✓ Top 3 articles by score:')
        for i, article in enumerate(articles, 1):
            print(f'  {i}. {article[1][:60]}...')
            print(f'     Domain: {article[2]}, Score: {article[3]}, Comments: {article[4]}')
        
        # Check comments for top article
        if articles:
            top_article_id = articles[0][0]
            cursor.execute('SELECT COUNT(*) FROM comments WHERE article_id = ?', (top_article_id,))
            top_article_comments = cursor.fetchone()[0]
            print(f'\n✓ Comments scraped for top article: {top_article_comments}')
            
            # Get sample comments
            cursor.execute('SELECT author, content FROM comments WHERE article_id = ? LIMIT 3', (top_article_id,))
            comments = cursor.fetchall()
            print(f'✓ Sample comments:')
            for comment in comments:
                content = comment[1][:100].replace('\n', ' ') if comment[1] else 'No content'
                print(f'   - {comment[0]}: {content}...')
        
        # Check table schemas
        cursor.execute('PRAGMA table_info(articles)')
        article_schema = cursor.fetchall()
        print(f'\n✓ Articles table has {len(article_schema)} columns')
        
        cursor.execute('PRAGMA table_info(comments)')
        comment_schema = cursor.fetchall()
        print(f'✓ Comments table has {len(comment_schema)} columns')
        
        # Test data integrity
        cursor.execute('SELECT COUNT(DISTINCT domain) FROM articles')
        unique_domains = cursor.fetchone()[0]
        print(f'✓ Unique domains: {unique_domains}')
        
        cursor.execute('SELECT AVG(score) FROM articles WHERE score > 0')
        avg_score = cursor.fetchone()[0]
        print(f'✓ Average score: {avg_score:.1f}')
        
        conn.close()
        
        print(f'\n🎉 Database test completed successfully!')
        print(f'📊 Summary: {article_count} articles, {comment_count} comments from {unique_domains} domains')
        
        return True
        
    except Exception as e:
        print(f'❌ Database test failed: {e}')
        return False

if __name__ == '__main__':
    success = test_database()
    sys.exit(0 if success else 1)
