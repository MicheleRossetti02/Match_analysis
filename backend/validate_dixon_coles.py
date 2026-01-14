"""
Validation Script for Dixon-Coles Implementation
Tests normalization, Double Chance logic, and Combo JSON storage
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.ml.poisson_model import PoissonGoalModel


def test_normalization():
    """Test that probability matrix sums to 1.0 after Dixon-Coles adjustment"""
    print("\n🧪 TEST 1: Probability Normalization")
    print("=" * 70)
    
    model = PoissonGoalModel(rho=-0.13)
    
    # Manual setup (no database needed)
    model.team_attack = {1: 1.5, 2: 1.2}
    model.team_defense = {1: 1.0, 2: 1.0}
    model.league_avg_home_goals = 1.5
    model.league_avg_away_goals = 1.2
    
    # Get score probabilities
    score_probs = model.predict_score_probabilities(1, 2)
    
    # Remove metadata
    metadata_keys = ['expected_home_goals', 'expected_away_goals', 'rho']
    for key in metadata_keys:
        if key in score_probs:
            score_probs.pop(key)
    
    # Calculate sum
    total = sum(score_probs.values())
    
    print(f"\n📊 Probability Sum: {total:.10f}")
    print(f"   Target: 1.0000000000")
    print(f"   Difference: {abs(total - 1.0):.10f}")
    
    # Check normalization
    is_normalized = abs(total - 1.0) < 0.0001
    
    if is_normalized:
        print(f"\n✅ PASSED: Matrix is properly normalized")
    else:
        print(f"\n❌ FAILED: Matrix sum = {total:.6f}, expected 1.0")
    
    print("\n" + "=" * 70)
    return is_normalized


def test_double_chance_logic():
    """Test Double Chance probabilities are derived from adjusted matrix"""
    print("\n🧪 TEST 2: Double Chance Derivation")
    print("=" * 70)
    
    model = PoissonGoalModel(rho=-0.13)
    model.team_attack = {1: 1.5, 2: 1.2}
    model.team_defense = {1: 1.0, 2: 1.0}
    model.league_avg_home_goals = 1.5
    model.league_avg_away_goals = 1.2
    
    # Get full prediction
    pred = model.predict_match(1, 2)
    
    # Extract probabilities
    prob_home = pred['home_win']
    prob_draw = pred['draw']
    prob_away = pred['away_win']
    
    prob_1x = pred['double_chance']['1X']
    prob_12 = pred['double_chance']['12']
    prob_x2 = pred['double_chance']['X2']
    
    print(f"\n1X2 Probabilities:")
    print(f"   Home: {prob_home:.4f}")
    print(f"   Draw: {prob_draw:.4f}")
    print(f"   Away: {prob_away:.4f}")
    print(f"   Sum:  {prob_home + prob_draw + prob_away:.4f}")
    
    print(f"\nDouble Chance Probabilities:")
    print(f"   1X: {prob_1x:.4f}")
    print(f"   12: {prob_12:.4f}")
    print(f"   X2: {prob_x2:.4f}")
    
    # Verify formulas
    print(f"\n🔍 Verification:")
    
    check_1x = abs(prob_1x - (prob_home + prob_draw)) < 0.0001
    check_12 = abs(prob_12 - (prob_home + prob_away)) < 0.0001
    check_x2 = abs(prob_x2 - (prob_draw + prob_away)) < 0.0001
    
    print(f"   1X = H + D: {prob_1x:.4f} = {prob_home:.4f} + {prob_draw:.4f} ({'✅' if check_1x else '❌'})")
    print(f"   12 = H + A: {prob_12:.4f} = {prob_home:.4f} + {prob_away:.4f} ({'✅' if check_12 else '❌'})")
    print(f"   X2 = D + A: {prob_x2:.4f} = {prob_draw:.4f} + {prob_away:.4f} ({'✅' if check_x2 else '❌'})")
    
    all_passed = check_1x and check_12 and check_x2
    
    if all_passed:
        print(f"\n✅ PASSED: Double Chance correctly derived from adjusted matrix")
    else:
        print(f"\n❌ FAILED: Double Chance formulas incorrect")
    
    print("\n" + "=" * 70)
    return all_passed


def test_combo_json_storage():
    """Test Combo predictions are stored in correct JSON format"""
    print("\n🧪 TEST 3: Combo JSON Storage")
    print("=" * 70)
    
    model = PoissonGoalModel(rho=-0.13)
    model.team_attack = {1: 1.5, 2: 1.2}
    model.team_defense = {1: 1.0, 2: 1.0}
    model.league_avg_home_goals = 1.5
    model.league_avg_away_goals = 1.2
    
    # Get prediction
    pred = model.predict_match(1, 2)
    
    # Check combo_predictions exists
    if 'combo_predictions' not in pred:
        print("\n❌ FAILED: 'combo_predictions' key not found in prediction")
        return False
    
    combo_json = pred['combo_predictions']
    
    print(f"\n📦 Combo Predictions JSON:")
    print(f"   Type: {type(combo_json)}")
    
    # Required combos
    required_combos = [
        '1_over_25',    # 1 + Over 2.5
        'x_under_25',   # X + Under 2.5
        'gg_over_25'    # GG + Over 2.5
    ]
    
    print(f"\n🔍 Required Combos:")
    all_present = True
    
    for combo in required_combos:
        if combo in combo_json:
            value = combo_json[combo]
            is_valid = isinstance(value, (int, float)) and 0 <= value <= 1
            status = '✅' if is_valid else '❌'
            print(f"   {combo}: {value:.4f} {status}")
            all_present = all_present and is_valid
        else:
            print(f"   {combo}: MISSING ❌")
            all_present = False
    
    print(f"\n📋 All Combos in JSON:")
    for key, value in combo_json.items():
        print(f"   {key}: {value:.4f}")
    
    if all_present:
        print(f"\n✅ PASSED: All required combos present with valid probabilities")
    else:
        print(f"\n❌ FAILED: Missing or invalid combo predictions")
    
    print("\n" + "=" * 70)
    return all_present


def test_correlation_impact():
    """Show impact of Dixon-Coles correlation on low scores"""
    print("\n🧪 TEST 4: Dixon-Coles Correlation Impact")
    print("=" * 70)
    
    # Create two models: one with correlation, one without
    model_with_corr = PoissonGoalModel(rho=-0.13)
    model_no_corr = PoissonGoalModel(rho=0.0)  # No correlation
    
    # Setup
    for model in [model_with_corr, model_no_corr]:
        model.team_attack = {1: 1.5, 2: 1.2}
        model.team_defense = {1: 1.0, 2: 1.0}
        model.league_avg_home_goals = 1.5
        model.league_avg_away_goals = 1.2
    
    # Get predictions
    pred_with = model_with_corr.predict_match(1, 2)
    pred_no = model_no_corr.predict_match(1, 2)
    
    print(f"\n📊 Low Score Probabilities Comparison:")
    print(f"   {'Score':<10} {'No Corr (ρ=0)':<20} {'Dixon-Coles (ρ=-0.13)':<20} {'Impact':<15}")
    print("   " + "-" * 65)
    
    # We need to get individual score probabilities
    scores_with = model_with_corr.predict_score_probabilities(1, 2)
    scores_no = model_no_corr.predict_score_probabilities(1, 2)
    
    low_scores = ['0-0', '1-0', '0-1', '1-1']
    
    for score in low_scores:
        prob_no = scores_no.get(score, 0)
        prob_with = scores_with.get(score, 0)
        diff = prob_with - prob_no
        diff_pct = (diff / prob_no * 100) if prob_no > 0 else 0
        
        print(f"   {score:<10} {prob_no:.4f} ({prob_no*100:.2f}%)    "
              f"{prob_with:.4f} ({prob_with*100:.2f}%)    "
              f"{diff:+.4f} ({diff_pct:+.1f}%)")
    
    print("\n💡 Interpretation:")
    print("   Negative ρ increases probabilities of low-scoring matches")
    print("   This corrects the underestimation of defensive games")
    
    print("\n" + "=" * 70)



if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  DIXON-COLES VALIDATION SUITE")
    print("=" * 70)
    
    # Run all tests
    test_1 = test_normalization()
    test_2 = test_double_chance_logic()
    test_3 = test_combo_json_storage()
    test_correlation_impact()
    
    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    print(f"\n  ✅ Normalization (sum = 1.0): {'PASSED' if test_1 else 'FAILED'}")
    print(f"  ✅ Double Chance Derivation:  {'PASSED' if test_2 else 'FAILED'}")
    print(f"  ✅ Combo JSON Storage:        {'PASSED' if test_3 else 'FAILED'}")
    
    all_passed = test_1 and test_2 and test_3
    
    if all_passed:
        print(f"\n  🎉 ALL TESTS PASSED - Dixon-Coles implementation validated!")
    else:
        print(f"\n  ⚠️  SOME TESTS FAILED - Review implementation")
    
    print("\n" + "=" * 70 + "\n")

