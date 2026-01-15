"""
Quick Training v3-Production
- Full dataset (14,962 matches)
- No GridSearch - uses best params from v2
- Class balancing active
- Fast execution: 2-3 minutes
"""
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.utils.class_weight import compute_class_weight
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score, confusion_matrix
import joblib
import json
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.models.database import SessionLocal, ModelPerformance

print("\n" + "="*70)
print("🚀 QUICK TRAINING v3-PRODUCTION")
print("   Full Dataset | Best Params from v2 | Class Balancing")
print("="*70 + "\n")

start_time = time.time()

# Load dataset
print("📂 Loading ml_dataset_production.csv...")
df = pd.read_csv('ml_dataset_production.csv')
print(f"✅ Loaded {len(df)} matches\n")

# Prepare data
exclude_cols = ['match_id', 'result', 'match_date', 'league_id', 
                'home_team_id', 'away_team_id']
feature_cols = [col for col in df.columns if col not in exclude_cols]

X = df[feature_cols].fillna(0)
y = df['result']

le = LabelEncoder()
y_encoded = le.fit_transform(y)

print(f"📊 Dataset: {len(df)} matches, {len(feature_cols)} features")
print(f"\n🎯 Class Distribution:")
for cls, count in zip(*np.unique(y, return_counts=True)):
    print(f"   {cls}: {count:5d} ({count/len(y)*100:.2f}%)")

# Class weights
class_weights = compute_class_weight('balanced', classes=np.unique(y_encoded), y=y_encoded)
print(f"\n⚖️  Class Weights:")
for cls, weight in zip(le.classes_, class_weights):
    print(f"   {cls}: {weight:.3f}")

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.25, random_state=42, stratify=y_encoded
)
print(f"\n✂️  Split: {len(X_train)} train | {len(X_test)} test")

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train with BEST params from v2
print("\n" + "="*70)
print("🎯 TRAINING WITH OPTIMAL PARAMETERS")
print("="*70 + "\n")

best_params = {
    'max_depth': 8,
    'learning_rate': 0.1,
    'n_estimators': 150,
    'subsample': 0.9,
    'colsample_bytree': 0.9,
    'random_state': 42,
    'n_jobs': -1,
    'use_label_encoder': False,
    'eval_metric': 'logloss'
}

print("📋 Using Best Parameters from v2:")
for k, v in best_params.items():
    if k not in ['random_state', 'n_jobs', 'use_label_encoder', 'eval_metric']:
        print(f"   {k:20s}: {v}")

print("\n⏳ Training XGBoost...")
train_start = time.time()

# Compute sample weights
sample_weights_vals = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
sample_weight_array = np.array([sample_weights_vals[y] for y in y_train])

model = XGBClassifier(**best_params)
model.fit(X_train_scaled, y_train, sample_weight=sample_weight_array)

train_time = time.time() - train_start
print(f"✅ Training completed in {train_time:.1f}s\n")

# Evaluation
print("="*70)
print("📊 MODEL EVALUATION")
print("="*70 + "\n")

y_pred = model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)
f1_weighted = f1_score(y_test, y_pred, average='weighted')
f1_per_class = f1_score(y_test, y_pred, average=None)

