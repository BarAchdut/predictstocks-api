# import logging
# from typing import Dict, Any, List
# from datetime import datetime, timedelta

# from app.prediction_service import PredictionService
# from app.social_media import SocialMediaService
# from app.ai import AIService
# from app.data.historical_data import HistoricalDataService
# from app.utils.price_prediction import calculate_technical_prediction, combine_predictions

# logger = logging.getLogger(__name__)

# class AIPredictionService(PredictionService):
#     """Enhanced prediction service using AI for social media sentiment analysis."""

#     def __init__(self):
#         super().__init__()
#         self.social_media_service = SocialMediaService()
#         self.ai_service = AIService()
#         self.historical_service = HistoricalDataService()

#     def predict_price_movement(self, ticker: str, timeframe: str = "1d", include_reddit: bool = True) -> Dict[str, Any]:
#         """
#         Predict stock price movement based on technical indicators and social media sentiment.

#         Args:
#             ticker: Stock ticker symbol
#             timeframe: Timeframe for prediction ("1d", "1w", "1m")
#             include_reddit: Whether to include Reddit posts in the analysis

#         Returns:
#             Dictionary with prediction results
#         """
#         try:
#             logger.info(f"Starting prediction for {ticker} with timeframe {timeframe}")
            
#             # Get historical data for technical analysis
#             historical_data = self.historical_service.get_historical_data(ticker, days=30)
#             logger.info(f"Retrieved {len(historical_data)} historical data points for {ticker}")

#             # Get social media posts about the ticker
#             social_posts = self.social_media_service.get_posts_for_ticker(
#                 ticker, 
#                 limit=50, 
#                 include_reddit=include_reddit
#             )
#             logger.info(f"Retrieved {len(social_posts)} social media posts for {ticker}")

#             # Get additional posts from known influencers and high-quality sources
#             influencer_posts = self.social_media_service.get_influencer_posts(ticker)
#             logger.info(f"Retrieved {len(influencer_posts)} influencer posts for {ticker}")
            
#             # Combine all posts
#             all_posts = social_posts + influencer_posts
            
#             # Remove duplicates based on post ID
#             unique_posts = self._remove_duplicate_posts(all_posts)
#             logger.info(f"After deduplication: {len(unique_posts)} unique posts for analysis")

#             # Use AI to analyze sentiment and predict impact
#             ai_analysis = self.ai_service.analyze_social_media_impact(unique_posts, ticker)
#             logger.info(f"AI analysis completed for {ticker}")

#             # Calculate technical indicators
#             technical_signals = self._calculate_technical_indicators(historical_data)

#             # Combine technical analysis with AI sentiment analysis
#             prediction = self._combine_signals(technical_signals, ai_analysis)

#             # Calculate prediction confidence
#             confidence = self._calculate_confidence(prediction, ai_analysis, technical_signals, len(unique_posts))

#             # Get current price
#             current_price = technical_signals.get("latest_price", 0)

#             # Calculate technical prediction using linear regression
#             prediction_days = 1
#             if timeframe == "1w":
#                 prediction_days = 7
#             elif timeframe == "1m":
#                 prediction_days = 30

#             technical_prediction = calculate_technical_prediction(historical_data, prediction_days)

#             # Combine AI and technical predictions
#             combined_prediction = combine_predictions(
#                 ai_prediction={"prediction": prediction, "confidence": confidence},
#                 technical_prediction=technical_prediction,
#                 current_price=current_price
#             )

#             # Create detailed result
#             result = {
#                 "ticker": ticker,
#                 "prediction_time": datetime.now().isoformat(),
#                 "timeframe": timeframe,
#                 "prediction": prediction,
#                 "technical_signals": technical_signals,
#                 "sentiment_analysis": ai_analysis.get("ai_analysis", {}),
#                 "confidence": confidence,
#                 "predicted_price": combined_prediction.get("predicted_price"),
#                 "supporting_data": {
#                     "total_posts_analyzed": len(unique_posts),
#                     "social_posts": len(social_posts),
#                     "influencer_posts": len(influencer_posts),
#                     "reddit_included": include_reddit,
#                     "technical_prediction": technical_prediction,
#                     "combined_prediction_details": combined_prediction,
#                     "data_quality": self._assess_data_quality(unique_posts, historical_data)
#                 },
#                 "raw_ai_response": ai_analysis.get("raw_response", ""),
#                 "analysis_timestamp": datetime.now().isoformat()
#             }

#             logger.info(f"Prediction completed for {ticker}: {prediction.get('direction', 'unknown')}")
#             return result

