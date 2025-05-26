"""OpenAI client for AI-powered text analysis."""

import os
import logging
from typing import Dict, Any

from dotenv import load_dotenv

# Updated OpenAI import for version 1.0+
try:
    from openai import OpenAI
except ImportError:
    print("Please install openai>=1.0.0: pip install openai>=1.0.0")
    raise

load_dotenv()

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Client for OpenAI API interactions."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OpenAI API key is required")
        
        # Initialize OpenAI client (new syntax for v1.0+)
        self.client = OpenAI(api_key=self.api_key)
        self.model = 'gpt-4o-mini'  # Current recommended model
        self.max_tokens = 1000
        self.temperature = 0.3
    
    def is_configured(self) -> bool:
        """Check if OpenAI client is properly configured."""
        return bool(self.api_key)
    
    def analyze_text(self, prompt: str, system_message: str = None) -> str:
        """
        Send a text analysis request to OpenAI.
        
        Args:
            prompt: The user prompt to analyze
            system_message: Optional system message for context
            
        Returns:
            Raw response content from OpenAI
        """
        try:
            messages = []
            
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            messages.append({"role": "user", "content": prompt})
            
            # Use new OpenAI client syntax
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,  
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content.strip()
            logger.debug(f"OpenAI response received: {len(content)} characters")
            
            return content
            
        except Exception as e:
            logger.error(f"Error in OpenAI API call: {e}")
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the OpenAI API connection."""
        try:
            # Make a simple test request
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Hello, this is a test. Please respond with 'OK'."}
                ],
                max_tokens=10
            )
            
            content = response.choices[0].message.content.strip()
            
            return {
                "status": "success",
                "message": "OpenAI API connection successful",
                "response": content,
                "model_used": self.model
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "message": f"OpenAI API connection failed: {str(e)}",
                "error": str(e)
            }
    
    def get_model_capabilities(self) -> Dict[str, Any]:
        """Get information about available models and capabilities."""
        return {
            "available_models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            "current_model": self.model,
            "capabilities": [
                "text analysis",
                "sentiment analysis",
                "structured data extraction", 
                "reasoning",
                "financial analysis"
            ],
            "api_version": "1.0+",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }