# controllers/achievement_controller.py
import sys
import os
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from controllers.gamification_controller import GamificationController

class AchievementController:
    """Manages achievements and milestone rewards"""
    
    # Extended Pre-defined Achievements
    DEFAULT_ACHIEVEMENTS = [
        # -------------------------------
        # Level Achievements
        # -------------------------------
        {'name': 'First Steps', 'description': 'Reach level 5', 'type': 'level', 'requirement': 5, 'exp_reward': 100},
        {'name': 'Rising Star', 'description': 'Reach level 10', 'type': 'level', 'requirement': 10, 'exp_reward': 250},
        {'name': 'Veteran', 'description': 'Reach level 15', 'type': 'level', 'requirement': 15, 'exp_reward': 500},
        {'name': 'Master', 'description': 'Reach level 20', 'type': 'level', 'requirement': 20, 'exp_reward': 1000},
        {'name': 'Ascendant', 'description': 'Reach level 30', 'type': 'level', 'requirement': 30, 'exp_reward': 1500},
        {'name': 'Peak Performer', 'description': 'Reach level 50', 'type': 'level', 'requirement': 50, 'exp_reward': 3000},
        {'name': 'Limit Breaker', 'description': 'Reach level 75', 'type': 'level', 'requirement': 75, 'exp_reward': 5000},
        {'name': 'True Legend', 'description': 'Reach level 100', 'type': 'level', 'requirement': 100, 'exp_reward': 10000},

        # -------------------------------
        # Attendance Achievements
        # -------------------------------
        {'name': 'Consistency is Key', 'description': 'Check in 10 times', 'type': 'attendance', 'requirement': 10, 'exp_reward': 150},
        {'name': 'Gym Regular', 'description': 'Check in 30 times', 'type': 'attendance', 'requirement': 30, 'exp_reward': 300},
        {'name': 'Iron Dedication', 'description': 'Check in 100 times', 'type': 'attendance', 'requirement': 100, 'exp_reward': 1000},
        {'name': 'Never Miss a Day', 'description': 'Check in 250 times', 'type': 'attendance', 'requirement': 250, 'exp_reward': 2000},
        {'name': 'Lifetime Member', 'description': 'Check in 500 times', 'type': 'attendance', 'requirement': 500, 'exp_reward': 5000},

        # -------------------------------
        # Streak Achievements
        # -------------------------------
        {'name': 'On Fire!', 'description': 'Maintain a 7-day streak', 'type': 'streak', 'requirement': 7, 'exp_reward': 200},
        {'name': 'Unstoppable', 'description': 'Maintain a 30-day streak', 'type': 'streak', 'requirement': 30, 'exp_reward': 500},
        {'name': 'Legend', 'description': 'Maintain a 100-day streak', 'type': 'streak', 'requirement': 100, 'exp_reward': 2000},
        {'name': '365 Grind', 'description': 'Train every day for a full year', 'type': 'streak', 'requirement': 365, 'exp_reward': 7500},

        # -------------------------------
        # Workout Achievements
        # -------------------------------
        {'name': 'First Workout', 'description': 'Complete your first workout', 'type': 'workouts', 'requirement': 1, 'exp_reward': 50},
        {'name': 'Getting Strong', 'description': 'Complete 50 workouts', 'type': 'workouts', 'requirement': 50, 'exp_reward': 400},
        {'name': 'Fitness Warrior', 'description': 'Complete 100 workouts', 'type': 'workouts', 'requirement': 100, 'exp_reward': 800},
        {'name': 'Gym Veteran', 'description': 'Complete 250 workouts', 'type': 'workouts', 'requirement': 250, 'exp_reward': 1500},
        {'name': 'Titan of Training', 'description': 'Complete 500 workouts', 'type': 'workouts', 'requirement': 500, 'exp_reward': 3000},

        # -------------------------------
        # Rank Achievements
        # -------------------------------
        {'name': 'D-Rank Fighter', 'description': 'Achieve D rank', 'type': 'rank', 'requirement': 'D', 'exp_reward': 100},
        {'name': 'C-Rank Athlete', 'description': 'Achieve C rank', 'type': 'rank', 'requirement': 'C', 'exp_reward': 200},
        {'name': 'B-Rank Champion', 'description': 'Achieve B rank', 'type': 'rank', 'requirement': 'B', 'exp_reward': 300},
        {'name': 'A-Rank Elite', 'description': 'Achieve A rank', 'type': 'rank', 'requirement': 'A', 'exp_reward': 500},
        {'name': 'S-Rank Legend', 'description': 'Achieve S rank', 'type': 'rank', 'requirement': 'S', 'exp_reward': 750},
        {'name': 'SS-Rank Master', 'description': 'Achieve SS rank', 'type': 'rank', 'requirement': 'SS', 'exp_reward': 1500},
        {'name': 'Ω-Rank Godlike', 'description': 'Achieve Omega Rank – the ultimate form', 'type': 'rank', 'requirement': 'Ω', 'exp_reward': 5000},

        # -------------------------------
        # Exercise Volume Achievements
        # -------------------------------
        {'name': 'Hundred Club', 'description': 'Complete 100 total sets', 'type': 'sets', 'requirement': 100, 'exp_reward': 200},
        {'name': 'Volume Master', 'description': 'Complete 500 total sets', 'type': 'sets', 'requirement': 500, 'exp_reward': 600},
        {'name': 'Set Machine', 'description': 'Complete 1000 total sets', 'type': 'sets', 'requirement': 1000, 'exp_reward': 1200},
        {'name': 'Reps for Days', 'description': 'Complete 1000 total reps', 'type': 'reps', 'requirement': 1000, 'exp_reward': 300},
        {'name': 'Rep Monster', 'description': 'Complete 5000 total reps', 'type': 'reps', 'requirement': 5000, 'exp_reward': 1200},
        {'name': 'Endurance Machine', 'description': 'Complete 10,000 total reps', 'type': 'reps', 'requirement': 10000, 'exp_reward': 3000},

        # -------------------------------
        # Class Achievements
        # -------------------------------
        {'name': 'Class Chosen', 'description': 'Choose a specialized class', 'type': 'class', 'requirement': 1, 'exp_reward': 150},
        {'name': 'Dedicated Specialist', 'description': 'Complete 25 workouts in your class', 'type': 'class_progress', 'requirement': 25, 'exp_reward': 400},
        {'name': 'Class Master', 'description': 'Reach max level in your class specialization', 'type': 'class_mastery', 'requirement': 1, 'exp_reward': 1500},

        # -------------------------------
        # Bonus & Milestone Achievements
        # -------------------------------
        {'name': 'Daily Grinder', 'description': 'Complete workouts 7 days in a row', 'type': 'milestone', 'requirement': 7, 'exp_reward': 250},
        {'name': 'Morning Champion', 'description': 'Train before 7 AM for 30 days', 'type': 'milestone', 'requirement': 30, 'exp_reward': 600},
        {'name': 'Night Owl', 'description': 'Train after 9 PM for 30 days', 'type': 'milestone', 'requirement': 30, 'exp_reward': 600},
        {'name': 'Comeback Story', 'description': 'Return after a week break and complete a workout', 'type': 'milestone', 'requirement': 1, 'exp_reward': 400},
        {'name': 'Ultimate Grind', 'description': 'Train 365 days without missing a single day', 'type': 'milestone', 'requirement': 365, 'exp_reward': 10000}
    ] 
    def __init__(self):
        self.db = DatabaseManager()
        self.gamification = GamificationController()
    
    def initialize_achievements(self):
        """Populate database with default achievements"""
        for ach in self.DEFAULT_ACHIEVEMENTS:
            try:
                self.db.connect()
                query = '''
                    INSERT OR IGNORE INTO achievements 
                    (achievement_name, description, achievement_type, requirement_value, exp_reward)
                    VALUES (?, ?, ?, ?, ?)
                '''
                # For rank achievements, store rank as text in notes, use order number as requirement
                req_value = ach['requirement']
                if ach['type'] == 'rank':
                    rank_order = {'E': 0, 'D': 1, 'C': 2, 'B': 3, 'A': 4, 'S': 5, 'SS': 6}
                    req_value = rank_order.get(req_value, 0)
                
                self.db.cursor.execute(query, (
                    ach['name'], ach['description'], ach['type'], 
                    req_value, ach['exp_reward']
                ))
                self.db.conn.commit()
                self.db.disconnect()
            except Exception as e:
                print(f"Error adding achievement {ach['name']}: {e}")
        
        print("✅ Achievements initialized!")
    
    def check_and_unlock_achievements(self, client_id):
        """
        Check all achievements for a client and unlock any newly earned
        Returns: list of newly unlocked achievements
        """
        newly_unlocked = []
        
        # Get client's current stats
        stats = self._get_client_stats(client_id)
        
        # Get all achievements
        all_achievements = self._get_all_achievements()
        
        # Get already unlocked achievements
        unlocked_ids = self._get_unlocked_achievement_ids(client_id)
        
        # Check each achievement
        for achievement in all_achievements:
            # Skip if already unlocked
            if achievement['achievement_id'] in unlocked_ids:
                continue
            
            # Check if requirements are met
            if self._check_achievement_requirement(achievement, stats):
                # Unlock achievement
                result = self.unlock_achievement(client_id, achievement['achievement_id'])
                if result['success']:
                    newly_unlocked.append(result)
        
        return newly_unlocked
    
    def unlock_achievement(self, client_id, achievement_id):
        """Manually unlock an achievement for a client"""
        # Check if already unlocked
        if self._is_achievement_unlocked(client_id, achievement_id):
            return {'success': False, 'message': 'Achievement already unlocked'}
        
        # Get achievement info
        achievement = self._get_achievement_by_id(achievement_id)
        if not achievement:
            return {'success': False, 'message': 'Achievement not found'}
        
        # Unlock achievement
        self.db.connect()
        query = '''
            INSERT INTO client_achievements (client_id, achievement_id)
            VALUES (?, ?)
        '''
        self.db.cursor.execute(query, (client_id, achievement_id))
        self.db.conn.commit()
        self.db.disconnect()
        
        # Award EXP
        exp_result = self.gamification.add_experience(client_id, achievement['exp_reward'])
        
        return {
            'success': True,
            'achievement_name': achievement['achievement_name'],
            'description': achievement['description'],
            'exp_reward': achievement['exp_reward'],
            'exp_earned': exp_result['exp_gained'],
            'leveled_up': exp_result['leveled_up'],
            'new_level': exp_result['new_level']
        }
    
    def get_client_achievements(self, client_id):
        """Get all achievements for a client (unlocked and locked)"""
        query = '''
            SELECT a.*, ca.unlocked_date,
                   CASE WHEN ca.client_achievement_id IS NOT NULL THEN 1 ELSE 0 END as is_unlocked
            FROM achievements a
            LEFT JOIN client_achievements ca ON a.achievement_id = ca.achievement_id 
                AND ca.client_id = ?
            ORDER BY a.achievement_type, a.requirement_value
        '''
        results = self.db.execute_query(query, (client_id,))
        
        achievements = {
            'level': [],
            'attendance': [],
            'streak': [],
            'workouts': [],
            'rank': [],
            'sets': [],
            'reps': [],
            'class': []
        }
        
        total_unlocked = 0
        total_exp_earned = 0
        
        for row in results:
            ach_data = {
                'achievement_id': row['achievement_id'],
                'name': row['achievement_name'],
                'description': row['description'],
                'type': row['achievement_type'],
                'requirement': row['requirement_value'],
                'exp_reward': row['exp_reward'],
                'is_unlocked': bool(row['is_unlocked']),
                'unlocked_date': row['unlocked_date']
            }
            
            if ach_data['is_unlocked']:
                total_unlocked += 1
                total_exp_earned += ach_data['exp_reward']
            
            ach_type = row['achievement_type']
            if ach_type in achievements:
                achievements[ach_type].append(ach_data)
        
        return {
            'achievements': achievements,
            'total_unlocked': total_unlocked,
            'total_achievements': sum(len(achs) for achs in achievements.values()),
            'total_exp_earned': total_exp_earned,
            'completion_percentage': (total_unlocked / sum(len(achs) for achs in achievements.values()) * 100) 
                if sum(len(achs) for achs in achievements.values()) > 0 else 0
        }
    
    def get_unlocked_achievements(self, client_id):
        """Get only unlocked achievements"""
        query = '''
            SELECT a.*, ca.unlocked_date
            FROM client_achievements ca
            JOIN achievements a ON ca.achievement_id = a.achievement_id
            WHERE ca.client_id = ?
            ORDER BY ca.unlocked_date DESC
        '''
        results = self.db.execute_query(query, (client_id,))
        
        unlocked = []
        for row in results:
            unlocked.append({
                'achievement_id': row['achievement_id'],
                'name': row['achievement_name'],
                'description': row['description'],
                'type': row['achievement_type'],
                'exp_reward': row['exp_reward'],
                'unlocked_date': row['unlocked_date']
            })
        
        return unlocked
    
    def get_progress_towards_achievement(self, client_id, achievement_id):
        """Get progress towards a specific achievement"""
        achievement = self._get_achievement_by_id(achievement_id)
        if not achievement:
            return None
        
        # Check if already unlocked
        if self._is_achievement_unlocked(client_id, achievement_id):
            return {
                'achievement_name': achievement['achievement_name'],
                'is_unlocked': True,
                'message': 'Achievement already unlocked! 🏆'
            }
        
        stats = self._get_client_stats(client_id)
        ach_type = achievement['achievement_type']
        requirement = achievement['requirement_value']
        
        # Get current progress based on type
        if ach_type == 'level':
            current = stats['level']
        elif ach_type == 'attendance':
            current = stats['total_visits']
        elif ach_type == 'streak':
            current = stats['current_streak']
        elif ach_type == 'workouts':
            current = stats['total_workouts']
        elif ach_type == 'rank':
            rank_order = {'E': 0, 'D': 1, 'C': 2, 'B': 3, 'A': 4, 'S': 5, 'SS': 6}
            current = rank_order.get(stats['rank'], 0)
        elif ach_type == 'sets':
            current = stats['total_sets']
        elif ach_type == 'reps':
            current = stats['total_reps']
        elif ach_type == 'class':
            current = 1 if stats['client_class'] else 0
        else:
            current = 0
        
        progress_pct = (current / requirement * 100) if requirement > 0 else 0
        
        return {
            'achievement_name': achievement['achievement_name'],
            'description': achievement['description'],
            'is_unlocked': False,
            'current_progress': current,
            'requirement': requirement,
            'progress_percentage': min(progress_pct, 100),
            'remaining': max(0, requirement - current)
        }
    
    def get_recent_unlocks(self, client_id, limit=5):
        """Get most recently unlocked achievements"""
        unlocked = self.get_unlocked_achievements(client_id)
        return unlocked[:limit]
    
    def _check_achievement_requirement(self, achievement, stats):
        """Check if achievement requirements are met"""
        ach_type = achievement['achievement_type']
        requirement = achievement['requirement_value']
        
        if ach_type == 'level':
            return stats['level'] >= requirement
        elif ach_type == 'attendance':
            return stats['total_visits'] >= requirement
        elif ach_type == 'streak':
            return stats['current_streak'] >= requirement
        elif ach_type == 'workouts':
            return stats['total_workouts'] >= requirement
        elif ach_type == 'rank':
            rank_order = {'E': 0, 'D': 1, 'C': 2, 'B': 3, 'A': 4, 'S': 5, 'SS': 6}
            current_rank_value = rank_order.get(stats['rank'], 0)
            return current_rank_value >= requirement
        elif ach_type == 'sets':
            return stats['total_sets'] >= requirement
        elif ach_type == 'reps':
            return stats['total_reps'] >= requirement
        elif ach_type == 'class':
            return stats['client_class'] is not None
        
        return False
    
    def _get_client_stats(self, client_id):
        """Get all relevant stats for achievement checking"""
        # Gamification data
        gam_query = 'SELECT * FROM client_gamification WHERE client_id=?'
        gam_result = self.db.execute_query(gam_query, (client_id,))
        gam_data = dict(gam_result[0]) if gam_result else {}
        
        # Streak data
        streak_query = 'SELECT * FROM client_streaks WHERE client_id=?'
        streak_result = self.db.execute_query(streak_query, (client_id,))
        streak_data = dict(streak_result[0]) if streak_result else {}
        
        # Attendance count
        attendance_query = 'SELECT COUNT(*) as total FROM attendance WHERE client_id=?'
        attendance_result = self.db.execute_query(attendance_query, (client_id,))
        total_visits = attendance_result[0]['total'] if attendance_result else 0
        
        # Workout stats (handle None values for new users)
        workout_query = '''
            SELECT 
                COUNT(DISTINCT workout_date) as total_workouts,
                COUNT(*) as total_sets,
                SUM(reps_completed) as total_reps
            FROM workout_logs
            WHERE client_id=15 AND measurement='reps'
        '''
        workout_result = self.db.execute_query(workout_query, (client_id,))
        workout_data = dict(workout_result[0]) if workout_result else {}
        
        return {
            'level': gam_data.get('current_level', 1),
            'rank': gam_data.get('rank', 'E'),
            'client_class': gam_data.get('client_class'),
            'current_streak': streak_data.get('current_streak', 0),
            'longest_streak': streak_data.get('longest_streak', 0),
            'total_visits': total_visits,
            'total_workouts': workout_data.get('total_workouts', 0) or 0,
            'total_sets': workout_data.get('total_sets', 0) or 0,
            'total_reps': workout_data.get('total_reps', 0) or 0
        }
    
    def _get_all_achievements(self):
        """Get all achievements from database"""
        query = 'SELECT * FROM achievements'
        results = self.db.execute_query(query)
        return [dict(row) for row in results]
    
    def _get_achievement_by_id(self, achievement_id):
        """Get specific achievement"""
        query = 'SELECT * FROM achievements WHERE achievement_id=?'
        result = self.db.execute_query(query, (achievement_id,))
        return dict(result[0]) if result else None
    
    def _get_unlocked_achievement_ids(self, client_id):
        """Get IDs of unlocked achievements"""
        query = 'SELECT achievement_id FROM client_achievements WHERE client_id=?'
        results = self.db.execute_query(query, (client_id,))
        return [row['achievement_id'] for row in results]
    
    def _is_achievement_unlocked(self, client_id, achievement_id):
        """Check if specific achievement is unlocked"""
        query = 'SELECT 1 FROM client_achievements WHERE client_id=? AND achievement_id=?'
        result = self.db.execute_query(query, (client_id, achievement_id))
        return len(result) > 0


# Example usage and testing
if __name__ == "__main__":
    from database.db_manager import DatabaseManager
    from models.client import Client
    from controllers.attendance_controller import AttendanceController
    from controllers.workout_logger import WorkoutLogger
    from models.exercise_model import Exercise, populate_default_exercises
    from datetime import timedelta
    
    # Initialize database
    db = DatabaseManager()
    db.initialize_database()
    
    # Populate exercises if needed
    if len(Exercise.get_all()) == 0:
        populate_default_exercises()
    
    ach_ctrl = AchievementController()
    ach_ctrl.initialize_achievements()
    print()
    
    print("=== Inicialaized Achievement System ===\n")