"""
init_db.py
--------------------
Initialize the Building 296 database using the schema in /schema/schema.sql

Usage:
    python init_db.py
This script will:
- Connect to your SQLite database (schema/building296.db)
- Create all tables from schema/schema.sql if they don't already exist
- Print a clear success/failure message
"""

import os
import sqlite3

DB_PATH = "schema/building296.db"
SCHEMA_PATH = "schema/schema.sql"

def initialize_db():
    print("⚙️ Initializing Building 296 database...")
    if not os.path.exists("schema"):
        os.makedirs("schema")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql_script = f.read()

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.executescript(sql_script)  # ✅ FIXED LINE
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully!")
        print(f"📂 Location: {DB_PATH}")
    except Exception as e:
        print(f"❌ Error initializing the database: {e}")

if __name__ == "__main__":
    initialize_db()
