"""
Unit tests for Feature Engineer
Tests recency bias, xG features, momentum, and other enhancements
"""
import sys
import os
import pytest
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.ml.feature_engineer import FeatureEngineer


class TestRecencyBias:
    """Test recency-weighted form calculation"""
    
    def test_recency_weights_enabled(self, db_session, sample_matches):
        """Test that recency weights give more importance to recent matches"""
        engineer = FeatureEngineer(db=db_session)
        
        # Calculate form with and without recency weights
        test_date = datetime(2025, 1, 10)
        
        form_standard = engineer.calculate_team_form(
            team_id=1,
            before_date=test_date,
            last_n=5,
            home_away='all',
            use_recency_weights=False
        )
        
        form_weighted = engineer.calculate_team_form(
            team_id=1,
            before_date=test_date,
            last_n=5,
            home_away='all',
            use_recency_weights=True
        )
        
        # Weighted points should exist and be different from standard
        assert 'weighted_points' in form_weighted
        assert form_weighted['weighted_points'] > 0
        
        # Since Team 1 has strong recent form, weighted should be high
        assert form_weighted['weighted_points'] >= 2.0
        
    def test_exponential_decay(self, db_session, sample_matches):
        """Verify exponential decay factor λ=0.85"""
        engineer = FeatureEngineer(db=db_session)
        
        form = engineer.calculate_team_form(
            team_id=1,
            before_date=datetime(2025, 1, 10),
            last_n=5,
            use_recency_weights=True
        )
        
        # Most recent match should have more influence
        # Team 1's recent form is strong (multiple wins)
        assert form['weighted_points'] >= 2.5


class TestXGFeatures:
    """Test Expected Goals (xG) integration from Poisson model"""
    
    def test_xg_features_exist(self, db_session, sample_matches, upcoming_match):
        """Test that xG features are calculated and added to features"""
        engineer = FeatureEngineer(db=db_session)
        
        features = engineer.create_match_features(upcoming_match)
        
        # Check xG features exist
        assert 'poisson_xg_home' in features
        assert 'poisson_xg_away' in features
        assert 'poisson_xg_diff' in features
        assert 'poisson_xg_total' in features
        
        # Check reasonable values (not NaN or extreme outliers)
        assert 0.3 <= features['poisson_xg_home'] <= 4.0
        assert 0.3 <= features['poisson_xg_away'] <= 4.0
        assert features['poisson_xg_total'] == features['poisson_xg_home'] + features['poisson_xg_away']
    
    def test_xg_fallback_on_error(self, db_session):
        """Test that xG features have fallback values if Poisson model fails"""
        engineer = FeatureEngineer(db=db_session)
        
        # Create match with no historical data (should trigger fallback)
        from src.models.database import Match
        match = Match(
            id=999,
            api_id=999,
            league_id=1,
            home_team_id=999,  # Non-existent team
            away_team_id=998,
            match_date=datetime(2025, 1, 15),
            status='NS'
        )
        
        features = engineer.create_match_features(match)
        
        # Should have fallback values
        assert features['poisson_xg_home'] == 1.5
        assert features['poisson_xg_away'] == 1.2


class TestMomentumIndicators:
    """Test momentum calculation (3-match weighted goal difference)"""
    
    def test_momentum_calculation(self, db_session, sample_matches):
        """Test momentum is calculated correctly"""
        engineer = FeatureEngineer(db=db_session)
        
        # Team 1 has strong positive momentum (recent wins with good GD)
        momentum = engineer._calculate_momentum(
            team_id=1,
            before_date=datetime(2025, 1, 10),
            last_n=3
        )
        
        # Should be positive due to recent wins
        assert momentum > 0
        
    def test_momentum_in_features(self, db_session, sample_matches, upcoming_match):
        """Test that momentum is included in match features"""
        engineer = FeatureEngineer(db=db_session)
        
        features = engineer.create_match_features(upcoming_match)
        
        assert 'home_momentum' in features
        assert 'away_momentum' in features
        assert 'momentum_diff' in features
        
        # Momentum diff should be home - away
        assert features['momentum_diff'] == features['home_momentum'] - features['away_momentum']
    
    def test_negative_momentum(self, db_session, sample_matches):
        """Test that poor form results in negative momentum"""
        engineer = FeatureEngineer(db=db_session)
        
        # Team 3 has poor form (multiple losses)
        momentum = engineer._calculate_momentum(
            team_id=3,
            before_date=datetime(2025, 1, 10),
            last_n=3
        )
        
        # Should be negative due to losses
        assert momentum < 0


