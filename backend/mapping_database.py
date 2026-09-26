
import sqlite3
from pathlib import Path

# Locate the existing database
BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "data" / "database" / "wattwise.db"


def main():
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    # Enable foreign key validation
    cursor.execute("PRAGMA foreign_keys = ON")

    # 1. Consumer information
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consumers (
            consumer_id TEXT PRIMARY KEY,
            consumer_name TEXT,
            location_latitude REAL,
            location_longitude REAL,
            average_daily_energy_kwh REAL
        )
    """)

    # 2. Transformer information
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transformers (
            transformer_id TEXT PRIMARY KEY,
            transformer_name TEXT,
            rated_capacity_kva REAL,
            location_latitude REAL,
            location_longitude REAL
        )
    """)

    # 3. Consumer-to-transformer mapping records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mappings (
            mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumer_id TEXT NOT NULL,
            transformer_id TEXT NOT NULL,
            confidence_score REAL,
            mapping_status TEXT NOT NULL DEFAULT 'unverified',
            mapping_source TEXT NOT NULL DEFAULT 'unknown',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (consumer_id)
                REFERENCES consumers(consumer_id),

            FOREIGN KEY (transformer_id)
                REFERENCES transformers(transformer_id),

            CHECK (
                confidence_score IS NULL OR
                (confidence_score >= 0 AND confidence_score <= 1)
            ),

            CHECK (
                mapping_status IN (
                    'unverified',
                    'verified',
                    'rejected'
                )
            )
        )
    """)

    connection.commit()

    print("WattWise AI mapping tables created successfully!")

    # Verify the tables
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """)

    print("\nTables in the database:")
    for row in cursor.fetchall():
        print("-", row[0])

    connection.close()


if __name__ == "__main__":
    main()