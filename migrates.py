"""
migrate_goals.py
────────────────
Run this ONCE to add the new columns needed for goal-based auto-assignment.
Safe to re-run — each ALTER is wrapped in a try/except.

Usage:
    python migrate_goals.py
"""

import sqlite3
import os

# ── Adjust this path to point at your actual database file ──────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), 'levelup_gym.db')


def run():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    migrations = [

        # ── clients table ────────────────────────────────────────────────────
        ("clients", "fitness_goal",
         "ALTER TABLE clients ADD COLUMN fitness_goal TEXT DEFAULT NULL"),

        ("clients", "preferred_split",
         "ALTER TABLE clients ADD COLUMN preferred_split TEXT DEFAULT NULL"),

        # ── routines table ───────────────────────────────────────────────────
        ("routines", "difficulty_level",
         "ALTER TABLE routines ADD COLUMN difficulty_level TEXT "
         "CHECK(difficulty_level IN ('beginner','intermediate','advanced')) "
         "DEFAULT 'beginner'"),

        ("routines", "routine_type",
         "ALTER TABLE routines ADD COLUMN routine_type TEXT DEFAULT 'Full Body'"),
    ]

    for table, column, sql in migrations:
        try:
            c.execute(sql)
            print(f"  ✅  Added '{column}' to '{table}'")
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print(f"  ⏭   '{column}' on '{table}' already exists — skipped")
            else:
                print(f"  ❌  Error on '{table}.{column}': {e}")

    # ── Seed any existing routines that still have NULL difficulty/type ───────
    c.execute("""
        UPDATE routines
        SET difficulty_level = 'beginner',
            routine_type     = 'Full Body'
        WHERE difficulty_level IS NULL
           OR routine_type     IS NULL
    """)
    seeded = c.rowcount
    if seeded:
        print(f"\n  📌  Seeded {seeded} existing routine(s) with beginner / Full Body defaults.")
        print("      Remember to update them to their correct type and difficulty in the admin UI.\n")

    conn.commit()
    conn.close()
    print("\n  ✅  Migration complete.\n")


if __name__ == '__main__':
    run()