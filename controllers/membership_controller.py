# controllers/membership_controller.py
from datetime import date, datetime, timedelta
from database.db_manager import DatabaseManager

class MembershipController:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all_memberships(self):
        """Fetch all memberships; auto-create missing ones"""
        clients = self.db.execute_query("SELECT client_id FROM clients")
        for c in clients:
            has_membership = self.db.execute_query(
                "SELECT 1 FROM client_memberships WHERE client_id = ?", (c["client_id"],)
            )
            if not has_membership:
                start = date.today()
                end = start + timedelta(days=30)
                self.db.execute_update('''
                    INSERT INTO client_memberships (client_id, start_date, end_date, status, renewal_count, last_renewal_date, notes)
                    VALUES (?, ?, ?, 'active', 0, ?, 'Auto-created')
                ''', (c["client_id"], start, end, start))

        # Now fetch full membership list
        query = """
            SELECT 
                m.membership_id, m.client_id,
                c.first_name || ' ' || c.last_name AS full_name,
                m.start_date, m.end_date, m.status,
                m.renewal_count,
                ROUND(JULIANDAY(m.end_date) - JULIANDAY(DATE('now'))) AS days_remaining
            FROM client_memberships m
            JOIN clients c ON m.client_id = c.client_id
            ORDER BY m.end_date ASC
        """
        results = self.db.execute_query(query)
        memberships = [dict(r) for r in results]
        return memberships

    def add_membership(self, client_id, duration_days=30, notes=None):
        """Create a new or renewed membership"""
        start = date.today()
        end = start + timedelta(days=duration_days)

        query = """
            INSERT INTO client_memberships (client_id, start_date, end_date, status, renewal_count, last_renewal_date, notes)
            VALUES (?, ?, ?, 'active', 0, ?, ?)
        """
        self.db.execute_update(query, (client_id, start, end, start, notes))
        return {"success": True, "message": f"Membership created for {client_id} until {end}"}

    def renew_membership(self, membership_id, duration_days=30):
        """Renew membership by extending the end_date"""
        new_end = (date.today() + timedelta(days=duration_days)).strftime("%Y-%m-%d")
        query = """
            UPDATE client_memberships
            SET end_date = ?, status = 'active', renewal_count = renewal_count + 1, last_renewal_date = DATE('now')
            WHERE membership_id = ?
        """
        self.db.execute_update(query, (new_end, membership_id))
        return {"success": True, "message": f"Membership renewed until {new_end}"}

    def update_membership_status(self, membership_id, new_status):
        """Manually update membership status"""
        query = "UPDATE client_memberships SET status = ? WHERE membership_id = ?"
        self.db.execute_update(query, (new_status, membership_id))

    def get_client_membership(self, client_id):
        """Get membership info for a client (for client portal alerts)"""
        query = """
            SELECT * FROM client_memberships
            WHERE client_id = ?
            ORDER BY end_date DESC
            LIMIT 1
        """
        result = self.db.execute_query(query, (client_id,))
        return dict(result[0]) if result else None
