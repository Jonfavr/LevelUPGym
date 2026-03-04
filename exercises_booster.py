"""
exercises_booster.py
════════════════════════════════════════════════════════════════════
Adds missing exercise variations to the LevelUp Gym database.

Organized by muscle group. Every exercise has been cross-checked
against the existing database to avoid duplicates.

Usage:
    python exercises_booster.py                  # dry-run (preview only)
    python exercises_booster.py --commit         # write to database
    python exercises_booster.py --commit --group chest   # single group only

Groups available:
    chest | back | biceps | triceps | shoulders |
    legs | hamstrings | glutes | calves | core | lats | traps
════════════════════════════════════════════════════════════════════
"""

import sqlite3
import argparse
import os
import sys
from datetime import datetime

# ── Adjust path if needed ────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), 'levelup_gym.db')

# ════════════════════════════════════════════════════════════════════════════
# NEW EXERCISES — organised by muscle group
# Fields: name, description, exercise_type, primary_muscle,
#         complementary_muscle, difficulty_level, base_exp
# ════════════════════════════════════════════════════════════════════════════

NEW_EXERCISES = [

    # ══════════════════════════════════════════════════════════════════════
    # CHEST
    # Have: Barbell Bench Press, Dumbbell Bench Press, Incline BB & DB,
    #       Decline BB & DB, Cable Crossover, Cable Fly, Dumbbell Fly,
    #       Incline DB Fly, Pec Deck, Push Ups, Explosive Push-Ups,
    #       Chest/Seated/Incline machine variations
    # Missing: wide grip, close grip, decline fly, incline cable,
    #          floor press, landmine, diamond push-up, archer push-up,
    #          smith machine press, low cable fly
    # ══════════════════════════════════════════════════════════════════════
    {
        'name': 'Wide Grip Barbell Bench Press',
        'description': 'Place hands wider than shoulder width on the bar. Lower to mid-chest and press up. Wider grip increases chest stretch and shifts emphasis away from triceps.',
        'exercise_type': 'strength',
        'primary_muscle': 'Chest',
        'complementary_muscle': 'Shoulders, Triceps',
        'difficulty_level': 'intermediate',
        'base_exp': 22,
    },
    {
        'name': 'Smith Machine Bench Press',
        'description': 'Lie under the Smith machine bar, unrack and lower to mid-chest, then press back up. Guided bar path is ideal for beginners learning pressing mechanics.',
        'exercise_type': 'strength',
        'primary_muscle': 'Chest',
        'complementary_muscle': 'Triceps, Shoulders',
        'difficulty_level': 'beginner',
        'base_exp': 15,
    },
    {
        'name': 'Floor Press',
        'description': 'Lie on the floor with knees bent, press dumbbells or barbell from chest to lockout. Elbows stop at floor level, reducing shoulder strain and isolating the lockout.',
        'exercise_type': 'strength',
        'primary_muscle': 'Chest',
        'complementary_muscle': 'Triceps',
        'difficulty_level': 'intermediate',
        'base_exp': 20,
    },
    {
        'name': 'Incline Cable Fly',
        'description': 'Set bench to 30–45° between two low cables. Bring handles up and together in an arc, squeezing the upper chest at the top. Maintain constant tension throughout.',
        'exercise_type': 'strength',
        'primary_muscle': 'Chest',
        'complementary_muscle': 'Front Deltoids',
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Decline Cable Fly',
        'description': 'Set up on decline bench with high cables. Bring handles down and together targeting the lower chest. Keep a slight elbow bend and control the return.',
        'exercise_type': 'strength',
        'primary_muscle': 'Chest',
        'complementary_muscle': None,
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Low Cable Fly',
        'description': 'Set cables at the lowest position and bring handles up and together in front of the chest. Great for targeting the upper chest with constant cable tension.',
        'exercise_type': 'strength',
        'primary_muscle': 'Chest',
        'complementary_muscle': 'Front Deltoids',
        'difficulty_level': 'beginner',
        'base_exp': 15,
    },
    {
        'name': 'Decline Dumbbell Fly',
        'description': 'On a decline bench, hold dumbbells above chest, lower in a wide arc until a deep stretch is felt, then bring them back together. Targets the lower chest.',
        'exercise_type': 'strength',
        'primary_muscle': 'Chest',
        'complementary_muscle': None,
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Diamond Push-Ups',
        'description': 'Form a diamond shape with index fingers and thumbs, lower chest to hands, and press up. Shifts emphasis heavily onto the triceps and inner chest.',
        'exercise_type': 'strength',
        'primary_muscle': 'Chest',
        'complementary_muscle': 'Triceps',
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Archer Push-Up',
        'description': 'Wide push-up variation where one arm stays extended to the side while the other bends to lower the chest. Alternates sides. Builds unilateral pushing strength.',
        'exercise_type': 'strength',
        'primary_muscle': 'Chest',
        'complementary_muscle': 'Shoulders, Triceps',
        'difficulty_level': 'advanced',
        'base_exp': 28,
    },
    {
        'name': 'Landmine Press',
        'description': 'Place one end of the barbell in a corner or landmine attachment. Press the other end overhead at an angle from shoulder height. Great for shoulder-friendly pressing.',
        'exercise_type': 'strength',
        'primary_muscle': 'Chest',
        'complementary_muscle': 'Shoulders, Triceps',
        'difficulty_level': 'intermediate',
        'base_exp': 20,
    },
    {
        'name': 'Incline Smith Machine Press',
        'description': 'Set the Smith machine bench to incline. Press the bar from upper chest to full extension. Safe incline pressing option with guided bar path.',
        'exercise_type': 'strength',
        'primary_muscle': 'Chest',
        'complementary_muscle': 'Shoulders, Triceps',
        'difficulty_level': 'beginner',
        'base_exp': 16,
    },
    {
        'name': 'Decline Smith Machine Press',
        'description': 'Set bench to decline on the Smith machine. Press the bar from the lower chest upward. Targets the lower chest with controlled bar path.',
        'exercise_type': 'strength',
        'primary_muscle': 'Chest',
        'complementary_muscle': 'Triceps',
        'difficulty_level': 'beginner',
        'base_exp': 16,
    },
    {
        'name': 'Dumbbell Squeeze Press',
        'description': 'Lie flat and press two dumbbells together while pushing them upward. The constant medial squeeze creates strong inner chest activation throughout the rep.',
        'exercise_type': 'strength',
        'primary_muscle': 'Chest',
        'complementary_muscle': 'Triceps',
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Feet-Elevated Push-Up',
        'description': 'Place feet on a bench and perform push-ups. Elevation shifts load to the upper chest. Increase height to increase difficulty.',
        'exercise_type': 'strength',
        'primary_muscle': 'Chest',
        'complementary_muscle': 'Shoulders, Triceps',
        'difficulty_level': 'intermediate',
        'base_exp': 16,
    },

    # ══════════════════════════════════════════════════════════════════════
    # BACK
    # Have: Barbell Deadlift, Barbell Row, Dumbbell Row, Pull-Up variations,
    #       Lat Pulldown, Wide-Grip Pulldown, Seated Cable Row, T-Bar Row,
    #       Seated Row Machine
    # Missing: single arm row, inverted row, chest supported row,
    #          pendlay row, meadows row, deficit deadlift, rack pull,
    #          single arm cable row, wide cable row
    # ══════════════════════════════════════════════════════════════════════
    {
        'name': 'Single Arm Dumbbell Row',
        'description': 'Place one knee and hand on a bench for support. Pull a dumbbell from a dead hang to the hip, keeping the elbow close to the body. Excellent for unilateral back development.',
        'exercise_type': 'strength',
        'primary_muscle': 'Back',
        'complementary_muscle': 'Biceps',
        'difficulty_level': 'beginner',
        'base_exp': 16,
    },
    {
        'name': 'Inverted Row',
        'description': 'Set a bar at waist height. Hang below with straight body and pull chest to the bar. Easier than pull-ups and great for beginners building back and bicep strength.',
        'exercise_type': 'strength',
        'primary_muscle': 'Back',
        'complementary_muscle': 'Biceps, Core',
        'difficulty_level': 'beginner',
        'base_exp': 15,
    },
    {
        'name': 'Chest Supported Dumbbell Row',
        'description': 'Lie chest-down on an incline bench and row dumbbells toward the hips. Chest support eliminates lower back involvement, allowing full focus on the back.',
        'exercise_type': 'strength',
        'primary_muscle': 'Back',
        'complementary_muscle': 'Biceps',
        'difficulty_level': 'intermediate',
        'base_exp': 20,
    },
    {
        'name': 'Pendlay Row',
        'description': 'Dead-stop barbell row from the floor. Hinge to horizontal torso, explosively pull bar to lower chest, return to floor each rep. Builds raw back power.',
        'exercise_type': 'strength',
        'primary_muscle': 'Back',
        'complementary_muscle': 'Biceps, Core',
        'difficulty_level': 'advanced',
        'base_exp': 28,
    },
    {
        'name': 'Meadows Row',
        'description': 'Place one end of a landmine barbell perpendicular to you, stagger stance and row with one arm. Long range of motion with excellent lat stretch at the bottom.',
        'exercise_type': 'strength',
        'primary_muscle': 'Back',
        'complementary_muscle': 'Biceps',
        'difficulty_level': 'advanced',
        'base_exp': 26,
    },
    {
        'name': 'Rack Pull',
        'description': 'Set barbell on safety pins at knee height. Pull from this elevated position to lockout. Allows heavier loads and targets the upper back and lockout portion of the deadlift.',
        'exercise_type': 'strength',
        'primary_muscle': 'Back',
        'complementary_muscle': 'Glutes, Traps',
        'difficulty_level': 'advanced',
        'base_exp': 30,
    },
    {
        'name': 'Single Arm Cable Row',
        'description': 'Attach a single handle to a low cable. Pull toward the hip in a rowing motion. Allows full rotation and scapular movement for unilateral back training.',
        'exercise_type': 'strength',
        'primary_muscle': 'Back',
        'complementary_muscle': 'Biceps',
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Wide Grip Seated Cable Row',
        'description': 'Use a wide bar attachment on the seated cable row. Pull to the lower chest with elbows flaring out to target the upper and outer lats.',
        'exercise_type': 'strength',
        'primary_muscle': 'Back',
        'complementary_muscle': 'Rear Deltoids',
        'difficulty_level': 'intermediate',
        'base_exp': 20,
    },
    {
        'name': 'Deficit Deadlift',
        'description': 'Stand on a small platform or plates and perform a conventional deadlift. Increased range of motion challenges off-the-floor strength and leg drive.',
        'exercise_type': 'strength',
        'primary_muscle': 'Back',
        'complementary_muscle': 'Legs, Glutes',
        'difficulty_level': 'advanced',
        'base_exp': 32,
    },
    {
        'name': 'Banded Pull Apart',
        'description': 'Hold a resistance band at chest height with both hands. Pull it apart horizontally by squeezing shoulder blades together. Excellent for rear delts and upper back health.',
        'exercise_type': 'strength',
        'primary_muscle': 'Back',
        'complementary_muscle': 'Rear Deltoids',
        'difficulty_level': 'beginner',
        'base_exp': 10,
    },

    # ══════════════════════════════════════════════════════════════════════
    # BICEPS
    # Have: Barbell Curl, Alternating DB Curl, Hammer Curl, Cable Curl,
    #       Concentration Curl, EZ Preacher Curl, Incline DB Curl,
    #       Rope Cable Curl, Preacher Curl — NO ADVANCED exercises
    # Missing: advanced variations, drag curl, spider curl, 21s,
    #          zottman, reverse curl, wide grip curl, cross-body hammer
    # ══════════════════════════════════════════════════════════════════════
    {
        'name': 'Barbell Drag Curl',
        'description': 'Instead of curling in an arc, drag the barbell up the torso keeping elbows behind you. This unique path maximises long-head bicep peak contraction.',
        'exercise_type': 'strength',
        'primary_muscle': 'Biceps',
        'complementary_muscle': None,
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Spider Curl',
        'description': 'Lie face-down on an incline bench and curl dumbbells or a barbell with elbows pointing straight down. Eliminates momentum completely for peak bicep isolation.',
        'exercise_type': 'strength',
        'primary_muscle': 'Biceps',
        'complementary_muscle': None,
        'difficulty_level': 'advanced',
        'base_exp': 24,
    },
    {
        'name': 'Zottman Curl',
        'description': 'Curl up with a supinated grip, rotate to pronated at the top, then lower slowly in the reverse curl position. Trains both biceps and forearm extensors in one movement.',
        'exercise_type': 'strength',
        'primary_muscle': 'Biceps',
        'complementary_muscle': 'Forearms',
        'difficulty_level': 'intermediate',
        'base_exp': 20,
    },
    {
        'name': '21s',
        'description': 'Divide a bicep curl into three zones: 7 reps lower half, 7 reps upper half, 7 full reps. Creates intense time-under-tension and a major metabolic pump.',
        'exercise_type': 'strength',
        'primary_muscle': 'Biceps',
        'complementary_muscle': None,
        'difficulty_level': 'advanced',
        'base_exp': 26,
    },
    {
        'name': 'Reverse Curl',
        'description': 'Hold barbell or dumbbells with an overhand (pronated) grip and curl upward. Trains the brachialis and brachioradialis in addition to the biceps.',
        'exercise_type': 'strength',
        'primary_muscle': 'Biceps',
        'complementary_muscle': 'Forearms',
        'difficulty_level': 'intermediate',
        'base_exp': 16,
    },
    {
        'name': 'Wide Grip Barbell Curl',
        'description': 'Grip the barbell wider than shoulder-width and curl. Shifts emphasis to the short head (inner) bicep for greater width development.',
        'exercise_type': 'strength',
        'primary_muscle': 'Biceps',
        'complementary_muscle': None,
        'difficulty_level': 'intermediate',
        'base_exp': 16,
    },
    {
        'name': 'Cross Body Hammer Curl',
        'description': 'Curl the dumbbell across the body toward the opposite shoulder rather than straight up. Intensifies brachialis activation for arm thickness.',
        'exercise_type': 'strength',
        'primary_muscle': 'Biceps',
        'complementary_muscle': 'Forearms',
        'difficulty_level': 'intermediate',
        'base_exp': 16,
    },
    {
        'name': 'Cable Hammer Curl',
        'description': 'Attach a rope to a low cable and curl with a neutral grip. Provides constant tension on the brachialis and outer bicep through the full range of motion.',
        'exercise_type': 'strength',
        'primary_muscle': 'Biceps',
        'complementary_muscle': 'Forearms',
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Behind the Back Cable Curl',
        'description': 'Stand with cable behind you, arm extended back, and curl the handle forward. Unique angle maximises long-head stretch at the start of each rep.',
        'exercise_type': 'strength',
        'primary_muscle': 'Biceps',
        'complementary_muscle': None,
        'difficulty_level': 'advanced',
        'base_exp': 22,
    },
    {
        'name': 'Single Arm Preacher Curl',
        'description': 'Perform a preacher curl one arm at a time with a dumbbell. Maximises mind-muscle connection and eliminates any compensation from the stronger side.',
        'exercise_type': 'strength',
        'primary_muscle': 'Biceps',
        'complementary_muscle': None,
        'difficulty_level': 'advanced',
        'base_exp': 22,
    },

    # ══════════════════════════════════════════════════════════════════════
    # TRICEPS
    # Have: Triceps Pushdown, Cable Rope Pushdown, Kickback, Parallel Dip,
    #       Lying Triceps Extension, DB Overhead Extension, Close Grip Press
    #       — NO ADVANCED exercises
    # Missing: skull crusher variations, weighted dips, JM press,
    #          tate press, cable overhead extension, rope overhead extension
    # ══════════════════════════════════════════════════════════════════════
    {
        'name': 'EZ Bar Skull Crusher',
        'description': 'Lie on bench with EZ bar, lower it toward the forehead by bending the elbows, then extend back to lockout. Primary mass builder for the triceps long head.',
        'exercise_type': 'strength',
        'primary_muscle': 'Triceps',
        'complementary_muscle': None,
        'difficulty_level': 'intermediate',
        'base_exp': 20,
    },
    {
        'name': 'Barbell Skull Crusher',
        'description': 'Same as EZ bar version but with straight barbell. Greater stretch on the triceps long head. Keep elbows pointing to the ceiling throughout the movement.',
        'exercise_type': 'strength',
        'primary_muscle': 'Triceps',
        'complementary_muscle': None,
        'difficulty_level': 'intermediate',
        'base_exp': 20,
    },
    {
        'name': 'Weighted Dips',
        'description': 'Attach a weight belt or hold a dumbbell between knees. Perform parallel bar dips with added resistance. One of the best mass builders for the triceps.',
        'exercise_type': 'strength',
        'primary_muscle': 'Triceps',
        'complementary_muscle': 'Chest, Shoulders',
        'difficulty_level': 'advanced',
        'base_exp': 30,
    },
    {
        'name': 'Cable Overhead Triceps Extension',
        'description': 'Face away from a high cable, hold rope behind head and extend arms overhead. Excellent long-head stretch and constant tension through the full movement.',
        'exercise_type': 'strength',
        'primary_muscle': 'Triceps',
        'complementary_muscle': None,
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Rope Overhead Triceps Extension',
        'description': 'Attach a rope to a low cable. Face away and extend arms overhead, separating the rope at the top for maximum tricep contraction. Targets the long head.',
        'exercise_type': 'strength',
        'primary_muscle': 'Triceps',
        'complementary_muscle': None,
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Tate Press',
        'description': 'Lie on bench with dumbbells above chest. Bend elbows outward, lowering weights toward the chest, then press back up. Unique elbow path isolates the lateral head.',
        'exercise_type': 'strength',
        'primary_muscle': 'Triceps',
        'complementary_muscle': None,
        'difficulty_level': 'advanced',
        'base_exp': 24,
    },
    {
        'name': 'JM Press',
        'description': 'Hybrid between a close-grip bench press and a skull crusher. Lower the bar toward the throat, push back up. Builds huge tricep mass with compound loading.',
        'exercise_type': 'strength',
        'primary_muscle': 'Triceps',
        'complementary_muscle': 'Chest',
        'difficulty_level': 'advanced',
        'base_exp': 26,
    },
    {
        'name': 'Single Arm Cable Triceps Pushdown',
        'description': 'Attach a single handle to a high cable. Push down with one arm at a time, keeping the elbow pinned to the side. Fixes left/right imbalances.',
        'exercise_type': 'strength',
        'primary_muscle': 'Triceps',
        'complementary_muscle': None,
        'difficulty_level': 'beginner',
        'base_exp': 14,
    },
    {
        'name': 'Decline Skull Crusher',
        'description': 'Perform the skull crusher on a decline bench. The angle increases the range of motion and intensifies the stretch on the triceps long head.',
        'exercise_type': 'strength',
        'primary_muscle': 'Triceps',
        'complementary_muscle': None,
        'difficulty_level': 'advanced',
        'base_exp': 24,
    },

    # ══════════════════════════════════════════════════════════════════════
    # SHOULDERS
    # Have: DB & Machine & Smith Shoulder Press, Lateral/Front/Rear Raises,
    #       Cable variations, Face Pull, Push Press — missing beginner advanced
    # Missing: military press, arnold press, behind neck press,
    #          landmine press, Y raise, seated DB press, upright DB row
    # ══════════════════════════════════════════════════════════════════════
    {
        'name': 'Barbell Military Press',
        'description': 'Stand with barbell at shoulder height, press it strictly overhead to lockout. No leg drive. Regarded as the gold standard for raw overhead pressing strength.',
        'exercise_type': 'strength',
        'primary_muscle': 'Shoulders',
        'complementary_muscle': 'Triceps',
        'difficulty_level': 'intermediate',
        'base_exp': 24,
    },
    {
        'name': 'Seated Barbell Overhead Press',
        'description': 'Seated on a bench with back support, press barbell from shoulder height to overhead lockout. Back support allows heavier loading with reduced lower back stress.',
        'exercise_type': 'strength',
        'primary_muscle': 'Shoulders',
        'complementary_muscle': 'Triceps',
        'difficulty_level': 'intermediate',
        'base_exp': 22,
    },
    {
        'name': 'Arnold Press',
        'description': 'Start with dumbbells at chest, palms facing you, rotate palms forward as you press overhead. Named after Arnold Schwarzenegger. Hits all three deltoid heads.',
        'exercise_type': 'strength',
        'primary_muscle': 'Shoulders',
        'complementary_muscle': 'Triceps',
        'difficulty_level': 'intermediate',
        'base_exp': 22,
    },
    {
        'name': 'Seated Dumbbell Press',
        'description': 'Sit on a bench with back support, hold dumbbells at shoulder height and press overhead. The seated position provides stability to focus on shoulder development.',
        'exercise_type': 'strength',
        'primary_muscle': 'Shoulders',
        'complementary_muscle': 'Triceps',
        'difficulty_level': 'beginner',
        'base_exp': 18,
    },
    {
        'name': 'Landmine Shoulder Press',
        'description': 'Hold the end of a landmine barbell at shoulder height with one hand and press it upward at an angle. Shoulder-friendly pressing option with a natural arc.',
        'exercise_type': 'strength',
        'primary_muscle': 'Shoulders',
        'complementary_muscle': 'Triceps, Core',
        'difficulty_level': 'beginner',
        'base_exp': 16,
    },
    {
        'name': 'Single Arm Dumbbell Press',
        'description': 'Press one dumbbell overhead at a time. The offset load challenges core stability and eliminates the dominant arm from compensating.',
        'exercise_type': 'strength',
        'primary_muscle': 'Shoulders',
        'complementary_muscle': 'Triceps, Core',
        'difficulty_level': 'intermediate',
        'base_exp': 20,
    },
    {
        'name': 'Y Raise',
        'description': 'Lie face down on incline bench or stand bent over. Raise arms diagonally forming a Y shape to target the lower traps and rear deltoids. Essential for shoulder health.',
        'exercise_type': 'strength',
        'primary_muscle': 'Shoulders',
        'complementary_muscle': 'Traps',
        'difficulty_level': 'beginner',
        'base_exp': 12,
    },
    {
        'name': 'Dumbbell Upright Row',
        'description': 'Hold dumbbells at thighs with overhand grip and pull upward to chin height, elbows leading. Targets medial deltoids and traps. Use lighter weight to protect shoulders.',
        'exercise_type': 'strength',
        'primary_muscle': 'Shoulders',
        'complementary_muscle': 'Traps',
        'difficulty_level': 'beginner',
        'base_exp': 14,
    },
    {
        'name': 'Plate Front Raise',
        'description': 'Hold a weight plate with both hands and raise straight out in front to shoulder height. Teaches front delt control and is a great beginner introduction to isolation work.',
        'exercise_type': 'strength',
        'primary_muscle': 'Shoulders',
        'complementary_muscle': None,
        'difficulty_level': 'beginner',
        'base_exp': 12,
    },
    {
        'name': 'Behind the Neck Barbell Press',
        'description': 'Press a barbell from behind the neck to overhead lockout. Advanced movement requiring good shoulder flexibility. Targets lateral deltoids strongly.',
        'exercise_type': 'strength',
        'primary_muscle': 'Shoulders',
        'complementary_muscle': 'Triceps',
        'difficulty_level': 'advanced',
        'base_exp': 28,
    },
    {
        'name': 'Handstand Push-Up',
        'description': 'In a handstand against a wall, lower head toward the ground by bending elbows, then press back up. Elite bodyweight shoulder press requiring significant strength and balance.',
        'exercise_type': 'strength',
        'primary_muscle': 'Shoulders',
        'complementary_muscle': 'Triceps, Core',
        'difficulty_level': 'advanced',
        'base_exp': 35,
    },

    # ══════════════════════════════════════════════════════════════════════
    # LEGS
    # Already very well covered — adding key missing strength variations
    # and dedicated quad isolation
    # ══════════════════════════════════════════════════════════════════════
    {
        'name': 'Barbell Back Squat',
        'description': 'Place barbell on upper traps, brace core, and squat until thighs are below parallel. Drive through heels to stand. The king of lower body compound movements.',
        'exercise_type': 'strength',
        'primary_muscle': 'Legs',
        'complementary_muscle': 'Glutes, Core',
        'difficulty_level': 'advanced',
        'base_exp': 30,
    },
    {
        'name': 'Low Bar Squat',
        'description': 'Bar is placed lower on the rear delts than a high-bar squat. Torso leans more forward, engaging more posterior chain. Allows heavier loads for strength athletes.',
        'exercise_type': 'strength',
        'primary_muscle': 'Legs',
        'complementary_muscle': 'Glutes, Lower Back',
        'difficulty_level': 'advanced',
        'base_exp': 30,
    },
    {
        'name': 'Dumbbell Squat',
        'description': 'Hold dumbbells at sides and perform a standard squat. A beginner-friendly alternative to barbell squats that still builds solid lower body strength.',
        'exercise_type': 'strength',
        'primary_muscle': 'Legs',
        'complementary_muscle': 'Glutes',
        'difficulty_level': 'beginner',
        'base_exp': 14,
    },
    {
        'name': 'Single Leg Press',
        'description': 'Perform the leg press using only one leg at a time. Identifies and corrects left/right strength imbalances in the quads and glutes.',
        'exercise_type': 'strength',
        'primary_muscle': 'Legs',
        'complementary_muscle': 'Glutes',
        'difficulty_level': 'intermediate',
        'base_exp': 20,
    },
    {
        'name': 'Wide Stance Leg Press',
        'description': 'Place feet wide and high on the leg press platform. Increased glute and inner thigh activation compared to the standard foot position.',
        'exercise_type': 'strength',
        'primary_muscle': 'Legs',
        'complementary_muscle': 'Glutes, Inner Thighs',
        'difficulty_level': 'intermediate',
        'base_exp': 20,
    },
    {
        'name': 'Narrow Stance Squat',
        'description': 'Squat with feet hip-width or closer together. Places greater demand on the quadriceps and requires good ankle mobility. Excellent for quad isolation within a squat pattern.',
        'exercise_type': 'strength',
        'primary_muscle': 'Legs',
        'complementary_muscle': 'Glutes',
        'difficulty_level': 'intermediate',
        'base_exp': 22,
    },
    {
        'name': 'Paused Squat',
        'description': 'Perform a squat and pause at the bottom for 2–3 seconds before driving up. Eliminates the stretch-shortening cycle, building raw strength out of the hole.',
        'exercise_type': 'strength',
        'primary_muscle': 'Legs',
        'complementary_muscle': 'Glutes, Core',
        'difficulty_level': 'advanced',
        'base_exp': 28,
    },
    {
        'name': 'Sissy Squat',
        'description': 'Hold a support, lean back and lower by bending the knees while keeping the torso straight. Pure quad isolation exercise with no hip hinge involved.',
        'exercise_type': 'strength',
        'primary_muscle': 'Legs',
        'complementary_muscle': None,
        'difficulty_level': 'advanced',
        'base_exp': 26,
    },

    # ══════════════════════════════════════════════════════════════════════
    # HAMSTRINGS
    # Have: Romanian Deadlift, Dumbbell Deadlift, Good Morning, KB Swings,
    #       Lying Leg Curl, Single-Leg Deadlift — NO ADVANCED exercises
    # Missing: nordic curl, seated leg curl, glute ham raise,
    #          stiff leg deadlift, cable pull through, Swiss ball curl
    # ══════════════════════════════════════════════════════════════════════
    {
        'name': 'Nordic Hamstring Curl',
        'description': 'Kneel with feet anchored. Lower torso toward the floor using only hamstring strength, then use hands to push back up to start. One of the most effective hamstring exercises known.',
        'exercise_type': 'strength',
        'primary_muscle': 'Hamstrings',
        'complementary_muscle': 'Glutes',
        'difficulty_level': 'advanced',
        'base_exp': 32,
    },
    {
        'name': 'Seated Leg Curl',
        'description': 'Sit in the machine, place the pad against lower legs, and curl toward the glutes. Seated position places the hamstrings in a lengthened state for greater recruitment.',
        'exercise_type': 'strength',
        'primary_muscle': 'Hamstrings',
        'complementary_muscle': None,
        'difficulty_level': 'beginner',
        'base_exp': 14,
    },
    {
        'name': 'Stiff Leg Deadlift',
        'description': 'Perform a deadlift with minimal knee bend. Lower the bar close to the shins by hinging at the hips until a hamstring stretch is felt, then drive hips forward to stand.',
        'exercise_type': 'strength',
        'primary_muscle': 'Hamstrings',
        'complementary_muscle': 'Glutes, Lower Back',
        'difficulty_level': 'intermediate',
        'base_exp': 22,
    },
    {
        'name': 'Glute Ham Raise',
        'description': 'On a GHD machine, lower the torso toward the floor using hamstring control, then curl the body back up. Builds hamstring strength through a full range of motion.',
        'exercise_type': 'strength',
        'primary_muscle': 'Hamstrings',
        'complementary_muscle': 'Glutes, Core',
        'difficulty_level': 'advanced',
        'base_exp': 30,
    },
    {
        'name': 'Cable Pull Through',
        'description': 'Stand facing away from a cable machine, pull the handle through the legs using a hip hinge. Excellent for teaching the hip hinge pattern and loading the posterior chain.',
        'exercise_type': 'strength',
        'primary_muscle': 'Hamstrings',
        'complementary_muscle': 'Glutes',
        'difficulty_level': 'beginner',
        'base_exp': 14,
    },
    {
        'name': 'Swiss Ball Leg Curl',
        'description': 'Lie on back with heels on a Swiss ball. Lift hips and curl the ball toward the glutes. Challenges hamstrings and requires significant core stability.',
        'exercise_type': 'strength',
        'primary_muscle': 'Hamstrings',
        'complementary_muscle': 'Glutes, Core',
        'difficulty_level': 'intermediate',
        'base_exp': 20,
    },
    {
        'name': 'Barbell Romanian Deadlift',
        'description': 'Hinge at hips with barbell, lowering it close to the legs until a deep hamstring stretch is felt. Heavier loading potential than dumbbell version for advanced lifters.',
        'exercise_type': 'strength',
        'primary_muscle': 'Hamstrings',
        'complementary_muscle': 'Glutes, Lower Back',
        'difficulty_level': 'advanced',
        'base_exp': 28,
    },

    # ══════════════════════════════════════════════════════════════════════
    # GLUTES
    # Have: Glute Bridge, Hip Thrust, Donkey Kicks, Cable Kickback,
    #       Hip Abduction, Kettlebell Swing, Sumo Deadlift, Single-Leg RDL
    # Missing: barbell hip thrust, single-leg bridge, banded variations,
    #          fire hydrant, frog pump
    # ══════════════════════════════════════════════════════════════════════
    {
        'name': 'Barbell Hip Thrust',
        'description': 'Rest upper back on bench with barbell across hips. Drive hips up to full extension by squeezing glutes. The primary exercise for glute hypertrophy with maximum loading potential.',
        'exercise_type': 'strength',
        'primary_muscle': 'Glutes',
        'complementary_muscle': 'Hamstrings',
        'difficulty_level': 'advanced',
        'base_exp': 30,
    },
    {
        'name': 'Single Leg Glute Bridge',
        'description': 'Lie on back, one knee bent, other leg raised. Drive hips up through the planted foot. Single-leg variation increases glute demand and corrects imbalances.',
        'exercise_type': 'strength',
        'primary_muscle': 'Glutes',
        'complementary_muscle': 'Core',
        'difficulty_level': 'intermediate',
        'base_exp': 16,
    },
    {
        'name': 'Banded Glute Bridge',
        'description': 'Place a resistance band above the knees and perform a glute bridge. The band activates the glute medius and abductors in addition to the primary glute movement.',
        'exercise_type': 'strength',
        'primary_muscle': 'Glutes',
        'complementary_muscle': 'Core',
        'difficulty_level': 'beginner',
        'base_exp': 12,
    },
    {
        'name': 'Fire Hydrant',
        'description': 'On all fours, lift one knee out to the side like a dog at a hydrant. Targets the glute medius for hip stability and lateral glute development.',
        'exercise_type': 'functional',
        'primary_muscle': 'Glutes',
        'complementary_muscle': 'Hips',
        'difficulty_level': 'beginner',
        'base_exp': 10,
    },
    {
        'name': 'Frog Pump',
        'description': 'Lie on back, press soles of feet together and let knees fall out. From this frog position, pump hips upward. Maximum glute isolation with zero quad involvement.',
        'exercise_type': 'functional',
        'primary_muscle': 'Glutes',
        'complementary_muscle': None,
        'difficulty_level': 'beginner',
        'base_exp': 10,
    },
    {
        'name': 'Sumo Squat with Dumbbell',
        'description': 'Hold one dumbbell vertically at the chest. Take a wide stance with toes pointed out and squat deep. Targets glutes and inner thighs with excellent depth.',
        'exercise_type': 'strength',
        'primary_muscle': 'Glutes',
        'complementary_muscle': 'Inner Thighs, Legs',
        'difficulty_level': 'beginner',
        'base_exp': 14,
    },
    {
        'name': 'Bulgarian Split Squat with Barbell',
        'description': 'Place barbell on back, elevate rear foot on a bench and perform deep single-leg squats. Greater loading than dumbbell version for advanced glute and quad development.',
        'exercise_type': 'strength',
        'primary_muscle': 'Glutes',
        'complementary_muscle': 'Legs, Core',
        'difficulty_level': 'advanced',
        'base_exp': 30,
    },

    # ══════════════════════════════════════════════════════════════════════
    # CALVES
    # Have: Seated Calf Raise, Machine Calf Raise — both beginner
    # Missing: standing variations, single leg, donkey raise, tibialis
    # ══════════════════════════════════════════════════════════════════════
    {
        'name': 'Standing Calf Raise',
        'description': 'Stand on the edge of a step or calf raise machine. Rise onto toes, hold the peak contraction, then lower below neutral for a full stretch. Essential calf builder.',
        'exercise_type': 'strength',
        'primary_muscle': 'Calves',
        'complementary_muscle': None,
        'difficulty_level': 'beginner',
        'base_exp': 12,
    },
    {
        'name': 'Single Leg Calf Raise',
        'description': 'Perform standing calf raises on one leg. Doubles the load per calf and builds unilateral calf strength and balance. Can be done bodyweight or holding a dumbbell.',
        'exercise_type': 'strength',
        'primary_muscle': 'Calves',
        'complementary_muscle': None,
        'difficulty_level': 'intermediate',
        'base_exp': 16,
    },
    {
        'name': 'Donkey Calf Raise',
        'description': 'Bend at the hips with hands on a support. Rise onto toes and lower with full range. The hip-flexed position stretches the gastrocnemius for deeper calf recruitment.',
        'exercise_type': 'strength',
        'primary_muscle': 'Calves',
        'complementary_muscle': None,
        'difficulty_level': 'intermediate',
        'base_exp': 16,
    },
    {
        'name': 'Standing Barbell Calf Raise',
        'description': 'With barbell on upper back, perform calf raises on the edge of a platform. Heavy loading for maximum calf hypertrophy and strength.',
        'exercise_type': 'strength',
        'primary_muscle': 'Calves',
        'complementary_muscle': None,
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Tibialis Raise',
        'description': 'Stand with heels on a step, lift the toes upward repeatedly. Trains the tibialis anterior — the muscle on the front of the shin — for shin health and ankle stability.',
        'exercise_type': 'strength',
        'primary_muscle': 'Calves',
        'complementary_muscle': 'Ankles',
        'difficulty_level': 'beginner',
        'base_exp': 10,
    },

    # ══════════════════════════════════════════════════════════════════════
    # CORE / ABS
    # Have: Plank, Crunches, Sit-Ups, Toe Touches, Flutter Kicks,
    #       Mountain Climbers, Russian Twist, Side Plank, V-Ups,
    #       Jackknife, Hanging Leg Raise
    # Missing: cable crunch, ab wheel, dragon flag, bicycle crunch,
    #          dead bug, hollow body, reverse crunch, weighted plank
    # ══════════════════════════════════════════════════════════════════════
    {
        'name': 'Cable Crunch',
        'description': 'Kneel facing a high cable with rope attachment. Pull the rope down by crunching the abs, bringing elbows toward the knees. Allows progressive overload on the abs.',
        'exercise_type': 'strength',
        'primary_muscle': 'Abs',
        'complementary_muscle': None,
        'difficulty_level': 'intermediate',
        'base_exp': 16,
    },
    {
        'name': 'Ab Wheel Rollout',
        'description': 'Kneel and roll the ab wheel forward until the body is nearly horizontal, then pull back using the core. One of the most demanding anti-extension core exercises.',
        'exercise_type': 'core',
        'primary_muscle': 'Abs',
        'complementary_muscle': 'Lats, Shoulders',
        'difficulty_level': 'advanced',
        'base_exp': 28,
    },
    {
        'name': 'Dragon Flag',
        'description': 'Grip a bench overhead, lift the body to a rigid plank position, then lower slowly keeping the body straight. Bruce Lee\'s signature move. Extreme core challenge.',
        'exercise_type': 'core',
        'primary_muscle': 'Abs',
        'complementary_muscle': 'Core',
        'difficulty_level': 'advanced',
        'base_exp': 35,
    },
    {
        'name': 'Bicycle Crunch',
        'description': 'Lie on back, hands behind head. Alternate bringing opposite elbow to knee while extending the other leg. Targets both rectus abdominis and obliques simultaneously.',
        'exercise_type': 'core',
        'primary_muscle': 'Abs',
        'complementary_muscle': 'Obliques',
        'difficulty_level': 'beginner',
        'base_exp': 12,
    },
    {
        'name': 'Dead Bug',
        'description': 'Lie on back, arms and legs in the air. Lower opposite arm and leg toward the floor while pressing the lower back flat. Excellent anti-extension core stability exercise.',
        'exercise_type': 'core',
        'primary_muscle': 'Abs',
        'complementary_muscle': 'Core',
        'difficulty_level': 'beginner',
        'base_exp': 12,
    },
    {
        'name': 'Hollow Body Hold',
        'description': 'Lie on back, arms overhead, press lower back into floor and raise arms, head, and legs slightly. Hold the banana-shaped body position. Fundamental gymnastics core move.',
        'exercise_type': 'core',
        'primary_muscle': 'Abs',
        'complementary_muscle': 'Core',
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Reverse Crunch',
        'description': 'Lie on back with hands by sides. Pull knees toward the chest and lift the hips slightly off the floor. Targets the lower portion of the rectus abdominis.',
        'exercise_type': 'core',
        'primary_muscle': 'Abs',
        'complementary_muscle': None,
        'difficulty_level': 'beginner',
        'base_exp': 12,
    },
    {
        'name': 'Weighted Plank',
        'description': 'Standard plank position with a weight plate placed on the upper back by a partner. Progressive overload for the plank to continue building anti-extension core strength.',
        'exercise_type': 'core',
        'primary_muscle': 'Abs',
        'complementary_muscle': 'Shoulders',
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Toes to Bar',
        'description': 'Hang from a pull-up bar and raise straight legs to touch the bar. Full range hanging core exercise targeting the entire anterior core chain.',
        'exercise_type': 'core',
        'primary_muscle': 'Abs',
        'complementary_muscle': 'Hip Flexors, Lats',
        'difficulty_level': 'advanced',
        'base_exp': 28,
    },

    # ══════════════════════════════════════════════════════════════════════
    # LATS
    # Have: Close-Grip Pulldown, Straight Arm Pulldown, Reverse-Grip
    #       Pulldown, Rope Pulldown, Dumbbell Pullover, Barbell Pullover
    #       — NO ADVANCED exercises, only 1 beginner
    # Missing: single arm pulldown, kneeling lat pulldown, advanced pull variations
    # ══════════════════════════════════════════════════════════════════════
    {
        'name': 'Single Arm Lat Pulldown',
        'description': 'Attach a single handle to the lat pulldown machine. Pull down with one arm, allowing a natural torso lean for full lat stretch. Corrects side-to-side imbalances.',
        'exercise_type': 'strength',
        'primary_muscle': 'Lats',
        'complementary_muscle': 'Biceps',
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Kneeling Lat Pulldown',
        'description': 'Kneel facing a high cable and pull the bar or handle down to the chest. No seat to brace against forces deeper core engagement alongside lat activation.',
        'exercise_type': 'strength',
        'primary_muscle': 'Lats',
        'complementary_muscle': 'Core, Biceps',
        'difficulty_level': 'beginner',
        'base_exp': 14,
    },
    {
        'name': 'Weighted Pull-Up',
        'description': 'Attach a weight belt or hold a dumbbell between knees. Perform strict pull-ups with added resistance. The gold standard for lat mass and pulling strength.',
        'exercise_type': 'strength',
        'primary_muscle': 'Lats',
        'complementary_muscle': 'Biceps',
        'difficulty_level': 'advanced',
        'base_exp': 32,
    },
    {
        'name': 'Archer Pull-Up',
        'description': 'Wide grip pull-up where you pull toward one hand while the other arm stays extended. Alternates sides. Builds unilateral lat strength toward a one-arm pull-up.',
        'exercise_type': 'strength',
        'primary_muscle': 'Lats',
        'complementary_muscle': 'Biceps',
        'difficulty_level': 'advanced',
        'base_exp': 34,
    },
    {
        'name': 'Unilateral Dumbbell Pullover',
        'description': 'Perform the dumbbell pullover with one arm at a time. Greater range of motion and lat stretch than the two-arm version, with added rotational core demand.',
        'exercise_type': 'strength',
        'primary_muscle': 'Lats',
        'complementary_muscle': 'Chest',
        'difficulty_level': 'intermediate',
        'base_exp': 20,
    },

    # ══════════════════════════════════════════════════════════════════════
    # TRAPS
    # Have: Barbell Shrug, Dumbbell Shrugs, Barbell Upright Row — NO ADVANCED
    # Missing: cable shrug, dumbbell upright row, power shrug, rack pull
    # ══════════════════════════════════════════════════════════════════════
    {
        'name': 'Cable Shrug',
        'description': 'Stand at a cable machine, hold the bar with a straight-arm grip and shrug shoulders toward the ears. Constant cable tension maintains load at the bottom unlike a barbell.',
        'exercise_type': 'strength',
        'primary_muscle': 'Traps',
        'complementary_muscle': None,
        'difficulty_level': 'beginner',
        'base_exp': 12,
    },
    {
        'name': 'Behind the Back Barbell Shrug',
        'description': 'Hold barbell behind the glutes with straight arms and shrug. The posterior position shifts focus to the middle traps and is less common but highly effective.',
        'exercise_type': 'strength',
        'primary_muscle': 'Traps',
        'complementary_muscle': None,
        'difficulty_level': 'intermediate',
        'base_exp': 18,
    },
    {
        'name': 'Power Shrug',
        'description': 'Perform a barbell shrug with a slight knee dip and explosive drive. The momentum allows heavier loads and trains the upper trap explosively. Often used in Olympic lifting prep.',
        'exercise_type': 'power',
        'primary_muscle': 'Traps',
        'complementary_muscle': 'Shoulders',
        'difficulty_level': 'advanced',
        'base_exp': 26,
    },
    {
        'name': 'Farmer Walk with Shrug',
        'description': 'Perform a farmer\'s carry and add deliberate shrugs every few steps. Combines loaded carry stability with upper trap activation for functional trap development.',
        'exercise_type': 'functional',
        'primary_muscle': 'Traps',
        'complementary_muscle': 'Forearms, Core',
        'difficulty_level': 'intermediate',
        'base_exp': 20,
    },
]


