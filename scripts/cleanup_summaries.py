#!/usr/bin/env python3
"""
Clean up malformed summaries and key insights in the database
Remove JSON formatting artifacts and "Analysis generated" text
"""

import sqlite3
import re
import sys
from pathlib import Path

def clean_text(text):
    """Clean up malformed JSON and analysis text."""
    if not text:
        return text
    
    # Remove JSON wrapper patterns
    text = re.sub(r'```json\s*\{[^}]*"summary":\s*"', '', text)
    text = re.sub(r'```json\s*\{[^}]*"analysis":\s*"', '', text)
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    
    # Remove trailing quotes and brackets
    text = re.sub(r'"\s*\}\s*$', '', text)
    text = re.sub(r'"\s*$', '', text)
    
    # Remove "Analysis generated" suffix
    text = re.sub(r'\|Analysis generated\s*$', '', text)
    text = re.sub(r'Analysis generated\s*$', '', text)
    
    # Clean up any remaining JSON artifacts
    text = re.sub(r'\{[^}]*"[^"]*":\s*"?', '', text)
    text = re.sub(r'"[^"]*":\s*"', '', text)
    
    # Remove escaped quotes and normalize
    text = text.replace('\\"', '"')
    text = text.replace('\\n', ' ')
    text = text.replace('\\t', ' ')
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def main():
    db_path = Path(__file__).parent.parent / "data" / "enhanced_hn_articles.db"
    
    print(f"Looking for database at: {db_path}")
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        sys.exit(1)
    print(f"Database found: {db_path}")
    
    print("🧹 Cleaning up article summaries and key insights...")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get all articles with summaries
        cursor.execute("SELECT hn_id, summary, key_insights FROM article_analyses")
        articles = cursor.fetchall()
        
        cleaned_count = 0
        for hn_id, summary, key_insights in articles:
            original_summary = summary
            original_insights = key_insights
            
            # Clean the texts
            cleaned_summary = clean_text(summary) if summary else None
            cleaned_insights = clean_text(key_insights) if key_insights else None
            
            # Only update if something changed
            if (cleaned_summary != original_summary or 
                cleaned_insights != original_insights):
                
                cursor.execute("""
                    UPDATE article_analyses 
                    SET summary = ?, key_insights = ?
                    WHERE hn_id = ?
                """, (cleaned_summary, cleaned_insights, hn_id))
                
                cleaned_count += 1
                print(f"✅ Cleaned article {hn_id}")
        
        conn.commit()
        print(f"\n🎉 Successfully cleaned {cleaned_count} articles!")

if __name__ == "__main__":
    main()
