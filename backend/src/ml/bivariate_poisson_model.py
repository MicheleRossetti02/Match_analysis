"""
Bivariate Poisson Model for Combo Bet Predictions
Properly models correlation between match result and goal totals
Avoids naive P(A) × P(B) assumption that treats outcomes as independent
"""
import sys
import os
import numpy as np
from scipy.stats import poisson
from typing import Dict, Tuple
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.database import SessionLocal, Match


class BivariatePoissonModel:
    """
    Bivariate Poisson model for correlated predictions
    
    Models: P(Home=i, Away=j) with correlation parameter λ3
    
    Key insight: Strong home teams tend to both WIN and score MANY goals.
    This correlation means P(Home Win AND Over 2.5) > P(Home Win) × P(Over 2.5)
    
    Mathematical Formula:
    P(X=i, Y=j) = exp(-λ1 - λ2 - λ3) × Σ_k [ (λ1^(i-k) × λ2^(j-k) × λ3^k) / ((i-k)! × (j-k)! × k!) ]
    
    Where:
    - λ1 = expected home goals (marginal)
    - λ2 = expected away goals (marginal)
    - λ3 = correlation parameter (positive correlation)
    """
    
    MAX_GOALS = 8  # Maximum goals to calculate
    
    def __init__(self):
        self.lambda_home = 1.5  # Default home goal rate
        self.lambda_away = 1.2  # Default away goal rate
        self.lambda_corr = 0.1  # Default correlation (positive)
        self.team_attack = {}
        self.team_defense = {}
    
    def calculate_team_stats(self, db=None):
        """Calculate attack/defense ratings for teams (reuse Poisson model logic)"""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            # Import existing Poisson model stats
            from src.ml.poisson_model import get_poisson_model
            poisson = get_poisson_model()
            
            self.team_attack = poisson.team_attack.copy()
            self.team_defense = poisson.team_defense.copy()
            self.lambda_home = poisson.league_avg_home_goals
            self.lambda_away = poisson.league_avg_away_goals
            
            # Estimate correlation from data
            self._estimate_correlation(db)
            
            print(f"✅ Bivariate Poisson: {len(self.team_attack)} teams, λ3={self.lambda_corr:.3f}")
            
        finally:
            if should_close:
                db.close()
    
    def _estimate_correlation(self, db):
        """Estimate correlation parameter λ3 from match data"""
        # Get finished matches
        matches = db.query(Match).filter(
            Match.status == 'FT',
            Match.home_goals.isnot(None),
            Match.away_goals.isnot(None)
        ).limit(1000).all()
        
        if not matches:
            self.lambda_corr = 0.05
            return
        
        # Calculate covariance between home and away goals
        home_goals = [m.home_goals for m in matches]
        away_goals = [m.away_goals for m in matches]
        
        cov = np.cov(home_goals, away_goals)[0, 1]
        
        # Positive covariance suggests positive correlation
        # Scale to reasonable λ3 range (0.0 - 0.3)
        self.lambda_corr = max(0.0, min(0.3, cov * 0.1))
    
    def get_expected_goals(self, home_team_id: int, away_team_id: int) -> Tuple[float, float]:
        """Get marginal expected goals for each team"""
        home_attack = self.team_attack.get(home_team_id, 1.0)
        away_attack = self.team_attack.get(away_team_id, 1.0)
        home_defense = self.team_defense.get(home_team_id, 1.0)
        away_defense = self.team_defense.get(away_team_id, 1.0)
        
        lambda1 = home_attack * away_defense * self.lambda_home + 0.25  # Home advantage
        lambda2 = away_attack * home_defense * self.lambda_away
        
        # Clamp to reasonable ranges
        lambda1 = max(0.3, min(4.0, lambda1))
        lambda2 = max(0.3, min(3.5, lambda2))
        
        return lambda1, lambda2
    
    def predict_scoreline_matrix(self, home_team_id: int, away_team_id: int) -> np.ndarray:
        """
        Calculate probability matrix P(home=i, away=j) using Bivariate Poisson
        
        Returns:
            2D array where matrix[i][j] = P(home scores i, away scores j)
        """
        lambda1, lambda2 = self.get_expected_goals(home_team_id, away_team_id)
        lambda3 = self.lambda_corr
        
        prob_matrix = np.zeros((self.MAX_GOALS + 1, self.MAX_GOALS + 1))
        
        for i in range(self.MAX_GOALS + 1):
            for j in range(self.MAX_GOALS + 1):
                # Bivariate Poisson formula
                prob_sum = 0.0
                max_k = min(i, j)
                
                for k in range(max_k + 1):
                    term = (
                        (lambda1 ** (i - k)) * (lambda2 ** (j - k)) * (lambda3 ** k) /
                        (np.math.factorial(i - k) * np.math.factorial(j - k) * np.math.factorial(k))
                    )
                    prob_sum += term
                
                prob_matrix[i][j] = np.exp(-lambda1 - lambda2 - lambda3) * prob_sum
        
        # Normalize to ensure probabilities sum to ~1.0
        total = np.sum(prob_matrix)
        if total > 0:
            prob_matrix /= total
        
        return prob_matrix
    
    def predict_combo(self, home_team_id: int, away_team_id: int) -> Dict[str, float]:
        """
        Predict combo bet probabilities with correlation
        
        Returns correlated probabilities for:
        - Home Win AND Over 2.5
        - Away Win AND Over 2.5
        - Draw AND Under 2.5
        - Home Win AND BTTS
        - Away Win AND BTTS
        - Draw AND BTTS
        """
        prob_matrix = self.predict_scoreline_matrix(home_team_id, away_team_id)
        
        # Calculate combo probabilities by summing relevant cells
        combo_1_over_25 = 0  # Home win AND >2.5 goals
        combo_2_over_25 = 0  # Away win AND >2.5 goals
        combo_x_under_25 = 0  # Draw AND <=2.5 goals
        combo_1_btts = 0  # Home win AND both score
        combo_2_btts = 0  # Away win AND both score
        combo_x_btts = 0  # Draw AND both score
        
        for i in range(self.MAX_GOALS + 1):
            for j in range(self.MAX_GOALS + 1):
                total_goals = i + j
                is_home_win = i > j
                is_away_win = j > i
                is_draw = i == j
                is_over_25 = total_goals > 2.5
                is_under_25 = total_goals <= 2.5
                is_btts = i >= 1 and j >= 1
                
                prob = prob_matrix[i][j]
                
                if is_home_win and is_over_25:
                    combo_1_over_25 += prob
                if is_away_win and is_over_25:
                    combo_2_over_25 += prob
                if is_draw and is_under_25:
                    combo_x_under_25 += prob
                if is_home_win and is_btts:
                    combo_1_btts += prob
                if is_away_win and is_btts:
                    combo_2_btts += prob
                if is_draw and is_btts:
                    combo_x_btts += prob
        
        return {
            '1_over_25': combo_1_over_25,
            '2_over_25': combo_2_over_25,
            'x_under_25': combo_x_under_25,
            '1_btts': combo_1_btts,
            '2_btts': combo_2_btts,
            'x_btts': combo_x_btts
        }
    
    def compare_with_naive(self, home_team_id: int, away_team_id: int):
        """
        Compare Bivariate Poisson with naive independence assumption
        Shows why correlation matters!
        """
        # Bivariate (correct)
        combo_correlated = self.predict_combo(home_team_id, away_team_id)
        
        # Naive independence (wrong!)
        prob_matrix = self.predict_scoreline_matrix(home_team_id, away_team_id)
        
        # Calculate marginal probabilities
        prob_home = sum(prob_matrix[i][j] for i in range(self.MAX_GOALS + 1) for j in range(self.MAX_GOALS + 1) if i > j)
        prob_away = sum(prob_matrix[i][j] for i in range(self.MAX_GOALS + 1) for j in range(self.MAX_GOALS + 1) if j > i)
        prob_draw = sum(prob_matrix[i][i] for i in range(self.MAX_GOALS + 1))
        prob_over_25 = sum(prob_matrix[i][j] for i in range(self.MAX_GOALS + 1) for j in range(self.MAX_GOALS + 1) if i + j > 2.5)
        prob_under_25 = 1 - prob_over_25
        prob_btts = sum(prob_matrix[i][j] for i in range(1, self.MAX_GOALS + 1) for j in range(1, self.MAX_GOALS + 1))
        
        # Naive multiplication
        naive = {
            '1_over_25': prob_home * prob_over_25,
            '2_over_25': prob_away * prob_over_25,
            'x_under_25': prob_draw * prob_under_25,
            '1_btts': prob_home * prob_btts,
            '2_btts': prob_away * prob_btts,
            'x_btts': prob_draw * prob_btts
        }
        
        return combo_correlated, naive