#         except Exception as e:
#             logger.error(f"Error in predict_price_movement for {ticker}: {e}")
#             return {
#                 "ticker": ticker,
#                 "prediction_time": datetime.now().isoformat(),
#                 "timeframe": timeframe,
#                 "error": str(e),
#                 "prediction": {
#                     "direction": "hold",
#                     "expected_impact": "minimal change",
#                     "technical_trend": "neutral",
#                     "sentiment": "neutral"
#                 },
#                 "confidence": 0.1,
#                 "supporting_data": {
#                     "error_occurred": True,
#                     "error_details": str(e)
#                 }
#             }

#     def _remove_duplicate_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#         """Remove duplicate posts based on ID and content similarity."""
#         seen_ids = set()
#         seen_content = set()
#         unique_posts = []

#         for post in posts:
#             post_id = post.get('id')
#             post_content = post.get('text', '')[:100]  # First 100 characters for similarity check
            
#             # Skip if we've seen this ID or very similar content
#             if post_id and post_id in seen_ids:
#                 continue
#             if post_content and post_content in seen_content:
#                 continue
            
#             # Add to unique posts
#             unique_posts.append(post)
#             if post_id:
#                 seen_ids.add(post_id)
#             if post_content:
#                 seen_content.add(post_content)

#         return unique_posts

#     def _assess_data_quality(self, posts: List[Dict[str, Any]], historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
#         """Assess the quality of data available for prediction."""
#         return {
#             "posts_quality": {
#                 "total_posts": len(posts),
#                 "has_influencer_posts": any(post.get('author_type') == 'influencer' for post in posts),
#                 "has_high_quality_sources": any(post.get('author_type') == 'high_quality_subreddit' for post in posts),
#                 "platform_diversity": len(set(post.get('platform') for post in posts)),
#                 "recent_posts": len([p for p in posts if self._is_recent_post(p)])
#             },
#             "technical_data_quality": {
#                 "historical_points": len(historical_data),
#                 "has_sufficient_data": len(historical_data) >= 10,
#                 "data_recency": "recent" if historical_data else "none"
#             }
#         }

#     def _is_recent_post(self, post: Dict[str, Any]) -> bool:
#         """Check if a post is from the last 24 hours."""
#         try:
#             post_date = post.get('date')
#             if not post_date:
#                 return False
            
#             if isinstance(post_date, str):
#                 post_datetime = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
#             else:
#                 post_datetime = post_date
            
#             return datetime.now() - post_datetime.replace(tzinfo=None) < timedelta(hours=24)
#         except:
#             return False

#     def _calculate_technical_indicators(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
#         """Calculate technical indicators from historical price data."""
#         if len(historical_data) < 2:
#             logger.warning("Insufficient historical data for technical analysis")
#             return {
#                 "trend": "neutral",
#                 "latest_price": 0,
#                 "price_change": 0,
#                 "price_change_percent": 0,
#                 "data_quality": "insufficient"
#             }

#         latest_price = historical_data[-1].get("close", 0)
#         previous_price = historical_data[-2].get("close", 0)

#         # Calculate trend
#         trend = "neutral"
#         if latest_price > previous_price:
#             trend = "up"
#         elif latest_price < previous_price:
#             trend = "down"

#         # Calculate additional technical indicators if we have enough data
#         additional_indicators = {}
#         if len(historical_data) >= 5:
#             # Simple moving average trend
#             recent_prices = [data.get("close", 0) for data in historical_data[-5:]]
#             sma_5 = sum(recent_prices) / len(recent_prices)
#             additional_indicators["sma_5"] = sma_5
#             additional_indicators["price_vs_sma"] = "above" if latest_price > sma_5 else "below"

#         return {
#             "trend": trend,
#             "latest_price": latest_price,
#             "price_change": latest_price - previous_price,
#             "price_change_percent": ((latest_price - previous_price) / previous_price) * 100 if previous_price else 0,
#             "data_quality": "good" if len(historical_data) >= 10 else "limited",
#             **additional_indicators
#         }

#     def _combine_signals(self, technical_signals: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
#         """Combine technical signals with AI sentiment analysis."""
#         sentiment = "neutral"
#         impact = "minimal change"
#         reasoning = []

#         try:
#             ai_result = ai_analysis.get("ai_analysis", {})
#             if isinstance(ai_result, str):
#                 import json
#                 ai_result = json.loads(ai_result)

#             sentiment = ai_result.get("sentiment", "neutral")
#             impact = ai_result.get("impact", "minimal change")
            
#             # Extract reasoning from AI analysis
#             if "reasoning" in ai_result:
#                 reasoning.append(f"AI: {ai_result['reasoning']}")
#             if "key_factors" in ai_result and ai_result["key_factors"]:
#                 reasoning.append(f"Key factors: {', '.join(ai_result['key_factors'][:3])}")

