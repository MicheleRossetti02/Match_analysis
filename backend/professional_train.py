"""
Professional ML Training Pipeline - Sprint 5
Features:
- Optimized FeatureEngineer with bulk loading + memoization
- GridSearchCV for hyperparameter tuning
- Class weight balancing for draws
- K-Fold cross-validation (k=5)
- Comprehensive metrics and feature importance
- Model versioning as active_model_v2
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.utils.class_weight import compute_class_weight
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score, confusion_matrix
import joblib
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.models.database import SessionLocal, ModelPerformance
from src.ml.feature_engineer import FeatureEngineer

print("\n" + "="*70)
print("🚀 PROFESSIONAL ML TRAINING PIPELINE - Sprint 5")
print("="*70 + "\n")

# ==================== STEP 1: Dataset Generation ====================
print("📊 STEP 1: Generating Optimized Dataset with FeatureEngineer")
print("-" * 70)

start_total = time.time()

print("\n🔧 Initializing FeatureEngineer with optimizations...")
engineer = FeatureEngineer()

print("📂 Generating training dataset (target: 1500+ matches)...")
dataset_start = time.time()

# Generate dataset without date limits to get maximum matches
df = engineer.create_training_dataset()

dataset_time = time.time() - dataset_start

print(f"\n✅ Dataset generated in {dataset_time:.1f}s ({dataset_time/60:.1f}min)")
print(f"   Total matches: {len(df)}")
print(f"   Total features: {len(df.columns)}")

# Save dataset
df.to_csv('ml_dataset_full.csv', index=False)
print(f"💾 Saved to ml_dataset_full.csv")

engineer.close()

# ==================== STEP 2: Data Preparation ====================
print("\n" + "="*70)
print("📋 STEP 2: Data Preparation & Analysis")
print("-" * 70)

# Prepare features
exclude_cols = ['match_id', 'result', 'match_date', 'league_id', 
                'home_team_id', 'away_team_id']
feature_cols = [col for col in df.columns if col not in exclude_cols]

print(f"\n📌 Feature count: {len(feature_cols)}")
print(f"   Sample features: {feature_cols[:5]}")

X = df[feature_cols].fillna(0)
y = df['result']

# Encode target
le = LabelEncoder()
y_encoded = le.fit_transform(y)

print(f"\n🎯 Target Distribution:")
for cls, count in zip(*np.unique(y, return_counts=True)):
    pct = count/len(y)*100
    print(f"   {cls}: {count:4d} ({pct:5.1f}%)")

# Compute class weights for balancing
class_weights = compute_class_weight('balanced', classes=np.unique(y_encoded), y=y_encoded)
class_weight_dict = {i: w for i, w in enumerate(class_weights)}
print(f"\n⚖️  Class Weights (for balancing):")
for cls, weight in zip(le.classes_, class_weights):
    print(f"   {cls}: {weight:.3f}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

print(f"\n✂️  Train/Test Split:")
print(f"   Training: {len(X_train)} matches")
print(f"   Testing:  {len(X_test)} matches")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("✅ Features scaled with StandardScaler")

# ==================== STEP 3: Hyperparameter Tuning ====================
print("\n" + "="*70)
print("🔍 STEP 3: GridSearchCV - Hyperparameter Optimization")
print("-" * 70)

# Define parameter grid
param_grid = {
    'max_depth': [4, 6, 8],
    'learning_rate': [0.01, 0.05, 0.1],
    'n_estimators': [100, 200, 300],
    'subsample': [0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9],
    'min_child_weight': [1, 3, 5]
}

print(f"\n🎛️  Parameter Grid:")
for param, values in param_grid.items():
    print(f"   {param:20s}: {values}")

total_combinations = np.prod([len(v) for v in param_grid.values()])
print(f"\n📊 Total combinations: {total_combinations}")
print(f"   With 5-fold CV: {total_combinations * 5} fits")

# Base model with class weights
base_model = XGBClassifier(
    random_state=42,
    n_jobs=-1,
    use_label_encoder=False,
    eval_metric='logloss'
)

# GridSearchCV with StratifiedKFold
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

grid_search = GridSearchCV(
    estimator=base_model,
    param_grid=param_grid,
    scoring='f1_weighted',
    cv=cv,
    n_jobs=-1,
    verbose=2
)

print("\n⏳ Starting GridSearchCV (this may take several minutes)...")
grid_start = time.time()

grid_search.fit(X_train_scaled, y_train, sample_weight=compute_class_weight('balanced', classes=np.unique(y_train), y=y_train))

grid_time = time.time() - grid_start
print(f"\n✅ GridSearchCV completed in {grid_time:.1f}s ({grid_time/60:.1f}min)")

# Best parameters
print(f"\n🏆 Best Parameters Found:")
for param, value in grid_search.best_params_.items():
    print(f"   {param:20s}: {value}")

print(f"\n📈 Best CV Score (F1 Weighted): {grid_search.best_score_:.4f}")

# Use best estimator
best_model = grid_search.best_estimator_

# ==================== STEP 4: Model Evaluation ====================
print("\n" + "="*70)
print("📊 STEP 4: Model Evaluation on Test Set")
print("-" * 70)

# Predictions
y_pred = best_model.predict(X_test_scaled)
y_pred_proba = best_model.predict_proba(X_test_scaled)

# Metrics
accuracy = accuracy_score(y_test, y_pred)
f1_weighted = f1_score(y_test, y_pred, average='weighted')
f1_per_class = f1_score(y_test, y_pred, average=None)

print(f"\n🎯 Overall Performance:")
print(f"   Accuracy:    {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"   F1 Weighted: {f1_weighted:.4f}")

print(f"\n📋 Per-Class F1 Scores:")
for cls, f1 in zip(le.classes_, f1_per_class):
    print(f"   {cls}: {f1:.4f}")

print(f"\n📄 Detailed Classification Report:")
print(classification_report(y_test, y_pred, target_names=le.classes_, digits=4))

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
print(f"\n🔢 Confusion Matrix:")
print(f"{'':5s} " + "  ".join([f"{cls:^7s}" for cls in le.classes_]))
for i, cls in enumerate(le.classes_):
    print(f"{cls:5s} " + "  ".join([f"{cm[i][j]:7d}" for j in range(len(le.classes_))]))

# ==================== STEP 5: Feature Importance ====================
print("\n" + "="*70)
print("🔍 STEP 5: Feature Importance Analysis")
print("-" * 70)

feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': best_model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n📊 TOP 15 MOST IMPORTANT FEATURES:")
for idx, (_, row) in enumerate(feature_importance.head(15).iterrows(), 1):
    print(f"   {idx:2d}. {row['feature']:45s} {row['importance']:.5f}")

# ==================== STEP 6: Model Persistence ====================
print("\n" + "="*70)
print("💾 STEP 6: Saving Model as active_model_v2")
print("-" * 70)

version = "active_model_v2"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

os.makedirs('models', exist_ok=True)

model_path = f'models/{version}_1x2.pkl'
scaler_path = f'models/{version}_scaler.pkl'
encoder_path = f'models/{version}_encoder.pkl'
config_path = f'models/{version}_config.json'

joblib.dump(best_model, model_path)
joblib.dump(scaler, scaler_path)
joblib.dump(le, encoder_path)

config = {
    'version': version,
    'timestamp': timestamp,
    'model_type': 'xgboost_gridsearch',
    'features': feature_cols,
    'accuracy': float(accuracy),
    'f1_weighted': float(f1_weighted),
    'f1_per_class': {cls: float(f1) for cls, f1 in zip(le.classes_, f1_per_class)},
    'samples_train': len(X_train),
    'samples_test': len(X_test),
    'best_params': grid_search.best_params_,
    'cv_best_score': float(grid_search.best_score_),
    'class_weights': {cls: float(w) for cls, w in zip(le.classes_, class_weights)},
    'top_features': feature_importance.head(10).to_dict('records'),
    'training_time_minutes': (grid_time + dataset_time) / 60
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f"\n✅ Model Files Saved:")
print(f"   {model_path}")
print(f"   {scaler_path}")
print(f"   {encoder_path}")
print(f"   {config_path}")

# ==================== STEP 7: Database Registration ====================
print("\n" + "="*70)
print("📝 STEP 7: Registering Model in Database")
print("-" * 70)

db = SessionLocal()
try:
    # Deactivate old models
    updated = db.query(ModelPerformance).update({'is_active': False})
    print(f"   Deactivated {updated} previous models")
    
    # Register new model
    model_perf = ModelPerformance(
        model_version=version,
        model_type='xgboost_gridsearch_v2',
        accuracy=accuracy,
        f1_score=f1_weighted,
        trained_at=datetime.utcnow(),
        is_active=True,
        training_samples=len(X_train)
    )
    db.add(model_perf)
    db.commit()
    print(f"✅ Registered {version} as active model")
    
except Exception as e:
    print(f"⚠️  Database error: {e}")
    db.rollback()
finally:
    db.close()

# ==================== FINAL SUMMARY ====================
total_time = time.time() - start_total

print("\n" + "="*70)
print("🎉 PROFESSIONAL TRAINING COMPLETE!")
print("="*70)

print(f"\n📊 FINAL SUMMARY")
print(f"   Model Version:      {version}")
print(f"   Dataset Size:       {len(df)} matches")
print(f"   Features:           {len(feature_cols)}")
print(f"   Accuracy:           {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"   F1 Weighted:        {f1_weighted:.4f}")
print(f"   F1 Draw:            {f1_per_class[list(le.classes_).index('D')]:.4f}")
print(f"   Best CV Score:      {grid_search.best_score_:.4f}")
print(f"   Training Time:      {total_time/60:.1f} minutes")

print(f"\n💡 Improvement Over Quick Training:")
quick_acc = 0.4149
quick_f1 = 0.3971
print(f"   Accuracy: {quick_acc:.4f} → {accuracy:.4f} ({(accuracy-quick_acc)*100:+.2f}%)")
print(f"   F1 Score: {quick_f1:.4f} → {f1_weighted:.4f} ({(f1_weighted-quick_f1)*100:+.2f}%)")

print(f"\n✅ Model ready for production use!")
print("="*70 + "\n")
