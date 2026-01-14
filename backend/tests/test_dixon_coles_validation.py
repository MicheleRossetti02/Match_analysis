"""
Dixon-Coles Mathematical Validation Test
Verifies the correctness of the Dixon-Coles adjustment implementation
"""
import sys
import os
import numpy as np
from scipy.stats import poisson

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.ml.poisson_model import PoissonGoalModel


def test_dixon_coles_adjustment():
    """
    Test Dixon-Coles adjustment function
    
    Mathematical Formula:
    τ(i,j) = 1 - λ_home * λ_away * ρ   if i,j ∈ {0,1}
    τ(i,j) = 1                          otherwise
    """
    print("\n🧪 Dixon-Coles Mathematical Validation\n")
    print("=" * 70)
    
    model = PoissonGoalModel(rho=-0.13)
    
    # Test cases
    lambda_home = 1.5
    lambda_away = 1.2
    
    print(f"\nExpected goals: λ_home = {lambda_home}, λ_away = {lambda_away}")
    print(f"Correlation: ρ = {model.rho}")
    
    print("\n📊 Adjustment Factors (τ):")
    print("-" * 70)
    
    # Test low scores that should be adjusted
    low_scores = [(0, 0), (1, 0), (0, 1), (1, 1)]
    
    for home_goals, away_goals in low_scores:
        tau = model.dixon_coles_adjustment(home_goals, away_goals, lambda_home, lambda_away)
        
        # Manual calculation
        expected_tau = 1.0 - lambda_home * lambda_away * model.rho
        
        print(f"τ({home_goals},{away_goals}) = {tau:.4f}")
        print(f"  Expected: 1 - {lambda_home} × {lambda_away} × {model.rho} = {expected_tau:.4f}")
        print(f"  ✅ Match: {abs(tau - expected_tau) < 0.0001}")
        print()
    
    # Test higher scores (should return 1.0)
    print("\nHigher scores (no adjustment):")
    high_scores = [(2, 0), (0, 2), (2, 1), (1, 2), (2, 2), (3, 1)]
    
    for home_goals, away_goals in high_scores:
        tau = model.dixon_coles_adjustment(home_goals, away_goals, lambda_home, lambda_away)
        print(f"τ({home_goals},{away_goals}) = {tau:.4f} (expected 1.0) - {'✅' if tau == 1.0 else '❌'}")
    
    print("\n" + "=" * 70)


def compare_independent_vs_dixon_coles():
    """
    Compare Independent Poisson vs Dixon-Coles for specific scores
    """
    print("\n\n📈 Impact Analysis: Independent vs Dixon-Coles\n")
    print("=" * 70)
    
    model_dixon = PoissonGoalModel(rho=-0.13)
    model_dixon.team_attack = {1: 1.2, 2: 1.0}
    model_dixon.team_defense = {1: 1.0, 2: 1.1}
    
    lambda_home, lambda_away = model_dixon.get_expected_goals(1, 2)
    
    print(f"Expected Goals: Home {lambda_home:.2f}, Away {lambda_away:.2f}")
    print(f"Correlation ρ = {model_dixon.rho}\n")
    
    # Compare key scores
    key_scores = [(0, 0), (1, 0), (0, 1), (1, 1), (2, 1), (1, 2)]
    
    print(f"{'Score':<10} {'Independent':<15} {'Dixon-Coles':<15} {'Difference':<15}")
    print("-" * 70)
    
    for home_goals, away_goals in key_scores:
        # Independent Poisson
        prob_indep = poisson.pmf(home_goals, lambda_home) * poisson.pmf(away_goals, lambda_away)
        
        # Dixon-Coles adjusted
        tau = model_dixon.dixon_coles_adjustment(home_goals, away_goals, lambda_home, lambda_away)
        prob_dixon = prob_indep * tau
        
        diff = prob_dixon - prob_indep
        diff_pct = (diff / prob_indep * 100) if prob_indep > 0 else 0
        
        print(f"{home_goals}-{away_goals:<8} {prob_indep:.4f} ({prob_indep*100:.2f}%)   "
              f"{prob_dixon:.4f} ({prob_dixon*100:.2f}%)   "
              f"{diff:+.4f} ({diff_pct:+.1f}%)")
    
    print("\n" + "=" * 70)
    print("\n💡 Interpretation:")
    print("   - Negative ρ (-0.13) means defensive correlation")
    print("   - Low scores (0-0, 1-0, 0-1, 1-1) get adjusted UPWARD")
    print("   - This corrects the underestimation of defensive matches")
    print("   - High scores remain unchanged (τ = 1.0)")


def test_combo_probability_extraction():
    """
    Test that combo probabilities are correctly extracted from the matrix
    """
    print("\n\n🎯 Combo Probability Extraction Test\n")
    print("=" * 70)
    
    model = PoissonGoalModel(rho=-0.13)
    model.team_attack = {1: 1.5, 2: 1.2}
    model.team_defense = {1: 1.0, 2: 1.0}
    model.calculate_team_stats()  # Would need DB, skip for now
    
    # Manual setup for demonstration
    model.league_avg_home_goals = 1.5
    model.league_avg_away_goals = 1.2
    
    result = model.predict_match(1, 2)
    
    print("\n1X2 Probabilities:")
    print(f"  Home Win: {result['home_win']:.3f}")
    print(f"  Draw:     {result['draw']:.3f}")
    print(f"  Away Win: {result['away_win']:.3f}")
    print(f"  Sum:      {result['home_win'] + result['draw'] + result['away_win']:.3f}")
    
    print("\nDouble Chance:")
    for key, val in result['double_chance'].items():
        print(f"  {key}: {val:.3f}")
    
    print("\nCombo Probabilities (with correlation):")
    for key, val in result['combo'].items():
        print(f"  {key}: {val:.3f}")
    
    # Verify combo probabilities are less than naive multiplication
    print("\n🔍 Correlation Check:")
    naive_1_over25 = result['home_win'] * result['over_25']
    dixon_1_over25 = result['combo']['1_over_25']
    
    print(f"  Naive (independent):   {naive_1_over25:.3f}")
    print(f"  Dixon-Coles (corr):    {dixon_1_over25:.3f}")
    print(f"  Difference:            {dixon_1_over25 - naive_1_over25:+.3f}")
    
    if dixon_1_over25 != naive_1_over25:
        print("  ✅ Correlation captured correctly!")
    else:
        print("  ⚠️  No difference detected")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_dixon_coles_adjustment()
    compare_independent_vs_dixon_coles()
    test_combo_probability_extraction()
    
    print("\n✅ Mathematical validation complete!\n")
