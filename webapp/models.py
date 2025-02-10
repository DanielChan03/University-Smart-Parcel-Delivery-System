from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
import random

# University Table
class University(db.Model):
    __tablename__ = 'university'
    University_ID = db.Column(db.String(15), primary_key=True)
    University_Name = db.Column(db.String(100), nullable=False)
    University_Contact = db.Column(db.String(20), nullable=False)
    University_Location = db.Column(db.String(100), nullable=False)

# Student/Staff Table
class StudentStaff(db.Model, UserMixin):
    __tablename__ = 'student_staff'
    User_ID = db.Column(db.String(15), primary_key=True)
    University_ID = db.Column(db.String(15), db.ForeignKey('university.University_ID'), nullable=False)
    User_Type = db.Column(db.String(10), nullable=False)  # Changed from Enum to String
    User_Name = db.Column(db.String(50), nullable=False)
    User_Email = db.Column(db.String(30), nullable=False, unique=True)
    User_Password = db.Column(db.String(255), nullable=False)
    User_Contact = db.Column(db.String(20), nullable=False)
    Login_Status = db.Column(db.String(10), nullable=False, default="Inactive")  # Changed from Enum to String

    university = db.relationship('University', backref=db.backref('students_staff', lazy=True))

    def get_id(self):
        return str(self.User_ID)

    @staticmethod
    def generate_user_id(user_type):
        while True:
            prefix = 'STU' if user_type == 'Student' else 'STA'
            random_digits = ''.join([str(random.randint(0, 9)) for _ in range(8)])
            user_id = f"{prefix}{random_digits}"
            if not StudentStaff.query.get(user_id):
                return user_id

    def get_university_name(self):
        # Fetch the university name using the University_ID
        university = University.query.filter_by(University_ID=self.University_ID).first()
        return university.University_Name if university else 'Unknown'
    

    def get_university_location(self):
        # Fetch the university location using the University_ID
        university = University.query.filter_by(University_ID=self.University_ID).first()
        return university.University_Location if university else 'Unknown'

    def get_university_prefix(self):
        # Fetch the university record using the University_ID
        university = University.query.filter_by(University_ID=self.University_ID).first()

        if university:
            # Extract and return the prefix before 'UNI' from the University_ID
            return university.University_ID.split('UNI')[0] if university.University_ID else 'Unknown'
        return 'Unknown'


# Parcel Manager Table
class ParcelManager(db.Model, UserMixin):
    __tablename__ = 'parcel_manager'
    Manager_ID = db.Column(db.String(15), primary_key=True)
    Manager_Name = db.Column(db.String(50), nullable=False)
    Manager_Email = db.Column(db.String(30), nullable=False, unique=True)
    Manager_Password = db.Column(db.String(255), nullable=False)
    Manager_Contact = db.Column(db.String(20), nullable=False)
    Manager_Work_Branch = db.Column(db.String(20), nullable=False)

    
    def get_id(self):
        return str(self.Manager_ID) 

    @staticmethod
    def generate_manager_id():
        while True:
            prefix = 'MGR'  # Prefix for Manager IDs
            random_digits = ''.join([str(random.randint(0, 9)) for _ in range(8)])  # 8 random digits
            manager_id = f"{prefix}{random_digits}"  # Combine prefix and random digits
            if not ParcelManager.query.get(manager_id):  # Check if the ID already exists
                return manager_id


# Smart Locker Table
class SmartLocker(db.Model):
    __tablename__ = 'smart_locker'
    Locker_ID = db.Column(db.String(15), primary_key=True)
    Locker_Location = db.Column(db.String(100), nullable=False)
    Locker_Status = db.Column(db.String(15), nullable=False)  # Changed from Enum to String

# Courier Table
class Courier(db.Model, UserMixin):
    __tablename__ = 'courier'
    Courier_ID = db.Column(db.String(15), primary_key=True)
    Courier_Name = db.Column(db.String(50), nullable=False)
    Courier_Email = db.Column(db.String(30), nullable=False, unique=True)
    Courier_Password = db.Column(db.String(255), nullable=False)
    Courier_Contact = db.Column(db.String(20), nullable=False)

    def get_id(self):
        return str(self.Courier_ID) 
        
    def get_email(self):
        return str(self.Courier_Email)
        
    @staticmethod
    def generate_courier_id():
        while True:
            prefix = 'COU' 
            random_digits = ''.join([str(random.randint(0, 9)) for _ in range(8)])  # 8 random digits
            courier_id = f"{prefix}{random_digits}"  # Combine prefix and random digits
            if not Courier.query.get(courier_id):  # Check if the ID already exists
                return courier_id
   

# Delivery Table
class Delivery(db.Model):
    __tablename__ = 'delivery'
    Delivery_ID = db.Column(db.String(15), primary_key=True)
    Courier_ID = db.Column(db.String(15), db.ForeignKey('courier.Courier_ID'), nullable= False)
    Deliver_Date = db.Column(db.Date, nullable= False )  # Date when the parcel is collected by the courier
    Arrival_Date = db.Column(db.Date, nullable= True )  # Date when the parcel arrives at the destination
  
    # Relationship to Courier table
    courier = db.relationship('Courier', backref=db.backref('deliveries', lazy=True))
    parcels = db.relationship('Parcel', back_populates='delivery')


