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
    from webapp.Couriercode.CourierAuth import courier_auth
    from .ParcelManagerAuth import parcel_manager_auth
    from .parcel_manager import parcel_manager
    from webapp.Couriercode.courierdashboard import courier_dashboard_bp
    from webapp.Couriercode.courierprofile import courier_profile_bp
    from webapp.Couriercode.report_parcel import report_parcel_bp
    from webapp.Couriercode.notifications import notifications_bp
    from webapp.Couriercode.collect_parcel import collect_parcel_bp
    from webapp.Couriercode.view_manager_list import view_manager_list_bp
    from webapp.Couriercode.manage_parcel_status import manage_parcel_status_bp
    from webapp.Couriercode.view_reported_history import view_reported_history_bp



    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(admin_auth, url_prefix='/admin')
    app.register_blueprint(courier_auth, url_prefix='/courier')
    app.register_blueprint(parcel_manager, url_prefix='/parcel-manager')
    app.register_blueprint(parcel_manager_auth, url_prefix='/parcel-manager')
    app.register_blueprint(courier_dashboard_bp,url_prefix='/courier')
    app.register_blueprint(courier_profile_bp,url_prefix='/courier')
    app.register_blueprint(report_parcel_bp,url_prefix='/courier')
    app.register_blueprint(notifications_bp,url_prefix='/courier')
    app.register_blueprint(collect_parcel_bp,url_prefix='/courier')
    app.register_blueprint(view_manager_list_bp,url_prefix='/courier')
    app.register_blueprint(manage_parcel_status_bp,url_prefix='/courier')
    app.register_blueprint(view_reported_history_bp,url_prefix='/courier')

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
        from .models import StudentStaff, Admin, Courier, ParcelManager

        user = StudentStaff.query.get(user_id)
        if user:
            return user

        admin = Admin.query.get(user_id)
        if admin:
            return admin

        courier = Courier.query.get(user_id)
        if courier:
            return courier

        parcel_manager = ParcelManager.query.get(user_id)  # Add this
        if parcel_manager:
            return parcel_manager
            
        return None

    return app
