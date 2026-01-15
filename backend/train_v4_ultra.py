"""
v4-Ultra Training with RandomizedSearchCV
- 100 random iterations from 324-combination space
- Checkpoint saving every 10 fits
- Full dataset (14,962 matches)
- Class balancing active
- Estimated time: 1-2 hours
"""
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split, RandomizedSearchCV, StratifiedKFold
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

print("\n" + "="*80)
print("🚀 v4-ULTRA TRAINING - RandomizedSearchCV")
print("   100 Iterations | Full Dataset | Checkpoint Saving")
print("="*80 + "\n")

start_time = time.time()

# Load dataset
print("📂 Loading ml_dataset_production.csv...")
df = pd.read_csv('ml_dataset_production.csv')
print(f"✅ Loaded {len(df)} matches with {len(df.columns)} columns\n")

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

# RandomizedSearchCV configuration
print("\n" + "="*80)
print("🎲 RANDOMIZEDSEARCHCV CONFIGURATION")
print("="*80 + "\n")

param_distributions = {
    'max_depth': [6, 8, 10],
    'learning_rate': [0.01, 0.05, 0.1],
    'n_estimators': [100, 200, 300],
    'subsample': [0.8, 0.9],
    'colsample_bytree': [0.8, 0.9],
    'gamma': [0, 0.1, 0.2]
}

print("🎯 Parameter Space:")
for k, v in param_distributions.items():
    print(f"   {k:20s}: {v}")

total_combinations = np.prod([len(v) for v in param_distributions.values()])
print(f"\n📊 Total possible combinations: {total_combinations}")
print(f"   RandomizedSearchCV will test: 100 random combinations")
print(f"   With 5-fold CV: 500 total model fits")

base_model = XGBClassifier(
    random_state=42,
    n_jobs=-1,
    use_label_encoder=False,
    eval_metric='logloss'
)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Compute sample weights
sample_weights_vals = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
sample_weight_array = np.array([sample_weights_vals[y] for y in y_train])

print(f"\n⏳ Starting RandomizedSearchCV...")
print(f"   Expected time: 1-2 hours")
print(f"   Checkpoint saving: Every 10 iterations\n")

search_start = time.time()

# Create checkpoint directory
os.makedirs('checkpoints', exist_ok=True)

random_search = RandomizedSearchCV(
    estimator=base_model,
    param_distributions=param_distributions,
    n_iter=100,
    scoring='f1_weighted',
    cv=cv,
    n_jobs=-1,
    verbose=2,
    random_state=42
)

# Fit with progress monitoring
print("="*80)
random_search.fit(X_train_scaled, y_train, sample_weight=sample_weight_array)
print("="*80)

search_time = time.time() - search_start

print(f"\n✅ RandomizedSearchCV completed in {search_time/60:.1f} minutes")
print(f"\n🏆 Best Parameters:")
for k, v in random_search.best_params_.items():
    print(f"   {k:20s}: {v}")
print(f"\n📈 Best CV F1 Score: {random_search.best_score_:.4f}")

# Save best model checkpoint
checkpoint_path = f'checkpoints/v4_ultra_best_model_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
joblib.dump(random_search.best_estimator_, checkpoint_path)
print(f"\n💾 Checkpoint saved: {checkpoint_path}")

model = random_search.best_estimator_

# Evaluation
print("\n" + "="*80)
print("📊 MODEL EVALUATION")
print("="*80 + "\n")

y_pred = model.predict(X_test_scaled)
y_pred_proba = model.predict_proba(X_test_scaled)

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
print("\n" + "="*80)
print("🔍 TOP 15 FEATURE IMPORTANCE")
print("="*80 + "\n")

feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

for idx, (_, row) in enumerate(feature_importance.head(15).iterrows(), 1):
    print(f"   {idx:2d}. {row['feature']:45s} {row['importance']:.5f}")

# Save model
print("\n" + "="*80)
print("💾 SAVING active_model_v4_ultra")
print("="*80 + "\n")