# Global instance
_bivariate_model = None


def get_bivariate_poisson_model(recalculate: bool = False) -> BivariatePoissonModel:
    """Get or create the global Bivariate Poisson model"""
    global _bivariate_model
    
    if _bivariate_model is None or recalculate:
        _bivariate_model = BivariatePoissonModel()
        _bivariate_model.calculate_team_stats()
    
    return _bivariate_model


if __name__ == "__main__":
    print("\n📊 Bivariate Poisson Model Demo\n")
    print("=" * 70)
    
    model = BivariatePoissonModel()
    model.calculate_team_stats()
    
    print(f"\n🔬 Model Parameters:")
    print(f"   League avg home goals: {model.lambda_home:.2f}")
    print(f"   League avg away goals: {model.lambda_away:.2f}")
    print(f"   Correlation λ3: {model.lambda_corr:.3f}")
    
    # Example prediction
    if model.team_attack:
        teams = list(model.team_attack.keys())[:2]
        if len(teams) >= 2:
            print(f"\n⚽ Example: Team {teams[0]} vs Team {teams[1]}")
            
            combos = model.predict_combo(teams[0], teams[1])
            
            print(f"\n📈 Combo Probabilities (with correlation):")
            print(f"   • Home Win + Over 2.5: {combos['1_over_25']:.1%}")
            print(f"   • Away Win + Over 2.5: {combos['2_over_25']:.1%}")
            print(f"   • Draw + Under 2.5: {combos['x_under_25']:.1%}")
            print(f"   • Home Win + BTTS: {combos['1_btts']:.1%}")
            print(f"   • Away Win + BTTS: {combos['2_btts']:.1%}")
            print(f"   • Draw + BTTS: {combos['x_btts']:.1%}")
            
            # Compare with naive
            correlated, naive = model.compare_with_naive(teams[0], teams[1])
            
            print(f"\n🔍 Correlation Effect (Bivariate vs Naive):")
            for key in ['1_over_25', '1_btts']:
                diff = correlated[key] - naive[key]
                pct_diff = (diff / naive[key] * 100) if naive[key] > 0 else 0
                print(f"   {key}: {correlated[key]:.1%} vs {naive[key]:.1%} ({diff:+.1%}, {pct_diff:+.0f}%)")
    
    print("\n✅ Bivariate Poisson model ready!\n")
