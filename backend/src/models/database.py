"""
Database models and setup using SQLAlchemy
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import settings

# Database setup
engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models

class League(Base):
    """Football League/Competition"""
    __tablename__ = "leagues"
    
    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    logo = Column(String)
    season = Column(Integer, nullable=False)
    
    # Relationships
    teams = relationship("Team", back_populates="league")
    matches = relationship("Match", back_populates="league")


class Team(Base):
    """Football Team"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    code = Column(String)  # Short code (e.g., MCI, LIV)
    country = Column(String)
    logo = Column(String)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    
    # Relationships
    league = relationship("League", back_populates="teams")
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")


class Match(Base):
    """Football Match/Fixture"""
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True, nullable=False, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    season = Column(Integer, nullable=False)
    
    # Match Details
    match_date = Column(DateTime, nullable=False, index=True)
    round = Column(String)
    status = Column(String, nullable=False)  # NS, LIVE, FT, PST, etc.
    
    # Teams
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    
    # Results
    home_goals = Column(Integer)
    away_goals = Column(Integer)
    home_goals_halftime = Column(Integer)
    away_goals_halftime = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    league = relationship("League", back_populates="matches")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    statistics = relationship("MatchStatistics", back_populates="match", uselist=False)
    predictions = relationship("Prediction", back_populates="match")


class MatchStatistics(Base):
    """Detailed match statistics"""
    __tablename__ = "match_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), unique=True)
    
    # Home Team Stats
    home_possession = Column(Float)
    home_shots_total = Column(Integer)
    home_shots_on_target = Column(Integer)
    home_corners = Column(Integer)
    home_fouls = Column(Integer)
    home_yellow_cards = Column(Integer)
    home_red_cards = Column(Integer)
    home_offsides = Column(Integer)
    home_passes_total = Column(Integer)
    home_passes_accurate = Column(Integer)
    
    # Away Team Stats
    away_possession = Column(Float)
    away_shots_total = Column(Integer)
    away_shots_on_target = Column(Integer)
    away_corners = Column(Integer)
    away_fouls = Column(Integer)
    away_yellow_cards = Column(Integer)
    away_red_cards = Column(Integer)
    away_offsides = Column(Integer)
    away_passes_total = Column(Integer)
    away_passes_accurate = Column(Integer)
    
    # Relationship
    match = relationship("Match", back_populates="statistics")


class Prediction(Base):
    """ML Model Predictions"""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    
    # Prediction Details (1X2)
    predicted_result = Column(String, nullable=False)  # H, D, A
    confidence = Column(Float, nullable=False)
    
    # Probabilities
    prob_home_win = Column(Float)
    prob_draw = Column(Float)
    prob_away_win = Column(Float)
    
    # Score Prediction
    predicted_home_goals = Column(Float)
    predicted_away_goals = Column(Float)
    
    # BTTS (Both Teams To Score)
    btts_prediction = Column(Boolean)  # True = Yes, False = No
    btts_confidence = Column(Float)
    
    # Over/Under Goals
    over_15_prediction = Column(Boolean)  # Over 1.5 goals
    over_25_prediction = Column(Boolean)  # Over 2.5 goals
    over_25_confidence = Column(Float)
    over_35_prediction = Column(Boolean)  # Over 3.5 goals
    
    # Multi-goal range
    multi_goal_prediction = Column(String)  # "0-1", "2-3", "4-5", "6+"
    multi_goal_confidence = Column(Float)
    
    # Exact score
    exact_score_prediction = Column(String)  # e.g., "2-1"
    exact_score_confidence = Column(Float)
    
    # Model Info
    model_version = Column(String, nullable=False)
    model_type = Column(String)  # random_forest, xgboost, neural_network
    
    # Features used (stored as JSON)
    features = Column(JSON)
    key_factors = Column(JSON)  # List of key factors influencing prediction
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Actual result (filled after match)
    actual_result = Column(String)
    is_correct = Column(Boolean)
    
    # Bet-specific accuracy tracking
    # BTTS (Both Teams To Score)
    btts_actual = Column(Boolean)  # Actual BTTS outcome
    btts_correct = Column(Boolean)  # Whether BTTS prediction was correct
    
    # Over/Under 1.5 Goals
    over_15_actual = Column(Boolean)  # Actual Over 1.5 outcome
    over_15_correct = Column(Boolean)  # Whether Over 1.5 prediction was correct
    
    # Over/Under 2.5 Goals
    over_25_actual = Column(Boolean)  # Actual Over 2.5 outcome
    over_25_correct = Column(Boolean)  # Whether Over 2.5 prediction was correct
    
    # Over/Under 3.5 Goals
    over_35_actual = Column(Boolean)  # Actual Over 3.5 outcome
    over_35_correct = Column(Boolean)  # Whether Over 3.5 prediction was correct
    
    # Relationship
    match = relationship("Match", back_populates="predictions")



class ModelPerformance(Base):
    """Track ML model performance over time"""
    __tablename__ = "model_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String, nullable=False, index=True)
    model_type = Column(String, nullable=False)
    
    # Metrics
    accuracy = Column(Float)
    precision_home = Column(Float)
    precision_draw = Column(Float)
    precision_away = Column(Float)
    recall_home = Column(Float)
    recall_draw = Column(Float)
    recall_away = Column(Float)
    f1_score = Column(Float)
    
    # League-specific accuracy
    league_accuracy = Column(JSON)  # {"premier_league": 0.58, ...}
    
    # Training info
    training_samples = Column(Integer)
    validation_samples = Column(Integer)
    
    # Feature importance
    feature_importance = Column(JSON)
    
    # Metadata
    trained_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=False)


# Database initialization
def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    # Create tables when run directly
    init_db()
