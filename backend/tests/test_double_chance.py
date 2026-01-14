"""
Unit tests for Double Chance predictions
Tests mathematical derivation and probability validation
"""
import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.ml.double_chance_predictor import DoubleChancePredictor, get_double_chance_predictor


class TestMathematicalDerivation:
    """Test that DC probabilities are mathematically correct"""
    
    def test_probability_addition(self):
        """Verify P(1X) = P(1) + P(X)"""
        predictor = DoubleChancePredictor()
        
        prob_h, prob_d, prob_a = 0.50, 0.30, 0.20
        result = predictor.predict_from_probabilities(prob_h, prob_d, prob_a)
        
        # Test mathematical derivation
        assert abs(result['prob_1x'] - (prob_h + prob_d)) < 0.001
        assert abs(result['prob_12'] - (prob_h + prob_a)) < 0.001
        assert abs(result['prob_x2'] - (prob_d + prob_a)) < 0.001
    
    def test_probabilities_valid_range(self):
        """All DC probabilities should be valid (0-1)"""
        predictor = DoubleChancePredictor()
        
        test_cases = [
            (0.60, 0.25, 0.15),
            (0.35, 0.30, 0.35),
            (0.20, 0.25, 0.55),
        ]
        
        for ph, pd, pa in test_cases:
            result = predictor.predict_from_probabilities(ph, pd, pa)
            
            assert 0 <= result['prob_1x'] <= 1
            assert 0 <= result['prob_12'] <= 1
            assert 0 <= result['prob_x2'] <= 1
    
    def test_normalization(self):
        """Test that unnormalized probabilities are handled"""
        predictor = DoubleChancePredictor()
        
        # Probabilities that don't sum to 1.0
        result = predictor.predict_from_probabilities(0.51, 0.30, 0.20)
        
        # Should still produce valid DC probabilities
        assert 0 <= result['prob_1x'] <= 1
        assert 0 <= result['prob_12'] <= 1
        assert 0 <= result['prob_x2'] <= 1


class TestBestPrediction:
    """Test that best DC option is selected correctly"""
    
    def test_home_favorite_selects_1x(self):
        """Home favorite should recommend 1X"""
        predictor = DoubleChancePredictor()
        
        result = predictor.predict_from_probabilities(0.60, 0.25, 0.15)
        
        assert result['prediction'] == '1X'
        assert result['confidence'] >= 0.80
    
    def test_away_favorite_selects_x2(self):
        """Away favorite should recommend X2"""
        predictor = DoubleChancePredictor()
        
        result = predictor.predict_from_probabilities(0.20, 0.25, 0.55)
        
        assert result['prediction'] == 'X2'
        assert result['confidence'] >= 0.75
    
    def test_balanced_match_selects_12(self):
        """Balanced match (low draw prob) should often select 12"""
        predictor = DoubleChancePredictor()
        
        result = predictor.predict_from_probabilities(0.45, 0.10, 0.45)
        
        # 12 should be highest (0.90)
        assert result['prediction'] == '12'


class TestActualOutcome:
    """Test calculation of actual DC outcomes"""
    
    def test_home_win_outcome(self):
        """Home win triggers 1X and 12"""
        predictor = DoubleChancePredictor()
        
        outcome = predictor.calculate_dc_outcome(2, 1)
        
        assert '1X' in outcome
        assert '12' in outcome
        assert 'X2' not in outcome
    
    def test_draw_outcome(self):
        """Draw triggers 1X and X2"""
        predictor = DoubleChancePredictor()
        
        outcome = predictor.calculate_dc_outcome(1, 1)
        
        assert '1X' in outcome
        assert 'X2' in outcome
        assert outcome.count('12') == 0  # 12 doesn't include draws
    
    def test_away_win_outcome(self):
        """Away win triggers 12 and X2"""
        predictor = DoubleChancePredictor()
        
        outcome = predictor.calculate_dc_outcome(0, 2)
        
        assert '12' in outcome
        assert 'X2' in outcome
        assert '1X' not in outcome


class TestRecommendation:
    """Test betting recommendation logic"""
    
    def test_high_confidence_recommended(self):
        """High confidence (>70%) should be recommended"""
        predictor = DoubleChancePredictor()
        
        rec = predictor.get_recommendation(0.60, 0.25, 0.15, min_confidence=0.70)
        
        assert rec['recommended'] == True
        assert rec['confidence'] >= 0.70
        assert 'risk_level' in rec
    
    def test_low_confidence_not_recommended(self):
        """Low confidence should not be recommended"""
        predictor = DoubleChancePredictor()
        
        rec = predictor.get_recommendation(0.35, 0.35, 0.30, min_confidence=0.75)
        
        assert rec['recommended'] == False
        assert 'reason' in rec
    
    def test_risk_levels(self):
        """Test risk level classification"""
        predictor = DoubleChancePredictor()
        
        # High confidence = Low risk
        rec_high = predictor.get_recommendation(0.65, 0.25, 0.10)
        assert rec_high['risk_level'] == 'Low'
        
        # Medium confidence = Medium risk
        rec_med = predictor.get_recommendation(0.50, 0.25, 0.25)
        assert rec_med['risk_level'] == 'Medium'


class TestSingletonInstance:
    """Test that global instance works correctly"""
    
    def test_get_predictor(self):
        """Test getting global predictor instance"""
        predictor = get_double_chance_predictor()
        
        assert isinstance(predictor, DoubleChancePredictor)
        
        # Should return same instance
        predictor2 = get_double_chance_predictor()
        assert predictor is predictor2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
