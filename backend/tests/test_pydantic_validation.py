"""
Unit tests for Pydantic API-Sports schemas
Tests data validation and error handling
"""
import sys
import os
import pytest
from pydantic import ValidationError
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.schemas.api_sports_schemas import (
    TeamSchema,
    LeagueSchema,
    MatchSchema,
    MatchStatisticsSchema
)


class TestTeamSchema:
    """Test team data validation"""
    
    def test_valid_team(self):
        """Valid team data should pass"""
        data = {
            "id": 33,
            "name": "Manchester United",
            "code": "MUN",
            "country": "England",
            "logo": "https://example.com/logo.png"
        }
        team = TeamSchema(**data)
        assert team.id == 33
        assert team.name == "Manchester United"
    
    def test_empty_name_fails(self):
        """Empty team name should fail"""
        data = {"id": 1, "name": "   "}
        
        with pytest.raises(ValidationError) as exc_info:
            TeamSchema(**data)
        assert "Team name cannot be empty" in str(exc_info.value)
    
    def test_negative_id_fails(self):
        """Negative ID should fail"""
        data = {"id": -1, "name": "Test Team"}
        
        with pytest.raises(ValidationError):
            TeamSchema(**data)
    
    def test_name_whitespace_stripped(self):
        """Whitespace should be stripped from name"""
        data = {"id": 1, "name": "  Chelsea  "}
        team = TeamSchema(**data)
        assert team.name == "Chelsea"


class TestLeagueSchema:
    """Test league data validation"""
    
    def test_valid_league(self):
        """Valid league data should pass"""
        data = {
            "id": 39,
            "name": "Premier League",
            "country": "England",
            "season": 2025
        }
        league = LeagueSchema(**data)
        assert league.id == 39
        assert league.season == 2025
    
    def test_future_season_fails(self):
        """Season too far in future should fail"""
        data = {
            "id": 1,
            "name": "Test League",
            "country": "Test",
            "season": 2035  # Too far
        }
        
        with pytest.raises(ValidationError) as exc_info:
            LeagueSchema(**data)
        assert "too far in the future" in str(exc_info.value)
    
    def test_old_season_fails(self):
        """Season before 2015 should fail"""
        data = {
            "id": 1,
            "name": "Test League",
            "country": "Test",
            "season": 2010
        }
        
        with pytest.raises(ValidationError):
            LeagueSchema(**data)


class TestMatchSchema:
    """Test match data validation"""
    
    def test_valid_upcoming_match(self):
        """Valid not-started match should pass"""
        data = {
            "id": 12345,
            "league_id": 39,
            "season": 2025,
            "home_team_id": 33,
            "away_team_id": 34,
            "match_date": datetime.now() + timedelta(days=7),
            "status": "NS",
            "round": "Round 22"
        }
        match = MatchSchema(**data)
        assert match.fixture_id == 12345
        assert match.status == "NS"
        assert match.home_goals is None
    
    def test_valid_finished_match(self):
        """Valid finished match with goals should pass"""
        data = {
            "id": 12346,
            "league_id": 39,
            "season": 2025,
            "home_team_id": 33,
            "away_team_id": 34,
            "match_date": datetime.now() - timedelta(days=1),
            "status": "FT",
            "round": "Round 21",
            "home_goals": 2,
            "away_goals": 1
        }
        match = MatchSchema(**data)
        assert match.home_goals == 2
        assert match.away_goals == 1
    
    def test_same_teams_fails(self):
        """Home and away teams being the same should fail"""
        data = {
            "id": 1,
            "league_id": 1,
            "season": 2025,
            "home_team_id": 33,
            "away_team_id": 33,  # Same as home
            "match_date": datetime.now(),
            "status": "NS"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MatchSchema(**data)
        assert "cannot be the same" in str(exc_info.value)
    
    def test_not_started_with_goals_fails(self):
        """NS match with goals should fail"""
        data = {
            "id": 1,
            "league_id": 1,
            "season": 2025,
            "home_team_id": 1,
            "away_team_id": 2,
            "match_date": datetime.now(),
            "status": "NS",
            "home_goals": 2,  # Should not have goals
            "away_goals": 1
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MatchSchema(**data)
        assert "should not have goals" in str(exc_info.value)
    
    def test_old_match_fails(self):
        """Match older than 5 years should fail"""
        data = {
            "id": 1,
            "league_id": 1,
            "season": 2015,
            "home_team_id": 1,
            "away_team_id": 2,
            "match_date": datetime(2015, 1, 1),
            "status": "FT"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MatchSchema(**data)
        assert "older than 5 years" in str(exc_info.value)
    
    def test_excessive_goals_fails(self):
        """More than 50 goals should fail"""
        data = {
            "id": 1,
            "league_id": 1,
            "season": 2025,
            "home_team_id": 1,
            "away_team_id": 2,
            "match_date": datetime.now(),
            "status": "FT",
            "home_goals": 51,  # Excessive
            "away_goals": 1
        }
        
        with pytest.raises(ValidationError):
            MatchSchema(**data)


class TestMatchStatisticsSchema:
    """Test match statistics validation"""
    
    def test_valid_statistics(self):
        """Valid statistics should pass"""
        data = {
            "match_id": 1,
            "home_possession": 60.0,
            "away_possession": 40.0,
            "home_shots_total": 15,
            "home_shots_on_target": 5,
            "away_shots_total": 10,
            "away_shots_on_target": 3
        }
        stats = MatchStatisticsSchema(**data)
        assert stats.home_possession == 60.0
    
    def test_possession_sum_validation(self):
        """Possession should sum to ~100%"""
        data = {
            "match_id": 1,
            "home_possession": 80.0,
            "away_possession": 30.0  # Total = 110%
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MatchStatisticsSchema(**data)
        assert "should be ~100%" in str(exc_info.value)
    
    def test_shots_on_target_exceeds_total_fails(self):
        """Shots on target > total shots should fail"""
        data = {
            "match_id": 1,
            "home_shots_total": 10,
            "home_shots_on_target": 15  # More than total
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MatchStatisticsSchema(**data)
        assert "cannot exceed total shots" in str(exc_info.value)
    
    def test_cards_exceed_limit_fails(self):
        """More than 11 cards per team should fail"""
        data = {
            "match_id": 1,
            "home_yellow_cards": 12  # Max 11 players
        }
        
        with pytest.raises(ValidationError):
            MatchStatisticsSchema(**data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
