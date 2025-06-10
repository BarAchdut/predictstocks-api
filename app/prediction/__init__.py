"""Prediction services for stock analysis."""

from app.prediction_service import PredictionService
from .technical_analyzer import TechnicalAnalyzer
from .signal_combiner import SignalCombiner
from .confidence_calculator import ConfidenceCalculator

# Make PredictionService available as AIPredictionService for backward compatibility
AIPredictionService = PredictionService

__all__ = [
    'PredictionService',
    'AIPredictionService',
    'TechnicalAnalyzer',
    'SignalCombiner', 
    'ConfidenceCalculator'
]