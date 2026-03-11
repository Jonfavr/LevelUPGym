# controllers/workout_session_controller.py
"""
🆕 NEW FILE - Workout Session Controller
Manages in-progress workout sessions with progress tracking
"""

import sys
import os
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from models.routine import Routine
from controllers.workout_logger import WorkoutLogger

class WorkoutSessionController:
    """🆕 NEW - Manages workout sessions with progress tracking"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.workout_logger = WorkoutLogger()
        self._initialize_table()  # 🆕 Create new tables
    
    def _initialize_table(self):
        """🆕 NEW - Create workout session tracking tables"""
        with self.db.transaction() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workout_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    routine_id INTEGER NOT NULL,
                    workout_date DATE NOT NULL,
                    status TEXT DEFAULT 'in_progress',
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    total_exp_earned INTEGER DEFAULT 0,
                    FOREIGN KEY (client_id) REFERENCES clients(client_id),
                    FOREIGN KEY (routine_id) REFERENCES routines(routine_id),
                    UNIQUE(client_id, routine_id, workout_date)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workout_set_completions (
                    completion_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    exercise_id INTEGER NOT NULL,
                    set_number INTEGER NOT NULL,
                    reps_completed INTEGER,
                    weight_used REAL,
                    completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES workout_sessions(session_id) ON DELETE CASCADE,
                    FOREIGN KEY (exercise_id) REFERENCES exercises(exercise_id),
                    UNIQUE(session_id, exercise_id, set_number)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_exercise_swaps (
                    swap_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id      INTEGER NOT NULL,
                    old_exercise_id INTEGER NOT NULL,
                    new_exercise_id INTEGER NOT NULL,
                    swapped_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES workout_sessions(session_id) ON DELETE CASCADE,
                    UNIQUE(session_id, old_exercise_id)
                )
            ''')
    
    def start_or_resume_session(self, client_id, routine_id):
        """
        🆕 NEW - Start a new workout session or resume existing one
        Returns: dict with session info and completion status
        """
        today = date.today().strftime('%Y-%m-%d')
        
        # Check for existing session today
        session = self._get_session(client_id, routine_id, today)
        
        if session:
            if session['status'] == 'completed':
                # 🆕 PREVENTS duplicate workouts
                return {
                    'session_exists': True,
                    'status': 'completed',
                    'message': 'Workout already completed today! Take a rest 💪',
                    'session_id': session['session_id'],
                    'completed_at': session['completed_at'],
                    'total_exp': session['total_exp_earned']
                }
            else:
                # 🆕 RESUME in-progress session
                completed_sets = self._get_completed_sets(session['session_id'])
                return {
                    'session_exists': True,
                    'status': 'in_progress',
                    'message': 'Resuming your workout...',
                    'session_id': session['session_id'],
                    'completed_sets': completed_sets,
                    'total_exp': session['total_exp_earned']
                }
        
        # Create new session
        session_id = self.db.execute_update(
            "INSERT INTO workout_sessions (client_id, routine_id, workout_date, status) VALUES (?, ?, ?, 'in_progress')",
            (client_id, routine_id, today)
        )
        
        return {
            'session_exists': False,
            'status': 'new',
            'message': 'New workout started!',
            'session_id': session_id,
            'completed_sets': [],
            'total_exp': 0
        }
    
    def is_set_completed(self, session_id, exercise_id, set_number):
        """🆕 NEW - Check if a specific set is already completed"""
        query = '''
            SELECT 1 FROM workout_set_completions 
            WHERE session_id=? AND exercise_id=? AND set_number=?
        '''
        result = self.db.execute_query(query, (session_id, exercise_id, set_number))
        return len(result) > 0
    
    def mark_set_completed(self, session_id, exercise_id, set_number, reps, weight):
        """🆕 NEW - Mark a set as completed in the session"""
        self.db.execute_update(
            'INSERT OR REPLACE INTO workout_set_completions (session_id, exercise_id, set_number, reps_completed, weight_used) VALUES (?, ?, ?, ?, ?)',
            (session_id, exercise_id, set_number, reps, weight)
        )

    def update_session_exp(self, session_id, exp_amount):
        """🆕 NEW - Add EXP to session total"""
        self.db.execute_update(
            'UPDATE workout_sessions SET total_exp_earned = total_exp_earned + ? WHERE session_id = ?',
            (exp_amount, session_id)
        )

    def complete_session(self, session_id):
        """🆕 NEW - Mark session as completed (locks workout)"""
        self.db.execute_update(
            "UPDATE workout_sessions SET status='completed', completed_at=CURRENT_TIMESTAMP WHERE session_id=?",
            (session_id,)
        )

    def get_session_progress(self, session_id, routine, exercises=None):
        # Get detailed progress for a session. Accepts pre-swapped exercise list.\"\"\"
        if exercises is None:
            exercises = routine.get_exercises()

        total_sets = sum(
            ex['sets'] if isinstance(ex, dict) else ex.sets
            for ex in exercises
        )

        completed_sets = self._get_completed_sets(session_id)
        completed_count = len(completed_sets)

        completion_map = {}
        for comp in completed_sets:
            key = f"{comp['exercise_id']}-{comp['set_number']}"
            completion_map[key] = {
                'reps': comp['reps_completed'],
                'weight': comp['weight_used'],
                'completed_at': comp['completed_at']
            }

        return {
            'total_sets': total_sets,
            'completed_sets': completed_count,
            'completion_percentage': (completed_count / total_sets * 100) if total_sets > 0 else 0,
            'completion_map': completion_map
        }
    
    def get_session_by_id(self, session_id):
        query = """
            SELECT *
            FROM workout_sessions
            WHERE session_id = ?
        """
        rows = self.db.execute_query(query, (session_id,))
        return rows[0] if rows else None

    def get_weight_recommendation(self, client_id, exercise_id, session_id):
        """
        Smart weight recommendation system
        Uses:
        1. Previous sets in this session (priority)
        2. Routine-specific target reps (linked via session → routine)
        3. Historical data fallback

        Logic:
        - Fetch routine_id from workout_sessions
        - Get target reps from routine_exercises (specific to that routine)
        - Compare performed reps with target ±3 range
        - Suggest increase / decrease / maintain weight
        """
        # 1️. Get routine_id linked to this session
        routine_query = '''
            SELECT routine_id 
            FROM workout_sessions
            WHERE session_id = ?
            LIMIT 1
        '''
        routine_result = self.db.execute_query(routine_query, (session_id,))
        routine_id = routine_result[0]['routine_id'] if routine_result else None

        if not routine_id:
            # Fallback to historical data if no routine linked
            return self.workout_logger.get_recommended_weight(client_id, exercise_id)

        # 2️ Get last logged set from this session
        query = '''
            SELECT weight_used, reps_completed
            FROM workout_set_completions
            WHERE session_id = ? AND exercise_id = ?
            ORDER BY set_number DESC
            LIMIT 1
        '''
        result = self.db.execute_query(query, (session_id, exercise_id))

        if not result or result[0]['weight_used'] is None:
            # No set logged yet → fallback
            return self.workout_logger.get_recommended_weight(client_id, exercise_id)

        last_weight = result[0]['weight_used']
        last_reps = result[0]['reps_completed']

        # 3️ Fetch the target reps for this specific exercise in this routine
        target_query = '''
            SELECT reps 
            FROM routine_exercises
            WHERE routine_id = ? AND exercise_id = ?
            LIMIT 1
        '''
        target_result = self.db.execute_query(target_query, (routine_id, exercise_id))
        target_reps = target_result[0]['reps'] if target_result else 10  # default safe value

        # 4️ Intelligent feedback logic
        lower_bound = target_reps - 3
        upper_bound = target_reps + 3

        if last_reps > upper_bound:
            recommended = last_weight * 1.1  # 10% increase
            suggestion = 'increase'
            message = f"💪 Strong! Increase weight for the next set."
        elif last_reps < lower_bound:
            recommended = last_weight * 0.9  # 10% decrease
            suggestion = 'decrease'
            message = f"⚖️ Heavy! Decrease weight for the next set."
        else:
            recommended = last_weight
            suggestion = 'maintain'
            message = f"✅ Perfect! Keep that weight."

        return {
            'recommended_weight': round(recommended, 1),
            'suggestion': suggestion,
            'message': message,
            'based_on': 'current_session',
            'target_reps': target_reps,
            'performed_reps': last_reps
        }
    
    def _get_session(self, client_id, routine_id, workout_date):
        """Get session for specific date"""
        query = '''
            SELECT * FROM workout_sessions 
            WHERE client_id=? AND routine_id=? AND workout_date=?
        '''
        result = self.db.execute_query(query, (client_id, routine_id, workout_date))
        return dict(result[0]) if result else None
    
    def _get_completed_sets(self, session_id):
        """Get all completed sets for a session"""
        query = '''
            SELECT * FROM workout_set_completions 
            WHERE session_id=?
            ORDER BY exercise_id, set_number
        '''
        results = self.db.execute_query(query, (session_id,))
        return [dict(row) for row in results]
    
    def check_and_complete_session(self, session_id, routine_id):
        """Checks if all sets are done; marks as completed if so"""
        routine = Routine.get_by_id(routine_id)
        progress = self.get_session_progress(session_id, routine)
        if progress['completion_percentage'] >= 100:
            self.complete_session(session_id)
            return True
        return False
    
    def save_session_swap(self, session_id, old_exercise_id, new_exercise_id):
        # Record a per-session exercise swap (never touches routine_exercises).
        self.db.execute_update(
            'INSERT OR REPLACE INTO session_exercise_swaps (session_id, old_exercise_id, new_exercise_id) VALUES (?, ?, ?)',
            (session_id, old_exercise_id, new_exercise_id)
        )

    def get_session_swaps(self, session_id):
        # Return {old_exercise_id: new_exercise_id} for a session.\"\"\"
        rows = self.db.execute_query(
            'SELECT old_exercise_id, new_exercise_id FROM session_exercise_swaps WHERE session_id = ?',
            (session_id,)
        )
        return {row['old_exercise_id']: row['new_exercise_id'] for row in rows}
    