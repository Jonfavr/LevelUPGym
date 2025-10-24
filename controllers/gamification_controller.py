# controllers/gamification_controller.py
import sys
import os
from datetime import datetime, date, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager

class GamificationController:
    """Handles all gamification mechanics - levels, EXP, ranks, classes, streaks"""
    
    # Experience required for each level (exponential growth)
    EXP_TABLE = {
        1: 0, 2: 100, 3: 250, 4: 450, 5: 700,
        6: 1000, 7: 1350, 8: 1750, 9: 2200, 10: 2700,
        11: 3250, 12: 3850, 13: 4500, 14: 5200, 15: 5950,
        16: 6750, 17: 7600, 18: 8500, 19: 9450, 20: 10450,
        21: 11500, 22: 12600, 23: 13750, 24: 14950, 25: 16200,
        26: 17500, 27: 18850, 28: 20250, 29: 21700, 30: 23200,
        31: 24750, 32: 26350, 33: 28000, 34: 29700, 35: 31450,
        36: 33250, 37: 35100, 38: 37000, 39: 38950, 40: 40950,
        41: 43000, 42: 45100, 43: 47250, 44: 49450, 45: 51700,
        46: 54000, 47: 56350, 48: 58750, 49: 61200, 50: 63700,
        51: 66250, 52: 68850, 53: 71500, 54: 74200, 55: 76950,
        56: 79750, 57: 82600, 58: 85500, 59: 88450, 60: 91450,
        61: 94500, 62: 97600, 63: 100750, 64: 103950, 65: 107200,
        66: 110500, 67: 113850, 68: 117250, 69: 120700, 70: 124200,
        71: 127750, 72: 131350, 73: 135000, 74: 138700, 75: 142450,
        76: 146250, 77: 150100, 78: 154000, 79: 157950, 80: 161950,
        81: 166000, 82: 170100, 83: 174250, 84: 178450, 85: 182700,
        86: 187000, 87: 191350, 88: 195750, 89: 200200, 90: 204700,
        91: 209250, 92: 213850, 93: 218500, 94: 223200, 95: 227950,
        96: 232750, 97: 237600, 98: 242500, 99: 247450, 100: 252450
    }
    
    # Rank thresholds (total score from physical tests)
    RANK_THRESHOLDS = {
        'E': 0,      # Beginner
        'D': 100,    # Basic
        'C': 250,    # Intermediate
        'B': 450,    # Advanced
        'A': 700,    # Expert
        'S': 1000,   # Elite
        'SS': 1400   # Master
    }
    
    # Available classes (unlocked at level 5)
    CLASSES = {
        'Warrior': {
            'description': 'Strength and power focused',
            'bonus': 'Extra EXP from strength exercises',
            'multiplier': 1.2
        },
        'Ranger': {
            'description': 'Endurance and cardio specialist',
            'bonus': 'Extra EXP from cardio exercises',
            'multiplier': 1.2
        },
        'Tank': {
            'description': 'High resistance and stamina',
            'bonus': 'Extra EXP from compound exercises',
            'multiplier': 1.2
        },
        'Assassin': {
            'description': 'Speed and agility master',
            'bonus': 'Extra EXP from HIIT and speed work',
            'multiplier': 1.2
        },
        'Mage': {
            'description': 'Balance and technique expert',
            'bonus': 'Extra EXP from skill-based exercises',
            'multiplier': 1.2
        }
    }
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def add_experience(self, client_id, base_exp, exercise_type=None):
        """
        Add experience to client with all multipliers applied
        Returns: dict with exp gained, new level, level up status
        """
        # Get current gamification data
        gam_data = self._get_gamification_data(client_id)
        if not gam_data:
            return None
        
        # Get streak multiplier
        streak_multiplier = self._get_streak_multiplier(client_id)
        
        # Get class multiplier if applicable
        class_multiplier = self._get_class_multiplier(gam_data['client_class'], exercise_type)
        
        # Calculate total EXP
        total_multiplier = streak_multiplier * class_multiplier
        exp_gained = int(base_exp * total_multiplier)
        
        # Update EXP
        new_current_exp = gam_data['current_exp'] + exp_gained
        new_total_exp = gam_data['total_exp'] + exp_gained
        current_level = gam_data['current_level']
        
        # Check for level up
        leveled_up = False
        new_level = current_level
        
        while new_level < 20 and new_current_exp >= self.EXP_TABLE.get(new_level + 1, float('inf')):
            new_level += 1
            leveled_up = True
        
        # If leveled up, adjust current EXP
        if leveled_up:
            new_current_exp = new_current_exp - self.EXP_TABLE[new_level]
        
        # Update database
        self.db.connect()
        query = '''
            UPDATE client_gamification 
            SET current_exp=?, total_exp=?, current_level=?
            WHERE client_id=?
        '''
        self.db.cursor.execute(query, (new_current_exp, new_total_exp, new_level, client_id))
        self.db.conn.commit()
        self.db.disconnect()
        
        return {
            'exp_gained': exp_gained,
            'base_exp': base_exp,
            'streak_multiplier': streak_multiplier,
            'class_multiplier': class_multiplier,
            'total_multiplier': total_multiplier,
            'new_level': new_level,
            'leveled_up': leveled_up,
            'current_exp': new_current_exp,
            'total_exp': new_total_exp,
            'next_level_exp': self.EXP_TABLE.get(new_level + 1, 0)
        }
    
    def update_rank(self, client_id, new_rank):
        """
        Update client's rank in the gamification table.
        Returns the new rank if successful.
        """
        try:
            # Optional: validate rank input
            valid_ranks = ["S", "A", "B", "C", "D", "E", "F"]
            if new_rank not in valid_ranks:
                print(f"⚠️ Invalid rank '{new_rank}' provided for client {client_id}. Skipping update.")
                return None

            query = '''
                UPDATE client_gamification
                SET rank = ?
                WHERE client_id = ?
            '''
            self.db.execute_update(query, (new_rank, client_id))
            print(f"🏅 Updated client {client_id} rank → {new_rank}")
            return new_rank

        except Exception as e:
            print(f"❌ Error updating rank for client {client_id}: {e}")
            return None
    
    def unlock_class(self, client_id, class_name):
        """
        Unlock a specialized class for client (requires level 5)
        """
        if class_name not in self.CLASSES:
            return {'success': False, 'message': 'Invalid class name'}
        
        gam_data = self._get_gamification_data(client_id)
        
        if gam_data['current_level'] < 5:
            return {'success': False, 'message': 'Must be level 5 to choose a class'}
        
        if gam_data['client_class']:
            return {'success': False, 'message': 'Class already selected'}
        
        # Update database
        self.db.connect()
        query = '''
            UPDATE client_gamification 
            SET client_class=?, class_unlocked_at_level=?
            WHERE client_id=?
        '''
        self.db.cursor.execute(query, (class_name, gam_data['current_level'], client_id))
        self.db.conn.commit()
        self.db.disconnect()
        
        return {
            'success': True, 
            'message': f'Class {class_name} unlocked!',
            'class_info': self.CLASSES[class_name]
        }
    
    def update_streak(self, client_id, check_in_date=None):
        """
        Update attendance streak for client
        Returns: dict with streak info and multiplier
        """
        if check_in_date is None:
            check_in_date = date.today()
        elif isinstance(check_in_date, str):
            check_in_date = datetime.strptime(check_in_date, '%Y-%m-%d').date()
        
        self.db.connect()
        
        # Get current streak data
        query = 'SELECT * FROM client_streaks WHERE client_id=?'
        self.db.cursor.execute(query, (client_id,))
        streak_data = self.db.cursor.fetchone()
        
        if not streak_data:
            self.db.disconnect()
            return None
        
        current_streak = streak_data['current_streak']
        longest_streak = streak_data['longest_streak']
        last_date = streak_data['last_attendance_date']
        
        if last_date:
            last_date = datetime.strptime(last_date, '%Y-%m-%d').date()
            days_diff = (check_in_date - last_date).days
            
            if days_diff == 1:
                # Consecutive day - increase streak
                current_streak += 1
            elif days_diff == 0:
                # Same day - no change
                pass
            else:
                # Streak broken - reset to 1
                current_streak = 1
        else:
            current_streak = 1
        
        # Update longest streak if needed
        if current_streak > longest_streak:
            longest_streak = current_streak
        
        # Calculate multiplier (10% per consecutive day, max 2x)
        multiplier = min(1.0 + (current_streak - 1) * 0.1, 2.0)
        
        # Update database
        query = '''
            UPDATE client_streaks 
            SET current_streak=?, longest_streak=?, last_attendance_date=?, streak_multiplier=?
            WHERE client_id=?
        '''
        self.db.cursor.execute(query, (current_streak, longest_streak, 
                                       check_in_date.strftime('%Y-%m-%d'), 
                                       multiplier, client_id))
        self.db.conn.commit()
        self.db.disconnect()
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'multiplier': multiplier,
            'days_to_next_bonus': 1 if multiplier < 2.0 else 0
        }
    
    def get_client_progress(self, client_id):
        """Get complete progress overview for client"""
        gam_data = self._get_gamification_data(client_id)
        streak_data = self._get_streak_data(client_id)
        
        if not gam_data:
            return None
        
        current_level = gam_data['current_level']
        next_level_exp = self.EXP_TABLE.get(current_level + 1, 0)
        
        return {
            'level': current_level,
            'current_exp': gam_data['current_exp'],
            'total_exp': gam_data['total_exp'],
            'next_level_exp': next_level_exp,
            'exp_to_next_level': next_level_exp - gam_data['current_exp'],
            'progress_percentage': (gam_data['current_exp'] / next_level_exp * 100) if next_level_exp > 0 else 0,
            'rank': gam_data['rank'],
            'class': gam_data['client_class'],
            'class_info': self.CLASSES.get(gam_data['client_class']),
            'can_choose_class': current_level >= 5 and not gam_data['client_class'],
            'streak': streak_data['current_streak'] if streak_data else 0,
            'longest_streak': streak_data['longest_streak'] if streak_data else 0,
            'streak_multiplier': streak_data['streak_multiplier'] if streak_data else 1.0
        }
    
    def _get_gamification_data(self, client_id):
        """Get client's gamification data"""
        query = 'SELECT * FROM client_gamification WHERE client_id=?'
        result = self.db.execute_query(query, (client_id,))
        return dict(result[0]) if result else None
    
    def _get_streak_data(self, client_id):
        """Get client's streak data"""
        query = 'SELECT * FROM client_streaks WHERE client_id=?'
        result = self.db.execute_query(query, (client_id,))
        return dict(result[0]) if result else None
    
    def _get_streak_multiplier(self, client_id):
        """Get current streak multiplier"""
        streak_data = self._get_streak_data(client_id)
        return streak_data['streak_multiplier'] if streak_data else 1.0
    
    def _get_class_multiplier(self, client_class, exercise_type):
        """Get class bonus multiplier for exercise type"""
        if not client_class or not exercise_type:
            return 1.0
        
        # Simplified class bonuses based on exercise type
        class_bonuses = {
            'Warrior': ['strength', 'power', 'weights'],
            'Ranger': ['cardio', 'endurance', 'running'],
            'Tank': ['compound', 'full-body', 'functional'],
            'Assassin': ['hiit', 'speed', 'agility'],
            'Mage': ['balance', 'flexibility', 'technique']
        }
        
        if client_class in class_bonuses:
            bonus_types = class_bonuses[client_class]
            if any(bonus_type in exercise_type.lower() for bonus_type in bonus_types):
                return self.CLASSES[client_class]['multiplier']
        
        return 1.0
    
    @staticmethod
    def get_all_classes():
        """Get list of all available classes"""
        return GamificationController.CLASSES


