import time
from fastapi import FastAPI, HTTPException, Depends
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from rich.console import Console

from app.models import StockPredictionRequest, StockPrediction
from app.prediction import AIPredictionService

# Initialize console for logging
console = Console()

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
    print("[DEBUG] Root endpoint accessed")
    return {"message": "Welcome to the Stock Prediction API"}

@app.post("/predict", response_model=StockPrediction)
async def predict_stock(request: StockPredictionRequest):
    """
    Predict stock price movement based on technical and AI-powered social media analysis.
    """
    print(f"[DEBUG] === STARTING PREDICTION REQUEST FOR {request.ticker} ===")
    prediction_start_time = time.time()
    
    print(f"[DEBUG] Request parameters:")
    print(f"[DEBUG] - Ticker: {request.ticker}")
    print(f"[DEBUG] - Timeframe: {request.timeframe}")
    print(f"[DEBUG] - Include Reddit: {request.include_reddit}")
    print(f"[DEBUG] - Include Posts: {getattr(request, 'include_posts', False)}")
    
    try:
        prediction_service = AIPredictionService()

        # Step 1: Generate prediction with timeout protection
        print("[DEBUG] Step 1: Generating price movement prediction...")
        prediction_step_start = time.time()
        
        result = prediction_service.predict_price_movement(
            ticker=request.ticker,
            timeframe=request.timeframe,
            include_reddit=request.include_reddit
        )
        
        prediction_step_time = time.time() - prediction_step_start
        print(f"[DEBUG] Step 1 completed in {prediction_step_time:.3f} seconds")

        # Check if result is None or empty
        if not result:
            print("[DEBUG] Warning: Prediction service returned empty result")
            result = {
                "ticker": request.ticker,
                "prediction": {
                    "direction": "neutral",
                    "sentiment": "neutral", 
                    "confidence": 0.5,
                    "reasoning": "Unable to generate prediction due to API limitations"
                },
                "analysis": {
                    "posts_analyzed": 0,
                    "social_sentiment": "neutral"
                },
                "timestamp": time.time()
            }

        # Step 2: Add posts if requested (with error handling)
        if getattr(request, 'include_posts', False) and "posts" not in result:
            print("[DEBUG] Step 2: Fetching social media posts...")
            posts_step_start = time.time()
            
            try:
                from app.social_media import SocialMediaService
                console.log("Fetching posts for ticker:", request.ticker)
                social_service = SocialMediaService()
                result["posts"] = social_service.get_posts_for_ticker(
                    request.ticker, 
                    limit=20, 
                    include_reddit=request.include_reddit
                )
                
                posts_step_time = time.time() - posts_step_start
                print(f"[DEBUG] Step 2 completed in {posts_step_time:.3f} seconds")
                print(f"[DEBUG] Found {len(result.get('posts', []))} posts")
            except Exception as posts_error:
                posts_step_time = time.time() - posts_step_start
                print(f"[DEBUG] Step 2 failed in {posts_step_time:.3f} seconds: {posts_error}")
                result["posts"] = []
        else:
            print("[DEBUG] Step 2: Skipping posts fetch (not requested)")

        # Add timing information to response
        total_prediction_time = time.time() - prediction_start_time
        result["processing_time"] = round(total_prediction_time, 3)
        
        # Ensure required fields exist
        if "timestamp" not in result:
            result["timestamp"] = time.time()
            
        if "ticker" not in result:
            result["ticker"] = request.ticker

        print(f"[DEBUG] === PREDICTION COMPLETED FOR {request.ticker} ===")
        print(f"[DEBUG] Total processing time: {total_prediction_time:.3f} seconds")
        print(f"[DEBUG] Prediction direction: {result.get('prediction', {}).get('direction', 'N/A')}")
        print(f"[DEBUG] Sentiment: {result.get('prediction', {}).get('sentiment', 'N/A')}")
        print(f"[DEBUG] Confidence: {result.get('prediction', {}).get('confidence', 'N/A')}")
        print(f"[DEBUG] Posts analyzed: {result.get('analysis', {}).get('posts_analyzed', 0)}")

        return result
        
    except Exception as e:
        error_time = time.time() - prediction_start_time
        print(f"[DEBUG] === PREDICTION FAILED FOR {request.ticker} AFTER {error_time:.3f} SECONDS ===")
        print(f"[DEBUG] Error details: {str(e)}")
        print(f"[DEBUG] Error type: {type(e).__name__}")
        
        # Return a structured error response instead of raising HTTPException
        fallback_response = {
            "ticker": request.ticker,
            "prediction": {
                "direction": "neutral",
                "sentiment": "neutral",
                "confidence": 0.1,
                "reasoning": f"Prediction failed: {str(e)}"
            },
            "analysis": {
                "posts_analyzed": 0,
                "social_sentiment": "neutral",
                "error": str(e)
            },
            "processing_time": round(error_time, 3),
            "timestamp": time.time(),
            "status": "error"
        }
        
        return fallback_response

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    print("[DEBUG] Health check requested")
    health_start_time = time.time()
    
    try:
        # Test basic functionality
        health_response = {
            "status": "ok", 
            "version": "1.0.0",
            "timestamp": time.time()
        }
        
        health_time = time.time() - health_start_time
        print(f"[DEBUG] Health check completed in {health_time:.3f} seconds")
        
        return health_response
        
    except Exception as e:
        health_time = time.time() - health_start_time
        print(f"[DEBUG] Health check failed in {health_time:.3f} seconds: {e}")
        
        return {
            "status": "error",
            "version": "1.0.0", 
            "error": str(e),
            "timestamp": time.time()
        }