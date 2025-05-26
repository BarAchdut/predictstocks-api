"""Main social media service orchestrating Twitter and Reddit clients."""

import logging
import time
from typing import Dict, Any, List

from .twitter_client import TwitterClient
from .reddit_client import RedditClient
from .influencers_config import InfluencersConfig

logger = logging.getLogger(__name__)

class SocialMediaService:
    """Service for fetching posts from various social media platforms."""

    def __init__(self):
        self.twitter_client = TwitterClient()
        self.reddit_client = RedditClient()
        self.influencers_config = InfluencersConfig()

    def get_posts_for_ticker(self, ticker: str, limit: int = 100, days_back: int = 1, 
                           include_reddit: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch recent posts about a specific stock ticker from multiple platforms.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of posts to retrieve
            days_back: How many days back to search
            include_reddit: Whether to include Reddit posts

        Returns:
            List of posts with platform, author, text, date, and metrics
        """
        posts = []
        ticker = ticker.upper().strip()

        # Get Twitter posts
        twitter_posts = self.twitter_client.get_posts_for_ticker(ticker, limit // 2)
        posts.extend(twitter_posts)

        # Add delay between platform requests
        time.sleep(0.5)

        # Get Reddit posts
        if include_reddit:
            logger.info(f"Fetching Reddit posts for {ticker}")
            reddit_subreddits = self.influencers_config.get_general_subreddits()
            reddit_posts = self.reddit_client.get_posts_for_ticker(
                ticker, limit // 2, days_back, reddit_subreddits
            )
            posts.extend(reddit_posts)

        # Sort by date, then by engagement score
        posts.sort(key=lambda x: (x.get('date', ''), self._calculate_engagement_score(x)), reverse=True)

        logger.info(f"Retrieved {len(posts)} total posts for {ticker}")
        return posts[:limit]

    def get_influencer_posts(self, ticker: str, influencers: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get posts specifically from known financial influencers and high-quality Reddit sources.

        Args:
            ticker: Stock ticker symbol
            influencers: Custom influencer configuration

        Returns:
            List of influencer posts
        """
        if not influencers:
            influencers_config = self.influencers_config.get_default_influencers_config()
        elif isinstance(influencers, list):
            # If a simple list is provided, assume it's for Twitter only
            influencers_config = {
                'twitter': influencers,
                'reddit': self.influencers_config.get_reddit_sources()
            }
        else:
            influencers_config = influencers

        posts = []

        # Get Twitter influencer posts
        if influencers_config.get('twitter') and self.twitter_client.is_configured():
            twitter_posts = self.twitter_client.get_influencer_posts(
                ticker, influencers_config['twitter']
            )
            posts.extend(twitter_posts)

        # Get Reddit high-quality posts
        if influencers_config.get('reddit') and self.reddit_client.is_configured():
            reddit_sources = influencers_config['reddit']
            if isinstance(reddit_sources, dict) and 'high_quality_subreddits' in reddit_sources:
                reddit_posts = self.reddit_client.get_high_quality_posts(
                    ticker, reddit_sources['high_quality_subreddits']
                )
                posts.extend(reddit_posts)

        return posts

    def validate_credentials(self) -> Dict[str, bool]:
        """Validate API credentials for all platforms."""
        return {
            "twitter": self.twitter_client.validate_credentials(),
            "reddit": self.reddit_client.validate_credentials()
        }

    def get_platform_status(self) -> Dict[str, Any]:
        """Get status information for all platforms."""
        credentials_status = self.validate_credentials()
        
        return {
            "twitter": {
                "configured": self.twitter_client.is_configured(),
                "operational": credentials_status["twitter"]
            },
            "reddit": {
                "configured": self.reddit_client.is_configured(),
                "operational": credentials_status["reddit"]
            }
        }

    def _calculate_engagement_score(self, post: Dict[str, Any]) -> float:
        """Calculate engagement score for post ranking."""
        metrics = post.get('metrics', {})
        
        if post['platform'] == 'twitter':
            return (
                metrics.get('like_count', 0) * 1.0 +
                metrics.get('retweet_count', 0) * 2.0 +
                metrics.get('reply_count', 0) * 1.5 +
                metrics.get('quote_count', 0) * 1.8
            )
        elif post['platform'] == 'reddit':
            return (
                metrics.get('score', 0) * 1.0 +
                metrics.get('comments', 0) * 2.0 +
                metrics.get('upvote_ratio', 0.5) * 10
            )
        
        return 0.0