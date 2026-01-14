#!/usr/bin/env python3
"""
Quick test of optimized FeatureEngineer
Generates dataset with 100 matches to verify bulk loading works
"""
import time
from src.ml.feature_engineer import FeatureEngineer

print("\n" + "="*70)
print("🧪 TESTING OPTIMIZED FEATUREENGINEER")
print("="*70 + "\n")

print("🔧 Initializing FeatureEngineer...")
engineer = FeatureEngineer()

print("📊 Generating dataset (limited to 100 matches for test)...")
start = time.time()

# Generate with date limit to get ~100 matches
from datetime import datetime, timedelta
min_date = datetime(2025, 11, 1)  # November 2025

df = engineer.create_training_dataset(min_date=min_date)

elapsed = time.time() - start

print(f"\n✅ Generated {len(df)} matches in {elapsed:.2f}s")
print(f"   Cache hits: {engineer._cache_hits}")
print(f"   Cache misses: {engineer._cache_misses}")

if engineer._cache_hits > 0:
    hit_rate = engineer._cache_hits / (engineer._cache_hits + engineer._cache_misses) * 100
    print(f"   Cache hit rate: {hit_rate:.1f}%")

print(f"\n📈 Performance:")
print(f"   {elapsed/len(df):.3f}s per match")
print(f"   Estimated time for 14,962 matches: {(elapsed/len(df))*14962/60:.1f} minutes")

engineer.close()

if elapsed / len(df) < 0.2:
    print(f"\n✅ OPTIMIZATION WORKING! Fast enough for large-scale training")
else:
    print(f"\n⚠️  Still too slow. Need more optimization.")

print("="*70 + "\n")
