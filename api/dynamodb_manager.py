#!/usr/bin/env python3
"""
DynamoDB Database Manager for HN Scraper
Provides persistent storage for articles and comments using AWS DynamoDB
"""

import boto3
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from botocore.exceptions import ClientError

class DynamoDBManager:
    """DynamoDB database manager for HN articles and comments."""
    
    def __init__(self):
        # Initialize DynamoDB client
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'us-west-2')
        )
        
        # Table names (matching your existing tables)
        self.articles_table_name = 'HN_article_data'
        self.comments_table_name = 'hn-scraper-comments'
        self.analyses_table_name = 'hn-article-analyses'  # New table for analyses
        
        # Get existing tables (don't create them)
        self.articles_table = self.dynamodb.Table(self.articles_table_name)
        self.comments_table = self.dynamodb.Table(self.comments_table_name)
        
        # Try to get analyses table, create if it doesn't exist
        try:
            self.analyses_table = self.dynamodb.Table(self.analyses_table_name)
            self.analyses_table.table_status  # Test if table exists
        except Exception:
            print(f"📊 Creating analyses table: {self.analyses_table_name}")
            self.analyses_table = self._create_analyses_table()
        
        print(f"✅ Connected to DynamoDB tables in {os.environ.get('AWS_REGION', 'us-west-2')}")
    
    def test_connection(self) -> bool:
        """Test the connection to DynamoDB tables."""
        try:
            # Test articles table
            articles_desc = self.articles_table.table_status
            print(f"✅ Articles table status: {articles_desc}")
            
            # Test comments table  
            comments_desc = self.comments_table.table_status
            print(f"✅ Comments table status: {comments_desc}")
            
            # Test analyses table
            analyses_desc = self.analyses_table.table_status
            print(f"✅ Analyses table status: {analyses_desc}")
            
            return True
        except Exception as e:
            print(f"❌ Connection test failed: {str(e)}")
            return False
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return self._create_comments_table()
            raise
    
    def _create_articles_table(self):
        """Create the articles table."""
        table = self.dynamodb.create_table(
            TableName=self.articles_table_name,
            KeySchema=[
                {
                    'AttributeName': 'hn_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'hn_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'score',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'scraped_at',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'score-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'score',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                },
                {
                    'IndexName': 'scraped-at-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'scraped_at',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table to be created
        table.wait_until_exists()
        return table
    
    def _create_comments_table(self):
        """Create the comments table."""
        table = self.dynamodb.create_table(
            TableName=self.comments_table_name,
            KeySchema=[
                {
                    'AttributeName': 'comment_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'comment_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'article_id',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'article-id-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'article_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table to be created
        table.wait_until_exists()
        return table
    
    def _create_analyses_table(self):
        """Create the article analyses table."""
        table = self.dynamodb.create_table(
            TableName=self.analyses_table_name,
            KeySchema=[
                {
                    'AttributeName': 'hn_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'hn_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table to be created
        table.wait_until_exists()
        print(f"✅ Created analyses table: {self.analyses_table_name}")
        return table
    
    def save_article(self, article_data: Dict) -> bool:
        """Save article to DynamoDB (alias for insert_article)."""
        return self.insert_article(article_data)
    
    def save_comment(self, comment_data: Dict) -> bool:
        """Save comment to DynamoDB (alias for insert_comment)."""
        return self.insert_comment(comment_data)
    
    def insert_article(self, article_data: Dict) -> bool:
        """Insert or update an article."""
        try:
            # Prepare item for DynamoDB
            item = {
                'hn_id': str(article_data['hn_id']),
                'title': article_data.get('title', ''),
                'url': article_data.get('url', ''),
                'domain': article_data.get('domain', ''),
                'score': int(article_data.get('score', 0)),
                'author': article_data.get('author', 'unknown'),
                'time_posted': int(article_data.get('time_posted', 0)),
                'num_comments': int(article_data.get('num_comments', 0)),
                'story_text': article_data.get('story_text', ''),
                'story_type': article_data.get('story_type', 'story'),
                'scraped_at': article_data.get('scraped_at', datetime.now().isoformat())
            }
            
            self.articles_table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"Error inserting article {article_data.get('hn_id')}: {e}")
            return False
    
    def insert_comment(self, comment_data: Dict) -> bool:
        """Insert or update a comment."""
        try:
            # Prepare item for DynamoDB
            item = {
                'comment_id': str(comment_data['comment_id']),
                'article_id': str(comment_data['article_id']),
                'parent_id': str(comment_data.get('parent_id', '')),
                'author': comment_data.get('author', 'unknown'),
                'content': comment_data.get('content', ''),
                'time_posted': int(comment_data.get('time_posted', 0)),
                'level': int(comment_data.get('level', 0)),
                'scraped_at': comment_data.get('scraped_at', datetime.now().isoformat())
            }
            
            self.comments_table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"Error inserting comment {comment_data.get('comment_id')}: {e}")
            return False
    
    def insert_analysis(self, analysis_data: Dict) -> bool:
        """Insert or update an article analysis."""
        try:
            # Prepare item for DynamoDB
            item = {
                'hn_id': str(analysis_data['hn_id']),
                'title': analysis_data.get('title', ''),
                'url': analysis_data.get('url', ''),
                'domain': analysis_data.get('domain', ''),
                'summary': analysis_data.get('summary', ''),
                'generated_at': analysis_data.get('generated_at', datetime.now().isoformat())
            }
            
            self.analyses_table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"Error inserting analysis {analysis_data.get('hn_id')}: {e}")
            return False
    
    def save_analysis(self, analysis_data: Dict) -> bool:
        """Save analysis to DynamoDB (alias for insert_analysis)."""
        return self.insert_analysis(analysis_data)
    
    def get_articles(self, limit: int = 50, sort_by: str = 'score') -> List[Dict]:
        """Get articles with sorting."""
        try:
            if sort_by == 'score':
                # Scan and sort by score (in a real app, you'd use a GSI)
                response = self.articles_table.scan(
                    Limit=limit * 2  # Get more to sort
                )
                items = response.get('Items', [])
                items.sort(key=lambda x: int(x.get('score', 0)), reverse=True)
                return items[:limit]
            
            elif sort_by == 'recent':
                # Scan and sort by scraped_at
                response = self.articles_table.scan(
                    Limit=limit * 2
                )
                items = response.get('Items', [])
                items.sort(key=lambda x: x.get('scraped_at', ''), reverse=True)
                return items[:limit]
            
            else:
                # Default scan
                response = self.articles_table.scan(Limit=limit)
                return response.get('Items', [])
                
        except Exception as e:
            print(f"Error getting articles: {e}")
            return []
    
    def get_article(self, hn_id: str) -> Optional[Dict]:
        """Get a single article by ID."""
        try:
            response = self.articles_table.get_item(
                Key={'hn_id': str(hn_id)}
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error getting article {hn_id}: {e}")
            return None
    
    def get_article_comments(self, article_id: str) -> List[Dict]:
        """Get all comments for an article."""
        try:
            # Since we don't have a GSI, we'll use scan with filter
            response = self.comments_table.scan(
                FilterExpression='article_id = :article_id',
                ExpressionAttributeValues={
                    ':article_id': str(article_id)
                }
            )
            
            # Convert DynamoDB items to regular dicts and handle Decimal types
            comments = []
            for item in response.get('Items', []):
                comment = {
                    'comment_id': item.get('comment_id', ''),
                    'article_id': item.get('article_id', ''),
                    'parent_id': item.get('parent_id', ''),
                    'author': item.get('author', ''),
                    'content': item.get('content', ''),
                    'time_posted': int(item.get('time_posted', 0)),
                    'level': int(item.get('level', 0))
                }
                comments.append(comment)
            
            return comments
        except Exception as e:
            print(f"Error getting comments for article {article_id}: {e}")
            return []
    
    def get_analysis(self, hn_id: str) -> Optional[Dict]:
        """Get analysis for an article."""
        try:
            response = self.analyses_table.get_item(
                Key={'hn_id': str(hn_id)}
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error getting analysis {hn_id}: {e}")
            return None
    
    def article_exists(self, hn_id: str) -> bool:
        """Check if an article already exists."""
        try:
            response = self.articles_table.get_item(
                Key={'hn_id': str(hn_id)},
                ProjectionExpression='hn_id'
            )
            return 'Item' in response
        except Exception as e:
            print(f"Error checking article existence {hn_id}: {e}")
            return False
    
    def get_existing_article_ids(self) -> set:
        """Get all existing article IDs."""
        try:
            response = self.articles_table.scan(
                ProjectionExpression='hn_id'
            )
            return {item['hn_id'] for item in response.get('Items', [])}
        except Exception as e:
            print(f"Error getting existing article IDs: {e}")
            return set()
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        try:
            # Count articles
            articles_response = self.articles_table.scan(
                Select='COUNT'
            )
            total_articles = articles_response.get('Count', 0)
            
            # Count comments
            comments_response = self.comments_table.scan(
                Select='COUNT'
            )
            total_comments = comments_response.get('Count', 0)
            
            # Get average score (simple approach - in production you'd use aggregation)
            if total_articles > 0:
                articles_response = self.articles_table.scan(
                    ProjectionExpression='score'
                )
                scores = [int(item.get('score', 0)) for item in articles_response.get('Items', [])]
                avg_score = sum(scores) / len(scores) if scores else 0
            else:
                avg_score = 0
            
            # Get unique domains (using expression attribute names for reserved keyword)
            domains_response = self.articles_table.scan(
                ProjectionExpression='#d',
                ExpressionAttributeNames={'#d': 'domain'}
            )
            domains = set(item.get('domain', '') for item in domains_response.get('Items', []))
            unique_domains = len(domains)
            
            return {
                'total_articles': total_articles,
                'total_comments': total_comments,
                'avg_score': round(avg_score, 1),
                'unique_domains': unique_domains,
                'domains': list(domains)[:10]  # Top 10 domains
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                'total_articles': 0,
                'total_comments': 0,
                'avg_score': 0,
                'unique_domains': 0,
                'domains': []
            }
    
    def delete_article(self, hn_id: str) -> bool:
        """Delete an article by HN ID."""
        try:
            response = self.articles_table.delete_item(
                Key={'hn_id': hn_id}
            )
            return True
        except Exception as e:
            print(f"❌ Error deleting article {hn_id}: {str(e)}")
            return False
    
    def delete_comment(self, comment_id: str, article_id: str = None) -> bool:
        """Delete a comment by comment ID. If article_id not provided, will scan to find it."""
        try:
            if article_id:
                # Direct delete if we have both keys
                response = self.comments_table.delete_item(
                    Key={
                        'article_id': article_id,
                        'comment_id': comment_id
                    }
                )
                return True
            else:
                # Need to find the article_id first
                response = self.comments_table.scan(
                    FilterExpression='comment_id = :cid',
                    ExpressionAttributeValues={':cid': comment_id}
                )
                
                if response['Items']:
                    item = response['Items'][0]
                    response = self.comments_table.delete_item(
                        Key={
                            'article_id': item['article_id'],
                            'comment_id': comment_id
                        }
                    )
                    return True
                else:
                    print(f"❌ Comment {comment_id} not found")
                    return False
                    
        except Exception as e:
            print(f"❌ Error deleting comment {comment_id}: {str(e)}")
            return False
    
    def cleanup_test_data(self, test_prefix: str = "test_") -> bool:
        """Delete all test data (articles and comments starting with test prefix)."""
        try:
            # Clean up test articles
            articles_cleaned = 0
            response = self.articles_table.scan(
                FilterExpression='begins_with(hn_id, :prefix)',
                ExpressionAttributeValues={':prefix': test_prefix}
            )
            
            for item in response['Items']:
                if self.delete_article(item['hn_id']):
                    articles_cleaned += 1
            
            # Clean up test comments - check for multiple test patterns
            comments_cleaned = 0
            test_patterns = [test_prefix, "comment_", "test_save_comment_"]
            
            for pattern in test_patterns:
                response = self.comments_table.scan(
                    FilterExpression='begins_with(comment_id, :prefix)',
                    ExpressionAttributeValues={':prefix': pattern}
                )
                
                for item in response['Items']:
                    if self.delete_comment(item['comment_id'], item['article_id']):
                        comments_cleaned += 1
            
            print(f"🧹 Cleaned up {articles_cleaned} test articles and {comments_cleaned} test comments")
            return True
            
        except Exception as e:
            print(f"❌ Error during cleanup: {str(e)}")
            return False
    
    def get_articles_by_date(self, date: str, limit: int = 50) -> List[Dict]:
        """Get articles for a specific date."""
        try:
            # For DynamoDB, we need to scan since we don't have a date-based GSI
            # In a production system, you'd create a GSI on date
            response = self.articles_table.scan()
            
            articles = []
            for item in response.get('Items', []):
                # Extract date from scraped_at timestamp
                scraped_at = item.get('scraped_at', '')
                if scraped_at:
                    try:
                        # Handle different date formats
                        if 'T' in scraped_at:
                            article_date = scraped_at.split('T')[0]
                        else:
                            # Assume it's already in YYYY-MM-DD format
                            article_date = scraped_at[:10]
                        
                        if article_date == date:
                            articles.append(item)
                    except Exception:
                        continue
            
            return articles[:limit]
            
        except Exception as e:
            print(f"Error getting articles by date: {e}")
            return []
    

def test_connection():
    """Test DynamoDB connection."""
    try:
        db = DynamoDBManager()
        print("✅ DynamoDB connection successful!")
        
        # Test insert
        test_article = {
            'hn_id': 'test123',
            'title': 'Test Article',
            'url': 'https://example.com',
            'domain': 'example.com',
            'score': 100,
            'author': 'testuser',
            'time_posted': 1640995200,  # Example timestamp
            'num_comments': 5,
            'story_text': 'This is a test article.',
            'story_type': 'story'
        }
        
        if db.insert_article(test_article):
            print("✅ Test article inserted successfully!")
            
            # Test retrieve
            retrieved = db.get_article('test123')
            if retrieved:
                print("✅ Test article retrieved successfully!")
                print(f"   Title: {retrieved['title']}")
                print(f"   Score: {retrieved['score']}")
            else:
                print("❌ Could not retrieve test article")
        else:
            print("❌ Could not insert test article")
            
    except Exception as e:
        print(f"❌ DynamoDB connection failed: {e}")
        print("\nMake sure you have set these environment variables:")
        print("- AWS_ACCESS_KEY_ID")
        print("- AWS_SECRET_ACCESS_KEY") 
        print("- AWS_REGION (optional, defaults to us-east-1)")

if __name__ == "__main__":
    test_connection()
