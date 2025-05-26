# import os
# import logging
# import time
# from typing import List, Dict, Any, Optional
# import requests
# import praw
# from datetime import datetime, timedelta
# from dotenv import load_dotenv
# import json
# import re

# load_dotenv()

# logger = logging.getLogger(__name__)

# class SocialMediaService:
#     """Service for fetching posts from various social media platforms."""

#     def __init__(self):
#         self.twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

#         # Reddit authentication params
#         self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
#         self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
#         self.reddit_user_agent = os.getenv("REDDIT_USER_AGENT", "StockAnalyzer/1.0")
#         self.reddit_username = os.getenv("REDDIT_USERNAME")
#         self.reddit_password = os.getenv("REDDIT_PASSWORD")

#         # Rate limiting settings - Updated for better handling
#         self.twitter_request_delay = 2.0  # Increased to 2 seconds between Twitter requests
#         self.max_retries = 2  # Reduced retries to avoid long delays
#         self.retry_delay = 60  # Increased initial retry delay to 60 seconds

#         # Initialize Reddit client if credentials are available
#         self.reddit = None
#         if self.reddit_client_id and self.reddit_client_secret and self.reddit_user_agent:
#             try:
#                 if self.reddit_username and self.reddit_password:
#                     # Initialize with username/password for full access
#                     self.reddit = praw.Reddit(
#                         client_id=self.reddit_client_id,
#                         client_secret=self.reddit_client_secret,
#                         user_agent=self.reddit_user_agent,
#                         username=self.reddit_username,
#                         password=self.reddit_password
#                     )
#                 else:
#                     # Initialize in read-only mode
#                     self.reddit = praw.Reddit(
#                         client_id=self.reddit_client_id,
#                         client_secret=self.reddit_client_secret,
#                         user_agent=self.reddit_user_agent
#                     )
#                     self.reddit.read_only = True

#                 logger.info("Reddit client initialized successfully")
#             except Exception as e:
#                 logger.error(f"Error initializing Reddit client: {e}")
#                 self.reddit = None

#     def _make_twitter_request(self, url: str, headers: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
#         """Make a Twitter API request with rate limiting and retry logic."""
#         for attempt in range(self.max_retries):
#             try:
#                 if attempt > 0:
#                     time.sleep(self.twitter_request_delay)

#                 # Log request details for debugging
#                 logger.debug(f"Twitter API request: {url}")
#                 logger.debug(f"Query parameters: {params}")

#                 response = requests.get(url, headers=headers, params=params, timeout=30)
                
#                 # Log response details for debugging
#                 logger.debug(f"Response status: {response.status_code}")
#                 logger.debug(f"Response URL: {response.url}")

#                 if response.status_code == 200:
#                     return response.json()
#                 elif response.status_code == 429:
#                     # Get retry-after from headers, or use exponential backoff
#                     retry_after = int(response.headers.get('retry-after', 60))  # Default to 60 seconds
#                     # Use exponential backoff if no retry-after header
#                     if 'retry-after' not in response.headers:
#                         retry_after = min(60 * (2 ** attempt), 900)  # Max 15 minutes
                    
#                     logger.warning(f"Twitter rate limit exceeded. Waiting {retry_after} seconds before retry {attempt + 1}/{self.max_retries}")
                    
#                     # If we hit rate limits multiple times, stop trying this query
#                     if attempt >= 1:  # Give up after 2 rate limit hits
#                         logger.warning(f"Multiple rate limits hit, skipping to next query")
#                         break
                        
#                     time.sleep(retry_after)
#                     continue
#                 elif response.status_code == 400:
#                     error_detail = response.json() if response.content else "No error details"
#                     logger.error(f"Twitter API bad request: {error_detail}")
                    
#                     # Try with simplified query on first attempt
#                     if attempt == 0 and 'query' in params:
#                         original_query = params['query']
#                         # Simplify query by removing special characters and operators
#                         ticker = self._extract_ticker_from_query(original_query)
#                         params['query'] = f"{ticker} lang:en"
#                         logger.info(f"Retrying with simplified query: {params['query']}")
#                         continue
#                     break
#                 elif response.status_code == 401:
#                     logger.error("Twitter API authentication failed. Check your Bearer Token.")
#                     break
#                 else:
#                     logger.error(f"Twitter API error {response.status_code}: {response.text}")
#                     response.raise_for_status()

