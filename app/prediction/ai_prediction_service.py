import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.prediction_service import PredictionService
from app.social_media import SocialMediaService
from app.ai import AIService
from app.data.historical_data import HistoricalDataService
from app.utils.price_prediction import calculate_technical_prediction, combine_predictions

from .technical_analyzer import TechnicalAnalyzer
from .signal_combiner import SignalCombiner  
from .confidence_calculator import ConfidenceCalculator

logger = logging.getLogger(__name__)

class AIPredictionService(PredictionService):
    """Enhanced prediction service using AI for social media sentiment analysis."""

    def __init__(self):
        super().__init__()
        self.social_media_service = SocialMediaService()
        self.ai_service = AIService()
        self.historical_service = HistoricalDataService()
        
        # Initialize new components
        self.technical_analyzer = TechnicalAnalyzer()
        self.signal_combiner = SignalCombiner()
        self.confidence_calculator = ConfidenceCalculator()

    def predict_price_movement(self, ticker: str, timeframe: str = "1d", include_reddit: bool = True) -> Dict[str, Any]:
        """
        Predict stock price movement based on technical indicators and social media sentiment.

        Args:
            ticker: Stock ticker symbol
            timeframe: Timeframe for prediction ("1d", "1w", "1m")
            include_reddit: Whether to include Reddit posts in the analysis

        Returns:
            Dictionary with prediction results
        """
        try:
            logger.info(f"Starting prediction for {ticker} with timeframe {timeframe}")
            
            # Get historical data for technical analysis
            historical_data = self.historical_service.get_historical_data(ticker, days=30)
            logger.info(f"Retrieved {len(historical_data)} historical data points for {ticker}")

            # Get social media posts about the ticker
            social_posts = self.social_media_service.get_posts_for_ticker(
                ticker, 
                limit=50, 
                include_reddit=include_reddit
            )
            logger.info(f"Retrieved {len(social_posts)} social media posts for {ticker}")

            # Get additional posts from known influencers and high-quality sources
            influencer_posts = self.social_media_service.get_influencer_posts(ticker)
            logger.info(f"Retrieved {len(influencer_posts)} influencer posts for {ticker}")
            
            # Combine all posts and remove duplicates
            all_posts = social_posts + influencer_posts
            unique_posts = self._remove_duplicate_posts(all_posts)
            logger.info(f"After deduplication: {len(unique_posts)} unique posts for analysis")

            # Use AI to analyze sentiment and predict impact
            ai_analysis = self.ai_service.analyze_social_media_impact(unique_posts, ticker)
            logger.info(f"AI analysis completed for {ticker}")

            # Calculate technical indicators
            technical_signals = self.technical_analyzer.calculate_technical_indicators(historical_data)

            # Combine technical analysis with AI sentiment analysis
            prediction = self.signal_combiner.combine_signals(technical_signals, ai_analysis)

            # Calculate prediction confidence
            confidence = self.confidence_calculator.calculate_confidence(
                prediction, ai_analysis, technical_signals, len(unique_posts)
            )

            # Get current price
            current_price = technical_signals.get("latest_price", 0)

            # Calculate technical prediction using linear regression
            prediction_days = self._get_prediction_days(timeframe)
            technical_prediction = calculate_technical_prediction(historical_data, prediction_days)

            # Combine AI and technical predictions
            combined_prediction = combine_predictions(
                ai_prediction={"prediction": prediction, "confidence": confidence},
                technical_prediction=technical_prediction,
                current_price=current_price
            )

            # Create comprehensive result
            result = {
                "ticker": ticker,
                "prediction_time": datetime.now().isoformat(),
                "timeframe": timeframe,
                "prediction": prediction,
                "technical_signals": technical_signals,
                "sentiment_analysis": ai_analysis.get("ai_analysis", {}),
                "confidence": confidence,
                "predicted_price": combined_prediction.get("predicted_price"),
                "supporting_data": {
                    "total_posts_analyzed": len(unique_posts),
                    "social_posts": len(social_posts),
                    "influencer_posts": len(influencer_posts),
                    "reddit_included": include_reddit,
                    "technical_prediction": technical_prediction,
                    "combined_prediction_details": combined_prediction,
                    "data_quality": self._assess_data_quality(unique_posts, historical_data),
                    "confidence_breakdown": self.confidence_calculator.get_confidence_breakdown(
                        prediction, ai_analysis, technical_signals, len(unique_posts)
                    )
                },
                "raw_ai_response": ai_analysis.get("raw_response", ""),
                "analysis_timestamp": datetime.now().isoformat()
            }

            logger.info(f"Prediction completed for {ticker}: {prediction.get('direction', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"Error in predict_price_movement for {ticker}: {e}")
            return self._create_error_response(ticker, timeframe, str(e))

    def _get_prediction_days(self, timeframe: str) -> int:
        """Get number of days for prediction based on timeframe."""
        timeframe_map = {
            "1d": 1,
            "1w": 7,
            "1m": 30
        }
        return timeframe_map.get(timeframe, 1)

    def _remove_duplicate_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate posts based on ID and content similarity."""
        seen_ids = set()
        seen_content = set()
        unique_posts = []

        for post in posts:
            post_id = post.get('id')
            post_content = post.get('text', '')[:100]  # First 100 characters for similarity check
            
            # Skip if we've seen this ID or very similar content
            if post_id and post_id in seen_ids:
                continue
            if post_content and post_content in seen_content:
                continue
            
            # Add to unique posts
            unique_posts.append(post)
            if post_id:
                seen_ids.add(post_id)
            if post_content:
                seen_content.add(post_content)

        return unique_posts

    def _assess_data_quality(self, posts: List[Dict[str, Any]], historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the quality of data available for prediction."""
        return {
            "posts_quality": {
                "total_posts": len(posts),
                "has_influencer_posts": any(post.get('author_type') == 'influencer' for post in posts),
                "has_high_quality_sources": any(post.get('author_type') == 'high_quality_subreddit' for post in posts),
                "platform_diversity": len(set(post.get('platform') for post in posts)),
                "recent_posts": len([p for p in posts if self._is_recent_post(p)])
            },
            "technical_data_quality": {
                "historical_points": len(historical_data),
                "has_sufficient_data": len(historical_data) >= 10,
                "data_recency": "recent" if historical_data else "none"
            }
        }

    def _is_recent_post(self, post: Dict[str, Any]) -> bool:
        """Check if a post is from the last 24 hours."""
        try:
            post_date = post.get('date')
            if not post_date:
                return False
            
            if isinstance(post_date, str):
                post_datetime = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
            else:
                post_datetime = post_date
            
            return datetime.now() - post_datetime.replace(tzinfo=None) < timedelta(hours=24)
        except:
            return False

def _create_error_response(self, ticker: str, timeframe: str, error_message: str) -> Dict[str, Any]:
    return {
        "ticker": ticker,
        "prediction_time": datetime.now(),
        "timeframe": timeframe,
        "prediction": {
            "direction": "neutral",
            "sentiment": "neutral",
            "confidence": 0.1,
            "reasoning": f"Fallback response due to error: {error_message}"
        },
        "technical_signals": {
            "trend": "neutral",
            "latest_price": 0.0,
            "price_change": 0.0,
            "price_change_percent": 0.0
        },
        "sentiment_analysis": {
            "sentiment": "neutral",
            "impact": "low",
            "confidence": "low",
            "key_factors": [],
            "patterns": [],
            "reasoning": "No social media data available"
        },
        "confidence": 0.1,
        "supporting_data": {
            "error_occurred": True,
            "error_details": error_message
        },
        "posts": []
    }

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all underlying services."""
        try:
            # Test social media service
            social_status = self.social_media_service.get_platform_status()
            
            # Test AI service
            ai_test = self.ai_service.test_connection()
            ai_status = ai_test.get("status") == "success"
            
            return {
                "social_media": social_status,
                "ai_service": {
                    "operational": ai_status,
                    "details": ai_test
                },
                "historical_data": {
                    "operational": True  # Assume operational if no errors
                },
                "technical_analyzer": {
                    "operational": True
                },
                "signal_combiner": {
                    "operational": True
                },
                "confidence_calculator": {
                    "operational": True
                },
                "overall_status": "operational" if ai_status and any(social_status.values()) else "limited"
            }
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {
                "error": str(e),
                "overall_status": "error"
            }