import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from app.ai_prediction_service import AIPredictionService
from app.social_media_service import SocialMediaService
from app.ai_service import AIService
from app.data.historical_data import HistoricalDataService

class TestPredictionService(unittest.TestCase):
    """Test cases for the AI Prediction Service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.prediction_service = AIPredictionService()
        
        # Sample data for tests
        self.sample_ticker = "AAPL"
        self.sample_timeframe = "1d"
        
        # Sample historical data
        self.sample_historical_data = [
            {"date": "2023-01-01", "open": 150.0, "high": 155.0, "low": 149.0, "close": 153.0, "volume": 1000000},
            {"date": "2023-01-02", "open": 153.0, "high": 158.0, "low": 152.0, "close": 157.0, "volume": 1200000}
        ]
        
        # Sample social media posts
        self.sample_posts = [
            {"platform": "twitter", "author": "user1", "text": "Excited about the new $AAPL product launch!", "date": "2023-01-02T10:00:00", "metrics": {"likes": 100}},
            {"platform": "reddit", "author": "user2", "text": "AAPL stock might drop after the earnings report.", "date": "2023-01-02T11:00:00", "metrics": {"upvotes": 50}}
        ]
        
        # Sample AI analysis
        self.sample_ai_analysis = {
            "ai_analysis": json.dumps({
                "sentiment": "positive",
                "impact": "moderate increase",
                "confidence": "medium",
                "key_factors": ["product launch", "earnings report"]
            }),
            "raw_response": {"choices": [{"message": {"content": "{}"}}]}
        }
    
    @patch.object(HistoricalDataService, 'get_historical_data')
    @patch.object(SocialMediaService, 'get_posts_for_ticker')
    @patch.object(SocialMediaService, 'get_influencer_posts')
    @patch.object(AIService, 'analyze_social_media_impact')
    def test_predict_price_movement(self, mock_analyze, mock_get_influencer, mock_get_posts, mock_get_historical):
        """Test the predict_price_movement method."""
        # Configure mocks
        mock_get_historical.return_value = self.sample_historical_data
        mock_get_posts.return_value = self.sample_posts
        mock_get_influencer.return_value = []
        mock_analyze.return_value = self.sample_ai_analysis
        
        # Call the method under test
        result = self.prediction_service.predict_price_movement(self.sample_ticker, self.sample_timeframe)
        
        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result["ticker"], self.sample_ticker)
        self.assertEqual(result["timeframe"], self.sample_timeframe)
        self.assertIn("prediction", result)
        self.assertIn("technical_signals", result)
        self.assertIn("sentiment_analysis", result)
        self.assertIn("confidence", result)
        
        # Verify that the mocks were called correctly
        mock_get_historical.assert_called_once_with(self.sample_ticker, days=30)
        mock_get_posts.assert_called_once_with(self.sample_ticker, limit=50)
        mock_get_influencer.assert_called_once_with(self.sample_ticker)
        mock_analyze.assert_called_once()
    
    def test_calculate_technical_indicators(self):
        """Test the _calculate_technical_indicators method."""
        # Call the method under test
        result = self.prediction_service._calculate_technical_indicators(self.sample_historical_data)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn("trend", result)
        self.assertEqual(result["trend"], "up")  # Last price higher than previous
        self.assertEqual(result["latest_price"], 157.0)
        self.assertAlmostEqual(result["price_change"], 4.0)
    
    def test_combine_signals(self):
        """Test the _combine_signals method."""
        # Prepare test data
        technical_signals = {"trend": "up", "latest_price": 157.0}
        ai_analysis = self.sample_ai_analysis
        
        # Call the method under test
        result = self.prediction_service._combine_signals(technical_signals, ai_analysis)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn("direction", result)
        self.assertIn("sentiment", result)
        self.assertEqual(result["sentiment"], "positive")
        # Since both technical trend and sentiment are positive, expect a buy signal
        self.assertEqual(result["direction"], "buy")

if __name__ == '__main__':
    unittest.main()