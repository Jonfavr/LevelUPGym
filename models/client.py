import sys
import os
from datetime import datetime, date

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager

class Client:
    """Client model - represents a gym member"""
    
    def __init__(self, client_id=None, phone_number=None, first_name=None, 
                 last_name=None, email=None, date_of_birth=None, gender=None,
                 profile_photo_path=None, status='active'):
        self.client_id = client_id
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.profile_photo_path = profile_photo_path
        self.status = status
        self.registration_date = None
        
        # Related data
        self.physical_data = None
        self.availability = []
        self.gamification = None
        self.streak = None
        
    @property
    def full_name(self):
        """Return full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        if self.date_of_birth:
            if isinstance(self.date_of_birth, str):
                dob = datetime.strptime(self.date_of_birth, '%Y-%m-%d').date()
            else:
                dob = self.date_of_birth
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return None
    
    def save(self, pin):
        """Save new client to database"""
        db = DatabaseManager()
        pin_hash = db.hash_pin(pin)
        
        query = '''
            INSERT INTO clients (phone_number, pin_hash, first_name, last_name, 
                               email, date_of_birth, gender, profile_photo_path, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (self.phone_number, pin_hash, self.first_name, self.last_name,
                 self.email, self.date_of_birth, self.gender, 
                 self.profile_photo_path, self.status)
        
        self.client_id = db.execute_update(query, params)
        
        # Initialize gamification & streak tracking
        self._initialize_gamification()
        self._initialize_streak()
        
        return self.client_id
    
    def update(self):
        """Update existing client info"""
        db = DatabaseManager()
        query = '''
            UPDATE clients 
            SET phone_number=?, first_name=?, last_name=?, email=?, 
                date_of_birth=?, gender=?, profile_photo_path=?, status=?
            WHERE client_id=?
        '''
        params = (self.phone_number, self.first_name, self.last_name, self.email,
                 self.date_of_birth, self.gender, self.profile_photo_path, 
                 self.status, self.client_id)
        db.execute_update(query, params)

    # ----------------------------- #
    # 🧠 PHYSICAL DATA IMPROVEMENT #
    # ----------------------------- #

    def add_or_update_physical_data(self, height_cm, weight_kg, body_fat_percentage=None, notes=None):
        """
        Add or update the client's physical data (merged logic)
        Automatically updates if record exists; inserts otherwise.
        """
        db = DatabaseManager()
        existing = db.execute_query(
            "SELECT physical_id FROM client_physical_data WHERE client_id = ? ORDER BY measurement_date DESC LIMIT 1",
            (self.client_id,)
        )

        if existing:
            query = '''
                UPDATE client_physical_data
                SET height_cm=?, weight_kg=?, body_fat_percentage=?, notes=?, measurement_date=DATE('now')
                WHERE physical_id=?
            '''
            db.execute_update(query, (height_cm, weight_kg, body_fat_percentage, notes, existing[0]['physical_id']))
        else:
            query = '''
                INSERT INTO client_physical_data 
                (client_id, height_cm, weight_kg, body_fat_percentage, notes)
                VALUES (?, ?, ?, ?, ?)
            '''
            db.execute_update(query, (self.client_id, height_cm, weight_kg, body_fat_percentage, notes))

    def get_latest_physical_data(self):
        """Get most recent physical measurements"""
        db = DatabaseManager()
        query = '''
            SELECT * FROM client_physical_data 
            WHERE client_id=? 
            ORDER BY measurement_date DESC 
            LIMIT 1
        '''
        result = db.execute_query(query, (self.client_id,))
        return dict(result[0]) if result else None

    # ----------------------------- #
    # 🧩 AVAILABILITY + ROUTINES    #
    # ----------------------------- #

    def set_availability(self, days):
        """Set client's available training days"""
        db = DatabaseManager()
        all_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        db.execute_update('DELETE FROM client_availability WHERE client_id=?', (self.client_id,))

        for day in all_days:
            is_available = 1 if day in days else 0
            query = '''
                INSERT INTO client_availability (client_id, day_of_week, is_available)
                VALUES (?, ?, ?)
            '''
            db.execute_update(query, (self.client_id, day, is_available))

    def assign_routine_to_day(self, day, routine_id):
        """
        Assign a specific routine to a day of the week.
        Called from admin form on update.
        """
        db = DatabaseManager()
        db.execute_update("DELETE FROM routine_assignments WHERE client_id=? AND day_of_week=?", (self.client_id, day))

        if routine_id:
            db.execute_update('''
                INSERT INTO routine_assignments (client_id, routine_id, day_of_week, is_active)
                VALUES (?, ?, ?, 1)
            ''', (self.client_id, routine_id, day))

    def clear_unassigned_days(self, active_days):
        """
        Remove routine assignments for days that are no longer selected as available.
        """
        db = DatabaseManager()
        placeholders = ','.join('?' * len(active_days)) if active_days else 'NULL'
        if active_days:
            query = f"DELETE FROM routine_assignments WHERE client_id=? AND day_of_week NOT IN ({placeholders})"
            db.execute_update(query, (self.client_id, *active_days))
        else:
            db.execute_update("DELETE FROM routine_assignments WHERE client_id=?", (self.client_id,))

    def get_availability(self):
        """Return a list of available training days"""
        db = DatabaseManager()
        query = '''
            SELECT day_of_week FROM client_availability 
            WHERE client_id=? AND is_available=1
        '''
        results = db.execute_query(query, (self.client_id,))
        return [row['day_of_week'] for row in results]

    def get_weekly_schedule(self):
        """Return dictionary {day: routine info} for this client"""
        db = DatabaseManager()
        query = '''
            SELECT ra.day_of_week, r.routine_id, r.routine_name, r.description
            FROM routine_assignments ra
            JOIN routines r ON ra.routine_id = r.routine_id
            WHERE ra.client_id=? AND ra.is_active=1
        '''
        results = db.execute_query(query, (self.client_id,))
        return {row['day_of_week']: dict(row) for row in results}

    # ----------------------------- #
    # ⚡ GAMIFICATION & STREAKS     #
    # ----------------------------- #

    def _initialize_gamification(self):
        """Initialize gamification data for new client"""
        db = DatabaseManager()
        query = '''
            INSERT INTO client_gamification (client_id, current_level, current_exp, rank)
            VALUES (?, 1, 0, 'E')
        '''
        db.execute_update(query, (self.client_id,))

    def _initialize_streak(self):
        """Initialize streak tracking for new client"""
        db = DatabaseManager()
        query = '''
            INSERT INTO client_streaks (client_id, current_streak, longest_streak)
            VALUES (?, 0, 0)
        '''
        db.execute_update(query, (self.client_id,))

    def get_gamification_data(self):
        """Get client's gamification stats"""
        db = DatabaseManager()
        query = 'SELECT * FROM client_gamification WHERE client_id=?'
        result = db.execute_query(query, (self.client_id,))
        return dict(result[0]) if result else None
        
    
    def get_streak_data(self):
        """Get client's streak information"""
        db = DatabaseManager()
        query = 'SELECT * FROM client_streaks WHERE client_id=?'
        result = db.execute_query(query, (self.client_id,))
        return dict(result[0]) if result else None

    # ----------------------------- #
    # 🔍 RETRIEVAL HELPERS          #
    # ----------------------------- #

    @staticmethod
    def get_by_id(client_id):
        """Retrieve client by ID"""
        db = DatabaseManager()
        query = 'SELECT * FROM clients WHERE client_id=?'
        result = db.execute_query(query, (client_id,))
        
        if result:
            row = result[0]
            client = Client(
                client_id=row['client_id'],
                phone_number=row['phone_number'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                email=row['email'],
                date_of_birth=row['date_of_birth'],
                gender=row['gender'],
                profile_photo_path=row['profile_photo_path'],
                status=row['status']
            )
            client.registration_date = row['registration_date']
            return client
        return None
    
    @staticmethod
    def authenticate(phone_number, pin):
        """Authenticate client with phone and PIN"""
        db = DatabaseManager()
        pin_hash = db.hash_pin(pin)
        query = 'SELECT * FROM clients WHERE phone_number=? AND pin_hash=? AND status="active"'
        result = db.execute_query(query, (phone_number, pin_hash))
        
        if result:
            row = result[0]
            client = Client(
                client_id=row['client_id'],
                phone_number=row['phone_number'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                email=row['email'],
                date_of_birth=row['date_of_birth'],
                gender=row['gender'],
                profile_photo_path=row['profile_photo_path'],
                status=row['status']
            )
            client.registration_date = row['registration_date']
            return client
        return None
    
    @staticmethod
    def get_all_active():
        """Get all active clients"""
        db = DatabaseManager()
        query = 'SELECT * FROM clients WHERE status="active" ORDER BY last_name, first_name'
        results = db.execute_query(query)
        
        clients = []
        for row in results:
            client = Client(
                client_id=row['client_id'],
                phone_number=row['phone_number'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                email=row['email'],
                date_of_birth=row['date_of_birth'],
                gender=row['gender'],
                profile_photo_path=row['profile_photo_path'],
                status=row['status']
            )
            client.registration_date = row['registration_date']
            clients.append(client)
        
        return clients

    def __repr__(self):
        return f"<Client {self.client_id}: {self.full_name} ({self.phone_number})>"

# Example usage and testing
if __name__ == "__main__":
    # Initialize database first
    from database.db_manager import DatabaseManager
    db = DatabaseManager()
    db.initialize_database()
    
    # Create a new client
    client = Client(
        phone_number="1234567890",
        first_name="John",
        last_name="Doe",
        email="john.doe@email.com",
        date_of_birth="1990-05-15",
        gender="Male"
    )
    
    # Save to database with PIN
    client_id = client.save(pin="1234")
    print(f"✅ Client created with ID: {client_id}")
    
    # Add physical data
    client.add_physical_data(height_cm=175, weight_kg=80, body_fat_percentage=18.5)
    print("✅ Physical data added")
    
    # Set availability
    client.set_availability(['Monday', 'Wednesday', 'Friday'])
    print(f"✅ Availability set: {client.get_availability()}")
    
    # Test authentication
    auth_client = Client.authenticate("1234567890", "1234")
    if auth_client:
        print(f"✅ Authentication successful: {auth_client.full_name}")
        print(f"   Age: {auth_client.age}")
        print(f"   Gamification: {auth_client.get_gamification_data()}")
        print(f"   Streak: {auth_client.get_streak_data()}")
    
    # Get all active clients
    all_clients = Client.get_all_active()
    print(f"✅ Total active clients: {len(all_clients)}")
