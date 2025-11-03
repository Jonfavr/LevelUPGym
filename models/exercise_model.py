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
def populate_default_exercises_part1():
    """
    Populate chest, back, shoulders, and arms exercises safely (idempotent).
    Part 1 of 4 for the full exercise import.
    """
    print("=== Populating Default Exercises - Part 1 (Chest, Back, Shoulders, Arms) ===")
    default_exercises = [
        # ===== CHEST =====
        Exercise(
            name="Barbell Bench Press",
            description="Lie on a bench, grip the bar slightly wider than shoulder-width, keep shoulders flat. Lower the bar to mid-chest and press up while maintaining scapular control. Tip: plant feet and drive through the heels for stability.",
            exercise_type="strength",
            target_muscle="Chest, Triceps, Shoulders",
            difficulty_level="intermediate",
            base_exp=20
        ),
        Exercise(
            name="Incline Dumbbell Bench Press",
            description="Set bench to 30–45°, lower dumbbells to upper chest and press up in a controlled arc. Cue: avoid flaring elbows excessively to protect shoulders.",
            exercise_type="strength",
            target_muscle="Upper Chest, Shoulders, Triceps",
            difficulty_level="intermediate",
            base_exp=22
        ),
        Exercise(
            name="Pec Deck",
            description="Sit and place forearms/handles; bring arms together in a controlled arc squeezing the chest at peak contraction. Tip: keep a slight bend in elbows and avoid shrugging shoulders.",
            exercise_type="strength",
            target_muscle="Chest",
            difficulty_level="beginner",
            base_exp=14
        ),
        Exercise(
            name="Cable Crossover",
            description="Stand between two high pulleys, bring handles together in front of chest with a slight forward lean and controlled return. Emphasize constant tension and full range.",
            exercise_type="strength",
            target_muscle="Chest",
            difficulty_level="intermediate",
            base_exp=16
        ),
        Exercise(
            name="Incline Barbell Bench Press",
            description="With bench at incline, lower bar to upper chest then press up while keeping torso stable. Cue: keep ribs down and braced to avoid excessive lumbar extension.",
            exercise_type="strength",
            target_muscle="Upper Chest, Shoulders, Triceps",
            difficulty_level="intermediate",
            base_exp=22
        ),
        Exercise(
            name="Dumbbell Bench Press",
            description="Lie flat, press dumbbells up evenly, and lower under control to chest level. Benefits: improved unilateral control and ROM compared to barbell.",
            exercise_type="strength",
            target_muscle="Chest, Triceps, Shoulders",
            difficulty_level="beginner",
            base_exp=16
        ),
        Exercise(
            name="Dumbbell Fly",
            description="Lie flat, open arms in a wide arc until stretch felt in chest, then bring dumbbells together over chest. Keep slight elbow bend and avoid overstretching.",
            exercise_type="strength",
            target_muscle="Chest",
            difficulty_level="intermediate",
            base_exp=18
        ),
        Exercise(
            name="Incline Dumbbell Fly",
            description="Same as dumbbell fly but on incline bench to target upper chest; control descent to protect the shoulder joint.",
            exercise_type="strength",
            target_muscle="Upper Chest",
            difficulty_level="intermediate",
            base_exp=18
        ),
        Exercise(
            name="Chest Press Machine",
            description="Sit and press handles forward until arms extend, then return under control. Great for beginners to learn pressing mechanics with guided path.",
            exercise_type="strength",
            target_muscle="Chest, Triceps",
            difficulty_level="beginner",
            base_exp=10
        ),
        Exercise(
            name="Barbell Declined Bench Press",
            description="On a decline bench, lower bar to lower chest and press up. Keep a controlled tempo and secure footing on the bench supports.",
            exercise_type="strength",
            target_muscle="Lower Chest, Triceps",
            difficulty_level="intermediate",
            base_exp=18
        ),
        Exercise(
            name="Dumbbell Declined Bench Press",
            description="Decline position with dumbbells; lower toward lower chest and press up keeping wrists neutral to avoid strain.",
            exercise_type="strength",
            target_muscle="Lower Chest, Triceps",
            difficulty_level="intermediate",
            base_exp=18
        ),
        Exercise(
            name="Push Ups",
            description="Hands under shoulders, body straight, lower chest to just above ground and push up. Scale by elevating hands or feet to change difficulty.",
            exercise_type="strength",
            target_muscle="Chest, Triceps, Core",
            difficulty_level="beginner",
            base_exp=12
        ),

        # ===== BACK =====
        Exercise(
            name="Dumbbell Bent-Over Row",
            description="Hinge at hips with slight knee bend, pull dumbbells to your hip/torso and squeeze shoulder blades together. Keep back neutral and avoid rounding.",
            exercise_type="strength",
            target_muscle="Back, Biceps",
            difficulty_level="intermediate",
            base_exp=22
        ),
        Exercise(
            name="Wide-Grip Pulldown",
            description="At lat pulldown machine, grip wide and pull bar to upper chest while keeping torso slightly reclined. Lead with elbows to engage lats.",
            exercise_type="strength",
            target_muscle="Lats, Upper Back, Biceps",
            difficulty_level="beginner",
            base_exp=16
        ),
        Exercise(
            name="Seated Cable Row",
            description="Sit upright, pull handle to abdomen while squeezing shoulder blades together, then extend arms with control.",
            exercise_type="strength",
            target_muscle="Middle Back, Biceps",
            difficulty_level="beginner",
            base_exp=14
        ),
        Exercise(
            name="Close-Grip Pulldown",
            description="Use a narrow handle and pull to upper chest, focusing on contracting the lower lats and keeping torso stable.",
            exercise_type="strength",
            target_muscle="Lats, Biceps",
            difficulty_level="beginner",
            base_exp=14
        ),
        Exercise(
            name="Barbell Row",
            description="Bend at hips, keep back flat, pull barbell to lower ribs and lower slowly. Maintain core bracing to protect the lower back.",
            exercise_type="strength",
            target_muscle="Back, Biceps",
            difficulty_level="intermediate",
            base_exp=24
        ),
        Exercise(
            name="Behind-Neck Pulldown",
            description="Pull the bar behind the neck while maintaining an upright torso; use lighter weights and strict form to protect shoulders.",
            exercise_type="strength",
            target_muscle="Upper Back, Rear Delts",
            difficulty_level="advanced",
            base_exp=28
        ),
        Exercise(
            name="Reverse-Grip Pulldown",
            description="Use an underhand grip to pull the bar down toward the chest to emphasize biceps and lower lats; keep movement controlled.",
            exercise_type="strength",
            target_muscle="Lats, Biceps",
            difficulty_level="intermediate",
            base_exp=20
        ),
        Exercise(
            name="Rope Pulldown",
            description="Use rope attachment and pull down while separating hands at bottom to maximize lat contraction; keep torso still.",
            exercise_type="strength",
            target_muscle="Lats, Upper Back",
            difficulty_level="intermediate",
            base_exp=20
        ),
        Exercise(
            name="T-Bar Rows",
            description="Hinge at hips and row the T-bar to sternum, squeezing the shoulder blades; ensure neutral spine and solid foot placement.",
            exercise_type="strength",
            target_muscle="Middle Back, Lats",
            difficulty_level="intermediate",
            base_exp=22
        ),
        Exercise(
            name="Barbell Bent Over Rows Supinated Grip",
            description="Perform bent-over rows with underhand grip to emphasize lower lats and biceps; keep torso tight and core braced.",
            exercise_type="strength",
            target_muscle="Back, Biceps",
            difficulty_level="intermediate",
            base_exp=22
        ),
        Exercise(
            name="Pull Up",
            description="Hang from bar and pull chest toward bar using lats and arms; progress with bands or negatives if needed.",
            exercise_type="strength",
            target_muscle="Back, Biceps",
            difficulty_level="advanced",
            base_exp=30
        ),
        Exercise(
            name="Behind the Neck Pull Up",
            description="Pull up bringing bar toward the back of the neck; use only if shoulders are flexible and perform with control.",
            exercise_type="strength",
            target_muscle="Back, Rear Delts",
            difficulty_level="advanced",
            base_exp=34
        ),
        Exercise(
            name="Pull Up with a Supinated Grip",
            description="Underhand grip pull-up emphasizing biceps; focus on full range and controlled descent.",
            exercise_type="strength",
            target_muscle="Back, Biceps",
            difficulty_level="advanced",
            base_exp=32
        ),
        Exercise(
            name="Straight Arm Lat Pulldown",
            description="Stand and pull bar/rope with straight arms from overhead down to thighs, focusing on lat stretch and engagement.",
            exercise_type="strength",
            target_muscle="Lats",
            difficulty_level="intermediate",
            base_exp=18
        ),
        Exercise(
            name="Dumbbell Pullover",
            description="Lie on bench holding a dumbbell with both hands, lower it behind head in an arc and bring it back to chest to engage lats and chest.",
            exercise_type="strength",
            target_muscle="Lats, Chest",
            difficulty_level="intermediate",
            base_exp=18
        ),
        Exercise(
            name="Barbell Pullover",
            description="Similar to dumbbell pullover but using barbell or EZ. Keep ribcage stable and hinge from shoulders with a slight bend in elbows.",
            exercise_type="strength",
            target_muscle="Lats, Chest",
            difficulty_level="intermediate",
            base_exp=20
        ),
        Exercise(
            name="Barbell Deadlift",
            description="Stand with bar over mid-foot, hinge at hips, grip bar, and lift by extending hips and knees. Keep the bar close and spine neutral.",
            exercise_type="strength",
            target_muscle="Back, Hamstrings, Glutes",
            difficulty_level="advanced",
            base_exp=38
        ),
        Exercise(
            name="Barbell Sumo Deadlift",
            description="Wide stance deadlift variation with toes out; keep chest up and drive through heels, focusing on hips and quads.",
            exercise_type="strength",
            target_muscle="Glutes, Hamstrings, Quads",
            difficulty_level="advanced",
            base_exp=34
        ),
        Exercise(
            name="Trap Bar Deadlift",
            description="Stand in trap bar, grip handles and lift by driving through heels and hips; often easier on lower back than conventional deadlift.",
            exercise_type="strength",
            target_muscle="Quads, Glutes, Back",
            difficulty_level="advanced",
            base_exp=34
        ),
        Exercise(
            name="Dumbbell Deadlift",
            description="Perform deadlift movement with dumbbells by hinging at hips and keeping weights close to legs; keep core braced.",
            exercise_type="strength",
            target_muscle="Hamstrings, Glutes, Back",
            difficulty_level="intermediate",
            base_exp=22
        ),
        Exercise(
            name="Barbell Shrug",
            description="Hold barbell in front and shrug shoulders up toward ears, pause and lower with control to work traps.",
            exercise_type="strength",
            target_muscle="Traps",
            difficulty_level="beginner",
            base_exp=14
        ),
        Exercise(
            name="Dumbbell Shrugs",
            description="Hold dumbbells at sides and elevate shoulders up toward ears, hold briefly and lower slowly to emphasize traps.",
            exercise_type="strength",
            target_muscle="Traps",
            difficulty_level="beginner",
            base_exp=12
        ),

        # ===== SHOULDERS =====
        Exercise(
            name="Dumbbell Shoulder Press",
            description="Seated or standing, press dumbbells overhead from shoulder height while keeping core tight and spine neutral.",
            exercise_type="strength",
            target_muscle="Shoulders, Triceps",
            difficulty_level="intermediate",
            base_exp=22
        ),
        Exercise(
            name="Dumbbell Lateral Raise",
            description="With slight elbow bend, raise dumbbells to shoulder height and lower slowly—avoid momentum to isolate delts.",
            exercise_type="strength",
            target_muscle="Lateral Deltoids",
            difficulty_level="beginner",
            base_exp=14
        ),
        Exercise(
            name="Dumbbell Front Raise",
            description="Raise one or two dumbbells straight in front to shoulder height with controlled tempo to target front delts.",
            exercise_type="strength",
            target_muscle="Front Deltoids",
            difficulty_level="beginner",
            base_exp=14
        ),
        Exercise(
            name="High Cable Rear Delt Fly",
            description="Set cables high and perform a reverse fly movement to target rear delts; squeeze shoulder blades at peak.",
            exercise_type="strength",
            target_muscle="Rear Deltoids, Upper Back",
            difficulty_level="intermediate",
            base_exp=18
        ),
        Exercise(
            name="Smith Machine Shoulder Press",
            description="Perform overhead presses in the guided Smith path for beginners to learn pressing mechanics safely.",
            exercise_type="strength",
            target_muscle="Shoulders, Triceps",
            difficulty_level="beginner",
            base_exp=16
        ),
        Exercise(
            name="Barbell Upright Row",
            description="Pull barbell up along the body to chest/neck height with elbows high to target traps and shoulders; use moderate weight.",
            exercise_type="strength",
            target_muscle="Traps, Deltoids",
            difficulty_level="intermediate",
            base_exp=18
        ),
        Exercise(
            name="Bent-Over Lateral Raise",
            description="Hinge at hips and raise dumbbells laterally to target rear delts; keep a slight elbow bend and control the descent.",
            exercise_type="strength",
            target_muscle="Rear Deltoids, Upper Back",
            difficulty_level="intermediate",
            base_exp=18
        ),

        # ===== ARMS =====
        Exercise(
            name="Barbell Curl",
            description="Stand with a shoulder-width grip on the barbell and curl up while keeping elbows at sides; lower slowly for tempo.",
            exercise_type="strength",
            target_muscle="Biceps",
            difficulty_level="beginner",
            base_exp=14
        ),
        Exercise(
            name="Alternating Dumbbell Curl",
            description="Curl one dumbbell at a time with full control and no swing, rotating wrist slightly at the top for peak contraction.",
            exercise_type="strength",
            target_muscle="Biceps",
            difficulty_level="beginner",
            base_exp=12
        ),
        Exercise(
            name="Rope Cable Curl",
            description="Attach rope to low pulley and curl using neutral wrist action to emphasize brachialis and forearms.",
            exercise_type="strength",
            target_muscle="Biceps, Forearms",
            difficulty_level="intermediate",
            base_exp=16
        ),
        Exercise(
            name="EZ Barbell Preacher Curl",
            description="Use preacher bench and curl with EZ bar to isolate the biceps while preventing body swing.",
            exercise_type="strength",
            target_muscle="Biceps",
            difficulty_level="intermediate",
            base_exp=18
        ),
        Exercise(
            name="Hammer Curl",
            description="Hold dumbbells with neutral grip and curl, targeting brachialis and forearms with a controlled descent.",
            exercise_type="strength",
            target_muscle="Biceps, Forearms",
            difficulty_level="beginner",
            base_exp=12
        ),
        Exercise(
            name="Incline Dumbbell Curl",
            description="Lie back on an incline bench and curl dumbbells to emphasize long-head biceps stretch and contraction.",
            exercise_type="strength",
            target_muscle="Biceps",
            difficulty_level="intermediate",
            base_exp=18
        ),
        Exercise(
            name="Dumbbell Concentration Curl",
            description="Seated, brace elbow against inner thigh and curl slowly focusing on peak contraction and strict form.",
            exercise_type="strength",
            target_muscle="Biceps",
            difficulty_level="intermediate",
            base_exp=16
        ),
        Exercise(
            name="Triceps Pressdown (Cable Rope Pushdown)",
            description="Attach rope to high pulley and extend elbows to fully contract triceps; keep elbows pinned to sides.",
            exercise_type="strength",
            target_muscle="Triceps",
            difficulty_level="beginner",
            base_exp=12
        ),
        Exercise(
            name="Lying Triceps Extension",
            description="Lying on bench, lower bar/dumbbells toward forehead and extend arms to lockout, using controlled tempo to protect elbows.",
            exercise_type="strength",
            target_muscle="Triceps",
            difficulty_level="intermediate",
            base_exp=18
        ),
        Exercise(
            name="Dumbbell Overhead Triceps Extension",
            description="Seated or standing, hold one or two dumbbells overhead and lower behind head, then extend arms fully focusing on triceps.",
            exercise_type="strength",
            target_muscle="Triceps",
            difficulty_level="intermediate",
            base_exp=18
        ),
        Exercise(
            name="Close Grip Bench Press",
            description="Use a narrower bar grip on bench press to shift emphasis to triceps while keeping elbows tucked.",
            exercise_type="strength",
            target_muscle="Triceps, Chest",
            difficulty_level="intermediate",
            base_exp=20
        ),
        Exercise(
            name="Kickback",
            description="Hinge at hips, upper arm parallel to floor and extend elbow to straighten arm, squeezing the triceps at the top.",
            exercise_type="strength",
            target_muscle="Triceps",
            difficulty_level="beginner",
            base_exp=10
        ),
        Exercise(
            name="Bench Dips",
            description="Place hands on bench, extend legs forward and lower hips toward ground then push back up; bend knees to scale difficulty.",
            exercise_type="functional",
            target_muscle="Triceps, Chest",
            difficulty_level="beginner",
            base_exp=12
        ),
    ]
    print("\n✅ Part 1!")
    for exercise in default_exercises:
        print(f"Name: {exercise.name}")
        print(f"  Type: {exercise.exercise_type}")

