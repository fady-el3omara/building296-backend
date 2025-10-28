"""
init_db.py
--------------------
Initialize the Building 296 database using the schema in /schema/schema.sql.

Usage:
    python init_db.py
This script will:
 - Connect to your SQLite database (schema/building296.db)
 - Create all tables from schema/schema.sql if they don’t already exist
 - Print a clear success/failure message
"""

import os
from sqlalchemy import text
from backend.database import engine

SCHEMA_PATH = "schema/schema.sql"
DB_PATH = "schema/building296.db"

def init_database():
    """Initializes the SQLite database if missing or empty."""
    if not os.path.exists(SCHEMA_PATH):
        print(f"❌ Schema file not found: {SCHEMA_PATH}")
        return

    # If DB file doesn’t exist, it will be created automatically by SQLite
    if not os.path.exists(DB_PATH):
        print("📄 Creating new database file...")

    try:
        with engine.connect() as conn:
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            conn.execute(text(schema_sql))
            conn.commit()

        print("✅ Database initialized successfully!")
        print(f"📂 Location: {DB_PATH}")

    except Exception as e:
        print("❌ Error initializing the database:", e)


if __name__ == "__main__":
    print("⚙️ Initializing Building 296 database...")
    init_database()
