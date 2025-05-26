"""Technical analysis calculations for stock prediction."""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """Handles technical analysis calculations and indicators."""
    
    def __init__(self):
        self.min_data_points = 2
        self.good_data_threshold = 10
    
    def calculate_technical_indicators(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate technical indicators from historical price data."""
        if len(historical_data) < self.min_data_points:
            logger.warning("Insufficient historical data for technical analysis")
            return self._create_insufficient_data_result()
        
        latest_price = historical_data[-1].get("close", 0)
        previous_price = historical_data[-2].get("close", 0)
        
        # Basic trend calculation
        trend = self._calculate_trend(latest_price, previous_price)
        
        # Price change calculations
        price_change = latest_price - previous_price
        price_change_percent = self._calculate_percentage_change(latest_price, previous_price)
        
        # Additional indicators if we have enough data
        additional_indicators = {}
        if len(historical_data) >= 5:
            additional_indicators = self._calculate_advanced_indicators(historical_data)
        
        # Data quality assessment
        data_quality = "good" if len(historical_data) >= self.good_data_threshold else "limited"
        
        return {
            "trend": trend,
            "latest_price": latest_price,
            "price_change": price_change,
            "price_change_percent": price_change_percent,
            "data_quality": data_quality,
            "data_points": len(historical_data),
            **additional_indicators
        }
    
    def _create_insufficient_data_result(self) -> Dict[str, Any]:
        """Create result when insufficient data is available."""
        return {
            "trend": "neutral",
            "latest_price": 0,
            "price_change": 0,
            "price_change_percent": 0,
            "data_quality": "insufficient",
            "data_points": 0
        }
    
    def _calculate_trend(self, latest_price: float, previous_price: float) -> str:
        """Calculate basic price trend."""
        if latest_price > previous_price:
            return "up"
        elif latest_price < previous_price:
            return "down"
        else:
            return "neutral"
    
    def _calculate_percentage_change(self, latest_price: float, previous_price: float) -> float:
        """Calculate percentage change between two prices."""
        if previous_price == 0:
            return 0.0
        return ((latest_price - previous_price) / previous_price) * 100
    
    def _calculate_advanced_indicators(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate advanced technical indicators when sufficient data is available."""
        indicators = {}
        
        # Simple Moving Average (5 periods)
        if len(historical_data) >= 5:
            recent_prices = [data.get("close", 0) for data in historical_data[-5:]]
            sma_5 = sum(recent_prices) / len(recent_prices)
            latest_price = historical_data[-1].get("close", 0)
            
            indicators["sma_5"] = sma_5
            indicators["price_vs_sma"] = "above" if latest_price > sma_5 else "below"
        
        # Simple Moving Average (10 periods) if available
        if len(historical_data) >= 10:
            recent_prices_10 = [data.get("close", 0) for data in historical_data[-10:]]
            sma_10 = sum(recent_prices_10) / len(recent_prices_10)
            indicators["sma_10"] = sma_10
        
        # Volatility indicator (standard deviation of last 5 prices)
        if len(historical_data) >= 5:
            recent_prices = [data.get("close", 0) for data in historical_data[-5:]]
            mean_price = sum(recent_prices) / len(recent_prices)
            variance = sum((price - mean_price) ** 2 for price in recent_prices) / len(recent_prices)
            volatility = variance ** 0.5
            indicators["volatility"] = volatility
            indicators["volatility_level"] = self._classify_volatility(volatility, mean_price)
        
        return indicators
    
    def _classify_volatility(self, volatility: float, mean_price: float) -> str:
        """Classify volatility level relative to price."""
        if mean_price == 0:
            return "unknown"
        
        volatility_percent = (volatility / mean_price) * 100
        
        if volatility_percent < 2:
            return "low"
        elif volatility_percent < 5:
            return "medium"
        else:
            return "high"
    
    def get_technical_summary(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of technical analysis."""
        trend = indicators.get("trend", "neutral")
        price_change_pct = indicators.get("price_change_percent", 0)
        data_quality = indicators.get("data_quality", "unknown")
        
        # Generate technical signal strength
        signal_strength = self._calculate_signal_strength(indicators)
        
        # Generate recommendations
        recommendation = self._generate_technical_recommendation(indicators)
        
        return {
            "summary": f"Price trend: {trend} ({price_change_pct:.1f}%)",
            "signal_strength": signal_strength,
            "recommendation": recommendation,
            "data_reliability": data_quality,
            "key_indicators": self._extract_key_indicators(indicators)
        }
    
    def _calculate_signal_strength(self, indicators: Dict[str, Any]) -> str:
        """Calculate the strength of technical signals."""
        trend = indicators.get("trend", "neutral")
        price_change_pct = abs(indicators.get("price_change_percent", 0))
        
        if trend == "neutral":
            return "weak"
        elif price_change_pct > 5:
            return "strong"
        elif price_change_pct > 2:
            return "moderate"
        else:
            return "weak"
    
    def _generate_technical_recommendation(self, indicators: Dict[str, Any]) -> str:
        """Generate technical recommendation based on indicators."""
        trend = indicators.get("trend", "neutral")
        signal_strength = self._calculate_signal_strength(indicators)
        
        if trend == "up" and signal_strength in ["strong", "moderate"]:
            return "bullish"
        elif trend == "down" and signal_strength in ["strong", "moderate"]:
            return "bearish"
        else:
            return "neutral"
    
    def _extract_key_indicators(self, indicators: Dict[str, Any]) -> List[str]:
        """Extract key indicators for summary."""
        key_points = []
        
        trend = indicators.get("trend", "neutral")
        price_change_pct = indicators.get("price_change_percent", 0)
        
        if trend != "neutral":
            key_points.append(f"{trend} trend ({price_change_pct:.1f}%)")
        
        if "sma_5" in indicators:
            price_vs_sma = indicators.get("price_vs_sma", "unknown")
            key_points.append(f"Price {price_vs_sma} 5-day average")
        
        if "volatility_level" in indicators:
            vol_level = indicators.get("volatility_level", "unknown")
            key_points.append(f"{vol_level} volatility")
        
        return key_points