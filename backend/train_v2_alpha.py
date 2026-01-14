"""
Professional Training v2-Alpha - Smart Strategy
- Uses existing 467-match dataset (ml_dataset.csv)
- GridSearchCV for hyperparameter optimization
- Class weight balancing for improved Draw F1
- Saves as active_model_v2
"""
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
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
print("🚀 PROFESSIONAL TRAINING v2-ALPHA - GridSearchCV + Class Balancing")
print("="*70 + "\n")

start_time = time.time()

# ==================== STEP 1: Load Dataset ====================
print("📂 Loading existing dataset (ml_dataset.csv)...")
df = pd.read_csv('ml_dataset.csv')
print(f"✅ Loaded {len(df)} matches with {len(df.columns)} columns\n")

# ==================== STEP 2: Prepare Data ====================
print("📊 Preparing features and target...")
exclude_cols = ['match_id', 'result', 'match_date', 'league_id', 
                'home_team_id', 'away_team_id']
feature_cols = [col for col in df.columns if col not in exclude_cols]

X = df[feature_cols].fillna(0)
y = df['result']

# Encode
le = LabelEncoder()
y_encoded = le.fit_transform(y)

print(f"Features: {len(feature_cols)}")
print(f"\n🎯 Class Distribution:")
for cls, count in zip(*np.unique(y, return_counts=True)):
    print(f"   {cls}: {count:4d} ({count/len(y)*100:.1f}%)")

# Compute class weights
class_weights = compute_class_weight('balanced', classes=np.unique(y_encoded), y=y_encoded)
print(f"\n⚖️  Class Weights for Balancing:")
for cls, weight in zip(le.classes_, class_weights):
    print(f"   {cls}: {weight:.3f}")

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
print(f"\n✂️  Split: {len(X_train)} train | {len(X_test)} test")

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ==================== STEP 3: GridSearchCV ====================
print("\n" + "="*70)
print("🔍 GRIDSEARCHCV - Hyperparameter Tuning")
print("="*70 + "\n")

param_grid = {
    'max_depth': [4, 6, 8],
    'learning_rate': [0.05, 0.1, 0.15],
    'n_estimators': [100, 150, 200],
    'subsample': [0.8, 0.9],
    'colsample_bytree': [0.8, 0.9]
}

print("🎛️  Parameter Grid:")
for k, v in param_grid.items():
    print(f"   {k:20s}: {v}")

total_fits = np.prod([len(v) for v in param_grid.values()]) * 5
print(f"\n📊 Total combinations: {total_fits//5}")
print(f"   With 5-fold CV: {total_fits} model fits\n")

base_model = XGBClassifier(
    random_state=42,
    n_jobs=-1,
    use_label_encoder=False,
    eval_metric='logloss'
)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

grid_search = GridSearchCV(
    estimator=base_model,
    param_grid=param_grid,
    scoring='f1_weighted',
    cv=cv,
    n_jobs=-1,
    verbose=1
)

print("⏳ Running GridSearchCV (this will take 5-10 minutes)...\n")
grid_start = time.time()

# Compute sample weights for class balancing
sample_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
sample_weight_array = np.array([sample_weights[y] for y in y_train])

grid_search.fit(X_train_scaled, y_train, sample_weight=sample_weight_array)

grid_time = time.time() - grid_start

print(f"\n✅ GridSearchCV completed in {grid_time:.1f}s ({grid_time/60:.1f}min)")
print(f"\n🏆 Best Parameters:")
for k, v in grid_search.best_params_.items():
    print(f"   {k:20s}: {v}")
print(f"\n📈 Best CV F1 Score: {grid_search.best_score_:.4f}")

# Best model
model = grid_search.best_estimator_

# ==================== STEP 4: Evaluation ====================
print("\n" + "="*70)
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
    improvement = "" if cls != "D" else f" (was 0.17)"
    print(f"   {cls}: {f1:.4f}{improvement}")

print(f"\n📄 Classification Report:")
print(classification_report(y_test, y_pred, target_names=le.classes_, digits=4))

