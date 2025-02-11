from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_required
from .models import  Parcel, ParcelStatus, Waitlist, ParcelManager, Courier, SmartLocker, Delivery, db, StudentStaff
from werkzeug.security import generate_password_hash
import random
import string
from datetime import datetime  # Import the datetime class
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime, timezone



parcel_manager = Blueprint('parcel_manager', __name__)

# Parcel Manager Dashboard
@parcel_manager.route('/parcel-manager-dashboard')
@login_required
def parcel_manager_dashboard():
    if not isinstance(current_user, ParcelManager):
        flash('Unauthorized access! Please log in as a Parcel Manager.', category="error")
        return redirect(url_for('parcel_manager_auth.parcel_manager_login'))

    # Fetch notifications (unresponded feedback) from session
    notifications = session.get('feedback', {})

    # Fetch parcel statistics
    total_received_parcels = Parcel.query.count()

    # Fetch delivered parcels (status type is "Delivered")
    total_delivered_parcels = db.session.query(ParcelStatus).filter_by(Status_Type='Delivered').count()

    # Fetch pending parcels (status type is not "Delivered")
    pending_parcels = db.session.query(ParcelStatus).filter(ParcelStatus.Status_Type != "Delivered").count()

    # Fetch locker status
    locker_status = db.session.query(SmartLocker.Locker_Status).all()

    lockers = SmartLocker.query.all()

    # Count messages sent and received by the current user
    current_user_email = current_user.Manager_Email
    messages_sent = count_messages_sent(current_user_email)
    messages_received = count_messages_received(current_user_email)

    return render_template(
        "ParcelManager/ParcelManagerDashboard.html",
        parcel_manager = current_user,
        notifications = notifications,
        total_received_parcels = total_received_parcels,
        total_delivered_parcels = total_delivered_parcels,
        pending_parcels = pending_parcels,
        locker_status = locker_status,
        lockers = lockers,
        messages_sent=messages_sent,
        messages_received=messages_received
    )

def count_messages_sent(current_user_email):
    init_notifications()  # Ensure notifications are initialized

    # Check if 'notifications' exists and is a list
    if 'notifications' not in session or not isinstance(session['notifications'], list):
        return 0  # Return 0 if the key is missing or not a list

    return sum(1 for n in session['notifications'] if 'sender_email' in n and n['sender_email'] == current_user_email)

def count_messages_received(current_user_email):
    init_notifications()

    if 'notifications' not in session or not isinstance(session['notifications'], list):
        return 0

    return sum(1 for n in session['notifications'] if 'recipient_email' in n and n['recipient_email'] == current_user_email)

 #Initialize notifications in the session if not already present
def init_notifications():
    if 'notifications' not in session:
        session['notifications'] = []

def is_valid_recipient(email):
    # Check if the email exists in any of the user tables.
    return (
        StudentStaff.query.filter_by(User_Email=email).first() or
        ParcelManager.query.filter_by(Manager_Email=email).first() or
        Courier.query.filter_by(Courier_Email=email).first()
    )

# Add a notification to the session
def add_notification(recipient_email, title, message, sender_email):
    init_notifications()

    if not is_valid_recipient(recipient_email):
        return {'success': False, 'message': 'Recipient email not found.'}  # Don't add if recipient doesn't exist


    notification = {
        'id': f"NOT{random.randint(100000, 999999)}",  # Generate a unique ID
        'recipient_email': recipient_email,
        'title': title,
        'message': message,
        'sender_email': sender_email, 
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'is_read': False
    }
    session['notifications'].append(notification)
    session.modified = True  # Ensure the session is marked as modified
    return {'success': True, 'message': 'Message Succesfully sent'} 

# Get notifications for the current user
@parcel_manager.route('/get-notification/<string:notification_id>', methods=['GET'])
@login_required
def get_notifications_by_id(notification_id):
    init_notifications()
    notification = next((n for n in session['notifications'] if n['id'] == notification_id), None)
    if notification:
        return jsonify({'success': True, 'notification': notification})
    else:
        return jsonify({'success': False, 'message': 'Notification not found.'}), 404
    
