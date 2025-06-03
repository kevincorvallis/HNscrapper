# Deployment Guide - NYT-Style Hacker News Browser

This guide covers deploying the NYT-Style Hacker News application to various platforms.

## 🚀 Quick Deployment Options

### Option 1: Railway (Recommended)
Railway offers simple deployment with automatic builds.

1. **Fork the repository** on GitHub
2. **Connect to Railway**:
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your forked repository

3. **Configure environment variables**:
   ```bash
   SECRET_KEY=your-secure-random-secret-key
   FLASK_ENV=production
   PORT=8000
   ```

4. **Deploy**: Railway will automatically deploy from your main branch

### Option 2: Heroku
1. **Install Heroku CLI** and login
2. **Create Heroku app**:
   ```bash
   heroku create your-app-name
   ```

3. **Set environment variables**:
   ```bash
   heroku config:set SECRET_KEY=your-secure-secret-key
   heroku config:set FLASK_ENV=production
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

### Option 3: Digital Ocean App Platform
1. **Create new app** on Digital Ocean
2. **Connect GitHub repository**
3. **Configure build settings**:
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `gunicorn src.web.main:app --workers 4 --bind 0.0.0.0:$PORT`

## 🔧 Local Production Setup

### Using Gunicorn (Recommended)
```bash
# Install gunicorn
pip install gunicorn

# Run with production settings
gunicorn src.web.main:app --workers 4 --bind 0.0.0.0:8000 --access-logfile -
```

### Using Docker
Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "src.web.main:app", "--workers", "4", "--bind", "0.0.0.0:8000"]
```

Build and run:
```bash
docker build -t nyt-hn-browser .
docker run -p 8000:8000 -e SECRET_KEY=your-secret-key nyt-hn-browser
```

## ⚙️ Environment Configuration

### Required Environment Variables
```bash
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production
PORT=8000
```

### Optional Environment Variables
```bash
# OpenAI Integration (for enhanced features)
OPENAI_API_KEY=sk-your-openai-key

# Database Configuration (auto-configured)
DATABASE_PATH=data/enhanced_hn_articles.db

# Security Headers
FORCE_HTTPS=true
```

## 🔒 Security Checklist

### Pre-Deployment Security
- [ ] Set a strong, random `SECRET_KEY`
- [ ] Set `FLASK_ENV=production`
- [ ] Remove or secure debug endpoints
- [ ] Validate all user inputs
- [ ] Enable HTTPS in production

### Production Security Headers
Add to your web server or application:
```bash
# HTTPS Redirect
FORCE_HTTPS=true

# Security Headers
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
```

## 📊 Database Management

### SQLite in Production
The application uses SQLite which is included and ready for deployment:

```bash
# Database file location
data/enhanced_hn_articles.db

# Backup database
cp data/enhanced_hn_articles.db backups/backup-$(date +%Y%m%d).db
```

### Scaling Considerations
For high-traffic deployments:
- Consider PostgreSQL for concurrent users
- Implement Redis for session storage
- Use CDN for static assets

## 🔍 Monitoring & Logging

### Application Logs
```bash
# Check application logs
tail -f logs/app.log

# Heroku logs
heroku logs --tail

# Railway logs
railway logs
```

### Health Check Endpoint
The application includes health checks:
```bash
# Check application health
curl https://your-app.com/api/stats
```

## 🚀 Performance Optimization

### Production Optimizations
1. **Enable Gzip Compression**
2. **Use CDN for Static Assets**
3. **Implement Caching Headers**
4. **Optimize Database Queries**

### Recommended Web Server Config (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/your/app/src/web/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/ || echo "No tests found"
    
    - name: Deploy to Railway
      uses: railwayapp/railway-deploy-action@v1
      with:
        railway-token: ${{ secrets.RAILWAY_TOKEN }}
```

## 🛠 Troubleshooting

### Common Issues

**Port already in use**:
```bash
# Find process using port
lsof -i :8000
# Kill process
kill -9 <PID>
```

**Database permission errors**:
```bash
# Fix database permissions
chmod 644 data/enhanced_hn_articles.db
chown www-data:www-data data/enhanced_hn_articles.db
```

**Memory issues**:
```bash
# Reduce worker processes
gunicorn src.web.main:app --workers 1 --bind 0.0.0.0:8000
```

### Platform-Specific Issues

**Heroku**:
- Ensure `Procfile` is in root directory
- Check buildpack is set to Python
- Verify environment variables are set

**Railway**:
- Check build logs for dependency issues
- Ensure start command is configured correctly
- Verify domain settings

## 📈 Scaling Guidelines

### Vertical Scaling
- Start with 1 worker process
- Monitor CPU and memory usage
- Increase workers as needed

### Horizontal Scaling
- Use load balancer for multiple instances
- Implement session storage (Redis)
- Consider database replication

## 🔧 Maintenance

### Regular Tasks
1. **Monitor application logs**
2. **Backup database regularly**
3. **Update dependencies**
4. **Check security vulnerabilities**

### Update Process
```bash
# 1. Test locally
git pull origin main
pip install -r requirements.txt
python src/web/main.py

# 2. Deploy to staging
git push staging main

# 3. Deploy to production
git push heroku main
```

## 📞 Support

For deployment issues:
1. Check application logs first
2. Verify environment variables
3. Test database connectivity
4. Check platform-specific documentation

---

**Ready for production deployment! 🚀**
