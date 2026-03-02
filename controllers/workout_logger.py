# controllers/workout_logger.py
import sys
import os
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from controllers.gamification_controller import GamificationController
from controllers.attendance_controller import AttendanceController
from models.exercise_model import Exercise
from models.routine import Routine

class WorkoutLogger:
    """Handles logging of workout performance and real-time EXP calculation"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.gamification = GamificationController()
        self.attendance = AttendanceController()
    
    def log_set(self, client_id, exercise_id, set_number, reps_completed, 
                weight_used=None, measurement=None, workout_date=None):
        """
        Log a single set completion
        Returns: dict with set info and EXP earned
        """
        if workout_date is None:
            workout_date = date.today()
        elif isinstance(workout_date, str):
            workout_date = datetime.strptime(workout_date, '%Y-%m-%d').date()
        
        # Get exercise info
        exercise = Exercise.get_by_id(exercise_id)
        if not exercise:
            return {'success': False, 'message': 'Exercise not found'}
        
        # Calculate EXP for this set
        exp_result = self.gamification.add_experience(
            client_id, 
            base_exp=exercise.base_exp,
            exercise_type=exercise.exercise_type
        )
        
        # Log the set
        self.db.connect()
        query = '''
            INSERT INTO workout_logs 
            (client_id, exercise_id, workout_date, set_number, reps_completed, 
             weight_used, exp_earned, measurement)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        self.db.cursor.execute(query, (
            client_id, exercise_id, workout_date.strftime('%Y-%m-%d'), 
            set_number, reps_completed, weight_used, exp_result['exp_gained'], measurement
        ))
        self.db.conn.commit()
        log_id = self.db.cursor.lastrowid
        self.db.disconnect()

        # 🔹 Update session progress and EXP totals
        try:
            from controllers.workout_session_controller import WorkoutSessionController
            from models.routine import Routine

            session_ctrl = WorkoutSessionController()

            # Find today's session (if any)
            today_str = workout_date.strftime('%Y-%m-%d')
            exercise_routine_id = getattr(exercise, "routine_id", None)
            if exercise_routine_id:
                session = session_ctrl._get_session(client_id, exercise_routine_id, today_str)
                if session:
                    session_ctrl.mark_set_completed(session['session_id'], exercise.exercise_id, set_number, reps_completed, weight_used)
                    session_ctrl.update_session_exp(session['session_id'], exp_result['exp_gained'])

                    # Check if the workout is now completed
                    routine = Routine.get_by_id(exercise_routine_id)
                    progress = session_ctrl.get_session_progress(session['session_id'], routine)
                    if progress['completion_percentage'] >= 100:
                        session_ctrl.complete_session(session['session_id'])
        except Exception as e:
            print(f"[WorkoutLogger] Session sync failed: {e}")
            
        # Update attendance EXP if checked in today
        if workout_date == date.today():
            todays_attendance = self.attendance.get_todays_attendance(client_id)
            if todays_attendance:
                self.attendance.update_attendance_exp(
                    todays_attendance['attendance_id'], 
                    exp_result['exp_gained']
                )
        
        return {
            'success': True,
            'log_id': log_id,
            'exercise_name': exercise.name,
            'set_number': set_number,
            'reps_completed': reps_completed,
            'weight_used': weight_used,
            'exp_earned': exp_result['exp_gained'],
            'level_info': {
                'new_level': exp_result['new_level'],
                'leveled_up': exp_result['leveled_up'],
                'current_exp': exp_result['current_exp'],
                'next_level_exp': exp_result['next_level_exp']
            },
            'multipliers': {
                'base_exp': exp_result['base_exp'],
                'streak': exp_result['streak_multiplier'],
                'class': exp_result['class_multiplier'],
                'total': exp_result['total_multiplier']
            }
        }
    
    def log_complete_exercise(self, client_id, exercise_id, sets_data, workout_date=None):
        """
        Log multiple sets for an exercise at once
        Args:
            sets_data: list of dicts like [{'reps': 10, 'weight': 50}, {'reps': 8, 'weight': 55}]
        Returns: dict with complete exercise summary
        """
        if workout_date is None:
            workout_date = date.today()
        
        results = []
        total_exp = 0
        leveled_up = False
        new_level = None
        
        for i, set_data in enumerate(sets_data, start=1):
            result = self.log_set(
                client_id=client_id,
                exercise_id=exercise_id,
                set_number=i,
                reps_completed=set_data.get('reps', 0),
                weight_used=set_data.get('weight'),
                notes=set_data.get('notes'),
                workout_date=workout_date
            )
            
            if result['success']:
                results.append(result)
                total_exp += result['exp_earned']
                if result['level_info']['leveled_up']:
                    leveled_up = True
                    new_level = result['level_info']['new_level']
        
        exercise = Exercise.get_by_id(exercise_id)
        
        return {
            'success': True,
            'exercise_name': exercise.name if exercise else 'Unknown',
            'total_sets': len(results),
            'total_reps': sum(r['reps_completed'] for r in results),
            'total_exp': total_exp,
            'leveled_up': leveled_up,
            'new_level': new_level,
            'set_details': results
        }
    
    def get_workout_history(self, client_id, limit=10):
        """Get recent workout sessions"""
        query = '''
            SELECT workout_date, COUNT(DISTINCT exercise_id) as exercises_count,
                   COUNT(*) as total_sets, SUM(exp_earned) as total_exp
            FROM workout_logs
            WHERE client_id=?
            GROUP BY workout_date
            ORDER BY workout_date DESC
            LIMIT ?
        '''
        results = self.db.execute_query(query, (client_id, limit))
        
        history = []
        for row in results:
            history.append({
                'date': row['workout_date'],
                'exercises_count': row['exercises_count'],
                'total_sets': row['total_sets'],
                'total_exp': row['total_exp']
            })
        
        return history
    
    def get_workout_details(self, client_id, workout_date):
        """Get detailed breakdown of a specific workout"""
        if isinstance(workout_date, str):
            workout_date = datetime.strptime(workout_date, '%Y-%m-%d').date()
        
        query = '''
            SELECT wl.*, e.name as exercise_name, e.primary_muscle, e.exercise_type
            FROM workout_logs wl
            JOIN exercises e ON wl.exercise_id = e.exercise_id
            WHERE wl.client_id=? AND wl.workout_date=?
            ORDER BY wl.timestamp
        '''
        results = self.db.execute_query(query, (client_id, workout_date.strftime('%Y-%m-%d')))
        
        # Group by exercise
        exercises = {}
        for row in results:
            exercise_id = row['exercise_id']
            if exercise_id not in exercises:
                exercises[exercise_id] = {
                    'exercise_name': row['exercise_name'],
                    'primary_muscle': row['primary_muscle'],
                    'exercise_type': row['exercise_type'],
                    'sets': []
                }
            
            exercises[exercise_id]['sets'].append({
                'set_number': row['set_number'],
                'reps': row['reps_completed'],
                'weight': row['weight_used'],
                'exp_earned': row['exp_earned'],
                'notes': row['notes']
            })
        
        return {
            'workout_date': workout_date.strftime('%Y-%m-%d'),
            'exercises': list(exercises.values()),
            'total_exercises': len(exercises),
            'total_sets': sum(len(ex['sets']) for ex in exercises.values()),
            'total_exp': sum(
                sum(s['exp_earned'] for s in ex['sets']) 
                for ex in exercises.values()
            )
        }
    
    def get_exercise_progress(self, client_id, exercise_id, limit=10):
        """Track progress for a specific exercise over time"""
        query = '''
            SELECT workout_date, set_number, reps_completed, weight_used, exp_earned
            FROM workout_logs
            WHERE client_id=? AND exercise_id=?
            ORDER BY workout_date DESC, set_number
            LIMIT ?
        '''
        results = self.db.execute_query(query, (client_id, exercise_id, limit))
        
        # Group by date to get best performance per session
        sessions = {}
        for row in results:
            date_key = row['workout_date']
            if date_key not in sessions:
                sessions[date_key] = {
                    'date': date_key,
                    'sets': [],
                    'max_weight': 0,
                    'total_reps': 0,
                    'total_exp': 0
                }
            
            sessions[date_key]['sets'].append({
                'set': row['set_number'],
                'reps': row['reps_completed'],
                'weight': row['weight_used'] or 0
            })
            sessions[date_key]['max_weight'] = max(
                sessions[date_key]['max_weight'], 
                row['weight_used'] or 0
            )
            sessions[date_key]['total_reps'] += row['reps_completed']
            sessions[date_key]['total_exp'] += row['exp_earned']
        
        exercise = Exercise.get_by_id(exercise_id)
        
        return {
            'exercise_name': exercise.name if exercise else 'Unknown',
            'sessions': list(sessions.values()),
            'total_sessions': len(sessions)
        }
    
    def get_personal_records(self, client_id):
        """Get personal records (highest weight/reps) for each exercise"""
        query = '''
            SELECT e.name as exercise_name, e.primary_muscle,
                   MAX(wl.weight_used) as max_weight,
                   MAX(wl.reps_completed) as max_reps,
                   MAX(wl.workout_date) as last_performed
            FROM workout_logs wl
            JOIN exercises e ON wl.exercise_id = e.exercise_id
            WHERE wl.client_id=?
            GROUP BY wl.exercise_id
            ORDER BY e.name
        '''
        results = self.db.execute_query(query, (client_id,))
        
        records = []
        for row in results:
            records.append({
                'exercise': row['exercise_name'],
                'primary_muscle': row['primary_muscle'],
                'max_weight': row['max_weight'],
                'max_reps': row['max_reps'],
                'last_performed': row['last_performed']
            })
        
        return records
    
    def get_recommended_weight(self, client_id, exercise_id):
        """
        Suggest weight for next set based on recent performance
        Returns recommended weight or None if no history
        """
        query = '''
            SELECT weight_used, reps_completed
            FROM workout_logs
            WHERE client_id=? AND exercise_id=? AND weight_used IS NOT NULL
            ORDER BY workout_date DESC, timestamp DESC
            LIMIT 5
        '''
        results = self.db.execute_query(query, (client_id, exercise_id))
        
        if not results:
            return None
        
        # Get average of last successful sets
        recent_weights = [row['weight_used'] for row in results]
        recent_reps = [row['reps_completed'] for row in results]
        
        avg_weight = sum(recent_weights) / len(recent_weights)
        avg_reps = sum(recent_reps) / len(recent_reps)
        
        # If consistently hitting high reps, suggest increase
        if avg_reps >= 12:
            recommended = avg_weight * 1.05  # 5% increase
            suggestion = "increase"
        # If struggling with low reps, suggest decrease
        elif avg_reps <= 6:
            recommended = avg_weight * 0.95  # 5% decrease
            suggestion = "decrease"
        else:
            recommended = avg_weight
            suggestion = "maintain"
        
        return {
            'recommended_weight': round(recommended, 1),
            'recent_average': round(avg_weight, 1),
            'average_reps': round(avg_reps, 1),
            'suggestion': suggestion,
            'message': self._get_weight_suggestion_message(suggestion, recommended)
        }
    
    def _get_weight_suggestion_message(self, suggestion, weight):
        """Generate encouraging message for weight suggestion"""
        messages = {
            'increase': f"💪 Strong! Increase weight for the next set.",
            'decrease': f"⚖️ Heavy! Decrease weight for the next set.",
            'maintain': f"✅ Perfect! Keep that weight."
        }
        return messages.get(suggestion)
    
    def get_workout_stats(self, client_id):
        """Get overall workout statistics"""
        query = '''
            SELECT 
                COUNT(DISTINCT workout_date) as total_workouts,
                COUNT(DISTINCT exercise_id) as unique_exercises,
                COUNT(*) as total_sets,
                SUM(reps_completed) as total_reps,
                SUM(exp_earned) as total_exp,
                AVG(weight_used) as avg_weight
            FROM workout_logs
            WHERE client_id=? AND measurement='reps'
        '''
        result = self.db.execute_query(query, (client_id,))
        
        if result and result[0]['total_workouts'] > 0:
            stats = dict(result[0])
            
            # Get favorite exercise (most logged)
            fav_query = '''
                SELECT e.name, COUNT(*) as count
                FROM workout_logs wl
                JOIN exercises e ON wl.exercise_id = e.exercise_id
                WHERE wl.client_id=?
                GROUP BY wl.exercise_id
                ORDER BY count DESC
                LIMIT 1
            '''
            fav_result = self.db.execute_query(fav_query, (client_id,))
            if fav_result:
                stats['favorite_exercise'] = fav_result[0]['name']
            
            return stats
        
        return None
    
    def get_todays_workout(self, client_id):
        """Get current progress on today's workout"""
        today = date.today()
        return self.get_workout_details(client_id, today)
    
    def delete_set(self, log_id):
        """Delete a logged set (in case of mistake)"""
        # Get the set info first to reverse EXP
        query = 'SELECT * FROM workout_logs WHERE log_id=?'
        result = self.db.execute_query(query, (log_id,))
        
        if not result:
            return {'success': False, 'message': 'Set not found'}
        
        set_data = dict(result[0])
        
        # Delete the set
        self.db.connect()
        self.db.cursor.execute('DELETE FROM workout_logs WHERE log_id=?', (log_id,))
        self.db.conn.commit()
        self.db.disconnect()
        
        return {
            'success': True,
            'message': 'Set deleted successfully',
            'exp_lost': set_data['exp_earned']
        }


