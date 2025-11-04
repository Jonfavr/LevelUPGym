# controllers/salespoint_controller.py
from datetime import datetime, date, timedelta
from database.db_manager import DatabaseManager
import csv

class SalesPointController:
    def __init__(self):
        self.db = DatabaseManager()

    # ---------- Inventory / Items ----------
    def get_all_items(self):
        """Retorna todos los items de inventario con su stock."""
        query = "SELECT item_id, sku, name, price_cents, stock, description FROM items ORDER BY name"
        rows = self.db.execute_query(query)
        return [dict(r) for r in rows]

    def get_item(self, item_id):
        query = "SELECT item_id, sku, name, price_cents, stock, description FROM items WHERE item_id = ?"
        rows = self.db.execute_query(query, (item_id,))
        return dict(rows[0]) if rows else None

    def add_item(self, sku, name, price_cents, stock=0, description=None):
        """Agrega un item nuevo al inventario."""
        query = """
            INSERT INTO items (sku, name, price_cents, stock, description, created_at)
            VALUES (?, ?, ?, ?, ?, DATE('now'))
        """
        self.db.execute_update(query, (sku, name, price_cents, stock, description))
        return {"success": True}

    def update_stock(self, item_id, new_stock):
        query = "UPDATE items SET stock = ? WHERE item_id = ?"
        self.db.execute_update(query, (new_stock, item_id))
        return {"success": True}

    def change_stock_delta(self, item_id, delta):
        """Suma o resta stock (delta puede ser negativo)."""
        query = "UPDATE items SET stock = stock + ? WHERE item_id = ?"
        self.db.execute_update(query, (delta, item_id))
        return {"success": True}

    # ---------- Sales ----------
    def create_sale(self, cashier_id, cart_items, payment_type, paid_amount_cents):
        """
        Registra una venta:
        - cashier_id: id del admin/cajero que procesa la venta (nullable)
        - cart_items: lista de {'item_id': int, 'qty': int, 'price_cents': int}
        - payment_type: 'cash' or 'card'
        - paid_amount_cents: total pagado en centavos (para calcular cambio)
        """
        if not cart_items:
            return {"success": False, "message": "Carrito vacío"}

        # calcular total
        total_cents = sum(int(it['price_cents']) * int(it['qty']) for it in cart_items)

        # Inicia transacción: insertar sale, sale_items y actualizar stock
        try:
            self.db.connect()
            # insertar venta
            insert_sale = """
                INSERT INTO sales (cashier_id, total_cents, payment_type, paid_cents, change_cents, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            change_cents = int(paid_amount_cents) - int(total_cents)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.cursor.execute(insert_sale, (cashier_id, total_cents, payment_type, paid_amount_cents, change_cents, now))
            sale_id = self.db.cursor.lastrowid

            # insertar items vendidos y decrementar stock
            insert_item = """
                INSERT INTO sale_items (sale_id, item_id, qty, price_cents)
                VALUES (?, ?, ?, ?)
            """
            update_stock = "UPDATE items SET stock = stock - ? WHERE item_id = ?"

            for it in cart_items:
                item_id = int(it['item_id'])
                qty = int(it['qty'])
                price = int(it['price_cents'])
                self.db.cursor.execute(insert_item, (sale_id, item_id, qty, price))
                self.db.cursor.execute(update_stock, (qty, item_id))

            self.db.conn.commit()
            return {"success": True, "sale_id": sale_id, "total_cents": total_cents, "change_cents": change_cents}
        except Exception as e:
            self.db.conn.rollback()
            return {"success": False, "message": f"DB error: {e}"}
        finally:
            self.db.disconnect()

    def get_sales_today(self):
        """Lista ventas del día para mostrar historial rápido en admin."""
        today = date.today().strftime("%Y-%m-%d")
        q = """
            SELECT s.sale_id, s.created_at, s.total_cents, s.payment_type, s.paid_cents,
                   s.change_cents, s.cashier_id,
                   GROUP_CONCAT(si.item_id || ':' || si.qty, '|') AS items
            FROM sales s
            LEFT JOIN sale_items si ON s.sale_id = si.sale_id
            WHERE date(s.created_at) = ?
            GROUP BY s.sale_id
            ORDER BY s.created_at DESC
        """
        rows = self.db.execute_query(q, (today,))
        records = []
        for r in rows:
            rec = dict(r)
            rec['total'] = rec['total_cents'] / 100.0
            rec['paid'] = rec['paid_cents'] / 100.0
            rec['change'] = rec['change_cents'] / 100.0
            records.append(rec)
        return records

    def get_sale_detail(self, sale_id):
        q = """
            SELECT si.item_id, i.name, si.qty, si.price_cents
            FROM sale_items si
            JOIN items i ON si.item_id = i.item_id
            WHERE si.sale_id = ?
        """
        rows = self.db.execute_query(q, (sale_id,))
        return [dict(r) for r in rows]

    def get_sales_report(self, period="daily"):
        """Return sales records for a given period: daily, weekly, or monthly.
        Works with `created_at` datetime column (format: YYYY-MM-DD HH:MM:SS)."""
        today = date.today()

        if period == "daily":
            start_date = today
        elif period == "weekly":
            start_date = today - timedelta(days=today.weekday())
        elif period == "monthly":
            start_date = today.replace(day=1)
        else:
            raise ValueError("Invalid period: choose daily, weekly, or monthly")

        # Usa created_time si tu tabla lo tiene con ese nombre
        query = """
            SELECT s.sale_id,
                   s.total_cents,
                   s.payment_type,
                   s.paid_cents,
                   s.change_cents,
                   s.created_at
            FROM sales s
            WHERE DATE(s.created_at) >= ?
            ORDER BY s.created_at DESC
        """

        rows = self.db.execute_query(query, (start_date.strftime("%Y-%m-%d"),))
        records = []
        total_cents = 0

        for r in rows:
            created_at = r["created_at"] if "created_at" in r.keys() else ""
            sale_date, sale_time = "", ""
            if created_at:
                try:
                    dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                    sale_date = dt.strftime("%Y-%m-%d")
                    sale_time = dt.strftime("%H:%M:%S")
                except Exception:
                    parts = created_at.split(" ")
                    if len(parts) >= 2:
                        sale_date, sale_time = parts[0], parts[1]
                    else:
                        sale_date = created_at

            rec = {
                "sale_id": r["sale_id"],
                "sale_date": sale_date,
                "sale_time": sale_time,
                "payment_type": r["payment_type"] if "payment_type" in r.keys() else "",
                "total_cents": r["total_cents"] if "total_cents" in r.keys() else 0,
                "paid_cents": r["paid_cents"] if "paid_cents" in r.keys() else 0,
                "change_cents": r["change_cents"] if "change_cents" in r.keys() else 0,
            }

            total_cents += int(rec["total_cents"] or 0)
            records.append(rec)

        report = {
            "period": period.capitalize(),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "total_sales": total_cents / 100.0,
            "total_cents": total_cents,
            "records": records,
        }
        return report

    def export_sales_report_csv(self, period="daily", output_path=None):
        """Export sales report to CSV file (returns path)."""
        report = self.get_sales_report(period)

        if not output_path:
            output_path = f"sales_report_{period}_{date.today().strftime('%Y%m%d')}.csv"

        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Sale ID", "Date", "Time",
                "Payment Method", "Total ($)", "Paid ($)", "Change ($)"
            ])
            for row in report["records"]:
                writer.writerow([
                    row["sale_id"],
                    row["sale_date"],
                    row["sale_time"],
                    (row["payment_type"] or "").capitalize(),
                    "%.2f" % (int(row["total_cents"]) / 100.0),
                    "%.2f" % (int(row["paid_cents"]) / 100.0),
                    "%.2f" % (int(row["change_cents"]) / 100.0),
                ])
            writer.writerow([])
            writer.writerow(["", "", "", "TOTAL", "%.2f" % report["total_sales"]]), ""

        return output_path