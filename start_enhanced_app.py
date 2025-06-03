#!/usr/bin/env python3
"""
Direct FastAPI App Startup for HN Enhanced Scraper
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, '/Users/kevin/Downloads/HNscrapper')

try:
    print("🚀 Starting HN Enhanced Scraper (FastAPI)...")
    print("📍 Current directory:", os.getcwd())
    
    # Import the FastAPI app
    from fastapi_enhanced_app import app, OptimizedDatabaseManager
    
    print("✅ App imported successfully")
    
    # Test database connection
    db_path = '/Users/kevin/Downloads/HNscrapper/data/enhanced_hn_articles.db'
    print(f"🗄️ Testing database: {db_path}")
    
    if os.path.exists(db_path):
        print("✅ Database file exists")
        
        # Test connection
        db_manager = OptimizedDatabaseManager(db_path)
        stats = db_manager.get_basic_stats()
        print(f"✅ Database stats: {stats}")
        
        # Test sample articles
        articles = db_manager.get_enhanced_articles_safe(limit=3)
        print(f"✅ Sample articles: {len(articles)} retrieved")
        
    else:
        print("❌ Database file not found")
    
    # Start the FastAPI app with uvicorn
    import uvicorn
    port = 8085
    print(f"\n🌐 Starting FastAPI app on port {port}")
    print(f"🔗 Homepage: http://127.0.0.1:{port}")
    print(f"📖 API Documentation: http://127.0.0.1:{port}/docs")
    print(f"🧪 Test page: http://127.0.0.1:{port}/test")
    print("\n📝 Press Ctrl+C to stop")
    
    uvicorn.run(app, host='0.0.0.0', port=port, reload=False)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the correct directory and all dependencies are installed")
    
except Exception as e:
    print(f"❌ Startup error: {e}")
    import traceback
    traceback.print_exc()
