import unittest
from unittest.mock import patch, MagicMock
import json

from app.ai_service import AIService

class TestAIService(unittest.TestCase):
    """Test cases for the AI Service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ai_service = AIService()
        
        # Sample data for tests
        self.sample_ticker = "AAPL"
        
        # Sample social media posts
        self.sample_posts = [
            {"platform": "twitter", "author": "user1", "text": "Excited about the new $AAPL product launch!", "date": "2023-01-02T10:00:00", "metrics": {"likes": 100}},
            {"platform": "reddit", "author": "user2", "text": "AAPL stock might drop after the earnings report.", "date": "2023-01-02T11:00:00", "metrics": {"upvotes": 50}}
        ]
        
        # Sample API response
        self.sample_api_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "sentiment": "positive",
                            "impact": "moderate increase",
                            "confidence": "medium",
                            "key_factors": ["product launch", "earnings report"]
                        })
                    }
                }
            ]
        }
    
    @patch('requests.post')
    def test_analyze_social_media_impact(self, mock_post):
        """Test the analyze_social_media_impact method."""
        # Configure mock
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.sample_api_response
        mock_post.return_value = mock_response
        
        # Call the method under test
        result = self.ai_service.analyze_social_media_impact(self.sample_posts, self.sample_ticker)
        
        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertIn("ai_analysis", result)
        self.assertIn("raw_response", result)
        
        # Verify that the mock was called correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.openai.com/v1/chat/completions")
        self.assertIn("headers", kwargs)
        self.assertIn("json", kwargs)
        self.assertEqual(kwargs["json"]["model"], "gpt-4")
        
        # Verify that the API call included the ticker and posts
        self.assertIn(self.sample_ticker, kwargs["json"]["messages"][0]["content"])
        for post in self.sample_posts:
            self.assertIn(post["text"], kwargs["json"]["messages"][0]["content"])
    
    @patch('requests.post')
    def test_analyze_social_media_impact_error_handling(self, mock_post):
        """Test error handling in analyze_social_media_impact."""
        # Configure mock to raise an exception
        mock_post.side_effect = Exception("API Error")
        
        # Call the method under test
        result = self.ai_service.analyze_social_media_impact(self.sample_posts, self.sample_ticker)
        
        # Verify that the method handled the error gracefully
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("sentiment", result)
        self.assertIn("impact", result)
        self.assertIn("confidence", result)
        
        # Verify default values
        self.assertEqual(result["sentiment"], "neutral")
        self.assertEqual(result["impact"], "minimal change")
        self.assertEqual(result["confidence"], "low")
    
    def test_fine_tune_model(self):
        """Test the fine_tune_model method."""
        # Sample training examples
        examples = [
            {"posts": [{"text": "Great news for $AAPL!"}], "outcome": {"price_change": 2.5, "direction": "up"}},
            {"posts": [{"text": "Disappointing $AAPL earnings"}], "outcome": {"price_change": -1.8, "direction": "down"}}
        ]
        
        # Call the method under test
        result = self.ai_service.fine_tune_model(examples)
        
        # Verify the result
        self.assertTrue(result)  # Method should return True

if __name__ == '__main__':
    unittest.main()