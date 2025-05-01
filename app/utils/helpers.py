import json
import logging
from typing import Dict, Any, List, Union
from datetime import datetime, date

logger = logging.getLogger(__name__)

def format_currency(value: float, currency: str = "USD") -> str:
    """
    Format a numeric value as currency.
    
    Args:
        value: The numeric value to format
        currency: Currency code (default: USD)
        
    Returns:
        Formatted currency string
    """
    if currency == "USD":
        return f"${value:,.2f}"
    elif currency == "EUR":
        return f"€{value:,.2f}"
    else:
        return f"{value:,.2f} {currency}"

def format_percentage(value: float, decimal_places: int = 2) -> str:
    """
    Format a numeric value as a percentage.
    
    Args:
        value: The numeric value to format
        decimal_places: Number of decimal places to show
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimal_places}f}%"

def parse_timeframe(timeframe: str) -> int:
    """
    Parse a timeframe string into days.
    
    Args:
        timeframe: Timeframe string (e.g., "1d", "1w", "1m")
        
    Returns:
        Number of days
    """
    unit = timeframe[-1].lower()
    try:
        value = int(timeframe[:-1])
    except ValueError:
        logger.warning(f"Invalid timeframe format: {timeframe}, defaulting to 1 day")
        return 1
    
    if unit == 'd':
        return value
    elif unit == 'w':
        return value * 7
    elif unit == 'm':
        return value * 30
    else:
        logger.warning(f"Unknown timeframe unit: {unit}, defaulting to days")
        return value

class JSONEncoder(json.JSONEncoder):
    """Extended JSON encoder that handles dates and datetimes."""
    
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def safe_json_dumps(obj: Any) -> str:
    """
    Safely convert an object to a JSON string, handling dates and datetimes.
    
    Args:
        obj: The object to convert
        
    Returns:
        JSON string
    """
    return json.dumps(obj, cls=JSONEncoder)

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to a maximum length, adding ellipsis if needed.
    
    Args:
        text: The text to truncate
        max_length: Maximum allowed length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def filter_posts_by_keywords(posts: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Filter social media posts by keywords.
    
    Args:
        posts: List of post dictionaries
        keywords: List of keywords to match
        
    Returns:
        Filtered list of posts
    """
    if not keywords:
        return posts
        
    filtered_posts = []
    for post in posts:
        text = post.get("text", "").lower()
        if any(keyword.lower() in text for keyword in keywords):
            filtered_posts.append(post)
            
    return filtered_posts

def calculate_weighted_sentiment(sentiments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate weighted sentiment score from multiple sources.
    
    Args:
        sentiments: List of sentiment dictionaries with scores and weights
        
    Returns:
        Dictionary with combined sentiment score and label
    """
    if not sentiments:
        return {"score": 0, "label": "neutral"}
        
    total_weight = sum(item.get("weight", 1) for item in sentiments)
    weighted_score = sum(item.get("score", 0) * item.get("weight", 1) for item in sentiments) / total_weight
    
    # Map score to label
    if weighted_score >= 0.6:
        label = "very positive"
    elif weighted_score >= 0.2:
        label = "positive"
    elif weighted_score > -0.2:
        label = "neutral"
    elif weighted_score > -0.6:
        label = "negative"
    else:
        label = "very negative"
        
    return {
        "score": weighted_score,
        "label": label
    }