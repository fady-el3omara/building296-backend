"""
init_db.py
--------------------
Initialize the Building 296 database using the schema in /schema/schema.sql

Usage:
    python init_db.py

This script will:
- Connect to your SQLite database (schema/building296.db)
- Create all tables from schema/schema.sql if they don't already exist
- Verify key tables were created successfully
- Print a clear success/failure message
"""

import os
import sqlite3

DB_PATH = "schema/building296.db"
SCHEMA_PATH = "schema/schema.sql"

EXPECTED_TABLES = [
    "owners",
    "rents",
    "expenses",
    "owner_allowances",
    "owner_wallets",
    "expected_distribution",
    "variance_report"
]


def initialize_db():
    print("⚙️ Initializing Building 296 database...")

    # Ensure schema folder exists
    if not os.path.exists("schema"):
        os.makedirs("schema")

    # Read schema SQL file
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql_script = f.read()

    try:
        # Connect and execute full script
        conn = sqlite3.connect(DB_PATH)
        conn.executescript(sql_script)
        conn.commit()

        # Verify tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Compare expected vs actual tables
        missing = [t for t in EXPECTED_TABLES if t not in tables]

        if missing:
            print("⚠️ Database initialized, but missing expected tables:")
            for t in missing:
                print(f"   - {t}")
        else:
            print("✅ Database initialized successfully! All expected tables found.")

        print(f"📂 Database file: {DB_PATH}")
        print(f"🧩 Total tables created: {len(tables)}")

    except Exception as e:
        print(f"❌ Error initializing the database: {e}")


if __name__ == "__main__":
    initialize_db()