# Example usage and testing
if __name__ == "__main__":
    from models.client import Client
    from database.db_manager import DatabaseManager
    
    # Initialize database
    db = DatabaseManager()
    db.initialize_database()
    
    # Create test client
    client = Client(
        phone_number="5551234567",
        first_name="Test",
        last_name="Player",
        email="test@gym.com",
        date_of_birth="1995-01-01",
        gender="Male"
    )
    client_id = client.save(pin="1234")
    
    # Test gamification
    gam = GamificationController()
    
    print("=== Testing Gamification System ===\n")
    
    # Initial progress
    progress = gam.get_client_progress(client_id)
    print(f"Initial Level: {progress['level']}")
    print(f"Initial EXP: {progress['current_exp']}/{progress['next_level_exp']}")
    print(f"Initial Rank: {progress['rank']}\n")
    
    # Add experience (simulate workout)
    print("Simulating workout...")
    result = gam.add_experience(client_id, base_exp=50, exercise_type='strength')
    print(f"✅ Gained {result['exp_gained']} EXP (base: {result['base_exp']}, multiplier: {result['total_multiplier']:.2f}x)")
    if result['leveled_up']:
        print(f"🎉 LEVEL UP! Now level {result['new_level']}!")
    print()
    
    # Update streak
    print("Checking in for today...")
    streak = gam.update_streak(client_id)
    print(f"✅ Current streak: {streak['current_streak']} days")
    print(f"   Multiplier: {streak['multiplier']:.2f}x")
    print()
    
    # Simulate multiple workouts to reach level 5
    print("Simulating multiple workouts to reach level 5...")
    for i in range(10):
        result = gam.add_experience(client_id, base_exp=100)
        if result['leveled_up']:
            print(f"  Level {result['new_level']} reached!")
    print()
    
    # Try to unlock class
    progress = gam.get_client_progress(client_id)
    if progress['can_choose_class']:
        print("Level 5 reached! Unlocking Warrior class...")
        unlock_result = gam.unlock_class(client_id, 'Warrior')
        if unlock_result['success']:
            print(f"✅ {unlock_result['message']}")
            print(f"   Bonus: {unlock_result['class_info']['bonus']}")
    
    # Update rank based on physical tests
    print("\nUpdating rank based on physical tests...")
    test_scores = {'push-ups': 50, 'squats': 80, 'sit-ups': 60}
    new_rank = gam.update_rank(client_id, test_scores)
    print(f"✅ New rank: {new_rank}")
    
    # Final progress
    print("\n=== Final Progress ===")
    final_progress = gam.get_client_progress(client_id)
    print(f"Level: {final_progress['level']}")
    print(f"EXP: {final_progress['current_exp']}/{final_progress['next_level_exp']}")
    print(f"Rank: {final_progress['rank']}")
    print(f"Class: {final_progress['class']}")
    print(f"Streak: {final_progress['streak']} days ({final_progress['streak_multiplier']:.2f}x multiplier)")
