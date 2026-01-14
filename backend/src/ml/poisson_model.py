"""
Dixon-Coles Bivariate Poisson Model for Football Predictions
Implements correlation-aware goal predictions with τ adjustment
"""
import sys
import os
import numpy as np
from scipy.stats import poisson
from typing import Dict, Tuple
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.database import SessionLocal, Match


class DixonColesPoissonModel:
    """
    Dixon-Coles Bivariate Poisson Model
    
    Accounts for correlation between home and away goals,
    particularly for low-scoring matches (0-0, 1-0, 0-1, 1-1)
    
    Reference:
        Dixon, M. J., & Coles, S. G. (1997). "Modelling Association Football 
        Scores and Inefficiencies in the Football Betting Market"
    """
    
    HOME_ADVANTAGE = 0.25
    MAX_GOALS = 8
    
    def __init__(self, rho: float = -0.13):
        """
        Initialize with correlation parameter
        
        Args:
            rho: Correlation coefficient (negative = defensive correlation)
                 Typical value for football: -0.13
        """
        self.league_avg_home_goals = 1.5
        self.league_avg_away_goals = 1.2
        self.team_attack = {}
        self.team_defense = {}
        self.rho = rho
    
    def calculate_team_stats(self, db=None):
        """Calculate attack and defense ratings for all teams"""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
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
            
            # Calculate ratings
            for team_id in set(team_home_matches.keys()) | set(team_away_matches.keys()):
                home_attack = (team_home_scored.get(team_id, 0) / max(team_home_matches.get(team_id, 1), 1)) / self.league_avg_home_goals if self.league_avg_home_goals > 0 else 1
                away_attack = (team_away_scored.get(team_id, 0) / max(team_away_matches.get(team_id, 1), 1)) / self.league_avg_away_goals if self.league_avg_away_goals > 0 else 1
                self.team_attack[team_id] = (home_attack + away_attack) / 2
                
                home_defense = (team_home_conceded.get(team_id, 0) / max(team_home_matches.get(team_id, 1), 1)) / self.league_avg_away_goals if self.league_avg_away_goals > 0 else 1
                away_defense = (team_away_conceded.get(team_id, 0) / max(team_away_matches.get(team_id, 1), 1)) / self.league_avg_home_goals if self.league_avg_home_goals > 0 else 1
                self.team_defense[team_id] = (home_defense + away_defense) / 2
            
        finally:
            if should_close:
                db.close()
    
    def dixon_coles_adjustment(self, home_goals: int, away_goals: int, 
                              lambda_home: float, lambda_away: float) -> float:
        """
        Dixon-Coles τ adjustment for low scores
        
        Formula: 
            τ(i,j) = 1 - λ_home × λ_away × ρ   if i,j ∈ {0,1}
            τ(i,j) = 1                          otherwise
        
        Args:
            home_goals: Home team goals
            away_goals: Away team goals
            lambda_home: Expected home goals
            lambda_away: Expected away goals
            
        Returns:
            Adjustment factor τ (tau)
        """
        if home_goals > 1 or away_goals > 1:
            return 1.0
        
        tau = 1.0 - lambda_home * lambda_away * self.rho
        return tau
    
    def get_expected_goals(self, home_team_id: int, away_team_id: int) -> Tuple[float, float]:
        """Calculate expected goals with bounds"""
        home_attack = self.team_attack.get(home_team_id, 1.0)
        home_defense = self.team_defense.get(home_team_id, 1.0)
        away_attack = self.team_attack.get(away_team_id, 1.0)
        away_defense = self.team_defense.get(away_team_id, 1.0)
        
        lambda_home = home_attack * away_defense * self.league_avg_home_goals + self.HOME_ADVANTAGE
        lambda_away = away_attack * home_defense * self.league_avg_away_goals
        
        # Bounds to prevent extremes
        lambda_home = max(0.3, min(4.0, lambda_home))
        lambda_away = max(0.3, min(3.5, lambda_away))
        
        return lambda_home, lambda_away
    
    def predict_score_probabilities(self, home_team_id: int, away_team_id: int) -> Tuple[Dict, float, float]:
        """Calculate score probabilities with Dixon-Coles adjustment"""
        lambda_home, lambda_away = self.get_expected_goals(home_team_id, away_team_id)
        
        probabilities = {}
        for i in range(self.MAX_GOALS + 1):
            for j in range(self.MAX_GOALS + 1):
                # Independent Poisson
                prob_independent = poisson.pmf(i, lambda_home) * poisson.pmf(j, lambda_away)
                
                # Dixon-Coles adjustment
                tau = self.dixon_coles_adjustment(i, j, lambda_home, lambda_away)
                
                # Adjusted probability
                prob_adjusted = prob_independent * tau
                probabilities[f"{i}-{j}"] = prob_adjusted
        
        # Normalize
        total_prob = sum(probabilities.values())
        if total_prob > 0:
            probabilities = {k: v/total_prob for k, v in probabilities.items()}
        
        return probabilities, lambda_home, lambda_away
    
    def predict_match(self, home_team_id: int, away_team_id: int) -> Dict:
        """
        Full match prediction with all markets including DC and Combo
        
        Returns:
            dict with probabilities for:
                - 1X2 (home_win, draw, away_win)
                - Double Chance (double_chance_probs)
                - Over/Under (over_15, over_25, over_35)
                - BTTS (btts)
                - Combo (combo_predictions)
        """
        score_probs, exp_home, exp_away = self.predict_score_probabilities(home_team_id, away_team_id)
        
        # 1X2 probabilities
        prob_home = sum(v for k, v in score_probs.items() if self._is_home_win(k))
        prob_draw = sum(v for k, v in score_probs.items() if self._is_draw(k))
        prob_away = sum(v for k, v in score_probs.items() if self._is_away_win(k))
        
        # Double Chance
        prob_1x = prob_home + prob_draw
        prob_12 = prob_home + prob_away
        prob_x2 = prob_draw + prob_away
        
        # Over/Under
        prob_over_15 = sum(v for k, v in score_probs.items() if self._total_goals(k) > 1.5)
        prob_over_25 = sum(v for k, v in score_probs.items() if self._total_goals(k) > 2.5)
        prob_over_35 = sum(v for k, v in score_probs.items() if self._total_goals(k) > 3.5)
        
        # BTTS
        prob_btts = sum(v for k, v in score_probs.items() if self._is_btts(k))
        
        # Combo probabilities (correlation-aware)
        combo_1_over_25 = sum(v for k, v in score_probs.items() 
                              if self._is_home_win(k) and self._total_goals(k) > 2.5)
        combo_x_under_25 = sum(v for k, v in score_probs.items() 
                               if self._is_draw(k) and self._total_goals(k) <= 2.5)
        combo_gg_over_25 = sum(v for k, v in score_probs.items()
                               if self._is_btts(k) and self._total_goals(k) > 2.5)
        
        # Most likely scores
        top_scores = sorted(score_probs.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'expected_home_goals': round(exp_home, 2),
            'expected_away_goals': round(exp_away, 2),
            'correlation_rho': self.rho,
            'home_win': round(prob_home, 4),
            'draw': round(prob_draw, 4),
            'away_win': round(prob_away, 4),
            'double_chance_probs': {
                '1X': round(prob_1x, 4),
                '12': round(prob_12, 4),
                'X2': round(prob_x2, 4)
            },
            'over_15': round(prob_over_15, 4),
            'over_25': round(prob_over_25, 4),
            'over_35': round(prob_over_35, 4),
            'btts': round(prob_btts, 4),
            'combo_predictions': {
                '1_over_25': round(combo_1_over_25, 4),
                'x_under_25': round(combo_x_under_25, 4),
                'gg_over_25': round(combo_gg_over_25, 4)
            },
            'most_likely_score': top_scores[0][0] if top_scores else "1-1",
            'top_5_scores': [(score, round(prob, 4)) for score, prob in top_scores]
        }
    
    def _is_home_win(self, score: str) -> bool:
        if '-' not in score:
            return False
        h, a = map(int, score.split('-'))
        return h > a
    
    def _is_draw(self, score: str) -> bool:
        if '-' not in score:
            return False
        h, a = map(int, score.split('-'))
        return h == a
    
    def _is_away_win(self, score: str) -> bool:
        if '-' not in score:
            return False
        h, a = map(int, score.split('-'))
        return a > h
    
    def _total_goals(self, score: str) -> int:
        if '-' not in score:
            return 0
        h, a = map(int, score.split('-'))
        return h + a
    
    def _is_btts(self, score: str) -> bool:
        if '-' not in score:
            return False
        h, a = map(int, score.split('-'))
        return h >= 1 and a >= 1


# Global instance
_poisson_model = None

def get_poisson_model(recalculate: bool = False):
    """Get or create global Dixon-Coles model"""
    global _poisson_model
    
    if _poisson_model is None or recalculate:
        _poisson_model = DixonColesPoissonModel()
        _poisson_model.calculate_team_stats()
    
    return _poisson_model


if __name__ == "__main__":
    print("\n⚽ Dixon-Coles Bivariate Poisson Model\n")
    model = DixonColesPoissonModel(rho=-0.13)
    model.calculate_team_stats()
    
    if model.team_attack:
        teams = list(model.team_attack.keys())[:2]
        if len(teams) >= 2:
            pred = model.predict_match(teams[0], teams[1])
            print(f"\n🎯 Example: Team {teams[0]} vs Team {teams[1]}")
            print(f"   Expected: {pred['expected_home_goals']:.2f} - {pred['expected_away_goals']:.2f}")
            print(f"   1X2: H={pred['home_win']:.1%} D={pred['draw']:.1%} A={pred['away_win']:.1%}")
            print(f"   DC: 1X={pred['double_chance_probs']['1X']:.1%}")
            print(f"   Combo: {pred['combo_predictions']}")
    
    print("\n✅ Dixon-Coles model ready!")