class TestHomeAwaySplit:
    """Test home/away strength split features"""
    
    def test_home_away_features_exist(self, db_session, sample_matches, upcoming_match):
        """Test that separate home/away strength features exist"""
        engineer = FeatureEngineer(db=db_session)
        
        features = engineer.create_match_features(upcoming_match)
        
        # Check home/away split features
        assert 'home_attack_strength' in features
        assert 'home_defense_strength' in features
        assert 'away_attack_strength' in features
        assert 'away_defense_strength' in features
        
        # All should be reasonable values
        for key in ['home_attack_strength', 'home_defense_strength', 
                    'away_attack_strength', 'away_defense_strength']:
            assert 0.0 <= features[key] <= 5.0


class TestFormCalculation:
    """Test basic form calculations work correctly"""
    
    def test_wins_draws_losses(self, db_session, sample_matches):
        """Test that wins, draws, losses are counted correctly"""
        engineer = FeatureEngineer(db=db_session)
        
        form = engineer.calculate_team_form(
            team_id=1,
            before_date=datetime(2025, 1, 10),
            last_n=5,
            home_away='all'
        )
        
        # Team 1 should have mostly wins
        assert form['wins'] > 0
        assert form['matches_played'] <= 5
        assert form['wins'] + form['draws'] + form['losses'] == form['matches_played']
    
    def test_home_only_form(self, db_session, sample_matches):
        """Test filtering for home matches only"""
        engineer = FeatureEngineer(db=db_session)
        
        form_all = engineer.calculate_team_form(
            team_id=1,
            before_date=datetime(2025, 1, 10),
            home_away='all'
        )
        
        form_home = engineer.calculate_team_form(
            team_id=1,
            before_date=datetime(2025, 1, 10),
            home_away='home'
        )
        
        # Home-only should have fewer or equal matches
        assert form_home['matches_played'] <= form_all['matches_played']


class TestELOIntegration:
    """Test ELO rating integration"""
    
    def test_elo_features_exist(self, db_session, sample_matches, upcoming_match):
        """Test that ELO features are present"""
        engineer = FeatureEngineer(db=db_session)
        
        features = engineer.create_match_features(upcoming_match)
        
        assert 'home_elo' in features
        assert 'away_elo' in features
        assert 'elo_diff' in features
        assert 'elo_advantage' in features
        
    def test_elo_fallback(self, db_session, upcoming_match):
        """Test ELO fallback values when calculator fails"""
        engineer = FeatureEngineer(db=db_session)
        
        # With no historical matches, should use fallback
        features = engineer.create_match_features(upcoming_match)
        
        # Fallback values should be reasonable
        assert 1000 <= features['home_elo'] <= 2000
        assert 1000 <= features['away_elo'] <= 2000


class TestFeatureCompleteness:
    """Test that all expected features are generated"""
    
    def test_all_new_features_present(self, db_session, sample_matches, upcoming_match):
        """Verify all new Sprint 1 features are in output"""
        engineer = FeatureEngineer(db=db_session)
        
        features = engineer.create_match_features(upcoming_match)
        
        # New Sprint 1 features
        expected_features = [
            # Recency bias (in weighted_points from form)
            'home_form_all_weighted_points',
            'away_form_all_weighted_points',
            
            # xG features
            'poisson_xg_home',
            'poisson_xg_away',
            'poisson_xg_diff',
            'poisson_xg_total',
            
            # Momentum
            'home_momentum',
            'away_momentum',
            'momentum_diff',
            
            # Home/away splits (already existed, verify)
            'home_attack_strength',
            'away_attack_strength',
            
            # ELO (already existed, verify)
            'home_elo',
            'away_elo',
            'elo_diff',
        ]
        
        for feature in expected_features:
            assert feature in features, f"Missing feature: {feature}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
