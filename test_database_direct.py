#!/usr/bin/env python3
"""
Direct database test to identify hanging issues
"""
import sqlite3
import os
import time

def test_database_operations():
    """Test database operations that might be hanging."""
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'enhanced_hn_articles.db')
    
    print(f"🔍 Testing Database Operations")
    print(f"Database: {db_path}")
    print("=" * 40)
    
    try:
        # Test basic connection
        print("⏳ Testing basic connection...")
        start_time = time.time()
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        print(f"✅ Connection established in {time.time() - start_time:.2f}s")
        
        # Test simple count
        print("⏳ Testing simple count...")
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM article_analyses")
        count = cursor.fetchone()[0]
        print(f"✅ Found {count} articles in {time.time() - start_time:.2f}s")
        
        # Test the complex query that might be hanging
        print("⏳ Testing complex join query...")
        start_time = time.time()
        cursor.execute('''
            SELECT aa.hn_id, aa.title, aa.url, aa.domain, aa.summary, 
                   aa.key_insights, aa.main_themes, aa.sentiment_analysis,
                   aa.discussion_quality_score, aa.controversy_level, aa.generated_at,
                   COUNT(DISTINCT ca.comment_id) as analyzed_comments,
                   COUNT(DISTINCT ec.id) as total_comments,
                   AVG(ca.quality_score) as avg_comment_quality
            FROM article_analyses aa
            LEFT JOIN comment_analyses ca ON aa.hn_id = ca.hn_id
            LEFT JOIN enhanced_comments ec ON aa.hn_id = ec.article_hn_id
            GROUP BY aa.hn_id
            ORDER BY aa.discussion_quality_score DESC, aa.generated_at DESC
            LIMIT 10
        ''')
        
        results = cursor.fetchall()
        elapsed = time.time() - start_time
        print(f"✅ Complex query returned {len(results)} results in {elapsed:.2f}s")
        
        if elapsed > 2:
            print("⚠️  Query took longer than 2 seconds - this might be causing hanging")
        
        # Test stats queries
        print("⏳ Testing stats queries...")
        start_time = time.time()
        
        # Basic stats
        cursor.execute('SELECT COUNT(*) FROM comment_analyses')
        comment_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM enhanced_comments')
        enhanced_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(discussion_quality_score) FROM article_analyses WHERE discussion_quality_score IS NOT NULL')
        avg_quality = cursor.fetchone()[0]
        
        elapsed = time.time() - start_time
        print(f"✅ Stats queries completed in {elapsed:.2f}s")
        print(f"   • Comment analyses: {comment_count}")
        print(f"   • Enhanced comments: {enhanced_count}")
        print(f"   • Average quality: {avg_quality:.2f}")
        
        conn.close()
        return True
        
    except sqlite3.OperationalError as e:
        print(f"❌ Database locked or busy: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False

def test_table_structure():
    """Check table structure for any issues."""
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'enhanced_hn_articles.db')
    
    print(f"\n🔍 Testing Table Structure")
    print("=" * 30)
    
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Found {len(tables)} tables: {', '.join(tables)}")
        
        # Check each table
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   • {table}: {count} rows")
        
        # Check for indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        print(f"🔍 Found {len(indexes)} indexes")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Table structure error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Database Diagnostic Test")
    print("=" * 50)
    
    db_ok = test_database_operations()
    structure_ok = test_table_structure()
    
    print(f"\n📋 Diagnostic Results")
    print("=" * 25)
    print(f"Database Operations: {'✅' if db_ok else '❌'}")
    print(f"Table Structure: {'✅' if structure_ok else '❌'}")
    
    if db_ok and structure_ok:
        print("\n✅ Database is healthy. The hanging issue is likely in the Flask app logic.")
        print("💡 Consider adding database connection timeouts and query optimization.")
    else:
        print("\n❌ Database issues detected. Fix these first before testing the Flask app.")