#             except requests.exceptions.Timeout:
#                 logger.warning(f"Twitter API request timeout (attempt {attempt + 1}/{self.max_retries})")
#                 if attempt < self.max_retries - 1:
#                     time.sleep(self.retry_delay)
#             except requests.exceptions.RequestException as e:
#                 if attempt == self.max_retries - 1:
#                     logger.error(f"Twitter API request failed after {self.max_retries} attempts: {e}")
#                     raise
#                 else:
#                     wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
#                     logger.warning(f"Twitter API request failed (attempt {attempt + 1}/{self.max_retries}). Retrying in {wait_time} seconds: {e}")
#                     time.sleep(wait_time)

#         return {}

#     def _extract_ticker_from_query(self, query: str) -> str:
#         """Extract ticker symbol from query string."""
#         # Look for patterns like $AAPL or #AAPLstock
#         ticker_match = re.search(r'[\$#]([A-Z]{1,5})', query)
#         if ticker_match:
#             return ticker_match.group(1)
        
#         # Look for word patterns
#         words = query.split()
#         for word in words:
#             if word.isalpha() and len(word) <= 5 and word.isupper():
#                 return word
        
#         return "stock"  # fallback

#     def get_posts_for_ticker(self, ticker: str, limit: int = 100, days_back: int = 1, include_reddit: bool = True) -> List[Dict[str, Any]]:
#         """
#         Fetch recent posts about a specific stock ticker from multiple platforms.

#         Args:
#             ticker: Stock ticker symbol
#             limit: Maximum number of posts to retrieve
#             days_back: How many days back to search
#             include_reddit: Whether to include Reddit posts

#         Returns:
#             List of posts with platform, author, text, date, and metrics
#         """
#         posts = []
#         ticker = ticker.upper().strip()

#         # Get Twitter posts
#         twitter_posts = self._get_twitter_posts(ticker, limit // 2, days_back)
#         posts.extend(twitter_posts)

#         # Add delay between platform requests
#         time.sleep(0.5)

#         if include_reddit:
#             logger.info(f"Fetching Reddit posts for {ticker}")
#             reddit_posts = self._get_reddit_posts(ticker, limit // 2, days_back)
#             posts.extend(reddit_posts)

#         # Sort by date, then by engagement score
#         posts.sort(key=lambda x: (x.get('date', ''), self._calculate_engagement_score(x)), reverse=True)

#         logger.info(f"Retrieved {len(posts)} total posts for {ticker}")
#         return posts[:limit]

#     def _calculate_engagement_score(self, post: Dict[str, Any]) -> float:
#         """Calculate engagement score for post ranking."""
#         metrics = post.get('metrics', {})
        
#         if post['platform'] == 'twitter':
#             return (
#                 metrics.get('like_count', 0) * 1.0 +
#                 metrics.get('retweet_count', 0) * 2.0 +
#                 metrics.get('reply_count', 0) * 1.5 +
#                 metrics.get('quote_count', 0) * 1.8
#             )
#         elif post['platform'] == 'reddit':
#             return (
#                 metrics.get('score', 0) * 1.0 +
#                 metrics.get('comments', 0) * 2.0 +
#                 metrics.get('upvote_ratio', 0.5) * 10
#             )
        
#         return 0.0

#     def _get_twitter_posts(self, ticker: str, limit: int, days_back: int) -> List[Dict[str, Any]]:
#         """Get posts from Twitter about a specific ticker."""
#         if not self.twitter_bearer_token:
#             logger.warning("Twitter API token not found")
#             return []

#         try:
#             search_url = "https://api.twitter.com/2/tweets/search/recent"
            
