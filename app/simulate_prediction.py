# app/simulate_prediction.py

from app.models import HistoricalData
from app.prediction_service import get_predictions_with_social_sentiment
import random
from datetime import datetime, timedelta

# Generate mock historical data
def generate_mock_data(symbol: str, days: int = 60) -> list:
    base_price = 150.0
    today = datetime.today()
    data = []
    for i in range(days):
        date = today - timedelta(days=i)
        if date.weekday() >= 5:
            continue  # Skip weekends
        price = base_price * (1 + (random.random() - 0.5) * 0.02)
        data.append(HistoricalData(date=date.strftime('%Y-%m-%d'), price=round(price, 2)))
    return list(reversed(data))

if __name__ == "__main__":
    symbol = "AAPL"
    celebrity_handle = "realDonaldTrump"
    historical_data = generate_mock_data(symbol)

    predictions = get_predictions_with_social_sentiment(symbol, historical_data, celebrity_handle)
    
    print(f"Predictions for {symbol} considering {celebrity_handle}:")
    for p in predictions:
        print(f"Date: {p.date} - Predicted Price: ${p.price}")