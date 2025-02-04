# webapp/create_parcel_manager.py
from webapp import create_app, db
from webapp.models import ParcelManager
from werkzeug.security import generate_password_hash

# Create the Flask app and app context
app = create_app()

# Create the parcel manager account function
def create_parcel_manager(email, name, plain_password, contact, work_branch):
    with app.app_context():  # Ensure the app context is active
        
        # Check if a parcel manager with the given email already exists
        existing_manager = ParcelManager.query.filter_by(Manager_Email=email).first()
        
        if existing_manager:
            print(f"Parcel Manager with email {email} already exists.")
            return  # Early exit if the manager already exists
        
        # Hash the password
        hashed_password = generate_password_hash(plain_password, method='pbkdf2:sha256')

        manager_id = ParcelManager.generate_manager_id()
        # Create the ParcelManager object
        manager = ParcelManager(
            Manager_ID = manager_id,
            Manager_Name=name,
            Manager_Email=email,
            Manager_Password=hashed_password,
            Manager_Contact=contact,
            Manager_Work_Branch=work_branch
        )

        # Add the manager to the session and commit
        db.session.add(manager)
        db.session.commit()

        print(f"Parcel Manager account for {name} created successfully.")
