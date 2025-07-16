#!/usr/bin/env python3
"""
Comprehensive end-to-end test suite for HN Daily Scraper
Tests all components and verifies functionality
"""

import os
import sys
import sqlite3
import json
import time
import shutil
from datetime import datetime

class ScraperTestSuite:
    def __init__(self):
        self.test_db = "test_hn_articles.db"
        self.backup_db = "enhanced_hn_articles.db.backup"
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log(self, message, level="INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_basic_imports(self):
        """Test that all required modules can be imported"""
        self.log("Testing basic imports...")
        
        try:
            from daily_scraper import HNScraper
            self.log("✓ daily_scraper imports successfully")
            self.passed_tests += 1
        except ImportError as e:
            self.log(f"❌ daily_scraper import failed: {e}", "ERROR")
            self.failed_tests += 1
            
        try:
            import requests
            import sqlite3
            import json
            from datetime import datetime
            from urllib.parse import urlparse
            from bs4 import BeautifulSoup
            self.log("✓ All required dependencies available")
            self.passed_tests += 1
        except ImportError as e:
            self.log(f"❌ Missing dependency: {e}", "ERROR")
            self.failed_tests += 1
            
    def test_database_operations(self):
        """Test database creation and operations"""
        self.log("Testing database operations...")
        
        try:
            # Backup existing database if it exists
            if os.path.exists("enhanced_hn_articles.db"):
                shutil.copy("enhanced_hn_articles.db", self.backup_db)
                self.log("✓ Backed up existing database")
            
            # Create test scraper
            from daily_scraper import HNScraper
            scraper = HNScraper(self.test_db)
            
            # Test database initialization
            conn = sqlite3.connect(self.test_db)
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['articles', 'comments', 'article_analyses', 'comment_analyses']
            for table in expected_tables:
                if table in tables:
                    self.log(f"✓ Table '{table}' exists")
                    self.passed_tests += 1
                else:
                    self.log(f"❌ Table '{table}' missing", "ERROR")
                    self.failed_tests += 1
            
            conn.close()
            
        except Exception as e:
            self.log(f"❌ Database operations failed: {e}", "ERROR")
            self.failed_tests += 1
            
    def test_api_connectivity(self):
        """Test HN API connectivity"""
        self.log("Testing HN API connectivity...")
        
        try:
            import requests
            
            # Test top stories endpoint
            response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
            if response.status_code == 200:
                stories = response.json()
                self.log(f"✓ HN API accessible, got {len(stories)} stories")
                self.passed_tests += 1
            else:
                self.log(f"❌ HN API returned status {response.status_code}", "ERROR")
                self.failed_tests += 1
                
            # Test single item endpoint
            if stories:
                item_response = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{stories[0]}.json", timeout=10)
                if item_response.status_code == 200:
                    item = item_response.json()
                    self.log(f"✓ Single item API works, got: {item.get('title', 'No title')[:50]}...")
                    self.passed_tests += 1
                else:
                    self.log(f"❌ Single item API failed", "ERROR")
                    self.failed_tests += 1
                    
        except Exception as e:
            self.log(f"❌ API connectivity test failed: {e}", "ERROR")
            self.failed_tests += 1
            
    def test_small_scrape(self):
        """Test a small scrape operation"""
        self.log("Testing small scrape operation...")
        
        try:
            from daily_scraper import HNScraper
            scraper = HNScraper(self.test_db)
            
            # Run a small scrape (2 articles)
            results = scraper.scrape_daily(max_articles=2, max_comments_per_article=5)
            
            if results['success']:
                self.log(f"✓ Small scrape successful: {results['scraped_articles']} articles, {results['total_comments']} comments")
                self.passed_tests += 1
                
                # Verify data was stored
                stats = scraper.get_stats()
                if stats['total_articles'] > 0:
                    self.log(f"✓ Data stored successfully: {stats['total_articles']} articles in database")
                    self.passed_tests += 1
                else:
                    self.log("❌ No articles stored", "ERROR")
                    self.failed_tests += 1
                    
            else:
                self.log("❌ Small scrape failed", "ERROR")
                self.failed_tests += 1
                
        except Exception as e:
            self.log(f"❌ Small scrape test failed: {e}", "ERROR")
            self.failed_tests += 1
            
    def test_data_integrity(self):
        """Test data integrity and structure"""
        self.log("Testing data integrity...")
        
        try:
            conn = sqlite3.connect(self.test_db)
            cursor = conn.cursor()
            
            # Test article data
            cursor.execute("SELECT COUNT(*) FROM articles")
            article_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM comments")
            comment_count = cursor.fetchone()[0]
            
            if article_count > 0:
                self.log(f"✓ {article_count} articles in database")
                self.passed_tests += 1
                
                # Check article structure
                cursor.execute("SELECT hn_id, title, domain, score FROM articles LIMIT 1")
                article = cursor.fetchone()
                if article and all(field is not None for field in article[:2]):
                    self.log("✓ Article data structure valid")
                    self.passed_tests += 1
                else:
                    self.log("❌ Article data structure invalid", "ERROR")
                    self.failed_tests += 1
            else:
                self.log("❌ No articles in database", "ERROR")
                self.failed_tests += 1
                
            if comment_count > 0:
                self.log(f"✓ {comment_count} comments in database")
                self.passed_tests += 1
                
                # Check comment structure
                cursor.execute("SELECT article_id, author, content FROM comments LIMIT 1")
                comment = cursor.fetchone()
                if comment and comment[0] and comment[1]:
                    self.log("✓ Comment data structure valid")
                    self.passed_tests += 1
                else:
                    self.log("❌ Comment data structure invalid", "ERROR")
                    self.failed_tests += 1
            else:
                self.log("⚠ No comments in database", "WARNING")
                
            conn.close()
            
        except Exception as e:
            self.log(f"❌ Data integrity test failed: {e}", "ERROR")
            self.failed_tests += 1
            
    def cleanup(self):
        """Clean up test files"""
        self.log("Cleaning up test files...")
        
        try:
            # Remove test database
            if os.path.exists(self.test_db):
                os.remove(self.test_db)
                self.log("✓ Test database removed")
                
            # Restore backup if it exists
            if os.path.exists(self.backup_db):
                shutil.move(self.backup_db, "enhanced_hn_articles.db")
                self.log("✓ Original database restored")
                
        except Exception as e:
            self.log(f"⚠ Cleanup warning: {e}", "WARNING")
            
    def run_all_tests(self):
        """Run all tests"""
        self.log("Starting comprehensive scraper test suite...")
        self.log("=" * 60)
        
        start_time = time.time()
        
        # Run all tests
        self.test_basic_imports()
        self.test_database_operations()
        self.test_api_connectivity()
        self.test_small_scrape()
        self.test_data_integrity()
        
        end_time = time.time()
        
        # Summary
        self.log("=" * 60)
        self.log(f"Test suite completed in {end_time - start_time:.1f} seconds")
        self.log(f"✓ Passed: {self.passed_tests}")
        self.log(f"❌ Failed: {self.failed_tests}")
        
        if self.failed_tests == 0:
            self.log("🎉 ALL TESTS PASSED! Your daily scraper is working perfectly!", "SUCCESS")
        else:
            self.log(f"⚠ {self.failed_tests} tests failed. Please check the errors above.", "WARNING")
            
        # Cleanup
        self.cleanup()
        
        return self.failed_tests == 0

def main():
    """Run the test suite"""
    suite = ScraperTestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
