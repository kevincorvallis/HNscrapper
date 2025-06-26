#!/usr/bin/env python3
"""
Detailed HN Scraper DynamoDB Schema Explorer
Focus on the HN scraper specific tables and their complete schema
"""

import boto3
import json
import os
from datetime import datetime
from decimal import Decimal

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def get_detailed_item_schema(dynamodb, table_name, sample_size=10):
    """Analyze items to determine all possible attributes and their types."""
    try:
        table = dynamodb.Table(table_name)
        response = table.scan(Limit=sample_size)
        items = response.get('Items', [])
        
        if not items:
            return {}
        
        # Collect all attributes and their types
        schema = {}
        for item in items:
            for key, value in item.items():
                if key not in schema:
                    schema[key] = set()
                schema[key].add(type(value).__name__)
        
        # Convert sets to lists for JSON serialization
        for key in schema:
            schema[key] = list(schema[key])
        
        return schema, items
    except Exception as e:
        print(f"Error analyzing {table_name}: {e}")
        return {}, []

def analyze_hn_tables():
    """Analyze HN scraper specific tables in detail."""
    print("🔍 Detailed HN Scraper DynamoDB Analysis")
    print("=" * 60)
    
    # Connect to DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-west-2'))
    
    # HN Scraper tables
    hn_tables = {
        'HN_article_data': 'Main articles storage',
        'hn-article-analyses': 'AI analysis results', 
        'hn-scraper-comments': 'Comments and discussions'
    }
    
    detailed_results = {}
    
    for table_name, description in hn_tables.items():
        print(f"\n📊 {table_name}")
        print(f"Description: {description}")
        print("-" * 50)
        
        try:
            # Get table info
            table = dynamodb.Table(table_name)
            table_meta = table.meta.client.describe_table(TableName=table_name)['Table']
            
            # Get schema from items
            schema, sample_items = get_detailed_item_schema(dynamodb, table_name, 20)
            
            print(f"Status: {table_meta['TableStatus']}")
            print(f"Item Count: {table_meta.get('ItemCount', 0)}")
            print(f"Table Size: {table_meta.get('TableSizeBytes', 0):,} bytes")
            
            # Key Schema
            print(f"\n🔑 Primary Key:")
            for key in table_meta['KeySchema']:
                print(f"  {key['KeyType']}: {key['AttributeName']}")
            
            # Detailed attribute analysis
            print(f"\n📝 All Attributes Found (from {len(sample_items)} sample items):")
            for attr_name, types in sorted(schema.items()):
                type_str = ', '.join(types)
                print(f"  {attr_name:20} : {type_str}")
            
            # Sample data structure
            if sample_items:
                print(f"\n📄 Sample Item Structure:")
                sample_item = sample_items[0]
                print(json.dumps(sample_item, indent=2, default=json_serial, ensure_ascii=False)[:1000] + "...")
            
            detailed_results[table_name] = {
                'schema': schema,
                'table_meta': table_meta,
                'sample_count': len(sample_items)
            }
            
        except Exception as e:
            print(f"❌ Error analyzing {table_name}: {e}")
            detailed_results[table_name] = {'error': str(e)}
    
    # Summary
    print(f"\n📊 HN Scraper Database Summary")
    print("=" * 50)
    
    total_items = 0
    total_size = 0
    
    for table_name, result in detailed_results.items():
        if 'error' not in result:
            items = result['table_meta'].get('ItemCount', 0)
            size = result['table_meta'].get('TableSizeBytes', 0)
            total_items += items
            total_size += size
            
            print(f"{table_name:25} : {items:6,} items, {size:10,} bytes")
    
    print("-" * 50)
    print(f"{'TOTAL':25} : {total_items:6,} items, {total_size:10,} bytes")
    print(f"Total Size: {total_size / 1024 / 1024:.2f} MB")
    
    # Data relationships
    print(f"\n🔗 Data Relationships:")
    print("HN_article_data.hn_id → hn-article-analyses.hn_id (1:1)")
    print("HN_article_data.hn_id → hn-scraper-comments.article_id (1:many)")
    
    return detailed_results

if __name__ == "__main__":
    analyze_hn_tables()
