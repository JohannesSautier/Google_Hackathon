"""
Example usage of the Reddit scraper

Before running this script, you need to:
1. Create a Reddit app at https://www.reddit.com/prefs/apps
2. Get your client_id and client_secret
3. Update the credentials below
"""

from get_reddit import RedditScraper

def example_basic_usage():
    """Basic example with default parameters"""
    
    # Your Reddit API credentials
    CLIENT_ID = "your_client_id_here"
    CLIENT_SECRET = "your_client_secret_here"
    USER_AGENT = "RedditScraper/1.0 by YourUsername"
    
    # Initialize scraper
    scraper = RedditScraper(CLIENT_ID, CLIENT_SECRET, USER_AGENT)
    
    # Scrape all subreddits with default parameters
    scraper.scrape_all_subreddits(
        num_upvotes_posts=500,  # Posts with at least 500 upvotes
        num_replies_posts=5,    # Top 5 comments per post
        limit=100               # Check up to 100 posts per subreddit
    )

def example_custom_parameters():
    """Example with custom parameters"""
    
    CLIENT_ID = "your_client_id_here"
    CLIENT_SECRET = "your_client_secret_here"
    USER_AGENT = "RedditScraper/1.0 by YourUsername"
    
    scraper = RedditScraper(CLIENT_ID, CLIENT_SECRET, USER_AGENT)
    
    # Scrape with custom parameters
    scraper.scrape_all_subreddits(
        num_upvotes_posts=1000,  # Higher threshold for more popular posts
        num_replies_posts=10,    # More comments per post
        limit=50                 # Fewer posts to check per subreddit
    )

def example_single_subreddit():
    """Example scraping a single subreddit"""
    
    CLIENT_ID = "your_client_id_here"
    CLIENT_SECRET = "your_client_secret_here"
    USER_AGENT = "RedditScraper/1.0 by YourUsername"
    
    scraper = RedditScraper(CLIENT_ID, CLIENT_SECRET, USER_AGENT)
    
    # Scrape only one subreddit
    posts_data = scraper.scrape_subreddit(
        subreddit_name="studying_in_germany",
        num_upvotes_posts=200,
        num_replies_posts=3,
        limit=50
    )
    
    # Save the data
    scraper.save_posts_to_json(posts_data, "studying_in_germany")

if __name__ == "__main__":
    print("Reddit Scraper Example Usage")
    print("=" * 40)
    print("Please update the CLIENT_ID and CLIENT_SECRET with your Reddit API credentials")
    print("You can get these from: https://www.reddit.com/prefs/apps")
    print()
    print("Uncomment one of the example functions below to run:")
    print()
    print("# example_basic_usage()")
    print("# example_custom_parameters()")
    print("# example_single_subreddit()")
