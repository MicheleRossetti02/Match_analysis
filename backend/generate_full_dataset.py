#!/usr/bin/env python3
"""
Full Dataset Generation - All 14,962 Matches
Generates ml_dataset_production.csv with complete historical data
"""
import time
from datetime import datetime
from src.ml.feature_engineer import FeatureEngineer

print("\n" + "="*70)
print("🚀 GENERATING FULL PRODUCTION DATASET")
print("="*70 + "\n")

print("📊 Target: All ~14,962 finished matches")
print("⏱️  Estimated time: ~10 minutes\n")

start_time = time.time()

print("🔧 Initializing FeatureEngineer...")
engineer = FeatureEngineer()

print("📂 Generating complete training dataset...")
print("   (No date filters - using ALL historical data)\n")

# Generate without any date limits to get maximum matches
df = engineer.create_training_dataset()

elapsed = time.time() - start_time

print(f"\n✅ Dataset Generation Complete!")
print(f"   Total matches: {len(df)}")
print(f"   Total features: {len(df.columns)}")
print(f"   Generation time: {elapsed/60:.1f} minutes")
print(f"   Speed: {elapsed/len(df):.3f}s per match")

# Save
output_file = 'ml_dataset_production.csv'
df.to_csv(output_file, index=False)
print(f"\n💾 Saved to: {output_file}")

# Statistics
print(f"\n📊 Dataset Statistics:")
print(f"   Features: {', '.join(df.columns[:10])}...")
print(f"\n🎯 Target Distribution:")
print(df['result'].value_counts())
print(f"\n📈 Class Percentages:")
for result, count in df['result'].value_counts().items():
    print(f"   {result}: {count/len(df)*100:.2f}%")

engineer.close()

print(f"\n✅ Ready for v3-Production training!")
print("="*70 + "\n")
