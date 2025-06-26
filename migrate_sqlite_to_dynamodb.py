#!/usr/bin/env python3
"""
Migrate data from SQLite to DynamoDB
Transfers articles, comments, and analyses from enhanced_hn_articles.db to AWS DynamoDB
"""

import sqlite3
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from dynamodb_manager import DynamoDBManager

# Load environment variables
load_dotenv()

class SQLiteToDynamoDBMigrator:
    """Migrates data from SQLite to DynamoDB."""
    
    def __init__(self, sqlite_db_path: str):
        self.sqlite_db_path = sqlite_db_path
        self.dynamo_db = DynamoDBManager()
        self.migration_stats = {
            'articles_migrated': 0,
            'comments_migrated': 0,
            'analyses_migrated': 0,
            'articles_skipped': 0,
            'comments_skipped': 0,
            'errors': []
        }
    
    def connect_sqlite(self):
        """Connect to SQLite database."""
        if not os.path.exists(self.sqlite_db_path):
            raise FileNotFoundError(f"SQLite database not found: {self.sqlite_db_path}")
        
        self.sqlite_conn = sqlite3.connect(self.sqlite_db_path)
        self.sqlite_conn.row_factory = sqlite3.Row  # Enable column access by name
        print(f"✅ Connected to SQLite database: {self.sqlite_db_path}")
    
    def get_sqlite_stats(self):
        """Get statistics from SQLite database."""
        cursor = self.sqlite_conn.cursor()
        
        stats = {}
        tables = ['articles', 'comments', 'article_analyses', 'comment_analyses']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
            except sqlite3.Error:
                stats[table] = 0
        
        return stats
    
    def migrate_articles(self):
        """Migrate articles from SQLite to DynamoDB."""
        print("\n📰 Migrating articles...")
        
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM articles")
        
        for row in cursor.fetchall():
            try:
                # Check if article already exists in DynamoDB
                if self.dynamo_db.article_exists(row['hn_id']):
                    print(f"   ⏭️  Article {row['hn_id']} already exists, skipping")
                    self.migration_stats['articles_skipped'] += 1
                    continue
                
                # Prepare article data for DynamoDB
                article_data = {
                    'hn_id': row['hn_id'],
                    'title': row['title'] or '',
                    'url': row['url'] or '',
                    'domain': row['domain'] or '',
                    'score': row['score'] or 0,
                    'author': row['author'] or 'unknown',
                    'time_posted': row['time_posted'] or 0,
                    'num_comments': row['num_comments'] or 0,
                    'story_text': row['story_text'] or '',
                    'story_type': row['story_type'] or 'story',
                    'scraped_at': row['scraped_at'] or datetime.now().isoformat()
                }
                
                # Insert into DynamoDB
                if self.dynamo_db.insert_article(article_data):
                    self.migration_stats['articles_migrated'] += 1
                    if self.migration_stats['articles_migrated'] % 10 == 0:
                        print(f"   ✅ Migrated {self.migration_stats['articles_migrated']} articles...")
                else:
                    self.migration_stats['errors'].append(f"Failed to migrate article {row['hn_id']}")
                    
            except Exception as e:
                error_msg = f"Error migrating article {row['hn_id']}: {str(e)}"
                self.migration_stats['errors'].append(error_msg)
                print(f"   ❌ {error_msg}")
        
        print(f"✅ Articles migration complete: {self.migration_stats['articles_migrated']} migrated, {self.migration_stats['articles_skipped']} skipped")
    
    def migrate_comments(self):
        """Migrate comments from SQLite to DynamoDB."""
        print("\n💬 Migrating comments...")
        
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM comments")
        
        batch_size = 100
        comment_count = 0
        
        for row in cursor.fetchall():
            try:
                # Prepare comment data for DynamoDB
                comment_data = {
                    'comment_id': row['comment_id'],
                    'article_id': row['article_id'],
                    'parent_id': row['parent_id'] or '',
                    'author': row['author'] or 'unknown',
                    'content': row['content'] or '',
                    'time_posted': row['time_posted'] or 0,
                    'level': row['level'] or 0,
                    'scraped_at': row['scraped_at'] or datetime.now().isoformat()
                }
                
                # Insert into DynamoDB
                if self.dynamo_db.insert_comment(comment_data):
                    comment_count += 1
                    self.migration_stats['comments_migrated'] += 1
                    
                    if comment_count % batch_size == 0:
                        print(f"   ✅ Migrated {comment_count} comments...")
                else:
                    self.migration_stats['errors'].append(f"Failed to migrate comment {row['comment_id']}")
                    
            except Exception as e:
                error_msg = f"Error migrating comment {row['comment_id']}: {str(e)}"
                self.migration_stats['errors'].append(error_msg)
                if len(self.migration_stats['errors']) <= 5:  # Only print first few errors
                    print(f"   ❌ {error_msg}")
        
        print(f"✅ Comments migration complete: {self.migration_stats['comments_migrated']} migrated")
    
    def migrate_article_analyses(self):
        """Migrate article analyses to the new DynamoDB analyses table."""
        print("\n🔍 Migrating article analyses to DynamoDB...")
        
        cursor = self.sqlite_conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM article_analyses")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"   📊 Found {count} article analyses to migrate")
                
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
                        
                        if self.dynamo_db.insert_analysis(analysis_data):
                            migrated += 1
                            if migrated % 10 == 0:
                                print(f"   ✅ Migrated {migrated} analyses...")
                        else:
                            errors += 1
                            
                    except Exception as e:
                        error_msg = f"Error migrating analysis {row['hn_id']}: {str(e)}"
                        self.migration_stats['errors'].append(error_msg)
                        errors += 1
                
                self.migration_stats['analyses_migrated'] = migrated
                print(f"✅ Analyses migration complete: {migrated} migrated, {errors} errors")
            else:
                print("   ✅ No article analyses to migrate")
                
        except sqlite3.Error as e:
            print(f"   ❌ Could not migrate article analyses: {e}")
    
    def verify_migration(self):
        """Verify the migration was successful."""
        print("\n🔍 Verifying migration...")
        
        # Get DynamoDB stats
        dynamo_stats = self.dynamo_db.get_stats()
        
        # Get SQLite stats
        sqlite_stats = self.get_sqlite_stats()
        
        print("📊 Migration Summary:")
        print(f"   SQLite Articles: {sqlite_stats.get('articles', 0)}")
        print(f"   DynamoDB Articles: {dynamo_stats['total_articles']}")
        print(f"   SQLite Comments: {sqlite_stats.get('comments', 0)}")
        print(f"   DynamoDB Comments: {dynamo_stats['total_comments']}")
        
        print(f"\n✅ Migration Stats:")
        print(f"   Articles migrated: {self.migration_stats['articles_migrated']}")
        print(f"   Articles skipped (already existed): {self.migration_stats['articles_skipped']}")
        print(f"   Comments migrated: {self.migration_stats['comments_migrated']}")
        print(f"   Errors: {len(self.migration_stats['errors'])}")
        
        if self.migration_stats['errors']:
            print(f"\n❌ Errors encountered:")
            for error in self.migration_stats['errors'][:10]:  # Show first 10 errors
                print(f"   - {error}")
            if len(self.migration_stats['errors']) > 10:
                print(f"   ... and {len(self.migration_stats['errors']) - 10} more errors")
        
        return len(self.migration_stats['errors']) == 0
    
    def run_migration(self):
        """Run the complete migration process."""
        print("🚀 Starting SQLite to DynamoDB Migration")
        print("=" * 60)
        
        try:
            # Connect to SQLite
            self.connect_sqlite()
            
            # Show initial stats
            sqlite_stats = self.get_sqlite_stats()
            print(f"\n📊 SQLite Database Contents:")
            for table, count in sqlite_stats.items():
                print(f"   {table}: {count} rows")
            
            # Run migrations
            self.migrate_articles()
            self.migrate_comments()
            self.migrate_article_analyses()  # Now actually migrate analyses
            
            # Verify migration
            success = self.verify_migration()
            
            return success
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            return False
        
        finally:
            if hasattr(self, 'sqlite_conn'):
                self.sqlite_conn.close()
                print("✅ SQLite connection closed")

