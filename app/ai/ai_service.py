"""Main AI service for social media sentiment analysis with fallback handling."""

import logging
from typing import Dict, Any, List

from .openai_client import OpenAIClient
from .sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI analysis with robust error handling."""

    def __init__(self):
        try:
            self.openai_client = OpenAIClient()
            self.sentiment_analyzer = SentimentAnalyzer()
            logger.info("✅ AI Service initialized successfully")
        except Exception as e:
            logger.error(f"❌ AI Service initialization failed: {e}")
            self.openai_client = None
            self.sentiment_analyzer = SentimentAnalyzer()

    def analyze_social_media_impact(self, posts: List[Dict[str, Any]], ticker: str) -> Dict[str, Any]:
        """Analyze social media posts with fallback for failures."""
        try:
            if not posts:
                logger.warning(f"No posts provided for analysis of {ticker}")
                return self._create_fallback_response("No posts available", 0)

            if not self.openai_client:
                logger.warning("OpenAI client not available, using fallback analysis")
                return self._create_fallback_response("OpenAI service unavailable", len(posts))

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
            return self._create_fallback_response(str(e), len(posts) if posts else 0)

    def _create_fallback_response(self, error_reason: str, posts_count: int) -> Dict[str, Any]:
        """Create fallback response when AI analysis fails."""
        fallback_analysis = {
            "sentiment": "neutral",
            "impact": "minimal change",
            "confidence": "low",
            "key_factors": ["AI analysis unavailable"],
            "patterns": [],
            "reasoning": f"Fallback analysis: {error_reason}"
        }
        
        return {
            "ai_analysis": fallback_analysis,
            "error": error_reason,
            "posts_analyzed": posts_count,
            "posts_shown_to_ai": 0
        }

    def test_connection(self) -> Dict[str, Any]:
        """Test AI service connection."""
        if not self.openai_client:
            return {
                "status": "error",
                "message": "OpenAI client not initialized"
            }
        
        return self.openai_client.test_connection()
    
    def is_configured(self) -> bool:
        """Check if AI service is properly configured."""
        return self.openai_client is not None and self.openai_client.is_configured()

    def get_model_capabilities(self) -> Dict[str, Any]:
        """Get information about AI capabilities."""
        if not self.openai_client:
            return {"status": "unavailable"}
        
        return self.openai_client.get_model_capabilities()