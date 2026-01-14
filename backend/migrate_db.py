"""
Database Migration Script
Add missing columns to predictions table for accuracy tracking
"""
import sqlite3
import os

DB_PATH = "football_predictions.db"

def migrate_database():
    """Add missing columns to predictions table"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return
    
    print(f"🔄 Migrating database: {DB_PATH}\n")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(predictions)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    print(f"📊 Found {len(existing_columns)} existing columns")
    
    # Define new columns to add
    new_columns = [
        ("btts_actual", "BOOLEAN"),
        ("btts_correct", "BOOLEAN"),
        ("over_15_actual", "BOOLEAN"),
        ("over_15_correct", "BOOLEAN"),
        ("over_25_actual", "BOOLEAN"),
        ("over_25_correct", "BOOLEAN"),
        ("over_35_actual", "BOOLEAN"),
        ("over_35_correct", "BOOLEAN"),
    ]
    
    # Add missing columns
    added_count = 0
    for column_name, column_type in new_columns:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE predictions ADD COLUMN {column_name} {column_type}")
                print(f"  ✅ Added column: {column_name} ({column_type})")
                added_count += 1
            except Exception as e:
                print(f"  ❌ Error adding {column_name}: {e}")
        else:
            print(f"  ⏭️  Column already exists: {column_name}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\n✅ Migration complete! Added {added_count} new columns")

if __name__ == "__main__":
    migrate_database()
