#!/usr/bin/env python3
"""
Migrate analyses from SQLite backup to DynamoDB analyses table
"""

import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv
from dynamodb_manager import DynamoDBManager

load_dotenv()

def migrate_analyses_from_backup():
    """Migrate article analyses from backup database to DynamoDB."""
    backup_file = "enhanced_hn_articles.db.backup_20250624_172537"
    
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    print("🔄 Migrating analyses from backup to DynamoDB")
    print("=" * 50)
    
    try:
        # Connect to backup SQLite database
        conn = sqlite3.connect(backup_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Initialize DynamoDB manager
        db = DynamoDBManager()
        
        # Get analyses count
        cursor.execute("SELECT COUNT(*) FROM article_analyses")
        total_count = cursor.fetchone()[0]
        print(f"📊 Found {total_count} analyses in backup")
        
        if total_count == 0:
            print("✅ No analyses to migrate")
            return True
        
        # Migrate analyses
        cursor.execute("SELECT * FROM article_analyses")
        migrated = 0
        errors = 0
        
        for row in cursor.fetchall():
            try:
                analysis_data = {
                    'hn_id': row['hn_id'],
                    'title': row['title'] or '',
                    'url': row['url'] or '',
                    'domain': row['domain'] or '',
                    'summary': row['summary'] or '',
                    'generated_at': row['generated_at'] or datetime.now().isoformat()
                }
                
                if db.insert_analysis(analysis_data):
                    migrated += 1
                    if migrated % 10 == 0:
                        print(f"   ✅ Migrated {migrated}/{total_count} analyses...")
                else:
                    errors += 1
                    print(f"   ❌ Failed to migrate analysis for {row['hn_id']}")
                    
            except Exception as e:
                errors += 1
                print(f"   ❌ Error migrating analysis {row['hn_id']}: {e}")
        
        conn.close()
        
        print(f"\n🎉 Analysis migration complete!")
        print(f"✅ Migrated: {migrated}")
        print(f"❌ Errors: {errors}")
        
        # Verify migration
        sample_analysis = db.get_analysis('sample1')  # Try to get a known analysis
        if sample_analysis:
            print(f"✅ Verification: Successfully retrieved sample analysis")
            print(f"   Title: {sample_analysis['title']}")
        
        return migrated > 0
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_analyses_from_backup()
