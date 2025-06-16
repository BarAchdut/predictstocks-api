from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class StockPredictionRequest(BaseModel):
    """Request model for stock prediction."""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL)")
    timeframe: str = Field("1d", description="Prediction timeframe: 1d, 1w, 1m")
    include_posts: bool = Field(False, description="Include analyzed posts in response")
    include_reddit: bool = Field(True, description="Include Reddit posts in response")

class SocialMediaPost(BaseModel):
    """Model for a social media post."""
    platform: str
    author: str
    text: str
    date: datetime
    metrics: Dict[str, Any] = {}

class SentimentAnalysis(BaseModel):
    """Model for sentiment analysis results."""
    sentiment: str
    impact: str
    confidence: str
    key_factors: List[str] = []

class StockPrediction(BaseModel):
    """Response model for stock prediction."""
    ticker: str
    prediction_time: datetime
    timeframe: str
    prediction: Dict[str, Any]
    
    technical_signals: Optional[Dict[str, Any]] = None
    sentiment_analysis: Optional[Any] = None
    confidence: Optional[float] = None

    supporting_data: Dict[str, Any] = {}
    posts: Optional[List[SocialMediaPost]] = None