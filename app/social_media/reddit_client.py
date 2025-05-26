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
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "StockAnalyzer/1.0")
        self.username = os.getenv("REDDIT_USERNAME")
        self.password = os.getenv("REDDIT_PASSWORD")
        
        self.reddit = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Reddit client if credentials are available."""
        if not (self.client_id and self.client_secret and self.user_agent):
            logger.warning("Reddit credentials not found")
            return
        
        try:
            if self.username and self.password:
                # Initialize with username/password for full access
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent,
                    username=self.username,
                    password=self.password
                )
            else:
                # Initialize in read-only mode
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                self.reddit.read_only = True
            
            logger.info("Reddit client initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Reddit client: {e}")
            self.reddit = None
    
    def is_configured(self) -> bool:
        """Check if Reddit client is properly configured."""
        return self.reddit is not None
    
    def get_posts_for_ticker(self, ticker: str, limit: int = 50, days_back: int = 1, 
                           subreddits: List[str] = None) -> List[Dict[str, Any]]:
        """Get Reddit posts about a specific ticker."""
        if not self.is_configured():
            logger.warning("Reddit client not initialized")
            return []
        
        if subreddits is None:
            subreddits = ['wallstreetbets', 'stocks', 'investing', 'StockMarket', 'SecurityAnalysis']
        
        posts = []
        cutoff_time = datetime.utcnow() - timedelta(days=days_back)
        
        for i, subreddit_name in enumerate(subreddits):
            if i > 0:
                time.sleep(0.2)  # Small delay between subreddit requests
            
            try:
                subreddit_posts = self._search_subreddit(
                    subreddit_name, ticker, limit // len(subreddits), cutoff_time
                )
                posts.extend(subreddit_posts)
                
                if len(posts) >= limit:
                    break
                    
            except Exception as e:
                logger.warning(f"Error accessing subreddit r/{subreddit_name}: {e}")
                continue
        
        logger.info(f"Retrieved {len(posts)} Reddit posts for {ticker}")
        return posts[:limit]
    
    def get_high_quality_posts(self, ticker: str, quality_subreddits: List[str], 
                             limit: int = 15) -> List[Dict[str, Any]]:
        """Get posts from high-quality subreddits."""
        if not self.is_configured():
            return []
        
        posts = []
        
        for subreddit_name in quality_subreddits[:3]:  # Limit to 3 subreddits
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
                    
            except Exception as e:
                logger.warning(f"Error fetching from high-quality subreddit r/{subreddit_name}: {e}")
                continue
        
        return posts
    
    def validate_credentials(self) -> bool:
        """Validate Reddit API credentials."""
        if not self.reddit:
            return False
        
        try:
            # Try to access a public subreddit
            test_subreddit = self.reddit.subreddit('test')
            list(test_subreddit.hot(limit=1))  # This will raise an exception if credentials are bad
            logger.info("✅ Reddit API credentials are valid")
            return True
            
        except Exception as e:
            logger.error(f"❌ Reddit API credentials invalid: {e}")
            return False
    
    def _search_subreddit(self, subreddit_name: str, ticker: str, limit: int, 
                         cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Search a specific subreddit for ticker mentions."""
        posts = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            search_queries = [f"{ticker}", f"${ticker}", f"{ticker} stock"]
            
            for query in search_queries:
                try:
                    submissions = subreddit.search(
                        query,
                        sort='new',
                        time_filter='week',
                        limit=max(5, limit)
                    )
                    
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
                    
                    # If we got results from this query, no need to try other queries
                    if any(p['subreddit'] == subreddit_name for p in posts):
                        break
                        
                except Exception as e:
                    logger.warning(f"Search query '{query}' failed in r/{subreddit_name}: {e}")
                    continue
                    
        except Exception as e:
            if "403" in str(e):
                logger.error("❌ Reddit returned 403 — possibly blocked or misconfigured.")
            else:
                logger.error(f"Error searching subreddit r/{subreddit_name}: {e}")
        
        return posts