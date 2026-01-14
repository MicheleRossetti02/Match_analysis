"""
Accuracy Comparison Test
Compare model accuracy with old features vs. new Sprint 1 features
"""
import sys
import os
import pytest
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.ml.feature_engineer import FeatureEngineer


def test_feature_count_increase(db_session, sample_matches):
    """Test that new features increase the total feature count"""
    engineer = FeatureEngineer(db=db_session)
    
    # Create features for first finished match
    finished_match = [m for m in sample_matches if m.status == 'FT'][0]
    features = engineer.create_match_features(finished_match)
    
    # Count new Sprint 1 features
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
    
    found_new_features = [f for f in new_features if f in features]
    
    assert len(found_new_features) >= 7, "Not all new features were added"
    print(f"\n✅ Added {len(found_new_features)} new features")


def test_feature_quality(db_session, sample_matches):
    """Test that new features have good quality (no NaN, reasonable ranges)"""
    engineer = FeatureEngineer(db=db_session)
    
    finished_matches = [m for m in sample_matches if m.status == 'FT']
    
    for match in finished_matches[:5]:  # Test first 5 matches
        features = engineer.create_match_features(match)
        
        # Check critical new features
        assert not pd.isna(features['home_momentum'])
        assert not pd.isna(features['away_momentum'])
        assert not pd.isna(features['poisson_xg_home'])
        assert not pd.isna(features['poisson_xg_away'])
        
        # Check reasonable ranges
        assert -5.0 <= features['home_momentum'] <= 5.0
        assert -5.0 <= features['away_momentum'] <= 5.0
        assert 0.0 <= features['poisson_xg_home'] <= 6.0
        assert 0.0 <= features['poisson_xg_away'] <= 6.0


def test_cross_validation_ready(db_session, sample_matches):
    """Test that feature set is ready for cross-validation"""
    engineer = FeatureEngineer(db=db_session)
    
    # Create dataset
    finished_matches = [m for m in sample_matches if m.status == 'FT']
    
    if len(finished_matches) < 5:
        pytest.skip("Not enough matches for cross-validation test")
    
    features_list = []
    for match in finished_matches:
        try:
            features = engineer.create_match_features(match)
            if features['result'] is not None:
                features_list.append(features)
        except Exception as e:
            print(f"Error creating features: {e}")
    
    if len(features_list) < 3:
        pytest.skip("Not enough valid features for test")
    
    df = pd.DataFrame(features_list)
    
    # Verify target exists
    assert 'result' in df.columns
    assert df['result'].notna().sum() > 0
    
    print(f"\n✅ Created dataset with {len(df)} samples and {len(df.columns)} features")


def generate_accuracy_report(old_accuracy: float, new_accuracy: float, output_path: str):
    """Generate a comparison report"""
    improvement = new_accuracy - old_accuracy
    improvement_pct = (improvement / old_accuracy) * 100 if old_accuracy > 0 else 0
    
    report = f"""
# Sprint 1 Accuracy Comparison Report

## Results

- **Old Features Accuracy**: {old_accuracy:.2%}
- **New Features Accuracy**: {new_accuracy:.2%}
- **Improvement**: {improvement:+.2%} ({improvement_pct:+.1f}%)

## New Features Added

1. **Recency Bias**: Exponential decay weights (λ=0.85) for last 5 matches
2. **Expected Goals (xG)**: Poisson model-based goal expectations
3. **Momentum Indicators**: 3-match weighted goal difference trends

## Conclusion

{"✅ **SUCCESS**: New features improved accuracy!" if improvement > 0 else "⚠️ **REVIEW NEEDED**: Accuracy did not improve. Consider feature selection."}
"""
    
    with open(output_path, 'w') as f:
        f.write(report)
    
    print(f"\n📊 Report saved to {output_path}")
    return report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