# Example usage and testing
if __name__ == "__main__":
    from database.db_manager import DatabaseManager
    from models.client import Client
    from models.exercise_model import Exercise, populate_default_exercises
    
    # Initialize database
    db = DatabaseManager()
    db.initialize_database()
    
    # Populate exercises if needed
    if len(Exercise.get_all()) == 0:
        populate_default_exercises()
    
    # Create test client
    client = Client(
        phone_number="5553334444",
        first_name="Workout",
        last_name="Logger",
        email="workout@gym.com",
        date_of_birth="1991-08-10"
    )
    client_id = client.save(pin="7777")
    print(f"✅ Created test client: {client.full_name}\n")
    
    # Check in first
    attendance_ctrl = AttendanceController()
    check_in = attendance_ctrl.check_in(client_id)
    print(f"✅ Checked in: {check_in['message']}\n")
    
    # Initialize workout logger
    logger = WorkoutLogger()
    
    print("=== Testing Workout Logger ===\n")
    
    # Get exercises
    bench_press = Exercise.get_by_name("Bench Press")
    squats = Exercise.get_by_name("Squats")
    
    # Log bench press sets
    print("--- Logging Bench Press Sets ---")
    bench_sets = [
        {'reps': 10, 'weight': 60.0},
        {'reps': 10, 'weight': 60.0},
        {'reps': 8, 'weight': 65.0},
        {'reps': 6, 'weight': 70.0}
    ]
    
    result = logger.log_complete_exercise(client_id, bench_press.exercise_id, bench_sets)
    if result['success']:
        print(f"✅ Completed {result['exercise_name']}")
        print(f"   Total Sets: {result['total_sets']}")
        print(f"   Total Reps: {result['total_reps']}")
        print(f"   Total EXP: {result['total_exp']}")
        if result['leveled_up']:
            print(f"   🎉 LEVEL UP! Now level {result['new_level']}!")
    print()
    
    # Log squats
    print("--- Logging Squats ---")
    squat_sets = [
        {'reps': 12, 'weight': 80.0},
        {'reps': 10, 'weight': 85.0},
        {'reps': 8, 'weight': 90.0}
    ]
    
    result = logger.log_complete_exercise(client_id, squats.exercise_id, squat_sets)
    if result['success']:
        print(f"✅ Completed {result['exercise_name']}")
        print(f"   Total Sets: {result['total_sets']}")
        print(f"   Total Reps: {result['total_reps']}")
        print(f"   Total EXP: {result['total_exp']}")
    print()
    
    # Get today's workout summary
    print("--- Today's Workout Summary ---")
    todays_workout = logger.get_todays_workout(client_id)
    print(f"Date: {todays_workout['workout_date']}")
    print(f"Exercises Completed: {todays_workout['total_exercises']}")
    print(f"Total Sets: {todays_workout['total_sets']}")
    print(f"Total EXP: {todays_workout['total_exp']}")
    print("\nExercise Breakdown:")
    for exercise in todays_workout['exercises']:
        print(f"  • {exercise['exercise_name']} ({exercise['primary_muscle']})")
        print(f"    {len(exercise['sets'])} sets")
        for set_data in exercise['sets']:
            weight_str = f"{set_data['weight']}kg" if set_data['weight'] else "bodyweight"
            print(f"      Set {set_data['set_number']}: {set_data['reps']} reps @ {weight_str} (+{set_data['exp_earned']} EXP)")
    print()
    
    # Get weight recommendation
    print("--- Weight Recommendations ---")
    bench_rec = logger.get_recommended_weight(client_id, bench_press.exercise_id)
    if bench_rec:
        print(f"Bench Press: {bench_rec['message']}")
        print(f"  Current avg: {bench_rec['recent_average']}kg @ {bench_rec['average_reps']} reps")
    print()
    
    # Simulate more workouts for history
    print("--- Simulating Additional Workouts ---")
    from datetime import timedelta
    
    for i in range(1, 4):
        past_date = date.today() - timedelta(days=i)
        
        # Log some sets for past days
        logger.log_complete_exercise(
            client_id, 
            bench_press.exercise_id, 
            [{'reps': 10, 'weight': 55.0}, {'reps': 8, 'weight': 60.0}],
            workout_date=past_date
        )
        print(f"✅ Added workout for {past_date.strftime('%Y-%m-%d')}")
    print()
    
    # Get workout history
    print("--- Workout History ---")
    history = logger.get_workout_history(client_id, limit=5)
    for workout in history:
        print(f"  {workout['date']}: {workout['exercises_count']} exercises, "
              f"{workout['total_sets']} sets, {workout['total_exp']} EXP")
    print()
    
    # Get exercise progress
    print("--- Bench Press Progress ---")
    progress = logger.get_exercise_progress(client_id, bench_press.exercise_id)
    print(f"Exercise: {progress['exercise_name']}")
    print(f"Total Sessions: {progress['total_sessions']}")
    print("Recent sessions:")
    for session in progress['sessions'][:3]:
        print(f"  {session['date']}: {len(session['sets'])} sets, "
              f"Max weight: {session['max_weight']}kg, "
              f"Total reps: {session['total_reps']}")
    print()
    
    # Get personal records
    print("--- Personal Records ---")
    records = logger.get_personal_records(client_id)
    for record in records:
        print(f"  {record['exercise']} ({record['primary_muscle']})")
        if record['max_weight']:
            print(f"    Max Weight: {record['max_weight']}kg")
        print(f"    Max Reps: {record['max_reps']}")
        print(f"    Last Done: {record['last_performed']}")
    print()
    
    # Get overall stats
    print("--- Overall Workout Statistics ---")
    stats = logger.get_workout_stats(client_id)
    if stats:
        print(f"  Total Workouts: {stats['total_workouts']}")
        print(f"  Unique Exercises: {stats['unique_exercises']}")
        print(f"  Total Sets: {stats['total_sets']}")
        print(f"  Total Reps: {stats['total_reps']}")
        print(f"  Total EXP: {stats['total_exp']}")
        if stats.get('avg_weight'):
            print(f"  Average Weight: {stats['avg_weight']:.1f}kg")
        if stats.get('favorite_exercise'):
            print(f"  Favorite Exercise: {stats['favorite_exercise']}")
    print()
    
    # Check out
    print("--- Checking Out ---")
    checkout = attendance_ctrl.check_out(client_id)
    if checkout['success']:
        print(f"✅ {checkout['message']}")
        print(f"   Session Duration: {checkout['duration_minutes']} minutes")
        print(f"   Total Session EXP: {checkout['exp_earned']}")
