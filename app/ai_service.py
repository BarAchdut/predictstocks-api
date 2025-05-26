# import os
# import logging
# from typing import Dict, Any, List
# import json
# import re

# from dotenv import load_dotenv

# # Updated OpenAI import for version 1.0+
# try:
#     from openai import OpenAI
# except ImportError:
#     print("Please install openai>=1.0.0: pip install openai>=1.0.0")
#     raise

# load_dotenv()

# logger = logging.getLogger(__name__)

# class AIService:
#     """Service for interacting with external AI APIs for sentiment and impact analysis."""

#     def __init__(self):
#         self.openai_api_key = os.getenv("OPENAI_API_KEY")
#         if not self.openai_api_key:
#             logger.error("OPENAI_API_KEY not found in environment variables")
#             raise ValueError("OpenAI API key is required")
        
#         # Initialize OpenAI client (new syntax for v1.0+)
#         self.client = OpenAI(api_key=self.openai_api_key)

#     def analyze_social_media_impact(self, posts: List[Dict[str, Any]], ticker: str) -> Dict[str, Any]:
#         """Analyze social media posts for sentiment and potential stock impact."""
#         try:
#             if not posts:
#                 logger.warning(f"No posts provided for analysis of {ticker}")
#                 return {
#                     "ai_analysis": {
#                         "sentiment": "neutral",
#                         "impact": "minimal change",
#                         "confidence": "low",
#                         "key_factors": ["No posts available for analysis"]
#                     },
#                     "raw_response": "No posts to analyze"
#                 }

#             # Format posts for analysis (limit to avoid token limits)
#             formatted_posts = "\n".join([
#                 f"Post by {post.get('author', 'Unknown')} ({post.get('platform', 'unknown')}): {post.get('text', '')[:500]}" 
#                 for post in posts[:15]  # Increased from 10 to 15 posts
#             ])

#             prompt = f"""
#             Analyze the following social media posts about {ticker} stock and determine:
#             1. The overall sentiment (very negative, negative, neutral, positive, very positive)
#             2. The potential impact on stock price (significant decrease, moderate decrease, minimal change, moderate increase, significant increase)
#             3. The confidence level of your prediction (low, medium, high)
#             4. Key factors mentioned that could influence stock price (as a list)
#             5. Notable patterns or trends in the discussion

#             Posts ({len(posts)} total, showing first {min(len(posts), 15)}):
#             {formatted_posts}

#             Please return your analysis in the following JSON format:
#             {{
#                 "sentiment": "one of: very negative, negative, neutral, positive, very positive",
#                 "impact": "one of: significant decrease, moderate decrease, minimal change, moderate increase, significant increase",
#                 "confidence": "one of: low, medium, high",
#                 "key_factors": ["list", "of", "key", "factors"],
#                 "patterns": ["notable", "patterns", "or", "trends"],
#                 "reasoning": "Brief explanation of your analysis"
#             }}
#             """

#             # Use new OpenAI client syntax (updated for v1.0+)
#             response = self.client.chat.completions.create(
#                 model='gpt-4o-mini',  # Updated model name
#                 messages=[
#                     {"role": "system", "content": "You are a financial analyst AI specializing in social media sentiment analysis for stock prediction. Provide accurate, unbiased analysis based on the provided data."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0.3,
#                 max_tokens=1000  # Increased from 512 to 1000
#             )

#             content = response.choices[0].message.content.strip()
#             logger.debug(f"OpenAI raw response: {content}")

#             # Parse JSON response with improved error handling
#             try:
#                 parsed_content = json.loads(content)
#             except json.JSONDecodeError:
#                 try:
#                     json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
#                     if json_match:
#                         parsed_content = json.loads(json_match.group(1))
#                     else:
#                         json_match = re.search(r'({[\s\S]*})', content)
#                         if json_match:
#                             parsed_content = json.loads(json_match.group(1))
#                         else:
#                             # Fallback: create structured response from unstructured content
#                             parsed_content = self._parse_unstructured_response(content)
#                 except Exception as e:
#                     logger.error(f"Error extracting JSON from response: {e}")
#                     parsed_content = self._parse_unstructured_response(content)

#             # Validate and normalize the response
#             normalized_response = self._validate_and_normalize_response(parsed_content)

#             return {
#                 "ai_analysis": normalized_response,
#                 "raw_response": content,
#                 "posts_analyzed": len(posts),
#                 "posts_shown_to_ai": min(len(posts), 15)
#             }

#         except Exception as e:
#             logger.error(f"Error analyzing social media posts: {e}")
#             return {
#                 "error": str(e),
#                 "ai_analysis": {
#                     "sentiment": "neutral",
#                     "impact": "minimal change",
#                     "confidence": "low",
#                     "key_factors": ["Analysis failed due to error"],
#                     "patterns": [],
#                     "reasoning": f"Error occurred during analysis: {str(e)}"
#                 },
#                 "posts_analyzed": len(posts) if posts else 0
#             }

