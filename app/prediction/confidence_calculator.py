"""Confidence calculation for prediction accuracy assessment."""

import json
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class ConfidenceCalculator:
    """Calculates confidence levels for predictions based on multiple factors."""
    
    def __init__(self):
        self.ai_confidence_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
        self.min_confidence = 0.1
        self.max_confidence = 0.95
        
        # Weights for different factors
        self.weights = {
            "base": 0.2,
            "ai_confidence": 0.3,
            "data_quality": 0.25,
            "signal_alignment": 0.25
        }
    
    def calculate_confidence(self, prediction: Dict[str, Any], ai_analysis: Dict[str, Any], 
                           technical_signals: Dict[str, Any], post_count: int) -> float:
        """
        Calculate confidence level for the prediction with improved logic.
        
        Args:
            prediction: Combined prediction results
            ai_analysis: AI sentiment analysis results
            technical_signals: Technical analysis results
            post_count: Number of posts analyzed
            
        Returns:
            Confidence score between 0.1 and 0.95
        """
        try:
            # Extract components
            ai_confidence_factor = self._calculate_ai_confidence_factor(ai_analysis)
            data_quality_factor = self._calculate_data_quality_factor(post_count, technical_signals)
            signal_alignment_factor = self._calculate_signal_alignment_factor(prediction)
            base_factor = self._calculate_base_factor()
            
            # Calculate weighted confidence
            final_confidence = (
                base_factor * self.weights["base"] +
                ai_confidence_factor * self.weights["ai_confidence"] +
                data_quality_factor * self.weights["data_quality"] +
                signal_alignment_factor * self.weights["signal_alignment"]
            )
            
            # Apply prediction type multiplier
            prediction_multiplier = self._get_prediction_multiplier(prediction)
            final_confidence *= prediction_multiplier
            
            # Ensure confidence is within bounds
            final_confidence = max(self.min_confidence, min(self.max_confidence, final_confidence))
            
            # Log calculation details
            self._log_confidence_calculation(
                ai_confidence_factor, data_quality_factor, signal_alignment_factor,
                prediction_multiplier, final_confidence
            )
            
            return round(final_confidence, 2)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.4  # Conservative fallback
    
    def _calculate_ai_confidence_factor(self, ai_analysis: Dict[str, Any]) -> float:
        """Calculate confidence factor based on AI analysis quality."""
        try:
            ai_result = ai_analysis.get("ai_analysis", {})
            if isinstance(ai_result, str):
                ai_result = json.loads(ai_result)
            
            ai_confidence = ai_result.get("confidence", "medium")
            return self.ai_confidence_map.get(ai_confidence, 0.5)
            
        except Exception:
            return 0.5  # Default medium confidence
    
    def _calculate_data_quality_factor(self, post_count: int, technical_signals: Dict[str, Any]) -> float:
        """Calculate confidence factor based on data quality and quantity."""
        # Posts quality factor (0.3 to 1.0)
        posts_factor = min(1.0, post_count / 20)  # Max confidence at 20+ posts
        
        # Technical data quality factor
        tech_quality = technical_signals.get("data_quality", "limited")
        tech_factor = 1.0 if tech_quality == "good" else 0.7
        
        # Combine factors (weighted average)
        return (posts_factor * 0.6) + (tech_factor * 0.4)
    
    def _calculate_signal_alignment_factor(self, prediction: Dict[str, Any]) -> float:
        """Calculate confidence factor based on signal alignment."""
        alignment = prediction.get("signal_alignment", "mixed")
        combined_strength = prediction.get("combined_strength", "weak")
        
        # Alignment factor
        alignment_scores = {
            "strong_alignment": 1.0,
            "good_alignment": 0.8,
            "neutral": 0.6,
            "mixed": 0.4,
            "conflicting": 0.2
        }
        alignment_factor = alignment_scores.get(alignment, 0.5)
        
        # Strength factor
        strength_scores = {
            "very_strong": 1.0,
            "strong": 0.8,
            "moderate": 0.6,
            "weak": 0.4,
            "very_weak": 0.2
        }
        strength_factor = strength_scores.get(combined_strength, 0.5)
        
        # Combined factor (weighted average)
        return (alignment_factor * 0.6) + (strength_factor * 0.4)
    
    def _calculate_base_factor(self) -> float:
        """Calculate base confidence factor."""
        return 0.5  # Neutral starting point
    
    def _get_prediction_multiplier(self, prediction: Dict[str, Any]) -> float:
        """Get multiplier based on prediction type."""
        direction = prediction.get("direction", "hold")
        
        # Strong predictions get higher confidence if signals align
        if direction in ["strong_buy", "strong_sell"]:
            alignment = prediction.get("signal_alignment", "mixed")
            if alignment in ["strong_alignment", "good_alignment"]:
                return 1.2  # Boost confidence for aligned strong signals
            else:
                return 0.8  # Reduce confidence for conflicting strong signals
        
        # Regular buy/sell predictions
        elif direction in ["buy", "sell"]:
            return 1.0  # Neutral multiplier
        
        # Hold predictions (typically lower confidence)
        else:
            return 0.8
    
    def _log_confidence_calculation(self, ai_factor: float, data_factor: float, 
                                  alignment_factor: float, multiplier: float, 
                                  final_confidence: float):
        """Log confidence calculation details for debugging."""
        logger.debug(
            f"Confidence calculation: "
            f"AI={ai_factor:.2f}, Data={data_factor:.2f}, "
            f"Alignment={alignment_factor:.2f}, Multiplier={multiplier:.2f} "
            f"→ Final={final_confidence:.2f}"
        )
    
    def get_confidence_breakdown(self, prediction: Dict[str, Any], ai_analysis: Dict[str, Any], 
                               technical_signals: Dict[str, Any], post_count: int) -> Dict[str, Any]:
        """Get detailed breakdown of confidence calculation."""
        try:
            ai_factor = self._calculate_ai_confidence_factor(ai_analysis)
            data_factor = self._calculate_data_quality_factor(post_count, technical_signals)
            alignment_factor = self._calculate_signal_alignment_factor(prediction)
            multiplier = self._get_prediction_multiplier(prediction)
            
            return {
                "components": {
                    "ai_confidence": {
                        "value": ai_factor,
                        "weight": self.weights["ai_confidence"],
                        "contribution": ai_factor * self.weights["ai_confidence"]
                    },
                    "data_quality": {
                        "value": data_factor,
                        "weight": self.weights["data_quality"],
                        "contribution": data_factor * self.weights["data_quality"]
                    },
                    "signal_alignment": {
                        "value": alignment_factor,
                        "weight": self.weights["signal_alignment"],
                        "contribution": alignment_factor * self.weights["signal_alignment"]
                    }
                },
                "prediction_multiplier": multiplier,
                "factors_summary": {
                    "posts_analyzed": post_count,
                    "technical_data_quality": technical_signals.get("data_quality", "unknown"),
                    "signal_alignment": prediction.get("signal_alignment", "unknown"),
                    "combined_strength": prediction.get("combined_strength", "unknown")
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating confidence breakdown: {e}")
            return {"error": str(e)}
    
    def get_confidence_level_description(self, confidence: float) -> str:
        """Get human-readable description of confidence level."""
        if confidence >= 0.8:
            return "Very High - Strong conviction in prediction"
        elif confidence >= 0.7:
            return "High - Good confidence in prediction"
        elif confidence >= 0.6:
            return "Moderate - Reasonable confidence"
        elif confidence >= 0.4:
            return "Low - Limited confidence"
        else:
            return "Very Low - Weak confidence, proceed with caution"
    
    def should_act_on_prediction(self, confidence: float, prediction_direction: str) -> Dict[str, Any]:
        """Determine if prediction confidence is sufficient for action."""
        min_action_confidence = {
            "strong_buy": 0.7,
            "strong_sell": 0.7,
            "buy": 0.6,
            "sell": 0.6,
            "hold": 0.3
        }
        
        required_confidence = min_action_confidence.get(prediction_direction, 0.6)
        should_act = confidence >= required_confidence
        
        return {
            "should_act": should_act,
            "required_confidence": required_confidence,
            "actual_confidence": confidence,
            "confidence_gap": confidence - required_confidence,
            "recommendation": "Act on prediction" if should_act else "Wait for better signals"
        }