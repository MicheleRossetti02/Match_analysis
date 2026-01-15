"""
Database Migration: Add BetHistory Table
"""

import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

DB_PATH = settings.DATABASE_URL.replace('sqlite:///', '')

print(f"🔧 Database Migration: Adding BetHistory table")
print(f"📁 Database: {DB_PATH}\n")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # Check if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bet_history'")
    exists = cursor.fetchone()
    
    if exists:
        print(f"✓ bet_history table already exists")
    else:
        print(f"➕ Creating bet_history table...")
        
        cursor.execute("""
            CREATE TABLE bet_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id INTEGER NOT NULL,
                market VARCHAR NOT NULL,
                market_name VARCHAR,
                stake_kelly_percent REAL NOT NULL,
                stake_amount REAL NOT NULL,
                bankroll_at_bet REAL,
                odds REAL NOT NULL,
                is_estimated_odds BOOLEAN DEFAULT 1,
                ai_probability REAL,
                expected_value REAL,
                edge_percentage REAL,
                value_level VARCHAR,
                status VARCHAR NOT NULL DEFAULT 'PENDING',
                actual_result VARCHAR,
                is_winner BOOLEAN,
                pnl REAL DEFAULT 0.0,
                roi_percent REAL,
                bankroll_after REAL,
                placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                settled_at TIMESTAMP,
                notes VARCHAR,
                confidence_level VARCHAR,
                FOREIGN KEY (prediction_id) REFERENCES predictions (id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_bet_history_prediction_id ON bet_history(prediction_id)")
        cursor.execute("CREATE INDEX idx_bet_history_placed_at ON bet_history(placed_at)")
        cursor.execute("CREATE INDEX idx_bet_history_status ON bet_history(status)")
        
        conn.commit()
        print(f"✅ bet_history table created successfully!")
        print(f"✅ Indexes created")
    
    print(f"\n🎉 Database migration complete!")
    
except sqlite3.Error as e:
    print(f"\n❌ Error during migration: {e}")
    conn.rollback()
    sys.exit(1)

finally:
    conn.close()
