#!/usr/bin/env python3
"""
Comprehensive unit tests for DynamoDB Manager.
Tests all functionality including article and comment operations.
"""

import unittest
import os
import time
from datetime import datetime
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the DynamoDB manager
from dynamodb_manager import DynamoDBManager

class TestDynamoDBManager(unittest.TestCase):
    """Test suite for DynamoDB Manager functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class - run once before all tests."""
        print("\n🧪 Setting up DynamoDB test suite...")
        
        # Verify environment variables
        required_env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION']
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        
        if missing_vars:
            raise unittest.SkipTest(f"Missing required environment variables: {missing_vars}")
        
        # Initialize manager
        cls.db = DynamoDBManager()
        cls.test_article_id = f"test_{int(time.time())}"
        cls.test_comment_id = f"comment_{int(time.time())}"
        
        print(f"✅ Test setup complete")
        print(f"🆔 Test article ID: {cls.test_article_id}")
        print(f"🆔 Test comment ID: {cls.test_comment_id}")
    
    def setUp(self):
        """Set up each individual test."""
        self.sample_article = {
            'hn_id': self.test_article_id,
            'title': 'Test Article for Unit Testing',
            'url': 'https://example.com/test-article',
            'domain': 'example.com',
            'score': 150,
            'author': 'test_author',
            'time_posted': 1640995200,
            'num_comments': 25,
            'story_text': 'This is a comprehensive test article for our unit tests.',
            'story_type': 'story'
        }
        
        self.sample_comment = {
            'comment_id': self.test_comment_id,
            'article_id': self.test_article_id,
            'parent_id': '',
            'author': 'test_commenter',
            'content': 'This is a test comment for unit testing purposes.',
            'time_posted': 1640995300,
            'level': 0
        }
    
    def test_01_connection(self):
        """Test DynamoDB connection and table access."""
        print("\n🔍 Testing DynamoDB connection...")
        
        # Test that manager was initialized
        self.assertIsNotNone(self.db)
        self.assertIsNotNone(self.db.articles_table)
        self.assertIsNotNone(self.db.comments_table)
        
        # Test table names
        self.assertEqual(self.db.articles_table_name, 'HN_article_data')
        self.assertEqual(self.db.comments_table_name, 'hn-scraper-comments')
        
        print("✅ Connection test passed")
    
    def test_02_table_status(self):
        """Test that tables are active and accessible."""
        print("\n📊 Testing table status...")
        
        try:
            articles_status = self.db.articles_table.table_status
            comments_status = self.db.comments_table.table_status
            
            self.assertEqual(articles_status, 'ACTIVE')
            self.assertEqual(comments_status, 'ACTIVE')
            
            print(f"✅ Articles table: {articles_status}")
            print(f"✅ Comments table: {comments_status}")
        except Exception as e:
            self.fail(f"Table status check failed: {e}")
    
    def test_03_insert_article(self):
        """Test article insertion."""
        print("\n💾 Testing article insertion...")
        
        # Insert the test article
        result = self.db.insert_article(self.sample_article)
        self.assertTrue(result, "Article insertion should succeed")
        
        # Verify the article was inserted
        retrieved = self.db.get_article(self.test_article_id)
        self.assertIsNotNone(retrieved, "Article should be retrievable after insertion")
        
        # Check article data
        self.assertEqual(retrieved['hn_id'], self.test_article_id)
        self.assertEqual(retrieved['title'], self.sample_article['title'])
        self.assertEqual(int(retrieved['score']), self.sample_article['score'])
        self.assertEqual(retrieved['author'], self.sample_article['author'])
        
        print("✅ Article insertion test passed")
    
    def test_04_article_exists(self):
        """Test article existence checking."""
        print("\n🔍 Testing article existence check...")
        
        # Test existing article
        exists = self.db.article_exists(self.test_article_id)
        self.assertTrue(exists, "Test article should exist")
        
        # Test non-existing article
        fake_id = f"fake_{int(time.time())}"
        not_exists = self.db.article_exists(fake_id)
        self.assertFalse(not_exists, "Fake article should not exist")
        
        print("✅ Article existence test passed")
    
    def test_05_insert_comment(self):
        """Test comment insertion."""
        print("\n💬 Testing comment insertion...")
        
        # Insert the test comment
        result = self.db.insert_comment(self.sample_comment)
        self.assertTrue(result, "Comment insertion should succeed")
        
        # Verify the comment was inserted by getting comments for the article
        comments = self.db.get_article_comments(self.test_article_id)
        self.assertIsInstance(comments, list, "Comments should be returned as a list")
        
        # Find our test comment
        test_comment_found = False
        for comment in comments:
            if comment['comment_id'] == self.test_comment_id:
                test_comment_found = True
                self.assertEqual(comment['article_id'], self.test_article_id)
                self.assertEqual(comment['author'], self.sample_comment['author'])
                self.assertEqual(comment['content'], self.sample_comment['content'])
                break
        
        self.assertTrue(test_comment_found, "Test comment should be found in article comments")
        
        print("✅ Comment insertion test passed")
    
    def test_06_get_articles(self):
        """Test article retrieval with different sorting options."""
        print("\n📖 Testing article retrieval...")
        
        # Test getting articles with default sorting
        articles = self.db.get_articles(limit=10)
        self.assertIsInstance(articles, list, "Articles should be returned as a list")
        
        # Our test article should be in the results
        test_article_found = False
        for article in articles:
            if article['hn_id'] == self.test_article_id:
                test_article_found = True
                break
        
        self.assertTrue(test_article_found, "Test article should be found in article list")
        
        # Test different sorting options
        articles_by_score = self.db.get_articles(limit=5, sort_by='score')
        articles_by_recent = self.db.get_articles(limit=5, sort_by='recent')
        
        self.assertIsInstance(articles_by_score, list)
        self.assertIsInstance(articles_by_recent, list)
        
        print("✅ Article retrieval test passed")
    
    def test_07_get_single_article(self):
        """Test single article retrieval."""
        print("\n📄 Testing single article retrieval...")
        
        # Get our test article
        article = self.db.get_article(self.test_article_id)
        
        self.assertIsNotNone(article, "Article should be retrievable")
        self.assertEqual(article['hn_id'], self.test_article_id)
        self.assertEqual(article['title'], self.sample_article['title'])
        
        # Test non-existent article
        fake_article = self.db.get_article('non_existent_id')
        self.assertIsNone(fake_article, "Non-existent article should return None")
        
        print("✅ Single article retrieval test passed")
    
    def test_08_get_article_comments(self):
        """Test retrieving comments for an article."""
        print("\n💬 Testing article comments retrieval...")
        
        comments = self.db.get_article_comments(self.test_article_id)
        
        self.assertIsInstance(comments, list, "Comments should be returned as a list")
        self.assertGreaterEqual(len(comments), 1, "Should have at least our test comment")
        
        # Verify our test comment is in the results
        comment_found = False
        for comment in comments:
            if comment['comment_id'] == self.test_comment_id:
                comment_found = True
                self.assertEqual(comment['article_id'], self.test_article_id)
                break
        
        self.assertTrue(comment_found, "Test comment should be found")
        
        print("✅ Article comments retrieval test passed")
    
    def test_09_get_existing_article_ids(self):
        """Test getting all existing article IDs."""
        print("\n🆔 Testing existing article IDs retrieval...")
        
        existing_ids = self.db.get_existing_article_ids()
        
        self.assertIsInstance(existing_ids, set, "Should return a set of IDs")
        self.assertIn(self.test_article_id, existing_ids, "Test article ID should be in the set")
        
        print(f"✅ Found {len(existing_ids)} existing article IDs")
    
    def test_10_get_stats(self):
        """Test database statistics retrieval."""
        print("\n📊 Testing database statistics...")
        
        stats = self.db.get_stats()
        
        # Check stats structure
        required_keys = ['total_articles', 'total_comments', 'avg_score', 'unique_domains', 'domains']
        for key in required_keys:
            self.assertIn(key, stats, f"Stats should contain {key}")
        
        # Check data types
        self.assertIsInstance(stats['total_articles'], int)
        self.assertIsInstance(stats['total_comments'], int)
        self.assertIsInstance(stats['avg_score'], (int, float))
        self.assertIsInstance(stats['unique_domains'], int)
        self.assertIsInstance(stats['domains'], list)
        
        # Should have at least our test data
        self.assertGreaterEqual(stats['total_articles'], 1)
        
        print(f"✅ Stats: {stats['total_articles']} articles, {stats['total_comments']} comments")
        print(f"   Avg score: {stats['avg_score']}, Domains: {stats['unique_domains']}")
    
    def test_11_save_methods(self):
        """Test the save_article and save_comment alias methods."""
        print("\n💾 Testing save method aliases...")
        
        # Test save_article alias
        test_article_2 = self.sample_article.copy()
        test_article_2['hn_id'] = f"test_save_{int(time.time())}"
        test_article_2['title'] = "Test Save Article"
        
        result = self.db.save_article(test_article_2)
        self.assertTrue(result, "save_article should succeed")
        
        # Verify it was saved
        retrieved = self.db.get_article(test_article_2['hn_id'])
        self.assertIsNotNone(retrieved, "Saved article should be retrievable")
        
        # Test save_comment alias
        test_comment_2 = self.sample_comment.copy()
        test_comment_2['comment_id'] = f"test_save_comment_{int(time.time())}"
        test_comment_2['article_id'] = test_article_2['hn_id']
        test_comment_2['content'] = "Test save comment"
        
        result = self.db.save_comment(test_comment_2)
        self.assertTrue(result, "save_comment should succeed")
        
        print("✅ Save method aliases test passed")
    
    def test_12_error_handling(self):
        """Test error handling with invalid data."""
        print("\n⚠️  Testing error handling...")
        
        # Test with missing required fields
        invalid_article = {'title': 'Invalid Article'}  # Missing hn_id
        
        # This should not crash, but might return False
        try:
            result = self.db.insert_article(invalid_article)
            # Result could be True or False depending on how DynamoDB handles it
            print(f"   Invalid article insert result: {result}")
        except Exception as e:
            print(f"   Expected error for invalid article: {type(e).__name__}")
        
        # Test with non-existent article ID
        non_existent = self.db.get_article('definitely_does_not_exist_12345')
        self.assertIsNone(non_existent, "Non-existent article should return None")
        
        print("✅ Error handling test passed")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests - remove test data."""
        print("\n🧹 Cleaning up test data...")
        
        try:
            cleanup_success = cls.db.cleanup_test_data("test_")
            if cleanup_success:
                print("   ✅ Test data cleanup completed successfully")
            else:
                print("   ⚠️  Test data cleanup had some issues")
        except Exception as e:
            print(f"   Cleanup warning: {e}")
        
        print("✅ Test suite completed")

class TestDynamoDBManagerMocked(unittest.TestCase):
    """Test suite with mocked DynamoDB for testing without actual AWS calls."""
    
    @patch('dynamodb_manager.boto3.resource')
    def test_initialization_with_mock(self, mock_boto3_resource):
        """Test manager initialization with mocked boto3."""
        print("\n🎭 Testing with mocked AWS...")
        
        # Mock the DynamoDB resource
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_table.table_status = 'ACTIVE'
        
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb
        
        # Initialize manager
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'fake_key',
            'AWS_SECRET_ACCESS_KEY': 'fake_secret',
            'AWS_REGION': 'us-west-2'
        }):
            manager = DynamoDBManager()
            
            # Verify initialization
            self.assertIsNotNone(manager)
            self.assertEqual(manager.articles_table_name, 'HN_article_data')
            self.assertEqual(manager.comments_table_name, 'hn-scraper-comments')
        
        print("✅ Mocked initialization test passed")

def run_integration_tests():
    """Run integration tests that require actual DynamoDB connection."""
    print("🚀 Running DynamoDB Integration Tests")
    print("=" * 60)
    
    # Check if we can run integration tests
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Skipping integration tests - missing environment variables: {missing_vars}")
        print("Please set up your .env file with AWS credentials to run integration tests.")
        return False
    
    # Run the main test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDynamoDBManager)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"🏁 Integration Tests Complete")
    print(f"✅ Tests run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback}")
    
    if result.errors:
        print("\n⚠️  ERRORS:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback}")
    
    return len(result.failures) == 0 and len(result.errors) == 0

def run_unit_tests():
    """Run unit tests with mocked dependencies."""
    print("🧪 Running DynamoDB Unit Tests (Mocked)")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDynamoDBManagerMocked)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == "__main__":
    print("🧪 DynamoDB Manager Test Suite")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Run unit tests first (these don't require AWS)
    unit_success = run_unit_tests()
    
    # Run integration tests if AWS credentials are available
    integration_success = run_integration_tests()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏆 FINAL TEST SUMMARY")
    print("=" * 60)
    print(f"🧪 Unit Tests: {'✅ PASSED' if unit_success else '❌ FAILED'}")
    print(f"🔗 Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    
    if unit_success and integration_success:
        print("\n🎉 All tests passed! DynamoDB Manager is ready for production.")
        exit(0)
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        exit(1)