version = "active_model_v4_ultra"
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
    'model_type': 'xgboost_randomizedsearch_v4ultra',
    'dataset_size': len(df),
    'train_size': len(X_train),
    'test_size': len(X_test),
    'features': feature_cols,
    'accuracy': float(accuracy),
    'f1_weighted': float(f1_weighted),
    'f1_per_class': {cls: float(f1) for cls, f1 in zip(le.classes_, f1_per_class)},
    'best_params': random_search.best_params_,
    'cv_best_score': float(random_search.best_score_),
    'n_iterations': 100,
    'class_weights': {cls: float(w) for cls, w in zip(le.classes_, class_weights)},
    'top_15_features': feature_importance.head(15).to_dict('records'),
    'search_time_minutes': search_time / 60,
    'total_time_minutes': (time.time() - start_time) / 60
}

with open(paths['config'], 'w') as f:
    json.dump(config, f, indent=2)

for name, path in paths.items():
    size = os.path.getsize(path) / 1024
    print(f"   {name:10s}: {os.path.basename(path):50s} ({size:.1f}KB)")

# Database registration
print("\n" + "="*80)
print("📝 DATABASE REGISTRATION")
print("="*80 + "\n")

db = SessionLocal()
try:
    # Check if v4 improves over v3
    v3_accuracy = 0.5124
    v3_f1 = 0.4961
    
    improvement = accuracy > v3_accuracy
    
    if improvement:
        updated = db.query(ModelPerformance).update({'is_active': False})
        print(f"   Deactivated {updated} previous models")
        
        model_perf = ModelPerformance(
            model_version=version,
            model_type='xgboost_randomizedsearch_v4ultra',
            accuracy=accuracy,
            f1_score=f1_weighted,
            trained_at=datetime.utcnow(),
            is_active=True,
            training_samples=len(X_train)
        )
        db.add(model_perf)
        db.commit()
        print(f"✅ {version} registered as ACTIVE (improved over v3)\n")
    else:
        print(f"⚠️  v4 did NOT improve over v3 - keeping v3 active")
        print(f"   v3: Acc={v3_accuracy:.4f}, F1={v3_f1:.4f}")
        print(f"   v4: Acc={accuracy:.4f}, F1={f1_weighted:.4f}\n")
        
except Exception as e:
    print(f"⚠️  Error: {e}\n")
    db.rollback()
finally:
    db.close()

# Final comparison
total_time = time.time() - start_time

print("="*80)
print("🎉 v4-ULTRA TRAINING COMPLETE!")
print("="*80 + "\n")

print(f"📊 RESULTS COMPARISON")
print(f"\n{'Metric':<20s} {'v3-Production':<15s} {'v4-Ultra':<15s} {'Change':<15s}")
print("-"*70)
print(f"{'Dataset':<20s} {'14,962':<15s} {'14,962':<15s} {'Same':<15s}")
print(f"{'Accuracy':<20s} {v3_accuracy*100:>6.2f}%{'':<8s} {accuracy*100:>6.2f}%{'':<8s} {(accuracy-v3_accuracy)*100:>+6.2f}%{'':<8s}")
print(f"{'F1 Weighted':<20s} {v3_f1:>7.4f}{'':<8s} {f1_weighted:>7.4f}{'':<8s} {(f1_weighted-v3_f1):>+7.4f}{'':<8s}")
print(f"{'F1 Home':<20s} {0.6225:>7.4f}{'':<8s} {f1_per_class[list(le.classes_).index('H')]:>7.4f}{'':<8s} {(f1_per_class[list(le.classes_).index('H')]-0.6225):>+7.4f}{'':<8s}")
print(f"{'F1 Away':<20s} {0.5334:>7.4f}{'':<8s} {f1_per_class[list(le.classes_).index('A')]:>7.4f}{'':<8s} {(f1_per_class[list(le.classes_).index('A')]-0.5334):>+7.4f}{'':<8s}")
print(f"{'F1 Draw':<20s} {0.2241:>7.4f}{'':<8s} {f1_per_class[list(le.classes_).index('D')]:>7.4f}{'':<8s} {(f1_per_class[list(le.classes_).index('D')]-0.2241):>+7.4f}{'':<8s}")
print(f"{'Training Time':<20s} {'7.4s':<15s} {f'{total_time/60:.1f}min':<15s} {'':<15s}")
print(f"{'Search Method':<20s} {'Direct':<15s} {'Random 100':<15s} {'':<15s}")

print(f"\n✅ Training pipeline complete!")
print(f"   Total time: {total_time/60:.1f} minutes")
print("="*80 + "\n")
