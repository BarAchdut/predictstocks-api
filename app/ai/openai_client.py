"""OpenAI client with retry logic and error handling."""

import os
import logging
import time
from typing import Dict, Any

from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    print("Please install openai>=1.0.0: pip install openai>=1.0.0")
    raise

load_dotenv()

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Client for OpenAI API with robust error handling."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = 'gpt-4o-mini'
        self.max_tokens = 1000
        self.temperature = 0.3
        self.max_retries = 2
        self.retry_delay = 1.0
    
    def is_configured(self) -> bool:
        """Check if OpenAI client is properly configured."""
        return bool(self.api_key)
    
    def analyze_text(self, prompt: str, system_message: str = None) -> str:
        """Send analysis request to OpenAI with retry logic."""
        for attempt in range(self.max_retries):
            try:
                messages = []
                
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                
                messages.append({"role": "user", "content": prompt})
                
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
                logger.warning(f"OpenAI attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    time.sleep(wait_time)
                else:
                    logger.error(f"OpenAI failed after {self.max_retries} attempts: {e}")
                    raise
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the OpenAI API connection."""
        try:
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