"""
Simple feature demonstration - shows new Sprint 1 features
Run this script to see the new features in action (without database dependency)
"""

def demonstrate_recency_bias():
    """Show how recency bias weights work"""
    print("\n📊 RECENCY BIAS DEMONSTRATION")
    print("=" * 50)
    print("\nScenario: Team with 5 recent matches")
    print("Results (newest to oldest): Win, Win, Draw, Loss, Win")
    print("Points: 3, 3, 1, 0, 3")
    
    points = [3, 3, 1, 0, 3]
    decay_factor = 0.85
    
    # Standard average
    standard_avg = sum(points) / len(points)
    print(f"\n📌 Standard average: {standard_avg:.2f} points/game")
    
    # Weighted average with recency bias
    weighted_sum = 0.0
    weight_total = 0.0
    
    print("\n🔄 Recency-weighted calculation:")
    for i, pts in enumerate(points):
        weight = decay_factor ** i
        weighted_sum += pts * weight
        weight_total += weight
        print(f"   Match {i}: {pts} pts × {weight:.3f} = {pts * weight:.3f}")
    
    weighted_avg = weighted_sum / weight_total
    
    print(f"\n   Total: {weighted_sum:.2f} / {weight_total:.2f}")
    print(f"📌 Weighted average: {weighted_avg:.2f} points/game")
    print(f"\n✅ Difference: {weighted_avg - standard_avg:+.2f} (recent form weighted more!)")


def demonstrate_momentum():
    """Show how momentum is calculated"""
    print("\n\n📈 MOMENTUM INDICATOR DEMONSTRATION")
    print("=" * 50)
    print("\nScenario: Last 3 matches goal differences")
    print("Results (newest to oldest): +2, +1, -1")
    
    goal_diffs = [2, 1, -1]
    decay_factor = 0.85
    
    weighted_sum = 0.0
    weight_total = 0.0
    
    print("\n🔄 Momentum calculation:")
    for i, gd in enumerate(goal_diffs):
        weight = decay_factor ** i
        weighted_sum += gd * weight
        weight_total += weight
        print(f"   Match {i}: {gd:+d} GD × {weight:.3f} = {gd * weight:+.3f}")

    
    momentum = weighted_sum / weight_total
    
    print(f"\n   Total: {weighted_sum:.2f} / {weight_total:.2f}")
    print(f"📌 Momentum score: {momentum:+.2f}")
    
    if momentum > 0:
        print(f"✅ Positive momentum: Team improving!")
    else:
        print(f"⚠️  Negative momentum: Team declining")


def demonstrate_xg_features():
    """Show xG feature concepts"""
    print("\n\n⚽ EXPECTED GOALS (xG) DEMONSTRATION")
    print("=" * 50)
    print("\nScenario: Strong home team vs. weak away team")
    
    # Simulated attack/defense ratings
    home_attack = 1.8  # 80% above league avg
    away_defense = 1.2  # 20% above (worse defense)
    league_avg_home = 1.5
    home_advantage = 0.25
    
    xg_home = home_attack * away_defense * league_avg_home + home_advantage
    
    print(f"\n   Home attack rating: {home_attack:.2f}")
    print(f"   Away defense rating: {away_defense:.2f}")
    print(f"   League avg home goals: {league_avg_home:.2f}")
    print(f"   Home advantage: +{home_advantage:.2f}")
    
    print(f"\n📌 Expected home goals (xG): {xg_home:.2f}")
    print(f"   Calculation: {home_attack} × {away_defense} × {league_avg_home} + {home_advantage}")
    
    print("\n✅ xG Features added to model:")
    print(f"   • poisson_xg_home: {xg_home:.2f}")
    print(f"   • poisson_xg_away: 1.05")
    print(f"   • poisson_xg_diff: {xg_home - 1.05:+.2f}")
    print(f"   • poisson_xg_total: {xg_home + 1.05:.2f}")


def show_feature_summary():
    """Show summary of new features"""
    print("\n\n📋 SPRINT 1 NEW FEATURES SUMMARY")
    print("=" * 50)
    
    features = [
        ("Recency Bias", "home_form_all_weighted_points, away_form_all_weighted_points"),
        ("Expected Goals", "poisson_xg_home, poisson_xg_away, poisson_xg_diff, poisson_xg_total"),
        ("Momentum", "home_momentum, away_momentum, momentum_diff"),
    ]
    
    total = 0
    for category, feats in features:
        count = len(feats.split(", "))
        total += count
        print(f"\n{category}:")
        for feat in feats.split(", "):
            print(f"   • {feat}")
        print(f"   ({count} features)")
    
    print(f"\n✅ Total new features: {total}")
    print("\n🎯 Expected accuracy improvement: +3-6%")


if __name__ == "__main__":
    print("\n🚀 Sprint 1: Advanced Feature Engineering Demo")
    print("=" * 50)
    
    demonstrate_recency_bias()
    demonstrate_momentum()
    demonstrate_xg_features()
    show_feature_summary()
    
    print("\n" + "=" * 50)
    print("✅ Demo complete!\n")
