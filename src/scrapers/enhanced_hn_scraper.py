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
        """Initialize SQLite database for URL and comment tracking."""
        with sqlite3.connect(self.db_path) as conn:
            # Articles table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_articles (
                    url TEXT PRIMARY KEY,
                    title TEXT,
                    domain TEXT,
                    content_length INTEGER,
                    comment_count INTEGER DEFAULT 0,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            conn.commit()
    
    def is_url_processed(self, url: str) -> bool:
        """Check if URL has been processed before."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM processed_articles WHERE url = ?", (url,))
            return cursor.fetchone() is not None
    
    def mark_url_processed(self, url: str, title: str, domain: str, content_length: int, comment_count: int = 0) -> None:
        """Mark URL as processed in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO processed_articles 
                (url, title, domain, content_length, comment_count) VALUES (?, ?, ?, ?, ?)
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
        """Extract data from a single HN item (story)."""
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
        
        # Extract comment count and other metadata
        comment_count = 0
        comments_link = meta_row.find("a", string=re.compile(r"\d+\s+comment"))
        if comments_link:
            comment_text = comments_link.get_text()
            comment_match = re.search(r'(\d+)', comment_text)
            if comment_match:
                comment_count = int(comment_match.group(1))
        
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
                                      skip_processed: bool = True) -> List[Dict]:
        """
        Main method to scrape articles with complete comment threads.
        
        Args:
            pages: Number of HN pages to scrape
            max_articles: Maximum number of articles to process (None for all)
            skip_processed: Whether to skip already processed URLs
            
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
            self.logger.info(f"Processing item {i}/{len(items)}: {item['title']}")
            
            # Skip if already processed
            if skip_processed and item['url'] and self.is_url_processed(item['url']):
                self.logger.info(f"Skipping already processed URL: {item['url']}")
                continue
            
            article_data = {
                'title': item['title'],
                'url': item['url'],
                'domain': item['domain'],
                'hn_id': item['hn_id'],
                'comments_url': item['comments_url'],
                'comment_count': item['comment_count'],
                'type': item['type'],
                'content': None,
                'comments': []
            }
            
            # Extract article content (if external URL)
            if item['url']:
                content = self.extract_article_content(item['url'], item['title'])
                article_data['content'] = content
            
            # Extract complete comment thread
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
            
            # Mark as processed
            content_length = len(article_data['content']) if article_data['content'] else 0
            actual_comment_count = article_data.get('actual_comment_count', 0)
            
            self.mark_url_processed(
                item['url'] or item['comments_url'],
                item['title'],
                item['domain'],
                content_length,
                actual_comment_count
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
        """Save articles (without nested comments) to CSV file."""
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


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description='Enhanced Hacker News Scraper with Comments')
    parser.add_argument('--pages', type=int, default=3, help='Number of pages to scrape (default: 3)')
    parser.add_argument('--max-articles', type=int, help='Maximum number of articles to process')
    parser.add_argument('--output-json', default='enhanced_hn_articles.json', help='JSON output filename')
    parser.add_argument('--output-csv', default='enhanced_hn_articles.csv', help='CSV output filename')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--skip-processed', action='store_true', default=True, 
                       help='Skip already processed URLs (default: True)')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('enhanced_hn_scraper.log'),
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