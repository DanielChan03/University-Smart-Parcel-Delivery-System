from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'Admin'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite.db'
    db.init_app(app)

    # Register Blueprints
    from .views import views
    from .auth import auth
    from .admin import admin
    from .AdminAuth import admin_auth 
    from .CourierAuth import courier_auth


    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(admin_auth, url_prefix='/admin')
    app.register_blueprint(courier_auth, url_prefix='/courier')

    # Import models and create tables
    from .models import StudentStaff, University, ParcelManager, SmartLocker, Courier, ParcelStatus, Parcel, Waitlist,Admin, Report  # Import all your models here
    with app.app_context():
        db.create_all()  # Create tables if not already present

    # Set up Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'  # Default route for login
    login_manager.init_app(app)
    

    @login_manager.user_loader
    def load_user(user_id):
        from .models import StudentStaff, Admin, Courier

        user = StudentStaff.query.get(user_id)
        if user:
            return user

        admin = Admin.query.get(user_id)
        if admin:
            return admin

        courier = Courier.query.get(user_id)
        if courier:
            return courier
            
        return None

    return app