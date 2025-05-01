# app/ai_service.py
import os
import logging
from typing import Dict, Any, List
import json

import requests
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AIService:
    """Service for interacting with external AI APIs for sentiment and impact analysis."""
    
    def __init__(self):
        # Load API keys from environment variables
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.alternative_api_key = os.getenv("ALTERNATIVE_API_KEY")  # Like HuggingFace, Cohere, etc.
        
        # Configure Gemini API
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
        else:
            logger.warning("Gemini API key not found. Some features may be limited.")
    
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
            
            if not self.gemini_api_key:
                logger.error("Gemini API key not available")
                return {
                    "error": "API key not configured",
                    "sentiment": "neutral",
                    "impact": "minimal change",
                    "confidence": "low"
                }
                
            # Call Gemini API
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            
            # Parse the response
            content = response.text
            
            # Try to extract JSON from the response
            try:
                # Check if the response is already valid JSON
                parsed_content = json.loads(content)
            except json.JSONDecodeError:
                # If not, try to extract JSON from the text
                try:
                    # Look for content between ```json and ``` markers
                    import re
                    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
                    if json_match:
                        parsed_content = json.loads(json_match.group(1))
                    else:
                        # Try to find anything that looks like JSON
                        json_match = re.search(r'({[\s\S]*})', content)
                        if json_match:
                            parsed_content = json.loads(json_match.group(1))
                        else:
                            # If all else fails, create a simple structure with the raw text
                            parsed_content = {
                                "raw_response": content,
                                "sentiment": "neutral",
                                "impact": "minimal change",
                                "confidence": "medium"
                            }
                except Exception as e:
                    logger.error(f"Error extracting JSON from response: {e}")
                    parsed_content = {
                        "raw_response": content,
                        "sentiment": "neutral",
                        "impact": "minimal change",
                        "confidence": "medium"
                    }
            
            return {
                "ai_analysis": parsed_content,
                "raw_response": content
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
        Note: Gemini does not currently support fine-tuning via API.
        
        Args:
            examples: Training examples with posts and known outcomes
            
        Returns:
            Success boolean
        """
        logger.info("Fine-tuning is not currently supported with Gemini API")
        return False
        
    def get_model_capabilities(self) -> Dict[str, Any]:
        """
        Get information about the AI model's capabilities.
        
        Returns:
            Dictionary with model information
        """
        try:
            if not self.gemini_api_key:
                return {"error": "API key not configured"}
                
            # List available models
            models = genai.list_models()
            available_models = [
                {
                    "name": model.name,
                    "display_name": model.display_name,
                    "description": model.description,
                    "input_token_limit": getattr(model, "input_token_limit", None),
                    "output_token_limit": getattr(model, "output_token_limit", None),
                    "supported_generation_methods": getattr(model, "supported_generation_methods", []),
                }
                for model in models
                if "gemini" in model.name.lower()
            ]
            
            return {
                "available_models": available_models,
                "current_model": "gemini-pro",
                "capabilities": [
                    "text analysis",
                    "sentiment analysis",
                    "structured data extraction",
                    "reasoning"
                ]
            }
        except Exception as e:
            logger.error(f"Error retrieving model capabilities: {e}")
            return {"error": str(e)}