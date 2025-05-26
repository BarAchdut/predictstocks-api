"""Signal combination logic for merging technical and sentiment analysis."""

import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SignalCombiner:
    """Combines technical signals with AI sentiment analysis."""
    
    def __init__(self):
        self.prediction_map = {
            ("up", "positive"): "buy",
            ("up", "very positive"): "strong_buy",
            ("down", "negative"): "sell", 
            ("down", "very negative"): "strong_sell",
            ("neutral", "neutral"): "hold"
        }
    
    def combine_signals(self, technical_signals: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Combine technical signals with AI sentiment analysis."""
        sentiment = "neutral"
        impact = "minimal change"
        reasoning = []
        
        # Extract AI analysis results
        try:
            ai_result = self._extract_ai_results(ai_analysis)
            sentiment = ai_result.get("sentiment", "neutral")
            impact = ai_result.get("impact", "minimal change")
            
            # Extract reasoning from AI analysis
            reasoning.extend(self._extract_ai_reasoning(ai_result))
            
        except Exception as e:
            logger.error(f"Error parsing AI analysis: {e}")
            reasoning.append("AI analysis parsing failed")
        
        # Extract technical analysis
        technical_trend = technical_signals.get("trend", "neutral")
        
        # Add technical reasoning
        reasoning.extend(self._extract_technical_reasoning(technical_signals))
        
        # Generate combined prediction
        prediction = self._generate_prediction(technical_trend, sentiment)
        reasoning.append(self._get_prediction_reasoning(technical_trend, sentiment, prediction))
        
        return {
            "direction": prediction,
            "expected_impact": impact,
            "technical_trend": technical_trend,
            "sentiment": sentiment,
            "reasoning": reasoning,
            "signal_alignment": self._assess_signal_alignment(technical_trend, sentiment),
            "combined_strength": self._calculate_combined_strength(technical_signals, sentiment)
        }
    
    def _extract_ai_results(self, ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and parse AI analysis results."""
        ai_result = ai_analysis.get("ai_analysis", {})
        
        if isinstance(ai_result, str):
            try:
                ai_result = json.loads(ai_result)
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI analysis JSON string")
                ai_result = {}
        
        return ai_result
    
    def _extract_ai_reasoning(self, ai_result: Dict[str, Any]) -> List[str]:
        """Extract reasoning points from AI analysis."""
        reasoning = []
        
        if "reasoning" in ai_result:
            reasoning.append(f"AI: {ai_result['reasoning']}")
        
        if "key_factors" in ai_result and ai_result["key_factors"]:
            key_factors = ai_result["key_factors"][:3]  # Limit to top 3
            reasoning.append(f"Key factors: {', '.join(key_factors)}")
        
        if "patterns" in ai_result and ai_result["patterns"]:
            patterns = ai_result["patterns"][:2]  # Limit to top 2
            reasoning.append(f"Patterns: {', '.join(patterns)}")
        
        return reasoning
    
    def _extract_technical_reasoning(self, technical_signals: Dict[str, Any]) -> List[str]:
        """Extract reasoning points from technical analysis."""
        reasoning = []
        
        technical_trend = technical_signals.get("trend", "neutral")
        if technical_trend != "neutral":
            price_change_pct = technical_signals.get("price_change_percent", 0)
            reasoning.append(f"Technical: {technical_trend} trend ({price_change_pct:.1f}% change)")
        
        # Add SMA reasoning if available
        if "price_vs_sma" in technical_signals:
            sma_position = technical_signals["price_vs_sma"]
            reasoning.append(f"Price is {sma_position} moving average")
        
        # Add volatility reasoning if available
        if "volatility_level" in technical_signals:
            vol_level = technical_signals["volatility_level"]
            reasoning.append(f"Market volatility: {vol_level}")
        
        return reasoning
    
    def _generate_prediction(self, technical_trend: str, sentiment: str) -> str:
        """Generate prediction based on technical trend and sentiment."""
        # Check for exact matches in prediction map
        key = (technical_trend, sentiment)
        if key in self.prediction_map:
            return self.prediction_map[key]
        
        # Enhanced prediction logic
        if technical_trend == "up" and sentiment in ["positive", "very positive"]:
            return "strong_buy" if sentiment == "very positive" else "buy"
        elif technical_trend == "up" or sentiment in ["positive", "very positive"]:
            return "buy"
        elif technical_trend == "down" and sentiment in ["negative", "very negative"]:
            return "strong_sell" if sentiment == "very negative" else "sell"
        elif technical_trend == "down" or sentiment in ["negative", "very negative"]:
            return "sell"
        else:
            return "hold"
    
    def _get_prediction_reasoning(self, technical_trend: str, sentiment: str, prediction: str) -> str:
        """Generate reasoning for the prediction."""
        if prediction in ["strong_buy", "strong_sell"]:
            return f"Both technical ({technical_trend}) and sentiment ({sentiment}) signals align strongly"
        elif prediction in ["buy", "sell"]:
            if technical_trend != "neutral" and sentiment != "neutral":
                return f"Technical ({technical_trend}) and sentiment ({sentiment}) signals support {prediction}"
            elif technical_trend != "neutral":
                return f"Technical signal ({technical_trend}) suggests {prediction}"
            else:
                return f"Sentiment signal ({sentiment}) suggests {prediction}"
        else:
            return "Mixed or neutral signals suggest holding position"
    
    def _assess_signal_alignment(self, technical_trend: str, sentiment: str) -> str:
        """Assess how well technical and sentiment signals align."""
        if technical_trend == "neutral" and sentiment == "neutral":
            return "neutral"
        elif technical_trend == sentiment:  # Both up/positive or down/negative
            return "strong_alignment"
        elif (technical_trend == "up" and sentiment in ["positive", "very positive"]) or \
             (technical_trend == "down" and sentiment in ["negative", "very negative"]):
            return "good_alignment"
        elif (technical_trend == "up" and sentiment in ["negative", "very negative"]) or \
             (technical_trend == "down" and sentiment in ["positive", "very positive"]):
            return "conflicting"
        else:
            return "mixed"
    
    def _calculate_combined_strength(self, technical_signals: Dict[str, Any], sentiment: str) -> str:
        """Calculate the combined strength of all signals."""
        technical_trend = technical_signals.get("trend", "neutral")
        price_change_pct = abs(technical_signals.get("price_change_percent", 0))
        
        # Technical strength
        technical_strength = 0
        if technical_trend != "neutral":
            if price_change_pct > 5:
                technical_strength = 3  # Strong
            elif price_change_pct > 2:
                technical_strength = 2  # Moderate
            else:
                technical_strength = 1  # Weak
        
        # Sentiment strength
        sentiment_strength = 0
        if sentiment in ["very positive", "very negative"]:
            sentiment_strength = 3
        elif sentiment in ["positive", "negative"]:
            sentiment_strength = 2
        elif sentiment != "neutral":
            sentiment_strength = 1
        
        # Combined strength
        total_strength = technical_strength + sentiment_strength
        
        if total_strength >= 5:
            return "very_strong"
        elif total_strength >= 3:
            return "strong"
        elif total_strength >= 2:
            return "moderate"
        elif total_strength >= 1:
            return "weak"
        else:
            return "very_weak"
    
    def get_signal_summary(self, combined_signals: Dict[str, Any]) -> Dict[str, str]:
        """Generate a human-readable summary of combined signals."""
        direction = combined_signals.get("direction", "hold")
        alignment = combined_signals.get("signal_alignment", "unknown")
        strength = combined_signals.get("combined_strength", "unknown")
        
        return {
            "recommendation": direction.replace("_", " ").title(),
            "confidence_level": strength.replace("_", " ").title(),
            "signal_quality": alignment.replace("_", " ").title(),
            "summary": f"{direction.replace('_', ' ').title()} recommendation with {strength} signals"
        }