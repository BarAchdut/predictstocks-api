import random
from datetime import datetime, timedelta
from typing import List, Dict
import numpy as np
from app.models import HistoricalData


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

    print(f"Generated {len(predictions)} predictions for {symbol}:", [p.to_dict() for p in predictions])
    return predictions


def evaluate_prediction_accuracy(symbol: str, full_historical_data: List[HistoricalData], step_size: int = 5):
    sorted_data = sorted(full_historical_data, key=lambda d: d.date)
    prediction_window = 7
    window_size = 30
    errors = []

    print(f"[Evaluation] Starting accuracy evaluation for {symbol}...")

    for i in range(0, len(sorted_data) - (window_size + prediction_window), step_size):
        input_slice = sorted_data[i:i + window_size]
        actual_slice = sorted_data[i + window_size:i + window_size + prediction_window]
        predicted = predict_stock_prices(symbol, input_slice)
        if len(predicted) != len(actual_slice):
            continue
        for j in range(len(predicted)):
            actual_price = actual_slice[j].price
            predicted_price = predicted[j].price
            error = abs((predicted_price - actual_price) / actual_price)
            errors.append(error)
            date = actual_slice[j].date
            error_percent = round(error * 100, 2)
            log_prefix = '⚠️  ' if error_percent > 10 else '✅'
            print(f"{log_prefix} {symbol} {date} → Predicted: ${predicted_price} | Actual: ${actual_price} | Error: {error_percent}%")

    if errors:
        avg_error = sum(errors) / len(errors)
        mape = round(avg_error * 100, 2)
        print(f"[Evaluation] Final MAPE for {symbol}: {mape}%")
    else:
        print("[Evaluation] No predictions could be evaluated.")


def get_predictions_with_silent_eval(symbol: str, full_historical_data: List[HistoricalData]) -> List[HistoricalData]:
    prediction_input = full_historical_data[-30:]
    predictions = predict_stock_prices(symbol, prediction_input)

    if len(full_historical_data) >= 60:
        backtest_data = full_historical_data[:-7]
        evaluate_prediction_accuracy(symbol, backtest_data)

    return predictions
