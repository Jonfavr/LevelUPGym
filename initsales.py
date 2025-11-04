# database/init_salespoint.py
from database.db_manager import DatabaseManager

def initialize_salespoint_tables():
    db = DatabaseManager()

    db.execute_update('''
        CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            price_cents INTEGER NOT NULL DEFAULT 0, -- almacenamos en centavos para evitar floats
            stock INTEGER NOT NULL DEFAULT 0,
            created_at DATE
        )
    ''')

    db.execute_update('''
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cashier_id INTEGER, -- opcional, referencia a admin user
            total_cents INTEGER NOT NULL,
            payment_type TEXT NOT NULL, -- 'cash'|'card'
            paid_cents INTEGER NOT NULL,
            change_cents INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    db.execute_update('''
        CREATE TABLE IF NOT EXISTS sale_items (
            sale_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            qty INTEGER NOT NULL,
            price_cents INTEGER NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales(sale_id),
            FOREIGN KEY (item_id) REFERENCES items(item_id)
        )
    ''')

    print("✅ Sales Point tables created successfully!")

if __name__ == "__main__":
    initialize_salespoint_tables()
