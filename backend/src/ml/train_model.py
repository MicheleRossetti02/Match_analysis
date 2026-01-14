"""
ML Model Training for Football Match Prediction
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    roc_auc_score, log_loss
)
import joblib
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.database import SessionLocal, ModelPerformance
from config import settings


class MatchPredictor:
    """ML model for match outcome prediction"""
    
    def __init__(self, model_type='random_forest'):
        """
        Initialize predictor
        
        Args:
            model_type: 'random_forest' or 'xgboost'
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_names = None
        self.version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'xgboost':
            self.model = XGBClassifier(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def prepare_data(self, df: pd.DataFrame):
        """Prepare data for training"""
        # Drop non-feature columns
        feature_cols = [col for col in df.columns if col not in [
            'match_id', 'result', 'match_date', 'league_id', 
            'home_team_id', 'away_team_id'
        ]]
        
        X = df[feature_cols].copy()
        y = df['result'].copy()
        
        # Store feature names
        self.feature_names = feature_cols
        
        # Encode target
        y_encoded = self.label_encoder.fit_transform(y)
        
        return X, y_encoded
    
    def train(self, X_train, y_train, X_val, y_val):
        """Train the model"""
        print(f"\n🤖 Training {self.model_type} model...")
        print(f"   Training samples: {len(X_train)}")
        print(f"   Validation samples: {len(X_val)}")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Train
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate on validation
        val_preds = self.model.predict(X_val_scaled)
        val_proba = self.model.predict_proba(X_val_scaled)
        
        val_acc = accuracy_score(y_val, val_preds)
        
        print(f"\n✅ Training completed!")
        print(f"   Validation Accuracy: {val_acc:.4f}")
        
        return val_acc
    
    def evaluate(self, X_test, y_test):
        """Evaluate model on test set"""
        print(f"\n📊 Evaluating {self.model_type} model on test set...")
        
        X_test_scaled = self.scaler.transform(X_test)
        
        # Predictions
        y_pred = self.model.predict(X_test_scaled)
        y_proba = self.model.predict_proba(X_test_scaled)
        
        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n{'='*60}")
        print(f"📈 Test Set Results - {self.model_type.upper()}")
        print(f"{'='*60}")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"\nClassification Report:")
        print(classification_report(
            y_test, y_pred,
            target_names=self.label_encoder.classes_,
            zero_division=0
        ))
        print(f"\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        print(f"{'='*60}\n")
        
        return {
            'accuracy': accuracy,
            'y_pred': y_pred,
            'y_proba': y_proba
        }
    
    def get_feature_importance(self, top_n=20):
        """Get top N most important features"""
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            indices = np.argsort(importances)[::-1][:top_n]
            
            print(f"\n🔝 Top {top_n} Most Important Features:")
            for i, idx in enumerate(indices, 1):
                print(f"   {i}. {self.feature_names[idx]}: {importances[idx]:.4f}")
            
            return {
                self.feature_names[idx]: float(importances[idx])
                for idx in indices
            }
        return {}
    
    def predict(self, X):
        """Make predictions"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        """Predict probabilities"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def save_model(self, directory='models'):
        """Save model and preprocessing objects"""
        os.makedirs(directory, exist_ok=True)
        
        model_path = os.path.join(directory, f'{self.model_type}_{self.version}.pkl')
        scaler_path = os.path.join(directory, f'{self.model_type}_{self.version}_scaler.pkl')
        encoder_path = os.path.join(directory, f'{self.model_type}_{self.version}_encoder.pkl')
        config_path = os.path.join(directory, f'{self.model_type}_{self.version}_config.json')
        
        # Save objects
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        joblib.dump(self.label_encoder, encoder_path)
        
        # Save config
        config = {
            'model_type': self.model_type,
            'version': self.version,
            'feature_names': self.feature_names,
            'classes': self.label_encoder.classes_.tolist()
        }
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n✅ Model saved to {directory}/")
        return model_path
    
    def load_model(self, model_path):
        """Load saved model"""
        directory = os.path.dirname(model_path)
        base_name = os.path.basename(model_path).replace('.pkl', '')
        
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(os.path.join(directory, f'{base_name}_scaler.pkl'))
        self.label_encoder = joblib.load(os.path.join(directory, f'{base_name}_encoder.pkl'))
        
        with open(os.path.join(directory, f'{base_name}_config.json'), 'r') as f:
            config = json.load(f)
            self.feature_names = config['feature_names']
            self.model_type = config['model_type']
            self.version = config['version']
        
        print(f"✅ Model loaded from {model_path}")


def train_and_evaluate_models(dataset_path='ml_dataset.csv'):
    """Train and evaluate both Random Forest and XGBoost models"""
    print("\n🚀 Starting model training pipeline...\n")
    
    # Load dataset
    df = pd.read_csv(dataset_path)
    print(f"Loaded dataset: {df.shape}")
    
    # Remove rows with missing target
    df = df[df['result'].notna()]
    print(f"After removing missing targets: {df.shape}")
    
    # Prepare data
    predictor_temp = MatchPredictor()
    X, y = predictor_temp.prepare_data(df)
    
    # Split: 70% train, 15% val, 15% test
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.176, random_state=42, stratify=y_train_val  # 0.15/0.85
    )
    
    print(f"\nDataset splits:")
    print(f"  Train: {len(X_train)} ({len(X_train)/len(X)*100:.1f}%)")
    print(f"  Val: {len(X_val)} ({len(X_val)/len(X)*100:.1f}%)")
    print(f"  Test: {len(X_test)} ({len(X_test)/len(X)*100:.1f}%)")
    
    results = {}
    
    # Train Random Forest
    print("\n" + "="*60)
    print("RANDOM FOREST")
    print("="*60)
    rf_predictor = MatchPredictor('random_forest')
    rf_predictor.feature_names = predictor_temp.feature_names
    rf_predictor.label_encoder = predictor_temp.label_encoder
    
    rf_val_acc = rf_predictor.train(X_train, y_train, X_val, y_val)
    rf_results = rf_predictor.evaluate(X_test, y_test)
    rf_importance = rf_predictor.get_feature_importance(15)
    rf_path = rf_predictor.save_model()
    
    results['random_forest'] = {
        'accuracy': rf_results['accuracy'],
        'val_accuracy': rf_val_acc,
        'model_path': rf_path,
        'feature_importance': rf_importance
    }
    
    # Train XGBoost
    print("\n" + "="*60)
    print("XGBOOST")
    print("="*60)
    xgb_predictor = MatchPredictor('xgboost')
    xgb_predictor.feature_names = predictor_temp.feature_names
    xgb_predictor.label_encoder = predictor_temp.label_encoder
    
    xgb_val_acc = xgb_predictor.train(X_train, y_train, X_val, y_val)
    xgb_results = xgb_predictor.evaluate(X_test, y_test)
    xgb_importance = xgb_predictor.get_feature_importance(15)
    xgb_path = xgb_predictor.save_model()
    
    results['xgboost'] = {
        'accuracy': xgb_results['accuracy'],
        'val_accuracy': xgb_val_acc,
        'model_path': xgb_path,
        'feature_importance': xgb_importance
    }
    
    # Compare results
    print("\n" + "="*60)
    print("📊 MODEL COMPARISON")
    print("="*60)
    print(f"{'Model':<20} {'Test Accuracy':<15} {'Val Accuracy':<15}")
    print("-"*60)
    for model_name in results:
        print(f"{model_name:<20} {results[model_name]['accuracy']:<15.4f} {results[model_name]['val_accuracy']:<15.4f}")
    print("="*60)
    
    # Determine best model
    best_model = max(results.items(), key=lambda x: x[1]['accuracy'])
    print(f"\n🏆 Best Model: {best_model[0].upper()} (Accuracy: {best_model[1]['accuracy']:.4f})")
    
    return results


if __name__ == "__main__":
    results = train_and_evaluate_models()
