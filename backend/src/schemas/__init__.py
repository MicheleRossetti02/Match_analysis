"""
Package initialization for schemas
"""
from .api_sports_schemas import (
    TeamSchema,
    LeagueSchema,
    MatchSchema,
    MatchStatisticsSchema
)
from .prediction_schemas import (
    PredictionRequest,
    PredictionResponse,
    PredictionListResponse
)

__all__ = [
    # API-Sports schemas
    'TeamSchema',
    'LeagueSchema',
    'MatchSchema',
    'MatchStatisticsSchema',
    # Prediction schemas
    'PredictionRequest',
    'PredictionResponse',
    'PredictionListResponse'
]
