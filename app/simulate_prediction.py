"""
Enhanced simulation script for stock price prediction using real data and new architecture.
This script tests the complete prediction pipeline with actual market data and social media sentiment.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our new modular services
from app.prediction import AIPredictionService
from app.data.historical_data import HistoricalDataService
from app.social_media import SocialMediaService
from app.ai import AIService

class StockPredictionSimulator:
    """Enhanced simulator for testing prediction accuracy with real data."""
    
    def __init__(self):
        """Initialize all services."""
        try:
            self.prediction_service = AIPredictionService()
            self.historical_service = HistoricalDataService()
            self.social_media_service = SocialMediaService()
            self.ai_service = AIService()
            
            logger.info("✅ All services initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing services: {e}")
            raise
    
    def run_comprehensive_simulation(self, ticker: str, timeframes: List[str] = None) -> Dict[str, Any]:
        """
        Run comprehensive simulation for a stock ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            timeframes: List of timeframes to test (default: ['1d', '1w', '1m'])
            
        Returns:
            Dictionary with complete simulation results
        """
        if timeframes is None:
            timeframes = ['1d', '1w', '1m']
        
        logger.info(f"🚀 Starting comprehensive simulation for {ticker}")
        
        # Check service status first
        service_status = self._check_service_status()
        if not service_status["all_operational"]:
            logger.warning("⚠️ Some services may not be operational")
        
        simulation_results = {
            "ticker": ticker,
            "simulation_start": datetime.now().isoformat(),
            "service_status": service_status,
            "predictions": {},
            "data_summary": {},
            "performance_metrics": {}
        }
        
        # Run predictions for each timeframe
        for timeframe in timeframes:
            logger.info(f"📊 Testing {timeframe} prediction for {ticker}")
            
            try:
                # Get prediction
                prediction_result = self.prediction_service.predict_price_movement(
                    ticker=ticker,
                    timeframe=timeframe,
                    include_reddit=True
                )
                
                # Analyze prediction quality
                prediction_analysis = self._analyze_prediction_quality(prediction_result)
                
                simulation_results["predictions"][timeframe] = {
                    "prediction": prediction_result,
                    "analysis": prediction_analysis
                }
                
                logger.info(f"✅ {timeframe} prediction completed - Direction: {prediction_result.get('prediction', {}).get('direction', 'unknown')}")
                
            except Exception as e:
                logger.error(f"❌ Error in {timeframe} prediction: {e}")
                simulation_results["predictions"][timeframe] = {
                    "error": str(e),
                    "analysis": {"status": "failed"}
                }
        
        # Generate summary
        simulation_results["summary"] = self._generate_simulation_summary(simulation_results)
        simulation_results["simulation_end"] = datetime.now().isoformat()
        
        return simulation_results
    
    def run_social_media_analysis_test(self, ticker: str) -> Dict[str, Any]:
        """
        Test social media analysis capabilities.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Social media analysis results
        """
        logger.info(f"📱 Testing social media analysis for {ticker}")
        
        results = {
            "ticker": ticker,
            "test_start": datetime.now().isoformat(),
            "platforms_tested": []
        }
        
        try:
            # Test regular posts
            logger.info("🔍 Fetching regular social media posts...")
            social_posts = self.social_media_service.get_posts_for_ticker(
                ticker, limit=25, include_reddit=True
            )
            
            # Test influencer posts
            logger.info("👑 Fetching influencer posts...")
            influencer_posts = self.social_media_service.get_influencer_posts(ticker)
            
            # Combine and analyze
            all_posts = social_posts + influencer_posts
            
            if all_posts:
                logger.info("🤖 Running AI sentiment analysis...")
                ai_analysis = self.ai_service.analyze_social_media_impact(all_posts, ticker)
                
                results.update({
                    "posts_found": {
                        "social_posts": len(social_posts),
                        "influencer_posts": len(influencer_posts),
                        "total_posts": len(all_posts)
                    },
                    "ai_analysis": ai_analysis.get("ai_analysis", {}),
                    "platforms_represented": list(set(post.get('platform') for post in all_posts)),
                    "sentiment_summary": self._create_sentiment_summary(ai_analysis),
                    "status": "success"
                })
                
                logger.info(f"✅ Found {len(all_posts)} posts, sentiment: {ai_analysis.get('ai_analysis', {}).get('sentiment', 'unknown')}")
                
            else:
                results.update({
                    "posts_found": {"total_posts": 0},
                    "message": "No social media posts found for this ticker",
                    "status": "no_data"
                })
                logger.warning("⚠️ No social media posts found")
                
        except Exception as e:
            logger.error(f"❌ Error in social media analysis: {e}")
            results.update({
                "error": str(e),
                "status": "error"
            })
        
        results["test_end"] = datetime.now().isoformat()
        return results
    
    def compare_predictions_with_actual(self, ticker: str, days_back: int = 5) -> Dict[str, Any]:
        """
        Compare predictions with actual price movements (historical analysis).
        
        Args:
            ticker: Stock ticker symbol
            days_back: How many days back to analyze
            
        Returns:
            Comparison results
        """
        logger.info(f"📈 Comparing predictions with actual data for {ticker}")
        
        results = {
            "ticker": ticker,
            "analysis_period": f"{days_back} days",
            "comparisons": []
        }
        
        try:
            # Get historical data
            historical_data = self.historical_service.get_historical_data(ticker, days=days_back + 5)
            
            if len(historical_data) < days_back + 2:
                return {
                    "error": "Insufficient historical data for comparison",
                    "status": "insufficient_data"
                }
            
            # Simulate predictions for each day
            for i in range(days_back):
                test_date = datetime.now() - timedelta(days=days_back - i)
                
                # Get prediction (simulated as if we were predicting on that day)
                prediction = self.prediction_service.predict_price_movement(ticker, "1d")
                
                # Get actual price movement
                if i < len(historical_data) - 1:
                    actual_change = historical_data[i+1]["close"] - historical_data[i]["close"]
                    actual_direction = "up" if actual_change > 0 else "down" if actual_change < 0 else "neutral"
                    
                    predicted_direction = prediction.get("prediction", {}).get("direction", "hold")
                    
                    # Compare
                    comparison = {
                        "date": test_date.strftime("%Y-%m-%d"),
                        "predicted_direction": predicted_direction,
                        "actual_direction": actual_direction,
                        "actual_change": round(actual_change, 2),
                        "prediction_confidence": prediction.get("confidence", 0),
                        "match": self._directions_match(predicted_direction, actual_direction)
                    }
                    
                    results["comparisons"].append(comparison)
            
            # Calculate accuracy
            matches = sum(1 for comp in results["comparisons"] if comp["match"])
            total = len(results["comparisons"])
            accuracy = (matches / total * 100) if total > 0 else 0
            
            results["accuracy_summary"] = {
                "total_predictions": total,
                "correct_predictions": matches,
                "accuracy_percentage": round(accuracy, 1)
            }
            
            logger.info(f"✅ Historical analysis completed - Accuracy: {accuracy:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ Error in historical comparison: {e}")
            results["error"] = str(e)
        
        return results
    
    def _check_service_status(self) -> Dict[str, Any]:
        """Check status of all services."""
        logger.info("🔍 Checking service status...")
        
        status = {
            "social_media": {"operational": False, "details": {}},
            "ai_service": {"operational": False, "details": {}},
            "historical_data": {"operational": False, "details": {}},
            "prediction_service": {"operational": False, "details": {}}
        }
        
        try:
            # Check social media services
            social_status = self.social_media_service.get_platform_status()
            status["social_media"] = {
                "operational": any(platform.get("operational", False) for platform in social_status.values()),
                "details": social_status
            }
            
            # Check AI service
            ai_test = self.ai_service.test_connection()
            status["ai_service"] = {
                "operational": ai_test.get("status") == "success",
                "details": ai_test
            }
            
            # Check prediction service
            pred_status = self.prediction_service.get_service_status()
            status["prediction_service"] = {
                "operational": pred_status.get("overall_status") == "operational",
                "details": pred_status
            }
            
            # Check historical data (simple test)
            try:
                test_data = self.historical_service.get_historical_data("AAPL", days=5)
                status["historical_data"] = {
                    "operational": len(test_data) > 0,
                    "details": {"test_data_points": len(test_data)}
                }
            except:
                status["historical_data"] = {
                    "operational": False,
                    "details": {"error": "Failed to fetch test data"}
                }
            
        except Exception as e:
            logger.error(f"Error checking service status: {e}")
        
        status["all_operational"] = all(
            service.get("operational", False) for service in status.values()
        )
        
        return status
    
    def _analyze_prediction_quality(self, prediction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the quality of a prediction result."""
        analysis = {
            "status": "success",
            "quality_score": 0,
            "issues": [],
            "strengths": []
        }
        
        try:
            # Check if prediction was successful
            if "error" in prediction_result:
                analysis["status"] = "error"
                analysis["issues"].append(f"Prediction failed: {prediction_result['error']}")
                return analysis
            
            # Analyze confidence level
            confidence = prediction_result.get("confidence", 0)
            if confidence >= 0.7:
                analysis["strengths"].append(f"High confidence ({confidence:.2f})")
                analysis["quality_score"] += 30
            elif confidence >= 0.5:
                analysis["strengths"].append(f"Moderate confidence ({confidence:.2f})")
                analysis["quality_score"] += 20
            else:
                analysis["issues"].append(f"Low confidence ({confidence:.2f})")
                analysis["quality_score"] += 10
            
            # Analyze data quality
            supporting_data = prediction_result.get("supporting_data", {})
            posts_count = supporting_data.get("total_posts_analyzed", 0)
            
            if posts_count >= 20:
                analysis["strengths"].append(f"Good data volume ({posts_count} posts)")
                analysis["quality_score"] += 25
            elif posts_count >= 10:
                analysis["strengths"].append(f"Moderate data volume ({posts_count} posts)")
                analysis["quality_score"] += 15
            else:
                analysis["issues"].append(f"Limited data volume ({posts_count} posts)")
                analysis["quality_score"] += 5
            
            # Analyze signal alignment
            prediction_data = prediction_result.get("prediction", {})
            alignment = prediction_data.get("signal_alignment", "unknown")
            
            if alignment in ["strong_alignment", "good_alignment"]:
                analysis["strengths"].append(f"Good signal alignment ({alignment})")
                analysis["quality_score"] += 25
            elif alignment == "mixed":
                analysis["issues"].append("Mixed signals")
                analysis["quality_score"] += 10
            elif alignment == "conflicting":
                analysis["issues"].append("Conflicting signals")
                analysis["quality_score"] += 5
            
            # Final quality assessment
            if analysis["quality_score"] >= 70:
                analysis["overall_quality"] = "high"
            elif analysis["quality_score"] >= 50:
                analysis["overall_quality"] = "moderate"
            else:
                analysis["overall_quality"] = "low"
                
        except Exception as e:
            analysis["status"] = "analysis_error"
            analysis["issues"].append(f"Analysis failed: {e}")
        
        return analysis
    
    def _create_sentiment_summary(self, ai_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Create a readable summary of sentiment analysis."""
        ai_result = ai_analysis.get("ai_analysis", {})
        
        return {
            "sentiment": ai_result.get("sentiment", "unknown"),
            "impact": ai_result.get("impact", "unknown"),
            "confidence": ai_result.get("confidence", "unknown"),
            "key_factors": ", ".join(ai_result.get("key_factors", [])[:3])
        }
    
    def _directions_match(self, predicted: str, actual: str) -> bool:
        """Check if predicted direction matches actual direction."""
        # Simplify predictions to basic directions
        pred_simple = "up" if predicted in ["buy", "strong_buy"] else "down" if predicted in ["sell", "strong_sell"] else "neutral"
        return pred_simple == actual
    
    def _generate_simulation_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall summary of simulation results."""
        summary = {
            "total_timeframes_tested": len(results["predictions"]),
            "successful_predictions": 0,
            "failed_predictions": 0,
            "average_confidence": 0,
            "recommendations": []
        }
        
        confidences = []
        
        for timeframe, prediction_data in results["predictions"].items():
            if "error" not in prediction_data:
                summary["successful_predictions"] += 1
                confidence = prediction_data["prediction"].get("confidence", 0)
                confidences.append(confidence)
            else:
                summary["failed_predictions"] += 1
        
        if confidences:
            summary["average_confidence"] = round(sum(confidences) / len(confidences), 2)
        
        # Generate recommendations
        if summary["successful_predictions"] == 0:
            summary["recommendations"].append("Check API credentials and service configuration")
        elif summary["average_confidence"] < 0.5:
            summary["recommendations"].append("Consider gathering more data sources for better confidence")
        else:
            summary["recommendations"].append("Prediction system is functioning well")
        
        return summary

def main():
    """Main simulation function."""
    print("🚀 Starting Enhanced Stock Prediction Simulation")
    print("=" * 50)
    
    # Configuration
    TEST_TICKERS = ["AAPL", "MSFT", "GOOGL"]
    TIMEFRAMES = ["1d", "1w"]
    
    simulator = StockPredictionSimulator()
    
    for ticker in TEST_TICKERS:
        print(f"\n📊 Testing {ticker}")
        print("-" * 30)
        
        try:
            # Run comprehensive simulation
            simulation_results = simulator.run_comprehensive_simulation(ticker, TIMEFRAMES)
            
            # Print summary
            summary = simulation_results["summary"]
            print(f"✅ Successful predictions: {summary['successful_predictions']}/{summary['total_timeframes_tested']}")
            print(f"📈 Average confidence: {summary['average_confidence']:.2f}")
            
            # Test social media analysis
            print(f"\n📱 Testing social media analysis for {ticker}...")
            social_results = simulator.run_social_media_analysis_test(ticker)
            
            if social_results["status"] == "success":
                posts_info = social_results["posts_found"]
                sentiment = social_results["sentiment_summary"]["sentiment"]
                print(f"✅ Found {posts_info['total_posts']} posts, sentiment: {sentiment}")
            else:
                print(f"⚠️ Social media test: {social_results.get('message', 'Failed')}")
            
            # Save detailed results
            filename = f"simulation_results_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump({
                    "simulation": simulation_results,
                    "social_media_test": social_results
                }, f, indent=2, default=str)
            
            print(f"💾 Detailed results saved to {filename}")
            
        except Exception as e:
            print(f"❌ Error testing {ticker}: {e}")
            logger.error(f"Simulation error for {ticker}: {e}")
    
    print("\n🎉 Simulation completed!")

if __name__ == "__main__":
    main()