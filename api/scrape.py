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
    
    # Verify authorization
    auth_header = request.headers.get('Authorization', '')
    cron_secret = os.environ.get('CRON_SECRET', 'default-secret')
    expected_auth = f"Bearer {cron_secret}"
    
    if auth_header != expected_auth:
        return {
            'statusCode': 401,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Unauthorized'})
        }
    
    try:
        if request.method == 'POST':
            # Trigger DynamoDB scraping
            results = scrape_hn_with_dynamodb()
            
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
    
    # Check AWS credentials
    aws_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    if not all([aws_key_id, aws_secret]):
        raise Exception(
            "AWS credentials not found. Please set AWS_ACCESS_KEY_ID and "
            "AWS_SECRET_ACCESS_KEY"
        )
    
    if HNScrapperDynamoDB is None:
        raise Exception(
            "HNScrapperDynamoDB not available. Check import dependencies."
        )
    
    try:
        # Use the DynamoDB scraper
        scraper = HNScrapperDynamoDB()
        
        # Run scrape with conservative limits for serverless environment
        results = scraper.scrape_daily(
            max_articles=10,
            max_comments_per_article=20
        )
        
        return results
    
    except Exception as e:
        print(f"Error in DynamoDB scraping: {e}")
        raise


# For local testing
if __name__ == "__main__":
    class MockRequest:
        def __init__(self):
            self.method = 'POST'
            cron_secret = os.environ.get('CRON_SECRET', 'test')
            self.headers = {'Authorization': f"Bearer {cron_secret}"}
    
    result = handler(MockRequest())
    print(json.dumps(result, indent=2))
