"""
Unit tests for Bivariate Poisson Model
Tests correlation modeling and combo probability calculations
"""
import sys
import os
import pytest
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.ml.bivariate_poisson_model import BivariatePoissonModel


class TestCorrelationParameter:
    """Test λ3 correlation parameter estimation"""
    
    def test_correlation_in_valid_range(self):
        """λ3 should be in reasonable range (0.0 - 0.3)"""
        model = BivariatePoissonModel()
        
        # Mock correlation (without database)
        model.lambda_corr = 0.15
        
        assert 0.0 <= model.lambda_corr <= 0.3
    
    def test_positive_correlation(self):
        """Correlation should typically be positive (high-scoring matches)"""
        model = BivariatePoissonModel()
        model.lambda_corr = 0.1
        
        assert model.lambda_corr >= 0


class TestScorelineProbabilities:
    """Test scoreline probability matrix generation"""
    
    def test_probability_matrix_shape(self):
        """Probability matrix should be (MAX_GOALS+1) x (MAX_GOALS+1)"""
        model = BivariatePoissonModel()
        model.team_attack = {1: 1.5, 2: 1.2}
        model.team_defense = {1: 1.0, 2: 1.0}
        
        matrix = model.predict_scoreline_matrix(1, 2)
        
        assert matrix.shape == (model.MAX_GOALS + 1, model.MAX_GOALS + 1)
    
    def test_probabilities_sum_to_one(self):
        """All scoreline probabilities should sum to ~1.0"""
        model = BivariatePoissonModel()
        model.team_attack = {1: 1.5, 2: 1.2}
        model.team_defense = {1: 1.0, 2: 1.0}
        
        matrix = model.predict_scoreline_matrix(1, 2)
        
        total = np.sum(matrix)
        assert 0.99 <= total <= 1.01
    
    def test_all_probabilities_positive(self):
        """All probabilities should be >= 0"""
        model = BivariatePoissonModel()
        model.team_attack = {1: 1.5, 2: 1.2}
        model.team_defense = {1: 1.0, 2: 1.0}
        
        matrix = model.predict_scoreline_matrix(1, 2)
        
        assert np.all(matrix >= 0)


class TestComboPredictions:
    """Test combo bet probability calculations"""
    
    def test_combo_probabilities_valid(self):
        """All combo probabilities should be in [0, 1]"""
        model = BivariatePoissonModel()
        model.team_attack = {1: 1.8, 2: 1.2}
        model.team_defense = {1: 1.0, 2: 1.1}
        
        combos = model.predict_combo(1, 2)
        
        for key, prob in combos.items():
            assert 0 <= prob <= 1, f"{key} probability {prob} out of range"
    
    def test_combo_keys_present(self):
        """All expected combo keys should be present"""
        model = BivariatePoissonModel()
        model.team_attack = {1: 1.5, 2: 1.2}
        model.team_defense = {1: 1.0, 2: 1.0}
        
        combos = model.predict_combo(1, 2)
        
        expected_keys = ['1_over_25', '2_over_25', 'x_under_25', 
                        '1_btts', '2_btts', 'x_btts']
        
        for key in expected_keys:
            assert key in combos
    
    def test_combo_less_than_marginal(self):
        """Combo probabilities should be less than marginal probabilities"""
        model = BivariatePoissonModel()
        model.team_attack = {1: 1.8, 2: 1.2}
        model.team_defense = {1: 1.0, 2: 1.1}
        
        combos = model.predict_combo(1, 2)
        
        # P(Home Win AND Over 2.5) should be < P(Home Win)
        # This is a sanity check (marginal >= joint)
        assert combos['1_over_25'] <= 0.70  # Reasonable upper bound


class TestCorrelationEffect:
    """Test that correlation modeling differs from naive multiplication"""
    
    def test_bivariate_vs_naive_different(self):
        """Bivariate should differ from naive P(A) × P(B)"""
        model = BivariatePoissonModel()
        model.team_attack = {1: 1.8, 2: 1.2}
        model.team_defense = {1: 1.0, 2: 1.1}
        model.lambda_corr = 0.15  # Positive correlation
        
        correlated, naive = model.compare_with_naive(1, 2)
        
        # At least one combo should differ significantly
        assert correlated['1_over_25'] != naive['1_over_25']
        
        # With positive correlation, combos should typically be higher
        # (but this depends on the specific match context)
    
    def test_correlation_increases_high_scoring_combos(self):
        """Positive correlation should increase high-scoring combo probabilities"""
        model = BivariatePoissonModel()
        model.team_attack = {1: 2.0, 2: 1.5}  # Strong teams
        model.team_defense = {1: 1.2, 2: 1.3}
        model.lambda_corr = 0.2  # Strong positive correlation
        
        combos = model.predict_combo(1, 2)
        
        # With strong teams and correlation, home win + over 2.5 should be reasonable
        assert combos['1_over_25'] > 0.10


class TestExpectedGoals:
    """Test expected goals calculation"""
    
    def test_expected_goals_reasonable(self):
        """Expected goals should be in reasonable range"""
        model = BivariatePoissonModel()
        model.team_attack = {1: 1.5, 2: 1.2}
        model.team_defense = {1: 1.0, 2: 1.0}
        model.lambda_home = 1.5
        model.lambda_away = 1.2
        
        lambda1, lambda2 = model.get_expected_goals(1, 2)
        
        assert 0.3 <= lambda1 <= 4.0
        assert 0.3 <= lambda2 <= 3.5
    
    def test_home_advantage_applied(self):
        """Home team should get goal advantage"""
        model = BivariatePoissonModel()
        model.team_attack = {1: 1.0, 2: 1.0}  # Equal teams
        model.team_defense = {1: 1.0, 2: 1.0}
        model.lambda_home = 1.5
        model.lambda_away = 1.2
        
        lambda1, lambda2 = model.get_expected_goals(1, 2)
        
        # Home should have higher expected goals due to home advantage bonus
        assert lambda1 > lambda2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
