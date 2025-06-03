"""
Enhanced Daily HN Scraper

This module provides a comprehensive daily scraper for Hacker News.
"""

import asyncio
import sqlite3
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import re
import hashlib
from pathlib import Path

# Environment variables
import os
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ScrapingConfig:
    """Configuration for the daily scraper"""
    max_articles: int = 100
    max_comments_per_article: int = 500
    rate_limit_delay: float = 1.0
    request_timeout: int = 30
    max_retries: int = 3
    enable_ai_analysis: bool = False
    enable_content_extraction: bool = True
    min_score_threshold: int = 10
    batch_size: int = 10
    
    @classmethod
    def from_env(cls) -> 'ScrapingConfig':
        """Create config from environment variables"""
        return cls(
            max_articles=int(os.getenv('SCRAPER_MAX_ARTICLES', 100)),
            max_comments_per_article=int(os.getenv('SCRAPER_MAX_COMMENTS', 500)),
            rate_limit_delay=float(os.getenv('SCRAPER_RATE_LIMIT', 1.0)),
            request_timeout=int(os.getenv('SCRAPER_TIMEOUT', 30)),
            max_retries=int(os.getenv('SCRAPER_MAX_RETRIES', 3)),
            enable_ai_analysis=os.getenv('ENABLE_AI_ANALYSIS', 'false').lower() == 'true',
            enable_content_extraction=os.getenv('ENABLE_CONTENT_EXTRACTION', 'true').lower() == 'true',
            min_score_threshold=int(os.getenv('SCRAPER_MIN_SCORE', 10)),
            batch_size=int(os.getenv('SCRAPER_BATCH_SIZE', 10))
        )

print("Daily scraper file created successfully!")
