# controllers/attendance_controller.py
import sys
import os
from datetime import datetime, date, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from controllers.gamification_controller import GamificationController

class AttendanceController:
    """Manages client check-ins, check-outs, and attendance tracking"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.gamification = GamificationController()
    
    def check_in(self, client_id, check_in_date=None, check_in_time=None):
        """
        Record client check-in
        Returns: dict with check-in info and streak update (synced to leaderboard)
        """
        if check_in_date is None:
            check_in_date = date.today()
        elif isinstance(check_in_date, str):
            check_in_date = datetime.strptime(check_in_date, '%Y-%m-%d').date()

        if check_in_time is None:
            check_in_time = datetime.now().strftime('%H:%M:%S')

        # Prevent duplicate same-day check-in
        existing = self._get_attendance_for_date(client_id, check_in_date)
        if existing:
            return {
                'success': False,
                'message': 'Already checked in today',
                'attendance_id': existing['attendance_id']
            }

        # ✅ Insert attendance record
        self.db.connect()
        query = '''
            INSERT OR IGNORE INTO attendance (client_id, check_in_date, check_in_time)
            VALUES (?, ?, ?)
        '''
        self.db.cursor.execute(query, (client_id, check_in_date.strftime('%Y-%m-%d'), check_in_time))
        self.db.conn.commit()
        attendance_id = self.db.cursor.lastrowid
        self.db.disconnect()

        # ✅ Update streaks automatically (and mirror into client_gamification)
        try:
            self.db.update_streak(client_id)
        except Exception as e:
            print(f"⚠️ Warning: failed to update streak for client {client_id}: {e}")

        # ✅ Get updated streak info for return payload
        streak_data = self.db.execute_query(
            "SELECT current_streak, longest_streak FROM client_gamification WHERE client_id = ?",
            (client_id,)
        )
        streak_info = dict(streak_data[0]) if streak_data else {'current_streak': 1, 'longest_streak': 1}

        return {
            'success': True,
            'message': 'Check-in successful!',
            'attendance_id': attendance_id,
            'check_in_date': check_in_date.strftime('%Y-%m-%d'),
            'check_in_time': check_in_time,
            'streak': streak_info
        }
    
    def check_out(self, client_id, check_out_time=None):
        """Record client check-out for today and update EXP if applicable"""
        if check_out_time is None:
            check_out_time = datetime.now().strftime('%H:%M:%S')

        today = date.today()
        attendance = self._get_attendance_for_date(client_id, today)

        if not attendance:
            return {'success': False, 'message': 'No check-in found for today'}

        if attendance['check_out_time']:
            return {
                'success': False,
                'message': 'Already checked out',
                'check_out_time': attendance['check_out_time']
            }

        # ✅ Record check-out time
        self.db.connect()
        self.db.cursor.execute(
            'UPDATE attendance SET check_out_time=? WHERE attendance_id=?',
            (check_out_time, attendance['attendance_id'])
        )
        self.db.conn.commit()
        self.db.disconnect()

        # Calculate session duration
        check_in = datetime.strptime(attendance['check_in_time'], '%H:%M:%S')
        check_out = datetime.strptime(check_out_time, '%H:%M:%S')
        duration = check_out - check_in
        duration_minutes = int(duration.total_seconds() / 60)

        # Optional EXP bonus for completing longer sessions
        exp_bonus = 0
        if duration_minutes >= 45:
            exp_bonus = 10
            self.update_attendance_exp(attendance['attendance_id'], exp_bonus)

        return {
            'success': True,
            'message': 'Check-out successful!',
            'check_in_time': attendance['check_in_time'],
            'check_out_time': check_out_time,
            'duration_minutes': duration_minutes,
            'exp_earned': attendance['exp_earned'] + exp_bonus
        }
    
    def get_attendance_history(self, client_id, limit=30):
        """Get recent attendance records for a client (with streaks and exp)"""
        query = '''
            SELECT * FROM attendance 
            WHERE client_id=?
            ORDER BY check_in_date DESC, check_in_time DESC
            LIMIT ?
        '''
        results = self.db.execute_query(query, (client_id, limit))

        history = []
        for row in results:
            record = {
                'attendance_id': row['attendance_id'],
                'check_in_date': row['check_in_date'],
                'check_in_time': row['check_in_time'],
                'check_out_time': row['check_out_time'],
                'exp_earned': row['exp_earned']
            }
            # Duration
            if row['check_out_time']:
                check_in = datetime.strptime(row['check_in_time'], '%H:%M:%S')
                check_out = datetime.strptime(row['check_out_time'], '%H:%M:%S')
                record['duration_minutes'] = int((check_out - check_in).total_seconds() / 60)
            history.append(record)

        # ✅ Include current streak for UI/portal display
        streak_data = self.db.execute_query(
            "SELECT current_streak, longest_streak FROM client_gamification WHERE client_id = ?",
            (client_id,)
        )
        streak_info = dict(streak_data[0]) if streak_data else {'current_streak': 0, 'longest_streak': 0}

        return {'history': history, 'streak': streak_info}
        
    def get_monthly_attendance(self, client_id, year=None, month=None):
        """Get attendance statistics for a specific month"""
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month
        
        # Get all attendance for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        query = '''
            SELECT * FROM attendance 
            WHERE client_id=? AND check_in_date >= ? AND check_in_date < ?
            ORDER BY check_in_date
        '''
        results = self.db.execute_query(query, (client_id, start_date.strftime('%Y-%m-%d'), 
                                                end_date.strftime('%Y-%m-%d')))
        
        total_days = len(results)
        total_exp = sum(row['exp_earned'] for row in results)
        
        # Count days per week
        days_by_weekday = {}
        for row in results:
            check_in_date = datetime.strptime(row['check_in_date'], '%Y-%m-%d').date()
            weekday = check_in_date.strftime('%A')
            days_by_weekday[weekday] = days_by_weekday.get(weekday, 0) + 1
        
        return {
            'year': year,
            'month': month,
            'total_days': total_days,
            'total_exp_earned': total_exp,
            'days_by_weekday': days_by_weekday,
            'attendance_records': [dict(row) for row in results]
        }
    
    def get_attendance_stats(self, client_id):
        """Get overall attendance + streak statistics"""
        query = '''
            SELECT 
                COUNT(*) as total_visits,
                SUM(exp_earned) as total_exp,
                MIN(check_in_date) as first_visit,
                MAX(check_in_date) as last_visit
            FROM attendance
            WHERE client_id=?
        '''
        result = self.db.execute_query(query, (client_id,))

        if not result or result[0]['total_visits'] == 0:
            return None

        stats = dict(result[0])

        # Compute average weekly visits
        if stats['first_visit'] and stats['last_visit']:
            first = datetime.strptime(stats['first_visit'], '%Y-%m-%d').date()
            last = datetime.strptime(stats['last_visit'], '%Y-%m-%d').date()
            weeks = max((last - first).days / 7, 1)
            stats['avg_visits_per_week'] = round(stats['total_visits'] / weeks, 1)
        else:
            stats['avg_visits_per_week'] = 0

        # ✅ Add streak information for dashboard/leaderboard
        streak_data = self.db.execute_query(
            "SELECT current_streak, longest_streak FROM client_gamification WHERE client_id = ?",
            (client_id,)
        )
        if streak_data:
            stats['current_streak'] = streak_data[0]['current_streak']
            stats['longest_streak'] = streak_data[0]['longest_streak']
        else:
            stats['current_streak'] = 0
            stats['longest_streak'] = 0

        return stats
    
    def update_attendance_exp(self, attendance_id, exp_amount):
        """Add EXP earned to an attendance record"""
        self.db.connect()
        query = '''
            UPDATE attendance 
            SET exp_earned = exp_earned + ?
            WHERE attendance_id=?
        '''
        self.db.cursor.execute(query, (exp_amount, attendance_id))
        self.db.conn.commit()
        self.db.disconnect()
    
    def is_checked_in_today(self, client_id):
        """Check if client has checked in today"""
        today = date.today()
        attendance = self._get_attendance_for_date(client_id, today)
        return attendance is not None
    
    def get_todays_attendance(self, client_id):
        """Get today's attendance record if it exists"""
        today = date.today()
        return self._get_attendance_for_date(client_id, today)
    
    def _get_attendance_for_date(self, client_id, check_date):
        """Helper to get attendance for a specific date"""
        if isinstance(check_date, date):
            check_date = check_date.strftime('%Y-%m-%d')
        
        query = '''
            SELECT * FROM attendance 
            WHERE client_id=? AND check_in_date=?
        '''
        results = self.db.execute_query(query, (client_id, check_date))
        return dict(results[0]) if results else None
    
    def get_gym_attendance_today(self):
        """Get all clients who checked in today (for admin view)"""
        today = date.today().strftime('%Y-%m-%d')
        query = '''
            SELECT a.*, c.first_name, c.last_name, c.phone_number
            FROM attendance a
            JOIN clients c ON a.client_id = c.client_id
            WHERE a.check_in_date = ?
            ORDER BY a.check_in_time DESC
        '''
        results = self.db.execute_query(query, (today,))
        
        attendance_list = []
        for row in results:
            record = {
                'client_id': row['client_id'],
                'client_name': f"{row['first_name']} {row['last_name']}",
                'phone_number': row['phone_number'],
                'check_in_time': row['check_in_time'],
                'check_out_time': row['check_out_time'],
                'exp_earned': row['exp_earned']
            }
            attendance_list.append(record)
        
        return attendance_list
    
    def get_weekly_attendance_report(self, start_date=None):
        """Get attendance report for the week (for admin)"""
        if start_date is None:
            # Get Monday of current week
            today = date.today()
            start_date = today - timedelta(days=today.weekday())
        elif isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        end_date = start_date + timedelta(days=7)
        
        query = '''
            SELECT check_in_date, COUNT(*) as count
            FROM attendance
            WHERE check_in_date >= ? AND check_in_date < ?
            GROUP BY check_in_date
            ORDER BY check_in_date
        '''
        results = self.db.execute_query(query, (start_date.strftime('%Y-%m-%d'), 
                                                end_date.strftime('%Y-%m-%d')))
        
        # Create dict with all days of the week
        weekly_data = {}
        current_date = start_date
        for i in range(7):
            weekly_data[current_date.strftime('%Y-%m-%d')] = {
                'date': current_date.strftime('%Y-%m-%d'),
                'day_name': current_date.strftime('%A'),
                'count': 0
            }
            current_date += timedelta(days=1)
        
        # Fill in actual counts
        for row in results:
            if row['check_in_date'] in weekly_data:
                weekly_data[row['check_in_date']]['count'] = row['count']
        
        return {
            'week_start': start_date.strftime('%Y-%m-%d'),
            'week_end': (end_date - timedelta(days=1)).strftime('%Y-%m-%d'),
            'daily_attendance': list(weekly_data.values()),
            'total_visits': sum(day['count'] for day in weekly_data.values())
        }


