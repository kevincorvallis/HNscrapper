#!/usr/bin/env python3
"""
Direct Flask App Startup for HN Enhanced Scraper
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, '/Users/kevin/Downloads/HNscrapper')

try:
    print("🚀 Starting HN Enhanced Scraper...")
    print("📍 Current directory:", os.getcwd())
    
    # Import the optimized app
    from optimized_enhanced_app import app, OptimizedDatabaseManager
    
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
    
    # Start the Flask app
    port = 8085
    print(f"\n🌐 Starting Flask app on port {port}")
    print(f"🔗 Homepage: http://127.0.0.1:{port}")
    print(f"🧪 Test page: http://127.0.0.1:{port}/test")
    print("\n📝 Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the correct directory and all dependencies are installed")
    
except Exception as e:
    print(f"❌ Startup error: {e}")
    import traceback
    traceback.print_exc()
