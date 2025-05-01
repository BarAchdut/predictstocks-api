import os
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class HistoricalDataService:
    """Service for fetching historical stock price data."""
    
    def __init__(self):
        """Initialize the historical data service."""
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.finnhub_key = os.getenv("FINNHUB_API_KEY")
        self.yfinance_enabled = True  # Can be used as a fallback
    
    def get_historical_data(self, ticker: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get historical price data for a stock.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back
            
        Returns:
            List of daily price data dictionaries
        """
        # Try Alpha Vantage first
        if self.alpha_vantage_key:
            try:
                return self._get_alpha_vantage_data(ticker, days)
            except Exception as e:
                logger.warning(f"Error fetching data from Alpha Vantage: {e}")
        
        # Try Finnhub as a fallback
        if self.finnhub_key:
            try:
                return self._get_finnhub_data(ticker, days)
            except Exception as e:
                logger.warning(f"Error fetching data from Finnhub: {e}")
        
        # Use yfinance as a last resort
        if self.yfinance_enabled:
            try:
                return self._get_yfinance_data(ticker, days)
            except Exception as e:
                logger.error(f"Error fetching data from yfinance: {e}")
        
        # If all methods fail, return an empty dataset
        logger.error(f"Failed to fetch historical data for {ticker}")
        return []
    
    def _get_alpha_vantage_data(self, ticker: str, days: int) -> List[Dict[str, Any]]:
        """Fetch historical data from Alpha Vantage API."""
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": "full" if days > 100 else "compact",
            "apikey": self.alpha_vantage_key
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract time series data
        time_series = data.get("Time Series (Daily)", {})
        result = []
        
        # Convert to list of dictionaries
        for date_str, values in time_series.items():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if date >= datetime.now() - timedelta(days=days):
                result.append({
                    "date": date_str,
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0)),
                    "volume": int(values.get("5. volume", 0))
                })
        
        return sorted(result, key=lambda x: x["date"])
    
    def _get_finnhub_data(self, ticker: str, days: int) -> List[Dict[str, Any]]:
        """Fetch historical data from Finnhub API."""
        end_timestamp = int(datetime.now().timestamp())
        start_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
        
        url = "https://finnhub.io/api/v1/stock/candle"
        params = {
            "symbol": ticker,
            "resolution": "D",  # Daily resolution
            "from": start_timestamp,
            "to": end_timestamp,
            "token": self.finnhub_key
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Check if the API returned valid data
        if data.get("s") != "ok":
            raise ValueError(f"Finnhub API error: {data.get('s')}")
        
        # Process the data
        result = []
        timestamps = data.get("t", [])
        opens = data.get("o", [])
        highs = data.get("h", [])
        lows = data.get("l", [])
        closes = data.get("c", [])
        volumes = data.get("v", [])
        
        for i in range(len(timestamps)):
            date_str = datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d")
            result.append({
                "date": date_str,
                "open": opens[i],
                "high": highs[i],
                "low": lows[i],
                "close": closes[i],
                "volume": volumes[i]
            })
        
        return result
    
    def _get_yfinance_data(self, ticker: str, days: int) -> List[Dict[str, Any]]:
        """Fetch historical data using yfinance (Python package)."""
        try:
            import yfinance as yf
        except ImportError:
            logger.error("yfinance package not installed")
            return []
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Fetch data
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
        
        # Convert to list of dictionaries
        result = []
        for index, row in hist.iterrows():
            result.append({
                "date": index.strftime("%Y-%m-%d"),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": row["Volume"]
            })
        
        return result
    
    def get_technical_indicators(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate common technical indicators for the provided historical data.
        
        Args:
            data: List of historical price data
            
        Returns:
            Dictionary of technical indicators
        """
        if not data:
            return {}
        
        # Convert to pandas DataFrame for easier calculation
        df = pd.DataFrame(data)
        
        # Calculate moving averages
        df["ma_5"] = df["close"].rolling(window=5).mean()
        df["ma_20"] = df["close"].rolling(window=20).mean()
        
        # Calculate RSI (Relative Strength Index)
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))
        
        # Calculate MACD (Moving Average Convergence Divergence)
        ema_12 = df["close"].ewm(span=12, adjust=False).mean()
        ema_26 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = ema_12 - ema_26
        df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        
        # Get the latest values
        latest = df.iloc[-1].to_dict()
        
        # Return technical indicators
        return {
            "moving_averages": {
                "ma_5": latest.get("ma_5"),
                "ma_20": latest.get("ma_20"),
                "trend_5_20": "bullish" if latest.get("ma_5", 0) > latest.get("ma_20", 0) else "bearish"
            },
            "rsi": latest.get("rsi"),
            "macd": {
                "macd": latest.get("macd"),
                "signal": latest.get("signal"),
                "histogram": latest.get("macd", 0) - latest.get("signal", 0),
                "trend": "bullish" if latest.get("macd", 0) > latest.get("signal", 0) else "bearish"
            },
            "price": {
                "current": latest.get("close"),
                "previous_day": df.iloc[-2]["close"] if len(df) > 1 else None,
                "change_percent": ((latest.get("close", 0) / df.iloc[-2]["close"]) - 1) * 100 if len(df) > 1 else 0
            }
        }