from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
from flask_login import login_required, current_user
from . import db
import random
import string
from .models import Parcel, SmartLocker, University, StudentStaff, ParcelManager, Delivery, ParcelStatus  # Ensure these models are imported

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    return render_template("StudentStaff/home.html", user=current_user)

@views.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    user_id = current_user.User_ID

    sent_parcels = Parcel.query.filter_by(Sender_User_ID=user_id).all()
    received_parcels = Parcel.query.filter_by(Recipient_User_ID=user_id).all()

    total_sent_parcels = len(sent_parcels)
    total_received_parcels = len(received_parcels)
    pending_parcels = sum(1 for parcel in received_parcels if parcel.Parcel_Received_at is None)

    feedbacks = session.get('feedbacks', {}).get(user_id, [])
    not_responded_feedback = sum(1 for feedback in feedbacks if feedback['admin_response'] == 'Not Responded')

    notifications = session.get('notifications', [])
    notifications = [{'message': msg} for msg in notifications]



    return render_template(
        'StudentStaff/StudentStaffDashboard.html',
        user=current_user,
        total_sent_parcels=total_sent_parcels,
        total_received_parcels=total_received_parcels,
        pending_parcels=pending_parcels,
        not_responded_feedback=not_responded_feedback,
        notifications=notifications
    )


@views.route('/submit_feedback', methods=['GET', 'POST'])
@login_required
def submit_feedback():
    feedbacks = session.get('feedbacks', {})
    if request.method == 'POST':
        content = request.form['content']
        feedback_type = request.form['feedback_type']

        if content:
            user_id = str(current_user.User_ID)  # Ensure consistent key type
            user_name = current_user.User_Name  

            # Initialize feedbacks storage if not present
            if 'feedbacks' not in session:
                session['feedbacks'] = {}

            # Ensure the user has a list to store multiple feedback entries
            if user_id not in session['feedbacks']:
                session['feedbacks'][user_id] = []

            # Append new feedback instead of overwriting
            session['feedbacks'][user_id].append({
                'name': user_name,  
                'content': content,
                'feedback_type': feedback_type,
                'admin_response': 'Not Responded'  # New field added
            })

            flash('Your feedback has been submitted successfully.', 'success')

    return render_template('StudentStaff/StudentStaffFeedback.html', feedbacks=feedbacks)


