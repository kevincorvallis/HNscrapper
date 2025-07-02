#!/usr/bin/env python3
"""
Enhanced Hacker News Scraper with Complete Comment Thread Support

Scrapes articles from Hacker News 'best' tab AND captures complete comment threads
with hierarchical structure, including all nested replies and metadata.
"""

import argparse
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime, timezone

import pandas as pd
import requests
import tldextract
from bs4 import BeautifulSoup


class EnhancedHackerNewsScraper:
    """Enhanced scraper that captures both articles and complete comment threads."""
    
    def __init__(self, db_path: str = "enhanced_hn_articles.db"):
        self.base_url = "https://news.ycombinator.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; Enhanced-HN-Scraper/2.0)'
        })
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
    def setup_database(self) -> None:
        """Initialize SQLite database with historical vote tracking."""
        with sqlite3.connect(self.db_path) as conn:
            # Articles table (current state)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_articles (
                    url TEXT PRIMARY KEY,
                    hn_id TEXT UNIQUE,
                    title TEXT,
                    domain TEXT,
                    author TEXT,
                    content_length INTEGER,
                    comment_count INTEGER DEFAULT 0,
                    score INTEGER DEFAULT 0,
                    rank INTEGER,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Historical tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS article_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hn_id TEXT,
                    url TEXT,
                    score INTEGER,
                    comment_count INTEGER,
                    rank INTEGER,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (hn_id) REFERENCES processed_articles (hn_id)
                )
            """)
            
            # Comments table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_comments (
                    comment_id TEXT PRIMARY KEY,
                    article_url TEXT,
                    parent_id TEXT,
                    level INTEGER,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_url) REFERENCES processed_articles (url)
                )
            """)
            
            # Create indexes for better performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_article_history_hn_id 
                ON article_history(hn_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_article_history_scraped_at 
                ON article_history(scraped_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_articles_hn_id 
                ON processed_articles(hn_id)
            """)
            
            conn.commit()
    
    def is_url_processed(self, url: str) -> bool:
        """Check if URL has been processed before."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM processed_articles WHERE url = ?", (url,)
            )
            return cursor.fetchone() is not None

    def update_article_metrics(self, hn_id: str, url: str, title: str, 
                              domain: str, author: str, content_length: int, 
                              comment_count: int, score: int, 
                              rank: int = None) -> None:
        """Update article metrics and store historical data."""
        with sqlite3.connect(self.db_path) as conn:
            # Insert or update main article record
            conn.execute("""
                INSERT OR REPLACE INTO processed_articles 
                (url, hn_id, title, domain, author, content_length, 
                 comment_count, score, rank, first_seen, last_updated) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 
                        COALESCE((SELECT first_seen FROM processed_articles 
                                 WHERE hn_id = ?), CURRENT_TIMESTAMP),
                        CURRENT_TIMESTAMP)
            """, (url, hn_id, title, domain, author, content_length, 
                  comment_count, score, rank, hn_id))
            
            # Store historical snapshot
            conn.execute("""
                INSERT INTO article_history 
                (hn_id, url, score, comment_count, rank) 
                VALUES (?, ?, ?, ?, ?)
            """, (hn_id, url, score, comment_count, rank))
            
            conn.commit()

    def mark_url_processed(self, url: str, title: str, domain: str, 
                          content_length: int, comment_count: int = 0) -> None:
        """Legacy method - use update_article_metrics instead."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO processed_articles
                (url, title, domain, content_length, comment_count) 
                VALUES (?, ?, ?, ?, ?)
            """, (url, title, domain, content_length, comment_count))
            conn.commit()
    
    def get_article_links_and_discussions(self, pages: int = 3) -> List[Dict[str, Union[str, int]]]:
        """
        Extract both article links and HN discussion threads from 'best' pages.
        
        Args:
            pages: Number of pages to scrape (default: 3)
            
        Returns:
            List of dictionaries containing title, url, domain, hn_id, and comments_url
        """
        all_items = []
        seen_urls = set()
        
        for page in range(1, pages + 1):
            self.logger.info(f"Scraping page {page}/{pages}")
            url = f"{self.base_url}/best?p={page}"
            
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Find all story items
                story_items = soup.find_all("tr", class_="athing")
                
                for item in story_items:
                    item_data = self._extract_item_data(item, soup)
                    if not item_data:
                        continue
                    
                    # Resolve redirects for external URLs
                    if item_data['url'] and not item_data['url'].startswith('item?id='):
                        try:
                            resolved_url = self._resolve_final_url(item_data['url'])
                            item_data['url'] = resolved_url
                        except Exception as e:
                            self.logger.warning(f"Failed to resolve URL {item_data['url']}: {e}")
                    
                    # Deduplicate based on URL or HN ID
                    dedup_key = item_data['url'] if item_data['url'] else item_data['hn_id']
                    if dedup_key in seen_urls:
                        self.logger.debug(f"Duplicate item skipped: {dedup_key}")
                        continue
                    
                    seen_urls.add(dedup_key)
                    all_items.append(item_data)
                
                # Small delay between page requests
                time.sleep(0.5)
                
            except requests.RequestException as e:
                self.logger.error(f"Failed to fetch page {page}: {e}")
                continue
        
        self.logger.info(f"Found {len(all_items)} unique items across {pages} pages")
        return all_items
    
    def _extract_item_data(self, item, soup) -> Optional[Dict[str, Union[str, int]]]:
        """Extract data from a single HN item (story) including score and author."""
        # Get HN item ID
        hn_id = item.get('id')
        if not hn_id:
            return None
        
        # Look for the title link inside titleline span
        titleline = item.find("span", class_="titleline")
        if not titleline:
            return None
        
        title_tag = titleline.find("a")
        if not title_tag:
            return None
        
        title = title_tag.get_text(strip=True)
        article_url = title_tag.get('href', '')
        
        # Find the corresponding metadata row (next sibling)
        meta_row = item.find_next_sibling("tr")
        if not meta_row:
            return None
        
        # Extract score/points
        score = 0
        score_elem = meta_row.find("span", class_="score")
        if score_elem:
            score_text = score_elem.get_text()
            score_match = re.search(r'(\d+)', score_text)
            if score_match:
                score = int(score_match.group(1))
        
        # Extract author
        author = None
        author_link = meta_row.find("a", class_="hnuser")
        if author_link:
            author = author_link.get_text(strip=True)
        
        # Extract comment count
        comment_count = 0
        comments_link = meta_row.find("a", string=re.compile(r"\d+\s+comment"))
        if comments_link:
            comment_text = comments_link.get_text()
            comment_match = re.search(r'(\d+)', comment_text)
            if comment_match:
                comment_count = int(comment_match.group(1))
        
        # Extract rank (position on the page)
        rank_elem = item.find("span", class_="rank")
        rank = None
        if rank_elem:
            rank_text = rank_elem.get_text()
            rank_match = re.search(r'(\d+)', rank_text)
            if rank_match:
                rank = int(rank_match.group(1))
        
        # Create HN discussion URL
        comments_url = f"{self.base_url}/item?id={hn_id}"
        
        # Handle different types of links
        if article_url.startswith('item?id='):
            # HN-only discussion thread
            return {
                'title': title,
                'url': None,  # No external URL
                'domain': 'news.ycombinator.com',
                'hn_id': hn_id,
                'comments_url': comments_url,
                'comment_count': comment_count,
                'score': score,
                'author': author,
                'rank': rank,
                'type': 'discussion'
            }
        elif not article_url.startswith(('http://', 'https://')):
            # Relative URL - make it absolute
            article_url = urljoin(self.base_url, article_url)
        
        # Extract domain for external articles
        if article_url:
            extracted = tldextract.extract(article_url)
            domain = f"{extracted.domain}.{extracted.suffix}"
        else:
            domain = 'news.ycombinator.com'
        
        return {
            'title': title,
            'url': article_url,
            'domain': domain,
            'hn_id': hn_id,
            'comments_url': comments_url,
            'comment_count': comment_count,
            'score': score,
            'author': author,
            'rank': rank,
            'type': 'article'
        }
    
    def _resolve_final_url(self, url: str) -> str:
        """Resolve redirects to get the final URL."""
        try:
            response = self.session.head(url, timeout=10, allow_redirects=True)
            return response.url
        except Exception:
            # If HEAD fails, try GET with a small range
            try:
                response = self.session.get(
                    url, timeout=10, allow_redirects=True,
                    headers={'Range': 'bytes=0-1023'}
                )
                return response.url
            except Exception:
                return url
    
    def extract_article_content(self, url: str, title: str) -> Optional[str]:
        """
        Extract article content using requests and BeautifulSoup.
        
        Args:
            url: Article URL
            title: Article title for logging
            
        Returns:
            Article content or None if extraction fails
        """
        if not url:
            return None
            
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Try to find the main content using common patterns
            content_selectors = [
                'article',
                '[role="main"]',
                '.post-content',
                '.entry-content', 
                '.article-content',
                '.content',
                '.post-body',
                '.story-body',
                'main',
                '.main-content'
            ]
            
            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break
            
            # Fallback to body if no specific content area found
            if not content_element:
                content_element = soup.find('body')
                if not content_element:
                    return None
            
            # Extract text content
            content = content_element.get_text(separator=' ', strip=True)
            
            # Basic content filtering
            if len(content) < 100:
                self.logger.warning(f"Content too short for '{title}': {len(content)} chars")
                return None
            
            # Remove excessive whitespace
            content = re.sub(r'\s+', ' ', content)
            
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to extract content from '{title}' ({url}): {e}")
            return None
    
    def extract_complete_comment_thread(self, comments_url: str, hn_id: str) -> List[Dict]:
        """
        Extract complete comment thread with hierarchical structure.
        
        Args:
            comments_url: URL to HN discussion page
            hn_id: HN item ID
            
        Returns:
            List of comment dictionaries with hierarchical structure
        """
        try:
            response = self.session.get(comments_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            comments = []
            
            # Find all comment elements
            comment_elements = soup.find_all("tr", class_="athing comtr")
            
            for comment_elem in comment_elements:
                comment_data = self._parse_comment(comment_elem)
                if comment_data:
                    comments.append(comment_data)
            
            # Build hierarchical structure
            threaded_comments = self._build_comment_hierarchy(comments)
            
            self.logger.info(f"Extracted {len(comments)} comments from {comments_url}")
            return threaded_comments
            
        except Exception as e:
            self.logger.error(f"Failed to extract comments from {comments_url}: {e}")
            return []
    
    def _parse_comment(self, comment_elem) -> Optional[Dict]:
        """Parse a single comment element from HN HTML."""
        try:
            # Get comment ID
            comment_id = comment_elem.get('id')
            if not comment_id:
                return None
            
            # Get indentation level (determines hierarchy)
            indent_elem = comment_elem.find("td", class_="ind")
            indent_level = 0
            if indent_elem:
                indent_attr = indent_elem.get('indent')
                if indent_attr:
                    indent_level = int(indent_attr)
            
            # Find the table containing comment data
            table = comment_elem.find("table")
            if not table:
                return None
            
            # Extract author
            author_link = table.find("a", class_="hnuser")
            author = author_link.get_text(strip=True) if author_link else "unknown"
            
            # Extract timestamp
            age_elem = table.find("span", class_="age")
            timestamp = None
            if age_elem:
                title_attr = age_elem.get('title')
                if title_attr:
                    try:
                        # Parse ISO format timestamp
                        timestamp = datetime.fromisoformat(title_attr.replace('Z', '+00:00'))
                    except:
                        pass
            
            # Extract comment text
            comment_div = table.find("div", class_="commtext")
            comment_text = ""
            if comment_div:
                # Convert HTML to plain text while preserving some structure
                comment_text = self._html_to_text(comment_div)
            
            # Check if comment is collapsed/dead
            is_dead = "dead" in comment_elem.get("class", [])
            
            # Extract parent relationship from navigation links
            parent_id = None
            parent_link = table.find("a", string="parent")
            if parent_link and indent_level > 0:
                # For nested comments, we'll determine parent during hierarchy building
                pass
            
            return {
                'id': comment_id,
                'author': author,
                'text': comment_text,
                'timestamp': timestamp.isoformat() if timestamp else None,
                'level': indent_level,
                'is_dead': is_dead,
                'parent_id': parent_id,
                'replies': []  # Will be populated during hierarchy building
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to parse comment: {e}")
            return None
    
    def _html_to_text(self, element) -> str:
        """Convert HTML comment content to clean text."""
        # Replace <p> tags with newlines
        for p in element.find_all('p'):
            p.insert_before('\n\n')
        
        # Replace <br> tags with newlines
        for br in element.find_all('br'):
            br.replace_with('\n')
        
        # Get text and clean it up
        text = element.get_text()
        
        # Clean up excessive whitespace while preserving paragraph breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = text.strip()
        
        return text
    
    def _build_comment_hierarchy(self, comments: List[Dict]) -> List[Dict]:
        """Build hierarchical comment structure from flat list."""
        if not comments:
            return []
        
        # Sort by level to ensure parents come before children
        comments.sort(key=lambda x: x['level'])
        
        # Create lookup by ID
        comment_lookup = {c['id']: c for c in comments}
        root_comments = []
        parent_stack = []  # Stack to track parent at each level
        
        for comment in comments:
            level = comment['level']
            
            # Adjust parent stack to current level
            while len(parent_stack) > level:
                parent_stack.pop()
            
            if level == 0:
                # Root level comment
                root_comments.append(comment)
                parent_stack = [comment]
            else:
                # Nested comment - find parent
                if parent_stack:
                    parent = parent_stack[-1]
                    comment['parent_id'] = parent['id']
                    parent['replies'].append(comment)
                    parent_stack.append(comment)
                else:
                    # Orphaned comment - treat as root
                    root_comments.append(comment)
                    parent_stack = [comment]
        
        return root_comments
    
    def scrape_articles_with_comments(self, pages: int = 3, max_articles: int = None, 
                                      skip_processed: bool = False) -> List[Dict]:
        """
        Main method to scrape articles with complete comment threads and vote tracking.
        
        Args:
            pages: Number of HN pages to scrape
            max_articles: Maximum number of articles to process (None for all)
            skip_processed: Whether to skip already processed URLs (default: False for updates)
            
        Returns:
            List of article dictionaries with complete comment data
        """
        self.setup_database()
        
        # Get all items (articles and discussions)
        items = self.get_article_links_and_discussions(pages)
        
        if max_articles:
            items = items[:max_articles]
        
        processed_articles = []
        
        for i, item in enumerate(items, 1):
            self.logger.info(f"Processing item {i}/{len(items)}: {item['title']} (Score: {item.get('score', 0)})")
            
            # Check if already processed (but don't skip for updates)
            is_existing = item['url'] and self.is_url_processed(item['url'])
            if skip_processed and is_existing:
                self.logger.info(f"Skipping already processed URL: {item['url']}")
                continue
            elif is_existing:
                self.logger.info(f"Updating existing article: {item['title']}")
            
            article_data = {
                'title': item['title'],
                'url': item['url'],
                'domain': item['domain'],
                'hn_id': item['hn_id'],
                'comments_url': item['comments_url'],
                'comment_count': item['comment_count'],
                'score': item.get('score', 0),
                'author': item.get('author'),
                'rank': item.get('rank'),
                'type': item['type'],
                'content': None,
                'comments': []
            }
            
            # Extract article content (if external URL and not existing)
            if item['url'] and not is_existing:
                content = self.extract_article_content(item['url'], item['title'])
                article_data['content'] = content
            
            # Extract complete comment thread (always update for latest comments)
            if item['comment_count'] > 0:
                comments = self.extract_complete_comment_thread(
                    item['comments_url'], 
                    item['hn_id']
                )
                article_data['comments'] = comments
                
                # Update actual comment count
                actual_count = self._count_total_comments(comments)
                article_data['actual_comment_count'] = actual_count
                
                self.logger.info(f"Captured {actual_count} comments (HN reported {item['comment_count']})")
            
            processed_articles.append(article_data)
            
            # Update article metrics with historical tracking
            content_length = len(article_data['content']) if article_data['content'] else 0
            actual_comment_count = article_data.get('actual_comment_count', 0)
            
            self.update_article_metrics(
                hn_id=item['hn_id'],
                url=item['url'] or item['comments_url'],
                title=item['title'],
                domain=item['domain'],
                author=item.get('author', ''),
                content_length=content_length,
                comment_count=actual_comment_count,
                score=item.get('score', 0),
                rank=item.get('rank')
            )
            
            # Rate limiting
            time.sleep(1)
        
        return processed_articles
    
    def _count_total_comments(self, comments: List[Dict]) -> int:
        """Recursively count total comments including replies."""
        total = 0
        for comment in comments:
            total += 1  # Count this comment
            total += self._count_total_comments(comment.get('replies', []))  # Count replies
        return total
    
    def save_to_json(self, articles: List[Dict], filename: str) -> None:
        """Save articles with comments to JSON file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False, default=str)
            self.logger.info(f"Saved {len(articles)} articles to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save to JSON: {e}")
    
    def save_to_csv(self, articles: List[Dict], filename: str) -> None:
        """Save articles (without nested comments) to CSV file with vote tracking."""
        try:
            # Flatten data for CSV (comments will be summarized)
            flattened_data = []
            for article in articles:
                row = {
                    'title': article['title'],
                    'url': article['url'],
                    'domain': article['domain'],
                    'hn_id': article['hn_id'],
                    'comments_url': article['comments_url'],
                    'type': article['type'],
                    'score': article.get('score', 0),
                    'author': article.get('author', ''),
                    'rank': article.get('rank'),
                    'content_length': len(article['content']) if article['content'] else 0,
                    'reported_comment_count': article['comment_count'],
                    'actual_comment_count': article.get('actual_comment_count', 0),
                    'has_content': bool(article['content']),
                    'has_comments': bool(article['comments'])
                }
                flattened_data.append(row)
            
            df = pd.DataFrame(flattened_data)
            df.to_csv(filename, index=False, encoding='utf-8')
            self.logger.info(f"Saved {len(articles)} articles to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save to CSV: {e}")
    
    def get_article_history(self, hn_id: str) -> List[Dict]:
        """Get historical vote/comment data for an article."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT score, comment_count, rank, scraped_at 
                FROM article_history 
                WHERE hn_id = ? 
                ORDER BY scraped_at
            """, (hn_id,))
            
            columns = ['score', 'comment_count', 'rank', 'scraped_at']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_trending_articles(self, hours: int = 24) -> List[Dict]:
        """Get articles with biggest score increases in the last N hours."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                WITH latest_scores AS (
                    SELECT hn_id, score, comment_count, 
                           ROW_NUMBER() OVER (PARTITION BY hn_id ORDER BY scraped_at DESC) as rn
                    FROM article_history 
                    WHERE scraped_at >= datetime('now', '-{} hours')
                ),
                earliest_scores AS (
                    SELECT hn_id, score as initial_score, comment_count as initial_comments,
                           ROW_NUMBER() OVER (PARTITION BY hn_id ORDER BY scraped_at ASC) as rn
                    FROM article_history 
                    WHERE scraped_at >= datetime('now', '-{} hours')
                )
                SELECT p.title, p.url, p.hn_id, p.domain, p.author,
                       l.score as current_score, e.initial_score,
                       (l.score - e.initial_score) as score_increase,
                       l.comment_count, e.initial_comments,
                       (l.comment_count - e.initial_comments) as comment_increase
                FROM latest_scores l
                JOIN earliest_scores e ON l.hn_id = e.hn_id AND l.rn = 1 AND e.rn = 1
                JOIN processed_articles p ON l.hn_id = p.hn_id
                WHERE (l.score - e.initial_score) > 0
                ORDER BY score_increase DESC
                LIMIT 20
            """.format(hours, hours))
            
            columns = ['title', 'url', 'hn_id', 'domain', 'author', 
                      'current_score', 'initial_score', 'score_increase',
                      'comment_count', 'initial_comments', 'comment_increase']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # ...existing code...
def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description='Enhanced Hacker News Scraper with Comments')
    parser.add_argument('--pages', type=int, default=3, help='Number of pages to scrape (default: 3)')
    parser.add_argument('--max-articles', type=int, help='Maximum number of articles to process')
    parser.add_argument('--output-json', default='enhanced_hn_articles.json', help='JSON output filename')
    parser.add_argument('--output-csv', default='enhanced_hn_articles.csv', help='CSV output filename')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--skip-processed', action='store_true', default=False,
                       help='Skip already processed URLs (default: False, enables vote tracking)')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('hn_scraper.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting enhanced HN scraper with comment support")
    
    # Create scraper and run
    scraper = EnhancedHackerNewsScraper()
    
    try:
        articles = scraper.scrape_articles_with_comments(
            pages=args.pages,
            max_articles=args.max_articles,
            skip_processed=args.skip_processed
        )
        
        if articles:
            # Save results
            scraper.save_to_json(articles, args.output_json)
            scraper.save_to_csv(articles, args.output_csv)
            
            # Print summary
            total_comments = sum(article.get('actual_comment_count', 0) for article in articles)
            logger.info(f"Summary: {len(articles)} articles, {total_comments} total comments")
        else:
            logger.warning("No articles were processed")
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise


if __name__ == "__main__":
    main()