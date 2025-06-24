# HN Scraper - Vercel Deployment Guide

## 🚀 Quick Deployment

### 1. **Install Vercel CLI**
```bash
npm i -g vercel
vercel login
```

### 2. **Deploy to Vercel**
```bash
# From your project directory
vercel --prod
```

### 3. **Configure Environment Variables**
In your Vercel dashboard, add these environment variables:

#### Required:
- `OPENAI_API_KEY` - Your OpenAI API key
- `SECRET_KEY` - Random secure string for Flask sessions
- `CRON_SECRET` - Random secure string for scheduled scraping

#### Optional:
- `AWS_ACCESS_KEY_ID` - For S3 storage
- `AWS_SECRET_ACCESS_KEY` - For S3 storage
- `DATABASE_URL` - External database (PostgreSQL)

### 4. **Set up GitHub Actions**
In your GitHub repository, add these secrets:
- `VERCEL_SCRAPE_URL` - Your Vercel app URL (e.g., https://your-app.vercel.app)
- `CRON_SECRET` - Same as the one in Vercel

## 📊 Features Available

✅ **Web Interface**: Modern, responsive dashboard
✅ **Article Scraping**: HN best articles
✅ **AI Analysis**: OpenAI-powered content analysis
✅ **Search & Filter**: Find articles and comments
✅ **API Endpoints**: RESTful API for programmatic access
✅ **Health Monitoring**: Built-in health checks
✅ **Daily Automation**: GitHub Actions for scheduled scraping

## 🛠 Development

### Local Development
```bash
# Install dependencies
pip install -r requirements-vercel.txt

# Run locally
python api/index.py
```

### Testing API Functions
```bash
# Test scraping function
python api/scrape.py

# Test analysis function
python api/analyze.py
```

## 📋 API Endpoints

### Main Routes
- `GET /` - Main dashboard
- `GET /health` - Health check

### API Routes
- `GET /api/stats` - Database statistics
- `GET /api/articles` - Get articles with filtering
- `GET /api/search` - Search articles and comments
- `POST /api/scrape` - Trigger scraping (requires auth)
- `POST /api/analyze` - Analyze content with AI

### Example API Usage
```javascript
// Get articles
fetch('/api/articles?limit=10')
  .then(response => response.json())
  .then(data => console.log(data));

// Search
fetch('/api/search?q=typescript')
  .then(response => response.json())
  .then(data => console.log(data));

// Analyze comment
fetch('/api/analyze', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    type: 'comment',
    content: 'This is a great discussion about AI.'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## 🗄 Database Options

### SQLite (Default - Temporary)
- Good for development and testing
- Data resets on each deployment

### Supabase (Recommended)
1. Create account at supabase.com
2. Create new project
3. Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` in Vercel
4. Update code to use Supabase client

### PostgreSQL
- Set `DATABASE_URL` environment variable
- Update database connection code

## 📈 Monitoring

### Health Check
```bash
curl https://your-app.vercel.app/health
```

### Vercel Analytics
- Built-in analytics available in Vercel dashboard
- Monitor function invocations and performance

### Custom Monitoring
Add monitoring services like:
- Sentry for error tracking
- Uptime Robot for availability monitoring
- DataDog for detailed metrics

## 🔧 Customization

### Adding New Features
1. Create new API function in `/api/` directory
2. Add route to `vercel.json` if needed
3. Update frontend in templates

### Modifying Scraping
- Edit `api/scrape.py`
- Adjust scraping frequency in `.github/workflows/daily-scrape.yml`

### Enhancing AI Analysis
- Update prompts in `api/analyze.py`
- Add new analysis types
- Integrate additional AI services

## 🚨 Troubleshooting

### Common Issues
1. **OpenAI API errors**: Check API key and billing
2. **Database connection**: Verify DATABASE_URL
3. **Deployment failures**: Check Vercel logs
4. **Cron job failures**: Verify GitHub secrets

### Debug Commands
```bash
# Check Vercel logs
vercel logs

# Test local deployment
vercel dev

# Check function limits
vercel inspect
```

## 💰 Cost Estimation

### Vercel
- **Free tier**: 100GB bandwidth, 100GB-hrs compute
- **Pro**: $20/month for higher limits

### OpenAI API
- **GPT-3.5 Turbo**: ~$0.002 per 1K tokens
- **Estimated**: $5-20/month depending on usage

### Total: ~$0-40/month depending on usage

## 🔐 Security

- Environment variables stored securely in Vercel
- API endpoints protected with bearer tokens
- No sensitive data in code repository
- Regular dependency updates recommended

## 📱 Mobile Support

The interface is fully responsive and works great on:
- 📱 Mobile devices
- 📱 Tablets  
- 💻 Desktop computers
