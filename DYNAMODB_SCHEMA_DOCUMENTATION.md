# 🗄️ Pookie B News Daily - DynamoDB Schema Documentation

## 📊 Database Overview

Your DynamoDB setup contains **8 tables total**, with **3 core tables** specifically for the HN Scraper system:

- **Region**: `us-west-2`
- **Total HN Data**: 3,884 items (1.80 MB)
- **Billing Mode**: Pay-per-request (serverless)

---

## 🔑 Core HN Scraper Tables

### 1. `HN_article_data` - Main Articles Storage
**Purpose**: Primary storage for scraped Hacker News articles

**Schema**:
```
Primary Key: hn_id (String)
Billing: PAY_PER_REQUEST
Items: 130 articles
Size: 46,281 bytes
```

**Attributes**:
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `hn_id` | String | Hacker News article ID (Primary Key) | "44327942" |
| `title` | String | Article title | "Amoeba: A distributed operating system..." |
| `url` | String | Article URL | "https://cs.cornell.edu/..." |
| `author` | String | HN username who posted | "PaulHoule" |
| `domain` | String | Website domain | "cs.cornell.edu" |
| `score` | Decimal | HN upvote score | 55 |
| `num_comments` | Decimal | Total comment count | 21 |
| `time_posted` | Decimal | Unix timestamp | 1750428845 |
| `story_type` | String | Type of post | "story" |
| `story_text` | String | Post text content | "" (usually empty for links) |
| `scraped_at` | String | When data was collected | "2025-06-24 21:46:17" |

### 2. `hn-article-analyses` - AI Analysis Results  
**Purpose**: Stores AI-generated summaries and analysis

**Schema**:
```
Primary Key: hn_id (String)
Billing: PAY_PER_REQUEST  
Items: 94 analyses
Size: 27,173 bytes
```

**Attributes**:
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `hn_id` | String | Links to HN_article_data (Foreign Key) | "44327942" |
| `title` | String | Article title (duplicated) | "Amoeba: A distributed operating system..." |
| `url` | String | Article URL (duplicated) | "https://cs.cornell.edu/..." |
| `domain` | String | Website domain (duplicated) | "cs.cornell.edu" |
| `summary` | String | AI-generated summary | "Score: 55, Comments: 21, Author: PaulHoule" |
| `generated_at` | String | Analysis timestamp | "2025-06-24 21:46:17" |

### 3. `hn-scraper-comments` - Comments & Discussions
**Purpose**: Stores all comments with threading information

**Schema**:
```
Primary Key: 
  - HASH: article_id (String)  
  - RANGE: comment_id (String)
Billing: PAY_PER_REQUEST
Items: 3,660 comments  
Size: 1,818,807 bytes (largest table)
```

**Attributes**:
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `article_id` | String | Links to HN_article_data.hn_id | "44380185" |
| `comment_id` | String | Unique comment ID | "44382156" |
| `content` | String | Comment text content | "Related: Launch HN: Better Auth..." |
| `author` | String | Commenter's HN username | "dang" |
| `parent_id` | String | Parent comment ID (for threading) | "44380185" |
| `level` | Decimal | Nesting depth (0 = top-level) | 0 |
| `time_posted` | Decimal | Unix timestamp | 1750888527 |
| `scraped_at` | String | When comment was scraped | "2025-06-26T07:04:02.793329" |

---

## 🔗 Data Relationships

```
HN_article_data (1) ←→ (1) hn-article-analyses
     ↓ hn_id
     
HN_article_data (1) ←→ (many) hn-scraper-comments  
     ↓ hn_id = article_id
```

## 📈 Storage Statistics

| Table | Items | Size (Bytes) | Size (MB) | % of Total |
|-------|-------|--------------|-----------|------------|
| `hn-scraper-comments` | 3,660 | 1,818,807 | 1.73 | 96.1% |
| `HN_article_data` | 130 | 46,281 | 0.04 | 2.4% |
| `hn-article-analyses` | 94 | 27,173 | 0.03 | 1.4% |
| **TOTAL** | **3,884** | **1,892,261** | **1.80** | **100%** |

---

## 🛠️ Usage Patterns

### For Pookie B News Daily:

1. **Article Discovery**: Query `HN_article_data` for latest articles
2. **AI Insights**: Join with `hn-article-analyses` for summaries  
3. **Discussion Analysis**: Get comments from `hn-scraper-comments`
4. **Podcast Generation**: Combine all three tables for weekly content

### Common Queries:

```python
# Get article with analysis
article = dynamodb.Table('HN_article_data').get_item(Key={'hn_id': '44327942'})
analysis = dynamodb.Table('hn-article-analyses').get_item(Key={'hn_id': '44327942'})

# Get all comments for an article  
comments = dynamodb.Table('hn-scraper-comments').query(
    KeyConditionExpression=Key('article_id').eq('44327942')
)

# Get recent articles
recent = dynamodb.Table('HN_article_data').scan(
    FilterExpression=Attr('scraped_at').begins_with('2025-06-26')
)
```

---

## 🚀 Optimization Notes

1. **Comments table is 96% of storage** - Consider archiving old comments
2. **No Global Secondary Indexes** - Add GSI on `scraped_at` for time-based queries
3. **Duplicate data** in analyses table - Consider normalizing
4. **Pay-per-request billing** - Good for variable workloads

## 📊 Other Tables in Account

Your account also contains these non-HN tables:
- `AdviceDB` (0 items)
- `JournalEntries` (1 item) 
- `JournalPrompts` (6 items)
- `Users` (19 items)
- `userchats` (10 items)

Total account storage: ~2.5 MB across all tables.
