# prediction_service.py
import logging
import time
from typing import Dict, Any, List
from datetime import datetime

# Import your existing services
from app.social_media.social_media_service import SocialMediaService
from app.ai.ai_service import AIService
from app.data.historical_data import HistoricalDataService

logger = logging.getLogger(__name__)

class PredictionService:
    """Enhanced prediction service with 4-source fallback logic."""
    
    def __init__(self):
        """Initialize the enhanced prediction service."""
        logger.info("Initializing enhanced prediction service")
        
        try:
            self.social_media_service = SocialMediaService()
            self.ai_service = AIService()
            self.historical_service = HistoricalDataService()
            
            logger.info("✅ Enhanced Prediction Service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing PredictionService: {e}")
            # Allow service to run with limited functionality
            self.social_media_service = None
            self.ai_service = None
            self.historical_service = None
    
    def predict_price_movement(self, ticker: str, timeframe: str = "1d", 
                             include_reddit: bool = True, include_posts: bool = True) -> Dict[str, Any]:
        """
        4-source prediction: Historical Data + Twitter + Reddit + AI Analysis
        Each source is attempted independently with individual error handling.
        """
        logger.info(f"🚀 Starting prediction for {ticker} using available sources")
        start_time = datetime.now()
        
        # SET GLOBAL TWITTER TIMEOUT START TIME
        global_twitter_start = time.time()
        if self.social_media_service:
            self.social_media_service.set_global_start_time(global_twitter_start)
            print(f"[DEBUG] Global Twitter timeout started at {time.strftime('%H:%M:%S', time.localtime(global_twitter_start))}")
        
        # Collect data from all 4 sources
        collected_data = self._collect_all_sources(ticker, timeframe, include_reddit, include_posts)
        
        # Generate prediction from available data
        prediction = self._generate_prediction(ticker, collected_data, start_time)
        
        return prediction
    
    def _collect_all_sources(self, ticker: str, timeframe: str, include_reddit: bool, include_posts: bool) -> Dict[str, Any]:
        """Collect data from all 4 sources with individual try/catch blocks."""
        data = {
            "historical": [],
            "twitter": [],
            "reddit": [],
            "ai_analysis": {},
            "successful_sources": []
        }
        
        # SOURCE 1: Historical Data
        try:
            if self.historical_service:
                days = {"1d": 30, "1w": 90, "1m": 365}.get(timeframe, 30)
                historical = self.historical_service.get_historical_data(ticker, days=days)
                if historical:
                    data["historical"] = historical
                    data["successful_sources"].append("historical")
                    logger.info(f"✅ Historical: {len(historical)} data points")
        except Exception as e:
            logger.warning(f"❌ Historical data failed: {e}")
        
        # SOURCE 2 & 3: Social Media (Twitter & Reddit) - delegated to SocialMediaService
        if include_posts and self.social_media_service:
            try:
                # Get Twitter posts
                twitter_posts = self.social_media_service.get_twitter_posts_only(ticker, limit=25)
                if twitter_posts:
                    data["twitter"] = twitter_posts
                    data["successful_sources"].append("twitter")
                    logger.info(f"✅ Twitter: {len(twitter_posts)} posts")
            except Exception as e:
                logger.warning(f"❌ Twitter failed: {e}")
            
            # Get Reddit posts
            if include_reddit:
                try:
                    reddit_posts = self.social_media_service.get_reddit_posts_only(ticker, limit=25)
                    if reddit_posts:
                        data["reddit"] = reddit_posts
                        data["successful_sources"].append("reddit")
                        logger.info(f"✅ Reddit: {len(reddit_posts)} posts")
                except Exception as e:
                    logger.warning(f"❌ Reddit failed: {e}")
        
        # SOURCE 4: AI Analysis (analyze collected data)
        try:
            if self.ai_service:
                all_posts = data["twitter"] + data["reddit"]
                if all_posts or data["historical"]:
                    ai_result = self.ai_service.analyze_social_media_impact(all_posts, ticker)
                    if ai_result and "ai_analysis" in ai_result:
                        data["ai_analysis"] = ai_result["ai_analysis"]
                        data["successful_sources"].append("ai_analysis")
                        logger.info("✅ AI analysis completed")
        except Exception as e:
            logger.warning(f"❌ AI analysis failed: {e}")
            # Fallback AI analysis
            data["ai_analysis"] = {
                "sentiment": "neutral",
                "impact": "minimal change",
                "confidence": "low",
                "reasoning": f"AI analysis failed: {str(e)}"
            }
        
        logger.info(f"📊 Successful sources: {data['successful_sources']}")
        return data
    
    def _generate_prediction(self, ticker: str, data: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """Generate final prediction from collected data."""
        successful_sources = data["successful_sources"]
        ai_analysis = data["ai_analysis"]
        
        # Base result structure
        result = {
            "ticker": ticker,
            "prediction_time": start_time.isoformat(),
            "timeframe": "1d",
            "prediction": {
                "direction": "hold",
                "confidence": 0.0,
                "reasoning": "No data available"
            },
            "supporting_data": {
                "sources_used": successful_sources,
                "total_posts_analyzed": len(data["twitter"]) + len(data["reddit"]),
                "historical_data_points": len(data["historical"]),
                "sentiment": ai_analysis.get("sentiment", "neutral")
            },
            "success": len(successful_sources) > 0
        }
        
        if not successful_sources:
            result["prediction"]["reasoning"] = "All data sources failed"
            return result
        
        # Extract AI insights
        sentiment = ai_analysis.get("sentiment", "neutral")
        impact = ai_analysis.get("impact", "minimal change")
        
        # Map sentiment + impact to direction
        if sentiment in ["very positive", "positive"] and "increase" in impact:
            direction = "buy"
        elif sentiment in ["very negative", "negative"] and "decrease" in impact:
            direction = "sell"
        else:
            direction = "hold"
        
        # Calculate confidence based on source count and data volume
        base_confidence = len(successful_sources) * 0.2  # 0.2 per source
        
        posts_count = len(data["twitter"]) + len(data["reddit"])
        if posts_count >= 15:
            base_confidence += 0.2
        elif posts_count >= 5:
            base_confidence += 0.1
        
        if len(data["historical"]) >= 20:
            base_confidence += 0.2
        elif len(data["historical"]) >= 10:
            base_confidence += 0.1
        
        confidence = min(base_confidence, 1.0)
        
        # Generate reasoning
        reasoning_parts = [f"Based on {len(successful_sources)} data sources"]
        if posts_count > 0:
            reasoning_parts.append(f"{posts_count} social media posts")
        if len(data["historical"]) > 0:
            reasoning_parts.append(f"{len(data['historical'])} historical data points")
        reasoning_parts.append(f"AI analysis: {sentiment} sentiment")
        
        result["prediction"] = {
            "direction": direction,
            "confidence": round(confidence, 2),
            "reasoning": "; ".join(reasoning_parts)
        }
        
        return result
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status for monitoring."""
        if not self.social_media_service:
            return {
                "overall_status": "error",
                "twitter_available": False,
                "reddit_available": False,
                "can_analyze": False
            }
        
        platform_status = self.social_media_service.get_platform_status()
        
        return {
            "overall_status": "operational" if (platform_status["twitter"]["operational"] or platform_status["reddit"]["operational"]) else "degraded",
            "twitter_available": platform_status["twitter"]["operational"],
            "reddit_available": platform_status["reddit"]["operational"],
            "can_analyze": True
        }
    
    def reset_failures(self):
        """Reset failure flags after cooldown period."""
        if self.social_media_service:
            self.social_media_service.reset_platform_status()
        logger.info("🔄 Platform failure flags reset")
    
    def get_available_tickers(self) -> Dict[str, Any]:
        """Get a list of available stock tickers that can be predicted."""
        return {
            "message": "All major US stock tickers are supported",
            "popular_tickers": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]
        }