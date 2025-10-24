# models/exercise.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager

class Exercise:
    """Exercise model - represents a gym exercise"""
    
    def __init__(self, exercise_id=None, name=None, description=None,
                 exercise_type=None, target_muscle=None, difficulty_level=None,
                 base_exp=10, image_path=None):
        self.exercise_id = exercise_id
        self.name = name
        self.description = description
        self.exercise_type = exercise_type
        self.target_muscle = target_muscle
        self.difficulty_level = difficulty_level
        self.base_exp = base_exp
        self.image_path = image_path
        self.created_date = None
    
    def save(self):
        """Save new exercise to database"""
        db = DatabaseManager()
        query = '''
            INSERT INTO exercises (name, description, exercise_type, target_muscle, 
                                 difficulty_level, base_exp, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        params = (self.name, self.description, self.exercise_type, self.target_muscle,
                 self.difficulty_level, self.base_exp, self.image_path)
        
        self.exercise_id = db.execute_update(query, params)
        return self.exercise_id
    
    def update(self):
        """Update existing exercise"""
        db = DatabaseManager()
        query = '''
            UPDATE exercises 
            SET name=?, description=?, exercise_type=?, target_muscle=?, 
                difficulty_level=?, base_exp=?, image_path=?
            WHERE exercise_id=?
        '''
        params = (self.name, self.description, self.exercise_type, self.target_muscle,
                 self.difficulty_level, self.base_exp, self.image_path, self.exercise_id)
        
        db.execute_update(query, params)
    
    def delete(self):
        """Delete exercise from database"""
        db = DatabaseManager()
        query = 'DELETE FROM exercises WHERE exercise_id=?'
        db.execute_update(query, (self.exercise_id,))
    
    @staticmethod
    def get_by_id(exercise_id):
        """Retrieve exercise by ID"""
        db = DatabaseManager()
        query = 'SELECT * FROM exercises WHERE exercise_id=?'
        result = db.execute_query(query, (exercise_id,))
        
        if result:
            row = result[0]
            exercise = Exercise(
                exercise_id=row['exercise_id'],
                name=row['name'],
                description=row['description'],
                exercise_type=row['exercise_type'],
                target_muscle=row['target_muscle'],
                difficulty_level=row['difficulty_level'],
                base_exp=row['base_exp'],
                image_path=row['image_path']
            )
            exercise.created_date = row['created_date']
            return exercise
        return None
    
    @staticmethod
    def get_by_name(name):
        """Retrieve exercise by name"""
        db = DatabaseManager()
        query = 'SELECT * FROM exercises WHERE name=?'
        result = db.execute_query(query, (name,))
        
        if result:
            row = result[0]
            exercise = Exercise(
                exercise_id=row['exercise_id'],
                name=row['name'],
                description=row['description'],
                exercise_type=row['exercise_type'],
                target_muscle=row['target_muscle'],
                difficulty_level=row['difficulty_level'],
                base_exp=row['base_exp'],
                image_path=row['image_path']
            )
            exercise.created_date = row['created_date']
            return exercise
        return None
    
    @staticmethod
    def get_all():
        """Get all exercises"""
        db = DatabaseManager()
        query = 'SELECT * FROM exercises ORDER BY name'
        results = db.execute_query(query)
        
        exercises = []
        for row in results:
            exercise = Exercise(
                exercise_id=row['exercise_id'],
                name=row['name'],
                description=row['description'],
                exercise_type=row['exercise_type'],
                target_muscle=row['target_muscle'],
                difficulty_level=row['difficulty_level'],
                base_exp=row['base_exp'],
                image_path=row['image_path']
            )
            exercise.created_date = row['created_date']
            exercises.append(exercise)
        
        return exercises
    
    @staticmethod
    def search_by_type(exercise_type):
        """Search exercises by type"""
        db = DatabaseManager()
        query = 'SELECT * FROM exercises WHERE exercise_type=? ORDER BY name'
        results = db.execute_query(query, (exercise_type,))
        
        exercises = []
        for row in results:
            exercise = Exercise(
                exercise_id=row['exercise_id'],
                name=row['name'],
                description=row['description'],
                exercise_type=row['exercise_type'],
                target_muscle=row['target_muscle'],
                difficulty_level=row['difficulty_level'],
                base_exp=row['base_exp'],
                image_path=row['image_path']
            )
            exercises.append(exercise)
        
        return exercises
    
    @staticmethod
    def search_by_muscle(target_muscle):
        """Search exercises by target muscle"""
        db = DatabaseManager()
        query = 'SELECT * FROM exercises WHERE target_muscle LIKE ? ORDER BY name'
        results = db.execute_query(query, (f'%{target_muscle}%',))
        
        exercises = []
        for row in results:
            exercise = Exercise(
                exercise_id=row['exercise_id'],
                name=row['name'],
                description=row['description'],
                exercise_type=row['exercise_type'],
                target_muscle=row['target_muscle'],
                difficulty_level=row['difficulty_level'],
                base_exp=row['base_exp'],
                image_path=row['image_path']
            )
            exercises.append(exercise)
        
        return exercises
    
    def __repr__(self):
        return f"<Exercise {self.exercise_id}: {self.name} ({self.target_muscle})>"


# Helper function to populate database with common exercises
def populate_default_exercises():
    """Add common gym exercises to database"""
    default_exercises = [
        # Chest exercises
        Exercise(name="Bench Press", description="Classic chest exercise with barbell", 
                exercise_type="strength", target_muscle="Chest, Triceps, Shoulders", 
                difficulty_level="intermediate", base_exp=20),
        Exercise(name="Push-ups", description="Bodyweight chest exercise", 
                exercise_type="strength", target_muscle="Chest, Triceps", 
                difficulty_level="beginner", base_exp=10),
        Exercise(name="Dumbbell Fly", description="Isolation exercise for chest", 
                exercise_type="strength", target_muscle="Chest", 
                difficulty_level="intermediate", base_exp=15),
        
        # Back exercises
        Exercise(name="Pull-ups", description="Upper body pulling exercise", 
                exercise_type="strength", target_muscle="Back, Biceps", 
                difficulty_level="advanced", base_exp=25),
        Exercise(name="Bent Over Row", description="Compound back exercise", 
                exercise_type="strength", target_muscle="Back, Biceps", 
                difficulty_level="intermediate", base_exp=20),
        Exercise(name="Lat Pulldown", description="Machine-based back exercise", 
                exercise_type="strength", target_muscle="Back, Biceps", 
                difficulty_level="beginner", base_exp=15),
        
        # Leg exercises
        Exercise(name="Squats", description="King of leg exercises", 
                exercise_type="strength", target_muscle="Legs, Glutes, Core", 
                difficulty_level="intermediate", base_exp=25),
        Exercise(name="Leg Press", description="Machine-based leg exercise", 
                exercise_type="strength", target_muscle="Legs, Glutes", 
                difficulty_level="beginner", base_exp=15),
        Exercise(name="Lunges", description="Single-leg strength exercise", 
                exercise_type="strength", target_muscle="Legs, Glutes", 
                difficulty_level="intermediate", base_exp=20),
        Exercise(name="Deadlift", description="Full body compound exercise", 
                exercise_type="strength", target_muscle="Back, Legs, Core", 
                difficulty_level="advanced", base_exp=30),
        
        # Shoulder exercises
        Exercise(name="Overhead Press", description="Shoulder strength exercise", 
                exercise_type="strength", target_muscle="Shoulders, Triceps", 
                difficulty_level="intermediate", base_exp=20),
        Exercise(name="Lateral Raise", description="Shoulder isolation exercise", 
                exercise_type="strength", target_muscle="Shoulders", 
                difficulty_level="beginner", base_exp=10),
        
        # Arm exercises
        Exercise(name="Bicep Curls", description="Classic bicep exercise", 
                exercise_type="strength", target_muscle="Biceps", 
                difficulty_level="beginner", base_exp=10),
        Exercise(name="Tricep Dips", description="Bodyweight tricep exercise", 
                exercise_type="strength", target_muscle="Triceps", 
                difficulty_level="intermediate", base_exp=15),
        
        # Core exercises
        Exercise(name="Plank", description="Isometric core exercise", 
                exercise_type="core", target_muscle="Abdomen, Core", 
                difficulty_level="beginner", base_exp=10),
        Exercise(name="Sit-ups", description="Classic abdominal exercise", 
                exercise_type="core", target_muscle="Abdomen", 
                difficulty_level="beginner", base_exp=10),
        Exercise(name="Russian Twist", description="Rotational core exercise", 
                exercise_type="core", target_muscle="Obliques, Core", 
                difficulty_level="intermediate", base_exp=15),
        
        # Cardio exercises
        Exercise(name="Running", description="Cardiovascular endurance", 
                exercise_type="cardio", target_muscle="Legs, Cardiovascular", 
                difficulty_level="beginner", base_exp=20),
        Exercise(name="Cycling", description="Low-impact cardio", 
                exercise_type="cardio", target_muscle="Legs, Cardiovascular", 
                difficulty_level="beginner", base_exp=15),
        Exercise(name="Jump Rope", description="High-intensity cardio", 
                exercise_type="cardio", target_muscle="Full Body, Cardiovascular", 
                difficulty_level="intermediate", base_exp=20),
        Exercise(name="Burpees", description="Full body HIIT exercise", 
                exercise_type="hiit", target_muscle="Full Body", 
                difficulty_level="advanced", base_exp=25),
    ]
    
    for exercise in default_exercises:
        try:
            exercise.save()
            print(f"✅ Added: {exercise.name}")
        except Exception as e:
            print(f"⚠️ Skipped {exercise.name}: {e}")
    
    print(f"\n✅ Default exercises populated!")


# Example usage and testing
if __name__ == "__main__":
    from database.db_manager import DatabaseManager
    
    # Initialize database
    db = DatabaseManager()
    db.initialize_database()
    
    print("=== Populating Exercise Database ===\n")
    populate_default_exercises()
    
    print("\n=== Testing Exercise Model ===\n")
    
    # Get all exercises
    all_exercises = Exercise.get_all()
    print(f"Total exercises in database: {len(all_exercises)}")
    
    # Search by type
    print("\n--- Strength Exercises ---")
    strength = Exercise.search_by_type('strength')
    for ex in strength[:5]:
        print(f"  • {ex.name} - {ex.target_muscle} ({ex.base_exp} EXP)")
    
    # Search by muscle
    print("\n--- Chest Exercises ---")
    chest = Exercise.search_by_muscle('Chest')
    for ex in chest:
        print(f"  • {ex.name} - {ex.description}")
    
    # Get specific exercise
    print("\n--- Exercise Details ---")
    squat = Exercise.get_by_name('Squats')
    if squat:
        print(f"Name: {squat.name}")
        print(f"Type: {squat.exercise_type}")
        print(f"Target: {squat.target_muscle}")
        print(f"Difficulty: {squat.difficulty_level}")
        print(f"Base EXP: {squat.base_exp}")