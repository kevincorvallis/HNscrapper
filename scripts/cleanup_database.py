#!/usr/bin/env python3
"""
Database cleanup script to fix malformed thread_summary JSON.
"""

import sqlite3
import json
import re
import os

def clean_thread_summaries(db_path: str):
    """Clean up malformed thread_summary data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Cleaning up thread summary data...")
    
    # Get all thread summaries
    cursor.execute('SELECT thread_id, thread_summary FROM discussion_threads')
    threads = cursor.fetchall()
    
    cleaned_count = 0
    for thread_id, thread_summary in threads:
        if not thread_summary:
            continue
            
        cleaned_summary = thread_summary
        
        # Remove JSON markdown blocks
        if '```json' in cleaned_summary:
            cleaned_summary = re.sub(r'```json\s*', '', cleaned_summary)
            cleaned_summary = re.sub(r'```.*$', '', cleaned_summary, flags=re.MULTILINE)
        
        # Try to extract JSON if it exists
        try:
            # Look for JSON patterns
            json_match = re.search(r'\{[^}]*"thread_summary"[^}]*\}', cleaned_summary)
            if json_match:
                json_data = json.loads(json_match.group())
                cleaned_summary = json_data.get('thread_summary', cleaned_summary)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Fallback: extract first meaningful sentence
        if cleaned_summary.startswith('{') or '```' in cleaned_summary:
            # Find the first complete sentence
            sentences = re.split(r'[.!?]+', cleaned_summary.replace('\\n', ' '))
            meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20 and not s.strip().startswith('{')]
            if meaningful_sentences:
                cleaned_summary = meaningful_sentences[0] + '.'
            else:
                cleaned_summary = "Discussion covers various technical topics and community perspectives."
        
        # Clean up extra whitespace
        cleaned_summary = ' '.join(cleaned_summary.split())
        
        # Ensure reasonable length
        if len(cleaned_summary) > 300:
            cleaned_summary = cleaned_summary[:297] + '...'
        elif len(cleaned_summary) < 10:
            cleaned_summary = "Engaging discussion with diverse viewpoints on the topic."
            
        # Update if changed
        if cleaned_summary != thread_summary:
            cursor.execute(
                'UPDATE discussion_threads SET thread_summary = ? WHERE thread_id = ?',
                (cleaned_summary, thread_id)
            )
            cleaned_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"✅ Cleaned {cleaned_count} thread summaries")

def main():
    """Main cleanup function."""
    project_root = os.path.dirname(os.path.dirname(__file__))
    db_path = os.path.join(project_root, 'data', 'enhanced_hn_articles.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    clean_thread_summaries(db_path)
    print("🎉 Database cleanup completed!")

if __name__ == '__main__':
    main()
