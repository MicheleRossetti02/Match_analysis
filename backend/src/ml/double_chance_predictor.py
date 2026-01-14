"""
Double Chance Prediction Service
Provides predictions for Double Chance markets using mathematical probability derivation
"""
from typing import Dict, Tuple


class DoubleChancePredictor:
    """
    Generate Double Chance predictions from 1X2 probabilities
    
    Double Chance reduces risk by combining two outcomes:
    - 1X: Home Win OR Draw (safest when home team favored)
    - 12: Home Win OR Away Win (no draw)
    - X2: Draw OR Away Win (safest when away team or draw likely)
    """
    
    def predict_from_probabilities(
        self, 
        prob_home: float, 
        prob_draw: float, 
        prob_away: float
    ) -> Dict[str, float]:
        """
        Calculate Double Chance probabilities using mathematical derivation
        
        Mathematical Foundation:
        - P(1X) = P(Home) + P(Draw)  [mutually exclusive events]
        - P(12) = P(Home) + P(Away)
        - P(X2) = P(Draw) + P(Away)
        
        Args:
            prob_home: Probability of home win (0-1)
            prob_draw: Probability of draw (0-1)
            prob_away: Probability of away win (0-1)
            
        Returns:
            Dict with DC probabilities and best prediction
            
        Example:
            >>> predictor = DoubleChancePredictor()
            >>> result = predictor.predict_from_probabilities(0.50, 0.30, 0.20)
            >>> result['1X']  # Home or Draw
            0.80
        """
        # Validate inputs
        total = prob_home + prob_draw + prob_away
        if not (0.99 <= total <= 1.01):
            # Normalize if not exactly 1.0 due to floating point
            prob_home /= total
            prob_draw /= total
            prob_away /= total
        
        # Calculate Double Chance probabilities (simple addition)
        prob_1x = prob_home + prob_draw  # Home or Draw
        prob_12 = prob_home + prob_away  # Home or Away (No draw)
        prob_x2 = prob_draw + prob_away  # Draw or Away
        
        # Find best DC option (highest probability)
        dc_options = {
            '1X': prob_1x,
            '12': prob_12,
            'X2': prob_x2
        }
        
        best_dc = max(dc_options, key=dc_options.get)
        best_confidence = dc_options[best_dc]
        
        return {
            'prob_1x': prob_1x,
            'prob_12': prob_12,
            'prob_x2': prob_x2,
            'prediction': best_dc,
            'confidence': best_confidence,
            'breakdown': {
                '1X': f"Home({prob_home:.2%}) + Draw({prob_draw:.2%}) = {prob_1x:.2%}",
                '12': f"Home({prob_home:.2%}) + Away({prob_away:.2%}) = {prob_12:.2%}",
                'X2': f"Draw({prob_draw:.2%}) + Away({prob_away:.2%}) = {prob_x2:.2%}"
            }
        }
    
    def calculate_dc_outcome(self, home_goals: int, away_goals: int) -> str:
        """
        Calculate actual Double Chance outcome from match result
        
        Args:
            home_goals: Goals scored by home team
            away_goals: Goals scored by away team
            
        Returns:
            String indicating which DC markets won: "1X", "12", "X2", or "1X,X2" (if draw)
        """
        if home_goals > away_goals:
            # Home win: 1X and 12 both win
            return "1X,12"
        elif home_goals < away_goals:
            # Away win: 12 and X2 both win
            return "12,X2"
        else:
            # Draw: 1X and X2 both win
            return "1X,X2"
    
    def get_recommendation(
        self, 
        prob_home: float, 
        prob_draw: float, 
        prob_away: float,
        min_confidence: float = 0.70
    ) -> Dict:
        """
        Get betting recommendation with confidence threshold
        
        Args:
            prob_home: Probability of home win
            prob_draw: Probability of draw
            prob_away: Probability of away win
            min_confidence: Minimum confidence to recommend (default 70%)
            
        Returns:
            Dict with recommendation and reasoning
        """
        dc_probs = self.predict_from_probabilities(prob_home, prob_draw, prob_away)
        
        if dc_probs['confidence'] >= min_confidence:
            return {
                'recommended': True,
                'market': dc_probs['prediction'],
                'confidence': dc_probs['confidence'],
                'reasoning': dc_probs['breakdown'][dc_probs['prediction']],
                'risk_level': 'Low' if dc_probs['confidence'] >= 0.80 else 'Medium'
            }
        else:
            return {
                'recommended': False,
                'reason': f"Confidence {dc_probs['confidence']:.1%} below threshold {min_confidence:.0%}",
                'best_option': dc_probs['prediction'],
                'all_probabilities': {
                    '1X': dc_probs['prob_1x'],
                    '12': dc_probs['prob_12'],
                    'X2': dc_probs['prob_x2']
                }
            }


# Singleton instance
_dc_predictor = None


def get_double_chance_predictor() -> DoubleChancePredictor:
    """Get or create the global Double Chance predictor"""
    global _dc_predictor
    
    if _dc_predictor is None:
        _dc_predictor = DoubleChancePredictor()
    
    return _dc_predictor


if __name__ == "__main__":
    print("\n⚽ Double Chance Predictor Demo\n")
    print("=" * 60)
    
    # Example scenarios
    scenarios = [
        ("Home Favorite", 0.60, 0.25, 0.15),
        ("Balanced Match", 0.35, 0.30, 0.35),
        ("Away Favorite", 0.20, 0.25, 0.55),
        ("Draw Likely", 0.30, 0.45, 0.25),
    ]
    
    predictor = DoubleChancePredictor()
    
    for name, ph, pd, pa in scenarios:
        print(f"\n📊 {name}")
        print(f"   1X2: Home {ph:.0%} | Draw {pd:.0%} | Away {pa:.0%}")
        
        result = predictor.predict_from_probabilities(ph, pd, pa)
        
        print(f"\n   Double Chance Probabilities:")
        print(f"   • 1X (Home/Draw): {result['prob_1x']:.1%}")
        print(f"   • 12 (Home/Away): {result['prob_12']:.1%}")
        print(f"   • X2 (Draw/Away): {result['prob_x2']:.1%}")
        
        print(f"\n   ✅ Best Bet: {result['prediction']} ({result['confidence']:.1%})")
        
        recommendation = predictor.get_recommendation(ph, pd, pa)
        if recommendation['recommended']:
            print(f"   💰 RECOMMENDED - {recommendation['risk_level']} Risk")
        else:
            print(f"   ⚠️  Not recommended: {recommendation['reason']}")
        
        print("   " + "-" * 56)
    
    print("\n✅ Double Chance predictor ready!\n")
