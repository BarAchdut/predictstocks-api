"""Configuration for social media influencers and high-quality sources."""

from typing import Dict, List

class InfluencersConfig:
    """Configuration for financial influencers and quality sources."""
    
    @staticmethod
    def get_default_twitter_influencers() -> List[str]:
        """Get default list of financial influencers on Twitter."""
        return [
            'jeromepowell',     # Jerome Powell
            'realDonaldTrump',  # Donald Trump  
            'elonmusk',         # Elon Musk
            'JHuangNVIDIA',     # Jensen Huang
            'tim_cook',         # Tim Cook
            'sundarpichai',     # Sundar Pichai
            'zuck',             # Mark Zuckerberg
            'WarrenBuffett',    # Warren Buffett
            'jimcramer'         # Jim Cramer
        ]
    
    @staticmethod
    def get_reddit_sources() -> Dict[str, List[str]]:
        """Get Reddit sources categorized by quality level."""
        return {
            'high_quality_subreddits': [
                'SecurityAnalysis',        # Deep value investing discussions
                'ValueInvesting',          # Warren Buffett style investing
                'financialindependence',   # FIRE community insights
                'investing',               # General investing discussions
                'StockMarket'             # Market analysis and trends
            ],
            'trending_subreddits': [
                'wallstreetbets',         # Retail sentiment and meme stocks
                'stocks',                 # Popular stock discussions
                'pennystocks',            # Small cap and penny stock alerts
                'options'                 # Options trading insights
            ]
        }
    
    @staticmethod
    def get_general_subreddits() -> List[str]:
        """Get general financial subreddits for regular posts."""
        return ['wallstreetbets', 'stocks', 'investing', 'StockMarket', 'SecurityAnalysis']
    
    @staticmethod
    def get_default_influencers_config() -> Dict[str, any]:
        """Get complete default influencers configuration."""
        return {
            'twitter': InfluencersConfig.get_default_twitter_influencers(),
            'reddit': InfluencersConfig.get_reddit_sources()
        }