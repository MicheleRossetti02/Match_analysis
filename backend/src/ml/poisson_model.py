"""
Poisson Goal Prediction Model
Uses Poisson distribution to calculate probability of each scoreline.
"""
import sys
import os
import numpy as np
from scipy.stats import poisson
from typing import Dict, Tuple, List
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.database import SessionLocal, Match


class PoissonGoalModel:
    """
    Poisson-based goal prediction model.
    
    Calculates expected goals for each team based on:
    - Team's attack strength
    - Opponent's defense strength  
    - League averages
    - Home advantage
    """
    
    HOME_ADVANTAGE = 0.25  # Extra goals for home team
    MAX_GOALS = 8  # Maximum goals to calculate probability for
    
    def __init__(self):
        self.league_avg_home_goals = 1.5
        self.league_avg_away_goals = 1.2
        self.team_attack = {}  # team_id -> attack rating
        self.team_defense = {}  # team_id -> defense rating
        
    def calculate_team_stats(self, db=None):
        """Calculate attack and defense ratings for all teams"""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            # Get all finished matches
            matches = db.query(Match).filter(
                Match.status == 'FT',
                Match.home_goals.isnot(None),
                Match.away_goals.isnot(None)
            ).all()
            
            if not matches:
                return
            
            # Calculate league averages
            total_home_goals = sum(m.home_goals for m in matches)
            total_away_goals = sum(m.away_goals for m in matches)
            n_matches = len(matches)
            
            self.league_avg_home_goals = total_home_goals / n_matches
            self.league_avg_away_goals = total_away_goals / n_matches
            
            # Calculate per-team stats
            team_home_scored = {}
            team_home_conceded = {}
            team_away_scored = {}
            team_away_conceded = {}
            team_home_matches = {}
            team_away_matches = {}
            
            for match in matches:
                # Home team
                ht = match.home_team_id
                if ht not in team_home_scored:
                    team_home_scored[ht] = 0
                    team_home_conceded[ht] = 0
                    team_home_matches[ht] = 0
                team_home_scored[ht] += match.home_goals
                team_home_conceded[ht] += match.away_goals
                team_home_matches[ht] += 1
                
                # Away team
                at = match.away_team_id
                if at not in team_away_scored:
                    team_away_scored[at] = 0
                    team_away_conceded[at] = 0
                    team_away_matches[at] = 0
                team_away_scored[at] += match.away_goals
                team_away_conceded[at] += match.home_goals
                team_away_matches[at] += 1
            
            # Calculate attack and defense ratings
            for team_id in set(team_home_matches.keys()) | set(team_away_matches.keys()):
                # Attack = goals scored / league average
                home_attack = (team_home_scored.get(team_id, 0) / max(team_home_matches.get(team_id, 1), 1)) / self.league_avg_home_goals if self.league_avg_home_goals > 0 else 1
                away_attack = (team_away_scored.get(team_id, 0) / max(team_away_matches.get(team_id, 1), 1)) / self.league_avg_away_goals if self.league_avg_away_goals > 0 else 1
                self.team_attack[team_id] = (home_attack + away_attack) / 2
                
                # Defense = goals conceded / league average
                home_defense = (team_home_conceded.get(team_id, 0) / max(team_home_matches.get(team_id, 1), 1)) / self.league_avg_away_goals if self.league_avg_away_goals > 0 else 1
                away_defense = (team_away_conceded.get(team_id, 0) / max(team_away_matches.get(team_id, 1), 1)) / self.league_avg_home_goals if self.league_avg_home_goals > 0 else 1
                self.team_defense[team_id] = (home_defense + away_defense) / 2
            
            print(f"✅ Calculated stats for {len(self.team_attack)} teams")
            
        finally:
            if should_close:
                db.close()
    
    def get_expected_goals(self, home_team_id: int, away_team_id: int) -> Tuple[float, float]:
        """
        Calculate expected goals for each team
        
        Returns:
            Tuple of (expected_home_goals, expected_away_goals)
        """
        home_attack = self.team_attack.get(home_team_id, 1.0)
        home_defense = self.team_defense.get(home_team_id, 1.0)
        away_attack = self.team_attack.get(away_team_id, 1.0)
        away_defense = self.team_defense.get(away_team_id, 1.0)
        
        # Expected goals = attack * opponent_defense * league_avg
        exp_home = home_attack * away_defense * self.league_avg_home_goals + self.HOME_ADVANTAGE
        exp_away = away_attack * home_defense * self.league_avg_away_goals
        
        # Clamp to reasonable values
        exp_home = max(0.5, min(4.0, exp_home))
        exp_away = max(0.3, min(3.5, exp_away))
        
        return exp_home, exp_away
    
    def get_score_probabilities(self, home_team_id: int, away_team_id: int) -> np.ndarray:
        """
        Calculate probability matrix for all scorelines
        
        Returns:
            2D numpy array where prob[i][j] = P(home scores i, away scores j)
        """
        exp_home, exp_away = self.get_expected_goals(home_team_id, away_team_id)
        
        # Create probability matrix
        prob_matrix = np.zeros((self.MAX_GOALS + 1, self.MAX_GOALS + 1))
        
        for home_goals in range(self.MAX_GOALS + 1):
            for away_goals in range(self.MAX_GOALS + 1):
                # Poisson probability: P(X=k) = (λ^k * e^-λ) / k!
                prob_home = poisson.pmf(home_goals, exp_home)
                prob_away = poisson.pmf(away_goals, exp_away)
                prob_matrix[home_goals][away_goals] = prob_home * prob_away
        
        return prob_matrix
    
    def predict_match(self, home_team_id: int, away_team_id: int) -> Dict:
        """
        Get full match prediction with all probabilities
        """
        prob_matrix = self.get_score_probabilities(home_team_id, away_team_id)
        exp_home, exp_away = self.get_expected_goals(home_team_id, away_team_id)
        
        # Calculate outcome probabilities
        home_win = 0.0
        draw = 0.0
        away_win = 0.0
        
        for h in range(self.MAX_GOALS + 1):
            for a in range(self.MAX_GOALS + 1):
                if h > a:
                    home_win += prob_matrix[h][a]
                elif h == a:
                    draw += prob_matrix[h][a]
                else:
                    away_win += prob_matrix[h][a]
        
        # Find most likely scores
        top_scores = []
        for h in range(min(5, self.MAX_GOALS + 1)):
            for a in range(min(5, self.MAX_GOALS + 1)):
                top_scores.append((h, a, prob_matrix[h][a]))
        
        top_scores.sort(key=lambda x: x[2], reverse=True)
        
        # Calculate over/under probabilities
        total_prob = np.sum(prob_matrix)
        over_15 = sum(prob_matrix[h][a] for h in range(self.MAX_GOALS + 1) for a in range(self.MAX_GOALS + 1) if h + a > 1.5) / total_prob
        over_25 = sum(prob_matrix[h][a] for h in range(self.MAX_GOALS + 1) for a in range(self.MAX_GOALS + 1) if h + a > 2.5) / total_prob
        over_35 = sum(prob_matrix[h][a] for h in range(self.MAX_GOALS + 1) for a in range(self.MAX_GOALS + 1) if h + a > 3.5) / total_prob
        
        # BTTS probability
        btts = sum(prob_matrix[h][a] for h in range(1, self.MAX_GOALS + 1) for a in range(1, self.MAX_GOALS + 1)) / total_prob
        
        return {
            'expected_home_goals': exp_home,
            'expected_away_goals': exp_away,
            'home_win_prob': home_win,
            'draw_prob': draw,
            'away_win_prob': away_win,
            'most_likely_score': f"{top_scores[0][0]}-{top_scores[0][1]}",
            'score_probability': top_scores[0][2],
            'top_5_scores': [(f"{s[0]}-{s[1]}", round(s[2], 4)) for s in top_scores[:5]],
            'over_15_prob': over_15,
            'over_25_prob': over_25,
            'over_35_prob': over_35,
            'btts_prob': btts
        }


