import random
from datetime import datetime, timedelta
from typing import List, Dict
import numpy as np
import requests
from app.models import HistoricalData

# Config
API_BASE_URL = "http://localhost:3000"
SOCIAL_SIGNAL_WEIGHT = 0.3
MIN_RELEVANT_TWEETS = 3

def fetch_recent_tweets(handle: str, hours: int = 24) -> List[str]:
    try:
        response = requests.post(f"{API_BASE_URL}/functions/v1/twitter", json={
            "handles": [handle],
            "sinceHours": hours,
            "maxResults": 10
        })
        response.raise_for_status()
        data = response.json()
        return [tweet['text'] for tweet in data.get('tweets', [])]
    except Exception as e:
        print(f"Error fetching tweets: {e}")
        return []

def analyze_sentiment(text: str) -> float:
    try:
        response = requests.post(f"{API_BASE_URL}/functions/v1/openai", json={
            "text": text,
            "analyze": "sentiment"
        })
        response.raise_for_status()
        data = response.json()
        return data.get('score', 0)
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return 0

def calculate_social_signal_score(handle: str, symbol: str) -> float:
    tweets = fetch_recent_tweets(handle)
    if not tweets:
        return 0
    relevant_tweets = []
    symbol_lower = symbol.lower()
    for tweet in tweets:
        if symbol_lower in tweet.lower():
            relevant_tweets.append(tweet)
    if len(relevant_tweets) < MIN_RELEVANT_TWEETS:
        return 0
    total_sentiment = sum(analyze_sentiment(tweet) for tweet in relevant_tweets)
    avg_sentiment = total_sentiment / len(relevant_tweets)
    volume_factor = min(1, len(relevant_tweets) / 10)
    return avg_sentiment * volume_factor

def linear_regression(x: List[float], y: List[float]) -> Dict[str, float]:
    x = np.array(x)
    y = np.array(y)
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    return {"slope": slope, "intercept": intercept}

def predict_stock_prices(symbol: str, historical_data: List[HistoricalData]) -> List[HistoricalData]:
    if len(historical_data) < 30:
        print("Insufficient data for prediction (requires at least 30 days)")
        return []
    sorted_data = sorted(historical_data, key=lambda d: d.date)
    recent_data = sorted_data[-30:]
    prices = [d.price for d in recent_data]
    x_values = list(range(len(prices)))
    y_values = prices
    regression = linear_regression(x_values, y_values)
    slope = regression["slope"]
    intercept = regression["intercept"]
    returns = [(prices[i + 1] - prices[i]) / prices[i] for i in range(len(prices) - 1)]
    avg_return = sum(returns) / len(returns)
    volatility = np.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns))

    predictions = []
    last_date = datetime.strptime(recent_data[-1].date, "%Y-%m-%d")
    last_index = x_values[-1]
    i = 1
    while len(predictions) < 7:
        next_date = last_date + timedelta(days=i)
        if next_date.weekday() >= 5:
            i += 1
            continue
        next_index = last_index + i
        predicted_price = intercept + slope * next_index
        noise = predicted_price * (random.random() * volatility - volatility / 2)
        predicted_price += noise
        predictions.append(HistoricalData(next_date.strftime("%Y-%m-%d"), round(predicted_price, 2)))
        i += 1

    return predictions

def apply_social_signal_to_predictions(predictions: List[HistoricalData], social_score: float) -> List[HistoricalData]:
    if social_score == 0 or not predictions:
        return predictions
    enhanced = []
    for idx, prediction in enumerate(predictions):
        factor = (idx + 1) / len(predictions)
        adjustment = 1 + (social_score * SOCIAL_SIGNAL_WEIGHT * factor)
        enhanced_price = prediction.price * adjustment
        enhanced.append(HistoricalData(prediction.date, round(enhanced_price, 2)))
    return enhanced

def get_predictions_with_social_sentiment(symbol: str, historical_data: List[HistoricalData], celebrity_handle: str) -> List[HistoricalData]:
    baseline_predictions = predict_stock_prices(symbol, historical_data)
    social_score = calculate_social_signal_score(celebrity_handle, symbol)
    enhanced_predictions = apply_social_signal_to_predictions(baseline_predictions, social_score)
    return enhanced_predictions