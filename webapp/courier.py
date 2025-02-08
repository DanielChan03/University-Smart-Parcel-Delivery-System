from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify
from datetime import datetime
from flask_login import current_user, login_required
from .models import Courier, Parcel, ParcelStatus, Delivery, db
from werkzeug.security import generate_password_hash
import random

courier = Blueprint('courier', __name__)

# Courier Dashboard
@courier.route('/courier-dashboard')
@login_required
def courier_dashboard():

    # Fetch active deliveries
    active_delivery = Delivery.query.filter_by(Courier_ID=current_user.Courier_ID).order_by(Delivery.Deliver_Date.desc()).first()

    # Fetch collected parcels count
    collected_parcels = Parcel.query.filter_by(Delivery_ID=active_delivery.Delivery_ID).count() if active_delivery else 0

    # Fetch reported parcels
    reported_parcels = ParcelStatus.query.filter_by(Status_Type='Reported').count()

    # Fetch scheduled deliveries
    scheduled_delivery = Delivery.query.filter_by(Courier_ID=current_user.Courier_ID).order_by(Delivery.Arrival_Date.asc()).first()

    return render_template(
        "Courier/CourierDashboard.html",
        courier=current_user,
        active_delivery_id=active_delivery.Delivery_ID if active_delivery else "None",
        active_delivery_date=active_delivery.Deliver_Date if active_delivery else "N/A",
        collected_parcels=collected_parcels,
        reported_parcels=reported_parcels,
        scheduled_delivery_id=scheduled_delivery.Delivery_ID if scheduled_delivery else "None",
        scheduled_delivery_date=scheduled_delivery.Arrival_Date if scheduled_delivery else "N/A"
    )

# View Assigned Parcels
@courier.route('/assigned-parcels', methods=['GET'])
@login_required
def view_assigned_parcels():
    assigned_parcels = Parcel.query.filter_by(Delivery_ID=current_user.Courier_ID).all()
    return render_template("Courier/CourierAssignedParcels.html", parcels=assigned_parcels)

# Update Parcel Status
@courier.route('/report-parcel', methods=['GET', 'POST'])
@login_required
def report_parcel():
    if request.method == 'POST':
        parcel_id = request.form.get("parcel_id")
        issue_description = request.form.get("issue_description")
        issue_type = request.form.get("issue_type")

        if not parcel_id or not issue_description:
            flash("Parcel ID and issue description are required.", "danger")
            return redirect(url_for("courier.report_parcel"))

        # Check if the parcel exists
        parcel = Parcel.query.filter_by(Parcel_ID=parcel_id).first()
        if not parcel:
            flash("Parcel ID not found. Please enter a valid Parcel ID.", "danger")
            return redirect(url_for("courier.report_parcel"))

        # Create a new report
        new_report = ParcelStatus(
            Status_ID=f"REP{random.randint(100000, 999999)}",
            Parcel_ID=parcel_id,
            Status_Type="Reported - " + issue_type.capitalize(),
            Updated_by=current_user.Courier_ID
        )
        db.session.add(new_report)

        # Update parcel status (assuming there's a column to track status)
        parcel.Status = "Reported"  # Update status column in the Parcel table (if it exists)

        db.session.commit()

        flash("Parcel issue reported successfully!", "success")
        return redirect(url_for("courier.report_parcel"))

    return render_template("Courier/CourierReportDelivery.html") 

# Initialize notifications in the session if not already present
def init_notifications():
    if 'notifications' not in session:
        session['notifications'] = []

# Add a notification to the session
def add_notification(recipient_id, title, message):
    init_notifications()
    notification = {
        'id': f"NOT{random.randint(100000, 999999)}",  # Generate a unique ID
        'recipient_id': recipient_id,
        'title': title,
        'message': message,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'is_read': False
    }
    session['notifications'].append(notification)
    session.modified = True  # Ensure the session is marked as modified

# Get notifications for the current user
def get_notifications(recipient_id):
    init_notifications()
    return [n for n in session['notifications'] if n['recipient_id'] == recipient_id]

# Mark a notification as read
def mark_notification_read(notification_id):
    init_notifications()
    for notification in session['notifications']:
        if notification['id'] == notification_id:
            notification['is_read'] = True
            session.modified = True
            break

# Render the CourierNotifications.html page
@courier.route('/notifications', methods=['GET'])
@login_required
def notifications_page():
    
    return render_template("Courier/CourierNotifications.html")

# Send Notification
@courier.route('/send-notification', methods=['POST'])
@login_required
def send_notification():
    data = request.get_json()
    recipient_id = data.get('recipient_id')
    title = data.get('title')
    message = data.get('message')

    if not recipient_id or not title or not message:
        return jsonify({'success': False, 'message': 'Missing required fields.'}), 400

    # Add the notification to the session
    add_notification(recipient_id, title, message)

    return jsonify({'success': True, 'message': 'Notification sent successfully.'})

# Get Notifications
@courier.route('/get-notifications', methods=['GET'])
@login_required
def get_notifications_route():
    # Fetch notifications for the current user
    notifications = get_notifications(current_user.get_id())

    return jsonify({'success': True, 'notifications': notifications})

# Mark Notification as Read
@courier.route('/mark-notification-read/<string:notification_id>', methods=['POST'])
@login_required
def mark_notification_read_route(notification_id):
    mark_notification_read(notification_id)
    return jsonify({'success': True, 'message': 'Notification marked as read.'})

# Collect parcel
@courier.route('/collect-parcel', methods=['GET'])
@login_required
def collect_parcel():
    #  deliveries = Delivery.query.filter_by(Courier_ID=current_user.Courier_ID).all()
     return render_template("Courier/CourierCollectParcel.html") # , deliveries=deliveries

#View Parcel Manager List
@courier.route('/view-managers',methods =['GET'])
@login_required
def courierViewManagerList():
    return render_template('Courier/CourierViewManagerList.html')