# Parcel Status Table
class ParcelStatus(db.Model):
    __tablename__ = 'parcel_status'
    Status_ID = db.Column(db.String(15), primary_key=True)
    Parcel_ID = db.Column(db.String(15), db.ForeignKey('parcel.Parcel_ID'), nullable=False)  # New field
    Status_Type = db.Column(db.String(25), nullable=False)
    Updated_by = db.Column(db.String(25), nullable=False)  # New field
    Updated_At = db.Column(db.DateTime, nullable=False, default=func.now())  # New field

    # Relationship to Parcel table
    parcel = db.relationship('Parcel', foreign_keys=[Parcel_ID], backref=db.backref('status_updates', lazy=True))

# Parcel Table
class Parcel(db.Model):
    __tablename__ = 'parcel'
    Parcel_ID = db.Column(db.String(20), primary_key=True)  # Unique identifier for each parcel
    Send_Locker_ID = db.Column(db.String(15), db.ForeignKey('smart_locker.Locker_ID'), nullable=False)  # Locker ID for sending the parcel
    Receive_Locker_ID = db.Column(db.String(15), db.ForeignKey('smart_locker.Locker_ID'),  nullable=True)  # Locker ID for receiving the parcel (nullable)
    Sender_User_ID = db.Column(db.String(15), db.ForeignKey('student_staff.User_ID'), nullable=False)  # User ID of the sender
    Recipient_User_ID = db.Column(db.String(15), db.ForeignKey('student_staff.User_ID'), nullable=False)  # User ID of the recipient
    Delivery_ID = db.Column(db.String(15), db.ForeignKey('delivery.Delivery_ID'), nullable=True)  # Current delivery of the parcel
    Send_Manager_ID = db.Column(db.String(15), db.ForeignKey('parcel_manager.Manager_ID'), nullable=False)  # Parcel manager handling the send process
    Receive_Manager_ID = db.Column(db.String(15), db.ForeignKey('parcel_manager.Manager_ID'), nullable=False)  # Parcel manager handling the receive process
    Parcel_Received_at = db.Column(db.DateTime, nullable=True)  # Date when the receiver collected the parcel (nullable)
    Parcel_Sent_at = db.Column(db.DateTime, nullable=False)  # Date when the parcel was sent by the sender

    # Relationships
    send_locker = db.relationship('SmartLocker', foreign_keys=[Send_Locker_ID], backref=db.backref('sent_parcels', lazy=True))
    receive_locker = db.relationship('SmartLocker', foreign_keys=[Receive_Locker_ID], backref=db.backref('received_parcels', lazy=True))
    sender = db.relationship('StudentStaff', foreign_keys=[Sender_User_ID], backref=db.backref('sent_parcels', lazy=True))
    recipient = db.relationship('StudentStaff', foreign_keys=[Recipient_User_ID], backref=db.backref('received_parcels', lazy=True))
    delivery = db.relationship('Delivery', foreign_keys=[Delivery_ID], back_populates='parcels')
    send_manager = db.relationship('ParcelManager', foreign_keys=[Send_Manager_ID], backref=db.backref('sent_parcels', lazy=True))
    receive_manager = db.relationship('ParcelManager', foreign_keys=[Receive_Manager_ID], backref=db.backref('received_parcels', lazy=True))

        # Get sender name
    def get_sender_name(self):
        return self.sender.User_Name if self.sender else 'Unknown'

    # Get recipient name
    def get_recipient_name(self):
        return self.recipient.User_Name if self.recipient else 'Unknown'



# Waitlist Table
class Waitlist(db.Model):
    __tablename__ = 'waitlist'
    Waitlist_ID = db.Column(db.String(15), primary_key=True)
    Parcel_ID = db.Column(db.String(20), db.ForeignKey('parcel.Parcel_ID'), nullable=False)
    Waitlist_Status = db.Column(db.String(20), nullable=False)  # Changed from Enum to String

# Admin Table
class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    Admin_ID = db.Column(db.String(15), primary_key=True)
    University_ID = db.Column(db.String(15), db.ForeignKey('university.University_ID'), nullable=False)
    Admin_Name = db.Column(db.String(50), nullable=False)
    Admin_Email = db.Column(db.String(30), nullable=False, unique=True)
    Admin_Password = db.Column(db.String(255), nullable=False)
    Admin_Contact = db.Column(db.String(20), nullable=False)

    
    def get_id(self):
        return str(self.Admin_ID) 
        
    @staticmethod
    def generate_admin_id():
        while True:
            prefix = 'ADM'  # Prefix for Admin IDs
            random_digits = ''.join([str(random.randint(0, 9)) for _ in range(8)])  # 8 random digits
            admin_id = f"{prefix}{random_digits}"  # Combine prefix and random digits
            if not Admin.query.get(admin_id):  # Check if the ID already exists
                return admin_id

# Report Table
class Report(db.Model):
    __tablename__ = 'report'
    Report_ID = db.Column(db.String(15), primary_key=True)
    Admin_ID = db.Column(db.String(15), db.ForeignKey('admin.Admin_ID'), nullable=False)
    Report_Type = db.Column(db.String(20), nullable=False)
    Report_Date = db.Column(db.DateTime, nullable=False)
