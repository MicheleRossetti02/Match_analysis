#!/usr/bin/env python3
"""
Generate prediction for a specific match using active_model_v3_production
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.database import SessionLocal, Match, Prediction
from src.ml.feature_engineer import FeatureEngineer
from src.ml.poisson_model import DixonColesPoissonModel
import joblib
import json
from datetime import datetime

match_id = 326  # Match ID to predict

print(f"\n🎯 Generating Prediction for Match {match_id}")
print("="*70)

# Load database
db = SessionLocal()
match = db.query(Match).filter(Match.id == match_id).first()

if not match:
    print(f"❌ Match {match_id} not found")
    sys.exit(1)

print(f"\n📋 Match Details:")
print(f"   ID: {match.id}")
print(f"   Date: {match.match_date}")
print(f"   Home Team ID: {match.home_team_id}")
print(f"   Away Team ID: {match.away_team_id}")
print(f"   Status: {match.status}")

# Load v3-production model
print(f"\n🤖 Loading active_model_v3_production...")
model = joblib.load('models/active_model_v3_production_1x2.pkl')
scaler = joblib.load('models/active_model_v3_production_scaler.pkl')
encoder = joblib.load('models/active_model_v3_production_encoder.pkl')
print("✅ Model loaded successfully")

# Generate features
print(f"\n⚙️  Generating features...")
engineer = FeatureEngineer(db)
features_dict = engineer.create_match_features(match)

# Prepare features for prediction
feature_cols = list(features_dict.keys())
feature_values = [features_dict[f] for f in feature_cols]

# Handle missing values
import numpy as np
feature_values = [0 if v is None or (isinstance(v, float) and np.isnan(v)) else v for v in feature_values]

# Scale and predict
features_scaled = scaler.transform([feature_values])
prediction = model.predict(features_scaled)[0]
probabilities = model.predict_proba(features_scaled)[0]

result_map = {i: label for i, label in enumerate(encoder.classes_)}
predicted_outcome = result_map[prediction]

prob_dict = {result_map[i]: float(prob) for i, prob in enumerate(probabilities)}

print(f"\n📊 ML Prediction (v3-production - 51.24% accuracy):")
print(f"   Predicted: {predicted_outcome}")
print(f"   Probabilities: H={prob_dict.get('H', 0):.3f} | D={prob_dict.get('D', 0):.3f} | A={prob_dict.get('A', 0):.3f}")

# Dixon-Coles Poisson
print(f"\n🎲 Calculating Dixon-Coles Probabilities...")
dc_model = DixonColesPoissonModel(db)
dc_result = dc_model.predict_match(match.id)

print(f"   Poisson xG: Home={dc_result['poisson_home']:.2f}, Away={dc_result['poisson_away']:.2f}")
print(f"   Dixon-Coles 1X2: H={dc_result['prob_home']:.3f} | D={dc_result['prob_draw']:.3f} | A={dc_result['prob_away']:.3f}")
print(f"   Double Chance: 1X={dc_result['prob_1x']:.3f} | 12={dc_result['prob_12']:.3f} | X2={dc_result['prob_x2']:.3f}")

# Hybrid prediction (70% ML, 30% Dixon-Coles)
hybrid_home = 0.7 * prob_dict.get('H', 0) + 0.3 * dc_result['prob_home']
hybrid_draw = 0.7 * prob_dict.get('D', 0) + 0.3 * dc_result['prob_draw']
hybrid_away = 0.7 * prob_dict.get('A', 0) + 0.3 * dc_result['prob_away']

print(f"\n🔀 Hybrid (70% ML + 30% DC):")
print(f"   H={hybrid_home:.3f} | D={hybrid_draw:.3f} | A={hybrid_away:.3f}")

# Save to database
print(f"\n💾 Saving prediction to database...")
existing = db.query(Prediction).filter(Prediction.match_id == match_id).first()
if existing:
    db.delete(existing)
    db.commit()

new_prediction = Prediction(
    match_id=match_id,
    prob_home=hybrid_home,
    prob_draw=hybrid_draw,
    prob_away=hybrid_away,
    prob_btts_yes=dc_result.get('prob_btts_yes', 0.5),
    prob_btts_no=dc_result.get('prob_btts_no', 0.5),
    prob_over_15=dc_result.get('prob_over_15', 0.5),
    prob_under_15=dc_result.get('prob_under_15', 0.5),
    prob_over_25=dc_result.get('prob_over_25', 0.5),
    prob_under_25=dc_result.get('prob_under_25', 0.5),
    prob_over_35=dc_result.get('prob_over_35', 0.3),
    prob_under_35=dc_result.get('prob_under_35', 0.7),
    prob_1x=dc_result['prob_1x'],
    prob_12=dc_result['prob_12'],
    prob_x2=dc_result['prob_x2'],
    combo_predictions=dc_result['combo_predictions'],
    model_version='active_model_v3_production',
    created_at=datetime.utcnow()
)

db.add(new_prediction)
db.commit()

print(f"✅ Prediction saved (ID: {new_prediction.id})")

# Output JSON for verification
output = {
    "match_id": match_id,
    "ml_prediction": {
        "model": "active_model_v3_production",
        "accuracy": "51.24%",
        "predicted": predicted_outcome,
        "prob_home": prob_dict.get('H', 0),
        "prob_draw": prob_dict.get('D', 0),
        "prob_away": prob_dict.get('A', 0)
    },
    "dixon_coles": {
        "prob_home": dc_result['prob_home'],
        "prob_draw": dc_result['prob_draw'],
        "prob_away": dc_result['prob_away'],
        "prob_1x": dc_result['prob_1x'],
        "prob_12": dc_result['prob_12'],
        "prob_x2": dc_result['prob_x2']
    },
    "hybrid": {
        "prob_home": hybrid_home,
        "prob_draw": hybrid_draw,
        "prob_away": hybrid_away
    },
    "combo_predictions": dc_result['combo_predictions']
}

print(f"\n📋 JSON OUTPUT:")
print("="*70)
print(json.dumps(output, indent=2))
print("="*70)

db.close()
engineer.close()

print(f"\n✅ Prediction generation complete!")
print(f"   Check API: http://localhost:8000/api/predictions/{match_id}")