#     def _parse_unstructured_response(self, content: str) -> Dict[str, Any]:
#         """Parse unstructured AI response into structured format."""
#         # Default values
#         result = {
#             "sentiment": "neutral",
#             "impact": "minimal change",
#             "confidence": "medium",
#             "key_factors": [],
#             "patterns": [],
#             "reasoning": content
#         }

#         content_lower = content.lower()

#         # Extract sentiment
#         if any(word in content_lower for word in ["very positive", "extremely positive"]):
#             result["sentiment"] = "very positive"
#         elif "positive" in content_lower:
#             result["sentiment"] = "positive"
#         elif any(word in content_lower for word in ["very negative", "extremely negative"]):
#             result["sentiment"] = "very negative"
#         elif "negative" in content_lower:
#             result["sentiment"] = "negative"

#         # Extract impact
#         if any(phrase in content_lower for phrase in ["significant increase", "major increase"]):
#             result["impact"] = "significant increase"
#         elif any(phrase in content_lower for phrase in ["moderate increase", "slight increase"]):
#             result["impact"] = "moderate increase"
#         elif any(phrase in content_lower for phrase in ["significant decrease", "major decrease"]):
#             result["impact"] = "significant decrease"
#         elif any(phrase in content_lower for phrase in ["moderate decrease", "slight decrease"]):
#             result["impact"] = "moderate decrease"

#         # Extract confidence
#         if "high confidence" in content_lower or "confident" in content_lower:
#             result["confidence"] = "high"
#         elif "low confidence" in content_lower or "uncertain" in content_lower:
#             result["confidence"] = "low"

#         return result

#     def _validate_and_normalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
#         """Validate and normalize AI response to ensure consistency."""
#         # Valid options for each field
#         valid_sentiments = ["very negative", "negative", "neutral", "positive", "very positive"]
#         valid_impacts = ["significant decrease", "moderate decrease", "minimal change", "moderate increase", "significant increase"]
#         valid_confidences = ["low", "medium", "high"]

#         # Normalize sentiment
#         sentiment = str(response.get("sentiment", "neutral")).lower()
#         if sentiment not in valid_sentiments:
#             # Try to map similar values
#             if "very" in sentiment and "positive" in sentiment:
#                 sentiment = "very positive"
#             elif "very" in sentiment and "negative" in sentiment:
#                 sentiment = "very negative"
#             elif "positive" in sentiment:
#                 sentiment = "positive"
#             elif "negative" in sentiment:
#                 sentiment = "negative"
#             else:
#                 sentiment = "neutral"

#         # Normalize impact
#         impact = str(response.get("impact", "minimal change")).lower()
#         if impact not in valid_impacts:
#             # Try to map similar values
#             if "significant" in impact and ("increase" in impact or "up" in impact):
#                 impact = "significant increase"
#             elif "significant" in impact and ("decrease" in impact or "down" in impact):
#                 impact = "significant decrease"
#             elif "moderate" in impact and ("increase" in impact or "up" in impact):
#                 impact = "moderate increase"
#             elif "moderate" in impact and ("decrease" in impact or "down" in impact):
#                 impact = "moderate decrease"
#             else:
#                 impact = "minimal change"

#         # Normalize confidence
#         confidence = str(response.get("confidence", "medium")).lower()
#         if confidence not in valid_confidences:
#             confidence = "medium"

#         return {
#             "sentiment": sentiment,
#             "impact": impact,
#             "confidence": confidence,
#             "key_factors": response.get("key_factors", []),
#             "patterns": response.get("patterns", []),
#             "reasoning": response.get("reasoning", "Analysis completed")
#         }

#     def fine_tune_model(self, examples: List[Dict[str, Any]]) -> bool:
#         """Fine-tuning method (placeholder for future implementation).""" 
#         logger.info("Fine-tuning is not implemented in this version")
#         return False

#     def get_model_capabilities(self) -> Dict[str, Any]:
#         """Get information about available models and capabilities."""
#         return {
#             "available_models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
#             "current_model": "gpt-4o-mini",
#             "capabilities": [
#                 "text analysis",
#                 "sentiment analysis", 
#                 "structured data extraction",
#                 "reasoning",
#                 "financial analysis"
#             ],
#             "api_version": "1.0+",
#             "max_tokens": 4096
#         }

#     def test_connection(self) -> Dict[str, Any]:
#         """Test the OpenAI API connection."""
#         try:
#             # Make a simple test request
#             response = self.client.chat.completions.create(
#                 model='gpt-4o-mini',
#                 messages=[
#                     {"role": "user", "content": "Hello, this is a test. Please respond with 'OK'."}
#                 ],
#                 max_tokens=10
#             )
            
#             content = response.choices[0].message.content.strip()
            
#             return {
#                 "status": "success",
#                 "message": "OpenAI API connection successful",
#                 "response": content,
#                 "model_used": "gpt-4o-mini"
#             }
            
#         except Exception as e:
#             return {
#                 "status": "error",
#                 "message": f"OpenAI API connection failed: {str(e)}",
#                 "error": str(e)
#             }