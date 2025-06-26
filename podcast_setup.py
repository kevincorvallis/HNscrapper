#!/usr/bin/env python3
"""
Podcast System Setup and Configuration
Helps configure API keys, test the system, and provides usage examples
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv, set_key
import requests

def check_environment():
    """Check if all required environment variables are set."""
    load_dotenv()
    
    required_vars = {
        'AWS_ACCESS_KEY_ID': 'AWS Access Key for DynamoDB',
        'AWS_SECRET_ACCESS_KEY': 'AWS Secret Key for DynamoDB', 
        'AWS_DEFAULT_REGION': 'AWS Region (e.g., us-east-1)'
    }
    
    optional_vars = {
        'OPENAI_API_KEY': 'OpenAI API Key for script generation',
        'ELEVENLABS_API_KEY': 'ElevenLabs API Key for audio generation',
        'ELEVENLABS_VOICE_ID': 'ElevenLabs Voice ID (optional)'
    }
    
    print("🔍 Environment Configuration Check")
    print("=" * 50)
    
    # Check required variables
    missing_required = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Configured")
        else:
            print(f"❌ {var}: Missing ({description})")
            missing_required.append(var)
    
    print("\nOptional Configuration:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Configured")
        else:
            print(f"⚠️  {var}: Not set ({description})")
    
    if missing_required:
        print(f"\n❌ Missing required variables: {', '.join(missing_required)}")
        print("Please set these in your .env file")
        return False
    else:
        print("\n✅ All required environment variables are configured!")
        return True

def setup_env_file():
    """Interactive setup of .env file."""
    print("\n🛠️ Environment Setup Assistant")
    print("=" * 50)
    
    env_file = '.env'
    
    # Load existing .env if it exists
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"Found existing {env_file}")
    else:
        print(f"Creating new {env_file}")
    
    configs = {}
    
    # AWS Configuration
    print("\n📊 AWS DynamoDB Configuration (Required):")
    configs['AWS_ACCESS_KEY_ID'] = input(f"AWS Access Key ID [{os.getenv('AWS_ACCESS_KEY_ID', '')}]: ") or os.getenv('AWS_ACCESS_KEY_ID', '')
    configs['AWS_SECRET_ACCESS_KEY'] = input(f"AWS Secret Access Key [{os.getenv('AWS_SECRET_ACCESS_KEY', '')}]: ") or os.getenv('AWS_SECRET_ACCESS_KEY', '')
    configs['AWS_DEFAULT_REGION'] = input(f"AWS Region [{os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}]: ") or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    # OpenAI Configuration
    print("\n🤖 OpenAI Configuration (Optional - for AI script generation):")
    current_openai = os.getenv('OPENAI_API_KEY', '')
    openai_key = input(f"OpenAI API Key [{current_openai[:10] + '...' if current_openai else 'Not set'}]: ") or current_openai
    if openai_key:
        configs['OPENAI_API_KEY'] = openai_key
    
    # ElevenLabs Configuration
    print("\n🎵 ElevenLabs Configuration (Optional - for audio generation):")
    current_elevenlabs = os.getenv('ELEVENLABS_API_KEY', '')
    elevenlabs_key = input(f"ElevenLabs API Key [{current_elevenlabs[:10] + '...' if current_elevenlabs else 'Not set'}]: ") or current_elevenlabs
    if elevenlabs_key:
        configs['ELEVENLABS_API_KEY'] = elevenlabs_key
        
        current_voice = os.getenv('ELEVENLABS_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')
        voice_id = input(f"ElevenLabs Voice ID [{current_voice}]: ") or current_voice
        configs['ELEVENLABS_VOICE_ID'] = voice_id
    
    # Save to .env file
    for key, value in configs.items():
        if value:
            set_key(env_file, key, value)
            print(f"Set {key}")
    
    print(f"\n✅ Configuration saved to {env_file}")
    return True

def test_database_connection():
    """Test connection to DynamoDB."""
    print("\n🔌 Testing Database Connection")
    print("=" * 30)
    
    try:
        from dynamodb_manager import DynamoDBManager
        
        db = DynamoDBManager()
        stats = db.get_database_stats()
        
        print("✅ DynamoDB connection successful!")
        print(f"   Total articles: {stats.get('total_articles', 0)}")
        print(f"   Total comments: {stats.get('total_comments', 0)}")
        print(f"   Total analyses: {stats.get('total_analyses', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_openai_connection():
    """Test OpenAI API connection."""
    print("\n🤖 Testing OpenAI Connection")
    print("=" * 30)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  OpenAI API key not configured")
        return False
    
    try:
        import openai
        
        client = openai.OpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        
        print("✅ OpenAI connection successful!")
        print(f"   Model: gpt-3.5-turbo")
        print(f"   Response: {response.choices[0].message.content[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False

def test_elevenlabs_connection():
    """Test ElevenLabs API connection."""
    print("\n🎵 Testing ElevenLabs Connection") 
    print("=" * 30)
    
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("⚠️  ElevenLabs API key not configured")
        return False
    
    try:
        # Test API connection with voice list
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {
            "Accept": "application/json",
            "xi-api-key": api_key
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            voices = response.json().get('voices', [])
            print("✅ ElevenLabs connection successful!")
            print(f"   Available voices: {len(voices)}")
            
            voice_id = os.getenv('ELEVENLABS_VOICE_ID')
            if voice_id:
                voice_names = [v['name'] for v in voices if v['voice_id'] == voice_id]
                if voice_names:
                    print(f"   Selected voice: {voice_names[0]} ({voice_id})")
                else:
                    print(f"   ⚠️  Voice ID {voice_id} not found")
            
            return True
        else:
            print(f"❌ ElevenLabs API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ElevenLabs connection failed: {e}")
        return False

def run_system_test():
    """Run a complete system test."""
    print("\n🧪 Running System Test")
    print("=" * 50)
    
    try:
        from daily_podcast_generator import DailyPodcastGenerator
        
        generator = DailyPodcastGenerator()
        
        # Test with yesterday's date to avoid conflicts
        from datetime import timedelta
        test_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"Testing podcast generation for {test_date}...")
        
        # Test article fetching
        articles = generator.get_daily_articles(test_date)
        print(f"   Found {len(articles)} qualifying articles")
        
        if articles:
            # Test script generation
            script = generator.generate_podcast_script(articles[:2])  # Use only 2 articles for testing
            print(f"   Generated script: {len(script.split())} words")
            
            # Test episode creation (without audio)
            episode = generator.PodcastEpisode(
                date=test_date,
                title=f"Test Episode - {test_date}",
                script=script[:200] + "...",  # Truncated for test
                articles_featured=[a.get('id', '') for a in articles[:2]]
            )
            
            print("✅ System test completed successfully!")
            print(f"   Episode title: {episode.title}")
            print(f"   Articles featured: {len(episode.articles_featured)}")
            
            return True
        else:
            print("⚠️  No articles found for testing - this is normal if no recent data")
            return True
            
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def show_usage_examples():
    """Show usage examples and commands."""
    print("\n📖 Usage Examples")
    print("=" * 50)
    
    print("1. Generate today's podcast:")
    print("   python daily_podcast_generator.py")
    
    print("\n2. Generate podcast for specific date:")
    print("   python auto_podcast_runner.py --date 2024-01-15")
    
    print("\n3. Backfill last 7 days:")
    print("   python auto_podcast_runner.py --backfill 7")
    
    print("\n4. Run tests:")
    print("   python test_podcast_system.py")
    
    print("\n5. Start web server with podcast dashboard:")
    print("   python api/index.py")
    print("   Then visit: http://localhost:5000/podcast")
    
    print("\n6. API endpoints:")
    print("   GET  /api/podcast/episodes - List recent episodes")
    print("   GET  /api/podcast/episode/<date> - Get specific episode")
    print("   POST /api/podcast/generate - Generate new episode")
    
    print("\n7. Schedule daily generation (cron example):")
    print("   0 9 * * * cd /path/to/project && python auto_podcast_runner.py --quiet")

def main():
    """Main setup function."""
    print("🎙️ Daily Podcast Generator Setup")
    print("=" * 50)
    
    print("This tool will help you set up and test the daily podcast generation system.")
    
    while True:
        print("\nWhat would you like to do?")
        print("1. Check environment configuration")
        print("2. Set up .env file interactively")
        print("3. Test database connection")
        print("4. Test OpenAI connection")
        print("5. Test ElevenLabs connection")
        print("6. Run complete system test")
        print("7. Show usage examples")
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == '1':
            check_environment()
        elif choice == '2':
            setup_env_file()
        elif choice == '3':
            test_database_connection()
        elif choice == '4':
            test_openai_connection()
        elif choice == '5':
            test_elevenlabs_connection()
        elif choice == '6':
            run_system_test()
        elif choice == '7':
            show_usage_examples()
        elif choice == '8':
            print("\n👋 Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-8.")

if __name__ == "__main__":
    main()
