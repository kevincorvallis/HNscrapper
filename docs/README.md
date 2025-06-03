# Hacker News Scraper & AI Comment Curator

A comprehensive Python application that scrapes articles from Hacker News 'best' tab, provides a modern responsive web interface, and includes an intelligent AI-powered comment curator using OpenAI GPT-4.

## Features

### Scraper (`hn_scraper.py`)
- **Multi-page scraping**: Scrapes top N pages (default: 3) from Hacker News 'best' tab
- **Content extraction**: Extracts full article content using requests and BeautifulSoup
- **Deduplication**: SQLite database prevents reprocessing of already scraped URLs
- **Domain filtering**: Automatically extracts and categorizes articles by domain using tldextract
- **Content filtering**: Minimum content length filtering (200+ characters by default)
- **Multiple output formats**: Saves data to both JSON and CSV formats
- **Polite scraping**: Built-in delays between requests
- **Comprehensive CLI**: Full command-line interface with logging levels

### Web Interface (`app.py`)
- **Responsive design**: Mobile-first layout using Tailwind CSS
- **Dark mode**: Toggleable dark/light theme with persistence
- **Real-time search**: Search articles by title and content
- **Advanced filtering**: Filter by domain, content length, and sorting options
- **Interactive UI**: Expandable content views, domain tags
- **Statistics dashboard**: Comprehensive analytics with charts
- **API endpoints**: RESTful API for articles and domains data

### AI Comment Curator (`comment_curator.py`) 🤖
- **OpenAI GPT-4 Integration**: Uses advanced AI to analyze comment quality
- **Insightfulness Scoring**: Rates comments 0-10 on how valuable/enlightening they are
- **Originality Assessment**: Scores 0-10 on uniqueness and creativity of perspective
- **Semantic Categorization**: Auto-tags as Opinion, Question, Correction, Trivia, etc.
- **Intelligent Ranking**: Weighted algorithm combining AI scores with community engagement
- **Web Interface**: Beautiful UI at `/curate` for interactive comment analysis
- **Batch Processing**: Handle large comment datasets with progress tracking
- **Multiple Formats**: Command-line tool, API endpoint, and web interface

## Quick Start

### 1. Setup Environment

```bash
# Clone or download the project
cd HNscrapper

# Create and activate virtual environment
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Scrape Articles

```bash
# Basic scraping (3 pages)
python hn_scraper.py

# Custom options
python hn_scraper.py --pages 5 --json-file my_articles.json

# See all options
python hn_scraper.py --help
```

### 3. Launch Web Interface

```bash
# Start Flask development server
python app.py

# Or using environment variables
FLASK_DEBUG=True python app.py

# Or using gunicorn for production
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Visit `http://localhost:5000` to access the web interface.

## Project Structure

```
HNscrapper/
├── hn_scraper.py              # Main scraper script
├── app.py                     # Flask web application
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── HN.code-workspace         # VSCode workspace configuration
├── README.md                 # This file
├── env/                      # Virtual environment
├── templates/                # HTML templates
│   ├── index.html           # Main articles page
│   ├── stats.html           # Statistics dashboard
│   ├── 404.html             # Error pages
│   └── 500.html
├── static/                   # Static assets (if needed)
├── hn_articles.db           # SQLite database
├── hn_best_articles.json    # Scraped articles (JSON)
└── hn_best_articles.csv     # Scraped articles (CSV)
```

## Configuration

### Environment Variables (.env)
```bash
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_PATH=hn_articles.db
JSON_OUTPUT=hn_best_articles.json
CSV_OUTPUT=hn_best_articles.csv
DEFAULT_PAGES=3
```

### Scraper Options
```bash
python hn_scraper.py [OPTIONS]

Options:
  -p, --pages PAGES             Number of pages to scrape (default: 3)
  -j, --json-file JSON_FILE     Output JSON filename
  -c, --csv-file CSV_FILE       Output CSV filename
  -d, --db-path DB_PATH         SQLite database path
  --no-skip-processed           Don't skip already processed URLs
  -l, --log-level LEVEL         Logging level (DEBUG, INFO, WARNING, ERROR)
```

## Web Interface Features

### Main Articles Page
- **Search**: Full-text search across titles and content
- **Filters**: 
  - Domain filtering (show articles from specific domains)
  - Content length filtering (200+, 500+, 1000+ characters)
  - Sorting options (content length, title, domain)
- **Article Cards**: 
  - Expandable content preview
  - Domain tags
  - Direct links to original articles
  - Content length indicators

### Statistics Dashboard
- **Overview Cards**: Total articles, domains, average content length
- **Content Analytics**: Min/max/average content length statistics
- **Domain Distribution**: Top domains with article counts
- **Interactive Charts**: Visual domain distribution using Chart.js

### Dark Mode
- System-aware dark mode toggle
- Persistent theme preference
- Smooth transitions

## API Endpoints

- `GET /api/articles` - Get filtered articles
  - Query parameters: `search`, `domain`, `min_length`
- `GET /api/domains` - Get list of available domains

## Development

### Using VSCode
Open the `HN.code-workspace` file in VSCode for optimal development experience with:
- Python interpreter auto-detection
- Integrated terminal with virtual environment
- Recommended extensions
- Debugging configuration

### Running Tests
```bash
# Run the scraper with debug logging
python hn_scraper.py --log-level DEBUG --pages 1

# Test the Flask app
FLASK_DEBUG=True python app.py
```

## Production Deployment

### Using Gunicorn
```bash
# Install gunicorn (included in requirements.txt)
pip install gunicorn

# Run with multiple workers
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# With additional options
gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - --error-logfile - app:app
```

### Environment Setup for Production
1. Set `FLASK_ENV=production` in `.env`
2. Set `FLASK_DEBUG=False`
3. Configure proper database path
4. Use reverse proxy (nginx) for static files

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Dependencies

- **Core**: `requests`, `beautifulsoup4`, `pandas`, `tldextract`
- **Web**: `flask`, `gunicorn`, `python-dotenv`
- **Content**: `newspaper3k` (for enhanced content extraction)
- **Storage**: `sqlite3` (built-in)

## Troubleshooting

### Common Issues

1. **No articles displayed**: Run the scraper first with `python hn_scraper.py`
2. **Pillow installation errors**: The scraper works without newspaper3k if needed
3. **Port already in use**: Change port with `PORT=8000 python app.py`
4. **Virtual environment issues**: Ensure you're in the activated virtual environment

### Logs
- Scraper logs: Use `--log-level DEBUG` for detailed output
- Flask logs: Enable with `FLASK_DEBUG=True`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.