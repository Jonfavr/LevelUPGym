# database/db_manager.py
import sqlite3
import hashlib
from datetime import datetime, timedelta
import os


class DatabaseManager:
    """Manages all database operations for LevelUp Gym."""

    def __init__(self, db_name='levelup_gym.db'):
        self.db_name = db_name
        self.conn    = None
        self.cursor  = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def disconnect(self):
        if self.conn:
            self.conn.close()

    # ── Schema creation ───────────────────────────────────────────────────────

    def initialize_database(self):
        """Create all tables and run add_missing_columns for live-DB safety."""
        self.connect()

        # ── Clients ──────────────────────────────────────────────────────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                client_id           INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number        TEXT UNIQUE NOT NULL,
                pin_hash            TEXT NOT NULL,
                first_name          TEXT NOT NULL,
                last_name           TEXT NOT NULL,
                email               TEXT,
                date_of_birth       DATE,
                gender              TEXT,
                registration_date   DATETIME DEFAULT CURRENT_TIMESTAMP,
                status              TEXT DEFAULT 'active',
                profile_photo_path  TEXT,
                fitness_goal        TEXT,
                preferred_split     TEXT
            )
        ''')

        # ── Physical data ─────────────────────────────────────────────────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_physical_data (
                physical_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id           INTEGER NOT NULL,
                height_cm           REAL,
                weight_kg           REAL,
                body_fat_percentage REAL,
                activity            TEXT,
                chest_cm            REAL,
                arms_cm             REAL,
                forearms_cm         REAL,
                waist_cm            REAL,
                hips_cm             REAL,
                thighs_cm           REAL,
                claf_cm             REAL,
                measurement_date    DATE DEFAULT CURRENT_DATE,
                notes               TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
            )
        ''')

        # ── Availability ──────────────────────────────────────────────────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_availability (
                availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id       INTEGER NOT NULL,
                day_of_week     TEXT NOT NULL,
                is_available    BOOLEAN DEFAULT 1,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
                UNIQUE(client_id, day_of_week)
            )
        ''')

        # ── Exercises ─────────────────────────────────────────────────────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercises (
                exercise_id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name                  TEXT UNIQUE NOT NULL,
                description           TEXT,
                exercise_type         TEXT,
                primary_muscle        TEXT,
                complementary_muscle  TEXT,
                target_muscle         TEXT,
                difficulty_level      TEXT,
                base_exp              INTEGER DEFAULT 10,
                image_path            TEXT,
                created_date          DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ── Routines  (all 6 metadata columns included from the start) ────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS routines (
                routine_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                routine_name     TEXT NOT NULL,
                description      TEXT,
                difficulty_level TEXT,
                routine_type     TEXT,
                primary_muscle   TEXT,
                main_class       TEXT,
                created_by       TEXT,
                created_date     DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active        BOOLEAN DEFAULT 1
            )
        ''')

        # ── Routine exercises ─────────────────────────────────────────────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS routine_exercises (
                routine_exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
                routine_id          INTEGER NOT NULL,
                exercise_id         INTEGER NOT NULL,
                sets                INTEGER DEFAULT 3,
                reps                INTEGER DEFAULT 10,
                rest_seconds        INTEGER DEFAULT 60,
                order_position      INTEGER,
                measurement         TEXT DEFAULT 'reps',
                notes               TEXT,
                FOREIGN KEY (routine_id)  REFERENCES routines(routine_id)  ON DELETE CASCADE,
                FOREIGN KEY (exercise_id) REFERENCES exercises(exercise_id) ON DELETE CASCADE
            )
        ''')

        # ── Routine assignments ───────────────────────────────────────────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS routine_assignments (
                assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id     INTEGER NOT NULL,
                routine_id    INTEGER NOT NULL,
                day_of_week   TEXT NOT NULL,
                assigned_date DATE DEFAULT CURRENT_DATE,
                is_active     BOOLEAN DEFAULT 1,
                FOREIGN KEY (client_id)  REFERENCES clients(client_id)  ON DELETE CASCADE,
                FOREIGN KEY (routine_id) REFERENCES routines(routine_id) ON DELETE CASCADE
            )
        ''')

        # ── Workout logs ──────────────────────────────────────────────────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS workout_logs (
                log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id       INTEGER NOT NULL,
                exercise_id     INTEGER NOT NULL,
                workout_date    DATE NOT NULL,
                set_number      INTEGER NOT NULL,
                reps_completed  INTEGER,
                weight_used     REAL,
                exp_earned      INTEGER DEFAULT 0,
                measurement     TEXT DEFAULT 'reps',
                notes           TEXT,
                timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id)  REFERENCES clients(client_id)  ON DELETE CASCADE,
                FOREIGN KEY (exercise_id) REFERENCES exercises(exercise_id) ON DELETE CASCADE
            )
        ''')

        # ── Gamification ──────────────────────────────────────────────────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_gamification (
                gamification_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id               INTEGER UNIQUE NOT NULL,
                current_level           INTEGER DEFAULT 1,
                current_exp             INTEGER DEFAULT 0,
                total_exp               INTEGER DEFAULT 0,
                rank                    TEXT DEFAULT 'E',
                client_class            TEXT,
                class_unlocked_at_level INTEGER,
                current_streak          INTEGER DEFAULT 0,
                longest_streak          INTEGER DEFAULT 0,
                total_reps              INTEGER DEFAULT 0,
                workouts_completed      INTEGER DEFAULT 0,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
            )
        ''')

        # ── Attendance ────────────────────────────────────────────────────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id      INTEGER NOT NULL,
                check_in_date  DATE NOT NULL,
                check_in_time  TIME,
                check_out_time TIME,
                exp_earned     INTEGER DEFAULT 0,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
                UNIQUE(client_id, check_in_date)
            )
        ''')

        # ── Streaks ───────────────────────────────────────────────────────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_streaks (
                streak_id           INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id           INTEGER UNIQUE NOT NULL,
                current_streak      INTEGER DEFAULT 0,
                longest_streak      INTEGER DEFAULT 0,
                last_attendance_date DATE,
                streak_multiplier   REAL DEFAULT 1.0,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
            )
        ''')

        # ── Physical tests ────────────────────────────────────────────────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS physical_tests (
                test_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name        TEXT UNIQUE NOT NULL,
                description      TEXT,
                measurement_unit TEXT,
                ranking_criteria TEXT
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                result_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id    INTEGER NOT NULL,
                test_id      INTEGER NOT NULL,
                test_date    DATE NOT NULL,
                score        REAL NOT NULL,
                rank_achieved TEXT,
                notes        TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
                FOREIGN KEY (test_id)   REFERENCES physical_tests(test_id) ON DELETE CASCADE
            )
        ''')

        # ── Achievements ──────────────────────────────────────────────────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                achievement_name  TEXT UNIQUE NOT NULL,
                description       TEXT,
                achievement_type  TEXT,
                requirement_value INTEGER,
                exp_reward        INTEGER DEFAULT 0,
                icon_path         TEXT
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_achievements (
                client_achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id             INTEGER NOT NULL,
                achievement_id        INTEGER NOT NULL,
                unlocked_date         DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id)      REFERENCES clients(client_id)      ON DELETE CASCADE,
                FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id) ON DELETE CASCADE,
                UNIQUE(client_id, achievement_id)
            )
        ''')

        # ── Memberships ───────────────────────────────────────────────────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_memberships (
                membership_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id        INTEGER NOT NULL,
                start_date       DATE NOT NULL,
                end_date         DATE NOT NULL,
                status           TEXT DEFAULT 'active',
                renewal_count    INTEGER DEFAULT 0,
                last_renewal_date DATE,
                notes            TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
            )
        ''')

        # ── Admin users ───────────────────────────────────────────────────────
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name     TEXT NOT NULL,
                role          TEXT DEFAULT 'staff',
                is_active     BOOLEAN DEFAULT 1,
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()
        self._initialize_default_data()
        self.disconnect()

        # Patch any live DB that was created before these columns existed
        self.add_missing_columns()
        print("✅ Database initialized successfully!")

    def _initialize_default_data(self):
        """Insert default data."""
        tests = [
            ('Push-ups',  'Upper body strength test',  'repetitions', 'Chest, shoulders, triceps'),
            ('Squats',    'Lower body strength test',   'repetitions', 'Legs, glutes'),
            ('Sit-ups',   'Core endurance test',        'repetitions', 'Abdomen'),
            ('High Jump', 'Leg power test',             'centimeters', 'Explosive leg power'),
            ('Sprint',    'Cardiovascular test',        'seconds',     'Speed and endurance'),
        ]
        for t in tests:
            try:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO physical_tests
                        (test_name, description, measurement_unit, ranking_criteria)
                    VALUES (?, ?, ?, ?)
                ''', t)
            except Exception:
                pass

        # Default superadmin
        try:
            default_pw = hashlib.sha256(b'admin123').hexdigest()
            self.cursor.execute('''
                INSERT OR IGNORE INTO admin_users (username, password_hash, full_name, role)
                VALUES ('admin', ?, 'Administrator', 'superadmin')
            ''', (default_pw,))
        except Exception:
            pass

        self.conn.commit()

    # ── Live-DB migration ─────────────────────────────────────────────────────

    def add_missing_columns(self):
        """
        Safely add any columns that may be missing from a live database.
        Runs after every initialize_database() call — completely idempotent.
        """
        self.connect()
        try:
            def _add(table, col, col_type, default=None):
                self.cursor.execute(f"PRAGMA table_info({table})")
                existing = {row["name"] for row in self.cursor.fetchall()}
                if col not in existing:
                    sql = f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"
                    if default is not None:
                        sql += f" DEFAULT {default}"
                    self.cursor.execute(sql)
                    print(f"🆕 Added '{col}' to '{table}'")

            # routines — auto-assign metadata
            _add("routines", "difficulty_level", "TEXT")
            _add("routines", "routine_type",     "TEXT")
            _add("routines", "primary_muscle",   "TEXT")
            _add("routines", "main_class",       "TEXT")

            # clients — goal / split preference
            _add("clients", "fitness_goal",    "TEXT")
            _add("clients", "preferred_split", "TEXT")

            # client_gamification — leaderboard / streak columns
            _add("client_gamification", "current_streak",     "INTEGER", 0)
            _add("client_gamification", "longest_streak",     "INTEGER", 0)
            _add("client_gamification", "total_reps",         "INTEGER", 0)
            _add("client_gamification", "workouts_completed", "INTEGER", 0)

            # client_physical_data — body composition
            _add("client_physical_data", "activity",    "TEXT")
            _add("client_physical_data", "chest_cm",    "REAL")
            _add("client_physical_data", "arms_cm",     "REAL")
            _add("client_physical_data", "forearms_cm", "REAL")
            _add("client_physical_data", "waist_cm",    "REAL")
            _add("client_physical_data", "hips_cm",     "REAL")
            _add("client_physical_data", "thighs_cm",   "REAL")
            _add("client_physical_data", "claf_cm",     "REAL")

            # exercises — split / muscle columns
            _add("exercises", "primary_muscle",       "TEXT")
            _add("exercises", "complementary_muscle", "TEXT")

            # routine_exercises — measurement column
            _add("routine_exercises", "measurement", "TEXT", "'reps'")

            # workout_logs — measurement column
            _add("workout_logs", "measurement", "TEXT", "'reps'")

            self.conn.commit()

        except Exception as e:
            print(f"❌ add_missing_columns error: {e}")
        finally:
            self.disconnect()

    # ── Utilities ─────────────────────────────────────────────────────────────

    @staticmethod
    def hash_pin(pin):
        return hashlib.sha256(str(pin).encode()).hexdigest()

    def execute_query(self, query, params=None):
        self.connect()
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        results = self.cursor.fetchall()
        self.disconnect()
        return results

    def execute_update(self, query, params=None):
        self.connect()
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        self.conn.commit()
        last_id = self.cursor.lastrowid
        self.disconnect()
        return last_id

    def update_streak(self, client_id):
        """Update client streaks based on attendance and availability."""
        self.connect()
        cursor = self.cursor
        try:
            cursor.execute('''
                SELECT day_of_week FROM client_availability
                WHERE client_id = ? AND is_available = 1
            ''', (client_id,))
            available_days = [row['day_of_week'] for row in cursor.fetchall()]

            if not available_days:
                self.disconnect()
                return {'current_streak': 0, 'longest_streak': 0, 'multiplier': 1.0}

            cursor.execute('''
                SELECT check_in_date FROM attendance
                WHERE client_id = ?
                ORDER BY check_in_date DESC
                LIMIT 60
            ''', (client_id,))
            attendance_dates = {row['check_in_date'] for row in cursor.fetchall()}

            today         = datetime.now().date()
            current_date  = today
            streak        = 0
            longest       = 0
            temp_streak   = 0

            for _ in range(60):
                day_name = current_date.strftime('%A')
                if day_name in available_days:
                    date_str = current_date.strftime('%Y-%m-%d')
                    if date_str in attendance_dates:
                        temp_streak += 1
                        longest = max(longest, temp_streak)
                    else:
                        if current_date < today:
                            temp_streak = 0
                current_date -= timedelta(days=1)

            streak = temp_streak

            if streak >= 30:  multiplier = 2.0
            elif streak >= 14: multiplier = 1.8
            elif streak >= 7:  multiplier = 1.5
            elif streak >= 3:  multiplier = 1.2
            else:              multiplier = 1.0

            check_in_date = today.strftime('%Y-%m-%d')
            cursor.execute('''
                UPDATE client_streaks
                SET current_streak=?, longest_streak=?,
                    last_attendance_date=?, streak_multiplier=?
                WHERE client_id=?
            ''', (streak, longest, check_in_date, multiplier, client_id))
            self.conn.commit()
            self.disconnect()

            return {
                'current_streak': streak,
                'longest_streak': longest,
                'multiplier': multiplier,
                'days_to_next_bonus': 1 if multiplier < 2.0 else 0,
            }
        except Exception as e:
            print(f"update_streak error: {e}")
            self.disconnect()
            return {'current_streak': 0, 'longest_streak': 0, 'multiplier': 1.0}
