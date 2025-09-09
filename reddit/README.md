# Reddit Scraper

A Python script to scrape Reddit posts and comments from specific subreddits related to studying abroad, particularly in Germany.

## Features

- Scrapes 10 target subreddits focused on international students and German study programs
- Filters posts by minimum upvote count (default: 500)
- Collects top comments for each post (default: 5)
- Saves data as JSON files in organized structure
- Respects Reddit API rate limits

## Target Subreddits

| Subreddit | Focus |
|-----------|-------|
| r/Indians_StudyAbroad | Indian students abroad → applications, daily life, experiences |
| r/studying_in_germany | Studying in Germany → study process, language, life |
| r/tumunich | TUM studies → daily life, exams, jobs, exchange |
| r/LMUMunich | LMU studies → applications, subject questions, campus life |
| r/InternationalStudents | Broad forum for international students – study & life tips |
| r/MigrateToGermany | Migration to/life in Germany, authorities, culture |
| r/AskAcademia | Academic world exchange, applications, research |
| r/Europe | Life in Europe, cultural exchange, migration |
| r/Germany | Daily life & formalities in Germany – from visa to housing |
| r/LifeInGermany | Personal experiences, tips & help for life in Germany |

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" as the app type
4. Note down your `client_id` and `client_secret`

### 3. Configure Credentials

Update the credentials in `get_reddit.py` or `example_usage.py`:

```python
CLIENT_ID = "your_client_id_here"
CLIENT_SECRET = "your_client_secret_here"
USER_AGENT = "RedditScraper/1.0 by YourUsername"
```

## Usage

### Basic Usage

```python
from get_reddit import RedditScraper

# Initialize scraper
scraper = RedditScraper(CLIENT_ID, CLIENT_SECRET, USER_AGENT)

# Scrape all subreddits with default parameters
scraper.scrape_all_subreddits()
```

### Custom Parameters

```python
# Scrape with custom parameters
scraper.scrape_all_subreddits(
    num_upvotes_posts=1000,  # Posts with at least 1000 upvotes
    num_replies_posts=10,    # Top 10 comments per post
    limit=50                 # Check up to 50 posts per subreddit
)
```

### Single Subreddit

```python
# Scrape only one subreddit
posts_data = scraper.scrape_subreddit(
    subreddit_name="studying_in_germany",
    num_upvotes_posts=200,
    num_replies_posts=3,
    limit=50
)
```

## Output

The scraper creates a `reddit_data/` folder and saves JSON files for each subreddit with the following structure:

```json
[
  {
    "subreddit": "studying_in_germany",
    "post_id": "abc123",
    "title": "Post title",
    "author": "username",
    "score": 750,
    "upvote_ratio": 0.95,
    "num_comments": 45,
    "created_utc": 1640995200,
    "created_datetime": "2022-01-01T00:00:00",
    "url": "https://...",
    "permalink": "https://reddit.com/r/...",
    "selftext": "Post content...",
    "is_self": true,
    "link_flair_text": "Question",
    "comments": [
      {
        "comment_id": "def456",
        "author": "commenter",
        "body": "Comment text...",
        "score": 25,
        "created_utc": 1640995800,
        "created_datetime": "2022-01-01T00:10:00",
        "parent_id": "t3_abc123",
        "is_submitter": false
      }
    ]
  }
]
```

## Default Parameters

- `num_upvotes_posts`: 500 (minimum upvotes for posts)
- `num_replies_posts`: 5 (number of top comments per post)
- `limit`: 100 (maximum posts to check per subreddit)

## Rate Limiting

The script includes built-in delays to respect Reddit's API rate limits:
- 0.1 seconds between posts
- 1 second between subreddits

## Files

- `get_reddit.py` - Main scraper class and functions
- `example_usage.py` - Example usage patterns
- `requirements.txt` - Python dependencies
- `reddit_data/` - Output folder for JSON files (created automatically)
