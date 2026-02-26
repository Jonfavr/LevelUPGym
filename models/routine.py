# models/routine.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from models.exercise_model import Exercise

class Routine:
    """Routine model - represents a workout routine"""
    
    def __init__(self, routine_id=None, routine_name=None, description=None,
                 created_by=None, is_active=True):
        self.routine_id = routine_id
        self.routine_name = routine_name
        self.description = description
        self.created_by = created_by
        self.is_active = is_active
        self.created_date = None
        self.exercises = []  # List of routine exercises with sets/reps
    
    def save(self):
        """Save new routine to database"""
        db = DatabaseManager()
        query = '''
            INSERT INTO routines (routine_name, description, created_by, is_active)
            VALUES (?, ?, ?, ?)
        '''
        params = (self.routine_name, self.description, self.created_by, self.is_active)
        self.routine_id = db.execute_update(query, params)
        return self.routine_id
    
    def update(self):
        """Update existing routine"""
        db = DatabaseManager()
        query = '''
            UPDATE routines 
            SET routine_name=?, description=?, created_by=?, is_active=?
            WHERE routine_id=?
        '''
        params = (self.routine_name, self.description, self.created_by, 
                 self.is_active, self.routine_id)
        db.execute_update(query, params)
    
    def delete(self):
        """Delete routine and all associated exercises"""
        db = DatabaseManager()
        query = 'DELETE FROM routines WHERE routine_id=?'
        db.execute_update(query, (self.routine_id,))
    
    def add_exercise(self, exercise_id, sets=3, reps=10, rest_seconds=60, 
                    order_position=None, measurement=None):
        """Add an exercise to this routine"""
        if order_position is None:
            # Get current max position
            db = DatabaseManager()
            query = 'SELECT MAX(order_position) as max_pos FROM routine_exercises WHERE routine_id=?'
            result = db.execute_query(query, (self.routine_id,))
            max_pos = result[0]['max_pos'] if result and result[0]['max_pos'] else 0
            order_position = max_pos + 1
        
        db = DatabaseManager()
        query = '''
            INSERT INTO routine_exercises 
            (routine_id, exercise_id, sets, reps, rest_seconds, order_position, measurement)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        params = (self.routine_id, exercise_id, sets, reps, rest_seconds, 
                 order_position, measurement)
        return db.execute_update(query, params)
    
    def remove_exercise(self, routine_exercise_id):
        """Remove an exercise from this routine"""
        db = DatabaseManager()
        """Remove an exercise from a routine"""
        db.connect()
        db.cursor.execute('DELETE FROM routine_exercises WHERE id = ?', (routine_exercise_id,))
        db.conn.commit()
        db.disconnect()
        return {'success': True, 'message': 'Exercise deleted successfully'}
    
    def update_exercise(self, routine_exercise_id, sets=None, reps=None, 
                       rest_seconds=None, measurement=None):
        """Update sets/reps for an exercise in this routine"""
        db = DatabaseManager()
        
        query = '''
            UPDATE routine_exercises
            SET sets = ?, reps = ?, rest_seconds = ?, measurement = ?
            WHERE routine_exercise_id = ?
        '''
        db.connect()
        db.cursor.execute(query, (sets, reps, rest_seconds, measurement, routine_exercise_id))
        db.conn.commit()
        db.disconnect()
        return {'success': True, 'message': 'Exercise updated successfully'}
    
    def get_exercises(self):
        """Get all exercises in this routine with their parameters"""
        db = DatabaseManager()
        query = '''
            SELECT re.*, e.name, e.description, e.exercise_type, 
                   e.primary_muscle, e.complementary_muscle, e.base_exp, e.image_path
            FROM routine_exercises re
            JOIN exercises e ON re.exercise_id = e.exercise_id
            WHERE re.routine_id=?
            ORDER BY re.order_position
        '''
        results = db.execute_query(query, (self.routine_id,))
        
        exercises = []
        for row in results:
            exercise_data = {
                'routine_exercise_id': row['routine_exercise_id'],
                'exercise_id': row['exercise_id'],
                'name': row['name'],
                'description': row['description'],
                'exercise_type': row['exercise_type'],
                'primary_muscle': row['primary_muscle'],
                'complementary_muscle': row['complementary_muscle'],
                'base_exp': row['base_exp'],
                'image_path': row['image_path'],
                'sets': row['sets'],
                'reps': row['reps'],
                'rest_seconds': row['rest_seconds'],
                'order_position': row['order_position'],
                'measurement': row['measurement']
            }
            exercises.append(exercise_data)
        
        self.exercises = exercises
        return exercises
    
    def assign_to_client(self, client_id, day_of_week):
        """Assign this routine to a client for a specific day"""
        db = DatabaseManager()
        
        # Check if assignment already exists
        query = '''
            SELECT assignment_id FROM routine_assignments 
            WHERE client_id=? AND day_of_week=? AND is_active=1
        '''
        existing = db.execute_query(query, (client_id, day_of_week))
        
        if existing:
            # Update existing assignment
            query = '''
                UPDATE routine_assignments 
                SET routine_id=?, assigned_date=CURRENT_DATE
                WHERE assignment_id=?
            '''
            db.execute_update(query, (self.routine_id, existing[0]['assignment_id']))
        else:
            # Create new assignment
            query = '''
                INSERT INTO routine_assignments (client_id, routine_id, day_of_week)
                VALUES (?, ?, ?)
            '''
            db.execute_update(query, (client_id, self.routine_id, day_of_week))
    
    def unassign_from_client(self, client_id, day_of_week):
        """Remove routine assignment from client"""
        db = DatabaseManager()
        query = '''
            UPDATE routine_assignments 
            SET is_active=0
            WHERE client_id=? AND day_of_week=? AND routine_id=?
        '''
        db.execute_update(query, (client_id, day_of_week, self.routine_id))
    
    @staticmethod
    def get_by_id(routine_id):
        """Retrieve routine by ID"""
        db = DatabaseManager()
        query = 'SELECT * FROM routines WHERE routine_id=?'
        result = db.execute_query(query, (routine_id,))
        
        if result:
            row = result[0]
            routine = Routine(
                routine_id=row['routine_id'],
                routine_name=row['routine_name'],
                description=row['description'],
                created_by=row['created_by'],
                is_active=row['is_active']
            )
            routine.created_date = row['created_date']
            routine.get_exercises()  # Load exercises
            return routine
        return None
    
    @staticmethod
    def swap_exercise(routine_id, old_exercise_id, new_exercise_id):
        """
        Replace one exercise in a routine while preserving order, sets, reps, rest.
        """
        db = DatabaseManager()

        # 🔍 Safety: ensure new exercise is not already in routine
        exists_query = """
            SELECT 1 FROM routine_exercises
            WHERE routine_id = ? AND exercise_id = ?
        """
        exists = db.execute_query(exists_query, (routine_id, new_exercise_id))
        if exists:
            raise ValueError("Exercise already exists in routine")

        # 🔄 Swap exercise (preserves order_position, sets, reps, rest)
        update_query = """
            UPDATE routine_exercises
            SET exercise_id = ?
            WHERE routine_id = ? AND exercise_id = ?
        """

        db.execute_update(update_query, (new_exercise_id, routine_id, old_exercise_id))

    @staticmethod
    def get_all_active():
        """Get all active routines"""
        db = DatabaseManager()
        query = 'SELECT * FROM routines WHERE is_active=1 ORDER BY routine_name'
        results = db.execute_query(query)
        
        routines = []
        for row in results:
            routine = Routine(
                routine_id=row['routine_id'],
                routine_name=row['routine_name'],
                description=row['description'],
                created_by=row['created_by'],
                is_active=row['is_active']
            )
            routine.created_date = row['created_date']
            routines.append(routine)
        
        return routines
    
    @staticmethod
    def get_client_routine_for_day(client_id, day_of_week):
        """Get the routine assigned to a client for a specific day"""
        db = DatabaseManager()
        query = '''
            SELECT r.* FROM routines r
            JOIN routine_assignments ra ON r.routine_id = ra.routine_id
            WHERE ra.client_id=? AND ra.day_of_week=? AND ra.is_active=1
        '''
        result = db.execute_query(query, (client_id, day_of_week))
        
        if result:
            row = result[0]
            routine = Routine(
                routine_id=row['routine_id'],
                routine_name=row['routine_name'],
                description=row['description'],
                created_by=row['created_by'],
                is_active=row['is_active']
            )
            routine.created_date = row['created_date']
            routine.get_exercises()
            return routine
        return None
    
    @staticmethod
    def get_client_weekly_schedule(client_id):
        """Get all routine assignments for a client (weekly schedule)"""
        db = DatabaseManager()
        query = '''
            SELECT ra.day_of_week, r.routine_id, r.routine_name, r.description
            FROM routine_assignments ra
            JOIN routines r ON ra.routine_id = r.routine_id
            WHERE ra.client_id=? AND ra.is_active=1
            ORDER BY 
                CASE ra.day_of_week
                    WHEN 'Monday' THEN 1
                    WHEN 'Tuesday' THEN 2
                    WHEN 'Wednesday' THEN 3
                    WHEN 'Thursday' THEN 4
                    WHEN 'Friday' THEN 5
                    WHEN 'Saturday' THEN 6
                    WHEN 'Sunday' THEN 7
                END
        '''
        results = db.execute_query(query, (client_id,))
        
        schedule = {}
        for row in results:
            schedule[row['day_of_week']] = {
                'routine_id': row['routine_id'],
                'routine_name': row['routine_name'],
                'description': row['description']
            }
        
        return schedule
    
    def calculate_total_exp(self):
        """Calculate total base EXP for completing this routine"""
        if not self.exercises:
            self.get_exercises()
        
        total_exp = 0
        for exercise in self.exercises:
            # Base EXP * sets (simplified calculation)
            total_exp += exercise['base_exp'] * exercise['sets']
        
        return total_exp
    
    def __repr__(self):
        return f"<Routine {self.routine_id}: {self.routine_name}>"


# Example usage and testing
if __name__ == "__main__":
    from database.db_manager import DatabaseManager
    from models.client import Client
    from exercise_model import Exercise, populate_default_exercises
    
    # Initialize database
    db = DatabaseManager()
    db.initialize_database()
    
    # Populate exercises if needed
    if len(Exercise.get_all()) == 0:
        populate_default_exercises()
    
    print("=== Testing Routine System ===\n")
    
    # Create a client for testing
    client = Client(
        phone_number="5559876543",
        first_name="Routine",
        last_name="Tester",
        email="routine@gym.com",
        date_of_birth="1992-03-15"
    )
    client_id = client.save(pin="5678")
    client.set_availability(['Monday', 'Wednesday', 'Friday'])
    print(f"✅ Created test client: {client.full_name}\n")
    
    # Create a Push Day routine
    print("--- Creating Push Day Routine ---")
    push_routine = Routine(
        routine_name="Push Day",
        description="Chest, shoulders, and triceps workout",
        created_by="Admin"
    )
    push_routine.save()
    print(f"✅ Created routine: {push_routine.routine_name}")
    
    # Add exercises to the routine
    bench_press = Exercise.get_by_name("Bench Press")
    push_ups = Exercise.get_by_name("Push-ups")
    overhead_press = Exercise.get_by_name("Overhead Press")
    tricep_dips = Exercise.get_by_name("Tricep Dips")
    
    if bench_press:
        push_routine.add_exercise(bench_press.exercise_id, sets=4, reps=8, rest_seconds=90)
        print(f"  + Added: {bench_press.name} (4x8)")
    
    if push_ups:
        push_routine.add_exercise(push_ups.exercise_id, sets=3, reps=15, rest_seconds=60)
        print(f"  + Added: {push_ups.name} (3x15)")
    
    if overhead_press:
        push_routine.add_exercise(overhead_press.exercise_id, sets=3, reps=10, rest_seconds=75)
        print(f"  + Added: {overhead_press.name} (3x10)")
    
    if tricep_dips:
        push_routine.add_exercise(tricep_dips.exercise_id, sets=3, reps=12, rest_seconds=60)
        print(f"  + Added: {tricep_dips.name} (3x12)")
    
    # Create a Pull Day routine
    print("\n--- Creating Pull Day Routine ---")
    pull_routine = Routine(
        routine_name="Pull Day",
        description="Back and biceps workout",
        created_by="Admin"
    )
    pull_routine.save()
    print(f"✅ Created routine: {pull_routine.routine_name}")
    
    pull_ups = Exercise.get_by_name("Pull-ups")
    bent_row = Exercise.get_by_name("Bent Over Row")
    bicep_curls = Exercise.get_by_name("Bicep Curls")
    
    if pull_ups:
        pull_routine.add_exercise(pull_ups.exercise_id, sets=4, reps=6, rest_seconds=120)
        print(f"  + Added: {pull_ups.name} (4x6)")
    
    if bent_row:
        pull_routine.add_exercise(bent_row.exercise_id, sets=4, reps=10, rest_seconds=90)
        print(f"  + Added: {bent_row.name} (4x10)")
    
    if bicep_curls:
        pull_routine.add_exercise(bicep_curls.exercise_id, sets=3, reps=12, rest_seconds=60)
        print(f"  + Added: {bicep_curls.name} (3x12)")
    
    # Create a Leg Day routine
    print("\n--- Creating Leg Day Routine ---")
    leg_routine = Routine(
        routine_name="Leg Day",
        description="Lower body strength workout",
        created_by="Admin"
    )
    leg_routine.save()
    print(f"✅ Created routine: {leg_routine.routine_name}")
    
    squats = Exercise.get_by_name("Squats")
    lunges = Exercise.get_by_name("Lunges")
    leg_press = Exercise.get_by_name("Leg Press")
    
    if squats:
        leg_routine.add_exercise(squats.exercise_id, sets=4, reps=10, rest_seconds=120)
        print(f"  + Added: {squats.name} (4x10)")
    
    if lunges:
        leg_routine.add_exercise(lunges.exercise_id, sets=3, reps=12, rest_seconds=75)
        print(f"  + Added: {lunges.name} (3x12 each leg)")
    
    if leg_press:
        leg_routine.add_exercise(leg_press.exercise_id, sets=3, reps=15, rest_seconds=90)
        print(f"  + Added: {leg_press.name} (3x15)")
    
    # Assign routines to client
    print("\n--- Assigning Routines to Client ---")
    push_routine.assign_to_client(client_id, "Monday")
    print(f"✅ Assigned {push_routine.routine_name} to Monday")
    
    pull_routine.assign_to_client(client_id, "Wednesday")
    print(f"✅ Assigned {pull_routine.routine_name} to Wednesday")
    
    leg_routine.assign_to_client(client_id, "Friday")
    print(f"✅ Assigned {leg_routine.routine_name} to Friday")
    
    # Get client's weekly schedule
    print("\n--- Client's Weekly Schedule ---")
    schedule = Routine.get_client_weekly_schedule(client_id)
    for day, routine_info in schedule.items():
        print(f"  {day}: {routine_info['routine_name']}")
    
    # Get routine for specific day
    print("\n--- Monday's Routine Details ---")
    monday_routine = Routine.get_client_routine_for_day(client_id, "Monday")
    if monday_routine:
        print(f"Routine: {monday_routine.routine_name}")
        print(f"Description: {monday_routine.description}")
        print(f"Total Base EXP: {monday_routine.calculate_total_exp()}")
        print("\nExercises:")
        for i, ex in enumerate(monday_routine.exercises, 1):
            print(f"  {i}. {ex['name']}")
            print(f"     {ex['sets']} sets × {ex['reps']} reps")
            print(f"     Rest: {ex['rest_seconds']}s")
            print(f"     Primary Muscle: {ex['primary_muscle']}")
            print(f"     Base EXP per set: {ex['base_exp']}")
            print()
    
    # List all routines
    print("--- All Active Routines ---")
    all_routines = Routine.get_all_active()
    for routine in all_routines:
        print(f"  • {routine.routine_name} - {routine.description}")
