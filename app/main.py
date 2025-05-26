from fastapi import FastAPI, HTTPException, Depends
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from rich import _console

from app.models import StockPredictionRequest, StockPrediction
from app.prediction import AIPredictionService

app = FastAPI(
    title="Stock Prediction API",
    description="API for predicting stock prices using social media and AI analysis",
    version="1.0.0"
)

origins = [
    "http://localhost:8080",  
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Stock Prediction API"}

@app.post("/predict", response_model=StockPrediction)
async def predict_stock(request: StockPredictionRequest):
    """
    Predict stock price movement based on technical and AI-powered social media analysis.
    """
    prediction_service = AIPredictionService()

    try:
        result = prediction_service.predict_price_movement(
            ticker=request.ticker,
            timeframe=request.timeframe,
            include_reddit=request.include_reddit
        )

        # If posts were requested but not included in the result
        if request.include_posts and "posts" not in result:
            from app.social_media_service import SocialMediaService
            _console.log("Fetching posts for ticker:", request.include_posts)
            social_service = SocialMediaService()
            result["posts"] = social_service.get_posts_for_ticker(request.ticker, limit=20, include_reddit=request.include_reddit)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}