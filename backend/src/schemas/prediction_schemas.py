"""
Pydantic schemas for prediction requests and responses
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class PredictionRequest(BaseModel):
    """Request schema for generating a prediction"""
    match_id: int = Field(..., gt=0, description="Match ID to predict")
    
    class Config:
        schema_extra = {
            "example": {
                "match_id": 12345
            }
        }


class PredictionResponse(BaseModel):
    """Complete prediction response with all betting markets"""
    
    # Match info
    match_id: int = Field(..., description="Match ID")
    model_version: str = Field(..., description="Model version used")
    created_at: datetime = Field(..., description="Prediction timestamp")
    
    # 1X2 Prediction
    predicted_result: str = Field(..., regex='^[HAD]$', description="Predicted result: H/A/D")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    prob_home_win: float = Field(..., ge=0.0, le=1.0, description="Home win probability")
    prob_draw: float = Field(..., ge=0.0, le=1.0, description="Draw probability")
    prob_away_win: float = Field(..., ge=0.0, le=1.0, description="Away win probability")
    
    # BTTS (Both Teams To Score)
    btts_prediction: bool = Field(..., description="BTTS prediction: Yes/No")
    btts_confidence: float = Field(..., ge=0.0, le=1.0, description="BTTS confidence")
    
    # Over/Under
    over_15_prediction: bool = Field(..., description="Over 1.5 goals")
    over_25_prediction: bool = Field(..., description="Over 2.5 goals")
    over_25_confidence: float = Field(..., ge=0.0, le=1.0, description="Over 2.5 confidence")
    over_35_prediction: bool = Field(..., description="Over 3.5 goals")
    
    # Double Chance
    prob_1x: Optional[float] = Field(None, ge=0.0, le=1.0, description="Home or Draw probability")
    prob_12: Optional[float] = Field(None, ge=0.0, le=1.0, description="Home or Away probability")
    prob_x2: Optional[float] = Field(None, ge=0.0, le=1.0, description="Draw or Away probability")
    dc_prediction: Optional[str] = Field(None, regex='^(1X|12|X2)$', description="Best DC option")
    dc_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="DC confidence")
    
    # Combo Bets
    combo_1_over_25: Optional[float] = Field(None, ge=0.0, le=1.0, description="Home Win AND Over 2.5")
    combo_2_over_25: Optional[float] = Field(None, ge=0.0, le=1.0, description="Away Win AND Over 2.5")
    combo_x_under_25: Optional[float] = Field(None, ge=0.0, le=1.0, description="Draw AND Under 2.5")
    combo_1_btts: Optional[float] = Field(None, ge=0.0, le=1.0, description="Home Win AND BTTS")
    combo_2_btts: Optional[float] = Field(None, ge=0.0, le=1.0, description="Away Win AND BTTS")
    combo_x_btts: Optional[float] = Field(None, ge=0.0, le=1.0, description="Draw AND BTTS")
    best_combo_prediction: Optional[str] = Field(None, description="Best combo option")
    best_combo_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Best combo confidence")
    
    # Exact score and multi-goal
    exact_score_prediction: Optional[str] = Field(None, description="Predicted exact score")
    exact_score_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Exact score confidence")
    multi_goal_prediction: Optional[str] = Field(None, description="Multi-goal range")
    multi_goal_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Multi-goal confidence")
    
    @validator('prob_draw')
    def probabilities_sum_to_one(cls, v, values):
        """Validate that 1X2 probabilities sum to ~1.0"""
        if 'prob_home_win' in values and 'prob_away_win' in values:
            total = values['prob_home_win'] + v + values.get('prob_away_win', 0)
            if not (0.98 <= total <= 1.02):  # Allow small floating point tolerance
                raise ValueError(f'1X2 probabilities sum to {total:.3f}, should be ~1.0')
        return v
    
    @validator('dc_confidence')
    def dc_is_max_of_components(cls, v, values):
        """DC confidence should be the max of its component probabilities"""
        if v is not None and all(k in values for k in ['prob_1x', 'prob_12', 'prob_x2']):
            if values['prob_1x'] is not None and values['prob_12'] is not None and values['prob_x2'] is not None:
                max_prob = max(values['prob_1x'], values['prob_12'], values['prob_x2'])
                if abs(v - max_prob) > 0.01:
                    raise ValueError(f'DC confidence {v} should be max of DC probabilities {max_prob}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "match_id": 12345,
                "model_version": "extended_xgboost_v2.1",
                "created_at": "2025-01-14T12:00:00Z",
                "predicted_result": "H",
                "confidence": 0.65,
                "prob_home_win": 0.65,
                "prob_draw": 0.25,
                "prob_away_win": 0.10,
                "btts_prediction": True,
                "btts_confidence": 0.58,
                "over_15_prediction": True,
                "over_25_prediction": True,
                "over_25_confidence": 0.62,
                "over_35_prediction": False,
                "prob_1x": 0.90,
                "prob_12": 0.75,
                "prob_x2": 0.35,
                "dc_prediction": "1X",
                "dc_confidence": 0.90,
                "combo_1_over_25": 0.42,
                "combo_2_over_25": 0.06,
                "combo_x_under_25": 0.18,
                "combo_1_btts": 0.38,
                "combo_2_btts": 0.06,
                "combo_x_btts": 0.12,
                "best_combo_prediction": "1_over_25",
                "best_combo_confidence": 0.42,
                "exact_score_prediction": "2-1",
                "exact_score_confidence": 0.08,
                "multi_goal_prediction": "2-3",
                "multi_goal_confidence": 0.35
            }
        }


class PredictionListResponse(BaseModel):
    """Response for multiple predictions"""
    predictions: list[PredictionResponse]
    count: int = Field(..., description="Number of predictions")
    
    @validator('count')
    def count_matches_length(cls, v, values):
        """Count should match number of predictions"""
        if 'predictions' in values and len(values['predictions']) != v:
            raise ValueError(f'Count {v} does not match predictions length {len(values["predictions"])}')
        return v


__all__ = [
    'PredictionRequest',
    'PredictionResponse',
    'PredictionListResponse'
]
