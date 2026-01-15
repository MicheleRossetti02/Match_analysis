"""
FastAPI Main Application
Football Match Prediction System - Backend API
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import settings
from src.models.database import get_db, init_db, League, Team, Match, Prediction, ModelPerformance

# Initialize FastAPI app
app = FastAPI(
    title="Football Prediction API",
    description="Machine Learning-based football match prediction system for Top 5 European leagues",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
# Parse CORS origins from comma-separated string to list
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API responses
from pydantic import BaseModel

class LeagueResponse(BaseModel):
    id: int
    api_id: int
    name: str
    country: str
    season: int
    logo: Optional[str] = None
    
    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    id: int
    api_id: int
    name: str
    code: Optional[str] = None
    country: Optional[str] = None
    logo: Optional[str] = None
    
    class Config:
        from_attributes = True


class MatchResponse(BaseModel):
    id: int
    api_id: int
    match_date: datetime
    status: str
    home_team: Optional[TeamResponse] = None
    away_team: Optional[TeamResponse] = None
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    round: Optional[str] = None
    
    class Config:
        from_attributes = True


class PredictionResponse(BaseModel):
    id: int
    match_id: int
    predicted_result: str
    confidence: float
    prob_home_win: Optional[float] = None
    prob_draw: Optional[float] = None
    prob_away_win: Optional[float] = None
    predicted_home_goals: Optional[float] = None
    predicted_away_goals: Optional[float] = None
    model_version: str
    model_type: Optional[str] = None
    key_factors: Optional[List[str]] = None
    created_at: datetime
    
    # Winner display name (team name or "Draw")
    winner_name: Optional[str] = None
    
    # BTTS (Both Teams To Score)
    btts_prediction: Optional[bool] = None
    btts_confidence: Optional[float] = None
    
    # Over/Under Goals
    over_25_prediction: Optional[bool] = None
    over_25_confidence: Optional[float] = None
    over_15_prediction: Optional[bool] = None
    over_35_prediction: Optional[bool] = None
    
    # Multi-goal range
    multi_goal_prediction: Optional[str] = None  # "0-1", "2-3", "4-5", "6+"
    multi_goal_confidence: Optional[float] = None
    
    # Exact score
    exact_score_prediction: Optional[str] = None  # e.g., "2-1"
    exact_score_confidence: Optional[float] = None
    
    # Double Chance probabilities
    prob_1x: Optional[float] = None
    prob_12: Optional[float] = None
    prob_x2: Optional[float] = None
    double_chance_probs: Optional[dict] = None  # {"1X": 0.75, "12": 0.80, "X2": 0.55}
    
    # Combo predictions (JSON)
    combo_predictions: Optional[dict] = None  # {"1_over_25": 0.45, "x_under_25": 0.32, "gg_over_25": 0.38}
    
    # Features used in prediction (JSON) - includes elo_diff, form, strength, etc.
    features: Optional[dict] = None
    
    # Betting Value Analysis (Kelly Criterion)
    kelly_percentage: Optional[float] = None  # Recommended stake % (0-25%)
    kelly_raw: Optional[float] = None  # Raw Kelly value
    value_level: Optional[str] = None  # HIGH, MEDIUM, NEUTRAL
    expected_value: Optional[float] = None  # EV = probability × odds
    edge_percentage: Optional[float] = None  # (EV - 1) × 100
    estimated_odds: Optional[dict] = None  # Bookmaker odds (estimated or actual)
    has_value_analysis: Optional[bool] = False
    is_estimated_odds: Optional[bool] = True
    
    class Config:
        from_attributes = True


class PredictionWithMatchResponse(BaseModel):
    """Prediction with full match details for display"""
    id: int
    match_id: int
    predicted_result: str
    confidence: float
    prob_home_win: Optional[float] = None
    prob_draw: Optional[float] = None
    prob_away_win: Optional[float] = None
    predicted_home_goals: Optional[float] = None
    predicted_away_goals: Optional[float] = None
    model_version: str
    model_type: Optional[str] = None
    key_factors: Optional[List[str]] = None
    created_at: datetime
    match: Optional[MatchResponse] = None
    
    # Winner display name (team name or "Draw")
    winner_name: Optional[str] = None
    
    # BTTS (Both Teams To Score)
    btts_prediction: Optional[bool] = None
    btts_confidence: Optional[float] = None
    
    # Over/Under Goals
    over_25_prediction: Optional[bool] = None
    over_25_confidence: Optional[float] = None
    over_15_prediction: Optional[bool] = None
    over_35_prediction: Optional[bool] = None
    
    # Multi-goal range
    multi_goal_prediction: Optional[str] = None
    multi_goal_confidence: Optional[float] = None
    
    # Exact score
    exact_score_prediction: Optional[str] = None
    exact_score_confidence: Optional[float] = None
    
    # Double Chance probabilities
    prob_1x: Optional[float] = None
    prob_12: Optional[float] = None
    prob_x2: Optional[float] = None
    double_chance_probs: Optional[dict] = None  # {"1X": 0.75, "12": 0.80, "X2": 0.55}
    
    # Combo predictions (JSON)
    combo_predictions: Optional[dict] = None  # {"1_over_25": 0.45, "x_under_25": 0.32, "gg_over_25": 0.38}
    
    # Features used in prediction (JSON) - includes elo_diff, form, strength, etc.
    features: Optional[dict] = None
    
    # Betting Value Analysis (Kelly Criterion)
    kelly_percentage: Optional[float] = None  # Recommended stake % (0-25%)
    kelly_raw: Optional[float] = None  # Raw Kelly value
    value_level: Optional[str] = None  # HIGH, MEDIUM, NEUTRAL
    expected_value: Optional[float] = None  # EV = probability × odds
    edge_percentage: Optional[float] = None  # (EV - 1) × 100
    estimated_odds: Optional[dict] = None  # Bookmaker odds (estimated or actual)
    has_value_analysis: Optional[bool] = False
    is_estimated_odds: Optional[bool] = True
    
    class Config:
        from_attributes = True


# Helper function to get winner name
def get_winner_name(prediction, match) -> str:
    """Convert H/A/D to team name or 'Draw'"""
    if prediction.predicted_result == 'D':
        return 'Draw'
    elif prediction.predicted_result == 'H' and match and match.home_team:
        return match.home_team.name
    elif prediction.predicted_result == 'A' and match and match.away_team:
        return match.away_team.name
    return prediction.predicted_result  # Fallback to original


class ModelPerformanceResponse(BaseModel):
    id: int
    model_version: str
    model_type: str
    accuracy: Optional[float] = None
    f1_score: Optional[float] = None
    is_active: bool
    trained_at: datetime
    
    class Config:
        from_attributes = True


# API Endpoints

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Football Prediction API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
        "supported_leagues": list(settings.LEAGUES.keys())
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.APP_ENV
    }


@app.get("/api/leagues", response_model=List[LeagueResponse])
async def get_leagues(db: Session = Depends(get_db)):
    """Get all supported leagues"""
    leagues = db.query(League).all()
    return leagues


@app.get("/api/leagues/{league_id}/teams", response_model=List[TeamResponse])
async def get_league_teams(league_id: int, db: Session = Depends(get_db)):
    """Get all teams in a specific league"""
    teams = db.query(Team).filter(Team.league_id == league_id).all()
    
    if not teams:
        raise HTTPException(status_code=404, detail="No teams found for this league")
    
    return teams


@app.get("/api/leagues/{league_id}/matches", response_model=List[MatchResponse])
async def get_league_matches(
    league_id: int,
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get matches for a specific league
    
    - **league_id**: League ID
    - **status**: Match status (NS, FT, LIVE, etc.)
    - **from_date**: Start date (YYYY-MM-DD)
    - **to_date**: End date (YYYY-MM-DD)
    - **limit**: Maximum number of matches to return
    """
    query = db.query(Match).filter(Match.league_id == league_id)
    
    if status:
        query = query.filter(Match.status == status)
    
    if from_date:
        query = query.filter(Match.match_date >= datetime.fromisoformat(from_date))
    
    if to_date:
        query = query.filter(Match.match_date <= datetime.fromisoformat(to_date))
    
    matches = query.order_by(Match.match_date.desc()).limit(limit).all()
    
    return matches


