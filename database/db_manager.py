# database/db_manager.py
import sqlite3
import hashlib
from datetime import datetime, timedelta
import os

class DatabaseManager:
    """Manages all database operations for LevelUp Gym"""
    
    def __init__(self, db_name='levelup_gym.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self.cursor = self.conn.cursor()
        
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def initialize_database(self):
        """Create all necessary tables"""
        self.connect()
        
        # Clients table - core personal information
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                client_id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT UNIQUE NOT NULL,
                pin_hash TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT,
                date_of_birth DATE,
                gender TEXT,
                registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                profile_photo_path TEXT
            )
        ''')
        
        # Physical data table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_physical_data (
                physical_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                height_cm REAL,
                weight_kg REAL,
                body_fat_percentage REAL,
                measurement_date DATE DEFAULT CURRENT_DATE,
                notes TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
            )
        ''')
        
        # Availability table - days client can train
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_availability (
                availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                day_of_week TEXT NOT NULL,
                is_available BOOLEAN DEFAULT 1,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
                UNIQUE(client_id, day_of_week)
            )
        ''')
        
        # Gamification - levels and experience
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_gamification (
                gamification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER UNIQUE NOT NULL,
                current_level INTEGER DEFAULT 1,
                current_exp INTEGER DEFAULT 0,
                total_exp INTEGER DEFAULT 0,
                rank TEXT DEFAULT 'E',
                client_class TEXT,
                class_unlocked_at_level INTEGER,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
            )
        ''')
        
        # Attendance and streaks
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                check_in_date DATE NOT NULL,
                check_in_time TIME,
                check_out_time TIME,
                exp_earned INTEGER DEFAULT 0,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
                UNIQUE(client_id, check_in_date)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_streaks (
                streak_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER UNIQUE NOT NULL,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_attendance_date DATE,
                streak_multiplier REAL DEFAULT 1.0,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
            )
        ''')
        
        # Exercises table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercises (
                exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                exercise_type TEXT,
                target_muscle TEXT,
                difficulty_level TEXT,
                base_exp INTEGER DEFAULT 10,
                image_path TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Routines table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS routines (
                routine_id INTEGER PRIMARY KEY AUTOINCREMENT,
                routine_name TEXT NOT NULL,
                description TEXT,
                created_by TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Routine exercises - links exercises to routines
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS routine_exercises (
                routine_exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
                routine_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                sets INTEGER DEFAULT 3,
                reps INTEGER DEFAULT 10,
                rest_seconds INTEGER DEFAULT 60,
                order_position INTEGER,
                notes TEXT,
                FOREIGN KEY (routine_id) REFERENCES routines(routine_id) ON DELETE CASCADE,
                FOREIGN KEY (exercise_id) REFERENCES exercises(exercise_id) ON DELETE CASCADE
            )
        ''')
        
        # Routine assignments - which client gets which routine on which day
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS routine_assignments (
                assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                routine_id INTEGER NOT NULL,
                day_of_week TEXT NOT NULL,
                assigned_date DATE DEFAULT CURRENT_DATE,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
                FOREIGN KEY (routine_id) REFERENCES routines(routine_id) ON DELETE CASCADE
            )
        ''')
        
        # Workout logs - actual performance data
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS workout_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                workout_date DATE NOT NULL,
                set_number INTEGER NOT NULL,
                reps_completed INTEGER,
                weight_used REAL,
                exp_earned INTEGER DEFAULT 0,
                notes TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
                FOREIGN KEY (exercise_id) REFERENCES exercises(exercise_id) ON DELETE CASCADE
            )
        ''')
        
        # Physical tests
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS physical_tests (
                test_id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT UNIQUE NOT NULL,
                description TEXT,
                measurement_unit TEXT,
                ranking_criteria TEXT
            )
        ''')
        
        # Test results
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                test_id INTEGER NOT NULL,
                test_date DATE NOT NULL,
                score REAL NOT NULL,
                rank_achieved TEXT,
                notes TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
                FOREIGN KEY (test_id) REFERENCES physical_tests(test_id) ON DELETE CASCADE
            )
        ''')
        
        # Achievements
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                achievement_name TEXT UNIQUE NOT NULL,
                description TEXT,
                achievement_type TEXT,
                requirement_value INTEGER,
                exp_reward INTEGER DEFAULT 0,
                icon_path TEXT
            )
        ''')
        
        # Client achievements - unlocked achievements
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_achievements (
                client_achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                achievement_id INTEGER NOT NULL,
                unlocked_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
                FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id) ON DELETE CASCADE,
                UNIQUE(client_id, achievement_id)
            )
        ''')

        # Memberships table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_memberships (
                membership_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status TEXT DEFAULT 'active',  -- active | expired | cancelled
                renewal_count INTEGER DEFAULT 0,
                last_renewal_date DATE,
                notes TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
            )
        ''')
                
        self.conn.commit()
        self._initialize_default_data()
        self.disconnect()
        print("✅ Database initialized successfully!")
        
    def _initialize_default_data(self):
        """Insert default data for physical tests"""
        tests = [
            ('Push-ups', 'Upper body strength test', 'repetitions', 'Chest, shoulders, triceps'),
            ('Squats', 'Lower body strength test', 'repetitions', 'Legs, glutes'),
            ('Sit-ups', 'Core endurance test', 'repetitions', 'Abdomen'),
            ('High Jump', 'Leg power test', 'centimeters', 'Explosive leg power'),
            ('Sprint', 'Cardiovascular test', 'seconds', 'Speed and endurance')
        ]
        
        for test in tests:
            try:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO physical_tests (test_name, description, measurement_unit, ranking_criteria)
                    VALUES (?, ?, ?, ?)
                ''', test)
            except:
                pass
        
        self.conn.commit()

    def add_missing_columns(self):
        """Add missing leaderboard and streak columns if they don't exist"""
        self.connect()
        try:
            # Get all current columns in client_gamification
            self.cursor.execute("PRAGMA table_info(client_gamification)")
            existing_columns = [row["name"] for row in self.cursor.fetchall()]

            # Helper: adds column only if it doesn’t exist
            def add_column_if_missing(column_name, column_type, default_value=None):
                if column_name not in existing_columns:
                    print(f"🆕 Adding column '{column_name}' to client_gamification...")
                    if default_value is not None:
                        self.cursor.execute(
                            f"ALTER TABLE client_gamification ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
                        )
                    else:
                        self.cursor.execute(
                            f"ALTER TABLE client_gamification ADD COLUMN {column_name} {column_type}"
                        )

            # Add new leaderboard-related columns
            add_column_if_missing("current_streak", "INTEGER", 0)
            add_column_if_missing("longest_streak", "INTEGER", 0)
            add_column_if_missing("total_reps", "INTEGER", 0)
            add_column_if_missing("workouts_completed", "INTEGER", 0)

            self.conn.commit()
            print("✅ Columns verified and added successfully (if missing).")
        except Exception as e:
            print("❌ Error while adding missing columns:", e)
        finally:
            self.disconnect()
    
    @staticmethod
    def hash_pin(pin):
        """Create secure hash of PIN"""
        return hashlib.sha256(pin.encode()).hexdigest()
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        self.connect()
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        results = self.cursor.fetchall()
        self.disconnect()
        return results
    
    def execute_update(self, query, params=None):
        """Execute an insert/update/delete query"""
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
            # 1️⃣ Get client's available days (Mon, Tue, etc.)
            cursor.execute("""
                SELECT day_of_week
                FROM client_availability
                WHERE client_id = ? AND is_available = 1
            """, (client_id,))
            available_days = [row["day_of_week"] for row in cursor.fetchall()]

            # 2️⃣ Get last attendance info
            cursor.execute("""
                SELECT last_attendance_date, current_streak, longest_streak
                FROM client_streaks
                WHERE client_id = ?
            """, (client_id,))
            streak_data = cursor.fetchone()

            today = datetime.now().date()
            today_day = today.strftime("%A")  # e.g., 'Monday'

            if not streak_data:
                # First check-in ever for this client
                cursor.execute("""
                    INSERT INTO client_streaks (client_id, current_streak, longest_streak, last_attendance_date)
                    VALUES (?, 1, 1, ?)
                """, (client_id, today))
                print(f"🎉 First streak entry created for client {client_id}")
            else:
                last_date = (
                    datetime.strptime(streak_data["last_attendance_date"], "%Y-%m-%d").date()
                    if streak_data["last_attendance_date"] else None
                )
                current_streak = streak_data["current_streak"]
                longest_streak = streak_data["longest_streak"]

                # 3️⃣ Determine streak continuation
                if last_date:
                    days_difference = (today - last_date).days

                    # If consecutive day or missed non-training days only
                    if days_difference == 1 or (
                        days_difference > 1 and self._only_missed_rest_days(last_date, today, available_days)
                    ):
                        current_streak += 1
                    else:
                        current_streak = 1  # missed a training day → reset
                else:
                    current_streak = 1  # no previous record

                # Update longest streak
                if current_streak > longest_streak:
                    longest_streak = current_streak

                # 4️⃣ Update streaks table
                cursor.execute("""
                    UPDATE client_streaks
                    SET current_streak = ?, longest_streak = ?, last_attendance_date = ?
                    WHERE client_id = ?
                """, (current_streak, longest_streak, today, client_id))

                # 5️⃣ Also mirror to client_gamification
                cursor.execute("""
                    UPDATE client_gamification
                    SET current_streak = ?, longest_streak = ?
                    WHERE client_id = ?
                """, (current_streak, longest_streak, client_id))

            self.conn.commit()
            print(f"🔥 Streak updated for client {client_id}: {current_streak} days")

        except Exception as e:
            print(f"❌ Error updating streak for client {client_id}: {e}")
        finally:
            self.disconnect()


    def _only_missed_rest_days(self, last_date, today, available_days):
        """Check if all missed days were rest days (not in availability)."""
        missed_days = []
        day_iter = last_date
        while day_iter < today:
            day_iter += timedelta(days=1)
            missed_days.append(day_iter.strftime("%A"))
        # Return True if all missed days are NOT available training days
        return all(day not in available_days for day in missed_days)


# Usage example
if __name__ == "__main__":
    db = DatabaseManager()
    db.initialize_database()
    db.add_missing_columns()
