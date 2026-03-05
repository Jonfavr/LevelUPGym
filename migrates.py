"""
db_patch.py  —  Run once to add the 6 new columns to your live database.
Safe to run multiple times (uses ALTER TABLE only when the column is missing).

Usage:  python db_patch.py
"""

import sqlite3, os

DB_NAME = 'levelup_gym.db'

ROUTINES_COLUMNS = [
    ("difficulty_level", "TEXT", None),
    ("routine_type",     "TEXT", None),
    ("primary_muscle",   "TEXT", None),
    ("main_class",       "TEXT", None),
]

CLIENTS_COLUMNS = [
    ("fitness_goal",    "TEXT", None),
    ("preferred_split", "TEXT", None),
]

def add_columns_if_missing(cursor, table, columns):
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    for col_name, col_type, default in columns:
        if col_name not in existing:
            if default is not None:
                cursor.execute(
                    f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type} DEFAULT {default}"
                )
            else:
                cursor.execute(
                    f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"
                )
            print(f"  ✅ Added '{col_name}' to '{table}'")
        else:
            print(f"  — '{col_name}' already exists in '{table}', skipping.")

def run():
    if not os.path.exists(DB_NAME):
        print(f"❌ Database '{DB_NAME}' not found. Make sure you run this from the project root.")
        return

    conn = sqlite3.connect(DB_NAME)
    cur  = conn.cursor()

    print("\n📦 Patching 'routines' table…")
    add_columns_if_missing(cur, "routines", ROUTINES_COLUMNS)

    print("\n👤 Patching 'clients' table…")
    add_columns_if_missing(cur, "clients", CLIENTS_COLUMNS)

    conn.commit()
    conn.close()
    print("\n✅ Database patch complete.\n")

if __name__ == "__main__":
    run()