# Global model instance
_poisson_model = None


def get_poisson_model(recalculate: bool = False) -> PoissonGoalModel:
    """Get or create the global Poisson model"""
    global _poisson_model
    
    if _poisson_model is None or recalculate:
        _poisson_model = PoissonGoalModel()
        _poisson_model.calculate_team_stats()
    
    return _poisson_model


if __name__ == "__main__":
    print("\n⚽ Poisson Goal Model\n")
    
    model = PoissonGoalModel()
    model.calculate_team_stats()
    
    print(f"\n📊 League Averages:")
    print(f"   Home goals: {model.league_avg_home_goals:.2f}")
    print(f"   Away goals: {model.league_avg_away_goals:.2f}")
    
    # Example prediction (first two teams)
    if model.team_attack:
        teams = list(model.team_attack.keys())[:2]
        if len(teams) >= 2:
            pred = model.predict_match(teams[0], teams[1])
            print(f"\n🎯 Example Prediction (Team {teams[0]} vs Team {teams[1]}):")
            print(f"   Expected: {pred['expected_home_goals']:.2f} - {pred['expected_away_goals']:.2f}")
            print(f"   Most likely: {pred['most_likely_score']} ({pred['score_probability']:.1%})")
            print(f"   Probs: H={pred['home_win_prob']:.1%} D={pred['draw_prob']:.1%} A={pred['away_win_prob']:.1%}")
    
    print("\n✅ Poisson model ready!")
