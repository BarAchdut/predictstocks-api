import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.prediction_service import PredictionService
from app.social_media_service import SocialMediaService
from app.ai_service import AIService
from app.data.historical_data import HistoricalDataService
from app.utils.price_prediction import calculate_technical_prediction, combine_predictions

logger = logging.getLogger(__name__)

class AIPredictionService(PredictionService):
    """Enhanced prediction service using AI for social media sentiment analysis."""
    
    def __init__(self):
        super().__init__()
        self.social_media_service = SocialMediaService()
        self.ai_service = AIService()
        self.historical_service = HistoricalDataService()
    
    def predict_price_movement(self, ticker: str, timeframe: str = "1d") -> Dict[str, Any]:
        """
        Predict stock price movement based on technical indicators and social media sentiment.
        
        Args:
            ticker: Stock ticker symbol
            timeframe: Timeframe for prediction ("1d", "1w", "1m")
            
        Returns:
            Dictionary with prediction results
        """
        # Get historical data for technical analysis
        historical_data = self.historical_service.get_historical_data(ticker, days=30)
        
        # Get social media posts about the ticker
        social_posts = self.social_media_service.get_posts_for_ticker(ticker, limit=50)
        
        # Get additional posts from known influencers
        influencer_posts = self.social_media_service.get_influencer_posts(ticker)
        all_posts = social_posts + influencer_posts
        
        # Use AI to analyze sentiment and predict impact
        ai_analysis = self.ai_service.analyze_social_media_impact(all_posts, ticker)
        
        # Calculate technical indicators
        technical_signals = self._calculate_technical_indicators(historical_data)
        
        # Combine technical analysis with AI sentiment analysis
        prediction = self._combine_signals(technical_signals, ai_analysis)
        
        # Calculate prediction confidence
        confidence = self._calculate_confidence(prediction, ai_analysis, technical_signals)
        
        # Get current price
        current_price = technical_signals.get("latest_price", 0)
        
        # Calculate technical prediction using linear regression
        prediction_days = 1
        if timeframe == "1w":
            prediction_days = 7
        elif timeframe == "1m":
            prediction_days = 30
            
        technical_prediction = calculate_technical_prediction(historical_data, prediction_days)
        
        # Combine AI and technical predictions
        combined_prediction = combine_predictions(
            ai_prediction={"prediction": prediction, "confidence": confidence},
            technical_prediction=technical_prediction,
            current_price=current_price
        )
        
        # Add the predicted price to the result
        result = {
            "ticker": ticker,
            "prediction_time": datetime.now().isoformat(),
            "timeframe": timeframe,
            "prediction": prediction,
            "technical_signals": technical_signals,
            "sentiment_analysis": ai_analysis.get("ai_analysis"),
            "confidence": confidence,
            "predicted_price": combined_prediction.get("predicted_price"),
            "supporting_data": {
                "post_count": len(all_posts),
                "influencer_post_count": len(influencer_posts),
                "technical_prediction": technical_prediction,
                "combined_prediction_details": combined_prediction
            }
        }
        
        return result
    
    def _calculate_technical_indicators(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate technical indicators from historical price data."""
        # Here would be code to calculate technical indicators such as:
        # - Moving averages
        # - Momentum
        # - Oscillators
        
        # Simple example:
        if len(historical_data) < 2:
            return {"trend": "neutral"}
            
        latest_price = historical_data[-1].get("close", 0)
        previous_price = historical_data[-2].get("close", 0)
        
        trend = "neutral"
        if latest_price > previous_price:
            trend = "up"
        elif latest_price < previous_price:
            trend = "down"
            
        return {
            "trend": trend,
            "latest_price": latest_price,
            "price_change": latest_price - previous_price,
            "price_change_percent": ((latest_price - previous_price) / previous_price) * 100 if previous_price else 0
        }
    
    def _combine_signals(self, technical_signals: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Combine technical signals with AI sentiment analysis."""
        # Here would be logic to combine signals
        # Simple example:
        
        # Assume the AI provides analysis in a certain JSON format
        sentiment = "neutral"
        impact = "minimal change"
        
        # Try to extract sentiment and impact from AI response
        try:
            ai_result = ai_analysis.get("ai_analysis", {})
            if isinstance(ai_result, str):
                # Try to parse the response if it's a JSON string
                import json
                ai_result = json.loads(ai_result)
                
            sentiment = ai_result.get("sentiment", "neutral")
            impact = ai_result.get("impact", "minimal change")
        except Exception as e:
            logger.error(f"Error parsing AI analysis: {e}")
        
        # Simple combination of technical signals with sentiment analysis
        technical_trend = technical_signals.get("trend", "neutral")
        
        if technical_trend == "up" and sentiment in ["positive", "very positive"]:
            prediction = "strong_buy"
        elif technical_trend == "up" or sentiment in ["positive", "very positive"]:
            prediction = "buy"
        elif technical_trend == "down" and sentiment in ["negative", "very negative"]:
            prediction = "strong_sell"
        elif technical_trend == "down" or sentiment in ["negative", "very negative"]:
            prediction = "sell"
        else:
            prediction = "hold"
            
        return {
            "direction": prediction,
            "expected_impact": impact,
            "technical_trend": technical_trend,
            "sentiment": sentiment
        }
        
    def _calculate_confidence(self, prediction: Dict[str, Any], ai_analysis: Dict[str, Any], technical_signals: Dict[str, Any]) -> float:
        """Calculate confidence level for the prediction."""
        # Simple example:
        try:
            ai_result = ai_analysis.get("ai_analysis", {})
            if isinstance(ai_result, str):
                import json
                ai_result = json.loads(ai_result)
                
            ai_confidence = ai_result.get("confidence", "medium")
            
            # Convert from verbal to numeric
            confidence_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
            return confidence_map.get(ai_confidence, 0.5)
            
        except Exception:
            # Default
            return 0.5