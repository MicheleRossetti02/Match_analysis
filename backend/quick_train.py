"""
Quick Training Script - Uses existing CSV dataset
Bypasses slow feature generation
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
import joblib
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.models.database import SessionLocal, ModelPerformance

print("\n" + "="*60)
print("🚀 QUICK ML TRAINING - Using ml_dataset.csv")
print("="*60 + "\n")

# Load dataset
print("📂 Loading ml_dataset.csv...")
df = pd.read_csv('ml_dataset.csv')
print(f"✅ Loaded {len(df)} matches with {len(df.columns)} columns")

# Prepare data
print("\n📊 Preparing data...")
exclude_cols = ['match_id', 'result', 'match_date', 'league_id', 
                'home_team_id', 'away_team_id']
feature_cols = [col for col in df.columns if col not in exclude_cols]
print(f"   Features: {len(feature_cols)}")

X = df[feature_cols].fillna(0)
y = df['result']

# Encode target
le = LabelEncoder()
y_encoded = le.fit_transform(y)

print(f"\n🎯 Target distribution:")
for cls, count in zip(*np.unique(y, return_counts=True)):
    print(f"   {cls}: {count} ({count/len(y)*100:.1f}%)")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
print(f"\n✂️  Split: {len(X_train)} train, {len(X_test)} test")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
print("\n" + "="*60)
print("🤖 Training XGBoost Classifier...")
print("="*60)

model = XGBClassifier(
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

print("\n⏳ Training in progress...")
model.fit(X_train_scaled, y_train)
print("✅ Training complete!")

# Evaluate
print("\n" + "="*60)
print("📊 EVALUATION RESULTS")
print("="*60)

y_pred = model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='weighted')

print(f"\n🎯 Test Set Performance:")
print(f"   Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"   F1 Score: {f1:.4f}")

print(f"\n📋 Classification Report:")
print(classification_report(y_test, y_pred, target_names=le.classes_))

# Feature importance
print("\n" + "="*60)
print("🔍 TOP 10 FEATURE IMPORTANCE")
print("="*60)

feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n")
for idx, row in feature_importance.head(10).iterrows():
    print(f"   {row['feature']:40s} {row['importance']:.4f}")

# Save model
print("\n" + "="*60)
print("💾 SAVING MODEL")
print("="*60)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
base_name = f'quick_xgboost_{timestamp}'

os.makedirs('models', exist_ok=True)

model_path = f'models/{base_name}_1x2.pkl'
scaler_path = f'models/{base_name}_scaler.pkl'
encoder_path = f'models/{base_name}_encoder.pkl'
config_path = f'models/{base_name}_config.json'

joblib.dump(model, model_path)
joblib.dump(scaler, scaler_path)
joblib.dump(le, encoder_path)

config = {
    'version': timestamp,
    'model_type': 'xgboost',
    'features': feature_cols,
    'accuracy': float(accuracy),
    'f1_score': float(f1),
    'samples_train': len(X_train),
    'samples_test': len(X_test),
    'top_features': feature_importance.head(5).to_dict('records')
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f"\n✅ Model saved:")
print(f"   {model_path}")
print(f"   {scaler_path}")
print(f"   {encoder_path}")
print(f"   {config_path}")

# Register in database
print("\n📝 Registering in database...")
db = SessionLocal()
try:
    # Deactivate old models
    db.query(ModelPerformance).update({'is_active': False})
    
    # Add new model
    model_perf = ModelPerformance(
        model_version=timestamp,
        model_type='quick_xgboost',
        accuracy=accuracy,
        f1_score=f1,
        trained_at=datetime.utcnow(),
        is_active=True,
        training_samples=len(X_train)
    )
    db.add(model_perf)
    db.commit()
    print(f"✅ Registered as active model v{timestamp}")
except Exception as e:
    print(f"⚠️  Database registration failed: {e}")
    db.rollback()
finally:
    db.close()

print("\n" + "="*60)
print("🎉 QUICK TRAINING COMPLETE!")
print("="*60)
print(f"\nModel: {base_name}")
print(f"Accuracy: {accuracy:.4f}")
print(f"F1 Score: {f1:.4f}")
print(f"\n✅ Ready for predictions!")