# ════════════════════════════════════════════════════════════════════════════
# GROUP MAP — for filtering by --group flag
# ════════════════════════════════════════════════════════════════════════════

GROUP_MAP = {
    'chest':     ['Chest'],
    'back':      ['Back'],
    'biceps':    ['Biceps'],
    'triceps':   ['Triceps'],
    'shoulders': ['Shoulders'],
    'legs':      ['Legs'],
    'hamstrings':['Hamstrings'],
    'glutes':    ['Glutes'],
    'calves':    ['Calves'],
    'core':      ['Abs', 'Core'],
    'lats':      ['Lats'],
    'traps':     ['Traps'],
}


# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

def get_existing_names(conn) -> set:
    rows = conn.execute("SELECT LOWER(TRIM(name)) FROM exercises").fetchall()
    return {r[0] for r in rows}


def filter_exercises(exercises, group: str | None) -> list:
    if not group:
        return exercises
    muscles = GROUP_MAP.get(group.lower(), [])
    if not muscles:
        print(f"\n❌  Unknown group '{group}'. Available: {', '.join(GROUP_MAP.keys())}")
        sys.exit(1)
    return [e for e in exercises if e['primary_muscle'] in muscles]


def print_plan(exercises, existing: set):
    from collections import Counter
    groups = Counter(e['primary_muscle'] for e in exercises)

    print(f"\n{'═'*70}")
    print(f"  EXERCISE BOOSTER — {'DRY RUN' if True else 'COMMIT'}")
    print(f"  {len(exercises)} exercises planned across {len(groups)} muscle groups")
    print(f"{'═'*70}\n")

    current_muscle = None
    skipped = []
    to_add = []

    for e in exercises:
        is_dupe = e['name'].lower().strip() in existing
        if e['primary_muscle'] != current_muscle:
            current_muscle = e['primary_muscle']
            print(f"  ── {current_muscle.upper()} {'─'*(50-len(current_muscle))}")

        status = '⏭  SKIP (exists)' if is_dupe else '✅ ADD '
        diff_tag = {'beginner': '🟢', 'intermediate': '🟡', 'advanced': '🔴'}.get(e['difficulty_level'], '⚪')
        print(f"     {status}  {diff_tag} [{e['difficulty_level'][:3].upper()}] {e['name']}  ({e['base_exp']} EXP)")

        if is_dupe:
            skipped.append(e['name'])
        else:
            to_add.append(e)

    print(f"\n  {'─'*68}")
    print(f"  Total to add:  {len(to_add)}")
    print(f"  Already exist: {len(skipped)}")
    if skipped:
        print(f"  Skipped:       {', '.join(skipped)}")
    print()
    return to_add


