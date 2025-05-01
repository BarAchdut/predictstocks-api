import os
import logging
from typing import List, Dict, Any
import requests
import praw
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SocialMediaService:
    """Service for fetching posts from various social media platforms."""
    
    def __init__(self):
        self.twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        # Reddit authentication params
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.reddit_user_agent = os.getenv("REDDIT_USER_AGENT")
        self.reddit_username = os.getenv("REDDIT_USERNAME")
        
        # Initialize Reddit client if credentials are available
        self.reddit = None
        if self.reddit_client_id and self.reddit_client_secret and self.reddit_user_agent:
            try:
                if self.reddit_username and self.reddit_password:
                    # Initialize with username/password for full access
                    self.reddit = praw.Reddit(
                        client_id=self.reddit_client_id,
                        client_secret=self.reddit_client_secret,
                        user_agent=self.reddit_user_agent,
                        username=self.reddit_username,
                        password=self.reddit_password
                    )
                else:
                    # Initialize in read-only mode
                    self.reddit = praw.Reddit(
                        client_id=self.reddit_client_id,
                        client_secret=self.reddit_client_secret,
                        user_agent=self.reddit_user_agent
                    )
                    self.reddit.read_only = True
                
                logger.info("Reddit client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Reddit client: {e}")
                self.reddit = None
    
    def get_posts_for_ticker(self, ticker: str, limit: int = 100, days_back: int = 1) -> List[Dict[str, Any]]:
        """
        Fetch recent posts about a specific stock ticker from multiple platforms.
        
        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of posts to retrieve
            days_back: How many days back to search
            
        Returns:
            List of posts with platform, author, text, date, and metrics
        """
        posts = []
        
        # Get Twitter posts
        twitter_posts = self._get_twitter_posts(ticker, limit // 2, days_back)
        posts.extend(twitter_posts)
        
        # Get Reddit posts
        reddit_posts = self._get_reddit_posts(ticker, limit // 2, days_back)
        posts.extend(reddit_posts)
        
        # Sort by date, popularity, or relevance
        posts.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return posts[:limit]
    
    def _get_twitter_posts(self, ticker: str, limit: int, days_back: int) -> List[Dict[str, Any]]:
        """Get posts from Twitter about a specific ticker."""
        if not self.twitter_bearer_token:
            logger.warning("Twitter API token not found")
            return []
            
        try:
            # Query Twitter API for relevant posts
            # Here would be code to communicate with Twitter API
            search_url = "https://api.twitter.com/2/tweets/search/recent"
            query_params = {
                'query': f'${ticker} OR #{ticker}stock -is:retweet',
                'tweet.fields': 'author_id,created_at,public_metrics',
                'expansions': 'author_id',
                'user.fields': 'name,username,public_metrics',
                'max_results': limit
            }
            
            response = requests.get(
                search_url,
                headers={"Authorization": f"Bearer {self.twitter_bearer_token}"},
                params=query_params
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Process API response to a uniform format
            tweets = []
            for tweet in result.get('data', []):
                tweets.append({
                    'platform': 'twitter',
                    'author': tweet.get('author_id'),
                    'text': tweet.get('text'),
                    'date': tweet.get('created_at'),
                    'metrics': tweet.get('public_metrics', {})
                })
                
            return tweets
            
        except Exception as e:
            logger.error(f"Error fetching Twitter posts: {e}")
            return []
    
    def _get_reddit_posts(self, ticker: str, limit: int, days_back: int) -> List[Dict[str, Any]]:
        """Get posts from Reddit about a specific ticker."""
        if not self.reddit:
            logger.warning("Reddit client not initialized")
            return []
            
        try:
            posts = []
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(days=days_back)
            
            # Search in relevant financial subreddits
            subreddits = ['wallstreetbets', 'stocks', 'investing', 'StockMarket']
            
            for subreddit_name in subreddits:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search for submissions mentioning the ticker
                search_query = f"{ticker} OR ${ticker}"
                submissions = subreddit.search(search_query, sort='new', time_filter='week', limit=limit//len(subreddits))
                
                for submission in submissions:
                    # Check if submission is within the time period
                    submission_time = datetime.fromtimestamp(submission.created_utc)
                    if submission_time < cutoff_time:
                        continue
                    
                    # Add submission to results
                    posts.append({
                        'platform': 'reddit',
                        'author': submission.author.name if submission.author else '[deleted]',
                        'text': submission.title + "\n" + (submission.selftext if submission.selftext else ""),
                        'date': submission_time.isoformat(),
                        'metrics': {
                            'score': submission.score,
                            'comments': submission.num_comments,
                            'upvote_ratio': submission.upvote_ratio,
                            'url': submission.url
                        }
                    })
                    
                # If we already have enough posts, break early
                if len(posts) >= limit:
                    break
                    
            return posts[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching Reddit posts: {e}")
            return []
    
    def get_influencer_posts(self, ticker: str, influencers: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get posts specifically from known financial influencers.
        
        Args:
            ticker: Stock ticker symbol
            influencers: List of influencer handles/IDs to focus on
            
        Returns:
            List of influencer posts
        """
        if not influencers:
            # Default list of financial influencers
            twitter_influencers = [
                'jimcramer', 'elonmusk', 'WarrenBuffett', 'Carl_C_Icahn', 
                'CathieDWood', 'chamath', 'MorganStanley', 'GoldmanSachs'
            ]
            reddit_influencers = []  # Reddit doesn't have the same influencer concept
            influencers = {'twitter': twitter_influencers, 'reddit': reddit_influencers}
        elif isinstance(influencers, list):
            influencers = {'twitter': influencers, 'reddit': []}
            
        posts = []
        
        # Get Twitter influencer posts
        if self.twitter_bearer_token and influencers.get('twitter'):
            for influencer in influencers['twitter']:
                try:
                    search_url = "https://api.twitter.com/2/tweets/search/recent"
                    query_params = {
                        'query': f'from:{influencer} ${ticker} OR #{ticker}stock OR #{ticker} -is:retweet',
                        'tweet.fields': 'author_id,created_at,public_metrics',
                        'expansions': 'author_id',
                        'user.fields': 'name,username,public_metrics',
                        'max_results': 10
                    }
                    
                    response = requests.get(
                        search_url,
                        headers={"Authorization": f"Bearer {self.twitter_bearer_token}"},
                        params=query_params
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        for tweet in result.get('data', []):
                            posts.append({
                                'platform': 'twitter',
                                'author': influencer,
                                'author_type': 'influencer',
                                'text': tweet.get('text'),
                                'date': tweet.get('created_at'),
                                'metrics': tweet.get('public_metrics', {})
                            })
                except Exception as e:
                    logger.error(f"Error fetching tweets from influencer {influencer}: {e}")
                    
        return posts