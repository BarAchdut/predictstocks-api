"""Main AI service for social media sentiment analysis."""

import logging
from typing import Dict, Any, List

from .openai_client import OpenAIClient
from .sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)

class AIService:
    """Service for interacting with external AI APIs for sentiment and impact analysis."""

    def __init__(self):
        self.openai_client = OpenAIClient()
        self.sentiment_analyzer = SentimentAnalyzer()

    def analyze_social_media_impact(self, posts: List[Dict[str, Any]], ticker: str) -> Dict[str, Any]:
        """Analyze social media posts for sentiment and potential stock impact."""
        try:
            if not posts:
                logger.warning(f"No posts provided for analysis of {ticker}")
                return {
                    "ai_analysis": {
                        "sentiment": "neutral",
                        "impact": "minimal change",
                        "confidence": "low",
                        "key_factors": ["No posts available for analysis"]
                    },
                    "raw_response": "No posts to analyze",
                    "posts_analyzed": 0,
                    "posts_shown_to_ai": 0
                }

            # Create analysis prompt
            prompt_data = self.sentiment_analyzer.create_analysis_prompt(posts, ticker)
            
            # Get AI analysis
            raw_response = self.openai_client.analyze_text(
                prompt_data["user_prompt"], 
                prompt_data["system_message"]
            )
            
            logger.info(f"AI analysis completed for {ticker}")

            # Parse and validate response
            ai_analysis = self.sentiment_analyzer.parse_ai_response(raw_response)

            return {
                "ai_analysis": ai_analysis,
                "raw_response": raw_response,
                "posts_analyzed": len(posts),
                "posts_shown_to_ai": min(len(posts), 15)
            }

        except Exception as e:
            logger.error(f"Error analyzing social media posts: {e}")
            
            fallback_analysis = self.sentiment_analyzer.create_fallback_analysis(str(e))
            
            return {
                "error": str(e),
                "ai_analysis": fallback_analysis,
                "posts_analyzed": len(posts) if posts else 0,
                "posts_shown_to_ai": 0
            }

    def fine_tune_model(self, examples: List[Dict[str, Any]]) -> bool:
        """Fine-tuning method (placeholder for future implementation)."""
        logger.info("Fine-tuning is not implemented in this version")
        return False

    def get_model_capabilities(self) -> Dict[str, Any]:
        """Get information about available models and capabilities."""
        return self.openai_client.get_model_capabilities()

    def test_connection(self) -> Dict[str, Any]:
        """Test the OpenAI API connection."""
        return self.openai_client.test_connection()
    
    def is_configured(self) -> bool:
        """Check if AI service is properly configured."""
        return self.openai_client.is_configured()