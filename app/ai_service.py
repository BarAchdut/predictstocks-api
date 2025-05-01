import os
import logging
from typing import Dict, Any, List

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AIService:
    """Service for interacting with external AI APIs for sentiment and impact analysis."""
    
    def __init__(self):
        # Load API keys from environment variables
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.alternative_api_key = os.getenv("ALTERNATIVE_API_KEY")  # Like HuggingFace, Cohere, etc.
        
        # Validate API keys
        if not self.openai_api_key:
            logger.warning("OpenAI API key not found. Some features may be limited.")
    
    def analyze_social_media_impact(self, posts: List[Dict[str, Any]], ticker: str) -> Dict[str, Any]:
        """
        Analyze social media posts to determine potential impact on stock price.
        
        Args:
            posts: List of social media posts with metadata
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with sentiment analysis and predicted impact
        """
        try:
            # Format posts for API request
            formatted_posts = "\n".join([f"Post by {post.get('author', 'Unknown')}: {post.get('text', '')}" for post in posts])
            
            # Create prompt for the AI
            prompt = f"""
            Analyze the following social media posts about {ticker} stock and determine:
            1. The overall sentiment (very negative, negative, neutral, positive, very positive)
            2. The potential impact on stock price (significant decrease, moderate decrease, minimal change, moderate increase, significant increase)
            3. The confidence level of your prediction (low, medium, high)
            4. Key factors mentioned that could influence stock price
            
            Posts:
            {formatted_posts}
            
            Return your analysis in JSON format.
            """
            
            # Call OpenAI API
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",  # Or any other model you choose
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3  # Lower for more consistent responses
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Parse the AI response (assuming it returns valid JSON as requested)
            content = result["choices"][0]["message"]["content"]
            
            # You can add code here to process the response if the format doesn't match expectations
            
            return {
                "ai_analysis": content,
                "raw_response": result
            }
            
        except Exception as e:
            logger.error(f"Error analyzing social media posts: {e}")
            return {
                "error": str(e),
                "sentiment": "neutral",
                "impact": "minimal change",
                "confidence": "low"
            }
    
    def fine_tune_model(self, examples: List[Dict[str, Any]]) -> bool:
        """
        Optional: Fine-tune the AI model with stock-specific examples.
        
        Args:
            examples: Training examples with posts and known outcomes
            
        Returns:
            Success boolean
        """
        # Implementation of fine-tuning will be specific to the API you choose
        # Here would be code to format the data and send it to the API
        logger.info("Fine-tuning functionality is implemented but not active")
        return True