def backup_sqlite_db(db_path: str):
    """Create a backup of the SQLite database before deletion."""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return None

def delete_sqlite_db(db_path: str, backup_path: str = None):
    """Delete the SQLite database after successful migration."""
    try:
        if backup_path and os.path.exists(backup_path):
            print(f"✅ Backup exists at: {backup_path}")
        
        confirmation = input(f"\n⚠️  Are you sure you want to delete {db_path}? (yes/NO): ").strip().lower()
        
        if confirmation == 'yes':
            os.remove(db_path)
            print(f"✅ Deleted SQLite database: {db_path}")
            return True
        else:
            print("❌ Database deletion cancelled")
            return False
            
    except Exception as e:
        print(f"❌ Failed to delete database: {e}")
        return False

if __name__ == "__main__":
    print("🔄 SQLite to DynamoDB Migration Tool")
    print("=" * 50)
    
    db_path = "enhanced_hn_articles.db"
    
    if not os.path.exists(db_path):
        print(f"❌ SQLite database not found: {db_path}")
        sys.exit(1)
    
    # Create migrator
    migrator = SQLiteToDynamoDBMigrator(db_path)
    
    # Run migration
    success = migrator.run_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        
        # Ask about deletion
        print("\n" + "=" * 60)
        print("🗑️  DATABASE CLEANUP")
        print("=" * 60)
        
        # Create backup first
        backup_path = backup_sqlite_db(db_path)
        
        # Ask about deletion
        if backup_path:
            print(f"\n✅ Your data is now safely stored in DynamoDB")
            print(f"✅ A backup has been created at: {backup_path}")
            print(f"💡 You can safely delete the original SQLite database")
            
            delete_sqlite_db(db_path, backup_path)
        else:
            print("⚠️  Could not create backup, skipping deletion for safety")
    
    else:
        print("\n❌ Migration had errors. Please review and fix issues before trying again.")
        print("💡 Your original SQLite database is unchanged.")
