"""
routine_builder.py
════════════════════════════════════════════════════════════════════
Generates 24 hand-crafted routines for the LevelUp Gym system.

Routines are designed around the five player classes and their
exercise-type XP bonuses:

  Warrior  → strength, power      (heavy compound lifting)
  Ranger   → cardio, endurance    (running, rowing, stamina)
  Tank     → core, functional     (stability, carries, slams)
  Assassin → hiit, agility        (fast circuits, drills)
  Mage     → balance, flexibility (control, mobility, flow)

24 Routines across 3 difficulty tiers:
  BEGINNER (6)      — machines, bodyweight, simple movement patterns
  INTERMEDIATE (10) — free weights, circuits, class-specific splits
  ADVANCED (8)      — compound heavy, power, athletic performance

Usage:
    python routine_builder.py                   # dry-run (preview only)
    python routine_builder.py --commit          # write to database
    python routine_builder.py --commit --tier beginner
    python routine_builder.py --commit --tier intermediate
    python routine_builder.py --commit --tier advanced
    python routine_builder.py --commit --class warrior
════════════════════════════════════════════════════════════════════
"""

import sqlite3
import argparse
import os
import sys
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'levelup_gym.db')

# ════════════════════════════════════════════════════════════════════════════
# CLASS DEFINITIONS (for documentation & display)
# ════════════════════════════════════════════════════════════════════════════
CLASS_BONUSES = {
    'Warrior':  ['strength', 'power'],
    'Ranger':   ['cardio', 'endurance'],
    'Tank':     ['core', 'functional'],
    'Assassin': ['hiit', 'agility'],
    'Mage':     ['balance', 'flexibility'],
    'All':      [],
}

# ════════════════════════════════════════════════════════════════════════════
# ROUTINE DEFINITIONS
#
# Each routine dict:
#   name        → routine_name in DB
#   description → shown on routine card
#   tier        → 'beginner' | 'intermediate' | 'advanced'
#   class_focus → which class(es) benefit most from this routine
#   split       → Push | Pull | Legs | Upper | Lower | Full Body | Core | Cardio
#   exercises   → list of dicts:
#                   id          → exercise_id (verified against DB)
#                   sets        → number of sets
#                   reps        → reps per set (or seconds if measurement='seconds')
#                   rest        → rest in seconds between sets
#                   measurement → 'reps' | 'seconds'
# ════════════════════════════════════════════════════════════════════════════

