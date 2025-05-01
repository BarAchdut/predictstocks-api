import os
import logging
from typing import List, Dict, Any
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SocialMediaService:
    """Service for fetching posts from various social media platforms."""
    
    def __init__(self):
        self.twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.reddit_api_key = os.getenv("REDDIT_API_KEY")
        # You can add API keys for other platforms
    
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
            # For example:
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
        # Here would be similar code to communicate with Reddit API
        return []  # Implementation would be similar to Twitter
    
    def get_influencer_posts(self, ticker: str, influencers: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get posts specifically from known financial influencers.
        
        Args:
            ticker: Stock ticker symbol
            influencers: List of influencer handles/IDs to focus on
            
        Returns:
            List of influencer posts
        """
        # Implementation would be similar to previous methods
        return []