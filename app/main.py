# app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from app.models import HistoricalData
from app.prediction_service import get_predictions_with_social_sentiment  # <-- חשוב: קורא לחדש

app = FastAPI()

class HistoricalDataInput(BaseModel):
    date: str
    price: float

class PredictionRequest(BaseModel):
    symbol: str
    celebrity_handle: str
    historical: List[HistoricalDataInput]

@app.post("/PredictStocks")
def predict_stocks(request: PredictionRequest):
    try:
        historical_data = [HistoricalData(h.date, h.price) for h in request.historical]
        predictions = get_predictions_with_social_sentiment(
            request.symbol, 
            historical_data, 
            request.celebrity_handle
        )
        return [p.to_dict() for p in predictions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))