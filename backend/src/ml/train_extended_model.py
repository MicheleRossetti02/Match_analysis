"""
Extended ML Model Training for Multiple Prediction Types
Trains models for: 1X2, BTTS, Over/Under, Multi-goal
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
import joblib
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.database import SessionLocal, Match, ModelPerformance
from src.ml.feature_engineer import FeatureEngineer
from config import settings


class ExtendedMatchPredictor:
    """ML models for multiple prediction types"""
    
    def __init__(self, model_type='xgboost'):
        self.model_type = model_type
        self.version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Models for each target
        self.models = {
            '1x2': None,      # Home/Draw/Away
            'btts': None,     # Both Teams To Score
            'over_25': None,  # Over 2.5 goals
            'over_15': None,  # Over 1.5 goals
            'over_35': None,  # Over 3.5 goals
            'multi_goal': None  # Goal ranges
        }
        
        # Scalers and encoders for each model
        self.scalers = {key: StandardScaler() for key in self.models}
        self.encoders = {key: LabelEncoder() for key in self.models}
        
        self.feature_names = None
        
    def _create_model(self, use_ensemble=True):
        """Create a new model instance - ensemble or single"""
        if use_ensemble and self.model_type == 'ensemble':
            from sklearn.ensemble import VotingClassifier
            
            xgb = XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                use_label_encoder=False,
                eval_metric='logloss'
            )
            
            rf = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1
            )
            
            gb = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            
            return VotingClassifier(
                estimators=[('xgb', xgb), ('rf', rf), ('gb', gb)],
                voting='soft',  # Use probabilities
                n_jobs=-1
            )
        elif self.model_type == 'xgboost':
            return XGBClassifier(
                n_estimators=150,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                use_label_encoder=False,
                eval_metric='logloss'
            )
        else:
            return RandomForestClassifier(
                n_estimators=150,
                max_depth=12,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1
            )
    
    def prepare_targets(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create target variables for all prediction types from raw match data
        """
        # 1X2 result
        df['target_1x2'] = df['result']
        
        # BTTS (Both Teams To Score)
        # Calculate from home/away goals if available
        if 'home_goals' in df.columns and 'away_goals' in df.columns:
            df['target_btts'] = ((df['home_goals'] > 0) & (df['away_goals'] > 0)).astype(int)
            
            # Total goals for over/under
            df['total_goals'] = df['home_goals'] + df['away_goals']
            df['target_over_15'] = (df['total_goals'] > 1.5).astype(int)
            df['target_over_25'] = (df['total_goals'] > 2.5).astype(int)
            df['target_over_35'] = (df['total_goals'] > 3.5).astype(int)
            
            # Multi-goal ranges
            def get_multi_goal_range(goals):
                if goals <= 1:
                    return '0-1'
                elif goals <= 3:
                    return '2-3'
                elif goals <= 5:
                    return '4-5'
                else:
                    return '6+'
            df['target_multi_goal'] = df['total_goals'].apply(get_multi_goal_range)
        
        return df
    
    def train_all_models(self, df: pd.DataFrame):
        """
        Train models for all prediction types
        
        Returns:
            Dict with results for each model
        """
        results = {}
        
        # Define feature columns (exclude non-feature columns)
        exclude_cols = [
            'match_id', 'result', 'match_date', 'league_id', 
            'home_team_id', 'away_team_id', 'home_goals', 'away_goals',
            'target_1x2', 'target_btts', 'target_over_15', 'target_over_25',
            'target_over_35', 'target_multi_goal', 'total_goals'
        ]
        
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        self.feature_names = feature_cols
        
        X = df[feature_cols].fillna(0)
        
        # Train each model
        print("\n" + "="*60)
        print("🚀 TRAINING EXTENDED PREDICTION MODELS")
        print("="*60)
        
        # 1. Train 1X2 Model
        print("\n📊 Training 1X2 (Winner) Model...")
        y_1x2 = df['target_1x2'].dropna()
        X_1x2 = X.loc[y_1x2.index]
        results['1x2'] = self._train_single_model('1x2', X_1x2, y_1x2)
        
        # 2. Train BTTS Model
        if 'target_btts' in df.columns:
            print("\n⚽ Training BTTS Model...")
            y_btts = df['target_btts'].dropna()
            X_btts = X.loc[y_btts.index]
            results['btts'] = self._train_single_model('btts', X_btts, y_btts)
        
        # 3. Train Over 1.5 Model
        if 'target_over_15' in df.columns:
            print("\n📈 Training Over 1.5 Model...")
            y_o15 = df['target_over_15'].dropna()
            X_o15 = X.loc[y_o15.index]
            results['over_15'] = self._train_single_model('over_15', X_o15, y_o15)
        
        # 4. Train Over 2.5 Model  
        if 'target_over_25' in df.columns:
            print("\n📈 Training Over 2.5 Model...")
            y_o25 = df['target_over_25'].dropna()
            X_o25 = X.loc[y_o25.index]
            results['over_25'] = self._train_single_model('over_25', X_o25, y_o25)
        
        # 5. Train Over 3.5 Model
        if 'target_over_35' in df.columns:
            print("\n📈 Training Over 3.5 Model...")
            y_o35 = df['target_over_35'].dropna()
            X_o35 = X.loc[y_o35.index]
            results['over_35'] = self._train_single_model('over_35', X_o35, y_o35)
        
        # 6. Train Multi-goal Model
        if 'target_multi_goal' in df.columns:
            print("\n🎯 Training Multi-goal Model...")
            y_mg = df['target_multi_goal'].dropna()
            X_mg = X.loc[y_mg.index]
            results['multi_goal'] = self._train_single_model('multi_goal', X_mg, y_mg)
        
        return results
    
    def _train_single_model(self, target_name: str, X: pd.DataFrame, y: pd.Series):
        """Train a single model"""
        print(f"   Samples: {len(X)}")
        
        # Encode target if string
        if y.dtype == 'object':
            y_encoded = self.encoders[target_name].fit_transform(y)
        else:
            y_encoded = y.values
            self.encoders[target_name] = None
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Scale features
        X_train_scaled = self.scalers[target_name].fit_transform(X_train)
        X_test_scaled = self.scalers[target_name].transform(X_test)
        
        # Train model
        self.models[target_name] = self._create_model()
        self.models[target_name].fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.models[target_name].predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        print(f"   ✅ Accuracy: {accuracy:.4f} | F1: {f1:.4f}")
        
        return {
            'accuracy': accuracy,
            'f1_score': f1,
            'samples': len(X)
        }
    
    def predict(self, features: dict) -> dict:
        """
        Make predictions for all types
        
        Args:
            features: Dict of feature values
            
        Returns:
            Dict with all predictions
        """
        # Prepare feature vector
        feature_values = [features.get(f, 0) for f in self.feature_names]
        X = np.array(feature_values).reshape(1, -1)
        
        predictions = {}
        
        for target_name, model in self.models.items():
            if model is None:
                continue
            
            X_scaled = self.scalers[target_name].transform(X)
            
            # Get prediction and probability
            pred = model.predict(X_scaled)[0]
            proba = model.predict_proba(X_scaled)[0]
            
            # Decode if needed
            if self.encoders[target_name] is not None:
                pred = self.encoders[target_name].inverse_transform([pred])[0]
            
            predictions[target_name] = {
                'prediction': pred,
                'confidence': float(max(proba)),
                'probabilities': proba.tolist()
            }
        
        return predictions
    
    def save_models(self, directory='models'):
        """Save all models and preprocessing objects"""
        os.makedirs(directory, exist_ok=True)
        
        base_name = f'extended_{self.model_type}_{self.version}'
        
        # Save each model
        for target_name, model in self.models.items():
            if model is None:
                continue
            
            model_path = os.path.join(directory, f'{base_name}_{target_name}.pkl')
            joblib.dump(model, model_path)
            
            scaler_path = os.path.join(directory, f'{base_name}_{target_name}_scaler.pkl')
            joblib.dump(self.scalers[target_name], scaler_path)
            
            if self.encoders[target_name] is not None:
                encoder_path = os.path.join(directory, f'{base_name}_{target_name}_encoder.pkl')
                joblib.dump(self.encoders[target_name], encoder_path)
        
        # Save config
        config = {
            'model_type': self.model_type,
            'version': self.version,
            'feature_names': self.feature_names,
            'targets': list(self.models.keys())
        }
        config_path = os.path.join(directory, f'{base_name}_config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n✅ Models saved to {directory}/{base_name}_*.pkl")
        return base_name


def create_extended_dataset():
    """
    Create extended training dataset with all target variables
    """
    print("\n📊 Creating Extended Training Dataset...")
    
    db = SessionLocal()
    
    # Get finished matches with scores
    matches = db.query(Match).filter(
        Match.status == 'FT',
        Match.home_goals.isnot(None),
        Match.away_goals.isnot(None)
    ).order_by(Match.match_date).all()
    
    print(f"   Found {len(matches)} finished matches with scores")
    
    # Create features using FeatureEngineer
    engineer = FeatureEngineer(db)
    
    data = []
    for i, match in enumerate(matches):
        if i % 50 == 0:
            print(f"   Processing match {i}/{len(matches)}...")
        
        try:
            features = engineer.create_match_features(match)
            # Add actual goals for target creation
            features['home_goals'] = match.home_goals
            features['away_goals'] = match.away_goals
            features['match_id'] = match.id
            data.append(features)
        except Exception as e:
            print(f"   Error on match {match.id}: {e}")
    
    df = pd.DataFrame(data)
    engineer.close()
    
    print(f"\n✅ Created dataset with {len(df)} matches and {len(df.columns)} columns")
    
    return df


def train_extended_models(df=None, model_type='xgboost'):
    """
    Main function to train all extended models
    """
    # Create or load dataset
    if df is None:
        df = create_extended_dataset()
    
    # Create predictor and prepare targets
    predictor = ExtendedMatchPredictor(model_type=model_type)
    df = predictor.prepare_targets(df)
    
    # Train all models
    results = predictor.train_all_models(df)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TRAINING RESULTS SUMMARY")
    print("="*60)
    print(f"{'Model':<15} {'Accuracy':<12} {'F1 Score':<12} {'Samples':<10}")
    print("-"*60)
    for name, res in results.items():
        print(f"{name:<15} {res['accuracy']:<12.4f} {res['f1_score']:<12.4f} {res['samples']:<10}")
    print("="*60)
    
    # Save models
    predictor.save_models()
    
    # Register in database
    db = SessionLocal()
    model_perf = ModelPerformance(
        model_version=predictor.version,
        model_type=f'extended_{model_type}',
        accuracy=results['1x2']['accuracy'],
        f1_score=results['1x2']['f1_score'],
        trained_at=datetime.utcnow(),
        is_active=True,
        training_samples=results['1x2']['samples']
    )
    
    # Deactivate old models
    db.query(ModelPerformance).update({'is_active': False})
    db.add(model_perf)
    db.commit()
    db.close()
    
    print(f"\n🏆 Extended model v{predictor.version} registered as active!")
    
    return predictor, results


if __name__ == "__main__":
    print("\n🚀 Starting Extended Model Training Pipeline...\n")
    
    predictor, results = train_extended_models(model_type='xgboost')
    
    print("\n✅ Training complete!")