def insert_exercises(conn, exercises: list, existing: set) -> int:
    inserted = 0
    for e in exercises:
        if e['name'].lower().strip() in existing:
            continue
        conn.execute(
            """INSERT INTO exercises
               (name, description, exercise_type, primary_muscle,
                complementary_muscle, difficulty_level, base_exp, created_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                e['name'],
                e['description'],
                e['exercise_type'],
                e['primary_muscle'],
                e.get('complementary_muscle'),
                e['difficulty_level'],
                e['base_exp'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            )
        )
        inserted += 1
    return inserted


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='LevelUp Gym — Exercise Booster')
    parser.add_argument('--commit', action='store_true',
                        help='Write exercises to database (default is dry-run)')
    parser.add_argument('--group', type=str, default=None,
                        help='Only process one group: chest|back|biceps|triceps|shoulders|'
                             'legs|hamstrings|glutes|calves|core|lats|traps')
    parser.add_argument('--db', type=str, default=DB_PATH,
                        help='Path to SQLite database file')
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"\n❌  Database not found at: {args.db}")
        print(f"    Use --db /path/to/gym.db to specify the correct path.\n")
        sys.exit(1)

    conn = sqlite3.connect(args.db)
    existing = get_existing_names(conn)

    exercises = filter_exercises(NEW_EXERCISES, args.group)
    to_add = print_plan(exercises, existing)

    if not args.commit:
        print("  ℹ️   DRY RUN — no changes made.")
        print("      Run with --commit to write to the database.\n")
        conn.close()
        return

    # Commit
    try:
        inserted = insert_exercises(conn, exercises, existing)
        conn.commit()
        print(f"  ✅  Successfully inserted {inserted} exercise(s) into the database.\n")
    except Exception as e:
        conn.rollback()
        print(f"  ❌  Error: {e}\n")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