@parcel_manager.route('/reply-notification/<string:notification_id>', methods=['POST'])
@login_required
def reply_notification(notification_id):
    data = request.get_json()
    reply_message = data.get('reply_message')

    if not reply_message:
        return jsonify({'success': False, 'message': 'Reply message is required.'}), 400

    # Fetch the original notification
    init_notifications()
    original_notification = next((n for n in session['notifications'] if n['id'] == notification_id), None)
    if not original_notification:
        return jsonify({'success': False, 'message': 'Notification not found.'}), 404

    # Get the sender's email (e.g., current user's email)
    sender_email = current_user.Manager_Email  # Assuming the current user has an email field

    # Send the reply as a new notification to the original sender
    add_notification(original_notification['sender_email'], 'Reply to your notification', reply_message, sender_email)

    return jsonify({'success': True, 'message': 'Reply sent successfully.'})

# Mark a notification as read
def mark_notification_read(notification_id):
    init_notifications()
    for notification in session['notifications']:
        if notification['id'] == notification_id:
            notification['is_read'] = True
            session.modified = True
            break

# Render the CourierNotifications.html page
@parcel_manager.route('/notifications', methods=['GET'])
@login_required
def notifications_page():
    notifications = get_notifications_by_id(current_user.get_id())
    return render_template("ParcelManager/ParcelManagerNotifications.html", notifications=notifications)

# Send Notification
@parcel_manager.route('/send-notification', methods=['POST'])
@login_required
def send_notification():
    data = request.get_json()
    recipient_email = data.get('recipient_email')
    title = data.get('title')
    message = data.get('message')

    if not recipient_email or not title or not message:
        return jsonify({'success': False, 'message': 'Missing required fields.'}), 400

    # Determine the sender's email based on the current user's role
    sender_email = current_user.Manager_Email

    # Add the notification to the session
    result = add_notification(recipient_email, title, message, sender_email)

    return jsonify(result)

# Get Notifications
@parcel_manager.route('/get-notifications', methods=['GET'])
@login_required
def get_notifications_route():
    # Fetch notifications for the current user
    init_notifications()

    # Get the current user's email
    recipient_email = getattr(current_user, 'Manager_Email', None)

    if not recipient_email:
        return jsonify({'success': False, 'message': 'User email not found.'}), 400
     # Ensure session['notifications'] is a list before filtering
    notifications = session.get('notifications', [])

    # Filter notifications for the current recipient
    user_notifications = [n for n in notifications if n.get('recipient_email') == recipient_email]

    return jsonify({'success': True, 'notifications': user_notifications})

# Mark Notification as Read
@parcel_manager.route('/mark-notification-read/<string:notification_id>', methods=['POST'])
@login_required
def mark_notification_read_route(notification_id):
    init_notifications()  # Ensure notifications are initialized
    
    if 'read_notifications' not in session:
        session['read_notifications'] = []  # Use a list instead of a set

    notification = next((n for n in session['notifications'] if n['id'] == notification_id), None)

    if not notification:
        return jsonify({'success': False, 'message': 'Notification not found.'}), 404

    # Ensure only the recipient can mark it as read
    if notification['recipient_email'] != current_user.Manager_Email:
        return jsonify({'success': False, 'message': 'You are not allowed to mark this notification as read.'}), 403

    # Store read notification ID in session
    if notification_id not in session['read_notifications']:
        session['read_notifications'].append(notification_id)  
        session.modified = True  # Ensure session is saved

    notification['is_read'] = True  # Mark as read

    return jsonify({'success': True, 'message': 'Notification marked as read.'})

