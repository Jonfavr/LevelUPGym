"""
migrate_muscles.py
==================
Run this ONCE to migrate the exercises table from the old
`target_muscle` (comma-separated blob) to two clean columns:

    primary_muscle       TEXT   — single muscle, used by swap matching
    complementary_muscle TEXT   — secondary muscles (dropdown, optional)

Safe to run multiple times — it checks whether the columns already exist.

Usage:
    python migrate_muscles.py
"""

import sqlite3
import os
import sys

# ── Adjust this path if your db file lives elsewhere ──────────────
DB_PATH = os.path.join(os.path.dirname(__file__), 'levelup_gym.db')
# ──────────────────────────────────────────────────────────────────


def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"❌  Database not found at: {DB_PATH}")
        print("    Update DB_PATH at the top of this script.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ── 1. Add new columns if they don't exist ────────────────────
    added = []
    if not column_exists(cur, 'exercises', 'primary_muscle'):
        cur.execute("ALTER TABLE exercises ADD COLUMN primary_muscle TEXT")
        added.append('primary_muscle')

    if not column_exists(cur, 'exercises', 'complementary_muscle'):
        cur.execute("ALTER TABLE exercises ADD COLUMN complementary_muscle TEXT")
        added.append('complementary_muscle')

    if added:
        print(f"✅  Added columns: {', '.join(added)}")
    else:
        print("ℹ️   Columns already exist — skipping ALTER TABLE")

    # ── 2. Migrate existing target_muscle data ────────────────────
    cur.execute("SELECT exercise_id, target_muscle FROM exercises")
    rows = cur.fetchall()

    updated = 0
    for row in rows:
        eid = row['exercise_id']
        raw = (row['target_muscle'] or '').strip()

        if not raw:
            continue

        # Split on comma; first part → primary, rest → complementary
        parts = [p.strip() for p in raw.split(',') if p.strip()]
        primary       = parts[0] if parts else raw
        complementary = ', '.join(parts[1:]) if len(parts) > 1 else ''

        cur.execute(
            """UPDATE exercises
               SET primary_muscle = ?, complementary_muscle = ?
               WHERE exercise_id = ?""",
            (primary, complementary or None, eid)
        )
        updated += 1

    conn.commit()
    conn.close()

    print(f"✅  Migrated {updated} exercise records")
    print()
    print("Next steps:")
    print("  1. Replace  models/exercise_model.py  with the updated version")
    print("  2. Replace  templates/admin/exercises.html  with the redesigned version")
    print("  3. Replace  templates/admin/exercise_form.html  with the updated form")
    print("  4. Apply the main.py patches (swap route + add/edit routes)")
    print()
    print("The old `target_muscle` column is LEFT IN PLACE for safety.")
    print("Once everything is verified, you can drop it with:")
    print("  ALTER TABLE exercises RENAME TO exercises_old;")
    print("  CREATE TABLE exercises AS SELECT ... (without target_muscle) ... FROM exercises_old;")


if __name__ == '__main__':
    migrate()