#             # Use query format compatible with basic Twitter API access (no cashtag $)
#             query_variants = [
#                 f"{ticker} stock -is:retweet lang:en",               # Primary query (no cashtag)
#                 f"#{ticker}stock -is:retweet lang:en",               # Hashtag only
#                 f"{ticker} -is:retweet lang:en"                      # Simple fallback
#             ]
            
#             tweets = []
            
#             for i, query in enumerate(query_variants):
#                 try:
#                     query_params = {
#                         'query': query,
#                         'tweet.fields': 'author_id,created_at,public_metrics,context_annotations,lang',
#                         'expansions': 'author_id',
#                         'user.fields': 'name,username,public_metrics,verified',
#                         'max_results': min(limit, 100)  # Twitter API limit is 100
#                     }

#                     headers = {"Authorization": f"Bearer {self.twitter_bearer_token}"}

#                     result = self._make_twitter_request(search_url, headers, query_params)
                    
#                     if result and 'data' in result:
#                         # Create user lookup for author information
#                         users = {}
#                         if 'includes' in result and 'users' in result['includes']:
#                             users = {user['id']: user for user in result['includes']['users']}
                        
#                         # Process tweets
#                         for tweet in result.get('data', []):
#                             author_id = tweet.get('author_id')
#                             author_info = users.get(author_id, {})
                            
#                             tweet_data = {
#                                 'platform': 'twitter',
#                                 'id': tweet.get('id'),
#                                 'author': author_info.get('username', 'unknown'),
#                                 'author_name': author_info.get('name', 'Unknown'),
#                                 'text': tweet.get('text', ''),
#                                 'date': tweet.get('created_at'),
#                                 'metrics': tweet.get('public_metrics', {}),
#                                 'verified': author_info.get('verified', False),
#                                 'query_used': query
#                             }
#                             tweets.append(tweet_data)
                        
#                         # If we got results, break from trying other queries
#                         if tweets:
#                             logger.info(f"Successfully retrieved {len(tweets)} Twitter posts for {ticker} using query: {query}")
#                             break
                    
#                 except Exception as e:
#                     logger.warning(f"Query variant {i+1} failed for {ticker}: {e}")
#                     continue
            
#             return tweets

#         except Exception as e:
#             logger.error(f"Error fetching Twitter posts for {ticker}: {e}")
#             return []

#     def _get_reddit_posts(self, ticker: str, limit: int, days_back: int) -> List[Dict[str, Any]]:
#         """Get posts from Reddit about a specific ticker."""
#         if not self.reddit:
#             logger.warning("Reddit client not initialized")
#             return []

#         try:
#             posts = []
#             # Calculate cutoff time
#             cutoff_time = datetime.utcnow() - timedelta(days=days_back)

#             # Search in relevant financial subreddits
#             subreddits = ['wallstreetbets', 'stocks', 'investing', 'StockMarket', 'SecurityAnalysis']

#             for i, subreddit_name in enumerate(subreddits):
#                 if i > 0:
#                     # Add small delay between subreddit requests
#                     time.sleep(0.2)

#                 try:
#                     subreddit = self.reddit.subreddit(subreddit_name)

#                     # Search for submissions mentioning the ticker
#                     search_queries = [f"{ticker}", f"${ticker}", f"{ticker} stock"]
                    
#                     for query in search_queries:
#                         try:
#                             submissions = subreddit.search(
#                                 query, 
#                                 sort='new', 
#                                 time_filter='week', 
#                                 limit=max(5, limit // len(subreddits))
#                             )

#                             for submission in submissions:
#                                 # Check if submission is within the time period
#                                 submission_time = datetime.fromtimestamp(submission.created_utc)
#                                 if submission_time < cutoff_time:
#                                     continue

#                                 # Add submission to results
#                                 post_data = {
#                                     'platform': 'reddit',
#                                     'id': submission.id,
#                                     'author': submission.author.name if submission.author else '[deleted]',
#                                     'text': submission.title + "\n" + (submission.selftext if submission.selftext else ""),
#                                     'title': submission.title,
#                                     'date': submission_time.isoformat(),
#                                     'subreddit': subreddit_name,
#                                     'metrics': {
#                                         'score': submission.score,
#                                         'comments': submission.num_comments,
#                                         'upvote_ratio': submission.upvote_ratio,
#                                         'url': submission.url
#                                     }
#                                 }
#                                 posts.append(post_data)

#                             # If we got results from this query, no need to try other queries for this subreddit
#                             if any(p['subreddit'] == subreddit_name for p in posts):
#                                 break
                                
#                         except Exception as e:
#                             logger.warning(f"Search query '{query}' failed in r/{subreddit_name}: {e}")
#                             continue

#                 except Exception as e:
#                     logger.warning(f"Error accessing subreddit r/{subreddit_name}: {e}")
#                     continue

#                 # If we already have enough posts, break early
#                 if len(posts) >= limit:
#                     break

#             logger.info(f"Retrieved {len(posts)} Reddit posts for {ticker}")
#             return posts[:limit]

#         except Exception as e:
#             if "403" in str(e):
#                 logger.error("❌ Reddit returned 403 — possibly blocked or misconfigured.")
#             else:
#                 logger.error(f"Error fetching Reddit posts: {e}")
#             return []

#     def get_influencer_posts(self, ticker: str, influencers: List[str] = None) -> List[Dict[str, Any]]:
#         """
#         Get posts specifically from known financial influencers and high-quality Reddit sources.

#         Args:
#             ticker: Stock ticker symbol
#             influencers: Custom influencer configuration

#         Returns:
#             List of influencer posts
#         """
#         if not influencers:
#             # Updated list of financial influencers for Twitter
#             twitter_influencers = [
#                 'jeromepowell',     # Jerome Powell
#                 'realDonaldTrump',  # Donald Trump  
#                 'elonmusk',         # Elon Musk
#                 'JHuangNVIDIA',     # Jensen Huang
#                 'tim_cook',         # Tim Cook
#                 'sundarpichai',     # Sundar Pichai
#                 'zuck',             # Mark Zuckerberg
#                 'WarrenBuffett',    # Warren Buffett
#                 'jimcramer'         # Jim Cramer
#             ]
            
#             # For Reddit, track high-quality subreddits and trending topics
#             reddit_sources = {
#                 'high_quality_subreddits': [
#                     'SecurityAnalysis',        # Deep value investing discussions
#                     'ValueInvesting',          # Warren Buffett style investing
#                     'financialindependence',   # FIRE community insights
#                     'investing',               # General investing discussions
#                     'StockMarket'             # Market analysis and trends
#                 ],
#                 'trending_subreddits': [
#                     'wallstreetbets',         # Retail sentiment and meme stocks
#                     'stocks',                 # Popular stock discussions
#                     'pennystocks',            # Small cap and penny stock alerts
#                     'options'                 # Options trading insights
#                 ]
#             }
            
#             influencers = {
#                 'twitter': twitter_influencers, 
#                 'reddit': reddit_sources
#             }
#         elif isinstance(influencers, list):
#             # If a simple list is provided, assume it's for Twitter only
#             influencers = {
#                 'twitter': influencers, 
#                 'reddit': {
#                     'high_quality_subreddits': ['SecurityAnalysis', 'ValueInvesting', 'investing'],
#                     'trending_subreddits': ['wallstreetbets', 'stocks']
#                 }
#             }

#         posts = []

#         # Get Twitter influencer posts
#         if self.twitter_bearer_token and influencers.get('twitter'):
#             for i, influencer in enumerate(influencers['twitter']):
#                 if i > 0:
#                     # Add delay between influencer requests
#                     time.sleep(self.twitter_request_delay)

#                 try:
#                     search_url = "https://api.twitter.com/2/tweets/search/recent"
#                     query_params = {
#                         'query': f'from:{influencer} ({ticker} OR #{ticker}stock) -is:retweet',
#                         'tweet.fields': 'author_id,created_at,public_metrics',
#                         'expansions': 'author_id',
#                         'user.fields': 'name,username,public_metrics,verified',
#                         'max_results': 10
#                     }

#                     headers = {"Authorization": f"Bearer {self.twitter_bearer_token}"}

