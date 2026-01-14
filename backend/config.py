"""
Configuration settings for the Football Prediction Backend
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/football_predictions"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API Keys
    API_FOOTBALL_KEY: str = ""
    API_FOOTBALL_HOST: str = "api-football-v1.p.rapidapi.com"
    API_FOOTBALL_BASE_URL: str = "https://api-football-v1.p.rapidapi.com/v3"
    
    # Application
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-in-production"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000"
    
    # ML Settings
    MODEL_VERSION: str = "1.0.0"
    MIN_CONFIDENCE_THRESHOLD: float = 0.5
    RETRAIN_SCHEDULE_DAYS: int = 14
    
    # Paths
    MODELS_DIR: str = "models"
    DATA_DIR: str = "data"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Supported Leagues (football-data.org codes)
    LEAGUES: dict = {
        "premier_league": {"id": "PL", "name": "Premier League", "country": "England"},
        "serie_a": {"id": "SA", "name": "Serie A", "country": "Italy"},
        "la_liga": {"id": "PD", "name": "La Liga", "country": "Spain"},
        "bundesliga": {"id": "BL1", "name": "Bundesliga", "country": "Germany"},
        "ligue_1": {"id": "FL1", "name": "Ligue 1", "country": "France"}
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = 'ignore'  # Ignore extra environment variables


# Global settings instance
settings = Settings()
