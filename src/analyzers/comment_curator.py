#!/usr/bin/env python3
"""
Intelligent Comment Thread Curator using OpenAI API

This script analyzes comment threads from structured JSON data and uses OpenAI's
GPT model to score comments on insightfulness and originality, then re-ranks them
using a custom scoring formula.
"""

import argparse
import json
import logging
import math
import os
import sys
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
import getpass

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CommentCurator:
    """Intelligent comment thread curator using OpenAI API."""
    
    def __init__(self, model: str = "gpt-4-1106-preview"):
        """Initialize the curator with OpenAI client."""
        self.model = model
        self.client = self._setup_openai_client()
        
        # System prompt for GPT
        self.system_prompt = """You are a semantic content curator. Given a short comment thread, return a JSON list where each top-level comment is annotated with:
- 'insightfulness' score from 0–10 (how valuable/enlightening the comment is)
- 'originality' score from 0–10 (how unique/creative the perspective is)
- 'curator_tag': one of ['Opinion', 'Question', 'Correction', 'Trivia', 'Recommendation', 'Contrarian', 'Off-topic']

Return ONLY a valid JSON array with objects containing 'id', 'insightfulness', 'originality', and 'curator_tag' fields. Do not include any other text or explanations."""

    def _setup_openai_client(self) -> OpenAI:
        """Set up OpenAI client with API key from environment or user input."""
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            print("OpenAI API key not found in environment variables.")
            api_key = getpass.getpass("Please enter your OpenAI API key: ")
            
        if not api_key:
            raise ValueError("OpenAI API key is required")
            
        return OpenAI(api_key=api_key)

    def load_comments(self, file_path: str) -> List[Dict]:
        """Load comment threads from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                comments = json.load(f)
                
            logger.info(f"Loaded {len(comments)} comments from {file_path}")
            return comments
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {e}")
            raise

    def organize_comment_threads(self, comments: List[Dict]) -> List[Tuple[Dict, List[Dict]]]:
        """Organize comments into top-level comments with their immediate replies."""
        # Create a mapping of comment IDs to comments
        comment_map = {comment['id']: comment for comment in comments}
        
        # Find top-level comments (depth == 0)
        top_level_comments = [c for c in comments if c.get('depth', 0) == 0]
        
        # For each top-level comment, find its immediate replies (depth == 1)
        threads = []
        for top_comment in top_level_comments:
            replies = [
                c for c in comments 
                if c.get('parent_id') == top_comment['id'] and c.get('depth', 0) == 1
            ]
            threads.append((top_comment, replies))
            
        logger.info(f"Organized {len(threads)} comment threads")
        return threads

    def format_thread_for_gpt(self, top_comment: Dict, replies: List[Dict]) -> str:
        """Format a comment thread for GPT analysis."""
        formatted = f"TOP-LEVEL COMMENT (ID: {top_comment['id']}):\n"
        formatted += f"Score: {top_comment.get('score', 0)}\n"
        formatted += f"Text: {top_comment['text']}\n\n"
        
        if replies:
            formatted += "REPLIES:\n"
            for reply in replies:
                formatted += f"- Reply (ID: {reply['id']}, Score: {reply.get('score', 0)}): {reply['text']}\n"
        else:
            formatted += "No replies.\n"
            
        return formatted

    def analyze_thread_with_gpt(self, top_comment: Dict, replies: List[Dict]) -> Optional[Dict]:
        """Analyze a comment thread using GPT and return curation data."""
        try:
            thread_text = self.format_thread_for_gpt(top_comment, replies)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": thread_text}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse the JSON response
            result_text = response.choices[0].message.content.strip()
            
            # Handle potential markdown code blocks
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            results = json.loads(result_text)
            
            # Find the annotation for the top-level comment
            for result in results:
                if result.get('id') == top_comment['id']:
                    return {
                        'id': top_comment['id'],
                        'insightfulness': result.get('insightfulness', 0),
                        'originality': result.get('originality', 0),
                        'curator_tag': result.get('curator_tag', 'Opinion')
                    }
                    
            logger.warning(f"No analysis found for comment {top_comment['id']}")
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response for comment {top_comment['id']}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error analyzing comment {top_comment['id']}: {e}")
            return None

    def calculate_rank_score(self, comment: Dict, analysis: Dict) -> float:
        """Calculate ranking score using the formula: 
        rank_score = (insightfulness * 2) + (originality * 1.5) + log(score + 1)
        """
        insightfulness = analysis.get('insightfulness', 0)
        originality = analysis.get('originality', 0)
        comment_score = comment.get('score', 0)
        
        rank_score = (insightfulness * 2) + (originality * 1.5) + math.log(comment_score + 1)
        return round(rank_score, 2)

    def curate_comments(self, comments: List[Dict]) -> List[Dict]:
        """Main curation process: analyze and rank all top-level comments."""
        threads = self.organize_comment_threads(comments)
        curated_comments = []
        
        logger.info(f"Starting curation of {len(threads)} threads using {self.model}")
        
        for top_comment, replies in tqdm(threads, desc="Analyzing threads"):
            analysis = self.analyze_thread_with_gpt(top_comment, replies)
            
            if analysis:
                # Create enriched comment data
                curated_comment = {
                    **top_comment,  # Original comment data
                    'insightfulness': analysis['insightfulness'],
                    'originality': analysis['originality'],
                    'curator_tag': analysis['curator_tag'],
                    'rank_score': self.calculate_rank_score(top_comment, analysis)
                }
                curated_comments.append(curated_comment)
            else:
                # Add comment without analysis if GPT failed
                curated_comment = {
                    **top_comment,
                    'insightfulness': 0,
                    'originality': 0,
                    'curator_tag': 'Opinion',
                    'rank_score': self.calculate_rank_score(top_comment, {'insightfulness': 0, 'originality': 0})
                }
                curated_comments.append(curated_comment)
        
        # Sort by rank score (highest first)
        curated_comments.sort(key=lambda x: x['rank_score'], reverse=True)
        
        logger.info(f"Successfully curated {len(curated_comments)} comments")
        return curated_comments

    def save_results(self, curated_comments: List[Dict], output_file: str, top_n: Optional[int] = None):
        """Save curated and ranked comments to JSON file."""
        if top_n:
            curated_comments = curated_comments[:top_n]
            logger.info(f"Filtering to top {top_n} comments")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(curated_comments, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved {len(curated_comments)} curated comments to {output_file}")
            
            # Print summary statistics
            self.print_summary(curated_comments)
            
        except Exception as e:
            logger.error(f"Error saving results to {output_file}: {e}")
            raise

    def print_summary(self, curated_comments: List[Dict]):
        """Print summary statistics of the curation results."""
        if not curated_comments:
            return
            
        print("\n" + "="*60)
        print("CURATION SUMMARY")
        print("="*60)
        
        # Overall stats
        avg_insightfulness = sum(c['insightfulness'] for c in curated_comments) / len(curated_comments)
        avg_originality = sum(c['originality'] for c in curated_comments) / len(curated_comments)
        avg_rank_score = sum(c['rank_score'] for c in curated_comments) / len(curated_comments)
        
        print(f"Total comments curated: {len(curated_comments)}")
        print(f"Average insightfulness: {avg_insightfulness:.2f}")
        print(f"Average originality: {avg_originality:.2f}")
        print(f"Average rank score: {avg_rank_score:.2f}")
        
        # Tag distribution
        tag_counts = {}
        for comment in curated_comments:
            tag = comment['curator_tag']
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
        print("\nTag distribution:")
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(curated_comments)) * 100
            print(f"  {tag}: {count} ({percentage:.1f}%)")
        
        # Top 5 comments
        print(f"\nTop 5 ranked comments:")
        for i, comment in enumerate(curated_comments[:5], 1):
            print(f"{i}. [Score: {comment['rank_score']:.2f}] "
                  f"[{comment['curator_tag']}] "
                  f"{comment['text'][:100]}...")


def create_sample_comments(output_file: str):
    """Create a sample comments JSON file for testing."""
    sample_comments = [
        {
            "id": "comment_1",
            "parent_id": None,
            "text": "This is a really insightful analysis of the current market trends. The author makes excellent points about the economic implications.",
            "score": 45,
            "depth": 0
        },
        {
            "id": "comment_2", 
            "parent_id": "comment_1",
            "text": "I agree completely. The data supports this conclusion.",
            "score": 12,
            "depth": 1
        },
        {
            "id": "comment_3",
            "parent_id": None,
            "text": "What are the potential downsides of this approach? Has anyone considered the environmental impact?",
            "score": 32,
            "depth": 0
        },
        {
            "id": "comment_4",
            "parent_id": "comment_3",
            "text": "Good question! The environmental impact is indeed significant. Studies show...",
            "score": 18,
            "depth": 1
        },
        {
            "id": "comment_5",
            "parent_id": None,
            "text": "This reminds me of my cat. Completely off-topic but thought I'd share.",
            "score": 2,
            "depth": 0
        },
        {
            "id": "comment_6",
            "parent_id": None,
            "text": "Actually, the author got this wrong. The correct interpretation is different based on recent research from MIT.",
            "score": 67,
            "depth": 0
        },
        {
            "id": "comment_7",
            "parent_id": "comment_6",
            "text": "Do you have a link to that research?",
            "score": 8,
            "depth": 1
        },
        {
            "id": "comment_8",
            "parent_id": None,
            "text": "I highly recommend checking out the book 'Deep Work' if you're interested in this topic. It covers similar themes.",
            "score": 23,
            "depth": 0
        }
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_comments, f, indent=2)
    
    print(f"Created sample comments file: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Curate comment threads using OpenAI API")
    parser.add_argument("--input_file", "-i", 
                       default="sample_comments.json",
                       help="Input JSON file containing comment threads")
    parser.add_argument("--output_file", "-o", 
                       default="curated_comments.json",
                       help="Output JSON file for curated comments")
    parser.add_argument("--model", "-m",
                       default="gpt-4-1106-preview",
                       help="OpenAI model to use (default: gpt-4-1106-preview)")
    parser.add_argument("--top_n", "-n",
                       type=int,
                       help="Export only top N ranked comments")
    parser.add_argument("--create_sample", "-s",
                       action="store_true",
                       help="Create a sample comments file for testing")
    
    args = parser.parse_args()
    
    # Create sample file if requested
    if args.create_sample:
        create_sample_comments(args.input_file)
        print(f"Sample file created. Run without --create_sample to process it.")
        return
    
    try:
        # Initialize curator
        curator = CommentCurator(model=args.model)
        
        # Load comments
        comments = curator.load_comments(args.input_file)
        
        if not comments:
            logger.error("No comments found in input file")
            return
        
        # Curate comments
        curated_comments = curator.curate_comments(comments)
        
        # Save results
        curator.save_results(curated_comments, args.output_file, args.top_n)
        
        print(f"\n✅ Curation complete! Results saved to: {args.output_file}")
        
    except KeyboardInterrupt:
        logger.info("Curation interrupted by user")
    except Exception as e:
        logger.error(f"Error during curation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
