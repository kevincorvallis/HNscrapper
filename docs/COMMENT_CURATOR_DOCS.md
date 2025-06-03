# Comment Curator Documentation

## Overview

The Comment Curator is an intelligent content analysis tool that uses OpenAI's GPT models to evaluate and rank comment threads based on insightfulness, originality, and semantic categorization.

## Features

- **AI-Powered Analysis**: Uses OpenAI GPT models to score comments on insightfulness (0-10) and originality (0-10)
- **Semantic Categorization**: Automatically tags comments as Opinion, Question, Correction, Trivia, Recommendation, Contrarian, or Off-topic
- **Intelligent Ranking**: Combines AI scores with existing comment scores using a weighted formula
- **Progress Tracking**: Real-time progress bars using tqdm
- **Flexible Output**: Export all results or top-N ranked comments
- **Sample Data Generation**: Built-in sample data creation for testing

## Installation

```bash
# Install dependencies
pip install openai python-dotenv tqdm

# Set up OpenAI API key in .env file
echo "OPENAI_API_KEY=your_api_key_here" >> .env
```

## Usage

### Basic Usage

```bash
# Create sample data
python comment_curator.py --create_sample

# Analyze the sample data
python comment_curator.py --input_file sample_comments.json --output_file results.json

# Get only top 10 results
python comment_curator.py -i comments.json -o top10.json --top_n 10
```

### Command Line Options

```
--input_file, -i     Input JSON file containing comment threads (default: sample_comments.json)
--output_file, -o    Output JSON file for curated comments (default: curated_comments.json)
--model, -m          OpenAI model to use (default: gpt-4-1106-preview)
--top_n, -n          Export only top N ranked comments
--create_sample, -s  Create a sample comments file for testing
```

### Input Format

The input JSON should contain an array of comment objects with the following structure:

```json
[
  {
    "id": "comment_1",
    "parent_id": null,
    "text": "This is a top-level comment.",
    "score": 45,
    "depth": 0
  },
  {
    "id": "comment_2",
    "parent_id": "comment_1",
    "text": "This is a reply to comment_1.",
    "score": 12,
    "depth": 1
  }
]
```

Required fields:
- `id`: Unique identifier for the comment
- `parent_id`: ID of parent comment (null for top-level comments)
- `text`: The comment content
- `score`: Numeric score/upvotes for the comment
- `depth`: Comment depth (0 for top-level, 1 for direct replies)

### Output Format

The output JSON contains enriched comment data with AI analysis:

```json
[
  {
    "id": "comment_1",
    "parent_id": null,
    "text": "Original comment text...",
    "score": 45,
    "depth": 0,
    "insightfulness": 8,
    "originality": 6,
    "curator_tag": "Opinion",
    "rank_score": 27.33
  }
]
```

Added fields:
- `insightfulness`: AI-scored insightfulness (0-10)
- `originality`: AI-scored originality (0-10)
- `curator_tag`: Semantic category
- `rank_score`: Calculated ranking score

## Ranking Algorithm

The ranking score is calculated using:
```
rank_score = (insightfulness × 2) + (originality × 1.5) + log(score + 1)
```

This formula balances:
- **Insightfulness** (highest weight): How valuable/enlightening the comment is
- **Originality** (medium weight): How unique/creative the perspective is
- **Community Score** (logarithmic): Existing upvotes/score from the community

## Semantic Categories

The AI curator assigns one of seven categories to each comment:

- **Opinion**: Personal viewpoints and subjective statements
- **Question**: Inquiries seeking information or clarification
- **Correction**: Factual corrections or error pointing
- **Trivia**: Interesting facts or additional context
- **Recommendation**: Suggestions for books, tools, resources
- **Contrarian**: Alternative viewpoints that challenge mainstream opinions
- **Off-topic**: Comments that don't relate to the main discussion

## API Usage

The script can also be imported and used programmatically:

```python
from comment_curator import CommentCurator

# Initialize curator
curator = CommentCurator(model="gpt-4-1106-preview")

# Load and curate comments
comments = curator.load_comments("input.json")
curated = curator.curate_comments(comments)

# Save results
curator.save_results(curated, "output.json", top_n=20)
```

## Configuration

### Environment Variables

Set in `.env` file:
```
OPENAI_API_KEY=your_api_key_here
```

### Model Selection

Recommended models:
- `gpt-4-1106-preview`: Best quality analysis (default)
- `gpt-4`: Reliable alternative
- `gpt-3.5-turbo`: Faster but less accurate
- `gpt-4o`: Latest model with good performance

## Performance

- **Processing Speed**: ~2-3 seconds per thread (with API calls)
- **API Costs**: ~$0.01-0.03 per thread (depending on model and content length)
- **Accuracy**: GPT-4 provides consistent and reliable scoring

## Examples

### Example 1: Academic Discussion Curation
```bash
python comment_curator.py -i academic_comments.json -o curated_academic.json -m gpt-4
```

### Example 2: Social Media Content Analysis
```bash
python comment_curator.py -i social_media.json -o top_social.json --top_n 50
```

### Example 3: Customer Feedback Analysis
```bash
python comment_curator.py -i feedback.json -o insights.json -m gpt-4o
```

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Set `OPENAI_API_KEY` in `.env` file
   - Script will prompt for manual entry if not found

2. **Rate Limiting**
   - OpenAI API has rate limits
   - Script includes automatic delays between requests

3. **JSON Parse Errors**
   - Ensure input JSON is valid
   - Check that all required fields are present

4. **Model Not Available**
   - Verify model name is correct
   - Check OpenAI account has access to the specified model

### Logging

The script provides detailed logging:
```bash
# Enable debug logging
python comment_curator.py --input_file data.json --output_file results.json 2>&1 | tee curator.log
```

## Best Practices

1. **Batch Processing**: Process comments in reasonable batches to manage API costs
2. **Model Selection**: Use GPT-4 for quality analysis, GPT-3.5-turbo for speed
3. **Content Filtering**: Pre-filter very short or spam comments before processing
4. **Result Validation**: Review AI classifications for accuracy on your specific domain
5. **Cost Management**: Monitor OpenAI usage and set appropriate limits

## Integration Examples

### With Reddit Data
```python
# Example integration with Reddit comment data
import praw
from comment_curator import CommentCurator

reddit = praw.Reddit(...)
curator = CommentCurator()

# Extract Reddit comments and convert to required format
comments = extract_reddit_comments(reddit, subreddit="technology")
curated = curator.curate_comments(comments)
```

### With Hacker News
```python
# Example integration with HN comments
from comment_curator import CommentCurator

# Convert HN comment format to required structure
hn_comments = convert_hn_format(raw_hn_data)
curator = CommentCurator()
results = curator.curate_comments(hn_comments)
```

## License

This tool is open source and available under the MIT License.
