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
    RHO = -0.13  # Dixon-Coles correlation parameter (typical value for football)
    
    def __init__(self, rho: float = -0.13):
        """
        Initialize Poisson model with Dixon-Coles correlation
        
        Args:
            rho: Correlation parameter (default -0.13 for football)
                 Negative values indicate defensive correlation
                 (both teams tend to not score together)
        """
        self.league_avg_home_goals = 1.5
        self.league_avg_away_goals = 1.2
        self.team_attack = {}  # team_id -> attack rating
        self.team_defense = {}  # team_id -> defense rating
        self.rho = rho  # Dixon-Coles correlation parameter
        
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
            print(f"   League avg: {self.league_avg_home_goals:.2f} home, {self.league_avg_away_goals:.2f} away")
            print(f"   Dixon-Coles ρ: {self.rho:.3f}")
            
        finally:
            if should_close:
                db.close()
    
    def dixon_coles_adjustment(self, home_goals: int, away_goals: int, lambda_home: float, lambda_away: float) -> float:
        """
        Dixon-Coles adjustment factor for low-scoring matches
        
        Adjusts probability for scores (0,0), (1,0), (0,1), (1,1) to account for correlation
        between home and away goals. This corrects the independence assumption of basic Poisson.
        
        Mathematical Formula:
        τ(i,j) = 1 - λ_home * λ_away * ρ   if i,j ∈ {0,1}
        τ(i,j) = 1                          otherwise
        
        Args:
            home_goals: Home team goals
            away_goals: Away team goals  
            lambda_home: Expected home goals
            lambda_away: Expected away goals
            
        Returns:
            Adjustment factor τ (tau)
            
        Reference:
            Dixon, M. J., & Coles, S. G. (1997). "Modelling Association Football Scores 
            and Inefficiencies in the Football Betting Market"
        """
        # Only adjust for low scores (0,0), (1,0), (0,1), (1,1)
        if home_goals > 1 or away_goals > 1:
            return 1.0
        
        # Dixon-Coles adjustment formula
        tau = 1.0 - lambda_home * lambda_away * self.rho
        
        return tau
    
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
        
        # Calculate expected goals (lambda) with floor/ceiling
        lambda_home = home_attack * away_defense * self.league_avg_home_goals + self.HOME_ADVANTAGE
        lambda_away = away_attack * home_defense * self.league_avg_away_goals
        
        # Apply bounds to prevent extreme values
        lambda_home = max(0.3, min(4.0, lambda_home))
        lambda_away = max(0.3, min(3.5, lambda_away))
        
        return lambda_home, lambda_away
    
    def predict_score_probabilities(self, home_team_id: int, away_team_id: int) -> Dict:
        """
        Calculate score probabilities using Dixon-Coles Bivariate Poisson
        
        This method applies the Dixon-Coles adjustment to correct for correlation
        in low-scoring matches, addressing the issue identified in technical review.
        """
        lambda_home, lambda_away = self.get_expected_goals(home_team_id, away_team_id)
        
        # Calculate probability matrix with Dixon-Coles adjustment
        probabilities = {}
        for i in range(self.MAX_GOALS + 1):
            for j in range(self.MAX_GOALS + 1):
                # Basic independent Poisson probability
                prob_independent = poisson.pmf(i, lambda_home) * poisson.pmf(j, lambda_away)
                
                # Apply Dixon-Coles adjustment for low scores
                tau = self.dixon_coles_adjustment(i, j, lambda_home, lambda_away)
                
                # Adjusted probability
                prob_adjusted = prob_independent * tau
                
                probabilities[f"{i}-{j}"] = prob_adjusted
        
        # Normalize to ensure probabilities sum to 1.0
        total_prob = sum(probabilities.values())
        if total_prob > 0:
            probabilities = {k: v/total_prob for k, v in probabilities.items()}
        
        # Additional useful stats
        probabilities['expected_home_goals'] = lambda_home
        probabilities['expected_away_goals'] = lambda_away
        probabilities['rho'] = self.rho
        
        return probabilities
    
    def predict_match(self, home_team_id: int, away_team_id: int) -> Dict:
        """
        Get full match prediction with Dixon-Coles adjusted probabilities
        
        Returns normalized probabilities for all markets including:
        - 1X2 (home/draw/away)
        - Double Chance (1X, 12, X2) 
        - Over/Under (1.5, 2.5, 3.5)
        - BTTS
        - Combo (JSON format)
        """
        # Get Dixon-Coles adjusted score probabilities
        score_probs = self.predict_score_probabilities(home_team_id, away_team_id)
        
        # Extract metadata
        exp_home = score_probs.pop('expected_home_goals')
        exp_away = score_probs.pop('expected_away_goals')
        rho = score_probs.pop('rho')
        
        # === NORMALIZATION CHECK ===
        # Ensure probabilities sum to exactly 1.0 after Dixon-Coles adjustment
        total_prob = sum(score_probs.values())
        if abs(total_prob - 1.0) > 0.001:
            print(f"⚠️  Warning: Probabilities sum to {total_prob:.6f}, renormalizing...")
            score_probs = {k: v/total_prob for k, v in score_probs.items()}
        
        # === 1X2 PROBABILITIES ===
        prob_home = sum(v for k, v in score_probs.items() if self._is_home_win(k))
        prob_draw = sum(v for k, v in score_probs.items() if self._is_draw(k))
        prob_away = sum(v for k, v in score_probs.items() if self._is_away_win(k))
        
        # === DOUBLE CHANCE (from adjusted matrix) ===
        prob_1x = prob_home + prob_draw  # Home or Draw
        prob_12 = prob_home + prob_away  # Home or Away (no draw)
        prob_x2 = prob_draw + prob_away  # Draw or Away
        
        # === OVER/UNDER ===
        prob_over_15 = sum(v for k, v in score_probs.items() if self._total_goals(k) > 1.5)
        prob_over_25 = sum(v for k, v in score_probs.items() if self._total_goals(k) > 2.5)
        prob_over_35 = sum(v for k, v in score_probs.items() if self._total_goals(k) > 3.5)
        
        # === BTTS ===
        prob_btts = sum(v for k, v in score_probs.items() if self._is_btts(k))
        
        # === COMBO PROBABILITIES (with Dixon-Coles correlation) ===
        combo_1_over_25 = sum(v for k, v in score_probs.items() 
                              if self._is_home_win(k) and self._total_goals(k) > 2.5)
        combo_2_over_25 = sum(v for k, v in score_probs.items() 
                              if self._is_away_win(k) and self._total_goals(k) > 2.5)
        combo_x_under_25 = sum(v for k, v in score_probs.items() 
                               if self._is_draw(k) and self._total_goals(k) <= 2.5)
        combo_1_btts = sum(v for k, v in score_probs.items() 
                           if self._is_home_win(k) and self._is_btts(k))
        combo_2_btts = sum(v for k, v in score_probs.items() 
                           if self._is_away_win(k) and self._is_btts(k))
        combo_x_btts = sum(v for k, v in score_probs.items() 
                           if self._is_draw(k) and self._is_btts(k))
        combo_gg_over_25 = sum(v for k, v in score_probs.items()
                               if self._is_btts(k) and self._total_goals(k) > 2.5)
        
        # === COMBO JSON STRUCTURE ===
        combo_predictions_json = {
            "1_over_25": round(combo_1_over_25, 4),
            "2_over_25": round(combo_2_over_25, 4),
            "x_under_25": round(combo_x_under_25, 4),
            "1_btts": round(combo_1_btts, 4),
            "2_btts": round(combo_2_btts, 4),
            "x_btts": round(combo_x_btts, 4),
            "gg_over_25": round(combo_gg_over_25, 4)
        }
        
        # Find most likely scores
        top_scores = sorted(score_probs.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            # Expected goals
            'expected_home_goals': exp_home,
            'expected_away_goals': exp_away,
            'correlation_rho': rho,
            
            # 1X2 Market
            'home_win': prob_home,
            'draw': prob_draw,
            'away_win': prob_away,
            
            # Double Chance Market (derived from adjusted matrix)
            'double_chance': {
                '1X': prob_1x,
                '12': prob_12,
                'X2': prob_x2
            },
            
            # Over/Under Market
            'over_15': prob_over_15,
            'over_25': prob_over_25,
            'over_35': prob_over_35,
            
            # BTTS Market
            'btts': prob_btts,
            
            # Combo Market (JSON format for database storage)
            'combo_predictions': combo_predictions_json,
            
            # Most likely scores
            'most_likely_score': top_scores[0][0] if top_scores else "1-1",
            'top_5_scores': [(score, round(prob, 4)) for score, prob in top_scores],
            
            # Validation metadata
            'normalization_check': abs(sum(score_probs.values()) - 1.0) < 0.001,
            'total_probability': round(sum(score_probs.values()), 6)
        }
    
    # Helper methods for score classification
    def _is_home_win(self, score: str) -> bool:
        """Check if score is a home win"""
        if '-' not in score:
            return False
        h, a = map(int, score.split('-'))
        return h > a
    
    def _is_draw(self, score: str) -> bool:
        """Check if score is a draw"""
        if '-' not in score:
            return False
        h, a = map(int, score.split('-'))
        return h == a
    
    def _is_away_win(self, score: str) -> bool:
        """Check if score is an away win"""
        if '-' not in score:
            return False
        h, a = map(int, score.split('-'))
        return a > h
    
    def _total_goals(self, score: str) -> int:
        """Get total goals in score"""
        if '-' not in score:
            return 0
        h, a = map(int, score.split('-'))
        return h + a
    
    def _is_btts(self, score: str) -> bool:
        """Check if both teams scored"""
        if '-' not in score:
            return False
        h, a = map(int, score.split('-'))
        return h >= 1 and a >= 1


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
    print("\n⚽ Dixon-Coles Poisson Model\n")
    print("=" * 70)
    
    model = PoissonGoalModel(rho=-0.13)
    print(f"\n📊 Model Configuration:")
    print(f"   Dixon-Coles ρ: {model.rho:.3f}")
    
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