ROUTINES = [

    # ══════════════════════════════════════════════════════════════════════
    # BEGINNER TIER (6 routines)
    # Goals: build movement patterns, learn the gym, zero overwhelm
    # All exercises are machines, bodyweight, or light dumbbells
    # ══════════════════════════════════════════════════════════════════════

    {
        'name':        'First Contact',
        'description': (
            'Your first step into strength training. All machine-based exercises '
            'guide you through safe movement patterns and build your foundation. '
            'Perfect for complete beginners.'
        ),
        'tier':        'beginner',
        'class_focus': 'Warrior',
        'split':       'Full Body',
        'exercises': [
            # id   sets reps  rest  measurement
            {'id': 8,   'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Leg Press
            {'id': 67,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Chest Press Machine
            {'id': 182, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Seated Row Machine
            {'id': 191, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Machine Shoulder Press
            {'id': 187, 'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # Leg Extension Machine
            {'id': 188, 'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # Lying Leg Curl Machine
            {'id': 185, 'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # Cable Triceps Pushdown
            {'id': 184, 'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # Cable Curl
            {'id': 195, 'sets': 3, 'reps': 20, 'rest': 30,  'measurement': 'reps'},   # Machine Calf Raise
        ],
    },

    {
        'name':        'Iron Foundation',
        'description': (
            'A balanced full-body routine combining bodyweight and dumbbell '
            'movements. Builds overall strength and stability with exercises '
            'that carry directly into more advanced training.'
        ),
        'tier':        'beginner',
        'class_focus': 'Warrior',
        'split':       'Full Body',
        'exercises': [
            {'id': 106, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Goblet Squat
            {'id': 2,   'sets': 3, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # Push Ups
            {'id': 181, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Lat Pulldown
            {'id': 65,  'sets': 3, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # Dumbbell Bench Press
            {'id': 5,   'sets': 3, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # Dumbbell Bent-Over Row
            {'id': 110, 'sets': 3, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # Reverse Lunges
            {'id': 11,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Dumbbell Shoulder Press
            {'id': 15,  'sets': 3, 'reps': 30, 'rest': 45,  'measurement': 'seconds'},# Plank
            {'id': 33,  'sets': 3, 'reps': 20, 'rest': 30,  'measurement': 'reps'},   # Seated Calf Raise
        ],
    },

    {
        'name':        'Scout Training',
        'description': (
            'Built for endurance and movement. Light cardio, bodyweight drills, '
            'and functional exercises that improve stamina and body awareness. '
            'Rangers and Assassins will earn bonus XP on every set.'
        ),
        'tier':        'beginner',
        'class_focus': 'Ranger',
        'split':       'Cardio',
        'exercises': [
            {'id': 38,  'sets': 3, 'reps': 30, 'rest': 30,  'measurement': 'reps'},   # Jumping Jacks
            {'id': 138, 'sets': 3, 'reps': 60, 'rest': 60,  'measurement': 'seconds'},# Jogging
            {'id': 115, 'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Step-Ups
            {'id': 106, 'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Goblet Squat
            {'id': 110, 'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Reverse Lunges
            {'id': 117, 'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # Glute Bridge
            {'id': 149, 'sets': 3, 'reps': 20, 'rest': 30,  'measurement': 'reps'},   # Side Shuffles
            {'id': 141, 'sets': 3, 'reps': 20, 'rest': 30,  'measurement': 'reps'},   # Butt Kicks
            {'id': 15,  'sets': 3, 'reps': 30, 'rest': 45,  'measurement': 'seconds'},# Plank
        ],
    },

    {
        'name':        'Core Awakening',
        'description': (
            'A dedicated core session for beginners. Builds abdominal strength, '
            'spinal stability, and body control from the ground up. '
            'Tanks earn boosted XP on every exercise.'
        ),
        'tier':        'beginner',
        'class_focus': 'Tank',
        'split':       'Core',
        'exercises': [
            {'id': 15,  'sets': 3, 'reps': 30, 'rest': 45,  'measurement': 'seconds'},# Plank
            {'id': 130, 'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # Crunches
            {'id': 117, 'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # Glute Bridge
            {'id': 133, 'sets': 3, 'reps': 20, 'rest': 45,  'measurement': 'reps'},   # Flutter Kicks
            {'id': 136, 'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Toe Touches
            {'id': 17,  'sets': 3, 'reps': 20, 'rest': 45,  'measurement': 'reps'},   # Russian Twist
            {'id': 176, 'sets': 3, 'reps': 30, 'rest': 30,  'measurement': 'seconds'},# Standing Knee Raise Hold
            {'id': 131, 'sets': 3, 'reps': 20, 'rest': 30,  'measurement': 'seconds'},# Side Plank
            {'id': 162, 'sets': 3, 'reps': 15, 'rest': 30,  'measurement': 'reps'},   # Torso Twist
        ],
    },

    {
        'name':        'Push Protocol I',
        'description': (
            'A beginner push day targeting chest, shoulders, and triceps using '
            'machines and dumbbells. Master the pressing movement pattern before '
            'advancing to barbells.'
        ),
        'tier':        'beginner',
        'class_focus': 'Warrior',
        'split':       'Push',
        'exercises': [
            {'id': 2,   'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Push Ups
            {'id': 180, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Seated Chest Press Machine
            {'id': 62,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Pec Deck
            {'id': 191, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Machine Shoulder Press
            {'id': 199, 'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # Lateral Raise
            {'id': 200, 'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Front Raise
            {'id': 29,  'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # Triceps Pushdown
            {'id': 103, 'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Kickback
        ],
    },

    {
        'name':        'Pull Protocol I',
        'description': (
            'A beginner pull day building back thickness and bicep strength. '
            'Machine and cable-based so you can focus entirely on feeling the '
            'right muscles work before loading a barbell.'
        ),
        'tier':        'beginner',
        'class_focus': 'Warrior',
        'split':       'Pull',
        'exercises': [
            {'id': 181, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Lat Pulldown
            {'id': 6,   'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Wide-Grip Pulldown
            {'id': 182, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Seated Row Machine
            {'id': 5,   'sets': 3, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # Dumbbell Bent-Over Row
            {'id': 13,  'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Barbell Curl
            {'id': 96,  'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Hammer Curl
            {'id': 196, 'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Dumbbell Bicep Curl
            {'id': 86,  'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # Barbell Shrug
        ],
    },

    # ══════════════════════════════════════════════════════════════════════
    # INTERMEDIATE TIER (10 routines)
    # Goals: progressive overload, class identity, split training
    # Free weights introduced, circuits used, class bonuses become relevant
    # ══════════════════════════════════════════════════════════════════════

    {
        'name':        "Warrior's Push",
        'description': (
            'Strength and power pressing session for Warriors. Heavy barbell '
            'bench, explosive push press, and targeted tricep work. '
            'Warriors earn double XP on every exercise in this routine.'
        ),
        'tier':        'intermediate',
        'class_focus': 'Warrior',
        'split':       'Push',
        'exercises': [
            {'id': 1,   'sets': 4, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Barbell Bench Press
            {'id': 192, 'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Incline Chest Press Machine
            {'id': 63,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Cable Crossover
            {'id': 11,  'sets': 4, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Dumbbell Shoulder Press
            {'id': 186, 'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # Cable Lateral Raise
            {'id': 122, 'sets': 3, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Push Press (power — Warrior XP)
            {'id': 102, 'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Close Grip Bench Press
            {'id': 100, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Lying Triceps Extension
        ],
    },

    {
        'name':        "Warrior's Pull",
        'description': (
            'A strength-focused back and biceps session for Warriors. '
            'Heavy rows, vertical pulling, and arm volume. '
            'Every strength exercise here gives Warriors bonus XP.'
        ),
        'tier':        'intermediate',
        'class_focus': 'Warrior',
        'split':       'Pull',
        'exercises': [
            {'id': 71,  'sets': 4, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Barbell Row
            {'id': 5,   'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Dumbbell Bent-Over Row
            {'id': 32,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Seated Cable Row
            {'id': 73,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Reverse-Grip Pulldown
            {'id': 81,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Dumbbell Pullover
            {'id': 95,  'sets': 3, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # EZ Barbell Preacher Curl
            {'id': 97,  'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Incline Dumbbell Curl
            {'id': 91,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Barbell Upright Row
        ],
    },

    {
        'name':        "Warrior's Legs",
        'description': (
            'Strength-based leg day for Warriors. Squats, deadlifts, and '
            'compound lower body movements loaded for progressive overload. '
            'Strength exercises trigger Warrior XP multipliers.'
        ),
        'tier':        'intermediate',
        'class_focus': 'Warrior',
        'split':       'Legs',
        'exercises': [
            {'id': 7,   'sets': 4, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Squat
            {'id': 43,  'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Romanian Deadlift
            {'id': 112, 'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Bulgarian Split Squat
            {'id': 45,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Dumbbell Step Ups
            {'id': 85,  'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Dumbbell Deadlift
            {'id': 118, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Hip Thrust
            {'id': 109, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Walking Lunges
            {'id': 30,  'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # Lying Leg Curl
            {'id': 195, 'sets': 4, 'reps': 20, 'rest': 30,  'measurement': 'reps'},   # Machine Calf Raise
        ],
    },

    {
        'name':        "Ranger's Endurance Run",
        'description': (
            'A stamina-building cardio circuit for Rangers. Rowing, running '
            'intervals, and sustained aerobic effort that builds the engine '
            'to outlast every other class. Rangers earn XP on every rep.'
        ),
        'tier':        'intermediate',
        'class_focus': 'Ranger',
        'split':       'Cardio',
        'exercises': [
            {'id': 34,  'sets': 3, 'reps': 60, 'rest': 30,  'measurement': 'seconds'},# Rowing Machine
            {'id': 20,  'sets': 3, 'reps': 60, 'rest': 30,  'measurement': 'seconds'},# Jump Rope
            {'id': 55,  'sets': 3, 'reps': 40, 'rest': 30,  'measurement': 'reps'},   # High Knees
            {'id': 41,  'sets': 3, 'reps': 90, 'rest': 60,  'measurement': 'seconds'},# Interval Run
            {'id': 140, 'sets': 3, 'reps': 60, 'rest': 45,  'measurement': 'seconds'},# Stair Climb
            {'id': 59,  'sets': 3, 'reps': 20, 'rest': 30,  'measurement': 'reps'},   # Skater Hops
            {'id': 37,  'sets': 3, 'reps': 60, 'rest': 30,  'measurement': 'seconds'},# Row Intervals
            {'id': 114, 'sets': 3, 'reps': 45, 'rest': 30,  'measurement': 'seconds'},# Wall Sit
        ],
    },

    {
        'name':        'Iron Citadel',
        'description': (
            'Core and functional training for Tanks. Carries, slams, '
            'stability holds, and full-body functional movements that build '
            'the kind of strength that protects you and everyone around you.'
        ),
        'tier':        'intermediate',
        'class_focus': 'Tank',
        'split':       'Core',
        'exercises': [
            {'id': 57,  'sets': 3, 'reps': 30, 'rest': 45,  'measurement': 'reps'},   # Mountain Climbers
            {'id': 26,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Medicine Ball Slam
            {'id': 175, 'sets': 3, 'reps': 45, 'rest': 45,  'measurement': 'seconds'},# Stability Ball Plank
            {'id': 17,  'sets': 3, 'reps': 20, 'rest': 45,  'measurement': 'reps'},   # Russian Twist
            {'id': 123, 'sets': 3, 'reps': 15, 'rest': 60,  'measurement': 'reps'},   # Kettlebell Swing
            {'id': 131, 'sets': 3, 'reps': 30, 'rest': 45,  'measurement': 'seconds'},# Side Plank
            {'id': 50,  'sets': 3, 'reps': 40, 'rest': 60,  'measurement': 'seconds'},# Farmer's Carry
            {'id': 178, 'sets': 3, 'reps': 45, 'rest': 45,  'measurement': 'seconds'},# Balance Board Shift
        ],
    },

    {
        'name':        'Ghost Protocol',
        'description': (
            'HIIT and agility circuit designed for Assassins. Fast-paced, '
            'explosive, no mercy. Every movement demands quick reactions and '
            'athletic precision. Assassins earn double XP throughout.'
        ),
        'tier':        'intermediate',
        'class_focus': 'Assassin',
        'split':       'Full Body',
        'exercises': [
            {'id': 55,  'sets': 4, 'reps': 30, 'rest': 30,  'measurement': 'reps'},   # High Knees (hiit)
            {'id': 28,  'sets': 4, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Jump Squat (power)
            {'id': 59,  'sets': 3, 'reps': 20, 'rest': 30,  'measurement': 'reps'},   # Skater Hops (hiit)
            {'id': 148, 'sets': 3, 'reps': 30, 'rest': 30,  'measurement': 'seconds'},# Ladder Drills (agility)
            {'id': 147, 'sets': 3, 'reps': 30, 'rest': 60,  'measurement': 'seconds'},# Cone Sprints (agility)
            {'id': 57,  'sets': 3, 'reps': 30, 'rest': 30,  'measurement': 'reps'},   # Mountain Climbers (hiit)
            {'id': 145, 'sets': 3, 'reps': 30, 'rest': 45,  'measurement': 'seconds'},# Battle Rope Alternating Waves
            {'id': 142, 'sets': 3, 'reps': 20, 'rest': 30,  'measurement': 'reps'},   # Skater Jumps (agility)
        ],
    },

    {
        'name':        "Mage's Awakening",
        'description': (
            'Balance and mobility training for Mages. Every movement demands '
            'body awareness, proprioception, and control. A session that leaves '
            'you feeling lighter and more coordinated. Mages earn bonus XP here.'
        ),
        'tier':        'intermediate',
        'class_focus': 'Mage',
        'split':       'Full Body',
        'exercises': [
            {'id': 173, 'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Bosu Ball Squat (balance)
            {'id': 175, 'sets': 3, 'reps': 45, 'rest': 45,  'measurement': 'seconds'},# Stability Ball Plank (balance)
            {'id': 174, 'sets': 3, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # Single-Leg Romanian Deadlift (balance)
            {'id': 178, 'sets': 3, 'reps': 45, 'rest': 45,  'measurement': 'seconds'},# Balance Board Shift (balance)
            {'id': 163, 'sets': 3, 'reps': 10, 'rest': 30,  'measurement': 'reps'},   # World's Greatest Stretch (flexibility)
            {'id': 164, 'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Dynamic Lunges with Twist (mobility)
            {'id': 168, 'sets': 3, 'reps': 30, 'rest': 30,  'measurement': 'seconds'},# Deep Squat Hold (mobility)
            {'id': 121, 'sets': 3, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # Single-Leg Deadlift (balance)
            {'id': 131, 'sets': 3, 'reps': 30, 'rest': 45,  'measurement': 'seconds'},# Side Plank
        ],
    },

    {
        'name':        'Gladiator Circuit',
        'description': (
            'A full body intermediate circuit that mixes strength and power. '
            'Designed for clients without a fixed class who want a hard, '
            'complete workout in one session.'
        ),
        'tier':        'intermediate',
        'class_focus': 'All',
        'split':       'Full Body',
        'exercises': [
            {'id': 7,   'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Squat
            {'id': 71,  'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Barbell Row
            {'id': 122, 'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Push Press (power)
            {'id': 123, 'sets': 3, 'reps': 15, 'rest': 60,  'measurement': 'reps'},   # Kettlebell Swing
            {'id': 57,  'sets': 3, 'reps': 30, 'rest': 30,  'measurement': 'reps'},   # Mountain Climbers
            {'id': 106, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Goblet Squat
            {'id': 26,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Medicine Ball Slam
            {'id': 109, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Walking Lunges
        ],
    },

    {
        'name':        'Lower Body Blitz',
        'description': (
            'A dedicated lower body session covering quads, hamstrings, '
            'glutes, and calves with a mix of strength and functional movements. '
            'Suitable for any class looking to build leg power.'
        ),
        'tier':        'intermediate',
        'class_focus': 'All',
        'split':       'Lower',
        'exercises': [
            {'id': 7,   'sets': 4, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Squat
            {'id': 43,  'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Romanian Deadlift
            {'id': 112, 'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Bulgarian Split Squat
            {'id': 118, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Hip Thrust
            {'id': 109, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Walking Lunges
            {'id': 30,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Lying Leg Curl
            {'id': 117, 'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # Glute Bridge
            {'id': 195, 'sets': 4, 'reps': 20, 'rest': 30,  'measurement': 'reps'},   # Machine Calf Raise
        ],
    },

    {
        'name':        'Upper Body Forge',
        'description': (
            'A push-pull upper body session covering chest, back, shoulders, '
            'biceps, and triceps. Great for clients training 3 days a week who '
            'want complete upper body development each session.'
        ),
        'tier':        'intermediate',
        'class_focus': 'All',
        'split':       'Upper',
        'exercises': [
            {'id': 1,   'sets': 4, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Barbell Bench Press
            {'id': 71,  'sets': 4, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Barbell Row
            {'id': 11,  'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Dumbbell Shoulder Press
            {'id': 32,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Seated Cable Row
            {'id': 63,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Cable Crossover
            {'id': 204, 'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # Cable Face Pull
            {'id': 94,  'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Rope Cable Curl
            {'id': 101, 'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Dumbbell Overhead Triceps Extension
        ],
    },

    # ══════════════════════════════════════════════════════════════════════
    # ADVANCED TIER (8 routines)
    # Goals: maximum output, class mastery, performance training
    # Heavy compound movements, Olympic lifts, extreme conditioning
    # ══════════════════════════════════════════════════════════════════════

    {
        'name':        "Warlord's Push",
        'description': (
            'Maximum intensity push session for elite Warriors. Heavy 5x5 '
            'bench, explosive push press, and power-focused pressing. '
            'Every strength and power movement drops Warrior XP bombs.'
        ),
        'tier':        'advanced',
        'class_focus': 'Warrior',
        'split':       'Push',
        'exercises': [
            {'id': 1,   'sets': 5, 'reps': 5,  'rest': 120, 'measurement': 'reps'},   # Barbell Bench Press
            {'id': 127, 'sets': 4, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Explosive Push-Ups (power)
            {'id': 64,  'sets': 4, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Incline Barbell Bench Press
            {'id': 122, 'sets': 4, 'reps': 6,  'rest': 120, 'measurement': 'reps'},   # Push Press (power — Warrior XP)
            {'id': 183, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Cable Fly
            {'id': 22,  'sets': 3, 'reps': 12, 'rest': 75,  'measurement': 'reps'},   # Bench Dips
            {'id': 102, 'sets': 4, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Close Grip Bench Press
            {'id': 100, 'sets': 3, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # Lying Triceps Extension
        ],
    },

    {
        'name':        "Warlord's Pull",
        'description': (
            'Elite back and biceps training for Warriors. Deadlifts, pull-ups, '
            'and heavy rows that build the posterior chain capable of carrying '
            'any weight. Strength exercises award maximum Warrior XP.'
        ),
        'tier':        'advanced',
        'class_focus': 'Warrior',
        'split':       'Pull',
        'exercises': [
            {'id': 10,  'sets': 5, 'reps': 3,  'rest': 180, 'measurement': 'reps'},   # Barbell Deadlift
            {'id': 77,  'sets': 4, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Pull Up
            {'id': 71,  'sets': 4, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Barbell Row
            {'id': 75,  'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # T-Bar Rows
            {'id': 79,  'sets': 3, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Pull Up with a Supinated Grip
            {'id': 76,  'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Barbell Bent Over Rows Supinated Grip
            {'id': 95,  'sets': 3, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # EZ Barbell Preacher Curl
            {'id': 97,  'sets': 3, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Incline Dumbbell Curl
        ],
    },

    {
        'name':        "Warlord's Legs",
        'description': (
            'The most brutal leg session in the library. Heavy squats, '
            'sumo deadlifts, explosive jumps, and unilateral strength work '
            'for Warriors who want legs that can move mountains.'
        ),
        'tier':        'advanced',
        'class_focus': 'Warrior',
        'split':       'Legs',
        'exercises': [
            {'id': 7,   'sets': 5, 'reps': 5,  'rest': 120, 'measurement': 'reps'},   # Squat
            {'id': 194, 'sets': 4, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Hack Squat
            {'id': 83,  'sets': 4, 'reps': 6,  'rest': 120, 'measurement': 'reps'},   # Barbell Sumo Deadlift
            {'id': 112, 'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Bulgarian Split Squat
            {'id': 42,  'sets': 3, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Front Squat
            {'id': 58,  'sets': 4, 'reps': 8,  'rest': 75,  'measurement': 'reps'},   # Box Jumps (hiit)
            {'id': 221, 'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Explosive Lunges (power)
            {'id': 30,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Lying Leg Curl
        ],
    },

    {
        'name':        "Ranger's Gauntlet",
        'description': (
            'Elite endurance and speed work for advanced Rangers. Sprint '
            'intervals, resisted runs, and rowing sprints at max intensity. '
            'This session separates Rangers from everyone else.'
        ),
        'tier':        'advanced',
        'class_focus': 'Ranger',
        'split':       'Cardio',
        'exercises': [
            {'id': 144, 'sets': 4, 'reps': 45, 'rest': 30,  'measurement': 'seconds'},# Row Sprints (hiit)
            {'id': 139, 'sets': 4, 'reps': 30, 'rest': 60,  'measurement': 'seconds'},# Sprinting (speed)
            {'id': 146, 'sets': 3, 'reps': 60, 'rest': 30,  'measurement': 'seconds'},# Speed Skipping (speed)
            {'id': 128, 'sets': 3, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # Burpee Box Jump (hiit)
            {'id': 153, 'sets': 4, 'reps': 20, 'rest': 60,  'measurement': 'seconds'},# Sprint Starts (speed)
            {'id': 154, 'sets': 3, 'reps': 30, 'rest': 90,  'measurement': 'seconds'},# Resisted Sprint (power)
            {'id': 222, 'sets': 3, 'reps': 30, 'rest': 90,  'measurement': 'seconds'},# Resistance Band Sprint (speed)
            {'id': 41,  'sets': 3, 'reps': 90, 'rest': 60,  'measurement': 'seconds'},# Interval Run (running)
        ],
    },

    {
        'name':        'Iron Fortress',
        'description': (
            'Advanced Tank protocol. Olympic-style functional movements, '
            'heavy carries, tire flips, and max-effort core work. '
            'Tanks become walls of pure functional strength.'
        ),
        'tier':        'advanced',
        'class_focus': 'Tank',
        'split':       'Full Body',
        'exercises': [
            {'id': 125, 'sets': 4, 'reps': 5,  'rest': 90,  'measurement': 'reps'},   # Turkish Get-Up (functional)
            {'id': 210, 'sets': 3, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Kettlebell Snatch (functional)
            {'id': 53,  'sets': 3, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Tire Flip (functional)
            {'id': 132, 'sets': 4, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Hanging Leg Raise (core)
            {'id': 50,  'sets': 4, 'reps': 40, 'rest': 60,  'measurement': 'seconds'},# Farmer's Carry (functional)
            {'id': 212, 'sets': 3, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Sandbag Clean (functional)
            {'id': 26,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Medicine Ball Slam (power)
            {'id': 134, 'sets': 3, 'reps': 15, 'rest': 45,  'measurement': 'reps'},   # V-Ups (core)
        ],
    },

    {
        'name':        'Shadow Strike',
        'description': (
            'Maximum intensity HIIT and agility for elite Assassins. Box jumps, '
            'burpees, sprint drills, and explosive circuits at full speed. '
            'No rest for the deadly. Assassins earn max XP here.'
        ),
        'tier':        'advanced',
        'class_focus': 'Assassin',
        'split':       'Full Body',
        'exercises': [
            {'id': 128, 'sets': 4, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # Burpee Box Jump (hiit)
            {'id': 58,  'sets': 4, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # Box Jumps (hiit)
            {'id': 56,  'sets': 4, 'reps': 12, 'rest': 45,  'measurement': 'reps'},   # Jump Lunges (hiit)
            {'id': 147, 'sets': 4, 'reps': 30, 'rest': 45,  'measurement': 'seconds'},# Cone Sprints (agility)
            {'id': 48,  'sets': 3, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Man Maker (full-body)
            {'id': 144, 'sets': 3, 'reps': 30, 'rest': 45,  'measurement': 'seconds'},# Row Sprints (hiit)
            {'id': 153, 'sets': 4, 'reps': 20, 'rest': 60,  'measurement': 'seconds'},# Sprint Starts (speed)
            {'id': 152, 'sets': 3, 'reps': 30, 'rest': 45,  'measurement': 'seconds'},# Zigzag Runs (agility)
        ],
    },

    {
        'name':        'Arcane Mastery',
        'description': (
            'The pinnacle Mage session. Pistol squats, Turkish get-ups, '
            'and balance challenges that require complete body control and '
            'spatial awareness. True mastery of movement over raw force.'
        ),
        'tier':        'advanced',
        'class_focus': 'Mage',
        'split':       'Full Body',
        'exercises': [
            {'id': 113, 'sets': 4, 'reps': 6,  'rest': 90,  'measurement': 'reps'},   # Pistol Squat (balance)
            {'id': 125, 'sets': 3, 'reps': 5,  'rest': 90,  'measurement': 'reps'},   # Turkish Get-Up (functional)
            {'id': 174, 'sets': 3, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # Single-Leg Romanian Deadlift (balance)
            {'id': 173, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Bosu Ball Squat (balance)
            {'id': 163, 'sets': 3, 'reps': 10, 'rest': 30,  'measurement': 'reps'},   # World's Greatest Stretch (flexibility)
            {'id': 132, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Hanging Leg Raise (core)
            {'id': 178, 'sets': 3, 'reps': 45, 'rest': 45,  'measurement': 'seconds'},# Balance Board Shift (balance)
            {'id': 175, 'sets': 3, 'reps': 60, 'rest': 45,  'measurement': 'seconds'},# Stability Ball Plank (balance)
            {'id': 121, 'sets': 3, 'reps': 10, 'rest': 60,  'measurement': 'reps'},   # Single-Leg Deadlift (balance)
        ],
    },

    {
        'name':        "Titan's Wrath",
        'description': (
            'The ultimate advanced full-body session. Power cleans, deadlifts, '
            'explosive pushing, box jumps, and max-effort conditioning. '
            'For clients who have mastered everything else.'
        ),
        'tier':        'advanced',
        'class_focus': 'All',
        'split':       'Full Body',
        'exercises': [
            {'id': 23,  'sets': 4, 'reps': 5,  'rest': 120, 'measurement': 'reps'},   # Power Clean (power)
            {'id': 10,  'sets': 4, 'reps': 5,  'rest': 120, 'measurement': 'reps'},   # Barbell Deadlift (strength)
            {'id': 71,  'sets': 3, 'reps': 8,  'rest': 90,  'measurement': 'reps'},   # Barbell Row (strength)
            {'id': 127, 'sets': 3, 'reps': 10, 'rest': 75,  'measurement': 'reps'},   # Explosive Push-Ups (power)
            {'id': 58,  'sets': 4, 'reps': 8,  'rest': 75,  'measurement': 'reps'},   # Box Jumps (hiit)
            {'id': 44,  'sets': 3, 'reps': 6,  'rest': 120, 'measurement': 'reps'},   # Clean and Press (compound)
            {'id': 132, 'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Hanging Leg Raise (core)
            {'id': 21,  'sets': 3, 'reps': 12, 'rest': 60,  'measurement': 'reps'},   # Burpees (strength)
        ],
    },
]


# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

TIER_COLORS = {
    'beginner':     '\033[92m',   # green
    'intermediate': '\033[93m',   # yellow
    'advanced':     '\033[91m',   # red
}
CLASS_ICONS = {
    'Warrior': '⚔️ ', 'Ranger': '🏹', 'Tank': '🛡️ ',
    'Assassin': '🗡️ ', 'Mage': '🔮', 'All': '⭐',
}
RESET = '\033[0m'
BOLD  = '\033[1m'

def colored(text, color): return f"{color}{text}{RESET}"


def get_existing_routine_names(conn):
    rows = conn.execute("SELECT LOWER(TRIM(routine_name)) FROM routines").fetchall()
    return {r[0] for r in rows}


def get_exercise_name(conn, exercise_id):
    row = conn.execute(
        "SELECT name FROM exercises WHERE exercise_id=?", (exercise_id,)
    ).fetchone()
    return row['name'] if row else f'[UNKNOWN ID {exercise_id}]'


def calc_total_exp(conn, routine):
    total = 0
    for ex in routine['exercises']:
        row = conn.execute(
            "SELECT base_exp FROM exercises WHERE exercise_id=?", (ex['id'],)
        ).fetchone()
        if row:
            total += row['base_exp'] * ex['sets']
    return total


def filter_routines(routines, tier=None, class_focus=None):
    result = routines
    if tier:
        result = [r for r in result if r['tier'].lower() == tier.lower()]
    if class_focus:
        result = [
            r for r in result
            if r['class_focus'].lower() in (class_focus.lower(), 'all')
               or class_focus.lower() == 'all'
        ]
    return result


def print_plan(conn, routines, existing_names, commit):
    mode = f"{BOLD}{'COMMIT' if commit else 'DRY RUN'}{RESET}"
    print(f"\n  Routine Builder  |  Mode: {mode}")
    print(f"  {24} routines defined  |  Checking against {len(existing_names)} existing\n")

    by_tier = {'beginner': [], 'intermediate': [], 'advanced': []}
    for r in routines:
        by_tier[r['tier']].append(r)

    to_insert = []
    skip_count = 0

    for tier in ('beginner', 'intermediate', 'advanced'):
        tier_routines = by_tier.get(tier, [])
        if not tier_routines:
            continue

        col = TIER_COLORS[tier]
        print(f"{BOLD}{col}  {'═'*64}{RESET}")
        print(f"{BOLD}{col}  {tier.upper()} — {len(tier_routines)} routines{RESET}")
        print(f"{BOLD}{col}  {'═'*64}{RESET}\n")

        for r in tier_routines:
            is_dupe = r['name'].lower().strip() in existing_names
            icon = CLASS_ICONS.get(r['class_focus'], '  ')
            total_exp = calc_total_exp(conn, r)
            ex_count = len(r['exercises'])
            bonus_note = (
                f"  [Bonus: {', '.join(CLASS_BONUSES[r['class_focus']])}]"
                if r['class_focus'] != 'All' and CLASS_BONUSES.get(r['class_focus'])
                else ''
            )

            if is_dupe:
                print(f"  ⏭   {icon} {r['name']}  — SKIP (already exists)")
                skip_count += 1
                continue

            status_col = col if commit else '\033[93m'
            action = '✅ ADD' if commit else '~  ADD'
            print(f"  {status_col}{action}{RESET}  {icon} {BOLD}{r['name']}{RESET}")
            print(f"        Split: {r['split']:<12}  Class: {r['class_focus']:<10}  "
                  f"Exercises: {ex_count}  Total EXP: ~{total_exp}{bonus_note}")

            # List exercises
            for i, ex in enumerate(r['exercises'], 1):
                ex_name = get_exercise_name(conn, ex['id'])
                meas = 'sec' if ex['measurement'] == 'seconds' else 'reps'
                print(f"        {i:>2}. {ex_name:<42} {ex['sets']}×{ex['reps']}{meas}  rest:{ex['rest']}s")
            print()

            to_insert.append(r)

    print(f"  {'─'*64}")
    print(f"  To insert: {len(to_insert)}  |  Skipped (exist): {skip_count}\n")
    return to_insert


def insert_routines(conn, routines):
    inserted = 0
    for r in routines:
        cursor = conn.execute(
            """INSERT INTO routines (routine_name, description, created_by, is_active)
               VALUES (?, ?, ?, 1)""",
            (r['name'], r['description'], 'System')
        )
        routine_id = cursor.lastrowid

        for pos, ex in enumerate(r['exercises'], 1):
            conn.execute(
                """INSERT INTO routine_exercises
                   (routine_id, exercise_id, sets, reps, rest_seconds, order_position, measurement)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    routine_id,
                    ex['id'],
                    ex['sets'],
                    ex['reps'],
                    ex['rest'],
                    pos,
                    ex['measurement'],
                )
            )

        inserted += 1
    return inserted


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='LevelUp Gym — Routine Builder')
    parser.add_argument('--commit', action='store_true',
                        help='Write routines to database (default: dry-run)')
    parser.add_argument('--tier', type=str, default=None,
                        choices=['beginner', 'intermediate', 'advanced'],
                        help='Only insert routines of this difficulty tier')
    parser.add_argument('--class', dest='class_focus', type=str, default=None,
                        choices=['warrior', 'ranger', 'tank', 'assassin', 'mage', 'all'],
                        help='Only insert routines for this class')
    parser.add_argument('--db', type=str, default=DB_PATH,
                        help='Path to the SQLite database file')
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"\n  ❌  Database not found: {args.db}")
        print(f"      Use --db /path/to/gym.db\n")
        sys.exit(1)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    existing = get_existing_routine_names(conn)
    routines = filter_routines(ROUTINES, args.tier, args.class_focus)

    to_insert = print_plan(conn, routines, existing, args.commit)

    if not args.commit:
        print(f"  ℹ️   Dry-run — no changes made.")
        print(f"      Add --commit to write to the database.\n")
        conn.close()
        return

    try:
        inserted = insert_routines(conn, to_insert)
        conn.commit()
        print(f"  ✅  {inserted} routine(s) inserted successfully.\n")
    except Exception as e:
        conn.rollback()
        print(f"  ❌  Error: {e}\n")
        import traceback; traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
