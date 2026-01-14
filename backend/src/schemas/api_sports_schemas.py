"""
Pydantic schemas for API-Sports data validation
Ensures data quality before entering the database
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class TeamSchema(BaseModel):
    """Validate team data from API-Sports"""
    id: int = Field(..., gt=0, description="Team API ID")
    name: str = Field(..., min_length=1, max_length=100, description="Team name")
    code: Optional[str] = Field(None, max_length=10, description="Team code (e.g., MCI, LIV)")
    country: Optional[str] = Field(None, description="Country")
    logo: Optional[str] = Field(None, description="Logo URL")
    
    @validator('name')
    def name_not_empty(cls, v):
        """Ensure team name is not empty after stripping"""
        if not v.strip():
            raise ValueError('Team name cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "id": 33,
                "name": "Manchester United",
                "code": "MUN",
                "country": "England",
                "logo": "https://media.api-sports.io/football/teams/33.png"
            }
        }


class LeagueSchema(BaseModel):
    """Validate league data from API-Sports"""
    id: int = Field(..., gt=0, description="League API ID")
    name: str = Field(..., min_length=1, max_length=100, description="League name")
    country: str = Field(..., min_length=1, description="Country")
    season: int = Field(..., ge=2015, le=2030, description="Season year")
    logo: Optional[str] = Field(None, description="League logo URL")
    
    @validator('season')
    def season_valid_range(cls, v):
        """Ensure season is within reasonable range"""
        current_year = datetime.now().year
        if v > current_year + 1:
            raise ValueError(f'Season {v} is too far in the future')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "id": 39,
                "name": "Premier League",
                "country": "England",
                "season": 2025,
                "logo": "https://media.api-sports.io/football/leagues/39.png"
            }
        }


class MatchSchema(BaseModel):
    """Validate match/fixture data from API-Sports"""
    fixture_id: int = Field(..., alias='id', gt=0, description="Match API ID")
    league_id: int = Field(..., gt=0, description="League ID")
    season: int = Field(..., ge=2015, le=2030, description="Season")
    home_team_id: int = Field(..., gt=0, description="Home team ID")
    away_team_id: int = Field(..., gt=0, description="Away team ID")
    match_date: datetime = Field(..., description="Match datetime")
    status: str = Field(
        ..., 
        regex='^(NS|LIVE|FT|PST|CANC|ABD|AWD|WO|1H|HT|2H|ET|BT|P|SUSP|INT|AET|PEN)$',
        description="Match status code"
    )
    round: Optional[str] = Field(None, description="Round/matchday")
    home_goals: Optional[int] = Field(None, ge=0, le=50, description="Home team goals")
    away_goals: Optional[int] = Field(None, ge=0, le=50, description="Away team goals")
    home_goals_halftime: Optional[int] = Field(None, ge=0, le=25, description="HT home goals")
    away_goals_halftime: Optional[int] = Field(None, ge=0, le=25, description="HT away goals")
    
    @validator('match_date')
    def date_not_too_old(cls, v):
        """Reject matches older than 5 years"""
        cutoff_date = datetime.now().replace(year=datetime.now().year - 5)
        if v < cutoff_date:
            raise ValueError(f'Match date {v} is older than 5 years')
        return v
    
    @validator('away_team_id')
    def teams_different(cls, v, values):
        """Ensure home and away teams are different"""
        if 'home_team_id' in values and v == values['home_team_id']:
            raise ValueError('Home and away teams cannot be the same')
        return v
    
    @validator('away_goals')
    def goals_valid_for_status(cls, v, values):
        """Goals should only exist for finished/live matches"""
        if 'status' in values and values['status'] == 'NS':
            if v is not None or values.get('home_goals') is not None:
                raise ValueError('Not started matches should not have goals')
        return v
    
    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "id": 12345,
                "league_id": 39,
                "season": 2025,
                "home_team_id": 33,
                "away_team_id": 34,
                "match_date": "2025-01-20T15:00:00Z",
                "status": "NS",
                "round": "Regular Season - 22",
                "home_goals": None,
                "away_goals": None
            }
        }


class MatchStatisticsSchema(BaseModel):
    """Validate match statistics from API-Sports"""
    match_id: int = Field(..., gt=0)
    
    # Home team stats
    home_possession: Optional[float] = Field(None, ge=0.0, le=100.0)
    home_shots_total: Optional[int] = Field(None, ge=0, le=100)
    home_shots_on_target: Optional[int] = Field(None, ge=0, le=100)
    home_corners: Optional[int] = Field(None, ge=0, le=50)
    home_fouls: Optional[int] = Field(None, ge=0, le=50)
    home_yellow_cards: Optional[int] = Field(None, ge=0, le=11)
    home_red_cards: Optional[int] = Field(None, ge=0, le=11)
    
    # Away team stats
    away_possession: Optional[float] = Field(None, ge=0.0, le=100.0)
    away_shots_total: Optional[int] = Field(None, ge=0, le=100)
    away_shots_on_target: Optional[int] = Field(None, ge=0, le=100)
    away_corners: Optional[int] = Field(None, ge=0, le=50)
    away_fouls: Optional[int] = Field(None, ge=0, le=50)
    away_yellow_cards: Optional[int] = Field(None, ge=0, le=11)
    away_red_cards: Optional[int] = Field(None, ge=0, le=11)
    
    @validator('away_possession')
    def possession_sum_100(cls, v, values):
        """Home and away possession should sum to ~100%"""
        if v is not None and 'home_possession' in values and values['home_possession'] is not None:
            total = v + values['home_possession']
            if not (95.0 <= total <= 105.0):  # Allow 5% tolerance
                raise ValueError(f'Total possession {total}% should be ~100%')
        return v
    
    @validator('home_shots_on_target')
    def shots_on_target_valid(cls, v, values):
        """Shots on target <= total shots"""
        if v is not None and 'home_shots_total' in values and values['home_shots_total'] is not None:
            if v > values['home_shots_total']:
                raise ValueError('Shots on target cannot exceed total shots')
        return v


# Export all schemas
__all__ = [
    'TeamSchema',
    'LeagueSchema', 
    'MatchSchema',
    'MatchStatisticsSchema'
]
