#!/usr/bin/env python3
"""
DynamoDB Table Explorer
Explore tables, schema, and data in your DynamoDB setup
"""

import boto3
import json
import os
from datetime import datetime
from botocore.exceptions import ClientError

def get_dynamodb_client():
    """Get DynamoDB client with credentials from environment."""
    try:
        # Check for AWS credentials
        access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        region = os.environ.get('AWS_REGION', 'us-west-2')
        
        if not access_key or not secret_key:
            print("⚠️  AWS credentials not found in environment variables")
            print("Looking for credentials in default locations...")
            
        dynamodb = boto3.resource('dynamodb', region_name=region)
        dynamodb_client = boto3.client('dynamodb', region_name=region)
        
        return dynamodb, dynamodb_client, region
        
    except Exception as e:
        print(f"❌ Error connecting to DynamoDB: {e}")
        return None, None, None

def list_all_tables(dynamodb_client):
    """List all DynamoDB tables in the account."""
    try:
        print("🔍 Listing all DynamoDB tables...")
        print("=" * 50)
        
        response = dynamodb_client.list_tables()
        tables = response.get('TableNames', [])
        
        if not tables:
            print("No tables found in DynamoDB")
            return []
        
        print(f"Found {len(tables)} tables:")
        for i, table_name in enumerate(tables, 1):
            print(f"{i:2d}. {table_name}")
        
        return tables
        
    except Exception as e:
        print(f"❌ Error listing tables: {e}")
        return []

def describe_table(dynamodb_client, table_name):
    """Get detailed information about a table."""
    try:
        print(f"\n📊 Table: {table_name}")
        print("-" * 60)
        
        response = dynamodb_client.describe_table(TableName=table_name)
        table_info = response['Table']
        
        # Basic info
        print(f"Status: {table_info['TableStatus']}")
        print(f"Item Count: {table_info.get('ItemCount', 'Unknown')}")
        print(f"Table Size: {table_info.get('TableSizeBytes', 'Unknown')} bytes")
        print(f"Created: {table_info.get('CreationDateTime', 'Unknown')}")
        
        # Key schema
        print(f"\n🔑 Key Schema:")
        for key in table_info['KeySchema']:
            key_type = key['KeyType']
            attr_name = key['AttributeName']
            print(f"  {key_type}: {attr_name}")
        
        # Attribute definitions
        print(f"\n📝 Attribute Definitions:")
        for attr in table_info['AttributeDefinitions']:
            attr_name = attr['AttributeName']
            attr_type = attr['AttributeType']
            print(f"  {attr_name}: {attr_type}")
        
        # Billing mode
        billing_mode = table_info.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
        print(f"\n💰 Billing Mode: {billing_mode}")
        
        if billing_mode == 'PROVISIONED':
            throughput = table_info.get('ProvisionedThroughput', {})
            print(f"  Read Capacity: {throughput.get('ReadCapacityUnits', 'Unknown')}")
            print(f"  Write Capacity: {throughput.get('WriteCapacityUnits', 'Unknown')}")
        
        # Global Secondary Indexes
        gsi_list = table_info.get('GlobalSecondaryIndexes', [])
        if gsi_list:
            print(f"\n🌐 Global Secondary Indexes ({len(gsi_list)}):")
            for gsi in gsi_list:
                print(f"  Index: {gsi['IndexName']}")
                print(f"    Status: {gsi['IndexStatus']}")
                for key in gsi['KeySchema']:
                    print(f"    {key['KeyType']}: {key['AttributeName']}")
        
        # Local Secondary Indexes
        lsi_list = table_info.get('LocalSecondaryIndexes', [])
        if lsi_list:
            print(f"\n📍 Local Secondary Indexes ({len(lsi_list)}):")
            for lsi in lsi_list:
                print(f"  Index: {lsi['IndexName']}")
                for key in lsi['KeySchema']:
                    print(f"    {key['KeyType']}: {key['AttributeName']}")
        
        return table_info
        
    except Exception as e:
        print(f"❌ Error describing table {table_name}: {e}")
        return None

def scan_table_sample(dynamodb, table_name, limit=5):
    """Get a few sample items from the table."""
    try:
        print(f"\n📄 Sample Items from {table_name} (limit {limit}):")
        print("-" * 40)
        
        table = dynamodb.Table(table_name)
        response = table.scan(Limit=limit)
        items = response.get('Items', [])
        
        if not items:
            print("No items found in table")
            return
        
        for i, item in enumerate(items, 1):
            print(f"\nItem {i}:")
            # Show first few attributes to avoid overwhelming output
            sample_attrs = dict(list(item.items())[:5])
            for key, value in sample_attrs.items():
                # Truncate long values
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"  {key}: {value}")
            
            if len(item) > 5:
                print(f"  ... and {len(item) - 5} more attributes")
        
        print(f"\nTotal items scanned: {len(items)}")
        if 'LastEvaluatedKey' in response:
            print("(More items available)")
            
    except Exception as e:
        print(f"❌ Error scanning table {table_name}: {e}")

def main():
    """Main function to explore DynamoDB tables."""
    print("🗄️  DynamoDB Table Explorer")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get DynamoDB connection
    dynamodb, dynamodb_client, region = get_dynamodb_client()
    if not dynamodb or not dynamodb_client:
        print("❌ Failed to connect to DynamoDB")
        return 1
    
    print(f"✅ Connected to DynamoDB in region: {region}")
    print()
    
    # List all tables
    tables = list_all_tables(dynamodb_client)
    if not tables:
        return 1
    
    # Describe each table
    for table_name in tables:
        describe_table(dynamodb_client, table_name)
        scan_table_sample(dynamodb, table_name, limit=3)
        print("\n" + "=" * 80 + "\n")
    
    # Summary
    print("📊 Summary:")
    print(f"  Total tables: {len(tables)}")
    print(f"  Region: {region}")
    print(f"  Explored at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0

if __name__ == "__main__":
    exit(main())