@parcel_manager.route('/parcel-manager/profile')
@login_required
def parcel_manager_profile():
    # Ensure the user is a parcel manager
    if not isinstance(current_user, ParcelManager):
        return redirect(url_for('unauthorized'))  # Redirect if not a parcel manager

    # Retrieve the parcel manager's data from the database
    parcel_manager_data = {
        'Manager_ID': current_user.Manager_ID,
        'Manager_Name': current_user.Manager_Name,
        'Manager_Email': current_user.Manager_Email,
        'Manager_Contact': current_user.Manager_Contact,
    }

    return render_template('ParcelManager/ParcelManagerProfile.html', manager=parcel_manager_data)



@parcel_manager.route('/organize-parcel', methods=['GET', 'POST'])
def organize_parcel():
    parcels = Parcel.query.all()
    statuses = ParcelStatus.query.all()
    deliveries = Delivery.query.all()
    couriers = Courier.query.all()

    min_date = datetime.today().strftime('%Y-%m-%d')

    if request.method == 'POST':
        selectedParcel = request.form.getlist('selected_parcels[]')
        deliveryDate = request.form.get('delivery_date')
        courierID = request.form.get('courier_id')

        if selectedParcel and deliveryDate and courierID:
            # Generate a unique delivery ID
            def generate_unique_delivery_id():
                while True:
                    delivery_id = 'DEL' + ''.join(random.choices('0123456789', k=8))
                    existing_delivery = Delivery.query.filter_by(Delivery_ID=delivery_id).first()
                    if not existing_delivery:  # Ensure the ID is unique
                        return delivery_id

            # Inside your function where you create a new delivery
            delivery_id = generate_unique_delivery_id()

            # Create a new delivery
            newDelivery = Delivery(
                Delivery_ID=delivery_id,
                Courier_ID=courierID,
                Deliver_Date=datetime.strptime(deliveryDate, '%Y-%m-%d')
            )

            db.session.add(newDelivery)
            db.session.flush()  # Ensure newDelivery.Delivery_ID is available before linking parcels

            for parcelID in selectedParcel:
                parcel = Parcel.query.filter_by(Parcel_ID=parcelID).first()
                if parcel:
                    newDelivery.parcels.append(parcel)  # Link parcel to delivery

                    # Ensure each parcel has a unique status ID
                    status_id = f"{''.join(random.choices(string.ascii_uppercase, k=3))}{''.join(random.choices('0123456789', k=8))}"
                    while ParcelStatus.query.filter_by(Status_ID=status_id).first():
                        status_id = f"{''.join(random.choices(string.ascii_uppercase, k=3))}{''.join(random.choices('0123456789', k=8))}"

                    # Update parcel status
                    new_status = ParcelStatus(
                        Status_ID=status_id,
                        Parcel_ID=parcel.Parcel_ID,
                        Status_Type="Ready to Pickup",
                        Updated_by=current_user.Manager_ID,
                        Updated_At=datetime.utcnow()
                    )
                    db.session.add(new_status)

            db.session.commit()
            flash(f"New delivery created with ID {delivery_id}!", category="success")
        else:
            flash("No parcel selected, delivery date missing, or courier not assigned!", category="error")

        return redirect(url_for('parcel_manager.organize_parcel'))

    return render_template(
        'ParcelManager/ParcelManagerOrganizeParcel.html',
        parcels=parcels,
        statuses=statuses,
        deliveries=deliveries,
        couriers=couriers,
        min_date=min_date
    )



