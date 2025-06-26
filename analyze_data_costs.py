#!/usr/bin/env python3
"""
Analyze DynamoDB data volume and costs
"""

from dynamodb_manager import DynamoDBManager
from dotenv import load_dotenv
import json
import boto3

load_dotenv()

def analyze_data_volume():
    print('📊 ANALYZING DATA VOLUME AND COSTS')
    print('=' * 50)

    db = DynamoDBManager()
    stats = db.get_stats()

    print('Current Data Volume:')
    print(f'  Articles: {stats["total_articles"]}')
    print(f'  Comments: {stats["total_comments"]}') 
    avg_comments = stats['total_comments'] / max(stats['total_articles'], 1)
    print(f'  Avg comments per article: {avg_comments:.1f}')

    print('\nEstimated Storage (rough):')

    # Sample article to estimate size
    articles = db.get_articles(limit=1)
    if articles:
        # Convert DynamoDB Decimals to regular numbers for JSON serialization
        article = articles[0]
        article_dict = {}
        for key, value in article.items():
            if hasattr(value, '__float__'):  # Handle Decimal
                article_dict[key] = float(value)
            else:
                article_dict[key] = value
        
        article_json = json.dumps(article_dict)
        article_size = len(article_json.encode('utf-8'))
        total_article_size = article_size * stats['total_articles']
        print(f'  Article size (sample): {article_size} bytes')
        print(f'  Total articles: {total_article_size / 1024:.1f} KB')

        # Sample comments to estimate size  
        comments = db.get_article_comments(articles[0]['hn_id'])
        if comments:
            # Comments are already converted in the manager
            comment_json = json.dumps(comments[0])
            comment_size = len(comment_json.encode('utf-8'))
            total_comment_size = comment_size * stats['total_comments']
            print(f'  Comment size (sample): {comment_size} bytes')
            print(f'  Total comments: {total_comment_size / 1024:.1f} KB')
            total_size_kb = (total_article_size + total_comment_size) / 1024
            print(f'  TOTAL ESTIMATED: {total_size_kb:.1f} KB')
            
            # Cost estimates (very rough)
            monthly_cost = total_size_kb * 0.25 / 1024  # $0.25 per GB/month
            print(f'  Est. monthly storage cost: ${monthly_cost:.4f}')
            
            print('\n💡 OPTIMIZATION INSIGHTS:')
            comment_percentage = (total_comment_size/total_article_size)*100
            print(f'  Comments are {comment_percentage:.0f}% of total data')
            print(f'  Daily growth (est.): ~{(total_size_kb/30):.1f} KB/day')
            
            return {
                'total_articles': stats['total_articles'],
                'total_comments': stats['total_comments'],
                'article_size': article_size,
                'comment_size': comment_size,
                'total_size_kb': total_size_kb,
                'monthly_cost': monthly_cost,
                'comment_percentage': comment_percentage
            }

def get_actual_table_sizes():
    """Get actual table sizes from DynamoDB"""
    print('\n📏 ACTUAL DYNAMODB TABLE SIZES')
    print('=' * 40)
    
    try:
        dynamodb = boto3.client('dynamodb', region_name='us-west-2')
        
        # Get articles table info
        articles_info = dynamodb.describe_table(TableName='HN_article_data')
        articles_size = articles_info['Table']['TableSizeBytes']
        articles_count = articles_info['Table']['ItemCount']
        
        # Get comments table info  
        comments_info = dynamodb.describe_table(TableName='hn-scraper-comments')
        comments_size = comments_info['Table']['TableSizeBytes']
        comments_count = comments_info['Table']['ItemCount']
        
        total_size = articles_size + comments_size
        
        print(f'Articles table:')
        print(f'  Size: {articles_size / 1024:.1f} KB ({articles_count} items)')
        print(f'  Avg per item: {articles_size / max(articles_count, 1):.0f} bytes')
        
        print(f'Comments table:')
        print(f'  Size: {comments_size / 1024:.1f} KB ({comments_count} items)')
        print(f'  Avg per item: {comments_size / max(comments_count, 1):.0f} bytes')
        
        print(f'Total: {total_size / 1024:.1f} KB')
        
        # Real cost calculation
        monthly_storage_cost = (total_size / (1024**3)) * 0.25  # $0.25 per GB/month
        print(f'Actual monthly storage cost: ${monthly_storage_cost:.6f}')
        
        return {
            'articles_size': articles_size,
            'comments_size': comments_size,
            'total_size': total_size,
            'monthly_storage_cost': monthly_storage_cost
        }
        
    except Exception as e:
        print(f'Could not get actual table sizes: {e}')
        return None

if __name__ == '__main__':
    estimated = analyze_data_volume()
    actual = get_actual_table_sizes()
    
    if estimated and actual:
        print('\n📊 COST OPTIMIZATION RECOMMENDATIONS')
        print('=' * 50)
        
        if estimated['comment_percentage'] > 80:
            print('🔥 COMMENTS DOMINATE STORAGE:')
            print('  • Consider compressing comment content')
            print('  • Store only top-level comments for popular articles')
            print('  • Archive old comments to cheaper storage')
        
        if actual['monthly_storage_cost'] < 0.01:
            print('💰 COSTS ARE MINIMAL:')
            print('  • Current storage costs are negligible')
            print('  • Focus on read/write costs instead')
            print('  • Consider on-demand billing vs provisioned')
        
        print('\n🚀 GROWTH PROJECTIONS:')
        daily_items = 100  # Assume 100 new articles per day
        daily_comments = daily_items * estimated['total_comments'] / estimated['total_articles']
        yearly_growth = (daily_items * 365 * estimated['article_size'] + 
                        daily_comments * 365 * estimated['comment_size']) / 1024
        print(f'  Est. yearly growth: {yearly_growth:.0f} KB')
        print(f'  Still very affordable: ~${yearly_growth * 0.25 / 1024:.4f}/year')