def populate_default_exercises_part2():
    """Populate Legs, Glutes, Functional, and Core exercises."""
    db = DatabaseManager()
    default_exercises = [
        # 🦵 LEG & GLUTE EXERCISES
        Exercise(name="Squats", description="Stand with feet shoulder-width apart, lower hips back and down until thighs are parallel to the floor, then drive through heels to stand.", exercise_type="strength", target_muscle="Legs, Glutes, Core", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Front Squat", description="Hold barbell on front shoulders, keep chest up, and squat down maintaining upright posture for quad emphasis.", exercise_type="strength", target_muscle="Legs, Core", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Goblet Squat", description="Hold a dumbbell close to your chest, keep chest upright, squat down until elbows touch knees, then rise.", exercise_type="functional", target_muscle="Legs, Glutes, Core", difficulty_level="beginner", base_exp=15),
        Exercise(name="Sumo Squat", description="Widen stance, toes slightly out, lower hips while keeping chest upright to target inner thighs and glutes.", exercise_type="strength", target_muscle="Legs, Glutes", difficulty_level="beginner", base_exp=15),
        Exercise(name="Jump Squats", description="Perform a regular squat and explode upward, landing softly to absorb impact with bent knees.", exercise_type="power", target_muscle="Legs, Glutes", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Walking Lunges", description="Step forward with one leg, lower your hips until both knees are bent at 90°, push forward to the next rep.", exercise_type="strength", target_muscle="Legs, Glutes", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Reverse Lunges", description="Step backward into a lunge, keeping torso upright, then return to standing by pushing through front leg.", exercise_type="functional", target_muscle="Legs, Glutes", difficulty_level="beginner", base_exp=15),
        Exercise(name="Side Lunges", description="Step laterally, bending one knee while keeping the other leg straight, push back to center to work inner thighs.", exercise_type="functional", target_muscle="Legs, Glutes, Adductors", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Bulgarian Split Squat", description="Elevate one foot behind on a bench, lower into a single-leg squat, then press through the front heel to rise.", exercise_type="strength", target_muscle="Legs, Glutes", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Pistol Squat", description="Balance on one leg, extend the other forward, and slowly lower into a squat before standing back up.", exercise_type="balance", target_muscle="Legs, Glutes, Core", difficulty_level="advanced", base_exp=35),
        Exercise(name="Wall Sit", description="Slide down a wall until knees form 90°, hold position with core tight and back straight.", exercise_type="endurance", target_muscle="Legs, Glutes", difficulty_level="beginner", base_exp=10),
        Exercise(name="Step-Ups", description="Step onto a bench or platform with one foot, drive through the heel, then lower under control.", exercise_type="functional", target_muscle="Legs, Glutes", difficulty_level="beginner", base_exp=15),
        Exercise(name="Leg Press", description="Sit in a leg press machine, push platform upward by extending knees without locking them.", exercise_type="weights", target_muscle="Legs, Glutes", difficulty_level="beginner", base_exp=15),
        Exercise(name="Romanian Deadlift", description="Hold barbell or dumbbells, hinge at hips keeping slight knee bend, lower weight along shins, then extend hips.", exercise_type="strength", target_muscle="Hamstrings, Glutes, Lower Back", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Good Morning", description="With bar on upper back, hinge at hips keeping back straight until torso is parallel to floor, then return upright.", exercise_type="strength", target_muscle="Hamstrings, Glutes, Lower Back", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Glute Bridge", description="Lie on back, bend knees, lift hips by squeezing glutes, hold briefly, then lower slowly.", exercise_type="functional", target_muscle="Glutes, Core", difficulty_level="beginner", base_exp=10),
        Exercise(name="Hip Thrust", description="Place upper back on bench, barbell across hips, and lift hips upward by contracting glutes at the top.", exercise_type="strength", target_muscle="Glutes, Hamstrings", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Cable Kickback", description="Attach ankle strap to cable, kick leg backward while keeping upper body still to isolate glutes.", exercise_type="weights", target_muscle="Glutes", difficulty_level="intermediate", base_exp=15),
        Exercise(name="Donkey Kicks", description="On all fours, drive one heel upward keeping knee bent, squeeze glutes at the top of each rep.", exercise_type="functional", target_muscle="Glutes, Hamstrings", difficulty_level="beginner", base_exp=10),
        Exercise(name="Single-Leg Deadlift", description="Hold dumbbell in one hand, hinge forward balancing on one leg, return upright for glute and hamstring stability.", exercise_type="balance", target_muscle="Hamstrings, Glutes, Core", difficulty_level="intermediate", base_exp=20),

        # ⚙️ FUNCTIONAL MOVEMENTS
        Exercise(name="Push Press", description="Dip slightly and drive the barbell overhead with leg power and shoulder strength.", exercise_type="power", target_muscle="Shoulders, Triceps, Legs", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Clean and Press", description="Lift barbell from floor to shoulders, then press overhead in one fluid motion.", exercise_type="compound", target_muscle="Full Body", difficulty_level="advanced", base_exp=35),
        Exercise(name="Snatch", description="Lift barbell from floor overhead in one motion using explosive power and full-body control.", exercise_type="power", target_muscle="Full Body", difficulty_level="advanced", base_exp=40),
        Exercise(name="Kettlebell Swing", description="Swing kettlebell between legs and up to shoulder height using hip thrusts, keeping back neutral.", exercise_type="functional", target_muscle="Glutes, Hamstrings, Core", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Farmer's Carry", description="Hold heavy dumbbells at sides and walk steadily, keeping core tight and shoulders down.", exercise_type="functional", target_muscle="Forearms, Core, Legs", difficulty_level="intermediate", base_exp=15),
        Exercise(name="Turkish Get-Up", description="Holding a weight overhead, move from lying down to standing while maintaining arm stability.", exercise_type="functional", target_muscle="Full Body, Core", difficulty_level="advanced", base_exp=35),
        Exercise(name="Sled Push", description="Push weighted sled across turf using full-body power and steady leg drive.", exercise_type="power", target_muscle="Legs, Glutes, Core", difficulty_level="advanced", base_exp=30),
        Exercise(name="Battle Ropes", description="Grip ropes and move arms in alternating waves or slams to build endurance and power.", exercise_type="hiit", target_muscle="Arms, Shoulders, Core", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Medicine Ball Slam", description="Raise ball overhead, slam it to the floor with power, catch on rebound and repeat.", exercise_type="power", target_muscle="Full Body", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Explosive Push-Ups", description="Lower chest to floor, push up with enough force for hands to leave the ground briefly.", exercise_type="power", target_muscle="Chest, Triceps, Core", difficulty_level="advanced", base_exp=30),
        Exercise(name="Burpee Box Jump", description="Perform a burpee, then jump onto a sturdy box, land softly and step down.", exercise_type="hiit", target_muscle="Full Body", difficulty_level="advanced", base_exp=35),

        # 💪 CORE EXERCISES
        Exercise(name="Sit-Ups", description="Lie on your back, bend knees, curl torso upward, then slowly lower back down.", exercise_type="core", target_muscle="Abdomen", difficulty_level="beginner", base_exp=10),
        Exercise(name="Crunches", description="Lift shoulders off floor focusing on upper abs while keeping lower back grounded.", exercise_type="core", target_muscle="Abdomen", difficulty_level="beginner", base_exp=10),
        Exercise(name="Plank", description="Hold forearm position with body straight from head to heels and core engaged.", exercise_type="core", target_muscle="Core, Abs, Shoulders", difficulty_level="beginner", base_exp=10),
        Exercise(name="Side Plank", description="Lie on side, support with forearm, lift hips and hold to engage obliques.", exercise_type="core", target_muscle="Obliques, Core", difficulty_level="intermediate", base_exp=15),
        Exercise(name="Mountain Climbers", description="From plank, drive knees alternately toward chest at a quick pace.", exercise_type="hiit", target_muscle="Core, Legs, Shoulders", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Hanging Leg Raise", description="Hang from bar, lift legs straight up to 90°, control on the way down.", exercise_type="core", target_muscle="Abs, Hip Flexors", difficulty_level="advanced", base_exp=25),
        Exercise(name="Russian Twist", description="Sit with knees bent, lean slightly back, rotate torso side to side holding weight.", exercise_type="core", target_muscle="Obliques, Core", difficulty_level="intermediate", base_exp=15),
        Exercise(name="Flutter Kicks", description="Lie flat, lift legs slightly, and alternate small kicks while keeping abs tight.", exercise_type="core", target_muscle="Lower Abs, Core", difficulty_level="beginner", base_exp=10),
        Exercise(name="V-Ups", description="Lie on back, simultaneously lift legs and torso to meet in a V shape.", exercise_type="core", target_muscle="Abs, Core", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Ab Wheel Rollout", description="Kneel and roll ab wheel forward until torso almost touches ground, then pull back with core.", exercise_type="core", target_muscle="Core, Abs, Shoulders", difficulty_level="advanced", base_exp=25),
        Exercise(name="Toe Touches", description="Lie on back, raise legs straight up, reach for toes with controlled crunch.", exercise_type="core", target_muscle="Abs", difficulty_level="beginner", base_exp=10),
        Exercise(name="Jackknife Sit-Up", description="Lie flat, bring arms and legs together in one movement, reaching toward toes.", exercise_type="core", target_muscle="Abs, Core", difficulty_level="intermediate", base_exp=15),
    ]
    print("\n✅ Part 2!")
    for exercise in default_exercises:
        print(f"Name: {exercise.name}")
        print(f"  Type: {exercise.exercise_type}")

def populate_default_exercises_part3():
    """Populate Cardio, HIIT, Mobility, Stability, Speed, and Agility exercises."""
    db = DatabaseManager()
    default_exercises = [
        # 🫀 CARDIO & ENDURANCE EXERCISES
        Exercise(name="Running", description="Run at a steady pace with upright posture and relaxed breathing to build cardiovascular endurance.", exercise_type="cardio", target_muscle="Legs, Cardiovascular System", difficulty_level="beginner", base_exp=20),
        Exercise(name="Jogging", description="Maintain a light running pace for extended periods while keeping steady breathing.", exercise_type="endurance", target_muscle="Legs, Cardiovascular System", difficulty_level="beginner", base_exp=15),
        Exercise(name="Sprinting", description="Run at maximum speed for short distances, keeping arms pumping and core tight.", exercise_type="speed", target_muscle="Legs, Glutes, Core", difficulty_level="advanced", base_exp=30),
        Exercise(name="Cycling", description="Pedal steadily with controlled resistance, maintaining rhythmic breathing and upright posture.", exercise_type="cardio", target_muscle="Legs, Cardiovascular System", difficulty_level="beginner", base_exp=15),
        Exercise(name="Rowing Machine", description="Drive legs, lean back slightly, and pull handle to chest in a smooth motion.", exercise_type="cardio", target_muscle="Back, Legs, Arms, Core", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Elliptical Trainer", description="Move arms and legs in rhythm while maintaining balanced motion for low-impact cardio.", exercise_type="cardio", target_muscle="Full Body, Cardiovascular System", difficulty_level="beginner", base_exp=15),
        Exercise(name="Stair Climb", description="Step up and down stairs or machine with consistent pace and strong drive through heels.", exercise_type="endurance", target_muscle="Legs, Glutes", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Jump Rope", description="Jump lightly over rope, keeping elbows close and rhythm steady for coordination and endurance.", exercise_type="cardio", target_muscle="Full Body, Cardiovascular System", difficulty_level="intermediate", base_exp=20),
        Exercise(name="High Knees", description="Run in place lifting knees to hip height while pumping arms briskly.", exercise_type="hiit", target_muscle="Legs, Core, Cardiovascular System", difficulty_level="beginner", base_exp=15),
        Exercise(name="Butt Kicks", description="Jog in place, kicking heels toward glutes while maintaining fast pace.", exercise_type="hiit", target_muscle="Legs, Cardiovascular System", difficulty_level="beginner", base_exp=10),
        Exercise(name="Box Jumps", description="Jump explosively onto a sturdy box or platform, land softly with knees slightly bent.", exercise_type="power", target_muscle="Legs, Glutes, Core", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Skater Jumps", description="Leap laterally from one leg to the other while maintaining balance and rhythm.", exercise_type="agility", target_muscle="Legs, Glutes, Core", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Jumping Jacks", description="Jump legs apart while raising arms overhead, then return to starting position rhythmically.", exercise_type="cardio", target_muscle="Full Body", difficulty_level="beginner", base_exp=10),
        Exercise(name="Treadmill Incline Walk", description="Walk briskly on an incline to engage glutes and hamstrings while improving endurance.", exercise_type="cardio", target_muscle="Legs, Cardiovascular System", difficulty_level="beginner", base_exp=15),
        Exercise(name="Row Sprints", description="Perform short bursts of powerful rowing with maximum effort and quick recovery.", exercise_type="hiit", target_muscle="Full Body", difficulty_level="advanced", base_exp=30),
        Exercise(name="Battle Rope Alternating Waves", description="Move ropes up and down in alternating fashion using core and arm power.", exercise_type="hiit", target_muscle="Arms, Shoulders, Core", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Burpees", description="Drop into push-up position, perform a push-up, jump up explosively with arms overhead.", exercise_type="hiit", target_muscle="Full Body", difficulty_level="advanced", base_exp=25),
        Exercise(name="Jump Lunges", description="Lunge and explode upward, switching legs mid-air before landing softly.", exercise_type="power", target_muscle="Legs, Glutes", difficulty_level="advanced", base_exp=30),
        Exercise(name="Mountain Climbers", description="From plank, drive knees quickly toward chest, alternating rhythmically.", exercise_type="hiit", target_muscle="Core, Legs, Shoulders", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Speed Skipping", description="Spin rope quickly for double-under repetitions with quick wrist control.", exercise_type="speed", target_muscle="Full Body", difficulty_level="advanced", base_exp=25),

        # ⚡ SPEED & AGILITY TRAINING
        Exercise(name="Cone Sprints", description="Sprint between cones placed at short distances, changing direction rapidly.", exercise_type="agility", target_muscle="Legs, Core", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Ladder Drills", description="Step quickly through agility ladder patterns maintaining fast footwork and precision.", exercise_type="agility", target_muscle="Legs, Core", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Side Shuffles", description="Bend knees slightly and move laterally with quick steps while maintaining athletic stance.", exercise_type="agility", target_muscle="Legs, Core", difficulty_level="beginner", base_exp=15),
        Exercise(name="T-Drill Sprint", description="Sprint forward, shuffle sideways, and backpedal following a T-shaped path.", exercise_type="speed", target_muscle="Legs, Core", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Dot Drills", description="Hop between floor dots in quick succession to improve foot speed and control.", exercise_type="speed", target_muscle="Legs, Core", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Zigzag Runs", description="Sprint around cones set in zigzag pattern for sharp directional control.", exercise_type="agility", target_muscle="Legs, Core", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Sprint Starts", description="Explode forward from crouched start, focusing on reaction and first-step acceleration.", exercise_type="speed", target_muscle="Legs, Glutes", difficulty_level="advanced", base_exp=30),
        Exercise(name="Resisted Sprint", description="Sprint against resistance band or parachute for added power development.", exercise_type="power", target_muscle="Legs, Core", difficulty_level="advanced", base_exp=35),
        Exercise(name="Carioca Drill", description="Cross one foot over the other laterally in quick rhythm for coordination.", exercise_type="agility", target_muscle="Legs, Hips", difficulty_level="intermediate", base_exp=15),
        Exercise(name="Sprint and Backpedal", description="Sprint forward, stop, and backpedal quickly to starting point.", exercise_type="speed", target_muscle="Legs, Core", difficulty_level="intermediate", base_exp=20),

        # 🤸 FLEXIBILITY & MOBILITY
        Exercise(name="Forward Fold Stretch", description="Stand tall, hinge at hips, and reach toward toes for hamstring stretch.", exercise_type="flexibility", target_muscle="Hamstrings, Lower Back", difficulty_level="beginner", base_exp=10),
        Exercise(name="Hip Flexor Stretch", description="Lunge forward on one leg and push hips gently down to stretch hip flexors.", exercise_type="flexibility", target_muscle="Hip Flexors", difficulty_level="beginner", base_exp=10),
        Exercise(name="Shoulder Stretch", description="Pull one arm across chest, using opposite hand for support to loosen shoulders.", exercise_type="flexibility", target_muscle="Shoulders", difficulty_level="beginner", base_exp=10),
        Exercise(name="Quad Stretch", description="Stand tall, pull one ankle toward glutes, keep knees aligned to stretch quadriceps.", exercise_type="flexibility", target_muscle="Quadriceps", difficulty_level="beginner", base_exp=10),
        Exercise(name="Cat-Cow Stretch", description="Alternate arching and rounding spine while on hands and knees for spinal mobility.", exercise_type="mobility", target_muscle="Spine, Core", difficulty_level="beginner", base_exp=10),
        Exercise(name="Torso Twist", description="Stand tall and rotate upper body side to side for spinal mobility.", exercise_type="mobility", target_muscle="Core, Back", difficulty_level="beginner", base_exp=10),
        Exercise(name="World’s Greatest Stretch", description="Step into deep lunge, reach arm upward and rotate torso for full-body mobility.", exercise_type="flexibility", target_muscle="Hips, Hamstrings, Shoulders", difficulty_level="intermediate", base_exp=15),
        Exercise(name="Dynamic Lunges with Twist", description="Perform lunges and twist torso toward front leg for hip and spinal mobility.", exercise_type="mobility", target_muscle="Hips, Core", difficulty_level="intermediate", base_exp=15),
        Exercise(name="Inchworms", description="From standing, walk hands to plank, then walk feet forward, engaging core throughout.", exercise_type="mobility", target_muscle="Hamstrings, Core, Shoulders", difficulty_level="beginner", base_exp=15),
        Exercise(name="Ankle Circles", description="Rotate ankles in both directions to improve joint mobility and prevent injuries.", exercise_type="mobility", target_muscle="Ankles, Calves", difficulty_level="beginner", base_exp=10),
        Exercise(name="Shoulder Dislocates", description="Use band or stick to rotate shoulders overhead and back to improve flexibility.", exercise_type="flexibility", target_muscle="Shoulders, Chest", difficulty_level="intermediate", base_exp=15),
        Exercise(name="Deep Squat Hold", description="Sit in deep squat keeping heels down and chest tall for hip mobility.", exercise_type="mobility", target_muscle="Hips, Ankles", difficulty_level="intermediate", base_exp=15),
        Exercise(name="Cobra Stretch", description="Lie prone, press chest upward with hands to stretch abdominal and spine muscles.", exercise_type="flexibility", target_muscle="Spine, Abdomen", difficulty_level="beginner", base_exp=10),
        Exercise(name="Child’s Pose", description="Kneel on floor, sit back on heels, stretch arms forward to relax back and shoulders.", exercise_type="flexibility", target_muscle="Back, Shoulders", difficulty_level="beginner", base_exp=10),
        Exercise(name="Standing Side Bend", description="Stand tall and lean to each side to stretch obliques and lats.", exercise_type="flexibility", target_muscle="Obliques, Lats", difficulty_level="beginner", base_exp=10),

        # ⚖️ BALANCE & STABILITY
        Exercise(name="Single-Leg Balance", description="Stand on one leg keeping core tight and maintain balance for time.", exercise_type="balance", target_muscle="Legs, Core", difficulty_level="beginner", base_exp=10),
        Exercise(name="Bosu Ball Squat", description="Perform squats on Bosu ball to engage stabilizers and improve balance.", exercise_type="balance", target_muscle="Legs, Core", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Single-Leg Romanian Deadlift", description="Balance on one leg, hinge forward keeping back straight, and return upright.", exercise_type="balance", target_muscle="Glutes, Hamstrings, Core", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Stability Ball Plank", description="Place forearms on ball and hold plank position, maintaining balance and tension.", exercise_type="balance", target_muscle="Core, Shoulders", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Standing Knee Raise Hold", description="Lift one knee to waist height and hold position to engage core and hip flexors.", exercise_type="balance", target_muscle="Core, Hips", difficulty_level="beginner", base_exp=10),
        Exercise(name="Heel-to-Toe Walk", description="Walk in a straight line placing heel directly in front of toes to train balance.", exercise_type="balance", target_muscle="Legs, Core", difficulty_level="beginner", base_exp=10),
        Exercise(name="Balance Board Shift", description="Stand on balance board and shift weight side to side to improve stability.", exercise_type="balance", target_muscle="Core, Ankles, Legs", difficulty_level="intermediate", base_exp=15),
    ]
    print("\n✅ Part 3!")
    for exercise in default_exercises:
        print(f"Name: {exercise.name}")
        print(f"  Type: {exercise.exercise_type}")

def populate_default_exercises_part4():
    """Populate Compound, Machine, Advanced Functional, and Isolation exercises."""
    db = DatabaseManager()
    default_exercises = [
        # 🏋️ COMPOUND & MACHINE STRENGTH
        Exercise(name="Smith Machine Squat", description="Stand under bar on Smith machine, lower hips until thighs are parallel, then drive up through heels.", exercise_type="strength", target_muscle="Legs, Glutes", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Leg Press", description="Push platform away from you with feet shoulder-width apart, keeping knees aligned with toes.", exercise_type="strength", target_muscle="Legs, Glutes", difficulty_level="beginner", base_exp=20),
        Exercise(name="Seated Chest Press Machine", description="Push handles forward while keeping back against pad to target the chest.", exercise_type="strength", target_muscle="Chest, Shoulders, Triceps", difficulty_level="beginner", base_exp=20),
        Exercise(name="Lat Pulldown", description="Pull bar down to upper chest while keeping torso upright and elbows pointing down.", exercise_type="strength", target_muscle="Back, Biceps", difficulty_level="beginner", base_exp=20),
        Exercise(name="Seated Row Machine", description="Pull handles toward torso while squeezing shoulder blades together.", exercise_type="strength", target_muscle="Back, Biceps", difficulty_level="beginner", base_exp=20),
        Exercise(name="Cable Fly", description="From standing, bring cable handles together in front of chest with slight elbow bend.", exercise_type="strength", target_muscle="Chest", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Cable Curl", description="Hold cable bar with underhand grip and curl upward while keeping elbows fixed.", exercise_type="strength", target_muscle="Biceps", difficulty_level="beginner", base_exp=15),
        Exercise(name="Cable Triceps Pushdown", description="Push cable handle downward while keeping elbows close to sides.", exercise_type="strength", target_muscle="Triceps", difficulty_level="beginner", base_exp=15),
        Exercise(name="Cable Lateral Raise", description="Lift cable handle out to side to shoulder height with slight elbow bend.", exercise_type="strength", target_muscle="Shoulders", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Leg Extension Machine", description="Sit and extend legs upward to straighten knees against resistance.", exercise_type="strength", target_muscle="Quadriceps", difficulty_level="beginner", base_exp=15),
        Exercise(name="Lying Leg Curl Machine", description="Curl legs upward toward glutes while keeping hips down on pad.", exercise_type="strength", target_muscle="Hamstrings", difficulty_level="beginner", base_exp=15),
        Exercise(name="Hip Abduction Machine", description="Press legs outward against pads to strengthen hip abductors.", exercise_type="strength", target_muscle="Glutes, Outer Thighs", difficulty_level="beginner", base_exp=15),
        Exercise(name="Hip Adduction Machine", description="Squeeze legs inward against resistance to train inner thighs.", exercise_type="strength", target_muscle="Inner Thighs", difficulty_level="beginner", base_exp=15),
        Exercise(name="Machine Shoulder Press", description="Press handles overhead while maintaining a straight spine and braced core.", exercise_type="strength", target_muscle="Shoulders, Triceps", difficulty_level="beginner", base_exp=20),
        Exercise(name="Incline Chest Press Machine", description="Press handles upward on an incline to target the upper chest.", exercise_type="strength", target_muscle="Chest, Shoulders, Triceps", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Machine Rear Delt Fly", description="Pull handles backward with straight arms to engage rear delts and upper back.", exercise_type="strength", target_muscle="Shoulders, Back", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Hack Squat", description="Position shoulders under pads, lower hips deeply, and push through heels to stand up.", exercise_type="strength", target_muscle="Legs, Glutes", difficulty_level="advanced", base_exp=30),
        Exercise(name="Machine Calf Raise", description="Lift heels upward under load to contract calves fully, then lower slowly.", exercise_type="strength", target_muscle="Calves", difficulty_level="beginner", base_exp=15),

        # 💪 ISOLATION & ACCESSORY WORK
        Exercise(name="Dumbbell Bicep Curl", description="Curl dumbbells upward while keeping elbows close to torso and wrists steady.", exercise_type="strength", target_muscle="Biceps", difficulty_level="beginner", base_exp=15),
        Exercise(name="Concentration Curl", description="Sit, brace elbow on thigh, and curl dumbbell slowly upward for focused contraction.", exercise_type="strength", target_muscle="Biceps", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Triceps Kickback", description="Lean forward, extend dumbbells back by straightening elbows.", exercise_type="strength", target_muscle="Triceps", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Lateral Raise", description="Lift dumbbells out to sides to shoulder height with minimal swing.", exercise_type="strength", target_muscle="Shoulders", difficulty_level="beginner", base_exp=15),
        Exercise(name="Front Raise", description="Lift dumbbells forward to shoulder height with controlled motion.", exercise_type="strength", target_muscle="Shoulders", difficulty_level="beginner", base_exp=15),
        Exercise(name="Rear Delt Raise", description="Hinge forward slightly and lift dumbbells to the sides to hit rear delts.", exercise_type="strength", target_muscle="Shoulders, Upper Back", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Preacher Curl", description="Curl barbell or dumbbell from preacher bench for isolated bicep activation.", exercise_type="strength", target_muscle="Biceps", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Overhead Triceps Extension", description="Hold dumbbell overhead and lower behind head, extending elbows upward.", exercise_type="strength", target_muscle="Triceps", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Cable Face Pull", description="Pull cable toward face with elbows high to strengthen rear delts and traps.", exercise_type="strength", target_muscle="Shoulders, Upper Back", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Incline Dumbbell Curl", description="Perform curls while seated on incline bench to emphasize bicep stretch.", exercise_type="strength", target_muscle="Biceps", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Hammer Curl", description="Hold dumbbells neutral and curl upward to target brachialis and forearms.", exercise_type="strength", target_muscle="Biceps, Forearms", difficulty_level="beginner", base_exp=15),
        Exercise(name="Cable Kickback", description="Attach ankle strap and extend leg backward to engage glutes fully.", exercise_type="strength", target_muscle="Glutes", difficulty_level="beginner", base_exp=15),
        Exercise(name="Machine Crunch", description="Contract abs forward against resistance, keeping movement controlled.", exercise_type="core", target_muscle="Abdominals", difficulty_level="beginner", base_exp=15),
        Exercise(name="Reverse Pec Deck", description="Pull arms outward on machine to target rear delts and upper back.", exercise_type="strength", target_muscle="Shoulders, Back", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Wrist Curl", description="Rest forearms on bench, curl wrists upward to strengthen forearms.", exercise_type="strength", target_muscle="Forearms", difficulty_level="beginner", base_exp=10),
        Exercise(name="Reverse Wrist Curl", description="Hold barbell overhand and curl wrists upward for forearm extensors.", exercise_type="strength", target_muscle="Forearms", difficulty_level="beginner", base_exp=10),
        Exercise(name="Dumbbell Shrugs", description="Lift shoulders straight up toward ears, squeeze traps at top, then lower.", exercise_type="strength", target_muscle="Trapezius", difficulty_level="beginner", base_exp=15),

        # 🧠 ADVANCED FUNCTIONAL & PERFORMANCE VARIANTS
        Exercise(name="Explosive Push Ups", description="Perform push-ups with enough force for hands to leave ground slightly.", exercise_type="functional", target_muscle="Chest, Triceps, Core", difficulty_level="advanced", base_exp=30),
        Exercise(name="Kettlebell Snatch", description="Swing kettlebell overhead in one motion while keeping core tight.", exercise_type="functional", target_muscle="Full Body", difficulty_level="advanced", base_exp=35),
        Exercise(name="Barbell Thruster", description="Perform front squat then push bar overhead explosively for full-body engagement.", exercise_type="functional", target_muscle="Legs, Shoulders, Core", difficulty_level="advanced", base_exp=35),
        Exercise(name="Sandbag Clean", description="Lift sandbag explosively from floor to shoulder using hip drive.", exercise_type="functional", target_muscle="Full Body", difficulty_level="advanced", base_exp=35),
        Exercise(name="Sled Push", description="Drive heavy sled forward using powerful strides and tight core engagement.", exercise_type="power", target_muscle="Legs, Glutes, Core", difficulty_level="advanced", base_exp=35),
        Exercise(name="Farmer’s Carry", description="Walk forward carrying heavy weights at sides, maintaining upright posture.", exercise_type="functional", target_muscle="Grip, Core, Shoulders", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Turkish Get-Up", description="From lying down, rise to standing while holding kettlebell overhead through transitions.", exercise_type="functional", target_muscle="Full Body, Core", difficulty_level="advanced", base_exp=40),
        Exercise(name="Kettlebell Swing", description="Hinge at hips and swing kettlebell to shoulder height using hip power.", exercise_type="functional", target_muscle="Glutes, Hamstrings, Core", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Medicine Ball Slam", description="Lift ball overhead and slam forcefully into ground, engaging full body.", exercise_type="power", target_muscle="Full Body", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Wall Ball", description="Squat down holding medicine ball, then throw it upward to wall target and catch.", exercise_type="functional", target_muscle="Legs, Shoulders, Core", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Battle Rope Slams", description="Raise ropes overhead and slam down explosively while engaging core.", exercise_type="power", target_muscle="Arms, Core, Shoulders", difficulty_level="advanced", base_exp=30),
        Exercise(name="Box Step-Over", description="Step laterally over box while holding dumbbells for balance and coordination.", exercise_type="functional", target_muscle="Legs, Core", difficulty_level="intermediate", base_exp=20),
        Exercise(name="Lateral Medicine Ball Toss", description="Throw ball sideways against wall using hip rotation for power.", exercise_type="power", target_muscle="Core, Shoulders", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Sledgehammer Swings", description="Swing sledgehammer overhead and strike tire powerfully with controlled rhythm.", exercise_type="power", target_muscle="Arms, Core, Shoulders", difficulty_level="advanced", base_exp=35),
        Exercise(name="Weighted Step-Up", description="Step onto bench with dumbbells, pressing through heel of front leg.", exercise_type="functional", target_muscle="Legs, Glutes", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Weighted Carry Overhead", description="Walk forward holding weights overhead to engage shoulders and stability.", exercise_type="functional", target_muscle="Shoulders, Core", difficulty_level="advanced", base_exp=35),
        Exercise(name="Ball Slams with Squat", description="Combine deep squat and slam motion to increase power and mobility.", exercise_type="power", target_muscle="Full Body", difficulty_level="intermediate", base_exp=25),
        Exercise(name="Explosive Lunges", description="Alternate jumping lunges explosively, maintaining upright form.", exercise_type="power", target_muscle="Legs, Core", difficulty_level="advanced", base_exp=30),
        Exercise(name="Resistance Band Sprint", description="Sprint forward against band resistance for explosive drive.", exercise_type="speed", target_muscle="Legs, Glutes, Core", difficulty_level="advanced", base_exp=35),
        Exercise(name="Single-Arm Kettlebell Clean and Press", description="Clean kettlebell to shoulder and press overhead using single arm.", exercise_type="functional", target_muscle="Full Body", difficulty_level="advanced", base_exp=35),
    ]
    print("\n✅ Part 4!")
    for exercise in default_exercises:
        print(f"Name: {exercise.name}")
        print(f"  Type: {exercise.exercise_type}")

def print_all_exercises():
    populate_default_exercises_part1()
    populate_default_exercises_part2()
    populate_default_exercises_part3()
    populate_default_exercises_part4()


# Example usage and testing
if __name__ == "__main__":
    from database.db_manager import DatabaseManager
    
    # Initialize database
    db = DatabaseManager()
    db.initialize_database()
    
    print("=== Printing Exercise Database ===\n")
    print_all_exercises()
    
    print("\n=== Testing Exercise Model ===\n")
    
    # Get all exercises
    all_exercises = Exercise.get_all()
    print(f"Total exercises in database: {len(all_exercises)}")
    
    # Search by type
    print("\n--- Strength Exercises ---")
    strength = Exercise.search_by_type('strength')
    print(f"Strength Exercises: {len(strength)}")
    ''' for ex in strength[:5]:
        print(f"  • {ex.name} - {ex.target_muscle} ({ex.base_exp} EXP)")'''
    # Search by type
    print("\n--- Power Exercises ---")
    power = Exercise.search_by_type('power')
    print(f"Power Exercises: {len(power)}")
    ''' for ex in power[:5]:
        print(f"  • {ex.name} - {ex.target_muscle} ({ex.base_exp} EXP)")'''    

    # Search by type
    print("\n--- Cardio Exercises ---")
    cardio = Exercise.search_by_type('cardio')
    print(f"Cardio Exercises: {len(cardio)}")
    ''' for ex in cardio[:5]:
        print(f"  • {ex.name} - {ex.target_muscle} ({ex.base_exp} EXP)")'''
    
    # Search by type
    print("\n--- Endurance Exercises ---")
    endurance = Exercise.search_by_type('endurance')
    print(f"Endurance Exercises: {len(endurance)}")
    ''' for ex in endurance[:5]:
        print(f"  • {ex.name} - {ex.target_muscle} ({ex.base_exp} EXP)")'''

    # Search by type
    print("\n--- Core Exercises ---")
    core = Exercise.search_by_type('core')
    print(f"Core Exercises: {len(core)}")
    ''' for ex in core[:5]:
        print(f"  • {ex.name} - {ex.target_muscle} ({ex.base_exp} EXP)")'''

    # Search by type
    print("\n--- Functional Exercises ---")
    functional = Exercise.search_by_type('functional')
    print(f"Functional Exercises: {len(functional)}")
    ''' for ex in functional[:5]:
        print(f"  • {ex.name} - {ex.target_muscle} ({ex.base_exp} EXP)")'''

    # Search by type
    print("\n--- Hiit Exercises ---")
    hiit = Exercise.search_by_type('hiit')
    print(f"Hiit Exercises: {len(hiit)}")
    ''' for ex in hiit[:5]:
        print(f"  • {ex.name} - {ex.target_muscle} ({ex.base_exp} EXP)")'''

    # Search by type
    print("\n--- Agility Exercises ---")
    agility = Exercise.search_by_type('agility')
    print(f"Agility Exercises: {len(agility)}")
    ''' for ex in agility[:5]:
        print(f"  • {ex.name} - {ex.target_muscle} ({ex.base_exp} EXP)")'''

    # Search by type
    print("\n--- Balance Exercises ---")
    balance = Exercise.search_by_type('balance')
    print(f"Balance Exercises: {len(balance)}")
    ''' for ex in balance[:5]:
        print(f"  • {ex.name} - {ex.target_muscle} ({ex.base_exp} EXP)")'''

    # Search by type
    print("\n--- Flexibility Exercises ---")
    flexibility = Exercise.search_by_type('flexibility')
    print(f"Flexibility Exercises: {len(flexibility)}")
    ''' for ex in flexibility[:5]:
        print(f"  • {ex.name} - {ex.target_muscle} ({ex.base_exp} EXP)")'''
    
    print(len(strength) + len(power) + len(cardio) + len(endurance) + len(core) + len(functional) + len(hiit) + len(agility) + len(balance) + len(flexibility))
    

    # Search by muscle
    '''print("\n--- Chest Exercises ---")
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
        print(f"Base EXP: {squat.base_exp}")'''