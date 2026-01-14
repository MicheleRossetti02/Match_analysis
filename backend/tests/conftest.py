"""
Pytest configuration and shared fixtures for testing
"""
import sys
import os
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.models.database import Base, Match, Team, League


@pytest.fixture(scope='function')
def db_session():
    """
    Create an in-memory SQLite database for testing
    Yields a session that rolls back after each test
    """
    # In-memory SQLite database
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.rollback()
    session.close()


@pytest.fixture
def sample_league(db_session):
    """Create a sample league for testing"""
    league = League(
        id=1,
        api_id=39,  # Premier League
        name="Premier League",
        country="England",
        season=2025
    )
    db_session.add(league)
    db_session.commit()
    return league


@pytest.fixture
def sample_teams(db_session, sample_league):
    """Create sample teams for testing"""
    teams = [
        Team(id=1, api_id=33, name="Manchester United", league_id=sample_league.id),
        Team(id=2, api_id=34, name="Liverpool", league_id=sample_league.id),
        Team(id=3, api_id=35, name="Arsenal", league_id=sample_league.id),
        Team(id=4, api_id=36, name="Chelsea", league_id=sample_league.id),
    ]
    
    for team in teams:
        db_session.add(team)
    
    db_session.commit()
    return teams


@pytest.fixture
def sample_matches(db_session, sample_teams, sample_league):
    """
    Create sample finished matches with realistic data
    Creates a sequence of matches to test form, streaks, etc.
    """
    base_date = datetime(2025, 1, 1)
    matches = []
    
    # Team 1 (Man United) - Strong recent form
    match_data = [
        # (home_id, away_id, home_goals, away_goals, days_ago)
        (1, 2, 2, 1, 20),  # Won
        (3, 1, 0, 3, 17),  # Won away
        (1, 4, 2, 0, 14),  # Won
        (2, 1, 1, 1, 10),  # Draw
        (1, 3, 3, 1, 7),   # Won - strong momentum
        
        # Team 2 (Liverpool) - Mixed form
        (2, 3, 2, 2, 18),  # Draw
        (4, 2, 1, 2, 15),  # Won
        (2, 1, 1, 2, 10),  # Won
        (2, 4, 0, 1, 6),   # Loss
        
        # Team 3 (Arsenal) - Poor form
        (3, 4, 0, 2, 16),  # Loss
        (1, 3, 3, 0, 17),  # Loss
        (3, 2, 2, 2, 18),  # Draw
        (3, 1, 1, 3, 7),   # Loss
    ]
    
    for home_id, away_id, hg, ag, days_ago in match_data:
        match = Match(
            api_id=len(matches) + 1000,
            league_id=sample_league.id,
            home_team_id=home_id,
            away_team_id=away_id,
            match_date=base_date - timedelta(days=days_ago),
            status='FT',
            home_goals=hg,
            away_goals=ag,
            round="Regular Season"
        )
        db_session.add(match)
        matches.append(match)
    
    db_session.commit()
    return matches


@pytest.fixture
def upcoming_match(db_session, sample_teams, sample_league):
    """Create an upcoming match for prediction testing"""
    match = Match(
        api_id=9999,
        league_id=sample_league.id,
        home_team_id=1,  # Man United
        away_team_id=2,  # Liverpool
        match_date=datetime(2025, 1, 15),
        status='NS',  # Not started
        home_goals=None,
        away_goals=None,
        round="Regular Season"
    )
    db_session.add(match)
    db_session.commit()
    return match
