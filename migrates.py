"""
migrate_admin_users.py
─────────────────────
Run ONCE from the project root to:
  1. Create the admin_users table
  2. Seed the default superadmin (admin / admin123)

Usage:
    python migrate_admin_users.py
"""

import sqlite3
import hashlib
import os

DB_NAME = 'levelup_gym.db'


def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def run():
    if not os.path.exists(DB_NAME):
        print(f"❌  Database '{DB_NAME}' not found. Run the app once first.")
        return

    conn = sqlite3.connect(DB_NAME)
    cur  = conn.cursor()

    # ── 1. Create table ──────────────────────────────────────────────────
    cur.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name     TEXT NOT NULL,
            role          TEXT NOT NULL DEFAULT 'staff',
            is_active     INTEGER NOT NULL DEFAULT 1,
            created_by    TEXT,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅  admin_users table ready.")

    # ── 2. Seed default superadmin (only if no users exist) ──────────────
    cur.execute('SELECT COUNT(*) FROM admin_users')
    count = cur.fetchone()[0]

    if count == 0:
        cur.execute(
            '''INSERT INTO admin_users (username, password_hash, full_name, role, created_by)
               VALUES (?, ?, ?, ?, ?)''',
            ('admin', hash_pw('levelupadmin'), 'System Administrator', 'superadmin', 'migration')
        )
        print("✅  Default superadmin seeded  →  username: admin  |  password: levelupadmin")
        print("⚠️   Change the default password after first login!")
    else:
        print(f"ℹ️   {count} admin user(s) already exist — seed skipped.")

    conn.commit()
    conn.close()
    print("\n🎉  Migration complete. You can now start the app.")


if __name__ == '__main__':
    run()