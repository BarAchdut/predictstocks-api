from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from app.models import HistoricalData
from app.prediction import get_predictions_with_silent_eval

app = FastAPI()

class HistoricalDataInput(BaseModel):
    date: str
    price: float

@app.post("/PredictStocks")
def predict_stocks(symbol: str, historical: List[HistoricalDataInput]):
    try:
        historical_data = [HistoricalData(h.date, h.price) for h in historical]
        predictions = get_predictions_with_silent_eval(symbol, historical_data)
        return [p.to_dict() for p in predictions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
