#!/usr/bin/env python3
"""
Verification script to check the cleanup status of the HN scraper application.
This script verifies that malformed JSON summaries have been cleaned and 
that the application is properly focused on comment threads.
"""

import sqlite3
import re
import os
from datetime import datetime

def check_database_cleanup():
    """Check if the database has been cleaned of malformed JSON."""
    db_path = 'data/enhanced_hn_articles.db'
    
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Checking database cleanup status...")
    
    # Check for malformed JSON patterns in summaries
    cursor.execute("SELECT COUNT(*) FROM article_analyses WHERE summary LIKE '%'''json%'")
    json_artifacts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM article_analyses WHERE summary LIKE '%Analysis generated%'")
    analysis_artifacts = cursor.fetchone()[0]
    
    # Check total articles and comments
    cursor.execute("SELECT COUNT(*) FROM article_analyses")
    total_articles = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM comment_analyses")
    total_comments = cursor.fetchone()[0]
    
    # Check quality scores
    cursor.execute("SELECT COUNT(*) FROM comment_analyses WHERE quality_score > 0")
    quality_comments = cursor.fetchone()[0]
    
    # Check insightful comments
    cursor.execute("SELECT COUNT(*) FROM comment_analyses WHERE is_insightful = 1")
    insightful_comments = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"📊 Database Status:")
    print(f"   • Total articles: {total_articles}")
    print(f"   • Total comments: {total_comments}")
    print(f"   • Comments with quality scores: {quality_comments}")
    print(f"   • Insightful comments: {insightful_comments}")
    print()
    
    print(f"🧹 Cleanup Status:")
    if json_artifacts == 0:
        print(f"   ✅ JSON artifacts cleaned: 0 found")
    else:
        print(f"   ❌ JSON artifacts remaining: {json_artifacts}")
    
    if analysis_artifacts == 0:
        print(f"   ✅ Analysis artifacts cleaned: 0 found")
    else:
        print(f"   ❌ Analysis artifacts remaining: {analysis_artifacts}")
    
    return json_artifacts == 0 and analysis_artifacts == 0

def check_application_structure():
    """Check if the application files are properly structured."""
    print("\n🏗️ Checking application structure...")
    
    required_files = [
        'src/web/main.py',
        'src/web/templates/nyt_homepage.html',
        'src/web/templates/nyt_article.html',
        'src/web/templates/nyt_base_apple.html',
        'src/web/static/css/emergency-fix.css'
    ]
    
    all_files_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - Missing!")
            all_files_exist = False
    
    return all_files_exist

def check_comment_functions():
    """Check if the new comment-focused functions are implemented."""
    print("\n🛠️ Checking comment-focused functions...")
    
    main_py_path = 'src/web/main.py'
    if not os.path.exists(main_py_path):
        print("   ❌ main.py not found!")
        return False
    
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    functions_to_check = [
        'get_top_comment_threads',
        'get_comment_statistics'
    ]
    
    all_functions_exist = True
    for func_name in functions_to_check:
        if f"def {func_name}" in content:
            print(f"   ✅ {func_name}() function implemented")
        else:
            print(f"   ❌ {func_name}() function missing!")
            all_functions_exist = False
    
    return all_functions_exist

def check_template_updates():
    """Check if templates have been updated to focus on comments."""
    print("\n📄 Checking template updates...")
    
    # Check article template
    article_template = 'src/web/templates/nyt_article.html'
    if os.path.exists(article_template):
        with open(article_template, 'r') as f:
            content = f.read()
        
        if 'Top Discussion Threads' in content:
            print("   ✅ Article template updated with comment threads")
        else:
            print("   ❌ Article template missing comment thread display")
            return False
    
    # Check homepage template
    homepage_template = 'src/web/templates/nyt_homepage.html'
    if os.path.exists(homepage_template):
        with open(homepage_template, 'r') as f:
            content = f.read()
        
        if 'Top Community Insights' in content:
            print("   ✅ Homepage updated to focus on community insights")
        else:
            print("   ❌ Homepage still showing old AI analysis focus")
            return False
    
    return True

def main():
    """Run all verification checks."""
    print("🧪 HN Scraper Cleanup Verification")
    print("=" * 50)
    print(f"📅 Verification run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Change to project directory
    os.chdir('/Users/kevin/Downloads/HNscrapper')
    
    checks = [
        ("Database Cleanup", check_database_cleanup),
        ("Application Structure", check_application_structure),
        ("Comment Functions", check_comment_functions),
        ("Template Updates", check_template_updates)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"   ❌ Error during {check_name}: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ The HN scraper has been successfully cleaned up and refocused on comment discussions.")
        print("🚀 The application is ready to showcase quality community discussions instead of redundant AI analysis.")
    else:
        print("⚠️  SOME CHECKS FAILED!")
        print("🔧 Please review the issues above and fix them before proceeding.")
    
    print(f"\n📍 Application should be running at: http://localhost:8083")
    print("🌐 Test the comment thread display by visiting any article page.")

if __name__ == "__main__":
    main()
