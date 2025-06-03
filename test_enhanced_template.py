#!/usr/bin/env python3
"""
Template compatibility tester for the enhanced homepage
"""
import os
import sys
from flask import Flask, render_template

# Test data that matches the enhanced homepage template requirements
def get_test_data():
    """Generate test data that matches the template expectations."""
    return {
        'articles': [
            {
                'hn_id': '12345',
                'title': 'AI Breakthrough in Machine Learning',
                'url': 'https://example.com/ai-breakthrough',
                'domain': 'example.com',
                'summary': 'Researchers develop new neural network architecture that achieves state-of-the-art results.',
                'key_insights': 'Novel attention mechanism, 50% performance improvement, open source implementation',
                'main_themes': 'artificial intelligence, machine learning, research',
                'sentiment_analysis': 'positive',
                'discussion_quality_score': 8.5,
                'controversy_level': 'low',
                'analyzed_comments': 25,
                'total_comments': 45,
                'generated_at': '2025-06-03T10:00:00'
            },
            {
                'hn_id': '12346',
                'title': 'The Future of Web Development',
                'url': 'https://techblog.com/web-future',
                'domain': 'techblog.com',
                'summary': 'Exploring emerging trends and technologies shaping web development.',
                'key_insights': 'WebAssembly adoption, AI-powered development tools, performance optimization',
                'main_themes': 'web development, technology trends, programming',
                'sentiment_analysis': 'neutral',
                'discussion_quality_score': 7.2,
                'controversy_level': 'medium',
                'analyzed_comments': 18,
                'total_comments': 32,
                'generated_at': '2025-06-03T09:30:00'
            },
            {
                'hn_id': '12347',
                'title': 'Privacy Concerns in Modern Apps',
                'url': 'https://privacy.org/modern-apps',
                'domain': 'privacy.org',
                'summary': 'Analysis of data collection practices in popular mobile applications.',
                'key_insights': 'Excessive permissions, data monetization, regulatory gaps',
                'main_themes': 'privacy, mobile apps, data protection',
                'sentiment_analysis': 'negative',
                'discussion_quality_score': 9.1,
                'controversy_level': 'high',
                'analyzed_comments': 42,
                'total_comments': 78,
                'generated_at': '2025-06-03T08:45:00'
            }
        ],
        'stats': {
            'total_articles': 50,
            'analyzed_comments': 500,
            'total_comments': 6356,
            'avg_discussion_quality': 7.8,
            'avg_comment_quality': 6.9,
            'top_domains': [
                {'domain': 'github.com', 'count': 12},
                {'domain': 'techcrunch.com', 'count': 8},
                {'domain': 'ycombinator.com', 'count': 6},
                {'domain': 'stackoverflow.com', 'count': 5},
                {'domain': 'medium.com', 'count': 4}
            ],
            'sentiment_distribution': {
                'positive': 20,
                'neutral': 25,
                'negative': 5
            },
            'controversy_distribution': {
                'low': 30,
                'medium': 15,
                'high': 5
            },
            'insightful_comments': 156,
            'controversial_comments': 78
        },
        'domains': ['example.com', 'techblog.com', 'privacy.org', 'github.com', 'techcrunch.com'],
        'search_query': '',
        'domain_filter': 'all',
        'sort_by': 'quality',
        'view_mode': 'cards',
        'curator_available': True,
        'analyzer_available': True
    }

def test_template_rendering():
    """Test if the enhanced homepage template renders without errors."""
    print("🎨 Testing Enhanced Homepage Template")
    print("=" * 40)
    
    # Create Flask app
    app = Flask(__name__, template_folder='templates')
    
    with app.app_context():
        try:
            # Get test data
            test_data = get_test_data()
            print(f"✅ Test data prepared: {len(test_data['articles'])} articles, {len(test_data['domains'])} domains")
            
            # Try to render the template
            rendered_html = render_template('index.html', **test_data)
            
            print(f"✅ Template rendered successfully!")
            print(f"   • HTML length: {len(rendered_html):,} characters")
            
            # Check for specific elements that should be in the enhanced homepage
            checks = [
                ('AI-Powered Analysis Dashboard', 'Dashboard title'),
                ('Real-time Metrics', 'Metrics section'),
                ('Quality Score Distribution', 'Quality charts'),
                ('Sentiment Analysis', 'Sentiment features'),
                ('data-bs-toggle', 'Bootstrap functionality'),
                ('Chart.js', 'Chart integration'),
                ('var sentimentChart', 'Chart variables'),
                ('filter-tabs', 'Filter tabs'),
                ('search-input', 'Search functionality')
            ]
            
            found_features = 0
            for check_text, description in checks:
                if check_text in rendered_html:
                    print(f"   ✅ {description} found")
                    found_features += 1
                else:
                    print(f"   ⚠️  {description} missing or different")
            
            print(f"\n📊 Template Compatibility: {found_features}/{len(checks)} features found")
            
            if found_features >= len(checks) * 0.8:  # 80% threshold
                print("✅ Template is compatible with enhanced homepage!")
                return True, rendered_html
            else:
                print("⚠️  Template may need adjustments for full enhanced homepage functionality")
                return False, rendered_html
                
        except Exception as e:
            print(f"❌ Template rendering failed: {e}")
            import traceback
            traceback.print_exc()
            return False, None

def save_test_html(html_content):
    """Save the rendered HTML for inspection."""
    if html_content:
        test_file = 'test_enhanced_homepage.html'
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"💾 Test HTML saved to: {test_file}")
        print(f"   Open in browser to inspect: file://{os.path.abspath(test_file)}")

def create_minimal_test_server():
    """Create a minimal server to test the enhanced homepage live."""
    print("\n🚀 Creating Minimal Test Server")
    print("=" * 35)
    
    app = Flask(__name__, template_folder='templates')
    app.secret_key = 'test-key-enhanced-homepage'
    
    @app.route('/')
    def index():
        test_data = get_test_data()
        return render_template('index.html', **test_data)
    
    @app.route('/api/stats')
    def api_stats():
        test_data = get_test_data()
        from flask import jsonify
        return jsonify(test_data['stats'])
    
    @app.route('/api/test')
    def api_test():
        return {'status': 'ok', 'message': 'Enhanced homepage template test server running'}
    
    print("✅ Minimal test server created")
    print("📊 Enhanced homepage with test data")
    print("🌐 Starting on http://localhost:5002")
    
    try:
        app.run(host='0.0.0.0', port=5002, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Test server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    print("🧪 Enhanced Homepage Template Compatibility Test")
    print("=" * 60)
    
    # Test template rendering
    success, html_content = test_template_rendering()
    
    if success:
        print("\n✅ Template test passed!")
        
        # Save test HTML
        save_test_html(html_content)
        
        # Ask if user wants to start test server
        print(f"\n🚀 Start test server? [y/N]: ", end="")
        try:
            response = input().strip().lower()
            if response in ['y', 'yes']:
                create_minimal_test_server()
            else:
                print("👋 Test completed. Use the saved HTML file to inspect the template.")
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Test completed.")
    else:
        print("\n❌ Template test failed!")
        print("   • Check template syntax and required variables")
        print("   • Ensure all template dependencies are available")
        if html_content:
            save_test_html(html_content)
            print("   • Check saved HTML file for error details")