# Example usage and testing
if __name__ == "__main__":
    from database.db_manager import DatabaseManager
    from models.client import Client
    
    # Initialize database
    db = DatabaseManager()
    db.initialize_database()
    
    # Create test client
    client = Client(
        phone_number="5551112222",
        first_name="Attendance",
        last_name="Tester",
        email="attendance@gym.com",
        date_of_birth="1993-06-20"
    )
    client_id = client.save(pin="9999")
    print(f"✅ Created test client: {client.full_name}\n")
    
    # Test attendance system
    attendance = AttendanceController()
    
    print("=== Testing Attendance System ===\n")
    
    # Check in
    print("--- Check In ---")
    result = attendance.check_in(client_id)
    if result['success']:
        print(f"✅ {result['message']}")
        print(f"   Date: {result['check_in_date']}")
        print(f"   Time: {result['check_in_time']}")
        print(f"   Streak: {result['streak']['current_streak']} days ({result['streak']['multiplier']:.2f}x)")
        attendance_id = result['attendance_id']
    print()
    
    # Try to check in again (should fail)
    print("--- Duplicate Check In Test ---")
    result2 = attendance.check_in(client_id)
    if not result2['success']:
        print(f"❌ {result2['message']} (Expected behavior)")
    print()
    
    # Check if checked in today
    print("--- Check Status ---")
    if attendance.is_checked_in_today(client_id):
        print("✅ Client is currently checked in")
    print()
    
    # Simulate workout and add EXP
    print("--- Simulating Workout ---")
    attendance.update_attendance_exp(attendance_id, 150)
    print("✅ Added 150 EXP to today's session")
    print()
    
    # Check out
    print("--- Check Out ---")
    result = attendance.check_out(client_id)
    if result['success']:
        print(f"✅ {result['message']}")
        print(f"   Duration: {result['duration_minutes']} minutes")
        print(f"   Total EXP earned: {result['exp_earned']}")
    print()
    
    # Simulate attendance for past few days
    print("--- Simulating Past Attendance ---")
    for i in range(1, 6):
        past_date = date.today() - timedelta(days=i)
        attendance.check_in(client_id, check_in_date=past_date)
        print(f"✅ Added check-in for {past_date.strftime('%A, %Y-%m-%d')}")
    print()
    
    # Get attendance history
    print("--- Attendance History (Last 7 days) ---")
    history = attendance.get_attendance_history(client_id, limit=7)
    for record in history:
        print(f"  {record['check_in_date']} - {record['check_in_time']}")
        if record['check_out_time']:
            print(f"    Duration: {record.get('duration_minutes', 0)} min | EXP: {record['exp_earned']}")
    print()
    
    # Get attendance stats
    print("--- Overall Attendance Statistics ---")
    stats = attendance.get_attendance_stats(client_id)
    if stats:
        print(f"  Total Visits: {stats['total_visits']}")
        print(f"  Total EXP Earned: {stats['total_exp']}")
        print(f"  First Visit: {stats['first_visit']}")
        print(f"  Last Visit: {stats['last_visit']}")
        print(f"  Avg Visits/Week: {stats['avg_visits_per_week']}")
    print()
    
    # Get monthly attendance
    print("--- Monthly Attendance Report ---")
    monthly = attendance.get_monthly_attendance(client_id)
    print(f"  Month: {monthly['month']}/{monthly['year']}")
    print(f"  Total Days: {monthly['total_days']}")
    print(f"  Total EXP: {monthly['total_exp_earned']}")
    print(f"  Days by Weekday:")
    for day, count in monthly['days_by_weekday'].items():
        print(f"    {day}: {count} visits")
    print()
    
    # Admin view: Today's gym attendance
    print("--- Today's Gym Attendance (Admin View) ---")
    todays_attendance = attendance.get_gym_attendance_today()
    print(f"Total clients today: {len(todays_attendance)}")
    for record in todays_attendance:
        status = "Checked out" if record['check_out_time'] else "Still in gym"
        print(f"  • {record['client_name']} - {record['check_in_time']} ({status})")
    print()
    
    # Weekly report
    print("--- Weekly Attendance Report ---")
    weekly = attendance.get_weekly_attendance_report()
    print(f"Week: {weekly['week_start']} to {weekly['week_end']}")
    print(f"Total visits: {weekly['total_visits']}")
    print("Daily breakdown:")
    for day in weekly['daily_attendance']:
        print(f"  {day['day_name']}: {day['count']} visits")
