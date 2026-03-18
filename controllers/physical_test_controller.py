# controllers/physical_test_controller.py
import sys
import os
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from controllers.gamification_controller import GamificationController

class PhysicalTestController:
    """Manages physical fitness tests and ranking system (E to SS)"""
    
    # Ranking criteria for each test
    TEST_RANKINGS = {
        'Push-ups': {
            'SS': 60, 'S': 50, 'A': 40, 'B': 30, 'C': 20, 'D': 10, 'E': 0
        },
        'Squats': {
            'SS': 100, 'S': 80, 'A': 60, 'B': 45, 'C': 30, 'D': 15, 'E': 0
        },
        'Sit-ups': {
            'SS': 80, 'S': 65, 'A': 50, 'B': 35, 'C': 25, 'D': 15, 'E': 0
        },
        'High Jump': {  # in centimeters
            'SS': 70, 'S': 60, 'A': 50, 'B': 40, 'C': 30, 'D': 20, 'E': 0
        },
        'Sprint': {  # 100m in seconds (lower is better)
            'SS': 12.0, 'S': 13.5, 'A': 15.0, 'B': 17.0, 'C': 19.0, 'D': 22.0, 'E': 999
        }
    }
    
    # Points awarded for each rank
    RANK_POINTS = {
        'SS': 200, 'S': 150, 'A': 100, 'B': 70, 'C': 40, 'D': 20, 'E': 0
    }
    
    def __init__(self):
        self.db = DatabaseManager()
        self.gamification = GamificationController()
    
    def record_test_result(self, client_id, test_name, score, notes=None, test_date=None):
        """
        Record a physical test result and calculate rank
        Returns: dict with test result and rank achieved
        """
        if test_date is None:
            test_date = date.today()
        elif isinstance(test_date, str):
            test_date = datetime.strptime(test_date, '%Y-%m-%d').date()
        
        # Get test ID
        test = self._get_test_by_name(test_name)
        if not test:
            return {'success': False, 'message': f'Test "{test_name}" not found'}
        
        # Calculate rank for this test
        rank = self._calculate_rank(test_name, score)
        
        # Save result
        self.db.connect()
        query = '''
            INSERT INTO test_results (client_id, test_id, test_date, score, rank_achieved, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        self.db.cursor.execute(query, (
            client_id, test['test_id'], test_date.strftime('%Y-%m-%d'), 
            score, rank, notes
        ))
        self.db.conn.commit()
        result_id = self.db.cursor.lastrowid
        self.db.disconnect()
        
        # Award EXP based on rank
        points = self.RANK_POINTS[rank]
        exp_result = self.gamification.add_experience(client_id, base_exp=points)
        
        return {
            'success': True,
            'result_id': result_id,
            'test_name': test_name,
            'score': score,
            'rank': rank,
            'points': points,
            'exp_earned': exp_result['exp_gained'],
            'leveled_up': exp_result['leveled_up'],
            'new_level': exp_result['new_level']
        }
    
    def complete_full_assessment(self, client_id, test_scores, test_date=None):
        """
        Complete all 5 physical tests and update overall rank.
        Returns a summary with EXP and rank information.
        """
        if test_date is None:
            test_date = date.today()

        results = []
        total_points = 0

        # Record individual tests
        for test_name, score in test_scores.items():
            result = self.record_test_result(client_id, test_name, score, test_date=test_date)
            if result['success']:
                results.append(result)
                total_points += result['points']

        # Determine overall rank
        overall_rank = self._calculate_overall_rank(total_points)

        # ✅ Update client rank in gamification system
        new_rank = self.gamification.update_rank(client_id, overall_rank)

        return {
            'success': True,
            'test_date': test_date.strftime('%Y-%m-%d'),
            'individual_results': results,
            'total_points': total_points,
            'overall_rank': overall_rank,
            'rank_updated_to': new_rank,
            'total_exp_earned': sum(r['exp_earned'] for r in results)
        }
    
    def get_client_test_history(self, client_id, test_name=None):
        """Get test history for a client (all tests or specific test)"""
        if test_name:
            test = self._get_test_by_name(test_name)
            if not test:
                return []
            
            query = '''
                SELECT tr.*, pt.test_name, pt.measurement_unit
                FROM test_results tr
                JOIN physical_tests pt ON tr.test_id = pt.test_id
                WHERE tr.client_id=? AND tr.test_id=?
                ORDER BY tr.test_date DESC
            '''
            results = self.db.execute_query(query, (client_id, test['test_id']))
        else:
            query = '''
                SELECT tr.*, pt.test_name, pt.measurement_unit
                FROM test_results tr
                JOIN physical_tests pt ON tr.test_id = pt.test_id
                WHERE tr.client_id=?
                ORDER BY tr.test_date DESC, pt.test_name
            '''
            results = self.db.execute_query(query, (client_id,))
        
        history = []
        for row in results:
            history.append({
                'result_id': row['result_id'],
                'test_name': row['test_name'],
                'test_date': row['test_date'],
                'score': row['score'],
                'rank': row['rank_achieved'],
                'measurement_unit': row['measurement_unit'],
                'notes': row['notes']
            })
        
        return history
    
    def get_latest_assessment(self, client_id):
        """Get the most recent complete assessment (all 5 tests)"""
        # Get the most recent date where client did tests
        query = '''
            SELECT test_date, COUNT(DISTINCT test_id) as test_count
            FROM test_results
            WHERE client_id=?
            GROUP BY test_date
            ORDER BY test_date DESC
            LIMIT 1
        '''
        result = self.db.execute_query(query, (client_id,))
        
        if not result or result[0]['test_count'] < 5:
            return None
        
        assessment_date = result[0]['test_date']
        
        # Get all tests from that date
        query = '''
            SELECT tr.*, pt.test_name, pt.measurement_unit
            FROM test_results tr
            JOIN physical_tests pt ON tr.test_id = pt.test_id
            WHERE tr.client_id=? AND tr.test_date=?
        '''
        results = self.db.execute_query(query, (client_id, assessment_date))
        
        tests = []
        total_points = 0
        
        for row in results:
            test_data = {
                'test_name': row['test_name'],
                'score': row['score'],
                'rank': row['rank_achieved'],
                'points': self.RANK_POINTS[row['rank_achieved']],
                'measurement_unit': row['measurement_unit']
            }
            tests.append(test_data)
            total_points += test_data['points']
        
        overall_rank = self._calculate_overall_rank(total_points)
        
        return {
            'assessment_date': assessment_date,
            'tests': tests,
            'total_points': total_points,
            'overall_rank': overall_rank
        }
    
    def get_test_progress(self, client_id, test_name):
        """Track improvement on a specific test over time"""
        history = self.get_client_test_history(client_id, test_name)
        
        if not history:
            return None
        
        # Reverse to show oldest to newest
        history.reverse()
        
        # Calculate improvement
        if len(history) >= 2:
            first_score = history[0]['score']
            latest_score = history[-1]['score']
            
            # For sprint, lower is better
            if test_name == 'Sprint':
                improvement = first_score - latest_score
                improvement_pct = (improvement / first_score) * 100 if first_score > 0 else 0
            else:
                improvement = latest_score - first_score
                improvement_pct = (improvement / first_score) * 100 if first_score > 0 else 0
            
            best_score = min([h['score'] for h in history]) if test_name == 'Sprint' else max([h['score'] for h in history])
        else:
            improvement = 0
            improvement_pct = 0
            best_score = history[0]['score']
        
        return {
            'test_name': test_name,
            'total_attempts': len(history),
            'first_score': history[0]['score'],
            'latest_score': history[-1]['score'],
            'best_score': best_score,
            'improvement': round(improvement, 2),
            'improvement_percentage': round(improvement_pct, 1),
            'history': history
        }
    
    def get_rank_requirements(self, test_name=None):
        """Get ranking criteria for tests"""
        if test_name:
            return {
                'test_name': test_name,
                'requirements': self.TEST_RANKINGS.get(test_name, {})
            }
        else:
            return self.TEST_RANKINGS
    
    def get_next_rank_target(self, client_id, test_name):
        """Get what score is needed to reach next rank"""
        history = self.get_client_test_history(client_id, test_name)
        
        if not history:
            return None
        
        current_score = history[0]['score']
        current_rank = history[0]['rank']
        
        # Get rank hierarchy
        rank_order = ['E', 'D', 'C', 'B', 'A', 'S', 'SS']
        current_index = rank_order.index(current_rank)
        
        if current_index >= len(rank_order) - 1:
            return {
                'current_rank': current_rank,
                'message': 'Maximum rank achieved! 🏆'
            }
        
        next_rank = rank_order[current_index + 1]
        next_score = self.TEST_RANKINGS[test_name][next_rank]
        
        # For sprint, lower is better
        if test_name == 'Sprint':
            score_needed = current_score - next_score
        else:
            score_needed = next_score - current_score
        
        return {
            'test_name': test_name,
            'current_score': current_score,
            'current_rank': current_rank,
            'next_rank': next_rank,
            'target_score': next_score,
            'score_needed': abs(score_needed),
            'message': f"Reach {next_score} to achieve rank {next_rank}!"
        }
    
    def _calculate_rank(self, test_name, score):
        """Calculate rank for a single test score"""
        if test_name not in self.TEST_RANKINGS:
            return 'E'
        
        thresholds = self.TEST_RANKINGS[test_name]
        
        # For sprint, lower is better
        if test_name == 'Sprint':
            for rank in ['SS', 'S', 'A', 'B', 'C', 'D']:
                if score <= thresholds[rank]:
                    return rank
            return 'E'
        else:
            # For other tests, higher is better
            for rank in ['SS', 'S', 'A', 'B', 'C', 'D']:
                if score >= thresholds[rank]:
                    return rank
            return 'E'
    
    def _calculate_overall_rank(self, total_points):
        """Calculate overall rank based on total points from all tests"""
        if total_points >= 900:  # Near perfect scores
            return 'SS'
        elif total_points >= 650:
            return 'S'
        elif total_points >= 450:
            return 'A'
        elif total_points >= 300:
            return 'B'
        elif total_points >= 150:
            return 'C'
        elif total_points >= 50:
            return 'D'
        else:
            return 'E'
    
    def _get_test_by_name(self, test_name):
        """Get test info by name"""
        query = 'SELECT * FROM physical_tests WHERE test_name=?'
        result = self.db.execute_query(query, (test_name,))
        return dict(result[0]) if result else None
    
    def get_all_tests(self):
        """Get list of all available tests"""
        query = 'SELECT * FROM physical_tests ORDER BY test_name'
        results = self.db.execute_query(query)
        return [dict(row) for row in results]


# Example usage and testing
if __name__ == "__main__":
    from database.db_manager import DatabaseManager
    from models.client import Client
    
    # Initialize database
    db = DatabaseManager()
    db.initialize_database()
    
    # Create test client
    client = Client(
        phone_number="5556667777",
        first_name="Physical",
        last_name="Tester",
        email="physical@gym.com",
        date_of_birth="1990-12-05"
    )
    client_id = client.save(pin="4444")
    print(f"✅ Created test client: {client.full_name}\n")
    
    # Initialize test controller
    test_ctrl = PhysicalTestController()
    
    print("=== Testing Physical Test System ===\n")
    
    # Show all available tests
    print("--- Available Tests ---")
    all_tests = test_ctrl.get_all_tests()
    for test in all_tests:
        print(f"  • {test['test_name']} ({test['measurement_unit']})")
        print(f"    {test['description']}")
    print()
    
    # Show rank requirements
    print("--- Rank Requirements ---")
    print("Push-ups:")
    requirements = test_ctrl.get_rank_requirements('Push-ups')
    for rank, threshold in sorted(requirements['requirements'].items(), 
                                  key=lambda x: x[1], reverse=True):
        print(f"  {rank}: {threshold}+ reps")
    print()
    
    # Complete a full assessment
    print("--- Complete Physical Assessment ---")
    test_scores = {
        'Push-ups': 42,
        'Squats': 65,
        'Sit-ups': 55,
        'High Jump': 48,
        'Sprint': 15.2
    }
    
    assessment = test_ctrl.complete_full_assessment(client_id, test_scores)
    if assessment['success']:
        print(f"✅ Assessment completed on {assessment['test_date']}")
        print(f"\nIndividual Results:")
        for result in assessment['individual_results']:
            print(f"  • {result['test_name']}: {result['score']} - Rank {result['rank']} "
                  f"({result['points']} points, +{result['exp_earned']} EXP)")
        print(f"\nTotal Points: {assessment['total_points']}")
        print(f"Overall Rank: {assessment['overall_rank']}")
        print(f"Total EXP Earned: {assessment['total_exp_earned']}")
    print()
    
    # Record improvement after training
    print("--- Simulating Progress After Training ---")
    improved_scores = {
        'Push-ups': 48,
        'Squats': 72,
        'Sit-ups': 60,
        'High Jump': 52,
        'Sprint': 14.5
    }
    
    from datetime import timedelta
    future_date = date.today() + timedelta(days=30)
    assessment2 = test_ctrl.complete_full_assessment(client_id, improved_scores, test_date=future_date)
    print(f"✅ Follow-up assessment completed")
    print(f"New Overall Rank: {assessment2['overall_rank']}")
    print(f"Total Points: {assessment2['total_points']} "
          f"(+{assessment2['total_points'] - assessment['total_points']} improvement)")
    print()
    
    # Get test progress
    print("--- Push-ups Progress Tracking ---")
    progress = test_ctrl.get_test_progress(client_id, 'Push-ups')
    if progress:
        print(f"Test: {progress['test_name']}")
        print(f"Total Attempts: {progress['total_attempts']}")
        print(f"First Score: {progress['first_score']}")
        print(f"Latest Score: {progress['latest_score']}")
        print(f"Best Score: {progress['best_score']}")
        print(f"Improvement: +{progress['improvement']} ({progress['improvement_percentage']:+.1f}%)")
        print("\nHistory:")
        for h in progress['history']:
            print(f"  {h['test_date']}: {h['score']} reps (Rank {h['rank']})")
    print()
    
    # Get next rank target
    print("--- Next Rank Targets ---")
    for test_name in ['Push-ups', 'Squats', 'Sit-ups']:
        target = test_ctrl.get_next_rank_target(client_id, test_name)
        if target and 'next_rank' in target:
            print(f"{test_name}:")
            print(f"  Current: {target['current_score']} (Rank {target['current_rank']})")
            print(f"  Target: {target['target_score']} for Rank {target['next_rank']}")
            print(f"  Need: +{target['score_needed']} more")
        elif target:
            print(f"{test_name}: {target['message']}")
    print()
    
    # Get latest assessment
    print("--- Latest Complete Assessment ---")
    latest = test_ctrl.get_latest_assessment(client_id)
    if latest:
        print(f"Date: {latest['assessment_date']}")
        print(f"Overall Rank: {latest['overall_rank']}")
        print(f"Tests Completed:")
        for test in latest['tests']:
            print(f"  • {test['test_name']}: {test['score']} {test['measurement_unit']} "
                  f"(Rank {test['rank']}, {test['points']} pts)")
