"""Sentiment analysis and response processing for social media posts."""

import json
import logging
import re
import time
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Handles sentiment analysis and response processing."""
    
    def __init__(self):
        print("[DEBUG] Initializing SentimentAnalyzer...")
        start_time = time.time()
        
        self.valid_sentiments = ["very negative", "negative", "neutral", "positive", "very positive"]
        self.valid_impacts = ["significant decrease", "moderate decrease", "minimal change", 
                             "moderate increase", "significant increase"]
        self.valid_confidences = ["low", "medium", "high"]
        
        init_time = time.time() - start_time
        print(f"[DEBUG] SentimentAnalyzer initialized in {init_time:.3f} seconds")
    
    def create_analysis_prompt(self, posts: List[Dict[str, Any]], ticker: str) -> Dict[str, str]:
        """Create structured prompt for sentiment analysis."""
        print(f"[DEBUG] Creating analysis prompt for {ticker} with {len(posts)} posts")
        
        if not posts:
            print("[DEBUG] No posts available for analysis - returning neutral prompt")
            return {
                "system_message": "You are a financial analyst AI.",
                "user_prompt": f"No posts available for analysis of {ticker}. Provide neutral analysis."
            }
        
        # Format posts for analysis (limit to avoid token limits)
        formatted_posts = "\n".join([
            f"Post by {post.get('author', 'Unknown')} ({post.get('platform', 'unknown')}): {post.get('text', '')[:500]}" 
            for post in posts[:15]  # Limit to 15 posts
        ])
        
        system_message = (
            "You are a financial analyst AI specializing in social media sentiment analysis "
            "for stock prediction. Provide accurate, unbiased analysis based on the provided data."
        )
        
        user_prompt = f"""
        Analyze the following social media posts about {ticker} stock and determine:
        1. The overall sentiment (very negative, negative, neutral, positive, very positive)
        2. The potential impact on stock price (significant decrease, moderate decrease, minimal change, moderate increase, significant increase)
        3. The confidence level of your prediction (low, medium, high)
        4. Key factors mentioned that could influence stock price (list of specific factors)
        5. Notable patterns or trends in the discussion

        Posts ({len(posts)} total, showing first {min(len(posts), 15)}):
        {formatted_posts}

        Please return your analysis in the following JSON format:
        {{
            "sentiment": "one of: very negative, negative, neutral, positive, very positive",
            "impact": "one of: significant decrease, moderate decrease, minimal change, moderate increase, significant increase",
            "confidence": "one of: low, medium, high",
            "key_factors": ["list", "of", "key", "factors"],
            "patterns": ["notable", "patterns", "or", "trends"],
            "reasoning": "Brief explanation of your analysis"
        }}
        """
        
        print(f"[DEBUG] Analysis prompt created, length: {len(user_prompt)} characters")
        
        return {
            "system_message": system_message,
            "user_prompt": user_prompt
        }
    
    def parse_ai_response(self, raw_response: str) -> Dict[str, Any]:
        """Parse and validate AI response into structured format."""
        print("[DEBUG] Parsing AI response...")
        print(f"[DEBUG] Raw response length: {len(raw_response)} characters")
        
        try:
            # Try direct JSON parsing first
            parsed_content = json.loads(raw_response)
            print(f"[DEBUG] Successfully parsed JSON response")
            logger.debug("Successfully parsed JSON response")
            
        except json.JSONDecodeError:
            print("[DEBUG] Direct JSON parsing failed, trying extraction methods...")
            try:
                # Try to extract JSON from markdown code blocks
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', raw_response)
                if json_match:
                    parsed_content = json.loads(json_match.group(1))
                    print(f"[DEBUG] Extracted JSON from markdown block")
                else:
                    # Try to find JSON object in the response
                    json_match = re.search(r'({[\s\S]*})', raw_response)
                    if json_match:
                        parsed_content = json.loads(json_match.group(1))
                        print(f"[DEBUG] Extracted JSON from response text")
                    else:
                        # Fallback: create structured response from unstructured content
                        print("[DEBUG] JSON extraction failed, using unstructured parsing fallback")
                        parsed_content = self._parse_unstructured_response(raw_response)
                        
            except Exception as e:
                print(f"[DEBUG] Error extracting JSON from response: {e}")
                logger.error(f"Error extracting JSON from response: {e}")
                parsed_content = self._parse_unstructured_response(raw_response)
        
        # Validate and normalize the response
        validated_response = self._validate_and_normalize_response(parsed_content)
        
        print(f"[DEBUG] AI response parsing completed")
        print(f"[DEBUG] Parsed sentiment: {validated_response.get('sentiment')}")
        print(f"[DEBUG] Parsed impact: {validated_response.get('impact')}")
        print(f"[DEBUG] Parsed confidence: {validated_response.get('confidence')}")
        
        return validated_response
    
    def _parse_unstructured_response(self, content: str) -> Dict[str, Any]:
        """Parse unstructured AI response into structured format."""
        print("[DEBUG] Parsing unstructured response...")
        
        result = {
            "sentiment": "neutral",
            "impact": "minimal change", 
            "confidence": "medium",
            "key_factors": [],
            "patterns": [],
            "reasoning": content[:200] + "..." if len(content) > 200 else content
        }
        
        content_lower = content.lower()
        
        # Extract sentiment
        if any(word in content_lower for word in ["very positive", "extremely positive"]):
            result["sentiment"] = "very positive"
        elif "positive" in content_lower:
            result["sentiment"] = "positive"
        elif any(word in content_lower for word in ["very negative", "extremely negative"]):
            result["sentiment"] = "very negative"
        elif "negative" in content_lower:
            result["sentiment"] = "negative"
        
        # Extract impact
        if any(phrase in content_lower for phrase in ["significant increase", "major increase"]):
            result["impact"] = "significant increase"
        elif any(phrase in content_lower for phrase in ["moderate increase", "slight increase"]):
            result["impact"] = "moderate increase"
        elif any(phrase in content_lower for phrase in ["significant decrease", "major decrease"]):
            result["impact"] = "significant decrease"
        elif any(phrase in content_lower for phrase in ["moderate decrease", "slight decrease"]):
            result["impact"] = "moderate decrease"
        
        # Extract confidence
        if "high confidence" in content_lower or "very confident" in content_lower:
            result["confidence"] = "high"
        elif "low confidence" in content_lower or "uncertain" in content_lower:
            result["confidence"] = "low"
        
        return result
    
    def _validate_and_normalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize AI response to ensure consistency."""
        print("[DEBUG] Validating and normalizing response...")
        
        # Normalize sentiment
        sentiment = str(response.get("sentiment", "neutral")).lower()
        if sentiment not in self.valid_sentiments:
            if "very" in sentiment and "positive" in sentiment:
                sentiment = "very positive"
            elif "very" in sentiment and "negative" in sentiment:
                sentiment = "very negative"
            elif "positive" in sentiment:
                sentiment = "positive"
            elif "negative" in sentiment:
                sentiment = "negative"
            else:
                sentiment = "neutral"
        
        # Normalize impact
        impact = str(response.get("impact", "minimal change")).lower()
        if impact not in self.valid_impacts:
            if "significant" in impact and ("increase" in impact or "up" in impact):
                impact = "significant increase"
            elif "significant" in impact and ("decrease" in impact or "down" in impact):
                impact = "significant decrease"
            elif "moderate" in impact and ("increase" in impact or "up" in impact):
                impact = "moderate increase"
            elif "moderate" in impact and ("decrease" in impact or "down" in impact):
                impact = "moderate decrease"
            else:
                impact = "minimal change"
        
        # Normalize confidence
        confidence = str(response.get("confidence", "medium")).lower()
        if confidence not in self.valid_confidences:
            confidence = "medium"
        
        # Validate other fields
        key_factors = response.get("key_factors", [])
        patterns = response.get("patterns", [])
        reasoning = response.get("reasoning", "Analysis completed")
        
        if not isinstance(key_factors, list):
            key_factors = []
        if not isinstance(patterns, list):
            patterns = []
        
        validated_response = {
            "sentiment": sentiment,
            "impact": impact,
            "confidence": confidence,
            "key_factors": key_factors,
            "patterns": patterns,
            "reasoning": reasoning
        }
        
        return validated_response
    
    def create_fallback_analysis(self, error_message: str) -> Dict[str, Any]:
        """Create a fallback analysis when errors occur."""
        print(f"[DEBUG] Creating fallback analysis for error: {error_message}")
        
        fallback_analysis = {
            "sentiment": "neutral",
            "impact": "minimal change",
            "confidence": "low",
            "key_factors": ["Analysis failed due to error"],
            "patterns": [],
            "reasoning": f"Error occurred during analysis: {error_message}"
        }
        
        return fallback_analysis