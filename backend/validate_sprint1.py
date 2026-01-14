"""
Quick validation script for Sprint 1 feature enhancements
Tests that new features are generated correctly without full pytest
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.ml.feature_engineer import FeatureEngineer
from datetime import datetime

print("\n🔧 Sprint 1 Feature Validation\n")
print("=" * 50)

# Initialize feature engineer
try:
    engineer = FeatureEngineer()
    print("✅ FeatureEngineer initialized")
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    sys.exit(1)

# Test recency bias
print("\n1. Testing Recency Bias...")
try:
    form_weighted = engineer.calculate_team_form(
        team_id=1,
        before_date=datetime(2025, 1, 15),
        last_n=5,
        use_recency_weights=True
    )
    
    if 'weighted_points' in form_weighted:
        print(f"   ✅ Recency bias working: weighted_points = {form_weighted['weighted_points']:.2f}")
    else:
        print("   ❌ Recency bias: weighted_points not found")
except Exception as e:
    print(f"   ❌ Recency bias error: {e}")

# Test momentum calculation
print("\n2. Testing Momentum Indicator...")
try:
    momentum = engineer._calculate_momentum(
        team_id=1,
        before_date=datetime(2025, 1, 15),
        last_n=3
    )
    print(f"   ✅ Momentum calculation working: momentum = {momentum:.2f}")
except Exception as e:
    print(f"   ❌ Momentum error: {e}")

# Test full feature generation
print("\n3. Testing Full Feature Set...")
try:
    from src.models.database import Match
    
    # Get a recent match
    match = engineer.db.query(Match).filter(
        Match.status == 'NS'
    ).first()
    
    if not match:
        print("   ⚠️  No upcoming matches found, using finished match")
        match = engineer.db.query(Match).filter(
            Match.status == 'FT'
        ).first()
    
    if match:
        features = engineer.create_match_features(match)
        
        # Check for new Sprint 1 features
        new_features = [
            'home_form_all_weighted_points',
            'away_form_all_weighted_points',
            'poisson_xg_home',
            'poisson_xg_away',
            'poisson_xg_diff',
            'poisson_xg_total',
            'home_momentum',
            'away_momentum',
            'momentum_diff',
        ]
        
        found = []
        missing = []
        
        for feature in new_features:
            if feature in features:
                found.append(feature)
            else:
                missing.append(feature)
        
        print(f"   ✅ Found {len(found)}/{len(new_features)} new features")
        
        if found:
            print("\n   New Features:")
            for feat in found[:5]:  # Show first 5
                print(f"      • {feat}: {features[feat]}")
        
        if missing:
            print(f"\n   ⚠️  Missing features: {', '.join(missing)}")
        
        print(f"\n   📊 Total features: {len(features)}")
        
    else:
        print("   ❌ No matches found in database")
        
except Exception as e:
    print(f"   ❌ Feature generation error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("✅ Sprint 1 Validation Complete!\n")

engineer.close()
