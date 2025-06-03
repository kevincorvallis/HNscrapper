#!/usr/bin/env python3
"""
Final Verification and Launch Script for HN Enhanced Scraper
"""

import os
import sys
import sqlite3
import subprocess
import time
import signal
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check database
    db_path = '/Users/kevin/Downloads/HNscrapper/data/enhanced_hn_articles.db'
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return False
    
    # Check template
    template_path = '/Users/kevin/Downloads/HNscrapper/templates/index.html'
    if not os.path.exists(template_path):
        print("❌ Enhanced template not found!")
        return False
    
    # Check app file
    app_path = '/Users/kevin/Downloads/HNscrapper/optimized_enhanced_app.py'
    if not os.path.exists(app_path):
        print("❌ Optimized app not found!")
        return False
    
    print("✅ All required files present")
    return True

def test_database():
    """Test database connectivity"""
    print("🗄️ Testing database...")
    
    try:
        db_path = '/Users/kevin/Downloads/HNscrapper/data/enhanced_hn_articles.db'
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        
        # Basic queries
        cursor.execute("SELECT COUNT(*) FROM articles")
        articles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM article_analyses")
        analyses = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comments")
        comments = cursor.fetchone()[0]
        
        print(f"   Articles: {articles}")
        print(f"   Analyses: {analyses}")
        print(f"   Comments: {comments}")
        
        if articles > 0:
            # Test sample data
            cursor.execute("""
                SELECT title, domain, discussion_quality_score 
                FROM articles a
                LEFT JOIN article_analyses aa ON a.hn_id = aa.hn_id
                WHERE aa.discussion_quality_score IS NOT NULL 
                LIMIT 1
            """)
            sample = cursor.fetchone()
            if sample:
                print(f"   Sample: '{sample[0][:30]}...' from {sample[1]} (Quality: {sample[2]})")
            
        conn.close()
        print("✅ Database test passed")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_app_import():
    """Test if the app can be imported"""
    print("🐍 Testing app import...")
    
    try:
        sys.path.insert(0, '/Users/kevin/Downloads/HNscrapper')
        
        # Import components
        from optimized_enhanced_app import app, OptimizedDatabaseManager, db_manager
        
        # Quick functionality test
        stats = db_manager.get_basic_stats()
        articles = db_manager.get_enhanced_articles_safe(limit=2)
        
        print(f"   ✅ Import successful")
        print(f"   ✅ Database manager working: {stats['total_articles']} articles")
        print(f"   ✅ Sample articles: {len(articles)} loaded")
        
        return True
        
    except Exception as e:
        print(f"❌ App import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def launch_app():
    """Launch the Flask application"""
    print("🚀 Launching HN Enhanced Scraper...")
    
    try:
        # Change to app directory
        os.chdir('/Users/kevin/Downloads/HNscrapper')
        
        # Start the app
        print("📡 Starting Flask server...")
        print("🌐 Homepage will be available at: http://127.0.0.1:8085")
        print("🧪 Test page will be available at: http://127.0.0.1:8085/test")
        print("\n📝 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Start subprocess with live output
        process = subprocess.Popen(
            [sys.executable, 'optimized_enhanced_app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        try:
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            print("✅ Server stopped")
            
        return True
        
    except Exception as e:
        print(f"❌ Launch failed: {e}")
        return False

def show_success_message():
    """Show success message with next steps"""
    print("\n" + "=" * 60)
    print("🎉 HN ENHANCED SCRAPER - READY FOR LAUNCH!")
    print("=" * 60)
    print("✅ Database connectivity verified")
    print("✅ Enhanced homepage template ready")
    print("✅ Optimized Flask application ready")
    print("✅ AI-powered features available")
    print()
    print("🚀 FEATURES AVAILABLE:")
    print("   • AI-analyzed article summaries")
    print("   • Discussion quality scoring")
    print("   • Advanced search and filtering")
    print("   • Real-time analytics dashboard")
    print("   • Modern Apple-inspired UI design")
    print("   • Responsive mobile-friendly layout")
    print()
    print("🌐 ACCESS POINTS:")
    print("   • Homepage: http://127.0.0.1:8085")
    print("   • Test Page: http://127.0.0.1:8085/test")
    print("   • Stats API: http://127.0.0.1:8085/api/stats")
    print("   • Search API: http://127.0.0.1:8085/api/search?q=query")
    print("=" * 60)

def main():
    """Main verification and launch sequence"""
    print("🚀 HN Enhanced Scraper - Final Verification & Launch")
    print("=" * 60)
    
    # Step 1: Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed")
        return False
    
    # Step 2: Test database
    if not test_database():
        print("\n❌ Database test failed")
        return False
    
    # Step 3: Test app import
    if not test_app_import():
        print("\n❌ App import test failed")
        return False
    
    # All tests passed
    show_success_message()
    
    # Ask user if they want to launch
    print("\n🚀 Ready to launch! Start the server? [Y/n]: ", end="", flush=True)
    try:
        response = input().strip().lower()
        if response in ['', 'y', 'yes']:
            return launch_app()
        else:
            print("\n✋ Launch cancelled by user")
            print("💡 To start manually, run: python optimized_enhanced_app.py")
            return True
    except KeyboardInterrupt:
        print("\n✋ Launch cancelled")
        return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎯 Verification completed successfully!")
        else:
            print("\n⚠️  Some issues were detected")
            print("💡 Check the output above for details")
    except Exception as e:
        print(f"\n❌ Verification script error: {e}")
        import traceback
        traceback.print_exc()
