"""
Elo Rating Calculator for Football Teams
Calculates and tracks team Elo ratings over time for improved predictions.

Elo rating formula:
- New_Rating = Old_Rating + K * (Actual - Expected)
- Expected = 1 / (1 + 10^((Opponent_Rating - Team_Rating) / 400))
"""
import sys
import os
from datetime import datetime
from typing import Dict, Tuple, Optional
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.database import SessionLocal, Match, Team


class EloCalculator:
    """Calculate and track Elo ratings for football teams"""
    
    # Default parameters
    INITIAL_ELO = 1500
    K_FACTOR = 32  # How much ratings change per match
    HOME_ADVANTAGE = 100  # Elo points bonus for home team
    
    def __init__(self, k_factor: int = 32, home_advantage: int = 100):
        """
        Initialize Elo calculator
        
        Args:
            k_factor: How much ratings change per match (default 32)
            home_advantage: Elo bonus for home team (default 100)
        """
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.ratings: Dict[int, float] = {}  # team_id -> elo rating
        self.rating_history: Dict[int, list] = {}  # team_id -> [(date, elo), ...]
        
    def get_rating(self, team_id: int) -> float:
        """Get current Elo rating for a team"""
        return self.ratings.get(team_id, self.INITIAL_ELO)
    
    def get_expected_score(self, home_elo: float, away_elo: float) -> Tuple[float, float]:
        """
        Calculate expected score (probability) for each team
        
        Args:
            home_elo: Home team's Elo rating
            away_elo: Away team's Elo rating
            
        Returns:
            Tuple of (home_expected, away_expected) probabilities
        """
        # Add home advantage
        adjusted_home_elo = home_elo + self.home_advantage
        
        # Standard Elo formula
        home_expected = 1 / (1 + 10 ** ((away_elo - adjusted_home_elo) / 400))
        away_expected = 1 - home_expected
        
        return home_expected, away_expected
    
    def get_actual_score(self, home_goals: int, away_goals: int) -> Tuple[float, float]:
        """
        Convert match result to actual score for Elo calculation
        
        Args:
            home_goals: Goals scored by home team
            away_goals: Goals scored by away team
            
        Returns:
            Tuple of (home_actual, away_actual) where:
            - Win = 1.0
            - Draw = 0.5
            - Loss = 0.0
        """
        if home_goals > away_goals:
            return 1.0, 0.0  # Home win
        elif home_goals < away_goals:
            return 0.0, 1.0  # Away win
        else:
            return 0.5, 0.5  # Draw
    
    def update_ratings(self, home_team_id: int, away_team_id: int, 
                       home_goals: int, away_goals: int, match_date: datetime) -> Tuple[float, float]:
        """
        Update Elo ratings based on match result
        
        Args:
            home_team_id: ID of home team
            away_team_id: ID of away team
            home_goals: Home team goals
            away_goals: Away team goals
            match_date: When the match was played
            
        Returns:
            Tuple of (new_home_elo, new_away_elo)
        """
        # Get current ratings
        home_elo = self.get_rating(home_team_id)
        away_elo = self.get_rating(away_team_id)
        
        # Calculate expected scores
        home_expected, away_expected = self.get_expected_score(home_elo, away_elo)
        
        # Get actual scores
        home_actual, away_actual = self.get_actual_score(home_goals, away_goals)
        
        # Calculate new ratings
        new_home_elo = home_elo + self.k_factor * (home_actual - home_expected)
        new_away_elo = away_elo + self.k_factor * (away_actual - away_expected)
        
        # Update stored ratings
        self.ratings[home_team_id] = new_home_elo
        self.ratings[away_team_id] = new_away_elo
        
        # Store history
        if home_team_id not in self.rating_history:
            self.rating_history[home_team_id] = []
        if away_team_id not in self.rating_history:
            self.rating_history[away_team_id] = []
            
        self.rating_history[home_team_id].append((match_date, new_home_elo))
        self.rating_history[away_team_id].append((match_date, new_away_elo))
        
        return new_home_elo, new_away_elo
    
    def calculate_all_ratings(self, db=None) -> Dict[int, float]:
        """
        Calculate Elo ratings for all teams from historical matches
        
        Args:
            db: Database session (optional, will create if not provided)
            
        Returns:
            Dict of team_id -> current Elo rating
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            # Get all finished matches in chronological order
            matches = db.query(Match).filter(
                Match.status == 'FT',
                Match.home_goals.isnot(None),
                Match.away_goals.isnot(None)
            ).order_by(Match.match_date).all()
            
            print(f"📊 Calculating Elo ratings from {len(matches)} matches...")
            
            # Reset ratings
            self.ratings = {}
            self.rating_history = {}
            
            # Process each match
            for match in matches:
                self.update_ratings(
                    match.home_team_id,
                    match.away_team_id,
                    match.home_goals,
                    match.away_goals,
                    match.match_date
                )
            
            print(f"✅ Calculated ratings for {len(self.ratings)} teams")
            
            return self.ratings
            
        finally:
            if should_close:
                db.close()
    
    def get_rating_at_date(self, team_id: int, target_date: datetime) -> float:
        """
        Get team's Elo rating at a specific date
        
        Args:
            team_id: Team ID
            target_date: Date to get rating for
            
        Returns:
            Elo rating at that date
        """
        if team_id not in self.rating_history:
            return self.INITIAL_ELO
        
        history = self.rating_history[team_id]
        
        # Find the most recent rating before target_date
        rating = self.INITIAL_ELO
        for date, elo in history:
            if date < target_date:
                rating = elo
            else:
                break
        
        return rating
    
    def get_top_teams(self, n: int = 20) -> list:
        """Get top N teams by Elo rating"""
        sorted_teams = sorted(
            self.ratings.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_teams[:n]
    
    def predict_match(self, home_team_id: int, away_team_id: int) -> Dict:
        """
        Predict match outcome based on Elo ratings
        
        Returns:
            Dict with predictions
        """
        home_elo = self.get_rating(home_team_id)
        away_elo = self.get_rating(away_team_id)
        
        home_expected, away_expected = self.get_expected_score(home_elo, away_elo)
        
        # Calculate draw probability (simplified)
        # Higher when teams are close in rating
        elo_diff = abs(home_elo - away_elo)
        draw_prob = max(0.15, 0.35 - elo_diff / 1000)
        
        # Adjust win probabilities
        total = home_expected + away_expected
        home_win = (home_expected / total) * (1 - draw_prob)
        away_win = (away_expected / total) * (1 - draw_prob)
        
        return {
            'home_elo': home_elo,
            'away_elo': away_elo,
            'elo_diff': home_elo - away_elo,
            'home_win_prob': home_win,
            'draw_prob': draw_prob,
            'away_win_prob': away_win,
            'predicted_result': 'H' if home_win > away_win and home_win > draw_prob else ('A' if away_win > draw_prob else 'D')
        }


# Global calculator instance (cached)
_elo_calculator = None


def get_elo_calculator(recalculate: bool = False) -> EloCalculator:
    """
    Get or create the global Elo calculator
    
    Args:
        recalculate: If True, recalculate all ratings from scratch
        
    Returns:
        EloCalculator instance with ratings
    """
    global _elo_calculator
    
    if _elo_calculator is None or recalculate:
        _elo_calculator = EloCalculator()
        _elo_calculator.calculate_all_ratings()
    
    return _elo_calculator


if __name__ == "__main__":
    print("\n🏆 Elo Rating Calculator\n")
    
    calculator = EloCalculator()
    ratings = calculator.calculate_all_ratings()
    
    print("\n📊 Top 20 Teams by Elo Rating:")
    print("-" * 40)
    
    db = SessionLocal()
    top_teams = calculator.get_top_teams(20)
    
    for i, (team_id, elo) in enumerate(top_teams, 1):
        team = db.query(Team).filter(Team.id == team_id).first()
        team_name = team.name if team else f"Team {team_id}"
        print(f"{i:2}. {team_name:25} {elo:.0f}")
    
    db.close()
    
    print("\n✅ Elo calculations complete!")