@app.get("/api/matches/upcoming", response_model=List[MatchResponse])
async def get_upcoming_matches(
    days: int = 7,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get upcoming matches (TIMED/SCHEDULED status)"""
    from sqlalchemy.orm import joinedload
    
    today = datetime.utcnow()
    future_date = today + timedelta(days=days)
    
    matches = (
        db.query(Match)
        .options(
            joinedload(Match.home_team),
            joinedload(Match.away_team)
        )
        .filter(Match.match_date >= today)
        .filter(Match.match_date <= future_date)
        .filter(Match.status.in_(['NS', 'TIMED', 'SCHEDULED']))
        .order_by(Match.match_date)
        .limit(limit)
        .all()
    )
    
    return matches


@app.get("/api/matches/{match_id}", response_model=MatchResponse)
async def get_match(match_id: int, db: Session = Depends(get_db)):
    """Get details for a specific match"""
    match = db.query(Match).filter(Match.id == match_id).first()
    
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    return match


@app.get("/api/matches/{match_id}/prediction", response_model=PredictionResponse)
async def get_match_prediction(match_id: int, db: Session = Depends(get_db)):
    """Get prediction for a specific match"""
    # Get the latest prediction for this match
    prediction = (
        db.query(Prediction)
        .filter(Prediction.match_id == match_id)
        .order_by(Prediction.created_at.desc())
        .first()
    )
    
    if not prediction:
        raise HTTPException(
            status_code=404, 
            detail="No prediction found for this match. Prediction may not be available yet."
        )
    
    return prediction


@app.get("/api/predictions", response_model=List[PredictionWithMatchResponse])
async def get_all_predictions(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all predictions with match details"""
    from sqlalchemy.orm import joinedload
    
    predictions = (
        db.query(Prediction)
        .join(Match)
        .options(
            joinedload(Prediction.match).joinedload(Match.home_team),
            joinedload(Prediction.match).joinedload(Match.away_team)
        )
        .order_by(Match.match_date.desc())
        .limit(limit)
        .all()
    )
    
    return predictions


@app.get("/api/predictions/upcoming", response_model=List[PredictionWithMatchResponse])
async def get_upcoming_predictions(
    days: int = 7,
    league_id: Optional[int] = None,
    limit: int = 20,
    sort_by_confidence: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get predictions for upcoming matches with full match details
    
    - **days**: Number of days ahead to look for matches
    - **league_id**: Filter by specific league (optional)
    - **limit**: Maximum number of predictions to return
    - **sort_by_confidence**: Sort by highest confidence first (default: True)
    """
    from sqlalchemy.orm import joinedload
    
    today = datetime.utcnow()
    future_date = today + timedelta(days=days)
    
    # Query matches that are upcoming with eager loading of match and teams
    query = (
        db.query(Prediction)
        .join(Match)
        .options(
            joinedload(Prediction.match).joinedload(Match.home_team),
            joinedload(Prediction.match).joinedload(Match.away_team)
        )
        .filter(Match.match_date >= today)
        .filter(Match.match_date <= future_date)
        .filter(Match.status.in_(['NS', 'TIMED', 'SCHEDULED']))  # Include all upcoming statuses
    )
    
    if league_id:
        query = query.filter(Match.league_id == league_id)
    
    # Sort by confidence (highest first) or by match date
    if sort_by_confidence:
        query = query.order_by(Prediction.confidence.desc())
    else:
        query = query.order_by(Match.match_date)
    
    predictions = query.limit(limit).all()
    
    return predictions


@app.get("/api/predictions/top-by-league")
async def get_top_predictions_by_league(
    limit_per_league: int = 10,
    days: int = 14,
    db: Session = Depends(get_db)
):
    """
    Get top predictions by confidence for each major league
    
    Returns predictions grouped by league, sorted by main prediction confidence.
    Excludes exact score confidence from ranking (uses 1X2 prediction confidence).
    
    - **limit_per_league**: Maximum predictions per league (default: 10)
    - **days**: Number of days ahead to look for matches (default: 14)
    """
    from sqlalchemy.orm import joinedload
    from collections import defaultdict
    
    today = datetime.utcnow()
    future_date = today + timedelta(days=days)
    
    # Get all leagues
    leagues = db.query(League).all()
    
    result = {}
    
    for league in leagues:
        # Query predictions for this league
        predictions = (
            db.query(Prediction)
            .join(Match)
            .options(
                joinedload(Prediction.match).joinedload(Match.home_team),
                joinedload(Prediction.match).joinedload(Match.away_team)
            )
            .filter(Match.league_id == league.id)
            .filter(Match.match_date >= today)
            .filter(Match.match_date <= future_date)
            .filter(Match.status == "NS")  # Not Started
            .order_by(Prediction.confidence.desc())  # Main confidence (1X2), not exact score
            .limit(limit_per_league)
            .all()
        )
        
        if predictions:
            # Format predictions for response
            formatted_predictions = []
            for pred in predictions:
                match = pred.match
                formatted_predictions.append({
                    "id": pred.id,
                    "match_id": pred.match_id,
                    "home_team": match.home_team.name if match.home_team else "TBD",
                    "away_team": match.away_team.name if match.away_team else "TBD",
                    "home_team_logo": match.home_team.logo if match.home_team else None,
                    "away_team_logo": match.away_team.logo if match.away_team else None,
                    "match_date": match.match_date.isoformat(),
                    "predicted_result": pred.predicted_result,
                    "confidence": round(pred.confidence * 100, 1),  # As percentage
                    "prob_home_win": round((pred.prob_home_win or 0) * 100, 1),
                    "prob_draw": round((pred.prob_draw or 0) * 100, 1),
                    "prob_away_win": round((pred.prob_away_win or 0) * 100, 1),
                    "winner_name": get_winner_name(pred, match),
                    # Additional predictions (not used for ranking)
                    "btts_prediction": pred.btts_prediction,
                    "over_25_prediction": pred.over_25_prediction,
                })
            
            result[league.id] = {
                "league_id": league.id,
                "league_name": league.name,
                "country": league.country,
                "predictions": formatted_predictions
            }
    
    return result


@app.get("/api/teams/{team_id}", response_model=TeamResponse)
async def get_team(team_id: int, db: Session = Depends(get_db)):
    """Get details for a specific team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return team


@app.get("/api/stats/model-performance", response_model=List[ModelPerformanceResponse])
async def get_model_performance(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get model performance metrics"""
    performance = (
        db.query(ModelPerformance)
        .order_by(ModelPerformance.trained_at.desc())
        .limit(limit)
        .all()
    )
    
    return performance


# ML Prediction Endpoints

from pydantic import BaseModel as PydanticBase

class PredictMatchRequest(PydanticBase):
    home_team_id: int
    away_team_id: int
    league_id: int
    match_date: Optional[str] = None


class PredictMatchResponse(PydanticBase):
    predicted_result: str
    probabilities: dict
    confidence: float
    model_version: str
    model_type: str
    key_factors: Optional[list] = None


@app.post("/api/predict/match", response_model=PredictMatchResponse)
async def predict_match(
    request: PredictMatchRequest,
    db: Session = Depends(get_db)
):
    """
    Predict match outcome
    
    - **home_team_id**: Home team ID
    - **away_team_id**: Away team ID  
    - **league_id**: League ID
    - **match_date**: Optional match date (defaults to now)
    """
    try:
        # Import dependencies
        from src.ml.feature_engineer import FeatureEngineer
        from src.ml.model_manager import ModelManager
        
        # Create temporary match object
        match_date = datetime.fromisoformat(request.match_date) if request.match_date else datetime.utcnow()
        
        # Create a temporary match-like object
        class TempMatch:
            def __init__(self):
                self.home_team_id = request.home_team_id
                self.away_team_id = request.away_team_id
                self.league_id = request.league_id  
                self.match_date = match_date
                self.status = 'NS'
        
        temp_match = TempMatch()
        
        # Generate features
        engineer = FeatureEngineer(db)
        features = engineer.create_match_features(temp_match)
        engineer.close()
        
        # Load model and predict
        manager = ModelManager()
        manager.load_model()
        prediction = manager.predict(features)
        
        # Get top contributing features
        key_factors = []
        if hasattr(manager.current_model, 'feature_importances_'):
            importances = manager.current_model.feature_importances_
            indices = np.argsort(importances)[::-1][:5]
            key_factors = [manager.current_config['feature_names'][i] for i in indices]
        
        return {
            **prediction,
            'key_factors': key_factors
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


@app.post("/api/predict/upcoming")
async def generate_upcoming_predictions(
    days: int = 7,
    league_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Generate predictions for all upcoming matches
    
    - **days**: Number of days ahead to predict
    - **league_id**: Optional league filter
    """
    try:
        from src.ml.feature_engineer import FeatureEngineer
        from src.ml.model_manager import ModelManager
        import numpy as np
        
        # Get upcoming matches
        today = datetime.utcnow()
        future_date = today + timedelta(days=days)
        
        query = db.query(Match).filter(
            Match.match_date >= today,
            Match.match_date <= future_date,
            Match.status == 'NS'
        )
        
        if league_id:
            query = query.filter(Match.league_id == league_id)
        
        matches = query.all()
        
        if not matches:
            return {
                "message": "No upcoming matches found",
                "predictions_generated": 0
            }
        
        # Load model
        manager = ModelManager()
        manager.load_model()
        
        # Generate features and predictions
        engineer = FeatureEngineer(db)
        predictions_created = 0
        
        for match in matches:
            # Check if prediction already exists
            existing = db.query(Prediction).filter(
                Prediction.match_id == match.id,
                Prediction.model_version == manager.current_config['version']
            ).first()
            
            if existing:
                continue
            
            try:
                # Generate features
                features = engineer.create_match_features(match)
                
                # Predict
                pred_result = manager.predict(features)
                
                # Save to database
                prediction = Prediction(
                    match_id=match.id,
                    predicted_result=pred_result['predicted_result'],
                    confidence=pred_result['confidence'],
                    prob_home_win=pred_result['probabilities'].get('H'),
                    prob_draw=pred_result['probabilities'].get('D'),
                    prob_away_win=pred_result['probabilities'].get('A'),
                    model_version=pred_result['model_version'],
                    model_type=pred_result['model_type'],
                    created_at=datetime.utcnow()
                )
                
                db.add(prediction)
                predictions_created += 1
                
            except Exception as e:
                print(f"Error predicting match {match.id}: {e}")
                continue
        
        db.commit()
        engineer.close()
        
        return {
            "message": "Predictions generated successfully",
            "matches_processed": len(matches),
            "predictions_generated": predictions_created,
            "model_version": manager.current_config['version']
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating predictions: {str(e)}"
        )


@app.get("/api/stats/accuracy")
async def get_accuracy_stats(db: Session = Depends(get_db)):
    """Get overall accuracy statistics (legacy endpoint, maintained for backward compatibility)"""
    # Get the active model
    active_model = (
        db.query(ModelPerformance)
        .filter(ModelPerformance.is_active == True)
        .first()
    )
    
    if not active_model:
        return {
            "message": "No active model found. Models need to be trained first.",
            "accuracy": None
        }
    
    # Count total predictions and correct predictions
    total_predictions = (
        db.query(Prediction)
        .filter(Prediction.actual_result.isnot(None))
        .count()
    )
    
    correct_predictions = (
        db.query(Prediction)
        .filter(Prediction.is_correct == True)
        .count()
    )
    
    accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
    
    return {
        "active_model": {
            "version": active_model.model_version,
            "type": active_model.model_type,
            "trained_at": active_model.trained_at
        },
        "total_predictions": total_predictions,
        "correct_predictions": correct_predictions,
        "accuracy_percent": round(accuracy, 2),
        "model_accuracy": active_model.accuracy
    }


@app.get("/api/stats/accuracy/overall")
async def get_accuracy_overall(db: Session = Depends(get_db)):
    """Get overall accuracy statistics across all predictions"""
    from src.services.prediction_accuracy_service import PredictionAccuracyService
    
    service = PredictionAccuracyService(db)
    stats = service.get_accuracy_stats()
    
    return {
        "status": "success",
        "data": stats
    }


@app.get("/api/stats/accuracy/by-bet-type")
async def get_accuracy_by_bet_type(db: Session = Depends(get_db)):
    """Get accuracy breakdown by each bet type"""
    from src.services.prediction_accuracy_service import PredictionAccuracyService
    
    service = PredictionAccuracyService(db)
    stats = service.get_accuracy_stats()
    
    return {
        "status": "success",
        "data": {
            "1x2": stats["accuracy_1x2"],
            "btts": stats["accuracy_btts"],
            "over_15": stats["accuracy_over_15"],
            "over_25": stats["accuracy_over_25"],
            "over_35": stats["accuracy_over_35"]
        }
    }


@app.get("/api/stats/accuracy/history")
async def get_accuracy_history(
    period: str = "week",
    limit: int = 12,
    db: Session = Depends(get_db)
):
    """
    Get accuracy trends over time
    
    - **period**: Time period grouping (week, month)
    - **limit**: Number of periods to return
    """
    from sqlalchemy import func, extract
    from collections import defaultdict
    
    # Get predictions with actual results
    predictions = (
        db.query(Prediction)
        .filter(Prediction.actual_result.isnot(None))
        .order_by(Prediction.created_at.desc())
        .all()
    )
    
    if not predictions:
        return {
            "status": "success",
            "data": []
        }
    
    # Group by period
    grouped = defaultdict(lambda: {"total": 0, "correct": 0})
    
    for pred in predictions:
        if period == "week":
            # Get year and week number
            key = pred.created_at.strftime("%Y-W%U")
            label = pred.created_at.strftime("Week of %b %d, %Y")
        else:  # month
            key = pred.created_at.strftime("%Y-%m")
            label = pred.created_at.strftime("%B %Y")
        
        grouped[key]["label"] = label
        grouped[key]["total"] += 1
        if pred.is_correct:
            grouped[key]["correct"] += 1
    
    # Calculate accuracy for each period
    history = []
    for key in sorted(grouped.keys(), reverse=True)[:limit]:
        data = grouped[key]
        accuracy = (data["correct"] / data["total"] * 100) if data["total"] > 0 else 0
        history.append({
            "period": key,
            "label": data["label"],
            "total": data["total"],
            "correct": data["correct"],
            "accuracy": round(accuracy, 2)
        })
    
    return {
        "status": "success",
        "data": list(reversed(history))  # Chronological order
    }


@app.get("/api/predictions/with-results")
async def get_predictions_with_results(
    limit: int = 50,
    offset: int = 0,
    bet_type: Optional[str] = None,
    correct_only: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get predictions with actual results for comparison
    
    - **limit**: Maximum number of predictions to return
    - **offset**: Number of predictions to skip (for pagination)
    - **bet_type**: Filter by bet type (1x2, btts, over_15, over_25, over_35)
    - **correct_only**: If true, only return correct predictions; if false, only incorrect
    """
    from sqlalchemy.orm import joinedload
    
    # Base query with eager loading
    query = (
        db.query(Prediction)
        .join(Match)
        .options(
            joinedload(Prediction.match).joinedload(Match.home_team),
            joinedload(Prediction.match).joinedload(Match.away_team),
            joinedload(Prediction.match).joinedload(Match.league)
        )
        .filter(Prediction.actual_result.isnot(None))
    )
    
    # Filter by correctness if specified
    if correct_only is not None:
        if bet_type == "btts":
            query = query.filter(Prediction.btts_correct == correct_only)
        elif bet_type == "over_15":
            query = query.filter(Prediction.over_15_correct == correct_only)
        elif bet_type == "over_25":
            query = query.filter(Prediction.over_25_correct == correct_only)
        elif bet_type == "over_35":
            query = query.filter(Prediction.over_35_correct == correct_only)
        else:  # 1x2 or default
            query = query.filter(Prediction.is_correct == correct_only)
    
    # Get total count for pagination
    total = query.count()
    
    # Get predictions with pagination
    predictions = (
        query
        .order_by(Prediction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # Format response
    results = []
    for pred in predictions:
        match = pred.match
        
        # Determine which bet type to highlight
        if bet_type == "btts":
            prediction_value = "Yes" if pred.btts_prediction else "No"
            actual_value = "Yes" if pred.btts_actual else "No"
            is_correct = pred.btts_correct
        elif bet_type == "over_15":
            prediction_value = "Over 1.5" if pred.over_15_prediction else "Under 1.5"
            actual_value = "Over 1.5" if pred.over_15_actual else "Under 1.5"
            is_correct = pred.over_15_correct
        elif bet_type == "over_25":
            prediction_value = "Over 2.5" if pred.over_25_prediction else "Under 2.5"
            actual_value = "Over 2.5" if pred.over_25_actual else "Under 2.5"
            is_correct = pred.over_25_correct
        elif bet_type == "over_35":
            prediction_value = "Over 3.5" if pred.over_35_prediction else "Under 3.5"
            actual_value = "Over 3.5" if pred.over_35_actual else "Under 3.5"
            is_correct = pred.over_35_correct
        else:  # 1x2
            prediction_value = get_winner_name(pred, match)
            actual_value = get_winner_name(type('obj', (), {'predicted_result': pred.actual_result})(), match)
            is_correct = pred.is_correct
        
        results.append({
            "id": pred.id,
            "match_id": match.id,
            "home_team": match.home_team.name if match.home_team else "Home",
            "away_team": match.away_team.name if match.away_team else "Away",
            "home_team_logo": match.home_team.logo if match.home_team else None,
            "away_team_logo": match.away_team.logo if match.away_team else None,
            "league": match.league.name if match.league else "Unknown",
            "match_date": match.match_date.isoformat(),
            "score": f"{match.home_goals}-{match.away_goals}" if match.home_goals is not None else "N/A",
            "prediction": prediction_value,
            "actual": actual_value,
            "is_correct": is_correct,
            "confidence": round(pred.confidence * 100, 1),
            "bet_type": bet_type or "1x2"
        })
    
    return {
        "status": "success",
        "data": results,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    }



# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting Football Prediction API...")
    print(f"📊 Environment: {settings.APP_ENV}")
    print(f"🏟️  Supported Leagues: {len(settings.LEAGUES)}")
    
    # Initialize database tables
    try:
        init_db()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")


# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


# ============================================================================
# BET TRACKING ENDPOINTS
# ============================================================================

from src.models.database import BetHistory
from src.services.performance_service import (
    record_bet,
    update_bet_results,
    get_performance_stats,
    get_equity_curve,
    get_bet_history
)


class BetRecordRequest(BaseModel):
    prediction_id: int
    market: str
    market_name: str
    bankroll: float = 1000.0
    kelly_percent: float
    odds: float
    ai_probability: float
    expected_value: float
    edge_percentage: float
    value_level: str
    is_estimated_odds: bool = True
    notes: Optional[str] = None


class BetHistoryResponse(BaseModel):
    id: int
    prediction_id: int
    market: str
    market_name: Optional[str]
    stake_kelly_percent: float
    stake_amount: float
    bankroll_at_bet: Optional[float]
    odds: float
    is_estimated_odds: bool
    ai_probability: Optional[float]
    expected_value: Optional[float]
    edge_percentage: Optional[float]
    value_level: Optional[str]
    status: str
    actual_result: Optional[str]
    is_winner: Optional[bool]
    pnl: float
    roi_percent: Optional[float]
    placed_at: datetime
    settled_at: Optional[datetime]
    confidence_level: Optional[str]
    
    class Config:
        from_attributes = True


@app.post("/api/bets/record")
async def create_bet_record(bet: BetRecordRequest, db: Session = Depends(get_db)):
    """
    Record a new bet with Kelly Criterion stakes
    """
    try:
        bet_record = record_bet(
            db=db,
            prediction_id=bet.prediction_id,
            market=bet.market,
            market_name=bet.market_name,
            bankroll=bet.bankroll,
            kelly_percent=bet.kelly_percent,
            odds=bet.odds,
            ai_probability=bet.ai_probability,
            expected_value=bet.expected_value,
            edge_percentage=bet.edge_percentage,
            value_level=bet.value_level,
            is_estimated_odds=bet.is_estimated_odds,
            notes=bet.notes
        )
        return {"message": "Bet recorded successfully", "bet_id": bet_record.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bets/history", response_model=List[BetHistoryResponse])
async def get_bets_history(
    value_level: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get bet history with optional filters
    """
    try:
        bets = get_bet_history(db, value_level=value_level, status=status, limit=limit)
        return bets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bets/stats")
async def get_betting_stats(db: Session = Depends(get_db)):
    """
    Get aggregate betting performance statistics
    """
    try:
        stats = get_performance_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bets/equity-curve")
async def get_betting_equity_curve(initial_bankroll: float = 1000.0, db: Session = Depends(get_db)):
    """
    Get equity curve data for chart visualization
    """
    try:
        curve = get_equity_curve(db, initial_bankroll=initial_bankroll)
        return curve
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/bets/update-results")
async def update_betting_results(db: Session = Depends(get_db)):
    """
    Worker endpoint to update bet results for finished matches
    """
    try:
        result = update_bet_results(db)
        return {
            "message": "Bet results updated",
            "updated": result['updated'],
            "won": result['won'],
            "lost": result['lost']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
