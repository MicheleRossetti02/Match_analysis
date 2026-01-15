"""
Database Migration Script
Adds Kelly Criterion and Value Betting columns to the predictions table
"""

import sqlite3
import sys
import os

# Get database path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

DB_PATH = settings.DATABASE_URL.replace('sqlite:///', '')

print(f"🔧 Database Migration: Adding Kelly Criterion columns")
print(f"📁 Database: {DB_PATH}\n")

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(predictions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    migrations = []
    
    # Define new columns
    new_columns = {
        'kelly_percentage': 'REAL',
        'kelly_raw': 'REAL',
        'value_level': 'VARCHAR',
        'expected_value': 'REAL',
        'edge_percentage': 'REAL',
        'estimated_odds': 'JSON',
        'has_value_analysis': 'BOOLEAN DEFAULT 0',
        'is_estimated_odds': 'BOOLEAN DEFAULT 1'
    }
    
    # Add columns that don't exist
    for col_name, col_type in new_columns.items():
        if col_name not in columns:
            print(f"➕ Adding column: {col_name} ({col_type})")
            cursor.execute(f"ALTER TABLE predictions ADD COLUMN {col_name} {col_type}")
            migrations.append(col_name)
        else:
            print(f"✓ Column already exists: {col_name}")
    
    # Commit changes
    conn.commit()
    
    if migrations:
        print(f"\n✅ Migration complete! Added {len(migrations)} new columns:")
        for col in migrations:
            print(f"   - {col}")
    else:
        print(f"\n✅ All columns already exist. No migration needed.")
    
    print(f"\n🎉 Database is ready for Kelly Criterion analysis!")
    
except sqlite3.Error as e:
    print(f"\n❌ Error during migration: {e}")
    conn.rollback()
    sys.exit(1)

finally:
    conn.close()
