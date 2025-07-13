#!/usr/bin/env python3
"""
Test DynamoDB connection and basic operations.
"""

from dynamodb_manager import DynamoDBManager
import os
from dotenv import load_dotenv
import pytest

load_dotenv()

def test_dynamodb():
    """Test the DynamoDB connection and basic operations."""
    print("🧪 Testing DynamoDB connection...")
    
    # Load environment variables first
    load_dotenv()
    
    aws_region = os.environ.get('AWS_REGION')
    aws_key = os.environ.get('AWS_ACCESS_KEY_ID')
    
    if not aws_region or not aws_key:
        print("❌ AWS credentials not found in environment variables")
        print("Please check your .env file")
        pytest.skip("AWS credentials missing")
        
    print(f"AWS Region: {aws_region}")
    print(f"AWS Access Key ID: {aws_key[:10]}...")
    
    try:
        # Create manager instance
        print("Creating DynamoDB manager...")
        db = DynamoDBManager()
        print("✅ DynamoDB manager created successfully!")
        
        # Test connection
        print("🔍 Testing connection...")
        assert db.test_connection(), "DynamoDB connection failed"
        
        # Test getting stats
        print("📊 Getting current database stats...")
        stats = db.get_stats()
        print(f"Current articles: {stats['total_articles']}")
        print(f"Current comments: {stats['total_comments']}")
        print(f"Average score: {stats['avg_score']}")
        print(f"Unique domains: {stats['unique_domains']}")
        
        # Test saving a sample article
        print("💾 Testing article save...")
        test_article = {
            'hn_id': 'test123',
            'title': 'Test Article for DynamoDB Connection',
            'url': 'https://example.com/test',
            'domain': 'example.com',
            'score': 42,
            'author': 'testuser',
            'time_posted': 1234567890,
            'num_comments': 3,
            'story_text': 'This is a test article to verify DynamoDB connection.',
            'story_type': 'story'
        }
        
        if db.save_article(test_article):
            print("✅ Test article saved successfully!")
            
            # Test retrieving articles
            print("📖 Testing article retrieval...")
            articles = db.get_articles(limit=5)
            print(f"Retrieved {len(articles)} articles")
            
            if articles:
                print(f"Sample article: {articles[0]['title']}")
                print(f"Sample score: {articles[0]['score']}")
            
            # Test checking if article exists
            print("🔍 Testing article existence check...")
            exists = db.article_exists('test123')
            print(f"Test article exists: {exists}")
            
            print("\n🎉 All DynamoDB tests passed!")
        else:
            print("❌ Failed to save test article")
            assert False, "save_article failed"
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        assert False, f"Exception occurred: {e}"

if __name__ == "__main__":
    try:
        test_dynamodb()
        print("\n✅ DynamoDB is ready for use!")
    except AssertionError:
        print("\n❌ DynamoDB setup needs attention.")
