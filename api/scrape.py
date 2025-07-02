#!/usr/bin/env python3
"""
Serverless scraping function for Vercel.
Handles HN scraping using DynamoDB in a serverless environment.
"""

import json
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from daily_scraper_dynamodb import HNScrapperDynamoDB
except ImportError:
    # Fallback for when import fails in serverless environment
    HNScrapperDynamoDB = None


def handler(request):
    """Vercel function handler for scraping."""
    
    try:
        print(f"Handler called with method: {request.method}")
        print(f"Request headers: {dict(request.headers)}")
        
        # Verify authorization
        auth_header = request.headers.get('Authorization', '')
        cron_secret = os.environ.get('CRON_SECRET', 'default-secret')
        expected_auth = f"Bearer {cron_secret}"
        
        print(f"Auth check: header='{auth_header[:20]}...', expected set")
        
        if auth_header != expected_auth:
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        if request.method == 'POST':
            print("Starting scraping process...")
            # Trigger DynamoDB scraping
            results = scrape_hn_with_dynamodb()
            
            print(f"Scraping results: {results}")
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(results)
            }
        else:
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except Exception as e:
        error_msg = f"Handler error: {str(e)}"
        print(error_msg)
        import traceback
        print(f"Handler traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }


def scrape_hn_with_dynamodb():
    """Use the DynamoDB scraper for serverless environment."""
    
    try:
        # Check AWS credentials
        aws_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
        aws_region = os.environ.get('AWS_REGION', 'us-east-1')
        
        print(f"AWS credentials check: Key ID exists: {bool(aws_key_id)}")
        print(f"Secret exists: {bool(aws_secret)}, Region: {aws_region}")
        
        if not all([aws_key_id, aws_secret]):
            raise Exception(
                "AWS credentials not found. Please set AWS_ACCESS_KEY_ID and "
                "AWS_SECRET_ACCESS_KEY"
            )
        
        if HNScrapperDynamoDB is None:
            print("HNScrapperDynamoDB is None, trying fallback import...")
            # Try fallback import approach
            try:
                import sys
                current_file = os.path.abspath(__file__)
                parent_dir = os.path.dirname(os.path.dirname(current_file))
                sys.path.append(parent_dir)
                # Import the DynamoDB scraper
                from daily_scraper_dynamodb import (
                    HNScrapperDynamoDB as DynamoScraper
                )
                scraper = DynamoScraper()
            except ImportError as ie:
                print(f"Fallback import failed: {ie}")
                error_msg = (
                    f"HNScrapperDynamoDB not available. Import error: {ie}"
                )
                raise Exception(error_msg)
        else:
            print("Using main HNScrapperDynamoDB import")
            scraper = HNScrapperDynamoDB()
        
        print("Starting DynamoDB scraping...")
        
        # Run scrape with conservative limits for serverless environment
        results = scraper.scrape_daily(
            max_articles=5,  # Reduced for serverless
            max_comments_per_article=10  # Reduced for serverless
        )
        
        articles_count = len(results.get('articles_processed', []))
        print(f"Scraping completed successfully: {articles_count} articles")
        return results
    
    except Exception as e:
        error_msg = f"Error in DynamoDB scraping: {str(e)}"
        print(error_msg)
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise Exception(error_msg)


# For local testing
if __name__ == "__main__":
    class MockRequest:
        def __init__(self):
            self.method = 'POST'
            cron_secret = os.environ.get('CRON_SECRET', 'test')
            self.headers = {'Authorization': f"Bearer {cron_secret}"}
    
    result = handler(MockRequest())
    print(json.dumps(result, indent=2))
