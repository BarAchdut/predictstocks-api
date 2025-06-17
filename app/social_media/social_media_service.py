
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
        print("[DEBUG] Initializing SocialMediaService...")
        start_time = time.time()

        self.twitter_client = TwitterClient()
        self.reddit_client = RedditClient()
        self.influencers_config = InfluencersConfig()

        # Track platform status to avoid repeated failures
        self.twitter_rate_limited = False
        self.reddit_blocked = False

        # Global timeout tracking
        self.global_start_time = None

        init_time = time.time() - start_time
        print(f"[DEBUG] SocialMediaService initialized in {init_time:.3f} seconds")

    def set_global_start_time(self, start_time: float):
        """Set the global start time for timeout tracking."""
        self.global_start_time = start_time
        print(f"[DEBUG] Global Twitter timeout set: 180 seconds from {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    def get_posts_for_ticker(self, ticker: str, limit: int = 100, days_back: int = 1, 
                              include_reddit: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch posts from multiple platforms with individual error handling.
        Each platform failure is isolated and doesn't affect others.
        """
        print(f"[DEBUG] Starting data collection for {ticker}")
        prediction_start_time = time.time()

        posts = []
        ticker = ticker.upper().strip()

        # Twitter collection with error isolation and global timeout
        if not self.twitter_rate_limited:
            if self.global_start_time and time.time() - self.global_start_time > 180:
                print("[DEBUG] Global Twitter timeout reached (180s), skipping Twitter")
                self.twitter_rate_limited = True
            else:
                print("[DEBUG] Attempting Twitter posts fetch...")
                try:
                    twitter_posts = self.twitter_client.get_posts_for_ticker(
                        ticker, limit // 2, self.global_start_time
                    )
                    posts.extend(twitter_posts)
                    print(f"[DEBUG] Twitter: {len(twitter_posts)} posts collected")
                except Exception as e:
                    print(f"[DEBUG] Twitter failed: {e}")
                    if "rate limit" in str(e).lower() or "429" in str(e):
                        self.twitter_rate_limited = True
                        print("[DEBUG] Twitter rate limited - will skip future attempts")
        else:
            print("[DEBUG] Skipping Twitter (rate limited)")

        # Reddit collection with error isolation
        if include_reddit and not self.reddit_blocked:
            print("[DEBUG] Attempting Reddit posts fetch...")
            try:
                reddit_subreddits = self.influencers_config.get_general_subreddits()
                reddit_posts = self.reddit_client.get_posts_for_ticker(
                    ticker, limit // 2, days_back, reddit_subreddits
                )
                posts.extend(reddit_posts)
                print(f"[DEBUG] Reddit: {len(reddit_posts)} posts collected")
            except Exception as e:
                print(f"[DEBUG] Reddit failed: {e}")
                if "403" in str(e):
                    self.reddit_blocked = True
                    print("[DEBUG] Reddit blocked - will skip future attempts")
        elif self.reddit_blocked:
            print("[DEBUG] Skipping Reddit (blocked)")

        # Sort and limit results
        posts.sort(key=lambda x: (x.get('date', ''), self._calculate_engagement_score(x)), reverse=True)
        final_posts = posts[:limit]

        total_time = time.time() - prediction_start_time
        print(f"[DEBUG] Data collection completed in {total_time:.3f} seconds")
        print(f"[DEBUG] Final result: {len(final_posts)} posts for {ticker}")

        logger.info(f"Retrieved {len(final_posts)} total posts for {ticker}")
        return final_posts

    def get_twitter_posts_only(self, ticker: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get only Twitter posts for a ticker."""
        print(f"[DEBUG] Starting Twitter-only data collection for {ticker}")
        
        if self.twitter_rate_limited:
            print("[DEBUG] Skipping Twitter (rate limited)")
            return []
        
        if self.global_start_time and time.time() - self.global_start_time > 180:
            print("[DEBUG] Global Twitter timeout reached (180s), skipping Twitter")
            self.twitter_rate_limited = True
            return []
        
        print("[DEBUG] Attempting Twitter posts fetch...")
        try:
            twitter_posts = self.twitter_client.get_posts_for_ticker(
                ticker.upper().strip(), limit, self.global_start_time
            )
            print(f"[DEBUG] Twitter: {len(twitter_posts)} posts collected")
            return twitter_posts
        except Exception as e:
            print(f"[DEBUG] Twitter failed: {e}")
            if "rate limit" in str(e).lower() or "429" in str(e):
                self.twitter_rate_limited = True
                print("[DEBUG] Twitter rate limited - will skip future attempts")
            return []

    def get_reddit_posts_only(self, ticker: str, limit: int = 50, days_back: int = 1) -> List[Dict[str, Any]]:
        """Get only Reddit posts for a ticker."""
        print(f"[DEBUG] Starting Reddit-only data collection for {ticker}")
        
        if self.reddit_blocked:
            print("[DEBUG] Skipping Reddit (blocked)")
            return []
        
        print("[DEBUG] Attempting Reddit posts fetch...")
        try:
            reddit_subreddits = self.influencers_config.get_general_subreddits()
            reddit_posts = self.reddit_client.get_posts_for_ticker(
                ticker.upper().strip(), limit, days_back, reddit_subreddits
            )
            print(f"[DEBUG] Reddit: {len(reddit_posts)} posts collected")
            return reddit_posts
        except Exception as e:
            print(f"[DEBUG] Reddit failed: {e}")
            if "403" in str(e):
                self.reddit_blocked = True
                print("[DEBUG] Reddit blocked - will skip future attempts")
            return []

    def get_influencer_posts(self, ticker: str, influencers: List[str] = None) -> List[Dict[str, Any]]:
        """Get posts from financial influencers with error handling."""
        print(f"[DEBUG] Starting influencer posts fetch for {ticker}")

        if not influencers:
            influencers_config = self.influencers_config.get_default_influencers_config()
        elif isinstance(influencers, list):
            influencers_config = {
                'twitter': influencers,
                'reddit': self.influencers_config.get_reddit_sources()
            }
        else:
            influencers_config = influencers

        posts = []

        # Twitter influencers with global timeout check
        if influencers_config.get('twitter') and self.twitter_client.is_configured() and not self.twitter_rate_limited:
            if self.global_start_time and time.time() - self.global_start_time > 180:
                print("[DEBUG] Global Twitter timeout reached for influencers (180s), skipping")
                self.twitter_rate_limited = True
            else:
                try:
                    twitter_posts = self.twitter_client.get_influencer_posts(
                        ticker, influencers_config['twitter'], self.global_start_time
                    )
                    posts.extend(twitter_posts)
                    print(f"[DEBUG] Twitter influencers: {len(twitter_posts)} posts")
                except Exception as e:
                    print(f"[DEBUG] Twitter influencers failed: {e}")
                    if "rate limit" in str(e).lower() or "429" in str(e):
                        self.twitter_rate_limited = True

        # Reddit high-quality sources
        if influencers_config.get('reddit') and self.reddit_client.is_configured() and not self.reddit_blocked:
            try:
                reddit_sources = influencers_config['reddit']
                if isinstance(reddit_sources, dict) and 'high_quality_subreddits' in reddit_sources:
                    reddit_posts = self.reddit_client.get_high_quality_posts(
                        ticker, reddit_sources['high_quality_subreddits']
                    )
                    posts.extend(reddit_posts)
                    print(f"[DEBUG] Reddit high-quality: {len(reddit_posts)} posts")
            except Exception as e:
                print(f"[DEBUG] Reddit high-quality failed: {e}")
                if "403" in str(e):
                    self.reddit_blocked = True

        return posts

    def is_twitter_available(self) -> bool:
        """Check if Twitter is available for use."""
        if self.twitter_rate_limited:
            return False
        if self.global_start_time and time.time() - self.global_start_time > 180:
            return False
        return self.twitter_client.is_configured()

    def is_reddit_available(self) -> bool:
        """Check if Reddit is available for use."""
        return not self.reddit_blocked and self.reddit_client.is_configured()

    def get_platform_status(self) -> Dict[str, Any]:
        """Get current platform status."""
        global_timeout_remaining = 0
        if self.global_start_time:
            elapsed = time.time() - self.global_start_time
            global_timeout_remaining = max(0, 180 - elapsed)

        return {
            "twitter": {
                "configured": self.twitter_client.is_configured(),
                "operational": self.is_twitter_available(),
                "rate_limited": self.twitter_rate_limited,
                "global_timeout_remaining": global_timeout_remaining
            },
            "reddit": {
                "configured": self.reddit_client.is_configured(),
                "operational": self.is_reddit_available(),
                "blocked": self.reddit_blocked
            }
        }

    def reset_platform_status(self):
        """Reset platform limitation flags."""
        self.twitter_rate_limited = False
        self.reddit_blocked = False
        self.global_start_time = None
        print("[DEBUG] Platform status flags reset")

    def _calculate_engagement_score(self, post: Dict[str, Any]) -> float:
        """Calculate engagement score for post ranking."""
        metrics = post.get('metrics', {})

        if post['platform'] == 'twitter':
            score = (
                metrics.get('like_count', 0) * 1.0 +
                metrics.get('retweet_count', 0) * 2.0 +
                metrics.get('reply_count', 0) * 1.5 +
                metrics.get('quote_count', 0) * 1.8
            )
        elif post['platform'] == 'reddit':
            score = (
                metrics.get('score', 0) * 1.0 +
                metrics.get('comments', 0) * 2.0 +
                metrics.get('upvote_ratio', 0.5) * 10
            )
        else:
            score = 0.0

        return score