@parcel_manager.route('/update_parcel_status', methods=['GET', 'POST'])
@login_required
def update_parcel_status():
    # Fetch parcels that have the status "Verified - Collected" or "In Transit"
    parcels = db.session.query(Parcel).join(ParcelStatus).filter(
        ParcelStatus.Status_Type.in_(["Verified - Collected"])
    ).all()

    if request.method == 'POST':
        parcel_id = request.form.get('Parcel_ID')
        update_status = request.form.get('Update_Status')

        if not parcel_id or not update_status:
            flash('Parcel ID and Status are required!', category='error')
            return redirect(url_for('parcel_manager.update_parcel_status'))

        try:
            # Generate a unique status ID in the format UPSXXXXXXXX
            def generate_unique_status_id():
                while True:
                    status_id = f"UPS{random.randint(10000000, 99999999)}"
                    existing_status = ParcelStatus.query.filter_by(Status_ID=status_id).first()
                    if not existing_status:
                        return status_id

            new_status_id = generate_unique_status_id()

            # Add a new status entry instead of updating an existing one
            new_status = ParcelStatus(
                Status_ID=new_status_id,
                Parcel_ID=parcel_id,
                Status_Type=update_status,
                Updated_by=current_user.Manager_ID,
                Updated_At=datetime.now(timezone.utc)
            )
            db.session.add(new_status)
            db.session.commit()

            flash(f'Status updated successfully for Parcel {parcel_id}!', category='success')

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', category='error')

        return redirect(url_for('parcel_manager.update_parcel_status'))

    return render_template(
        'ParcelManager/ParcelManagerUpdateParcelStatus.html',
        parcels=parcels
    )

@parcel_manager.route('/monitor_locker_issue', methods=['GET', 'POST'])
def monitor_locker_issue():
    # Get search query
    lockerFilter = request.args.get('filter', '').strip()

    if lockerFilter:
        lockers = SmartLocker.query.filter(SmartLocker.Locker_ID.ilike(f'%{lockerFilter}%')).all()
        flash(f"Showing results for Locker ID: {lockerFilter}", "success")
    else:
        lockers = SmartLocker.query.all()


    
    return render_template(
        "ParcelManager/ParcelManagerMonitorLockerIssue.html",
        lockers = lockers,
        lockerFilter=lockerFilter,
    )


@parcel_manager.route('/log_arrival_parcel', methods=['GET', 'POST'])
@login_required
def log_arrival_parcel():
    if request.method == 'POST':
        parcel_id = request.form.get('Parcel_ID')
        update_status = request.form.get('Update_Status')

        if not parcel_id or not update_status:
            flash('Parcel ID and Status are required!', category='error')
            return redirect(url_for('parcel_manager.log_arrival_parcel'))

        try:
            # Generate a unique status ID in the format LOGXXXXXXXX
            def generate_unique_status_id():
                while True:
                    status_id = f"LOG{random.randint(10000000, 99999999)}"
                    existing_status = ParcelStatus.query.filter_by(Status_ID=status_id).first()
                    if not existing_status:
                        return status_id

            new_status_id = generate_unique_status_id()

            # Add a new status entry instead of updating an existing one
            new_status = ParcelStatus(
                Status_ID=new_status_id,
                Parcel_ID=parcel_id,
                Status_Type=update_status,
                Updated_by=current_user.Manager_ID,
                Updated_At=datetime.now(timezone.utc)
            )
            db.session.add(new_status)
            db.session.commit()

            flash(f'Status updated successfully for Parcel {parcel_id}!', category='success')

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', category='error')

        return redirect(url_for('parcel_manager.log_arrival_parcel'))

    # Fetch only parcels whose latest status is "Parcel Handed Over to Parcel Manager"
    subquery = db.session.query(
        ParcelStatus.Parcel_ID,
        db.func.max(ParcelStatus.Updated_At).label("Latest_Update")
    ).group_by(ParcelStatus.Parcel_ID).subquery()

    parcels = db.session.query(Parcel).join(
        ParcelStatus, Parcel.Parcel_ID == ParcelStatus.Parcel_ID
    ).join(
        subquery, (ParcelStatus.Parcel_ID == subquery.c.Parcel_ID) & (ParcelStatus.Updated_At == subquery.c.Latest_Update)
    ).filter(
        ParcelStatus.Status_Type == "Parcel Handed Over to Parcel Manager"
    ).all()

    return render_template(
        'ParcelManager/ParcelManagerLogArrivalParcel.html',
        parcels=parcels
    )



