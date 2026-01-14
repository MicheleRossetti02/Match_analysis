"""
Generate Predictions using Extended ML Models
Creates predictions with BTTS, Over/Under, Multi-goal for upcoming matches
"""
import os
import sys
import json
import joblib
import numpy as np
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.database import SessionLocal, Match, Prediction, Team
from src.ml.feature_engineer import FeatureEngineer


class ExtendedPredictionGenerator:
    """Generate predictions using extended ML models"""
    
    def __init__(self, models_dir='models'):
        self.models_dir = models_dir
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.config = None
        
    def load_models(self, version=None):
        """Load extended models from disk"""
        # Find latest extended model
        if version is None:
            config_files = [f for f in os.listdir(self.models_dir) 
                          if f.startswith('extended_') and f.endswith('_config.json')]
            if not config_files:
                raise ValueError("No extended models found")
            version = sorted(config_files)[-1].replace('_config.json', '')
        
        base_name = version if version.startswith('extended_') else f'extended_xgboost_{version}'
        config_path = os.path.join(self.models_dir, f'{base_name}_config.json')
        
        if not os.path.exists(config_path):
            # Try finding by pattern
            for f in os.listdir(self.models_dir):
                if f.endswith('_config.json') and 'extended' in f:
                    config_path = os.path.join(self.models_dir, f)
                    base_name = f.replace('_config.json', '')
                    break
        
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        print(f"Loading extended models v{self.config['version']}...")
        
        # Load each target model
        for target in self.config['targets']:
            model_path = os.path.join(self.models_dir, f'{base_name}_{target}.pkl')
            scaler_path = os.path.join(self.models_dir, f'{base_name}_{target}_scaler.pkl')
            encoder_path = os.path.join(self.models_dir, f'{base_name}_{target}_encoder.pkl')
            
            if os.path.exists(model_path):
                self.models[target] = joblib.load(model_path)
                self.scalers[target] = joblib.load(scaler_path)
                if os.path.exists(encoder_path):
                    self.encoders[target] = joblib.load(encoder_path)
                print(f"  ✓ Loaded {target} model")
        
        print(f"✅ Loaded {len(self.models)} models")
        return self
    
    def predict(self, features: dict) -> dict:
        """Make predictions for all model types"""
        feature_values = [features.get(f, 0) for f in self.config['feature_names']]
        X = np.array(feature_values).reshape(1, -1)
        
        predictions = {}
        
        for target, model in self.models.items():
            X_scaled = self.scalers[target].transform(X)
            pred = model.predict(X_scaled)[0]
            proba = model.predict_proba(X_scaled)[0]
            
            # Decode if needed
            if target in self.encoders and self.encoders[target] is not None:
                decoded = self.encoders[target].inverse_transform([pred])[0]
            else:
                decoded = pred
            
            predictions[target] = {
                'prediction': decoded,
                'confidence': float(max(proba)),
                'probabilities': proba.tolist()
            }
        
        return predictions
    
    def generate_predictions_for_match(self, match: Match, db) -> Prediction:
        """Generate prediction for a single match"""
        engineer = FeatureEngineer(db)
        
        # Get features
        features = engineer.create_match_features(match)
        
        # Get predictions from models
        preds = self.predict(features)
        
        # Get team names for winner display
        home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
        away_team = db.query(Team).filter(Team.id == match.away_team_id).first()
        
        # Create prediction object
        result_pred = preds.get('1x2', {})
        btts_pred = preds.get('btts', {})
        over15_pred = preds.get('over_15', {})
        over25_pred = preds.get('over_25', {})
        over35_pred = preds.get('over_35', {})
        multi_pred = preds.get('multi_goal', {})
        
        # Get 1X2 probabilities
        if '1x2' in preds and 'probabilities' in preds['1x2']:
            # Classes should be ['A', 'D', 'H']
            probas = preds['1x2']['probabilities']
            if len(probas) == 3:
                prob_a, prob_d, prob_h = probas[0], probas[1], probas[2]
            else:
                prob_h, prob_d, prob_a = 0.33, 0.33, 0.34
        else:
            prob_h, prob_d, prob_a = 0.33, 0.33, 0.34
        
        # Generate exact score based on predicted result and goals
        predicted_result = str(result_pred.get('prediction', 'H'))
        if predicted_result == 'H':
            scores = ['2-1', '2-0', '1-0', '3-1', '3-0']
        elif predicted_result == 'A':
            scores = ['1-2', '0-2', '0-1', '1-3', '0-3']
        else:
            scores = ['1-1', '2-2', '0-0']
        
        import random
        exact_score = random.choice(scores)
        
        prediction = Prediction(
            match_id=match.id,
            # 1X2
            predicted_result=predicted_result,
            confidence=result_pred.get('confidence', 0.33),
            prob_home_win=prob_h,
            prob_draw=prob_d,
            prob_away_win=prob_a,
            # BTTS
            btts_prediction=bool(btts_pred.get('prediction', 0)),
            btts_confidence=btts_pred.get('confidence', 0.5),
            # Over/Under
            over_15_prediction=bool(over15_pred.get('prediction', 1)),
            over_25_prediction=bool(over25_pred.get('prediction', 0)),
            over_25_confidence=over25_pred.get('confidence', 0.5),
            over_35_prediction=bool(over35_pred.get('prediction', 0)),
            # Multi-goal
            multi_goal_prediction=str(multi_pred.get('prediction', '2-3')),
            multi_goal_confidence=multi_pred.get('confidence', 0.3),
            # Exact score
            exact_score_prediction=exact_score,
            exact_score_confidence=0.08,  # Low confidence for exact scores
            # Model info
            model_version=self.config['version'],
            model_type=self.config['model_type'],
            created_at=datetime.utcnow()
        )
        
        return prediction


def generate_all_predictions(days_ahead=14):
    """Generate predictions for all upcoming matches"""
    print("\n🔮 Generating Extended Predictions...\n")
    
    db = SessionLocal()
    generator = ExtendedPredictionGenerator()
    generator.load_models()
    
    # Get upcoming matches
    today = datetime.utcnow()
    future = today + timedelta(days=days_ahead)
    
    upcoming = db.query(Match).filter(
        Match.match_date >= today,
        Match.match_date <= future,
        Match.status == 'NS'
    ).all()
    
    print(f"Found {len(upcoming)} upcoming matches")
    
    # Clear existing predictions for these matches
    for match in upcoming:
        db.query(Prediction).filter(Prediction.match_id == match.id).delete()
    db.commit()
    
    # Generate new predictions
    created = 0
    for i, match in enumerate(upcoming):
        if i % 10 == 0:
            print(f"  Processing {i}/{len(upcoming)}...")
        
        try:
            pred = generator.generate_predictions_for_match(match, db)
            db.add(pred)
            created += 1
        except Exception as e:
            print(f"  Error on match {match.id}: {e}")
    
    db.commit()
    db.close()
    
    print(f"\n✅ Generated {created} predictions with extended data!")
    return created


if __name__ == "__main__":
    generate_all_predictions()
