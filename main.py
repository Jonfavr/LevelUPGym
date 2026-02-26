# main.py
"""
Flask web server for LevelUp Gym Client Portal & Admin Portal
Run this on the gym's computer to allow clients and admins to access via local network
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory, send_file, render_template_string
from functools import wraps
import sys
import os
from datetime import datetime, date, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.client import Client
from models.routine import Routine
from models.exercise_model import Exercise
from controllers.gamification_controller import GamificationController
from controllers.attendance_controller import AttendanceController
from controllers.workout_logger import WorkoutLogger
from controllers.achievement_controller import AchievementController
from controllers.physical_test_controller import PhysicalTestController
# 🔄 CHANGED: Added new import
from controllers.workout_session_controller import WorkoutSessionController
from database.db_manager import DatabaseManager
from controllers.membership_controller import MembershipController
from controllers.salespoint_controller import SalesPointController

app = Flask(__name__)
app.secret_key = 'levelup_gym_secret_key_change_in_production'  # Change this in production

# Initialize controllers
gamification = GamificationController()
attendance_ctrl = AttendanceController()
workout_logger = WorkoutLogger()
achievement_ctrl = AchievementController()
test_ctrl = PhysicalTestController()
session_ctrl = WorkoutSessionController()
sales_ctrl = SalesPointController()

# Initialize database
db = DatabaseManager()
db.initialize_database()

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'client_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def apply_session_swaps(exercises, swaps):
    # Apply per-session exercise swaps to an exercise list.
    # swaps = {old_exercise_id: new_exercise_id}
    # Returns a new list with swapped exercises fetched from DB.

    if not swaps:
        return exercises

    result = []
    for ex in exercises:
        ex_id = ex['exercise_id'] if isinstance(ex, dict) else ex.exercise_id
        if ex_id in swaps:
            new_id = swaps[ex_id]
            new_ex = Exercise.get_by_id(new_id)
            if new_ex:
                # Preserve sets/reps/rest from the original slot
                new_ex_dict = {
                    'exercise_id': new_ex.exercise_id,
                    'name': new_ex.name,
                    'description': new_ex.description,
                    'exercise_type': new_ex.exercise_type,
                    'target_muscle': new_ex.target_muscle,
                    'base_exp': new_ex.base_exp,
                    'image_path': new_ex.image_path,
                    'sets': ex['sets'],
                    'reps': ex['reps'],
                    'rest_seconds': ex['rest_seconds'],
                    'measurement': ex['measurement'],
                    'weight': ex.get('weight', 0),
                }
                result.append(new_ex_dict)
                continue
        result.append(ex)
    return result

# ==================== CLIENT ROUTES ====================

@app.route('/')
def index():
    """Home page - redirect to login or dashboard"""
    if 'client_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Client login page"""
    if request.method == 'POST':
        phone = request.form.get('phone')
        pin = request.form.get('pin')
        
        client = Client.authenticate(phone, pin)
        
        if client:
            session['client_id'] = client.client_id
            session['client_name'] = client.full_name
            
            # Check in automatically
            attendance_ctrl.check_in(client.client_id)
            
            flash(f'Welcome back, {client.first_name}! 💪', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid phone number or PIN', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and check out"""
    if 'client_id' in session:
        # Auto check-out
        attendance_ctrl.check_out(session['client_id'])
        session.clear()
        flash('You have been logged out. See you next time! 👋', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    client_id = session['client_id']
    client = Client.get_by_id(client_id)

    # --- Gamification & progress ---
    progress = gamification.get_client_progress(client_id)

    # --- Today's routine ---
    today = datetime.now().strftime('%A')
    today_routine = Routine.get_client_routine_for_day(client_id, today)
    routine_status = 'not_started'  # default fallback

    # --- If client has a routine assigned today ---
    if today_routine:
        routine_id = today_routine.routine_id

        # Try to get today's active session
        session_data = session_ctrl._get_session(client_id, routine_id, date.today())

        if session_data:
            # ✅ Make sure the status is correctly interpreted
            if session_data.get('status') == 'completed':
                routine_status = 'completed'
            elif session_data.get('status') == 'in_progress':
                routine_status = 'in_progress'
            else:
                routine_status = 'not_started'
        else:
            # No session record yet → definitely not started
            routine_status = 'not_started'

    # --- Recent achievements ---
    recent_achievements = achievement_ctrl.get_recent_unlocks(client_id, limit=3)

    # --- Streak info ---
    streak_data = client.get_streak_data()

    # --- Membership notification ---
    mc = MembershipController()
    membership = mc.get_client_membership(client_id)
    notification = None
    if membership:
        end_date = datetime.strptime(membership['end_date'], '%Y-%m-%d').date()
        days_left = (end_date - date.today()).days
        print("Days Left", days_left)
        if 0 < days_left <= 5:
            notification = f"⚠️ Your membership expires in {days_left} days. Please renew soon!"
        elif days_left <= 0:
            notification = "❌ Your membership has expired. Please renew to continue training."

    # --- Achievement unlocking (safe) ---
    try:
        newly_unlocked = achievement_ctrl.check_and_unlock_achievements(client_id)
    except Exception as e:
        print(f"Achievement check error for client {client_id}: {e}")
        newly_unlocked = []

    ann_rows = db.execute_query(
        """SELECT ann_id, title, body, ann_type, is_pinned
            FROM announcements
            WHERE (expires_at IS NULL OR expires_at >= ?)
            ORDER BY is_pinned DESC, ann_id DESC""",
        (date.today().isoformat(),)
    )
    announcements = [dict(r) for r in ann_rows]
    
    print("Notification:",notification)
    # --- Render dashboard ---
    return render_template(
        'dashboard.html',
        client=client,
        progress=progress,
        today_routine=today_routine,
        today=today,
        recent_achievements=recent_achievements,
        streak_data=streak_data,
        newly_unlocked=newly_unlocked,
        notification=notification,
        status=routine_status,
        announcements=announcements
    )

@app.route('/workout/<int:routine_id>')
@login_required
def workout(routine_id):
    """Start workout session"""
    client_id = session['client_id']
    routine = Routine.get_by_id(routine_id)
    
    if not routine:
        flash('Routine not found', 'error')
        return redirect(url_for('dashboard'))
    
    # Start or resume session
    session_info = session_ctrl.start_or_resume_session(client_id, routine_id)
    
    # If already completed today
    if session_info['status'] == 'completed':
        flash(session_info['message'] + f" You earned {session_info['total_exp']} EXP!", 'info')
        return redirect(url_for('dashboard'))
    
    exercises = routine.get_exercises()

    # Apply any session-level swaps (does NOT affect other clients)
    swaps = session_ctrl.get_session_swaps(session_info['session_id'])
    exercises = apply_session_swaps(exercises, swaps)

    # Get progress using the (possibly swapped) exercise list
    progress = session_ctrl.get_session_progress(session_info['session_id'], routine, exercises)
    
    # Store session_id in Flask session for easy access
    session['workout_session_id'] = session_info['session_id']
    
    return render_template('workout.html',
                         routine=routine,
                         exercises=exercises,
                         session_info=session_info,
                         progress=progress,
                         client_id = client_id)

@app.route('/log_set', methods=['POST'])
@login_required
def log_set():
    """Log a completed set"""
    client_id = session['client_id']
    workout_session_id = session.get('workout_session_id')
    
    if not workout_session_id:
        return jsonify({'success': False, 'message': 'No active workout session'}), 400
    
    data = request.json
    exercise_id = data.get('exercise_id')
    set_number = data.get('set_number')
    reps = data.get('reps')
    weight = data.get('weight')
    measurement = data.get('measurement')
    
    # Check if already completed
    if session_ctrl.is_set_completed(workout_session_id, exercise_id, set_number):
        return jsonify({'success': False, 'message': 'Set already logged'}), 400
    
    # Log the set
    result = workout_logger.log_set(
        client_id=client_id,
        exercise_id=exercise_id,
        set_number=set_number,
        reps_completed=reps,
        weight_used=weight if weight else None,
        measurement= measurement
    )
    
    if result['success']:
        # Mark set as completed in session
        session_ctrl.mark_set_completed(workout_session_id, exercise_id, set_number, reps, weight)
        
        # Update session EXP total
        session_ctrl.update_session_exp(workout_session_id, result['exp_earned'])
        
        # Get weight recommendation for NEXT set
        recommendation = session_ctrl.get_weight_recommendation(client_id, exercise_id, workout_session_id)
        result['recommendation'] = recommendation
    
    return jsonify(result)

@app.route('/progress')
@login_required
def progress():
    """Progress tracking page"""
    client_id = session['client_id']
    client = Client.get_by_id(client_id)
    
    # Get gamification progress
    progress_data = gamification.get_client_progress(client_id)
    
    # Get workout history
    workout_history = workout_logger.get_workout_history(client_id, limit=10)
    
    # Get attendance stats
    attendance_stats = attendance_ctrl.get_attendance_stats(client_id)
    
    # Get workout stats
    workout_stats = workout_logger.get_workout_stats(client_id)
    
    # Get personal records
    personal_records = workout_logger.get_personal_records(client_id)
    
    return render_template('progress.html',
                         client=client,
                         progress=progress_data,
                         workout_history=workout_history,
                         attendance_stats=attendance_stats,
                         workout_stats=workout_stats,
                         personal_records=personal_records)

@app.route('/achievements')
@login_required
def achievements():
    """Achievements page"""
    client_id = session['client_id']
    
    # Get all achievements
    all_achievements = achievement_ctrl.get_client_achievements(client_id)
    
    return render_template('achievements.html',
                         achievements=all_achievements)

@app.route('/classes')
@login_required
def classes():
    """Class selection page"""
    client_id = session['client_id']
    
    progress = gamification.get_client_progress(client_id)
    
    if not progress['can_choose_class']:
        flash('You must reach level 5 to choose a class!', 'warning')
        return redirect(url_for('dashboard'))
    
    available_classes = GamificationController.get_all_classes()
    
    return render_template('classes.html',
                         progress=progress,
                         classes=available_classes)

@app.route('/choose_class/<class_name>', methods=['POST'])
@login_required
def choose_class(class_name):
    """Choose a specialized class"""
    client_id = session['client_id']
    
    result = gamification.unlock_class(client_id, class_name)
    
    if result['success']:
        flash(f'Class {class_name} unlocked! 🎉 {result["class_info"]["bonus"]}', 'success')
    else:
        flash(result['message'], 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/schedule')
@login_required
def schedule():
    """Weekly schedule page"""
    client_id = session['client_id']
    client = Client.get_by_id(client_id)
    
    # Get weekly schedule
    weekly_schedule = client.get_weekly_schedule()
    
    # Get availability
    availability = client.get_availability()
    
    all_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    session_ctrl = WorkoutSessionController()
    today = date.today().strftime('%Y-%m-%d')

    for day, routine_info in weekly_schedule.items():
        routine_id = routine_info['routine_id']
        session_data = session_ctrl._get_session(client_id, routine_id, today)
        if session_data:
            routine_info['status'] = session_data['status']
        else:
            routine_info['status'] = 'not_started'

    return render_template(
        'schedule.html',
        schedule=weekly_schedule,  # renamed variable
        all_days=all_days,
        availability=availability
    )
    

@app.route('/finish_workout', methods=['POST'])
@login_required
def finish_workout():
    """Finish the current workout session"""
    workout_session_id = session.get('workout_session_id')
    
    if not workout_session_id:
        return jsonify({'success': False, 'message': 'No active workout session'}), 400
    
    # Mark session as completed
    session_ctrl.complete_session(workout_session_id)
    
    # Clear session
    session.pop('workout_session_id', None)
    
    return jsonify({
        'success': True,
        'message': 'Workout completed! Great job! 🎉'
    })


@app.route('/profile')
@login_required
def profile():
    """Client profile page"""
    client_id = session['client_id']
    client = Client.get_by_id(client_id)
    
    # Get physical data
    physical_data = client.get_latest_physical_data()
    
    # Get gamification data
    gam_data = client.get_gamification_data()

    #calculated physical data
    physical_data_calculated = {}
    if physical_data:
        physical_data_calculated['bmi_value'] = round((physical_data['weight_kg'] / ((physical_data['height_cm'] / 100) ** 2)), 2)
        physical_data_calculated['mhr_value'] = int(208 - (0.7 * client.age))
        if client.gender == 'Male':
            physical_data_calculated['bmr_value'] = int((10 * physical_data['weight_kg']) + (6.25 * physical_data['height_cm']) - (5 * client.age) + 5)
        else:
            physical_data_calculated['bmr_value'] = int((10 * physical_data['weight_kg']) + (6.25 * physical_data['height_cm']) - (5 * client.age) - 161)
        if physical_data['activity'] == "Extreme":
            physical_data_calculated['tdee_value'] = int(physical_data_calculated['bmr_value'] * 1.9)
        elif physical_data['activity'] == "A lot":
            physical_data_calculated['tdee_value'] = int(physical_data_calculated['bmr_value'] * 1.72)
        elif physical_data['activity'] == "Some":
            physical_data_calculated['tdee_value'] = int(physical_data_calculated['bmr_value'] * 1.55)
        elif physical_data['activity'] == "A little":
            physical_data_calculated['tdee_value'] = int(physical_data_calculated['bmr_value'] * 1.37)
        else:
            physical_data_calculated['tdee_value'] = int(physical_data_calculated['bmr_value'] * 1.2)

    # --- Membership notification ---
    mc = MembershipController()
    membership = mc.get_client_membership(client_id)
    if membership:
        start_date = datetime.strptime(membership['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(membership['end_date'], '%Y-%m-%d').date()
        days_left = (end_date - date.today()).days
        
    
    return render_template('profile.html',
                         client=client,
                         physical_data=physical_data,
                         physical_data_calculated = physical_data_calculated,
                         gam_data=gam_data,
                         membership=membership,
                         start_date=start_date,
                         end_date=end_date,
                         days_left=days_left)

@app.route('/get_swap_options')
@login_required
def get_swap_options():
    """Return exercise alternatives for the swap modal in workout.html"""
    exercise_id    = request.args.get('exercise_id', type=int)
    primary_muscle = request.args.get('primary_muscle', '')   # param name kept for JS compatibility
    exercise_type  = request.args.get('exercise_type', '')

    db = DatabaseManager()
    query = """
        SELECT exercise_id, name, primary_muscle, complementary_muscle,
               exercise_type, difficulty_level, base_exp
        FROM   exercises
        WHERE  primary_muscle = ?
          AND  exercise_type  = ?
          AND  exercise_id   != ?
        ORDER  BY name
    """
    rows = db.execute_query(query, (primary_muscle, exercise_type, exercise_id))

    # If exact primary_muscle match gives nothing, broaden to same type only
    if not rows:
        query_broad = """
            SELECT exercise_id, name, primary_muscle, complementary_muscle,
                   exercise_type, difficulty_level, base_exp
            FROM   exercises
            WHERE  exercise_type = ?
              AND  exercise_id  != ?
            ORDER  BY name
            LIMIT  8
        """
        rows = db.execute_query(query_broad, (exercise_type, exercise_id))

    return jsonify({
        'options': [dict(r) for r in rows]
    })

@app.route('/api/get_similar_exercises')
def api_similar_exercises():
    muscle     = request.args.get('muscle', '')
    ex_type    = request.args.get('type', '')
    exclude    = request.args.get('exclude', type=int)

    db = DatabaseManager()
    query = """
        SELECT * FROM exercises
        WHERE  primary_muscle = ?
          AND  exercise_type  = ?
          AND  exercise_id   != ?
        ORDER  BY name
    """
    rows = db.execute_query(query, (muscle, ex_type, exclude))
    return jsonify([dict(r) for r in rows])

@app.route("/api/swap_exercise", methods=["POST"])
@login_required
def api_swap_exercise():
    data = request.get_json()
    old_id = int(data["old_id"])
    new_id = int(data["new_id"])

    session_id = session.get("workout_session_id")
    if not session_id:
        return jsonify({"success": False, "error": "No active workout session"}), 400

    session_info = session_ctrl.get_session_by_id(session_id)
    if not session_info:
        return jsonify({"success": False, "error": "Workout session not found"}), 400

    routine_id = session_info["routine_id"]

    # ✅ Save swap ONLY for this session — routine_exercises is NOT touched
    session_ctrl.save_session_swap(session_id, old_id, new_id)

    # Reload exercises with session swaps applied
    routine = Routine.get_by_id(routine_id)
    exercises = apply_session_swaps(routine.get_exercises(), session_ctrl.get_session_swaps(session_id))

    old_index = next((i for i, ex in enumerate(exercises) if ex["exercise_id"] == new_id), None)
    if old_index is None:
        return jsonify({"success": False, "error": "Swapped exercise not found"}), 400

    progress = session_ctrl.get_session_progress(session_id, routine, exercises)

    html = render_template(
        "partials/exercise_card.html",
        exercise=exercises[old_index],
        index=old_index + 1,
        progress=progress,
        session_info=session_info
    )

    return jsonify({"success": True, "html": html})

# ==================== ADMIN ROUTES ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple admin authentication (in production, use proper auth)
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Welcome, Admin! 👋', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.clear()
    flash('Admin logged out successfully', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard — Phase 2 enriched"""
    from datetime import date
    from controllers.leaderboard_controller import LeaderboardController
    from controllers.membership_controller import MembershipController

    db = DatabaseManager()

    # Basic counts
    all_clients      = Client.get_all_active()
    total_clients    = len(all_clients)
    attendance_list  = attendance_ctrl.get_gym_attendance_today()
    todays_attendance = len(attendance_list)

    weekly_report    = attendance_ctrl.get_weekly_attendance_report()
    weekly_visits    = weekly_report['total_visits']

    # Currently inside the gym (checked in but not checked out)
    currently_in = sum(1 for r in attendance_list if not r.get('check_out_time'))

    # Memberships expiring within 7 days
    mc = MembershipController()
    all_memberships  = mc.get_all_memberships()
    today            = date.today()
    expiring_soon = sum(
        1 for m in all_memberships
        if m.get('status') == 'active' and m.get('end_date')
        and 0 < (
            __import__('datetime').datetime.strptime(m['end_date'], '%Y-%m-%d').date() - today
        ).days <= 7
    )

    # Top EXP this week (reuse leaderboard controller)
    try:
        lb = LeaderboardController()
        top_exp_week = lb.get_top_exp()   # returns top 10 all-time; use as weekly proxy
    except Exception:
        top_exp_week = []

    return render_template(
        'admin/dashboard.html',
        total_clients    = total_clients,
        todays_attendance= todays_attendance,
        weekly_visits    = weekly_visits,
        attendance_list  = attendance_list,
        currently_in     = currently_in,
        expiring_soon    = expiring_soon,
        top_exp_week     = top_exp_week,
        gym_capacity     = 50,                # adjust as needed
        today_date       = today.strftime('%b %d, %Y'),
    )

@app.route('/admin/clients')
@admin_required
def admin_clients():
    """Client list — Phase 2: adds XP %, class, membership status"""
    from datetime import date
    from controllers.membership_controller import MembershipController

    mc      = MembershipController()
    clients = Client.get_all_active()

    for client in clients:
        # Gamification
        gam = client.get_gamification_data()
        client.level        = gam['current_level']   if gam else 1
        client.rank         = gam['rank']             if gam else 'E'
        client.current_exp  = gam['current_exp']      if gam else 0
        client.client_class = gam.get('class')        if gam else None

        # XP percentage toward next level
        if gam:
            next_exp = gam.get('next_level_exp', 1) or 1
            client.xp_pct = round((gam['current_exp'] / next_exp) * 100, 1)
        else:
            client.xp_pct = 0

        # Membership status label
        membership = mc.get_client_membership(client.client_id)
        if not membership:
            client.mem_status   = 'none'
            client.mem_days_left = 0
        else:
            end   = __import__('datetime').datetime.strptime(membership['end_date'], '%Y-%m-%d').date()
            days  = (end - date.today()).days
            client.mem_days_left = max(days, 0)
            if days <= 0:
                client.mem_status = 'expired'
            elif days <= 7:
                client.mem_status = 'expiring'
            else:
                client.mem_status = 'active'

    return render_template('admin/clients.html', clients=clients)

@app.route('/admin/client/<int:client_id>')
@admin_required
def admin_client_details(client_id):
    """Client profile — Phase 2: full tabs data"""
    from datetime import date
    from controllers.membership_controller import MembershipController
    from controllers.workout_logger import WorkoutLogger

    client = Client.get_by_id(client_id)
    if not client:
        flash('Client not found', 'danger')
        return redirect(url_for('admin_clients'))

    # ── Physical data ──
    physical_data = client.get_latest_physical_data()
    physical_data_calculated = {}
    if physical_data:
        physical_data_calculated['bmi_value'] = round(
            physical_data['weight_kg'] / ((physical_data['height_cm'] / 100) ** 2), 2
        )
        physical_data_calculated['mhr_value'] = int(208 - 0.7 * client.age) if client.age else None
        if client.gender == 'Male':
            physical_data_calculated['bmr_value'] = int(
                10 * physical_data['weight_kg']
                + 6.25 * physical_data['height_cm']
                - 5 * (client.age or 0) + 5
            )
        else:
            physical_data_calculated['bmr_value'] = int(
                10 * physical_data['weight_kg']
                + 6.25 * physical_data['height_cm']
                - 5 * (client.age or 0) - 161
            )
        activity_map = {
            'Extreme': 1.9, 'A lot': 1.72, 'Some': 1.55, 'A little': 1.37
        }
        mult = activity_map.get(physical_data.get('activity', ''), 1.2)
        physical_data_calculated['tdee_value'] = int(physical_data_calculated['bmr_value'] * mult)

    # ── Availability & schedule ──
    availability    = client.get_availability()
    weekly_schedule = client.get_weekly_schedule()

    # ── Gamification / progress ──
    gam  = client.get_gamification_data()
    progress = {
        'current_level'  : gam['current_level']   if gam else 1,
        'rank'           : gam['rank']             if gam else 'E',
        'class'          : gam.get('class')        if gam else None,
        'current_exp'    : gam['current_exp']      if gam else 0,
        'total_exp'      : gam['total_exp']        if gam else 0,
        'next_level_exp' : gam.get('next_level_exp', 100) if gam else 100,
        'streak'         : gam.get('streak', 0)   if gam else 0,
        'streak_multiplier': gam.get('streak_multiplier', 1.0) if gam else 1.0,
    }
    # XP percentage
    nxt = progress['next_level_exp'] or 1
    progress['xp_percentage'] = round((progress['current_exp'] / nxt) * 100, 1)

    # ── Attendance stats ──
    attendance_stats = {}
    try:
        attendance_stats = attendance_ctrl.get_attendance_stats(client_id) or {}
    except Exception as e:
        print(f'Attendance stats error: {e}')

    # ── Workout history & stats ──
    workout_logger = WorkoutLogger()
    workout_history = []
    workout_stats   = {}
    try:
        workout_history = workout_logger.get_workout_history(client_id, limit=15)
        workout_stats   = workout_logger.get_workout_stats(client_id) or {}
    except Exception as e:
        print(f'Workout data error: {e}')

    # ── Membership ──
    mc = MembershipController()
    membership = mc.get_client_membership(client_id)
    if membership:
        end_date = __import__('datetime').datetime.strptime(membership['end_date'], '%Y-%m-%d').date()
        membership = dict(membership)
        membership['days_left'] = (end_date - date.today()).days

    return render_template(
        'admin/client_details.html',
        client                  = client,
        physical_data           = physical_data,
        physical_data_calculated= physical_data_calculated,
        availability            = availability,
        weekly_schedule         = weekly_schedule,
        progress                = progress,
        attendance_stats        = attendance_stats,
        workout_history         = workout_history,
        workout_stats           = workout_stats,
        membership              = membership,
    )

@app.route('/admin/client/add', methods=['GET', 'POST'])
@admin_required
def admin_add_client():
    db = DatabaseManager()

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        dob = request.form.get('dob')
        gender = request.form.get('gender')
        pin = request.form.get('pin')

        # Create and save new client
        client = Client(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            email=email,
            date_of_birth=dob,
            gender=gender
        )
        client_id = client.save(pin)
        client.client_id = client_id

        # 🧠 Optional physical data
        height = request.form.get('height')
        weight = request.form.get('weight')
        bodyfat = request.form.get('bodyfat')
        if any([height, weight, bodyfat]):
            client.add_or_update_physical_data(height, weight, bodyfat)

        # 🗓️ Availability
        selected_days = request.form.getlist('days')
        client.set_availability(selected_days)

        # 🏋️ Assign routines to days
        for day in selected_days:
            routine_id = request.form.get(f"routine_{day.lower()}")
            if routine_id:
                client.assign_routine_to_day(day, routine_id)

        flash("✅ Client created successfully!", "success")
        return redirect(url_for('admin_clients'))

    # GET → render blank form
    all_routines = db.execute_query("SELECT routine_id, routine_name FROM routines WHERE is_active=1")

    return render_template(
        'admin/client_form.html',
        client=None,
        physical_data=None,
        availability=[],
        weekly_schedule={},
        all_routines=all_routines
    )

@app.route('/admin/client/<int:client_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_client(client_id):
    db = DatabaseManager()
    client = Client.get_by_id(client_id)

    if not client:
        flash("Client not found", "danger")
        return redirect(url_for('admin_clients'))

    # Load related info for GET
    physical_data = client.get_latest_physical_data()
    availability = client.get_availability()
    weekly_schedule = client.get_weekly_schedule()
    all_routines = db.execute_query("SELECT routine_id, routine_name FROM routines WHERE is_active=1")
    physical_data_calculated = {}

    # --- POST: Save updates ---
    if request.method == 'POST':
        client.first_name = request.form.get('first_name')
        client.last_name = request.form.get('last_name')
        client.phone_number = request.form.get('phone')
        client.email = request.form.get('email')
        client.date_of_birth = request.form.get('dob')
        client.gender = request.form.get('gender')
        client.update()

        # 🧠 Update physical data
        height = request.form.get('height')
        weight = request.form.get('weight')
        bodyfat = request.form.get('bodyfat')
        activity = request.form.get('activity')
        chest = request.form.get('chest')
        arms = request.form.get('arms')
        forearms = request.form.get('forearms')
        waist = request.form.get('waist')
        hips = request.form.get('hips')
        thighs = request.form.get('thighs')
        claf = request.form.get('claf')
        if any([height, weight, bodyfat, activity, chest, arms, forearms, waist, hips, thighs, claf]):
            client.add_or_update_physical_data(height, weight, bodyfat, activity, chest, arms, forearms, waist, hips, thighs, claf)

        # 🗓️ Update availability
        selected_days = request.form.getlist('days')
        client.set_availability(selected_days)
        client.clear_unassigned_days(selected_days)

        # 🏋️ Assign routines per selected day
        for day in selected_days:
            routine_id = request.form.get(f"routine_{day.lower()}")
            if routine_id:
                client.assign_routine_to_day(day, routine_id)

        flash("✅ Client information updated successfully!", "success")
        return redirect(url_for('admin_client_details', client_id=client.client_id))

    # --- GET: Render form ---
    return render_template(
        'admin/client_form.html',
        client=client,
        physical_data=physical_data,
        physical_data_calculated=physical_data_calculated,
        availability=availability,
        weekly_schedule=weekly_schedule,
        all_routines=all_routines
    )

@app.route('/admin/client/<int:client_id>/delete', methods=['POST'])
@admin_required
def admin_delete_client(client_id):
    """Delete client"""
    client = Client.get_by_id(client_id)
    if client:
        client.delete()
        flash('Client deleted successfully', 'success')
    return redirect(url_for('admin_clients'))

@app.route('/admin/exercises')
@admin_required
def admin_exercises():
    """Exercise management"""
    exercises = Exercise.get_all()
    return render_template('admin/exercises.html', exercises=exercises)

@app.route('/admin/client/<int:client_id>/clear_routines')
def admin_clear_routines(client_id):
    db = DatabaseManager()
    db.execute_update("DELETE FROM routine_assignments WHERE client_id=?", (client_id,))
    flash("✅ Cleared all assigned routines for this client", "info")
    return redirect(url_for('admin_edit_client', client_id=client_id))

@app.route('/admin/exercise/add', methods=['GET', 'POST'])
@admin_required
def admin_add_exercise():
    """Add new exercise"""
    if request.method == 'POST':
        try:
            exercise = Exercise(
                name                 = request.form.get('name'),
                description          = request.form.get('description'),
                exercise_type        = request.form.get('type'),
                primary_muscle       = request.form.get('primary_muscle'),
                complementary_muscle = request.form.get('complementary_muscle') or None,
                difficulty_level     = request.form.get('difficulty'),
                base_exp             = int(request.form.get('exp', 10))
            )
            exercise.save()
            flash('Exercise created successfully!', 'success')
        except Exception as e:
            flash(f'Error adding exercise: {e}', 'error')
    return redirect(url_for('admin_exercises'))

@app.route('/admin/exercise/<int:exercise_id>/edit', methods=['POST'])
@admin_required
def admin_edit_exercise(exercise_id):
    """Save edits to an existing exercise (POST from inline modal)"""
    exercise = Exercise.get_by_id(exercise_id)
    if not exercise:
        flash('Exercise not found.', 'error')
        return redirect(url_for('admin_exercises'))

    exercise.name                 = request.form.get('name')
    exercise.description          = request.form.get('description')
    exercise.exercise_type        = request.form.get('type')
    exercise.primary_muscle       = request.form.get('primary_muscle')
    exercise.complementary_muscle = request.form.get('complementary_muscle') or None
    exercise.difficulty_level     = request.form.get('difficulty')
    exercise.base_exp             = int(request.form.get('exp', 10))

    exercise.update()
    flash(f'"{exercise.name}" updated successfully!', 'success')
    return redirect(url_for('admin_exercises'))

@app.route('/admin/exercise/<int:exercise_id>/delete', methods=['POST'])
@admin_required
def admin_delete_exercise(exercise_id):
    """Delete exercise"""
    exercise = Exercise.get_by_id(exercise_id)
    if exercise:
        exercise.delete()
        flash('Exercise deleted.', 'success')
    return redirect(url_for('admin_exercises'))

@app.route('/admin/routine_exercise/delete/<int:routine_exercise_id>', methods=['POST'])
@admin_required
def delete_routine_exercise(routine_exercise_id):
    result = Routine().delete_routine_exercise(routine_exercise_id)
    flash(result.get('message', 'Exercise removed.'), 'info')
    return redirect(request.referrer or url_for('admin_routines'))


@app.route('/admin/routines')
@admin_required
def admin_routines():
    """Routine list — enriched with exercise count and total EXP per card"""
    routines = Routine.get_all_active()

    for r in routines:
        exercises = r.get_exercises()
        r.exercise_count = len(exercises)
        r.total_exp      = sum(ex['base_exp'] * ex['sets'] for ex in exercises)

    return render_template('admin/routines.html', routines=routines)

@app.route('/admin/routine/<int:routine_id>')
@admin_required
def admin_routine_details(routine_id):
    """Visual routine builder"""
    routine = Routine.get_by_id(routine_id)
    if not routine:
        flash('Routine not found', 'error')
        return redirect(url_for('admin_routines'))

    exercises  = routine.get_exercises()
    total_exp  = sum(ex['base_exp'] * ex['sets'] for ex in exercises)
    added_ids  = {ex['exercise_id'] for ex in exercises}
    all_exercises = Exercise.get_all()

    return render_template(
        'admin/routine_details.html',
        routine       = routine,
        exercises     = exercises,
        total_exp     = total_exp,
        added_ids     = added_ids,
        all_exercises = all_exercises,
    )

@app.route('/admin/routine/add', methods=['GET', 'POST'])
@admin_required
def admin_add_routine():
    if request.method == 'POST':
        try:
            routine = Routine(
                routine_name = request.form.get('name'),
                description  = request.form.get('description'),
                created_by   = 'Admin',
            )
            routine.save()
            flash(f'"{routine.routine_name}" created! Now add exercises.', 'success')
            return redirect(url_for('admin_routine_details', routine_id=routine.routine_id))
        except Exception as e:
            flash(f'Error creating routine: {e}', 'error')

    return render_template('admin/routine_form.html')

@app.route('/admin/routine/<int:routine_id>/add_exercise', methods=['POST'])
@admin_required
def admin_add_exercise_to_routine(routine_id):
    routine = Routine.get_by_id(routine_id)
    if not routine:
        flash('Routine not found', 'error')
        return redirect(url_for('admin_routines'))

    try:
        exercise_id = int(request.form.get('exercise_id'))
        sets        = int(request.form.get('sets',  3))
        reps        = int(request.form.get('reps',  10))
        rest        = int(request.form.get('rest',  60))
        measurement = request.form.get('measurement', 'reps')

        routine.add_exercise(exercise_id, sets=sets, reps=reps,
                             rest_seconds=rest, measurement=measurement)

        ex = Exercise.get_by_id(exercise_id)
        flash(f'"{ex.name if ex else "Exercise"}" added to routine!', 'success')
    except Exception as e:
        flash(f'Error adding exercise: {e}', 'error')

    return redirect(url_for('admin_routine_details', routine_id=routine_id))

@app.route('/admin/routine_exercise/update', methods=['POST'])
@admin_required
def update_routine_exercise():
    routine_exercise_id = request.form.get('routine_exercise_id')
    sets        = request.form.get('sets')
    reps        = request.form.get('reps')
    rest_seconds= request.form.get('rest_seconds')
    measurement = request.form.get('measurement')

    result = Routine().update_exercise(
        routine_exercise_id = routine_exercise_id,
        sets        = sets,
        reps        = reps,
        rest_seconds= rest_seconds,
        measurement = measurement,
    )
    flash(result['message'], 'success')
    return redirect(request.referrer or url_for('admin_routines'))

@app.route('/admin/routine/<int:routine_id>/move_exercise/<int:routine_exercise_id>/<direction>',
           methods=['POST'])
@admin_required
def admin_move_exercise(routine_id, routine_exercise_id, direction):
    """
    Swap order_position of two adjacent exercises in a routine.
    direction: 'up' | 'down'
    """
    from database.db_manager import DatabaseManager
    db = DatabaseManager()

    # Fetch all exercises in this routine ordered by position
    rows = db.execute_query(
        '''SELECT routine_exercise_id, order_position
           FROM routine_exercises
           WHERE routine_id = ?
           ORDER BY order_position ASC''',
        (routine_id,)
    )

    if not rows:
        flash('No exercises found.', 'error')
        return redirect(url_for('admin_routine_details', routine_id=routine_id))

    # Find index of the target exercise
    ids  = [r['routine_exercise_id'] for r in rows]
    poss = [r['order_position']      for r in rows]

    try:
        idx = ids.index(routine_exercise_id)
    except ValueError:
        flash('Exercise not found in this routine.', 'error')
        return redirect(url_for('admin_routine_details', routine_id=routine_id))

    # Determine swap partner
    if direction == 'up' and idx > 0:
        swap_idx = idx - 1
    elif direction == 'down' and idx < len(ids) - 1:
        swap_idx = idx + 1
    else:
        # Already at boundary — nothing to do
        return redirect(url_for('admin_routine_details', routine_id=routine_id))

    id_a, pos_a = ids[idx],      poss[idx]
    id_b, pos_b = ids[swap_idx], poss[swap_idx]

    # Swap positions
    db.execute_update(
        'UPDATE routine_exercises SET order_position = ? WHERE routine_exercise_id = ?',
        (pos_b, id_a)
    )
    db.execute_update(
        'UPDATE routine_exercises SET order_position = ? WHERE routine_exercise_id = ?',
        (pos_a, id_b)
    )

    return redirect(url_for('admin_routine_details', routine_id=routine_id))

@app.route('/admin/routine/<int:routine_id>/delete', methods=['POST'])
@admin_required
def admin_delete_routine(routine_id):
    routine = Routine.get_by_id(routine_id)
    if routine:
        routine.delete()
        flash(f'"{routine.routine_name}" deleted.', 'success')
    return redirect(url_for('admin_routines'))

@app.route('/admin/attendance')
@admin_required
def admin_attendance():
    """Attendance management — Phase 3 + duration bug fix"""
    from datetime import date, datetime, timedelta

    attendance_list = attendance_ctrl.get_gym_attendance_today()

    for record in attendance_list:
        ci_str = record.get('check_in_time')
        co_str = record.get('check_out_time')
        record['duration_minutes'] = None

        if ci_str and co_str:
            try:
                fmt = '%H:%M:%S'
                ci = datetime.strptime(ci_str, fmt)
                co = datetime.strptime(co_str, fmt)

                delta = (co - ci).total_seconds()

                # If negative, checkout crossed midnight — add 24 h
                if delta < 0:
                    delta += 86400  # 24 * 60 * 60

                minutes = int(delta / 60)

                # Sanity cap: ignore anything over 24 h (bad data)
                record['duration_minutes'] = minutes if minutes <= 1440 else None

            except Exception:
                record['duration_minutes'] = None

    # KPIs
    currently_in = sum(1 for r in attendance_list if not r.get('check_out_time'))

    durations    = [r['duration_minutes'] for r in attendance_list
                    if r.get('duration_minutes') is not None]
    avg_duration = round(sum(durations) / len(durations)) if durations else 0

    return render_template(
        'admin/attendance.html',
        attendance_list = attendance_list,
        clients         = Client.get_all_active(),
        currently_in    = currently_in,
        avg_duration    = avg_duration,
        today_date      = date.today().strftime('%A, %B %d %Y'),
    )

@app.route('/get_client_by_phone', methods=['POST'])
@admin_required
def get_client_by_phone():
    """Phone lookup — now also returns membership status for the warning banner"""
    from controllers.membership_controller import MembershipController

    phone_number = request.json.get('phone_number')
    client = Client.get_by_phone(phone_number)

    if not client:
        return jsonify({'success': False})

    # Membership check
    mc = MembershipController()
    membership = mc.get_client_membership(client.client_id)
    mem_status    = None
    mem_days_left = 0

    if membership:
        end_date  = datetime.strptime(membership['end_date'], '%Y-%m-%d').date()
        days_left = (end_date - date.today()).days
        mem_days_left = max(days_left, 0)
        if days_left <= 0:
            mem_status = 'expired'
        elif days_left <= 7:
            mem_status = 'expiring'
        else:
            mem_status = 'active'

    return jsonify({
        'success'              : True,
        'client_name'          : f"{client.first_name} {client.last_name}",
        'client_status'        : client.status,
        'client_id'            : client.client_id,
        'membership_status'    : mem_status,
        'membership_days_left' : mem_days_left,
    })

@app.route('/admin/checkin', methods=['POST'])
@admin_required
def admin_checkin():
    client_id = int(request.form.get('client_id'))
    result = attendance_ctrl.check_in(client_id)

    db = DatabaseManager()
    db.update_streak(client_id)

    if result['success']:
        client = Client.get_by_id(client_id)
        flash(f'{client.first_name if client else "Client"} checked in! 💪', 'success')
    else:
        flash(result['message'], 'warning')

    return redirect(url_for('admin_attendance'))

@app.route('/admin/checkout', methods=['POST'])
@admin_required
def admin_checkout():
    client_id = int(request.form.get('client_id'))
    result = attendance_ctrl.check_out(client_id)

    if result['success']:
        flash(f'Checked out! Duration: {result["duration_minutes"]} min', 'success')
    else:
        flash(result['message'], 'warning')

    return redirect(url_for('admin_attendance'))

@app.route('/admin/tests')
@admin_required
def admin_tests():
    """Physical tests management"""
    clients = Client.get_all_active()
    return render_template('admin/tests.html', clients=clients)

@app.route('/admin/test/submit', methods=['POST'])
@admin_required
def admin_submit_test():
    """Submit physical test results"""
    try:
        client_id = int(request.form.get('client_id'))
        
        test_scores = {
            'Push-ups': int(request.form.get('pushups')),
            'Squats': int(request.form.get('squats')),
            'Sit-ups': int(request.form.get('situps')),
            'High Jump': float(request.form.get('jump')),
            'Sprint': float(request.form.get('sprint'))
        }
        
        result = test_ctrl.complete_full_assessment(client_id, test_scores)
        
        if result['success']:
            flash(f'Assessment complete! Overall Rank: {result["overall_rank"]} | Total EXP: {result["total_exp_earned"]}', 'success')
        else:
            flash('Error submitting test results', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_tests'))

@app.route('/admin/assign_routine', methods=['POST'])
@admin_required
def admin_assign_routine():
    """Assign routine to client"""
    try:
        client_id = int(request.form.get('client_id'))
        routine_id = int(request.form.get('routine_id'))
        day = request.form.get('day')
        
        routine = Routine.get_by_id(routine_id)
        if routine:
            routine.assign_to_client(client_id, day)
            flash(f'Routine assigned to {day}!', 'success')
        else:
            flash('Routine not found', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/leaderboard')
def admin_leaderboard():
    from controllers.leaderboard_controller import LeaderboardController
    leaderboard = LeaderboardController()

    top_exp = leaderboard.get_top_exp()
    top_reps = leaderboard.get_top_reps()
    top_streaks = leaderboard.get_top_streaks()
    
    print("Top EXP",top_exp)
    print("Top Streaks",top_streaks)

    return render_template(
        'admin/leaderboard.html',
        top_exp=top_exp,
        top_reps=top_reps,
        top_streaks=top_streaks
    )

@app.route('/admin/memberships')
@admin_required
def admin_memberships():
    """Membership management — Phase 3 with counts and all_clients"""
    from controllers.membership_controller import MembershipController

    mc = MembershipController()
    memberships = mc.get_all_memberships()

    # Compute counts for KPI strip
    counts = {'active': 0, 'expiring': 0, 'expired': 0, 'total': len(memberships)}
    for m in memberships:
        days = m.get('days_remaining', 0) or 0
        if m['status'] == 'expired' or days <= 0:
            counts['expired'] += 1
        elif days <= 7:
            counts['expiring'] += 1
        else:
            counts['active'] += 1

    all_clients = Client.get_all_active()

    return render_template(
        'admin/memberships.html',
        memberships  = memberships,
        counts       = counts,
        all_clients  = all_clients,
    )

@app.route('/admin/membership/renew', methods=['POST'])
@admin_required
def renew_membership():
    from controllers.membership_controller import MembershipController
    mc = MembershipController()
    membership_id = request.form.get('membership_id')
    duration_days = int(request.form.get('duration_days', 30))
    result = mc.renew_membership(membership_id, duration_days)
    flash(result.get('message', 'Membership renewed.'), 'success')
    return redirect(url_for('admin_memberships'))

@app.route('/admin/membership/reactivate', methods=['POST'])
@admin_required
def reactivate_membership():
    from controllers.membership_controller import MembershipController
    mc = MembershipController()
    membership_id = request.form.get('membership_id')
    mc.update_membership_status(membership_id, 'active')
    flash('Membership reactivated.', 'success')
    return redirect(url_for('admin_memberships'))

@app.route('/admin/membership/create', methods=['POST'])
@admin_required
def admin_create_membership():
    """Create a brand-new membership from the modal form"""
    from controllers.membership_controller import MembershipController
    mc = MembershipController()
    client_id     = int(request.form.get('client_id'))
    duration_days = int(request.form.get('duration_days', 30))
    notes         = request.form.get('notes', '')

    result = mc.add_membership(client_id, duration_days, notes or None)
    flash(result.get('message', 'Membership created.'), 'success')
    return redirect(url_for('admin_memberships'))

@app.route('/admin/membership/bulk-renew', methods=['POST'])
@admin_required
def admin_bulk_renew_memberships():
    """Bulk renew multiple memberships at once"""
    from controllers.membership_controller import MembershipController
    mc = MembershipController()

    raw_ids       = request.form.get('membership_ids', '')
    duration_days = int(request.form.get('duration_days', 30))
    ids           = [i.strip() for i in raw_ids.split(',') if i.strip()]

    renewed = 0
    for mid in ids:
        result = mc.renew_membership(mid, duration_days)
        if result.get('success'):
            renewed += 1

    flash(f'{renewed} membership(s) renewed successfully!', 'success')
    return redirect(url_for('admin_memberships'))

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return "<h1>404 - Page Not Found</h1>", 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        '/image/favicon.ico',
        mimetype='image/x-icon'
    )

@app.route('/admin/salespoint')
@admin_required
def admin_salespoint():
    items = sales_ctrl.get_all_items()
    sales_today = sales_ctrl.get_sales_today()
    return render_template('admin/salespoint.html', items=items, sales_today=sales_today)

@app.route('/admin/salespoint/items', methods=['GET'])
@admin_required
def salespoint_items():
    items = sales_ctrl.get_all_items()
    # convertir price en float para JS (opcional)
    for it in items:
        it['price'] = it['price_cents'] / 100.0
    return jsonify({"success": True, "items": items})

@app.route('/admin/salespoint/add_item', methods=['POST'])
@admin_required
def salespoint_add_item():
    data = request.json or request.form
    sku = data.get('sku')
    name = data.get('name')
    price = float(data.get('price', 0))
    stock = int(data.get('stock', 0))
    description = data.get('description')
    price_cents = int(round(price * 100))
    sales_ctrl.add_item(sku, name, price_cents, stock, description)
    return jsonify({"success": True})

@app.route('/admin/salespoint/create_sale', methods=['POST'])
@admin_required
def salespoint_create_sale():
    data         = request.get_json()
    cashier_id   = 151
    payment_type = data.get('payment_type', 'cash')
    paid_amount  = float(data.get('paid_amount', 0.0))
    paid_cents   = int(round(paid_amount * 100))

    cart_items = [
        {
            'item_id':    int(it['item_id']),
            'qty':        int(it['qty']),
            'price_cents': int(round(float(it.get('price', 0)) * 100))
        }
        for it in data.get('cart', [])
    ]

    result = sales_ctrl.create_sale(cashier_id, cart_items, payment_type, paid_cents)
    return jsonify(result)

@app.route('/admin/salespoint/sales_today', methods=['GET'])
@admin_required
def salespoint_sales_today():
    sales = sales_ctrl.get_sales_today()
    return jsonify({"success": True, "sales": sales})

# (Opcional) endpoint para detalle de venta
@app.route('/admin/salespoint/sale/<int:sale_id>', methods=['GET'])
@admin_required
def salespoint_sale_detail(sale_id):
    detail = sales_ctrl.get_sale_detail(sale_id)
    return jsonify({"success": True, "items": detail})

@app.route("/admin/salespoint/report/<period>")
@admin_required
def admin_sales_report(period):
    """View sales report (daily, weekly, monthly)"""
    report = sales_ctrl.get_sales_report(period)
    return render_template("admin/sales_report.html", report=report)


@app.route("/admin/salespoint/export/<period>")
@admin_required
def admin_export_sales_report(period):
    """Download sales report as CSV"""
    output_path = sales_ctrl.export_sales_report_csv(period)
    return send_file(output_path, as_attachment=True)

# Utility function to get local IP
def get_local_ip():
    """Get local IP address"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def _get_announcements():
    """Helper — fetch active (non-expired) announcements, pinned first."""
    from database.db_manager import DatabaseManager
    from datetime import date
    db = DatabaseManager()
    rows = db.execute_query("""
        SELECT ann_id, title, body, ann_type, is_pinned, expires_at, created_at
        FROM   announcements
        WHERE  (expires_at IS NULL OR expires_at >= ?)
        ORDER  BY is_pinned DESC, ann_id DESC
    """, (date.today().isoformat(),))
    return [dict(r) for r in rows]


@app.route('/admin/announcements')
@admin_required
def admin_announcements():
    from datetime import date
    return render_template(
        'admin/announcements.html',
        announcements = _get_announcements(),
        today         = date.today().isoformat(),
    )


@app.route('/admin/announcements/create', methods=['POST'])
@admin_required
def admin_create_announcement():
    from database.db_manager import DatabaseManager
    db         = DatabaseManager()
    title      = request.form.get('title', '').strip()
    body       = request.form.get('body', '').strip()
    ann_type   = request.form.get('ann_type', 'info')
    is_pinned  = 1 if request.form.get('is_pinned') else 0
    expires_at = request.form.get('expires_at') or None

    if not title or not body:
        flash('Title and message are required.', 'error')
        return redirect(url_for('admin_announcements'))

    db.execute_update("""
        INSERT INTO announcements (title, body, ann_type, is_pinned, expires_at)
        VALUES (?, ?, ?, ?, ?)
    """, (title, body, ann_type, is_pinned, expires_at))

    flash(f'Announcement "{title}" published!', 'success')
    return redirect(url_for('admin_announcements'))


@app.route('/admin/announcements/<int:ann_id>/toggle_pin', methods=['POST'])
@admin_required
def admin_toggle_pin_announcement(ann_id):
    from database.db_manager import DatabaseManager
    db = DatabaseManager()
    db.execute_update("""
        UPDATE announcements SET is_pinned = CASE WHEN is_pinned=1 THEN 0 ELSE 1 END
        WHERE ann_id = ?
    """, (ann_id,))
    return redirect(url_for('admin_announcements'))


@app.route('/admin/announcements/<int:ann_id>/delete', methods=['POST'])
@admin_required
def admin_delete_announcement(ann_id):
    from database.db_manager import DatabaseManager
    db = DatabaseManager()
    db.execute_update("DELETE FROM announcements WHERE ann_id = ?", (ann_id,))
    flash('Announcement deleted.', 'info')
    return redirect(url_for('admin_announcements'))


@app.route('/api/announcements')
@login_required
def api_announcements():
    """Return active announcements as JSON for the client portal."""
    return jsonify({'announcements': _get_announcements()})

@app.route('/kiosk/leaderboard')
def kiosk_leaderboard():
    """
    Public leaderboard kiosk page.
    Renders as a standalone full-screen page (no admin sidebar).
    Designed to be displayed on a gym TV/monitor.
    """
    from controllers.leaderboard_controller import LeaderboardController
    leaderboard = LeaderboardController()

    top_exp     = leaderboard.get_top_exp(limit=10)
    top_reps    = leaderboard.get_top_reps(limit=10)
    top_streaks = leaderboard.get_top_streaks(limit=10)

    return render_template(
        'kiosk/leaderboard_kiosk.html',
        top_exp=top_exp,
        top_reps=top_reps,
        top_streaks=top_streaks
    )

if __name__ == '__main__':
    local_ip = get_local_ip()
    print("\n" + "="*70)
    print("🏋️  LevelUp Gym - Web Portal Server")
    print("="*70)
    print(f"\n📱 Client Portal:")
    print(f"   http://{local_ip}:5000")
    print(f"\n👨‍💼 Admin Portal:")
    print(f"   http://{local_ip}:5000/admin")
    print(f"   Username: admin | Password: admin123")
    print(f"\n   (Use these URLs on devices connected to the same WiFi)")
    print("\n" + "="*70 + "\n")
    
    # Run on all network interfaces
    app.run(host='0.0.0.0', port=5000, debug=True)