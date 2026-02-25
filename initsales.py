# database/init_salespoint.py
from database.db_manager import DatabaseManager

def add_announcements_table(self):
        """Create announcements table if it does not exist yet."""
        self.connect()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                ann_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                body        TEXT    NOT NULL,
                ann_type    TEXT    NOT NULL DEFAULT 'info',
                is_pinned   INTEGER NOT NULL DEFAULT 0,
                expires_at  DATE,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
        self.disconnect()
        print("✅ Announcements table ready.")

add_announcements_table(DatabaseManager)