# models/client.py
import sys
import os
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager


class Client:
    """Client model — represents a gym member."""

    def __init__(self, client_id=None, phone_number=None, first_name=None,
                 last_name=None, email=None, date_of_birth=None, gender=None,
                 profile_photo_path=None, status='active',
                 fitness_goal=None, preferred_split=None):
        self.client_id          = client_id
        self.phone_number       = phone_number
        self.first_name         = first_name
        self.last_name          = last_name
        self.email              = email
        self.date_of_birth      = date_of_birth
        self.gender             = gender
        self.profile_photo_path = profile_photo_path
        self.status             = status
        self.registration_date  = None

        # Auto-assign fields — stored in DB, loaded via get_by_id
        self.fitness_goal    = fitness_goal
        self.preferred_split = preferred_split

        # Related data (lazily loaded)
        self.physical_data  = None
        self.availability   = []
        self.gamification   = None
        self.streak         = None

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if self.date_of_birth:
            if isinstance(self.date_of_birth, str):
                dob = datetime.strptime(self.date_of_birth, '%Y-%m-%d').date()
            else:
                dob = self.date_of_birth
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return None

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def save(self, pin):
        """Insert a new client and initialise gamification + streak rows."""
        db       = DatabaseManager()
        pin_hash = db.hash_pin(pin)

        self.client_id = db.execute_update('''
            INSERT INTO clients
                (phone_number, pin_hash, first_name, last_name,
                 email, date_of_birth, gender, profile_photo_path, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.phone_number, pin_hash, self.first_name, self.last_name,
              self.email, self.date_of_birth, self.gender,
              self.profile_photo_path, self.status))

        self._initialize_gamification()
        self._initialize_streak()
        return self.client_id

    def update(self):
        """Update existing client, including fitness_goal and preferred_split."""
        db = DatabaseManager()
        db.execute_update('''
            UPDATE clients
            SET phone_number=?, first_name=?, last_name=?, email=?,
                date_of_birth=?, gender=?, profile_photo_path=?, status=?,
                fitness_goal=?, preferred_split=?
            WHERE client_id=?
        ''', (self.phone_number, self.first_name, self.last_name, self.email,
              self.date_of_birth, self.gender, self.profile_photo_path, self.status,
              self.fitness_goal, self.preferred_split,
              self.client_id))

    def delete(self):
        db = DatabaseManager()
        db.execute_update('DELETE FROM clients WHERE client_id=?', (self.client_id,))

    # ── Physical data ─────────────────────────────────────────────────────────

    def add_or_update_physical_data(self, height_cm, weight_kg, body_fat_percentage,
                                    activity=None, chest_cm=None, arms_cm=None,
                                    forearms_cm=None, waist_cm=None, hips_cm=None,
                                    thighs_cm=None, claf_cm=None, notes=None):
        db       = DatabaseManager()
        existing = db.execute_query(
            'SELECT physical_id FROM client_physical_data WHERE client_id=? ORDER BY measurement_date DESC LIMIT 1',
            (self.client_id,)
        )
        if existing:
            db.execute_update('''
                UPDATE client_physical_data
                SET height_cm=?, weight_kg=?, body_fat_percentage=?,
                    activity=?, chest_cm=?, arms_cm=?, forearms_cm=?,
                    waist_cm=?, hips_cm=?, thighs_cm=?, claf_cm=?,
                    notes=?, measurement_date=DATE('now')
                WHERE physical_id=?
            ''', (height_cm, weight_kg, body_fat_percentage,
                  activity, chest_cm, arms_cm, forearms_cm,
                  waist_cm, hips_cm, thighs_cm, claf_cm,
                  notes, existing[0]['physical_id']))
        else:
            db.execute_update('''
                INSERT INTO client_physical_data
                    (client_id, height_cm, weight_kg, body_fat_percentage,
                     activity, chest_cm, arms_cm, forearms_cm,
                     waist_cm, hips_cm, thighs_cm, claf_cm, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.client_id, height_cm, weight_kg, body_fat_percentage,
                  activity, chest_cm, arms_cm, forearms_cm,
                  waist_cm, hips_cm, thighs_cm, claf_cm, notes))

    def get_latest_physical_data(self):
        db     = DatabaseManager()
        result = db.execute_query('''
            SELECT * FROM client_physical_data
            WHERE client_id=? ORDER BY measurement_date DESC LIMIT 1
        ''', (self.client_id,))
        return dict(result[0]) if result else None

    # ── Availability + routines ───────────────────────────────────────────────

    def set_availability(self, days):
        db       = DatabaseManager()
        all_days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
        db.execute_update('DELETE FROM client_availability WHERE client_id=?', (self.client_id,))
        for day in all_days:
            db.execute_update('''
                INSERT INTO client_availability (client_id, day_of_week, is_available)
                VALUES (?, ?, ?)
            ''', (self.client_id, day, 1 if day in days else 0))

    def assign_routine_to_day(self, day, routine_id):
        db = DatabaseManager()
        db.execute_update(
            'DELETE FROM routine_assignments WHERE client_id=? AND day_of_week=?',
            (self.client_id, day)
        )
        if routine_id:
            db.execute_update('''
                INSERT INTO routine_assignments (client_id, routine_id, day_of_week, is_active)
                VALUES (?, ?, ?, 1)
            ''', (self.client_id, routine_id, day))

    def clear_unassigned_days(self, active_days):
        db = DatabaseManager()
        if active_days:
            placeholders = ','.join('?' * len(active_days))
            db.execute_update(
                f'DELETE FROM routine_assignments WHERE client_id=? AND day_of_week NOT IN ({placeholders})',
                (self.client_id, *active_days)
            )
        else:
            db.execute_update(
                'DELETE FROM routine_assignments WHERE client_id=?', (self.client_id,)
            )

    def get_availability(self):
        db      = DatabaseManager()
        results = db.execute_query('''
            SELECT day_of_week FROM client_availability
            WHERE client_id=? AND is_available=1
        ''', (self.client_id,))
        return [row['day_of_week'] for row in results]

    def get_weekly_schedule(self):
        db      = DatabaseManager()
        results = db.execute_query('''
            SELECT ra.day_of_week, r.routine_id, r.routine_name, r.description
            FROM routine_assignments ra
            JOIN routines r ON ra.routine_id = r.routine_id
            WHERE ra.client_id=? AND ra.is_active=1
        ''', (self.client_id,))
        return {row['day_of_week']: dict(row) for row in results}

    # ── Gamification & streaks ────────────────────────────────────────────────

    def _initialize_gamification(self):
        db = DatabaseManager()
        db.execute_update('''
            INSERT INTO client_gamification (client_id, current_level, current_exp, rank)
            VALUES (?, 1, 0, 'E')
        ''', (self.client_id,))

    def _initialize_streak(self):
        db = DatabaseManager()
        db.execute_update('''
            INSERT INTO client_streaks (client_id, current_streak, longest_streak)
            VALUES (?, 0, 0)
        ''', (self.client_id,))

    def get_gamification_data(self):
        db     = DatabaseManager()
        result = db.execute_query(
            'SELECT * FROM client_gamification WHERE client_id=?', (self.client_id,)
        )
        return dict(result[0]) if result else None

    def get_streak_data(self):
        db     = DatabaseManager()
        result = db.execute_query(
            'SELECT * FROM client_streaks WHERE client_id=?', (self.client_id,)
        )
        return dict(result[0]) if result else None

    def get_fitness_goal(self):
        db     = DatabaseManager()
        result = db.execute_query(
            'SELECT fitness_goal FROM clients WHERE client_id=?', (self.client_id,)
        )
        return result[0]['fitness_goal'] if result else None

    def get_preferred_split(self):
        db     = DatabaseManager()
        result = db.execute_query(
            'SELECT preferred_split FROM clients WHERE client_id=?', (self.client_id,)
        )
        return result[0]['preferred_split'] if result else None

    # ── Static factory methods ────────────────────────────────────────────────

    @staticmethod
    def _from_row(row):
        """Build a Client object from a DB row safely."""
        def g(k, d=None):
            try:    return row[k]
            except: return d

        c = Client(
            client_id          = g('client_id'),
            phone_number       = g('phone_number'),
            first_name         = g('first_name'),
            last_name          = g('last_name'),
            email              = g('email'),
            date_of_birth      = g('date_of_birth'),
            gender             = g('gender'),
            profile_photo_path = g('profile_photo_path'),
            status             = g('status', 'active'),
            fitness_goal       = g('fitness_goal'),
            preferred_split    = g('preferred_split'),
        )
        c.registration_date = g('registration_date')
        return c

    @staticmethod
    def get_by_id(client_id):
        db     = DatabaseManager()
        result = db.execute_query('SELECT * FROM clients WHERE client_id=?', (client_id,))
        return Client._from_row(result[0]) if result else None

    @staticmethod
    def get_by_phone(phone_number):
        db     = DatabaseManager()
        result = db.execute_query('SELECT * FROM clients WHERE phone_number=?', (phone_number,))
        return Client._from_row(result[0]) if result else None

    @staticmethod
    def authenticate(phone_number, pin):
        db       = DatabaseManager()
        pin_hash = db.hash_pin(pin)
        result   = db.execute_query(
            'SELECT * FROM clients WHERE phone_number=? AND pin_hash=? AND status="active"',
            (phone_number, pin_hash)
        )
        return Client._from_row(result[0]) if result else None

    @staticmethod
    def get_all_active():
        db      = DatabaseManager()
        results = db.execute_query(
            'SELECT * FROM clients WHERE status="active" ORDER BY last_name, first_name'
        )
        return [Client._from_row(row) for row in results]

    def __repr__(self):
        return f"<Client {self.client_id}: {self.full_name} ({self.phone_number})>"
