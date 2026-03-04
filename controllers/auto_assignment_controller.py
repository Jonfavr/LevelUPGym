# controllers/auto_assignment_controller.py
"""
Auto-Assignment Controller
─────────────────────────
Automatically assigns routines to clients based on:
  1. fitness_goal  → suggests a split template
  2. preferred_split → admin can override the suggestion
  3. difficulty     → derived from the client's current gamification level
  4. availability   → maps the split template onto the client's actual training days
"""

from database.db_manager import DatabaseManager


# ─────────────────────────────────────────────────────────────────────────────
# SPLIT TEMPLATES
# Each key is a template slug. Each inner dict maps number-of-days → ordered
# list of routine_type values that will be assigned to the client's days.
# ─────────────────────────────────────────────────────────────────────────────
SPLIT_TEMPLATES = {

    'balanced': {
        'label':       'Balanced / PPL',
        'description': 'Classic Push-Pull-Legs split. Great all-around program.',
        'icon':        'fa-scale-balanced',
        1: ['Full Body'],
        2: ['Full Body', 'Full Body'],
        3: ['Push', 'Pull', 'Legs'],
        4: ['Push', 'Pull', 'Legs', 'Full Body'],
        5: ['Push', 'Pull', 'Legs', 'Upper', 'Lower'],
        6: ['Push', 'Pull', 'Legs', 'Push', 'Pull', 'Cardio'],
        7: ['Push', 'Pull', 'Legs', 'Push', 'Pull', 'Cardio', 'Full Body'],
    },

    'bro_split': {
        'label':       'Bro Split',
        'description': 'One muscle group per day. Maximum volume per body part.',
        'icon':        'fa-dumbbell',
        1: ['Full Body'],
        2: ['Upper', 'Lower'],
        3: ['Chest', 'Back', 'Legs'],
        4: ['Chest', 'Back', 'Legs', 'Shoulders'],
        5: ['Chest', 'Back', 'Legs', 'Shoulders', 'Arms'],
        6: ['Chest', 'Back', 'Legs', 'Shoulders', 'Arms', 'Core'],
        7: ['Chest', 'Back', 'Legs', 'Shoulders', 'Arms', 'Core', 'Full Body'],
    },

    'cardio_focus': {
        'label':       'Cardio Focus',
        'description': 'Prioritises cardio sessions with supporting strength work.',
        'icon':        'fa-heart-pulse',
        1: ['Cardio'],
        2: ['Cardio', 'Full Body'],
        3: ['Cardio', 'Full Body', 'Cardio'],
        4: ['Cardio', 'Upper', 'Cardio', 'Lower'],
        5: ['Cardio', 'Push', 'Cardio', 'Pull', 'Legs'],
        6: ['Cardio', 'Push', 'Cardio', 'Pull', 'Legs', 'Cardio'],
        7: ['Cardio', 'Push', 'Cardio', 'Pull', 'Legs', 'Cardio', 'Core'],
    },

    'legs_focus': {
        'label':       'Legs Focus',
        'description': 'Extra leg days for athletes or clients targeting lower body.',
        'icon':        'fa-person-running',
        1: ['Legs'],
        2: ['Legs', 'Upper'],
        3: ['Legs', 'Upper', 'Legs'],
        4: ['Legs', 'Push', 'Legs', 'Pull'],
        5: ['Legs', 'Push', 'Legs', 'Pull', 'Legs'],
        6: ['Legs', 'Push', 'Legs', 'Pull', 'Legs', 'Core'],
        7: ['Legs', 'Push', 'Legs', 'Pull', 'Legs', 'Core', 'Cardio'],
    },

    'upper_focus': {
        'label':       'Upper Body Focus',
        'description': 'Chest, back, shoulders and arms prioritised.',
        'icon':        'fa-hand-fist',
        1: ['Upper'],
        2: ['Upper', 'Lower'],
        3: ['Push', 'Pull', 'Upper'],
        4: ['Chest', 'Back', 'Shoulders', 'Arms'],
        5: ['Chest', 'Back', 'Shoulders', 'Arms', 'Lower'],
        6: ['Chest', 'Back', 'Shoulders', 'Arms', 'Lower', 'Core'],
        7: ['Chest', 'Back', 'Shoulders', 'Arms', 'Lower', 'Core', 'Cardio'],
    },

    'strength': {
        'label':       'Strength / Powerlifting',
        'description': 'Heavy compound movements. Upper / Lower frequency focus.',
        'icon':        'fa-weight-hanging',
        1: ['Full Body'],
        2: ['Lower', 'Upper'],
        3: ['Lower', 'Upper', 'Full Body'],
        4: ['Lower', 'Upper', 'Lower', 'Upper'],
        5: ['Lower', 'Upper', 'Lower', 'Upper', 'Full Body'],
        6: ['Push', 'Pull', 'Legs', 'Push', 'Pull', 'Legs'],
        7: ['Push', 'Pull', 'Legs', 'Push', 'Pull', 'Legs', 'Core'],
    },

    'full_body_only': {
        'label':       'Full Body Only',
        'description': 'Every session is a full body workout. Best for beginners.',
        'icon':        'fa-person',
        1: ['Full Body'],
        2: ['Full Body', 'Full Body'],
        3: ['Full Body', 'Full Body', 'Full Body'],
        4: ['Full Body', 'Full Body', 'Full Body', 'Full Body'],
        5: ['Full Body', 'Full Body', 'Full Body', 'Full Body', 'Cardio'],
        6: ['Full Body', 'Full Body', 'Full Body', 'Full Body', 'Cardio', 'Core'],
        7: ['Full Body', 'Full Body', 'Full Body', 'Full Body', 'Cardio', 'Core', 'Full Body'],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# GOAL → SUGGESTED TEMPLATE
# When a fitness_goal is saved on a client, this mapping drives the
# automatic suggestion. The admin can always override it.
# ─────────────────────────────────────────────────────────────────────────────
GOAL_TO_TEMPLATE = {
    'Lose Weight':       'cardio_focus',
    'Build Muscle':      'bro_split',
    'General Fitness':   'balanced',
    'Improve Strength':  'strength',
    'Athletic':          'balanced',
    'Tone Up':           'full_body_only',
    'Leg Development':   'legs_focus',
    'Upper Body':        'upper_focus',
}

# All available fitness goals (used to populate dropdowns)
ALL_GOALS = list(GOAL_TO_TEMPLATE.keys())


def suggest_template_for_goal(goal: str) -> str:
    """Return the suggested split template slug for a given fitness goal."""
    return GOAL_TO_TEMPLATE.get(goal, 'balanced')


def get_difficulty_from_level(level: int) -> str:
    """Map gamification level → difficulty string."""
    if level <= 5:
        return 'beginner'
    elif level <= 12:
        return 'intermediate'
    return 'advanced'


# ─────────────────────────────────────────────────────────────────────────────
# CONTROLLER
# ─────────────────────────────────────────────────────────────────────────────
class AutoAssignmentController:

    def __init__(self):
        self.db = DatabaseManager()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _get_client_level(self, client_id: int) -> int:
        rows = self.db.execute_query(
            'SELECT current_level FROM client_gamification WHERE client_id = ?',
            (client_id,)
        )
        return dict(rows[0])['current_level'] if rows else 1

    def _get_client_availability(self, client_id: int) -> list:
        rows = self.db.execute_query(
            'SELECT day_of_week FROM client_availability WHERE client_id = ? AND is_available = 1',
            (client_id,)
        )
        return [dict(r)['day_of_week'] for r in rows]

    def _get_client_meta(self, client_id: int) -> dict:
        """Return fitness_goal and preferred_split for a client."""
        rows = self.db.execute_query(
            'SELECT fitness_goal, preferred_split FROM clients WHERE client_id = ?',
            (client_id,)
        )
        return dict(rows[0]) if rows else {}

    def _find_routine(self, difficulty: str, routine_type: str) -> dict | None:
        """
        Find a matching routine by difficulty + type.
        Falls back to type-only if no exact match exists.
        Uses RANDOM() so clients with the same profile get variety.
        """
        # Exact match
        rows = self.db.execute_query(
            '''SELECT routine_id, routine_name FROM routines
               WHERE is_active = 1
                 AND difficulty_level = ?
                 AND routine_type     = ?
               ORDER BY RANDOM() LIMIT 1''',
            (difficulty, routine_type)
        )
        if rows:
            return dict(rows[0])

        # Fallback: relax difficulty
        rows = self.db.execute_query(
            '''SELECT routine_id, routine_name FROM routines
               WHERE is_active = 1 AND routine_type = ?
               ORDER BY RANDOM() LIMIT 1''',
            (routine_type,)
        )
        return dict(rows[0]) if rows else None

    def _upsert_assignment(self, client_id: int, day: str, routine_id: int):
        """Insert or update a single day's routine assignment."""
        existing = self.db.execute_query(
            '''SELECT assignment_id FROM routine_assignments
               WHERE client_id = ? AND day_of_week = ? AND is_active = 1''',
            (client_id, day)
        )
        if existing:
            self.db.execute_update(
                '''UPDATE routine_assignments
                   SET routine_id = ?, assigned_date = DATE('now')
                   WHERE client_id = ? AND day_of_week = ?''',
                (routine_id, client_id, day)
            )
        else:
            self.db.execute_update(
                '''INSERT INTO routine_assignments
                   (client_id, routine_id, day_of_week, assigned_date, is_active)
                   VALUES (?, ?, ?, DATE('now'), 1)''',
                (client_id, routine_id, day)
            )

    # ── Public API ────────────────────────────────────────────────────────────

    def get_suggestion(self, client_id: int) -> dict:
        """
        Return the suggested template for a client without writing anything.
        Used by the admin UI to show a preview before confirming.
        """
        meta       = self._get_client_meta(client_id)
        goal       = meta.get('fitness_goal') or ''
        suggested  = suggest_template_for_goal(goal)
        override   = meta.get('preferred_split') or None
        active     = override or suggested

        template   = SPLIT_TEMPLATES.get(active, SPLIT_TEMPLATES['balanced'])
        days       = self._get_client_availability(client_id)
        n          = min(len(days), 7)
        split      = template.get(n, template.get(3, ['Full Body']))
        level      = self._get_client_level(client_id)
        difficulty = get_difficulty_from_level(level)

        return {
            'goal':             goal,
            'suggested_template': suggested,
            'active_template':  active,
            'overridden':       override is not None and override != suggested,
            'template_label':   template.get('label', active),
            'difficulty':       difficulty,
            'days':             days,
            'split':            split,   # e.g. ['Push', 'Pull', 'Legs']
        }

    def set_client_goal(self, client_id: int, goal: str,
                        override_split: str | None = None) -> dict:
        """
        Persist the fitness_goal (and optionally a preferred_split override).
        If no override is given, the column is cleared so the suggestion takes over.
        """
        suggested = suggest_template_for_goal(goal)
        split_to_save = override_split if override_split else suggested

        self.db.execute_update(
            '''UPDATE clients
               SET fitness_goal    = ?,
                   preferred_split = ?
               WHERE client_id = ?''',
            (goal, split_to_save, client_id)
        )
        return {
            'success':          True,
            'goal':             goal,
            'suggested':        suggested,
            'preferred_split':  split_to_save,
        }

    def assign_for_client(self, client_id: int,
                          overwrite: bool = False,
                          force_template: str | None = None) -> dict:
        """
        Auto-assign routines for a single client.

        Parameters
        ----------
        overwrite       Clear ALL existing active assignments first.
        force_template  Override both goal suggestion and preferred_split
                        for this single run (useful for 'try this template' preview).
        """
        meta       = self._get_client_meta(client_id)
        goal       = meta.get('fitness_goal') or ''
        suggested  = suggest_template_for_goal(goal)
        preferred  = meta.get('preferred_split') or suggested
        template_slug = force_template or preferred

        template   = SPLIT_TEMPLATES.get(template_slug, SPLIT_TEMPLATES['balanced'])
        days       = self._get_client_availability(client_id)

        if not days:
            return {'success': False, 'message': 'Client has no availability set.'}

        level      = self._get_client_level(client_id)
        difficulty = get_difficulty_from_level(level)

        n     = min(len(days), 7)
        split = template.get(n, template.get(3, ['Full Body'] * n))

        if overwrite:
            self.db.execute_update(
                'UPDATE routine_assignments SET is_active = 0 WHERE client_id = ?',
                (client_id,)
            )

        assigned = []
        warnings = []

        for day, routine_type in zip(days, split):
            routine = self._find_routine(difficulty, routine_type)

            if not routine:
                warnings.append(
                    f'No routine found for {day} ({routine_type} / {difficulty}). '
                    f'Create a routine with this type and difficulty to fill the gap.'
                )
                continue

            self._upsert_assignment(client_id, day, routine['routine_id'])
            assigned.append({
                'day':        day,
                'routine_id': routine['routine_id'],
                'routine':    routine['routine_name'],
                'type':       routine_type,
                'difficulty': difficulty,
            })

        return {
            'success':         True,
            'client_id':       client_id,
            'goal':            goal,
            'template':        template_slug,
            'template_label':  template.get('label', template_slug),
            'difficulty':      difficulty,
            'assigned':        assigned,
            'warnings':        warnings,
        }

    def assign_for_all(self, overwrite: bool = False) -> list:
        """Bulk auto-assign for every active client."""
        rows = self.db.execute_query(
            'SELECT client_id FROM clients WHERE status = "active"'
        )
        return [
            self.assign_for_client(dict(r)['client_id'], overwrite=overwrite)
            for r in rows
        ]

    # ── Utility: data for dropdowns ───────────────────────────────────────────

    @staticmethod
    def get_all_goals() -> list:
        return ALL_GOALS

    @staticmethod
    def get_all_templates() -> list:
        """Return list of {slug, label, description, icon} for UI dropdowns."""
        return [
            {
                'slug':        slug,
                'label':       data['label'],
                'description': data.get('description', ''),
                'icon':        data.get('icon', 'fa-list'),
            }
            for slug, data in SPLIT_TEMPLATES.items()
        ]