"""Twitter API client for fetching stock-related posts."""

import os
import logging
import time
import requests
import re
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class TwitterClient:
    """Client for Twitter API interactions."""
    
    def __init__(self):
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.request_delay = 2.0  # 2 seconds between requests
        self.max_retries = 2
        self.retry_delay = 60  # 60 seconds initial retry delay
        
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        } if self.bearer_token else {}
    
    def is_configured(self) -> bool:
        """Check if Twitter client is properly configured."""
        return bool(self.bearer_token)
    
    def get_posts_for_ticker(self, ticker: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get Twitter posts about a specific ticker."""
        if not self.is_configured():
            logger.warning("Twitter API token not found")
            return []
        
        # Query variants - no cashtag operator for basic API
        query_variants = [
            f"{ticker} stock -is:retweet lang:en",      # Primary query
            f"#{ticker}stock -is:retweet lang:en",      # Hashtag only  
            f"{ticker} -is:retweet lang:en"             # Simple fallback
        ]
        
        tweets = []
        search_url = "https://api.twitter.com/2/tweets/search/recent"
        
        for i, query in enumerate(query_variants):
            try:
                params = {
                    'query': query,
                    'tweet.fields': 'author_id,created_at,public_metrics,context_annotations,lang',
                    'expansions': 'author_id',
                    'user.fields': 'name,username,public_metrics,verified',
                    'max_results': min(limit, 100)  # API limit
                }
                
                result = self._make_request(search_url, params)
                
                if result and 'data' in result:
                    processed_tweets = self._process_tweets_response(result, query)
                    tweets.extend(processed_tweets)
                    
                    if tweets:
                        logger.info(f"Retrieved {len(tweets)} Twitter posts for {ticker} using: {query}")
                        break
                        
            except Exception as e:
                logger.warning(f"Query variant {i+1} failed for {ticker}: {e}")
                continue
        
        return tweets
    
    def get_influencer_posts(self, ticker: str, influencers: List[str]) -> List[Dict[str, Any]]:
        """Get posts from specific influencers about a ticker."""
        if not self.is_configured():
            return []
        
        posts = []
        search_url = "https://api.twitter.com/2/tweets/search/recent"
        
        for i, influencer in enumerate(influencers):
            if i > 0:
                time.sleep(self.request_delay)
            
            try:
                params = {
                    'query': f'from:{influencer} ({ticker} OR #{ticker}stock) -is:retweet',
                    'tweet.fields': 'author_id,created_at,public_metrics',
                    'expansions': 'author_id',
                    'user.fields': 'name,username,public_metrics,verified',
                    'max_results': 10
                }
                
                result = self._make_request(search_url, params)
                
                for tweet in result.get('data', []):
                    posts.append({
                        'platform': 'twitter',
                        'id': tweet.get('id'),
                        'author': influencer,
                        'author_type': 'influencer',
                        'text': tweet.get('text'),
                        'date': tweet.get('created_at'),
                        'metrics': tweet.get('public_metrics', {})
                    })
                    
            except Exception as e:
                logger.error(f"Error fetching tweets from influencer {influencer}: {e}")
                continue
        
        return posts
    
    def validate_credentials(self) -> bool:
        """Validate Twitter API credentials."""
        if not self.bearer_token:
            return False
        
        try:
            test_url = "https://api.twitter.com/2/tweets/search/recent"
            test_params = {"query": "test", "max_results": 10}
            
            response = requests.get(test_url, headers=self.headers, params=test_params, timeout=10)
            is_valid = response.status_code in [200, 429]  # 429 = rate limited but valid
            
            if is_valid:
                logger.info("✅ Twitter API credentials are valid")
            else:
                logger.error(f"❌ Twitter API credentials invalid: {response.status_code}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Twitter API test failed: {e}")
            return False
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a Twitter API request with retry logic."""
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    time.sleep(self.request_delay)
                
                logger.debug(f"Twitter API request: {url} with params: {params}")
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                logger.debug(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    return response.json()
                
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('retry-after', 60))
                    if 'retry-after' not in response.headers:
                        retry_after = min(60 * (2 ** attempt), 900)  # Max 15 minutes
                    
                    logger.warning(f"Rate limit exceeded. Waiting {retry_after}s (attempt {attempt + 1}/{self.max_retries})")
                    
                    if attempt >= 1:  # Give up after 2 rate limit hits
                        logger.warning("Multiple rate limits hit, skipping")
                        break
                    
                    time.sleep(retry_after)
                    continue
                
                elif response.status_code == 400:
                    error_detail = response.json() if response.content else "No error details"
                    logger.error(f"Bad request: {error_detail}")
                    
                    # Try simplified query on first attempt
                    if attempt == 0 and 'query' in params:
                        ticker = self._extract_ticker_from_query(params['query'])
                        params['query'] = f"{ticker} lang:en"
                        logger.info(f"Retrying with simplified query: {params['query']}")
                        continue
                    break
                
                elif response.status_code == 401:
                    logger.error("Authentication failed. Check Bearer Token.")
                    break
                
                else:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    response.raise_for_status()
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    raise
                else:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Request failed (attempt {attempt + 1}). Retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
        
        return {}
    
    def _extract_ticker_from_query(self, query: str) -> str:
        """Extract ticker symbol from query string."""
        ticker_match = re.search(r'[\$#]([A-Z]{1,5})', query)
        if ticker_match:
            return ticker_match.group(1)
        
        words = query.split()
        for word in words:
            if word.isalpha() and len(word) <= 5 and word.isupper():
                return word
        
        return "stock"
    
    def _process_tweets_response(self, result: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Process Twitter API response into standardized format."""
        tweets = []
        
        # Create user lookup
        users = {}
        if 'includes' in result and 'users' in result['includes']:
            users = {user['id']: user for user in result['includes']['users']}
        
        # Process tweets
        for tweet in result.get('data', []):
            author_id = tweet.get('author_id')
            author_info = users.get(author_id, {})
            
            tweet_data = {
                'platform': 'twitter',
                'id': tweet.get('id'),
                'author': author_info.get('username', 'unknown'),
                'author_name': author_info.get('name', 'Unknown'),
                'text': tweet.get('text', ''),
                'date': tweet.get('created_at'),
                'metrics': tweet.get('public_metrics', {}),
                'verified': author_info.get('verified', False),
                'query_used': query
            }
            tweets.append(tweet_data)
        
        return tweets