@parcel_manager.route('/assign_parcel_to_locker', methods=['GET', 'POST'])
def assign_parcel_to_locker():
    if request.method == 'POST':  # Handle form submission
        parcel_id = request.form.get('selected_parcel')
        locker_id = request.form.get('selected_locker')

        if not parcel_id:
            flash("Please select a parcel!", "error")
            return redirect(url_for('parcel_manager.assign_parcel_to_locker'))

        if not locker_id:
            flash("Please select a locker!", "error")
            return redirect(url_for('parcel_manager.assign_parcel_to_locker'))

        try:
            parcel = Parcel.query.get(parcel_id)
            locker = SmartLocker.query.get(locker_id)

            if parcel and locker:
                # Assign locker to parcel
                locker.Locker_Status = "Occupied"
                parcel.Receive_Locker_ID = locker.Locker_ID

                # Generate a unique status ID in the format APLXXXXXXXX
                def generate_unique_status_id():
                    while True:
                        status_id = f"APL{random.randint(10000000, 99999999)}"
                        existing_status = ParcelStatus.query.filter_by(Status_ID=status_id).first()
                        if not existing_status:
                            return status_id

                new_status_id = generate_unique_status_id()

                # Add a new status entry instead of updating an existing one
                new_status = ParcelStatus(
                    Status_ID=new_status_id,
                    Parcel_ID=parcel_id,
                    Status_Type=f"Assigned to Locker {locker.Locker_ID}",
                    Updated_by=current_user.Manager_ID,
                    Updated_At=datetime.now(timezone.utc)
                )
                db.session.add(new_status)

                # Remove parcel from waitlist if applicable
                waitlist_entry = Waitlist.query.filter_by(Parcel_ID=parcel_id).first()
                if waitlist_entry:
                    db.session.delete(waitlist_entry)

                db.session.commit()
                flash(f"Parcel {parcel_id} assigned to Locker {locker_id} successfully!", "success")

            else:
                flash("Invalid Parcel or Locker selection!", "error")

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "error")

        return redirect(url_for('parcel_manager.assign_parcel_to_locker'))

    # Handle GET requests - Fetch only unassigned parcels
    parcels = db.session.query(Parcel).outerjoin(ParcelStatus).filter(
        ~ParcelStatus.Status_Type.like("Assigned to Locker%")
    ).all()

    lockers = SmartLocker.query.filter_by(Locker_Status='Available').all()
    locker_count = len(lockers)

    return render_template(
        'ParcelManager/ParcelManagerAssignParcelToLocker.html',
        parcels=parcels,
        lockers=lockers,
        locker_count=locker_count
    )

@parcel_manager.route('/assign_parcel_to_waitlist', methods=['POST'])
@login_required
def assign_parcel_to_waitlist():
    parcel_id = request.form.get('selected_parcel')

    if not parcel_id:
        flash("Please select a parcel before adding to the waitlist!", "error")
        return redirect(url_for('parcel_manager.assign_parcel_to_locker'))

    try:
        # Check if parcel is already in waitlist
        existing_waitlist = Waitlist.query.filter_by(Parcel_ID=parcel_id).first()
        if existing_waitlist:
            flash("Parcel is already in the waitlist!", "info")
            return redirect(url_for('parcel_manager.assign_parcel_to_locker'))

        # Generate unique waitlist ID
        def generate_unique_waitlist_id():
            while True:
                waitlist_id = f"WT{random.randint(10000000, 99999999)}"
                existing_waitlist = Waitlist.query.filter_by(Waitlist_ID=waitlist_id).first()
                if not existing_waitlist:
                    return waitlist_id

        new_waitlist_id = generate_unique_waitlist_id()

        # Add the parcel to the waitlist
        new_waitlist = Waitlist(
            Waitlist_ID=new_waitlist_id,
            Parcel_ID=parcel_id,
            Waitlist_Status="Pending"
        )
        db.session.add(new_waitlist)
        db.session.commit()

        flash(f"Parcel {parcel_id} has been added to the waitlist!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "error")

    return redirect(url_for('parcel_manager.assign_parcel_to_locker'))
