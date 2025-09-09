import praw
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class RedditScraper:
    def __init__(self, client_id: str, client_secret: str, user_agent: str, gemini_api_key: str = None):
        """
        Initialize Reddit API client and Gemini AI
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string for API requests
            gemini_api_key: Google Gemini API key for content filtering
        """
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # Initialize Gemini AI if API key provided
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            self.use_gemini = True
        else:
            self.use_gemini = False
        
        # Target subreddits with focus descriptions and priority (study abroad first)
        self.subreddits = [
            # HIGH PRIORITY: Study abroad focused
            {"name": "Indians_StudyAbroad", "focus": "Indische Studierende im Ausland → Bewerbung, Alltag, Erfahrungen", "priority": 1},
            {"name": "studying_in_germany", "focus": "Studieren in Deutschland → Studienprozess, Sprache, Leben", "priority": 1},
            {"name": "tumunich", "focus": "Studium an der TUM → Alltag, Prüfungen, Jobs, Austausch", "priority": 1},
            {"name": "LMUMunich", "focus": "Studium an der LMU → Bewerbungen, Fachfragen, Campusleben", "priority": 1},
            {"name": "InternationalStudents", "focus": "Breites Forum für internationale Studierende – Tipps zu Studium & Alltag", "priority": 1},
            {"name": "AskAcademia", "focus": "Austausch zur akademischen Welt, Bewerbungen, Forschung", "priority": 1},
            
            # MEDIUM PRIORITY: Immigration and life in Germany
            {"name": "IWantOut", "focus": "Migration nach / Leben in Deutschland, Behörden, Kultur", "priority": 2},
            {"name": "LifeInGermany", "focus": "Persönliche Erfahrungen, Tipps & Hilfe für das Leben in Deutschland", "priority": 2},
            {"name": "germany", "focus": "Alltag & Formelles in Deutschland – von Visum bis Wohnung", "priority": 2},
            
            # LOWER PRIORITY: General Europe
            {"name": "europe", "focus": "Leben in Europa, kultureller Austausch, Migration", "priority": 3}
        ]
        
        # Create output directory
        self.output_dir = "reddit_data"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Keywords for immigration/study abroad relevance
        self.keywords = {
            # Visa
            "application": "visa",
            "consulate": "visa",
            "embassy": "visa",
            "appointment": "visa",
            "biometrics": "visa",
            "processing time": "visa",
            "rejection": "visa",
            "extension": "visa",
            "renewal": "visa",
            "documentation": "visa",
            "interview": "visa",
            "sponsorship": "visa",
            "validity": "visa",
            "overstay": "visa",

            # Insurance
            "coverage": "insurance",
            "premium": "insurance",
            "deductible": "insurance",
            "policyholder": "insurance",
            "claim": "insurance",
            "exclusion": "insurance",
            "certificate": "insurance",
            "provider": "insurance",
            "liability": "insurance",
            "validity period": "insurance",
            "proof of insurance": "insurance",
            "co-payment": "insurance",
            "emergency assistance": "insurance",

            # Bank Account
            "statement": "bank_account",
            "deposit": "bank_account",
            "withdrawal": "bank_account",
            "account holder": "bank_account",
            "iban": "bank_account",
            "swift code": "bank_account",
            "opening balance": "bank_account",
            "dormant account": "bank_account",
            "minimum balance": "bank_account",
            "transaction fee": "bank_account",
            "verification": "bank_account",
            "account closure": "bank_account",
            "online banking": "bank_account",

            # Proof of Finance
            "bank statement": "proof_of_finance",
            "balance certificate": "proof_of_finance",
            "scholarship letter": "proof_of_finance",
            "affidavit of support": "proof_of_finance",
            "sponsorship letter": "proof_of_finance",
            "fixed deposit": "proof_of_finance",
            "income proof": "proof_of_finance",
            "salary slip": "proof_of_finance",
            "tax return": "proof_of_finance",
            "savings account": "proof_of_finance",
            "financial guarantee": "proof_of_finance",
            "asset documentation": "proof_of_finance",
            "notarized affidavit": "proof_of_finance"
        }
    
    def find_keywords_in_content(self, title: str, content: str, comments: List[Dict]) -> Dict[str, Any]:
        """
        Find relevant keywords in post title, content, and comments
        
        Args:
            title: Post title
            content: Post content
            comments: List of comment dictionaries
            
        Returns:
            Dictionary with found keywords and categories
        """
        # Combine all text content
        all_text = f"{title} {content} ".lower()
        
        # Add comments text
        for comment in comments:
            all_text += f" {comment.get('body', '')} "
        
        found_keywords = {}
        found_categories = set()
        
        # Search for keywords
        for keyword, category in self.keywords.items():
            if keyword.lower() in all_text:
                found_keywords[keyword] = category
                found_categories.add(category)
        
        return {
            "found_keywords": found_keywords,
            "found_categories": list(found_categories),
            "has_relevant_keywords": len(found_keywords) > 0,
            "keyword_count": len(found_keywords)
        }
    
    def check_relevance_with_gemini(self, post_title: str, post_content: str, comments: List[Dict], found_keywords: Dict[str, str]) -> Dict[str, Any]:
        """
        Use Gemini AI to check if post and comments are relevant for immigration/organization
        STRICT MODE: Only relevant if keywords are found and content matches those keywords
        
        Args:
            post_title: Title of the Reddit post
            post_content: Content of the Reddit post
            comments: List of comment dictionaries
            found_keywords: Dictionary of found keywords and their categories
            
        Returns:
            Dictionary with relevance analysis
        """
        if not self.use_gemini:
            return {"relevant": True, "reason": "Gemini not configured", "confidence": 0.5}
        
        try:
            # Prepare content for analysis
            comments_text = "\n".join([f"Comment: {comment.get('body', '')[:200]}..." for comment in comments[:3]])
            
            # Create keyword context
            keyword_context = ""
            if found_keywords:
                keyword_context = f"\n\nIMPORTANT: The following relevant keywords were found in this content:\n"
                for keyword, category in found_keywords.items():
                    keyword_context += f"- '{keyword}' (category: {category})\n"
                keyword_context += f"\nThis post MUST be relevant to these specific topics: {', '.join(set(found_keywords.values()))}"
            
            prompt = f"""
            STRICT RELEVANCE ANALYSIS: This Reddit post contains specific immigration/study abroad keywords. 
            You must determine if the content is ACTUALLY about these topics or just mentions them casually.

            POST TITLE: {post_title}
            POST CONTENT: {post_content[:500]}...
            
            COMMENTS:
            {comments_text}
            {keyword_context}

            STRICT CRITERIA - Only mark as relevant if:
            1. The content is PRIMARILY about the found keywords/topics
            2. It provides useful information, advice, or experiences related to these topics
            3. It's not just casual mention or off-topic discussion
            4. The main focus is on immigration, study abroad, or administrative processes

            REJECT if:
            - Keywords are mentioned but not the main topic
            - Casual conversation that happens to mention these terms
            - Memes, jokes, or off-topic discussions
            - General life advice unrelated to immigration/study abroad

            Respond with a JSON object containing:
            - "relevant": true/false (be STRICT - only true if content is primarily about the keywords)
            - "reason": detailed explanation of why relevant/not relevant
            - "confidence": 0.0-1.0
            - "main_topic": the primary topic of the post
            - "keyword_relevance": how well the content matches the found keywords
            - "usefulness": "high"/"medium"/"low" for immigration/study abroad purposes
            """
            
            response = self.gemini_model.generate_content(
                prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Try to parse JSON response
            try:
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "relevant": "relevant" in response.text.lower(),
                    "reason": response.text[:200],
                    "confidence": 0.7,
                    "topics": [],
                    "usefulness": "medium"
                }
                
        except Exception as e:
            print(f"    Gemini analysis failed: {str(e)}")
            return {"relevant": True, "reason": f"Analysis failed: {str(e)}", "confidence": 0.3}
    
    def scrape_subreddit(self, subreddit_name: str, num_upvotes_posts: int = 500, 
                        num_replies_posts: int = 5, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Scrape posts from a specific subreddit
        
        Args:
            subreddit_name: Name of the subreddit to scrape
            num_upvotes_posts: Minimum number of upvotes for posts to consider
            num_replies_posts: Number of top-level comments to fetch per post
            limit: Maximum number of posts to check
            
        Returns:
            List of post data dictionaries
        """
        print(f"Scraping r/{subreddit_name}...")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts_data = []
            
            # Check if subreddit exists and is accessible
            try:
                # Try to get subreddit info
                subreddit_info = subreddit.description
                print(f"  Subreddit accessible. Description: {subreddit_info[:100]}...")
            except Exception as e:
                print(f"  Warning: Could not access subreddit info: {str(e)}")
            
            # Get posts from multiple time periods and sorting methods
            all_posts = []
            
            # Try different sorting methods to get more historical data
            sorting_methods = [
                ('hot', limit//4),
                ('top', limit//4), 
                ('new', limit//4),
                ('rising', limit//4)
            ]
            
            for method, method_limit in sorting_methods:
                try:
                    print(f"  Getting {method} posts...")
                    if method == 'hot':
                        posts = subreddit.hot(limit=method_limit)
                    elif method == 'top':
                        posts = subreddit.top(time_filter='all', limit=method_limit)
                    elif method == 'new':
                        posts = subreddit.new(limit=method_limit)
                    elif method == 'rising':
                        posts = subreddit.rising(limit=method_limit)
                    
                    for post in posts:
                        all_posts.append(post)
                        if len(all_posts) >= limit:
                            break
                    
                    if len(all_posts) >= limit:
                        break
                        
                except Exception as e:
                    print(f"  Error with {method} method: {str(e)}")
                    continue
            
            print(f"  Found {len(all_posts)} total posts to check")
            
            # Process all collected posts
            for post in all_posts:
                # Check if post meets upvote criteria
                if post.score >= num_upvotes_posts:
                    print(f"  Found qualifying post: '{post.title[:50]}...' ({post.score} upvotes)")
                    
                    # Get post data
                    post_data = {
                        "subreddit": subreddit_name,
                        "post_id": post.id,
                        "title": post.title,
                        "author": str(post.author) if post.author else "[deleted]",
                        "score": post.score,
                        "upvote_ratio": post.upvote_ratio,
                        "num_comments": post.num_comments,
                        "created_utc": post.created_utc,
                        "created_datetime": datetime.fromtimestamp(post.created_utc).isoformat(),
                        "url": post.url,
                        "permalink": f"https://reddit.com{post.permalink}",
                        "selftext": post.selftext,
                        "is_self": post.is_self,
                        "link_flair_text": post.link_flair_text,
                        "comments": []
                    }
                    
                    # Get comments
                    post.comments.replace_more(limit=0)  # Remove "more comments" objects
                    comments = post.comments.list()[:num_replies_posts]
                    
                    for comment in comments:
                        if hasattr(comment, 'body') and comment.body != '[deleted]':
                            comment_data = {
                                "comment_id": comment.id,
                                "author": str(comment.author) if comment.author else "[deleted]",
                                "body": comment.body,
                                "score": comment.score,
                                "created_utc": comment.created_utc,
                                "created_datetime": datetime.fromtimestamp(comment.created_utc).isoformat(),
                                "parent_id": comment.parent_id,
                                "is_submitter": comment.is_submitter
                            }
                            post_data["comments"].append(comment_data)
                    
                    # First, check for relevant keywords
                    keyword_analysis = self.find_keywords_in_content(
                        post.title, 
                        post.selftext, 
                        post_data["comments"]
                    )
                    
                    # Only proceed if relevant keywords are found
                    if keyword_analysis["has_relevant_keywords"]:
                        print(f"    Found keywords: {list(keyword_analysis['found_keywords'].keys())}")
                        print(f"    Categories: {keyword_analysis['found_categories']}")
                        
                        # Add keyword analysis to post data
                        post_data["keyword_analysis"] = keyword_analysis
                        
                        # Check relevance with Gemini AI (strict mode)
                        if self.use_gemini:
                            print(f"    Analyzing relevance with Gemini (strict mode)...")
                            relevance_analysis = self.check_relevance_with_gemini(
                                post.title, 
                                post.selftext, 
                                post_data["comments"],
                                keyword_analysis["found_keywords"]
                            )
                            post_data["relevance_analysis"] = relevance_analysis
                            
                            # Only add if Gemini confirms relevance
                            if relevance_analysis.get("relevant", False):
                                posts_data.append(post_data)
                                print(f"    ✓ Relevant: {relevance_analysis.get('reason', 'No reason provided')}")
                            else:
                                print(f"    ✗ Not relevant: {relevance_analysis.get('reason', 'No reason provided')}")
                        else:
                            # If no Gemini, add posts with keywords
                            posts_data.append(post_data)
                            print(f"    ✓ Added (keywords found, no Gemini filtering)")
                    else:
                        print(f"    ✗ No relevant keywords found")
                    
                    # Add small delay to be respectful to Reddit API
                    time.sleep(0.1)
            
            print(f"  Found {len(posts_data)} qualifying posts in r/{subreddit_name}")
            return posts_data
            
        except Exception as e:
            print(f"Error scraping r/{subreddit_name}: {str(e)}")
            return []
    
    def save_posts_to_json(self, posts_data: List[Dict[str, Any]], subreddit_name: str):
        """
        Save posts data to JSON file
        
        Args:
            posts_data: List of post data dictionaries
            subreddit_name: Name of the subreddit
        """
        if not posts_data:
            print(f"No data to save for r/{subreddit_name}")
            return
        
        filename = f"{self.output_dir}/reddit_{subreddit_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(posts_data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(posts_data)} posts to {filename}")
    
    def scrape_all_subreddits(self, num_upvotes_posts: int = 500, 
                             num_replies_posts: int = 5, limit: int = 100):
        """
        Scrape all target subreddits with priority and sorting
        
        Args:
            num_upvotes_posts: Minimum number of upvotes for posts to consider
            num_replies_posts: Number of top-level comments to fetch per post
            limit: Maximum number of posts to check per subreddit
        """
        print(f"Starting Reddit scraping with Gemini AI filtering...")
        print(f"Criteria: Posts with ≥{num_upvotes_posts} upvotes, {num_replies_posts} comments per post")
        print(f"Target subreddits: {len(self.subreddits)}")
        print(f"Gemini AI filtering: {'Enabled' if self.use_gemini else 'Disabled'}")
        print("-" * 50)
        
        all_posts = []
        total_posts = 0
        
        # Sort subreddits by priority (study abroad first)
        sorted_subreddits = sorted(self.subreddits, key=lambda x: x["priority"])
        
        for subreddit_info in sorted_subreddits:
            subreddit_name = subreddit_info["name"]
            focus = subreddit_info["focus"]
            priority = subreddit_info["priority"]
            
            print(f"\nSubreddit: r/{subreddit_name} (Priority: {priority})")
            print(f"Focus: {focus}")
            
            # Scrape the subreddit
            posts_data = self.scrape_subreddit(
                subreddit_name, 
                num_upvotes_posts, 
                num_replies_posts, 
                limit
            )
            
            # Add subreddit priority to each post
            for post in posts_data:
                post["subreddit_priority"] = priority
                all_posts.append(post)
            
            # Save individual subreddit data
            self.save_posts_to_json(posts_data, subreddit_name)
            
            total_posts += len(posts_data)
            
            # Add delay between subreddits
            time.sleep(1)
        
        # Sort all posts by date (newest first) and priority
        print(f"\nSorting {len(all_posts)} posts by date and priority...")
        all_posts.sort(key=lambda x: (x["subreddit_priority"], -x["created_utc"]))
        
        # Save combined sorted data
        combined_filename = f"{self.output_dir}/reddit_combined_sorted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(combined_filename, 'w', encoding='utf-8') as f:
            json.dump(all_posts, f, indent=2, ensure_ascii=False)
        
        print(f"\nScraping completed!")
        print(f"Total posts collected: {total_posts}")
        print(f"Posts with relevant keywords: {len(all_posts)}")
        print(f"Individual subreddit data saved in: {self.output_dir}/")
        print(f"Combined sorted data saved as: {combined_filename}")
        
        # Print summary by priority
        priority_counts = {}
        category_counts = {}
        keyword_counts = {}
        
        for post in all_posts:
            priority = post["subreddit_priority"]
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # Count categories
            if "keyword_analysis" in post:
                for category in post["keyword_analysis"]["found_categories"]:
                    category_counts[category] = category_counts.get(category, 0) + 1
                
                # Count individual keywords
                for keyword in post["keyword_analysis"]["found_keywords"].keys():
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        print(f"\nPosts by priority:")
        for priority in sorted(priority_counts.keys()):
            priority_name = {1: "Study Abroad", 2: "Immigration/Life", 3: "General Europe"}[priority]
            print(f"  Priority {priority} ({priority_name}): {priority_counts[priority]} posts")
        
        print(f"\nPosts by category:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count} posts")
        
        print(f"\nTop keywords found:")
        for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  '{keyword}': {count} posts")


def main():
    """
    Main function to run the Reddit scraper
    You need to set up your Reddit API credentials
    """
    # Reddit API credentials - you need to get these from https://www.reddit.com/prefs/apps
    CLIENT_ID = "0Tgmejze8_Z7Cw0z6IiBaw"
    CLIENT_SECRET = "SSu1QynvE1AvzFX5C4Kzr6xrAGq9VQ"
    USER_AGENT = "RedditScraper/1.0 by YourUsername"
    
    # Gemini API key - get from https://makersuite.google.com/app/apikey
    GEMINI_API_KEY = "AIzaSyD4lQsXYkp0X3DNtkFbRLKL-Dp5lFCLc5w"  # Replace with your actual API key
    
    # Initialize scraper with Gemini AI
    scraper = RedditScraper(CLIENT_ID, CLIENT_SECRET, USER_AGENT, GEMINI_API_KEY)
    
    # Scrape all subreddits with priority and Gemini filtering
    scraper.scrape_all_subreddits(
        num_upvotes_posts=500,   # Posts with at least 50 upvotes
        num_replies_posts=5,    # Top 5 comments per post
        limit=50                # Check up to 50 posts per subreddit
    )


if __name__ == "__main__":
    main()