print(f"🎯 Test Set Performance:")
print(f"   Accuracy:    {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"   F1 Weighted: {f1_weighted:.4f}\n")

print(f"📋 Per-Class F1 Scores:")
for cls, f1 in zip(le.classes_, f1_per_class):
    print(f"   {cls}: {f1:.4f}")

print(f"\n📄 Classification Report:")
print(classification_report(y_test, y_pred, target_names=le.classes_, digits=4))

cm = confusion_matrix(y_test, y_pred)
print(f"🔢 Confusion Matrix:")
print(f"{'':5s} " + "  ".join([f"{cls:^8s}" for cls in le.classes_]))
for i, cls in enumerate(le.classes_):
    print(f"{cls:5s} " + "  ".join([f"{cm[i][j]:8d}" for j in range(len(le.classes_))]))

# Feature importance
print("\n" + "="*70)
print("🔍 TOP 15 FEATURE IMPORTANCE")
print("="*70 + "\n")

feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

for idx, (_, row) in enumerate(feature_importance.head(15).iterrows(), 1):
    print(f"   {idx:2d}. {row['feature']:45s} {row['importance']:.5f}")

# Save model
print("\n" + "="*70)
print("💾 SAVING active_model_v3_production")
print("="*70 + "\n")

version = "active_model_v3_production"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

os.makedirs('models', exist_ok=True)

paths = {
    'model': f'models/{version}_1x2.pkl',
    'scaler': f'models/{version}_scaler.pkl',
    'encoder': f'models/{version}_encoder.pkl',
    'config': f'models/{version}_config.json'
}

joblib.dump(model, paths['model'])
joblib.dump(scaler, paths['scaler'])
joblib.dump(le, paths['encoder'])

config = {
    'version': version,
    'timestamp': timestamp,
    'model_type': 'xgboost_quick_v3production',
    'dataset_size': len(df),
    'train_size': len(X_train),
    'test_size': len(X_test),
    'features': feature_cols,
    'accuracy': float(accuracy),
    'f1_weighted': float(f1_weighted),
    'f1_per_class': {cls: float(f1) for cls, f1 in zip(le.classes_, f1_per_class)},
    'best_params': best_params,
    'class_weights': {cls: float(w) for cls, w in zip(le.classes_, class_weights)},
    'top_15_features': feature_importance.head(15).to_dict('records'),
    'training_time_seconds': train_time,
    'total_time_minutes': (time.time() - start_time) / 60
}

with open(paths['config'], 'w') as f:
    json.dump(config, f, indent=2)

for name, path in paths.items():
    size = os.path.getsize(path) / 1024
    print(f"   {name:10s}: {os.path.basename(path):50s} ({size:.1f}KB)")

# Database registration
print("\n" + "="*70)
print("📝 DATABASE REGISTRATION")
print("="*70 + "\n")

db = SessionLocal()
try:
    updated = db.query(ModelPerformance).update({'is_active': False})
    print(f"   Deactivated {updated} previous models")
    
    model_perf = ModelPerformance(
        model_version=version,
        model_type='xgboost_quick_v3production',
        accuracy=accuracy,
        f1_score=f1_weighted,
        trained_at=datetime.utcnow(),
        is_active=True,
        training_samples=len(X_train)
    )
    db.add(model_perf)
    db.commit()
    print(f"✅ {version} registered as ACTIVE\n")
except Exception as e:
    print(f"⚠️  Error: {e}\n")
    db.rollback()
finally:
    db.close()

# Final summary
total_time = time.time() - start_time

print("="*70)
print("🎉 v3-PRODUCTION TRAINING COMPLETE!")
print("="*70 + "\n")

print(f"📊 FINAL RESULTS")
print(f"   Model:              {version}")
print(f"   Dataset:            {len(df):,} matches")
print(f"   Features:           {len(feature_cols)}")
print(f"   Accuracy:           {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"   F1 Weighted:        {f1_weighted:.4f}")
print(f"   F1 Draw (D):        {f1_per_class[list(le.classes_).index('D')]:.4f}")
print(f"   Training Time:      {train_time:.1f}s")
print(f"   Total Time:         {total_time:.1f}s ({total_time/60:.1f}min)")

print(f"\n📈 IMPROVEMENT vs v2-Alpha:")
v2_acc, v2_f1 = 0.4043, 0.3944
print(f"   Dataset:  467 → {len(df):,} matches ({len(df)/467:.1f}x)")
print(f"   Accuracy: {v2_acc:.4f} → {accuracy:.4f} ({(accuracy-v2_acc)*100:+.2f}%)")
print(f"   F1 Score: {v2_f1:.4f} → {f1_weighted:.4f} ({(f1_weighted-v2_f1)*100:+.2f}%)")
print(f"   F1 Draw:  0.1500 → {f1_per_class[list(le.classes_).index('D')]:.4f} ({(f1_per_class[list(le.classes_).index('D')]-0.15)*100:+.2f}%)")

print(f"\n✅ Model deployed and ready for production!")
print("="*70 + "\n")