@parcel_manager.route('/assign_parcel_to_courier', methods=['GET', 'POST'])
def assign_parcel_to_courier():
    if request.method == 'POST':
        parcel_id = request.form.get('parcel_id')
        courier_id = request.form.get('courier_id')

        if not parcel_id or not courier_id:
            flash("Please select both a parcel and a courier!", "error")
            return redirect(url_for('parcel_manager.assign_parcel_to_courier'))

        parcel = Parcel.query.get(parcel_id)
        courier = Courier.query.get(courier_id)

        if parcel and courier:
            # Check if the parcel already has a delivery assigned
            if parcel.Delivery_ID:
                # Update the existing delivery record with the new courier_id
                delivery = Delivery.query.get(parcel.Delivery_ID)
                if delivery:
                    delivery.Courier_ID = courier.Courier_ID
                    db.session.commit()
                    flash(f"Parcel {parcel_id} reassigned to Courier {courier.Courier_ID} successfully!", "success")
                else:
                    flash(f"Delivery record not found for Parcel {parcel_id}!", "error")
            else:
                # Create a new delivery record
                new_delivery = Delivery(
                    Delivery_ID=f"D_{parcel_id}",  # Unique delivery ID (Example format)
                    Courier_ID=courier.Courier_ID,  # Assign to selected courier
                    Deliver_Date=None,  # Delivery date not set yet
                    Arrival_Date=None   # Arrival date not set yet
                )
                db.session.add(new_delivery)
                db.session.commit()

                # Assign the delivery to the parcel
                parcel.Delivery_ID = new_delivery.Delivery_ID
                db.session.commit()

                flash(f"Parcel {parcel_id} assigned to Courier {courier.Courier_ID} successfully!", "success")

            # Function to generate a unique Status_ID
            def generate_unique_status_id():
                while True:
                    status_id = f"PAR{''.join(random.choices('0123456789', k=8))}"
                    if not ParcelStatus.query.filter_by(Status_ID=status_id).first():
                        return status_id

            # Assign a unique Status_ID
            status_id = generate_unique_status_id()
            # Update the parcel status to "Assigned to Courier"
            new_status = ParcelStatus(
                Status_ID=status_id,
                Parcel_ID=parcel.Parcel_ID,
                Status_Type="Assigned to Courier",  # New status
                Updated_by=current_user.Manager_ID,
                Updated_At=datetime.utcnow()
            )
            db.session.add(new_status)
            db.session.commit()

            # Add a notification for the courier
            if 'courier_notifications' not in session:
                session['courier_notifications'] = {}

            courier_notifications = session['courier_notifications']
            if courier_id not in courier_notifications:
                courier_notifications[courier_id] = []

            courier_notifications[courier_id].append({
                'parcel_id': parcel_id,
                'message': f"Parcel {parcel_id} has been assigned to you.",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            session['courier_notifications'] = courier_notifications
            session.modified = True

        else:
            flash("Invalid parcel or courier selected!", "error")

        return redirect(url_for('parcel_manager.assign_parcel_to_courier'))

    # Get all parcels with status "Registered"
    parcels = db.session.query(Parcel).join(ParcelStatus).filter(ParcelStatus.Status_Type == 'Registered').all()
    
    # Fetch all couriers
    couriers = Courier.query.all()

    # Prepare the data to be passed to the template
    parcel_data = []
    for parcel in parcels:
        sender_name = parcel.sender.User_Name if parcel.sender else 'Unknown'
        recipient_name = parcel.recipient.User_Name if parcel.recipient else 'Unknown'
        destination = parcel.recipient.get_university_name() if parcel.recipient else 'Unknown'
        status = 'Registered'  # Since we filtered by "Registered" status

        parcel_data.append({
            'Parcel_ID': parcel.Parcel_ID,
            'Sender_Name': sender_name,
            'Recipient_Name': recipient_name,
            'Destination': destination,
            'Status': status
        })

    return render_template('ParcelManager/AssignParcelToCourier.html', parcels=parcel_data, couriers=couriers)

@views.route('/track_parcel', methods=['GET', 'POST'])
def track_parcel():
    if request.method == 'POST':
        parcel_id = request.form.get('parcel_id')

        latest_status = ParcelStatus.query.filter_by(Parcel_ID=parcel_id) \
                                          .order_by(ParcelStatus.Updated_At.desc()) \
                                          .first()
        if latest_status:
            parcel_info = {
                'parcel_id': latest_status.Parcel_ID,
                'status_type': latest_status.Status_Type,
                'updated_at': latest_status.Updated_At.strftime('%Y-%m-%d %H:%M:%S')  # 格式化时间
            }
            return render_template('StudentStaff/TrackParcel.html', parcel_info=parcel_info)
        else:
            return render_template('StudentStaff/TrackParcel.html', error="Parcel status not found.")

    return render_template('StudentStaff/TrackParcel.html')

@views.route('/notifications', methods=['GET'])
@login_required
def notifications():
    notifications = session.get('notifications', [])

    notifications = [{'message': msg} for msg in notifications]

    return render_template('StudentStaff/StudentStaffNotification.html', notifications=notifications)



@views.route('/report_locker_issue', methods=['GET', 'POST'])
@login_required
def report_locker_issue():
    if request.method == 'POST':
        locker_number = request.form['locker_number']
        issue_type = request.form['issue_type']
        issue_description = request.form.get('issue_description', '')

        # Store the issue in the session
        if 'locker_issues' not in session:
            session['locker_issues'] = []  # Initialize the list if not present

        issue = {
            'locker_number': locker_number,
            'issue_type': issue_type,
            'issue_description': issue_description,
            'reported_by': current_user.User_ID,
            'reported_at': datetime.utcnow().isoformat()
        }

        session['locker_issues'].append(issue)
        session.modified = True  # Ensure the session is marked as modified

        flash('Your issue has been reported successfully.', 'success')
        return redirect(url_for('views.home'))

    # GET method (Render the form page)
    lockers = SmartLocker.query.all()
    return render_template('StudentStaff/ReportLockerIssue.html', lockers=lockers)