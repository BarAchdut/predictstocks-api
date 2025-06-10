"""Reddit API client for fetching stock-related posts."""

import os
import logging
import time
import praw
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RedditClient:
    """Client for Reddit API interactions."""
    
    def __init__(self):
        print("[DEBUG] Initializing RedditClient...")
        start_time = time.time()
        
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "StockAnalyzer/1.0")
        self.username = os.getenv("REDDIT_USERNAME")
        self.password = os.getenv("REDDIT_PASSWORD")
        
        self.reddit = None
        self._initialize_client()
        
        init_time = time.time() - start_time
        print(f"[DEBUG] RedditClient initialized in {init_time:.3f} seconds")
    
    def _initialize_client(self):
        """Initialize Reddit client if credentials are available."""
        print("[DEBUG] Initializing Reddit API connection...")
        
        if not (self.client_id and self.client_secret and self.user_agent):
            print("[DEBUG] Reddit credentials not found - skipping initialization")
            logger.warning("Reddit credentials not found")
            return
        
        try:
            if self.username and self.password:
                print("[DEBUG] Initializing Reddit with username/password for full access")
                # Initialize with username/password for full access
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent,
                    username=self.username,
                    password=self.password
                )
            else:
                print("[DEBUG] Initializing Reddit in read-only mode")
                # Initialize in read-only mode
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                self.reddit.read_only = True
            
            print("[DEBUG] Reddit client initialized successfully")
            logger.info("Reddit client initialized successfully")
            
        except Exception as e:
            print(f"[DEBUG] Error initializing Reddit client: {e}")
            logger.error(f"Error initializing Reddit client: {e}")
            self.reddit = None
    
    def is_configured(self) -> bool:
        """Check if Reddit client is properly configured."""
        configured = self.reddit is not None
        print(f"[DEBUG] Reddit client configured: {configured}")
        return configured
    
    def get_posts_for_ticker(self, ticker: str, limit: int = 50, days_back: int = 1, 
                           subreddits: List[str] = None) -> List[Dict[str, Any]]:
        """Get Reddit posts about a specific ticker."""
        print(f"[DEBUG] Starting Reddit post fetch for ticker: {ticker}, limit: {limit}, days_back: {days_back}")
        start_time = time.time()
        
        if not self.is_configured():
            print("[DEBUG] Reddit client not initialized - returning empty list")
            logger.warning("Reddit client not initialized")
            return []
        
        if subreddits is None:
            subreddits = ['wallstreetbets', 'stocks', 'investing', 'StockMarket', 'SecurityAnalysis']
        
        print(f"[DEBUG] Searching in subreddits: {subreddits}")
        
        posts = []
        cutoff_time = datetime.utcnow() - timedelta(days=days_back)
        print(f"[DEBUG] Cutoff time for posts: {cutoff_time}")
        
        for i, subreddit_name in enumerate(subreddits):
            subreddit_start_time = time.time()
            print(f"[DEBUG] Processing subreddit {i+1}/{len(subreddits)}: r/{subreddit_name}")
            
            if i > 0:
                time.sleep(0.2)  # Small delay between subreddit requests
            
            try:
                subreddit_posts = self._search_subreddit(
                    subreddit_name, ticker, limit // len(subreddits), cutoff_time
                )
                posts.extend(subreddit_posts)
                
                subreddit_time = time.time() - subreddit_start_time
                print(f"[DEBUG] r/{subreddit_name} processed in {subreddit_time:.3f}s, found {len(subreddit_posts)} posts")
                
                if len(posts) >= limit:
                    print(f"[DEBUG] Reached post limit ({limit}), stopping search")
                    break
                    
            except Exception as e:
                print(f"[DEBUG] Error accessing subreddit r/{subreddit_name}: {e}")
                logger.warning(f"Error accessing subreddit r/{subreddit_name}: {e}")
                continue
        
        total_time = time.time() - start_time
        print(f"[DEBUG] Reddit post fetch completed in {total_time:.3f} seconds")
        logger.info(f"Retrieved {len(posts)} Reddit posts for {ticker}")
        return posts[:limit]
    
    def get_high_quality_posts(self, ticker: str, quality_subreddits: List[str], 
                             limit: int = 15) -> List[Dict[str, Any]]:
        """Get posts from high-quality subreddits."""
        print(f"[DEBUG] Fetching high-quality posts for {ticker} from {quality_subreddits[:3]}")
        start_time = time.time()
        
        if not self.is_configured():
            print("[DEBUG] Reddit client not configured - returning empty list")
            return []
        
        posts = []
        
        for i, subreddit_name in enumerate(quality_subreddits[:3]):  # Limit to 3 subreddits
            print(f"[DEBUG] Processing high-quality subreddit {i+1}/3: r/{subreddit_name}")
            subreddit_start_time = time.time()
            
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search for relevant posts
                for submission in subreddit.search(f"{ticker}", limit=5, sort='relevance', time_filter='week'):
                    post_data = {
                        'platform': 'reddit',
                        'id': submission.id,
                        'author': submission.author.name if submission.author else '[deleted]',
                        'author_type': 'high_quality_subreddit',
                        'text': submission.title + "\n" + (submission.selftext if submission.selftext else ""),
                        'title': submission.title,
                        'date': datetime.fromtimestamp(submission.created_utc).isoformat(),
                        'subreddit': subreddit_name,
                        'metrics': {
                            'score': submission.score,
                            'comments': submission.num_comments,
                            'upvote_ratio': submission.upvote_ratio,
                            'url': submission.url
                        }
                    }
                    posts.append(post_data)
                
                subreddit_time = time.time() - subreddit_start_time
                print(f"[DEBUG] High-quality subreddit r/{subreddit_name} processed in {subreddit_time:.3f}s")
                    
            except Exception as e:
                print(f"[DEBUG] Error fetching from high-quality subreddit r/{subreddit_name}: {e}")
                logger.warning(f"Error fetching from high-quality subreddit r/{subreddit_name}: {e}")
                continue
        
        total_time = time.time() - start_time
        print(f"[DEBUG] High-quality posts fetch completed in {total_time:.3f} seconds, found {len(posts)} posts")
        return posts
    
    def validate_credentials(self) -> bool:
        """Validate Reddit API credentials."""
        print("[DEBUG] Validating Reddit API credentials...")
        start_time = time.time()
        
        if not self.reddit:
            print("[DEBUG] No Reddit client instance - credentials invalid")
            return False
        
        try:
            # Try to access a public subreddit
            test_subreddit = self.reddit.subreddit('test')
            list(test_subreddit.hot(limit=1))  # This will raise an exception if credentials are bad
            
            validation_time = time.time() - start_time
            print(f"[DEBUG] Reddit credentials validated successfully in {validation_time:.3f}s")
            logger.info("✅ Reddit API credentials are valid")
            return True
            
        except Exception as e:
            validation_time = time.time() - start_time
            print(f"[DEBUG] Reddit credentials validation failed in {validation_time:.3f}s: {e}")
            logger.error(f"❌ Reddit API credentials invalid: {e}")
            return False
    
    def _search_subreddit(self, subreddit_name: str, ticker: str, limit: int, 
                         cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Search a specific subreddit for ticker mentions."""
        print(f"[DEBUG] Searching r/{subreddit_name} for ticker {ticker}")
        search_start_time = time.time()
        
        posts = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            search_queries = [f"{ticker}", f"${ticker}", f"{ticker} stock"]
            print(f"[DEBUG] Using search queries: {search_queries}")
            
            for query_idx, query in enumerate(search_queries):
                query_start_time = time.time()
                print(f"[DEBUG] Executing query {query_idx+1}/{len(search_queries)}: '{query}'")
                
                try:
                    submissions = subreddit.search(
                        query,
                        sort='new',
                        time_filter='week',
                        limit=max(5, limit)
                    )
                    
                    query_posts = 0
                    for submission in submissions:
                        # Check if submission is within the time period
                        submission_time = datetime.fromtimestamp(submission.created_utc)
                        if submission_time < cutoff_time:
                            continue
                        
                        post_data = {
                            'platform': 'reddit',
                            'id': submission.id,
                            'author': submission.author.name if submission.author else '[deleted]',
                            'text': submission.title + "\n" + (submission.selftext if submission.selftext else ""),
                            'title': submission.title,
                            'date': submission_time.isoformat(),
                            'subreddit': subreddit_name,
                            'metrics': {
                                'score': submission.score,
                                'comments': submission.num_comments,
                                'upvote_ratio': submission.upvote_ratio,
                                'url': submission.url
                            }
                        }
                        posts.append(post_data)
                        query_posts += 1
                    
                    query_time = time.time() - query_start_time
                    print(f"[DEBUG] Query '{query}' completed in {query_time:.3f}s, found {query_posts} posts")
                    
                    # If we got results from this query, no need to try other queries
                    if any(p['subreddit'] == subreddit_name for p in posts):
                        print(f"[DEBUG] Found results for r/{subreddit_name}, skipping remaining queries")
                        break
                        
                except Exception as e:
                    query_time = time.time() - query_start_time
                    print(f"[DEBUG] Search query '{query}' failed in {query_time:.3f}s: {e}")
                    logger.warning(f"Search query '{query}' failed in r/{subreddit_name}: {e}")
                    continue
                    
        except Exception as e:
            search_time = time.time() - search_start_time
            if "403" in str(e):
                print(f"[DEBUG] Reddit returned 403 for r/{subreddit_name} after {search_time:.3f}s — possibly blocked")
                logger.error("❌ Reddit returned 403 — possibly blocked or misconfigured.")
            else:
                print(f"[DEBUG] Error searching subreddit r/{subreddit_name} after {search_time:.3f}s: {e}")
                logger.error(f"Error searching subreddit r/{subreddit_name}: {e}")
        
        search_time = time.time() - search_start_time
        print(f"[DEBUG] Subreddit r/{subreddit_name} search completed in {search_time:.3f}s, found {len(posts)} posts")
        return posts