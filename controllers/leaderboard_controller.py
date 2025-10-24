# controllers/leaderboard_controller.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DatabaseManager

class LeaderboardController:
    """Handles leaderboard rankings for EXP, Reps, and Streaks"""
    def __init__(self):
        self.db = DatabaseManager()

    def get_top_exp(self, limit=10):
        query = """
            SELECT c.client_id, c.first_name || ' ' || c.last_name AS full_name, 
                g.total_exp
            FROM clients c
            JOIN client_gamification g ON c.client_id = g.client_id
            ORDER BY g.total_exp DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (limit,))

    def get_top_reps(self, limit=10):
        query = """
            SELECT c.client_id, c.first_name || ' ' || c.last_name AS full_name,
                   SUM(w.reps_completed) AS total_reps
            FROM clients c
            JOIN workout_logs w ON c.client_id = w.client_id
            GROUP BY c.client_id
            ORDER BY total_reps DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (limit,))

    def get_top_streaks(self, limit=10):
        query = """
            SELECT c.client_id, c.first_name || ' ' || c.last_name AS full_name,
                g.current_streak
            FROM clients c
            JOIN client_gamification g ON c.client_id = g.client_id
            ORDER BY g.current_streak DESC
            LIMIT ?
        """
        result = self.db.execute_query(query, (limit,))
        print(dict(result[0]), dict(result[1]), dict(result[2]) )
        return self.db.execute_query(query, (limit,))
