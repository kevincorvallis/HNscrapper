#!/usr/bin/env python3
"""
Quick Database Test
"""
import sqlite3
import os

def test_db():
    db_path = '/Users/kevin/Downloads/HNscrapper/data/enhanced_hn_articles.db'
    print(f"Testing database: {db_path}")
    print(f"File exists: {os.path.exists(db_path)}")
    
    if os.path.exists(db_path):
        print(f"File size: {os.path.getsize(db_path)} bytes")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # List tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tables: {[t[0] for t in tables]}")
            
            # Count articles
            cursor.execute("SELECT COUNT(*) FROM articles")
            articles = cursor.fetchone()[0]
            print(f"Articles: {articles}")
            
            if articles > 0:
                cursor.execute("SELECT title, domain FROM articles LIMIT 1")
                sample = cursor.fetchone()
                print(f"Sample: {sample[0]} from {sample[1]}")
            
            conn.close()
            print("✅ Database test successful")
            
        except Exception as e:
            print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_db()
