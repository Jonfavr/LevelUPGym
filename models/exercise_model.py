# models/exercise_model.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager


class Exercise:
    """Exercise model — represents a single gym exercise."""

    def __init__(self, exercise_id=None, name=None, description=None,
                 exercise_type=None,
                 primary_muscle=None,
                 complementary_muscle=None,
                 # Legacy alias kept so old code that passes target_muscle= still works
                 target_muscle=None,
                 difficulty_level=None, base_exp=10, image_path=None):

        self.exercise_id          = exercise_id
        self.name                 = name
        self.description          = description
        self.exercise_type        = exercise_type
        self.difficulty_level     = difficulty_level
        self.base_exp             = base_exp
        self.image_path           = image_path
        self.created_date         = None

        # New split fields
        self.primary_muscle       = primary_muscle
        self.complementary_muscle = complementary_muscle

        # ── Backwards-compatibility shim ──────────────────────────
        # If only the old target_muscle kwarg was supplied, use its
        # first comma-separated value as primary_muscle.
        if primary_muscle is None and target_muscle:
            parts = [p.strip() for p in target_muscle.split(',') if p.strip()]
            self.primary_muscle       = parts[0] if parts else target_muscle
            self.complementary_muscle = ', '.join(parts[1:]) if len(parts) > 1 else None

    # ── Legacy read-only property so templates/code using
    #    exercise.target_muscle still get something sensible ────────
    @property
    def target_muscle(self):
        if self.complementary_muscle:
            return f"{self.primary_muscle}, {self.complementary_muscle}"
        return self.primary_muscle or ''

    # ─────────────────────────────────────────────────────────────
    #  CRUD
    # ─────────────────────────────────────────────────────────────

    def save(self):
        """Insert new exercise into database."""
        db    = DatabaseManager()
        query = '''
            INSERT INTO exercises
                (name, description, exercise_type,
                 primary_muscle, complementary_muscle,
                 target_muscle,
                 difficulty_level, base_exp, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        # Keep target_muscle in sync so legacy queries don't break
        legacy = self.target_muscle
        params = (
            self.name, self.description, self.exercise_type,
            self.primary_muscle, self.complementary_muscle,
            legacy,
            self.difficulty_level, self.base_exp, self.image_path
        )
        self.exercise_id = db.execute_update(query, params)
        return self.exercise_id

    def update(self):
        """Update existing exercise record."""
        db    = DatabaseManager()
        query = '''
            UPDATE exercises
            SET name=?, description=?, exercise_type=?,
                primary_muscle=?, complementary_muscle=?,
                target_muscle=?,
                difficulty_level=?, base_exp=?, image_path=?
            WHERE exercise_id=?
        '''
        legacy = self.target_muscle
        params = (
            self.name, self.description, self.exercise_type,
            self.primary_muscle, self.complementary_muscle,
            legacy,
            self.difficulty_level, self.base_exp, self.image_path,
            self.exercise_id
        )
        db.execute_update(query, params)

    def delete(self):
        """Delete exercise."""
        db = DatabaseManager()
        db.execute_update('DELETE FROM exercises WHERE exercise_id=?', (self.exercise_id,))

    # ─────────────────────────────────────────────────────────────
    #  FACTORY / SEARCH
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def _from_row(cls, row):
        """Build an Exercise instance from a DB row (sqlite3.Row or dict)."""
        # sqlite3.Row supports key access but not .get() — use this helper
        def _get(key, default=None):
            try:
                return row[key]
            except (IndexError, KeyError):
                return default

        ex = cls(
            exercise_id          = _get('exercise_id'),
            name                 = _get('name'),
            description          = _get('description'),
            exercise_type        = _get('exercise_type'),
            primary_muscle       = _get('primary_muscle') or _get('target_muscle'),
            complementary_muscle = _get('complementary_muscle'),
            difficulty_level     = _get('difficulty_level'),
            base_exp             = _get('base_exp', 10),
            image_path           = _get('image_path'),
        )
        ex.created_date = _get('created_date')
        return ex

    @staticmethod
    def get_all():
        db      = DatabaseManager()
        results = db.execute_query('SELECT * FROM exercises ORDER BY name')
        return [Exercise._from_row(r) for r in results]

    @staticmethod
    def get_by_id(exercise_id):
        db     = DatabaseManager()
        result = db.execute_query('SELECT * FROM exercises WHERE exercise_id=?', (exercise_id,))
        return Exercise._from_row(result[0]) if result else None

    @staticmethod
    def get_by_name(name):
        db     = DatabaseManager()
        result = db.execute_query('SELECT * FROM exercises WHERE name=?', (name,))
        return Exercise._from_row(result[0]) if result else None

    @staticmethod
    def search_by_type(exercise_type):
        db      = DatabaseManager()
        results = db.execute_query(
            'SELECT * FROM exercises WHERE exercise_type=? ORDER BY name',
            (exercise_type,)
        )
        return [Exercise._from_row(r) for r in results]

    @staticmethod
    def search_by_primary_muscle(primary_muscle):
        """Exact match on primary_muscle — used by swap logic."""
        db      = DatabaseManager()
        results = db.execute_query(
            'SELECT * FROM exercises WHERE primary_muscle=? ORDER BY name',
            (primary_muscle,)
        )
        return [Exercise._from_row(r) for r in results]

    @staticmethod
    def search_by_muscle(muscle):
        """Broad search across both muscle fields (for library filtering)."""
        db      = DatabaseManager()
        results = db.execute_query(
            '''SELECT * FROM exercises
               WHERE primary_muscle LIKE ? OR complementary_muscle LIKE ?
               ORDER BY name''',
            (f'%{muscle}%', f'%{muscle}%')
        )
        return [Exercise._from_row(r) for r in results]

    def __repr__(self):
        return f"<Exercise {self.exercise_id}: {self.name} ({self.primary_muscle})>"