#                     result = self._make_twitter_request(search_url, headers, query_params)

#                     for tweet in result.get('data', []):
#                         posts.append({
#                             'platform': 'twitter',
#                             'id': tweet.get('id'),
#                             'author': influencer,
#                             'author_type': 'influencer',
#                             'text': tweet.get('text'),
#                             'date': tweet.get('created_at'),
#                             'metrics': tweet.get('public_metrics', {})
#                         })

#                 except Exception as e:
#                     logger.error(f"Error fetching tweets from influencer {influencer}: {e}")
#                     continue

#         # Get Reddit high-quality posts from relevant subreddits
#         if self.reddit and influencers.get('reddit'):
#             reddit_sources = influencers['reddit']
            
#             # Get posts from high-quality subreddits (more detailed analysis)
#             if isinstance(reddit_sources, dict) and 'high_quality_subreddits' in reddit_sources:
#                 for subreddit_name in reddit_sources['high_quality_subreddits'][:3]:  # Limit to 3 subreddits
#                     try:
#                         subreddit = self.reddit.subreddit(subreddit_name)
#                         # Get hot posts that mention the ticker
#                         for submission in subreddit.search(f"{ticker}", limit=5, sort='relevance', time_filter='week'):
#                             posts.append({
#                                 'platform': 'reddit',
#                                 'id': submission.id,
#                                 'author': submission.author.name if submission.author else '[deleted]',
#                                 'author_type': 'high_quality_subreddit',
#                                 'text': submission.title + "\n" + (submission.selftext if submission.selftext else ""),
#                                 'title': submission.title,
#                                 'date': datetime.fromtimestamp(submission.created_utc).isoformat(),
#                                 'subreddit': subreddit_name,
#                                 'metrics': {
#                                     'score': submission.score,
#                                     'comments': submission.num_comments,
#                                     'upvote_ratio': submission.upvote_ratio,
#                                     'url': submission.url
#                                 }
#                             })
#                     except Exception as e:
#                         logger.warning(f"Error fetching from high-quality subreddit r/{subreddit_name}: {e}")
#                         continue

#         return posts

#     def validate_credentials(self) -> Dict[str, bool]:
#         """Validate API credentials for all platforms."""
#         results = {
#             "twitter": False,
#             "reddit": False
#         }

#         # Test Twitter credentials
#         if self.twitter_bearer_token:
#             try:
#                 test_url = "https://api.twitter.com/2/tweets/search/recent"
#                 test_params = {"query": "test", "max_results": 10}
#                 headers = {"Authorization": f"Bearer {self.twitter_bearer_token}"}
                
#                 response = requests.get(test_url, headers=headers, params=test_params, timeout=10)
#                 results["twitter"] = response.status_code in [200, 429]  # 429 means rate limited but valid
                
#                 if results["twitter"]:
#                     logger.info("✅ Twitter API credentials are valid")
#                 else:
#                     logger.error(f"❌ Twitter API credentials invalid: {response.status_code}")
                    
#             except Exception as e:
#                 logger.error(f"❌ Twitter API test failed: {e}")

#         # Test Reddit credentials
#         if self.reddit:
#             try:
#                 # Try to access a public subreddit
#                 test_subreddit = self.reddit.subreddit('test')
#                 list(test_subreddit.hot(limit=1))  # This will raise an exception if credentials are bad
#                 results["reddit"] = True
#                 logger.info("✅ Reddit API credentials are valid")
#             except Exception as e:
#                 logger.error(f"❌ Reddit API credentials invalid: {e}")

#         return results

#     def get_platform_status(self) -> Dict[str, Any]:
#         """Get status information for all platforms."""
#         status = {
#             "twitter": {
#                 "configured": bool(self.twitter_bearer_token),
#                 "operational": False
#             },
#             "reddit": {
#                 "configured": bool(self.reddit),
#                 "operational": False
#             }
#         }

#         # Test operational status
#         credentials_status = self.validate_credentials()
#         status["twitter"]["operational"] = credentials_status["twitter"]
#         status["reddit"]["operational"] = credentials_status["reddit"]

#         return status