#         except Exception as e:
#             logger.error(f"Error parsing AI analysis: {e}")
#             reasoning.append("AI analysis parsing failed")

#         technical_trend = technical_signals.get("trend", "neutral")
        
#         # Add technical reasoning
#         if technical_trend != "neutral":
#             price_change_pct = technical_signals.get("price_change_percent", 0)
#             reasoning.append(f"Technical: {technical_trend} trend ({price_change_pct:.1f}% change)")

#         # Enhanced prediction logic
#         if technical_trend == "up" and sentiment in ["positive", "very positive"]:
#             prediction = "strong_buy"
#             reasoning.append("Both technical and sentiment signals are positive")
#         elif technical_trend == "up" or sentiment in ["positive", "very positive"]:
#             prediction = "buy"
#             reasoning.append("Either technical or sentiment signal is positive")
#         elif technical_trend == "down" and sentiment in ["negative", "very negative"]:
#             prediction = "strong_sell"
#             reasoning.append("Both technical and sentiment signals are negative")
#         elif technical_trend == "down" or sentiment in ["negative", "very negative"]:
#             prediction = "sell"
#             reasoning.append("Either technical or sentiment signal is negative")
#         else:
#             prediction = "hold"
#             reasoning.append("Mixed or neutral signals")

#         return {
#             "direction": prediction,
#             "expected_impact": impact,
#             "technical_trend": technical_trend,
#             "sentiment": sentiment,
#             "reasoning": reasoning
#         }

#     def _calculate_confidence(self, prediction: Dict[str, Any], ai_analysis: Dict[str, Any], 
#                            technical_signals: Dict[str, Any], post_count: int) -> float:
#         """Calculate confidence level for the prediction with improved logic."""
#         base_confidence = 0.5
#         confidence_adjustments = []

#         try:
#             # AI confidence factor
#             ai_result = ai_analysis.get("ai_analysis", {})
#             if isinstance(ai_result, str):
#                 import json
#                 ai_result = json.loads(ai_result)

#             ai_confidence = ai_result.get("confidence", "medium")
#             confidence_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
#             ai_conf_score = confidence_map.get(ai_confidence, 0.5)
            
#             # Data quality factor
#             data_quality_factor = min(1.0, post_count / 20)  # Max confidence at 20+ posts
#             technical_quality = 1.0 if technical_signals.get("data_quality") == "good" else 0.7
            
#             # Signal alignment factor
#             alignment_factor = 1.0
#             if prediction.get("direction") in ["strong_buy", "strong_sell"]:
#                 alignment_factor = 1.2  # Higher confidence for aligned signals
#             elif prediction.get("direction") == "hold":
#                 alignment_factor = 0.8   # Lower confidence for mixed signals

#             # Calculate final confidence
#             final_confidence = (
#                 base_confidence * 0.3 +
#                 ai_conf_score * 0.4 +
#                 data_quality_factor * 0.2 +
#                 technical_quality * 0.1
#             ) * alignment_factor

#             # Ensure confidence is between 0.1 and 0.95
#             final_confidence = max(0.1, min(0.95, final_confidence))
            
#             confidence_adjustments.append(f"AI: {ai_confidence} ({ai_conf_score:.2f})")
#             confidence_adjustments.append(f"Data: {post_count} posts ({data_quality_factor:.2f})")
#             confidence_adjustments.append(f"Alignment: {alignment_factor:.2f}")
            
#             logger.debug(f"Confidence calculation: {confidence_adjustments} = {final_confidence:.2f}")
            
#             return round(final_confidence, 2)

#         except Exception as e:
#             logger.error(f"Error calculating confidence: {e}")
#             return 0.4  # Conservative fallback

#     def get_service_status(self) -> Dict[str, Any]:
#         """Get status of all underlying services."""
#         try:
#             # Test social media service
#             social_status = self.social_media_service.get_platform_status()
            
#             # Test AI service
#             ai_test = self.ai_service.test_connection()
#             ai_status = ai_test.get("status") == "success"
            
#             return {
#                 "social_media": social_status,
#                 "ai_service": {
#                     "operational": ai_status,
#                     "details": ai_test
#                 },
#                 "historical_data": {
#                     "operational": True  # Assume operational if no errors
#                 },
#                 "overall_status": "operational" if ai_status and any(social_status.values()) else "limited"
#             }
#         except Exception as e:
#             logger.error(f"Error getting service status: {e}")
#             return {
#                 "error": str(e),
#                 "overall_status": "error"
#             }