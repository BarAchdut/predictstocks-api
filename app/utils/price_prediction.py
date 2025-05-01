import numpy as np
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def linear_regression(x: List[float], y: List[float]) -> Dict[str, float]:
    """
    Calculate linear regression parameters given x and y data points.
    
    Args:
        x: Independent variable values
        y: Dependent variable values
        
    Returns:
        Dictionary with slope and intercept
    """
    x = np.array(x)
    y = np.array(y)
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)
    
    if denominator == 0:
        logger.warning("Division by zero in linear regression, using default values")
        return {"slope": 0, "intercept": y_mean if len(y) > 0 else 0}
        
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    return {"slope": slope, "intercept": intercept}

def calculate_technical_prediction(historical_data: List[Dict[str, Any]], prediction_days: int = 1) -> Dict[str, Any]:
    """
    Use linear regression to predict future prices based on historical data.
    
    Args:
        historical_data: List of historical price dictionaries
        prediction_days: Number of days to predict into the future
        
    Returns:
        Dictionary with prediction details
    """
    if len(historical_data) < 5:
        logger.warning("Insufficient data for technical prediction (requires at least 5 data points)")
        return {
            "predicted_price": None,
            "confidence": 0.0,
            "trend": "neutral"
        }
    
    # Extract price data
    prices = [day.get("close", 0) for day in historical_data]
    dates = [datetime.strptime(day.get("date", ""), "%Y-%m-%d") for day in historical_data]
    
    # Use the last 30 days if available
    window_size = min(30, len(prices))
    recent_prices = prices[-window_size:]
    
    # Calculate daily returns
    returns = [(recent_prices[i+1] - recent_prices[i]) / recent_prices[i] for i in range(len(recent_prices)-1)]
    
    # Calculate average return and volatility
    avg_return = sum(returns) / len(returns) if returns else 0
    volatility = np.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns)) if returns else 0
    
    # Create x values (days indices)
    x_values = list(range(len(recent_prices)))
    
    # Calculate linear regression
    regression = linear_regression(x_values, recent_prices)
    slope = regression["slope"]
    intercept = regression["intercept"]
    
    # Predict future price
    next_x = len(recent_prices) + prediction_days - 1
    predicted_price = intercept + slope * next_x
    
    # Determine trend
    trend = "neutral"
    if slope > 0:
        trend = "up"
    elif slope < 0:
        trend = "down"
    
    # Calculate confidence based on R-squared value
    y_mean = np.mean(recent_prices)
    ss_total = sum((y - y_mean) ** 2 for y in recent_prices)
    ss_residual = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(x_values, recent_prices))
    r_squared = 1 - (ss_residual / ss_total) if ss_total != 0 else 0
    confidence = max(0, min(r_squared, 1))  # Ensure confidence is between 0 and 1
    
    return {
        "predicted_price": round(predicted_price, 2),
        "confidence": confidence,
        "trend": trend,
        "slope": slope,
        "volatility": volatility
    }

def combine_predictions(ai_prediction: Dict[str, Any], technical_prediction: Dict[str, Any], 
                        current_price: float) -> Dict[str, Any]:
    """
    Combine AI-based prediction with technical prediction.
    
    Args:
        ai_prediction: AI-generated prediction data
        technical_prediction: Technical analysis prediction data
        current_price: Current stock price
        
    Returns:
        Combined prediction dictionary
    """
    # Extract AI prediction direction and confidence
    ai_direction = ai_prediction.get("prediction", {}).get("direction", "hold")
    ai_confidence = ai_prediction.get("confidence", 0.5)
    
    # Convert direction to numeric modifier
    direction_modifiers = {
        "strong_buy": 0.05, 
        "buy": 0.02,
        "hold": 0.0,
        "sell": -0.02,
        "strong_sell": -0.05
    }
    ai_modifier = direction_modifiers.get(ai_direction, 0.0) * ai_confidence
    
    # Get technical prediction
    tech_predicted_price = technical_prediction.get("predicted_price")
    tech_confidence = technical_prediction.get("confidence", 0.0)
    
    # If technical prediction is available, use it
    if tech_predicted_price is not None:
        # Calculate the technical percent change
        tech_percent_change = (tech_predicted_price - current_price) / current_price
        
        # Weight between AI and technical predictions
        ai_weight = 0.7  # Give AI more weight
        tech_weight = 0.3  # Give technical prediction less weight
        
        # Combine predictions
        combined_percent_change = (ai_modifier * ai_weight) + (tech_percent_change * tech_weight * tech_confidence)
        combined_price = current_price * (1 + combined_percent_change)
    else:
        # Fall back to AI only if technical prediction is not available
        combined_price = current_price * (1 + ai_modifier)
    
    # Calculate the final confidence
    combined_confidence = (ai_confidence * 0.7) + (tech_confidence * 0.3) if tech_predicted_price is not None else ai_confidence
    
    return {
        "predicted_price": round(combined_price, 2),
        "combined_confidence": combined_confidence,
        "ai_contribution": ai_prediction.get("prediction", {}).get("direction", "hold"),
        "technical_contribution": technical_prediction.get("trend", "neutral") if tech_predicted_price is not None else "unavailable"
    }