cm = confusion_matrix(y_test, y_pred)
print(f"🔢 Confusion Matrix:")
print(f"{'':5s} " + "  ".join([f"{cls:^7s}" for cls in le.classes_]))
for i, cls in enumerate(le.classes_):
    print(f"{cls:5s} " + "  ".join([f"{cm[i][j]:7d}" for j in range(len(le.classes_))]))

# ==================== STEP 5: Feature Importance ====================
print("\n" + "="*70)
print("🔍 FEATURE IMPORTANCE")
print("="*70 + "\n")

feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("📊 TOP 10 FEATURES:")
for idx, (_, row) in enumerate(feature_importance.head(10).iterrows(), 1):
    print(f"   {idx:2d}. {row['feature']:40s} {row['importance']:.5f}")

# ==================== STEP 6: Save Model ====================
print("\n" + "="*70)
print("💾 SAVING active_model_v2")
print("="*70 + "\n")

version = "active_model_v2"
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
    'model_type': 'xgboost_gridsearch_v2alpha',
    'dataset_size': len(df),
    'features': feature_cols,
    'accuracy': float(accuracy),
    'f1_weighted': float(f1_weighted),
    'f1_per_class': {cls: float(f1) for cls, f1 in zip(le.classes_, f1_per_class)},
    'best_params': grid_search.best_params_,
    'cv_best_score': float(grid_search.best_score_),
    'class_weights_used': {cls: float(w) for cls, w in zip(le.classes_, class_weights)},
    'top_10_features': feature_importance.head(10).to_dict('records'),
    'training_time_minutes': (time.time() - start_time) / 60
}

with open(paths['config'], 'w') as f:
    json.dump(config, f, indent=2)

for name, path in paths.items():
    size = os.path.getsize(path) / 1024
    print(f"   {name:10s}: {path:50s} ({size:.1f}KB)")

# ==================== STEP 7: Database Registration ====================
print("\n" + "="*70)
print("📝 DATABASE REGISTRATION")
print("="*70 + "\n")

db = SessionLocal()
try:
    updated = db.query(ModelPerformance).update({'is_active': False})
    print(f"   Deactivated {updated} previous models")
    
    model_perf = ModelPerformance(
        model_version=version,
        model_type='xgboost_gridsearch_v2alpha',
        accuracy=accuracy,
        f1_score=f1_weighted,
        trained_at=datetime.utcnow(),
        is_active=True,
        training_samples=len(X_train)
    )
    db.add(model_perf)
    db.commit()
    print(f"✅ {version} registered as active\n")
except Exception as e:
    print(f"⚠️  Error: {e}\n")
    db.rollback()
finally:
    db.close()

# ==================== FINAL SUMMARY ====================
total_time = time.time() - start_time

print("="*70)
print("🎉 v2-ALPHA TRAINING COMPLETE!")
print("="*70 + "\n")

print(f"📊 RESULTS SUMMARY")
print(f"   Model:              {version}")
print(f"   Dataset:            {len(df)} matches")
print(f"   Features:           {len(feature_cols)}")
print(f"   Accuracy:           {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"   F1 Weighted:        {f1_weighted:.4f}")
print(f"   F1 Draw (D):        {f1_per_class[list(le.classes_).index('D')]:.4f} (was 0.17)")
print(f"   Best CV Score:      {grid_search.best_score_:.4f}")
print(f"   Training Time:      {total_time/60:.1f} minutes")

print(f"\n💡 Improvement vs Quick Training:")
quick_acc, quick_f1 = 0.4149, 0.3971
print(f"   Accuracy: {quick_acc:.4f} → {accuracy:.4f} ({(accuracy-quick_acc)*100:+.2f}%)")
print(f"   F1 Score: {quick_f1:.4f} → {f1_weighted:.4f} ({(f1_weighted-quick_f1)*100:+.2f}%)")

print(f"\n✅ Model ready for production!")
print("="*70 + "\n")
