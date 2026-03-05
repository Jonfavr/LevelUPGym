# models/routine.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from models.exercise_model import Exercise


class Routine:
    """Routine model — represents a workout routine."""

    def __init__(self, routine_id=None, routine_name=None, description=None,
                 difficulty_level='beginner', routine_type='Full Body',
                 primary_muscle=None, main_class=None,
                 created_by=None, is_active=True):
        self.routine_id       = routine_id
        self.routine_name     = routine_name
        self.description      = description
        self.difficulty_level = difficulty_level
        self.routine_type     = routine_type
        self.primary_muscle   = primary_muscle
        self.main_class       = main_class
        self.created_by       = created_by
        self.is_active        = is_active
        self.created_date     = None
        self.exercises        = []

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def save(self):
        """Insert a new routine into the database."""
        db = DatabaseManager()
        self.routine_id = db.execute_update('''
            INSERT INTO routines
                (routine_name, description, difficulty_level, routine_type,
                 primary_muscle, main_class, created_by, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ''', (self.routine_name, self.description,
              self.difficulty_level, self.routine_type,
              self.primary_muscle,   self.main_class,
              self.created_by))
        return self.routine_id

    def update(self):
        """Update all fields of an existing routine."""
        db = DatabaseManager()
        db.execute_update('''
            UPDATE routines
            SET routine_name=?, description=?, difficulty_level=?, routine_type=?,
                primary_muscle=?, main_class=?, created_by=?, is_active=?
            WHERE routine_id=?
        ''', (self.routine_name, self.description,
              self.difficulty_level, self.routine_type,
              self.primary_muscle,   self.main_class,
              self.created_by,       self.is_active,
              self.routine_id))

    def delete(self):
        """Delete routine and all associated exercises."""
        db = DatabaseManager()
        db.execute_update('DELETE FROM routines WHERE routine_id=?', (self.routine_id,))

    # ── Exercise management ───────────────────────────────────────────────────

    def add_exercise(self, exercise_id, sets=3, reps=10, rest_seconds=60,
                     order_position=None, measurement=None):
        """Add an exercise to this routine."""
        db = DatabaseManager()
        if order_position is None:
            result = db.execute_query(
                'SELECT MAX(order_position) as max_pos FROM routine_exercises WHERE routine_id=?',
                (self.routine_id,)
            )
            max_pos = result[0]['max_pos'] if result and result[0]['max_pos'] else 0
            order_position = max_pos + 1

        return db.execute_update('''
            INSERT INTO routine_exercises
                (routine_id, exercise_id, sets, reps, rest_seconds, order_position, measurement)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (self.routine_id, exercise_id, sets, reps, rest_seconds,
              order_position, measurement))

    def remove_exercise(self, routine_exercise_id):
        """Remove an exercise from this routine."""
        db = DatabaseManager()
        db.connect()
        db.cursor.execute(
            'DELETE FROM routine_exercises WHERE routine_exercise_id = ?',
            (routine_exercise_id,)
        )
        db.conn.commit()
        db.disconnect()
        return {'success': True, 'message': 'Exercise removed successfully.'}

    def delete_routine_exercise(self, routine_exercise_id):
        """Alias kept for backward-compat with existing routes."""
        return self.remove_exercise(routine_exercise_id)

    def update_exercise(self, routine_exercise_id, sets=None, reps=None,
                        rest_seconds=None, measurement=None):
        """Update sets/reps/rest for an exercise slot in this routine."""
        db = DatabaseManager()
        db.connect()
        db.cursor.execute('''
            UPDATE routine_exercises
            SET sets=?, reps=?, rest_seconds=?, measurement=?
            WHERE routine_exercise_id=?
        ''', (sets, reps, rest_seconds, measurement, routine_exercise_id))
        db.conn.commit()
        db.disconnect()
        return {'success': True, 'message': 'Exercise updated successfully.'}

    def get_exercises(self):
        """Return the ordered list of exercises in this routine."""
        db = DatabaseManager()
        results = db.execute_query('''
            SELECT re.routine_exercise_id, re.exercise_id,
                   re.sets, re.reps, re.rest_seconds, re.order_position, re.measurement,
                   e.name, e.description, e.exercise_type,
                   e.primary_muscle, e.complementary_muscle,
                   e.base_exp, e.image_path
            FROM routine_exercises re
            JOIN exercises e ON re.exercise_id = e.exercise_id
            WHERE re.routine_id = ?
            ORDER BY re.order_position
        ''', (self.routine_id,))

        self.exercises = [
            {
                'routine_exercise_id': row['routine_exercise_id'],
                'exercise_id':         row['exercise_id'],
                'name':                row['name'],
                'description':         row['description'],
                'exercise_type':       row['exercise_type'],
                'primary_muscle':      row['primary_muscle'],
                'complementary_muscle':row['complementary_muscle'],
                'base_exp':            row['base_exp'],
                'image_path':          row['image_path'],
                'sets':                row['sets'],
                'reps':                row['reps'],
                'rest_seconds':        row['rest_seconds'],
                'order_position':      row['order_position'],
                'measurement':         row['measurement'],
            }
            for row in results
        ]
        return self.exercises

    def calculate_total_exp(self):
        if not self.exercises:
            self.get_exercises()
        return sum(ex['base_exp'] * ex['sets'] for ex in self.exercises)

    # ── Assignment helpers ────────────────────────────────────────────────────

    def assign_to_client(self, client_id, day_of_week):
        """Assign this routine to a client for a specific day."""
        db = DatabaseManager()
        existing = db.execute_query('''
            SELECT assignment_id FROM routine_assignments
            WHERE client_id=? AND day_of_week=? AND is_active=1
        ''', (client_id, day_of_week))

        if existing:
            db.execute_update('''
                UPDATE routine_assignments
                SET routine_id=?, assigned_date=CURRENT_DATE
                WHERE assignment_id=?
            ''', (self.routine_id, existing[0]['assignment_id']))
        else:
            db.execute_update('''
                INSERT INTO routine_assignments (client_id, routine_id, day_of_week)
                VALUES (?, ?, ?)
            ''', (client_id, self.routine_id, day_of_week))

    def unassign_from_client(self, client_id, day_of_week):
        db = DatabaseManager()
        db.execute_update('''
            UPDATE routine_assignments SET is_active=0
            WHERE client_id=? AND day_of_week=? AND routine_id=?
        ''', (client_id, day_of_week, self.routine_id))

    # ── Static factory methods ────────────────────────────────────────────────

    @staticmethod
    def _from_row(row):
        """Build a Routine from a DB row, reading all columns safely."""
        def _get(key, default=None):
            try:
                return row[key]
            except (IndexError, KeyError):
                return default

        r = Routine(
            routine_id       = _get('routine_id'),
            routine_name     = _get('routine_name'),
            description      = _get('description'),
            difficulty_level = _get('difficulty_level') or 'beginner',
            routine_type     = _get('routine_type')     or 'Full Body',
            primary_muscle   = _get('primary_muscle'),
            main_class       = _get('main_class'),
            created_by       = _get('created_by'),
            is_active        = _get('is_active', True),
        )
        r.created_date = _get('created_date')
        return r

    @staticmethod
    def get_by_id(routine_id):
        """Retrieve routine by ID (with exercises loaded)."""
        db = DatabaseManager()
        result = db.execute_query(
            'SELECT * FROM routines WHERE routine_id=?', (routine_id,)
        )
        if not result:
            return None
        routine = Routine._from_row(result[0])
        routine.get_exercises()
        return routine

    @staticmethod
    def get_all_active():
        """Return all active routines (no exercises loaded — use for lists)."""
        db = DatabaseManager()
        results = db.execute_query(
            'SELECT * FROM routines WHERE is_active=1 ORDER BY routine_name'
        )
        return [Routine._from_row(row) for row in results]

    @staticmethod
    def swap_exercise(routine_id, old_exercise_id, new_exercise_id):
        """Replace one exercise in a routine, preserving order/sets/reps/rest."""
        db = DatabaseManager()
        exists = db.execute_query('''
            SELECT 1 FROM routine_exercises
            WHERE routine_id=? AND exercise_id=?
        ''', (routine_id, new_exercise_id))
        if exists:
            raise ValueError("Exercise already exists in routine")
        db.execute_update('''
            UPDATE routine_exercises SET exercise_id=?
            WHERE routine_id=? AND exercise_id=?
        ''', (new_exercise_id, routine_id, old_exercise_id))

    @staticmethod
    def get_client_routine_for_day(client_id, day_of_week):
        """Get the active routine assigned to a client for a specific day."""
        db = DatabaseManager()
        result = db.execute_query('''
            SELECT r.* FROM routines r
            JOIN routine_assignments ra ON r.routine_id = ra.routine_id
            WHERE ra.client_id=? AND ra.day_of_week=? AND ra.is_active=1
            LIMIT 1
        ''', (client_id, day_of_week))
        if not result:
            return None
        routine = Routine._from_row(result[0])
        routine.get_exercises()
        return routine

    @staticmethod
    def get_client_weekly_schedule(client_id):
        """Return {day: {routine_id, routine_name, description}} for a client."""
        db = DatabaseManager()
        rows = db.execute_query('''
            SELECT ra.day_of_week, r.routine_id, r.routine_name, r.description
            FROM routine_assignments ra
            JOIN routines r ON ra.routine_id = r.routine_id
            WHERE ra.client_id=? AND ra.is_active=1
        ''', (client_id,))
        return {
            row['day_of_week']: {
                'routine_id':   row['routine_id'],
                'routine_name': row['routine_name'],
                'description':  row['description'],
            }
            for row in rows
        }
