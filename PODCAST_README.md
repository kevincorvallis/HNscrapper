# Daily Podcast Generator for Hacker News

An AI-powered system that automatically generates 5-10 minute daily podcast episodes from the most engaging Hacker News articles and discussions.

## 🎙️ Features

- **Automated Article Selection**: Intelligently selects top articles based on score and engagement
- **AI-Powered Script Generation**: Uses OpenAI GPT to create natural, conversational podcast scripts
- **Text-to-Speech Integration**: Generates audio using ElevenLabs TTS
- **Web Dashboard**: Beautiful interface to view and manage episodes
- **API Endpoints**: RESTful API for integration with other systems
- **DynamoDB Storage**: Cloud-native storage for episodes and metadata
- **Comprehensive Testing**: Full test suite with mocks and integration tests

## 🚀 Quick Start

### 1. Set Up Environment

Run the interactive setup tool:

```bash
python podcast_setup.py
```

This will guide you through:
- Setting up your `.env` file with API keys
- Testing database connections
- Verifying API integrations

### 2. Generate Your First Episode

```bash
# Generate today's episode
python daily_podcast_generator.py

# Or use the automation runner
python auto_podcast_runner.py
```

### 3. View the Dashboard

```bash
python api/index.py
```

Then visit `http://localhost:5000/podcast` to see your episodes.

## ⚙️ Configuration

Create a `.env` file with the following variables:

### Required (for basic functionality):
```env
# AWS DynamoDB
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### Optional (for enhanced features):
```env
# OpenAI (for AI-generated scripts)
OPENAI_API_KEY=your_openai_api_key

# ElevenLabs (for audio generation)
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL
```

## 📖 Usage

### Command Line Interface

```bash
# Generate today's podcast
python auto_podcast_runner.py

# Generate for specific date
python auto_podcast_runner.py --date 2024-01-15

# Backfill multiple days
python auto_podcast_runner.py --backfill 7

# Quiet mode (for cron jobs)
python auto_podcast_runner.py --quiet
```

### Web API

```bash
# List recent episodes
curl http://localhost:5000/api/podcast/episodes

# Get specific episode
curl http://localhost:5000/api/podcast/episode/2024-01-15

# Generate new episode
curl -X POST http://localhost:5000/api/podcast/generate \
  -H "Content-Type: application/json" \
  -d '{"date": "2024-01-15"}'
```

### Automation (Cron)

Add to your crontab for daily generation at 9 AM:

```bash
0 9 * * * cd /path/to/project && python auto_podcast_runner.py --quiet
```

## 🏗️ Architecture

### Core Components

1. **DailyPodcastGenerator**: Main orchestrator class
   - Article selection and filtering
   - Discussion analysis
   - Script generation (AI or template-based)
   - Audio generation with ElevenLabs
   - Database storage

2. **AutoPodcastRunner**: Automation wrapper
   - Command-line interface
   - Batch processing for backfills
   - Error handling and logging

3. **Web Dashboard**: Flask-based interface
   - Episode browsing and playback
   - Manual episode generation
   - API endpoints

4. **Database Integration**: DynamoDB storage
   - Episode metadata and scripts
   - Article associations
   - Analytics data

### Data Flow

```
HN Articles (DynamoDB) → Article Selection → Discussion Analysis → 
Script Generation (OpenAI) → Audio Generation (ElevenLabs) → 
Storage (DynamoDB) → Web Dashboard
```

## 🎛️ Customization

### Article Selection Criteria

Edit `daily_podcast_generator.py`:

```python
# Modify these parameters
self.min_score = 50           # Minimum article score
self.min_comments = 10        # Minimum comment count
self.max_articles = 5         # Maximum articles per episode
```

### Podcast Parameters

```python
# Adjust duration and pacing
self.target_duration = 7 * 60  # 7 minutes target
self.words_per_minute = 160    # Speaking speed
```

### Script Templates

Customize the script generation in `_generate_template_script()` method to match your preferred style and format.

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_podcast_system.py
```

Tests cover:
- Unit tests for all major functions
- Integration tests with mocked APIs
- Error handling scenarios
- End-to-end workflow validation

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:5000/health
```

### Episode Statistics

View recent episodes and their metadata through the web dashboard or API endpoints.

### Logs

The system provides detailed logging for troubleshooting:
- Article selection process
- Script generation results
- Audio generation status
- Database operations

## 🔧 Troubleshooting

### Common Issues

**No episodes generated:**
- Check if articles meet minimum score/comment criteria
- Verify date format (YYYY-MM-DD)
- Ensure database contains articles for the target date

**Audio generation fails:**
- Verify ElevenLabs API key and voice ID
- Check API quota and billing status
- Review script length (very long scripts may fail)

**Script quality issues:**
- Ensure OpenAI API key is configured
- Check article and comment quality in database
- Adjust selection criteria for better content

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 Development

### Adding New Features

1. **Custom TTS Providers**: Implement new audio generation methods
2. **Enhanced AI Models**: Integrate other LLMs for script generation
3. **Analytics Dashboard**: Add usage and engagement tracking
4. **Multi-language Support**: Generate podcasts in different languages

### File Structure

```
├── daily_podcast_generator.py    # Main podcast generation logic
├── auto_podcast_runner.py        # Automation and CLI interface
├── podcast_setup.py              # Interactive setup tool
├── test_podcast_system.py        # Comprehensive test suite
├── api/
│   ├── index.py                  # Flask app with podcast endpoints
│   └── templates/
│       └── podcast.html          # Web dashboard
└── requirements.txt              # Python dependencies
```

## 📈 Scaling

### Production Deployment

- Deploy on Vercel for serverless operation
- Use AWS Lambda for scheduled generation
- Implement CDN for audio file distribution
- Add caching for improved performance

### Performance Optimization

- Cache frequently accessed articles
- Implement background job processing
- Use connection pooling for database operations
- Optimize script generation prompts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

[Add your license information here]

## 🙏 Acknowledgments

- OpenAI for GPT models
- ElevenLabs for text-to-speech
- Hacker News community for content
- AWS for cloud infrastructure

---

**Need help?** Run `python podcast_setup.py` for an interactive setup guide or check the troubleshooting section above.
