from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
from flask_login import login_required, current_user
from . import db
import random
from .models import Parcel, SmartLocker, University, StudentStaff, ParcelManager, Delivery  # Ensure these models are imported

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    return render_template("home.html", user=current_user)

@views.route('/submit_feedback', methods=['GET', 'POST'])
def submit_feedback():
    if request.method == 'POST':
        content = request.form['content']
        feedback_type = request.form['feedback_type']

        if content:
            user_id = current_user.User_ID  
            user_name = current_user.User_Name 
            
            # Store the feedback with the user ID in the session (temporary storage)
            if 'feedbacks' not in session:
                session['feedbacks'] = {}  # Initialize feedbacks if not present
            session['feedbacks'][str(user_id)] = {
                'name': user_name,  
                'content': content,
                'feedback_type': feedback_type
            }
            
            flash('Your feedback has been submitted successfully.', 'success')

    return render_template('StudentStaffFeedback.html')

@views.route('/send_parcel', methods=['GET', 'POST'])
@login_required
def send_parcel():
    universities = University.query.all()

    # Ensure current_user has the university relationship loaded
    sender = StudentStaff.query.filter_by(User_ID=current_user.User_ID).first()

    sender_university_name = sender.get_university_name()
    sender_university_prefix = sender.get_university_prefix()

    receiver_users = StudentStaff.query.all()

    if request.method == 'POST':
        sender_user_id = request.form['sender_user_id']
        receiver_user_id = request.form['receiver_user_id']
        sender_university_id = request.form['sender_university']
        receiver_university_id = request.form['receiver_university']

        # Generate a unique Delivery_ID
        delivery_id = f"DEL{''.join(random.choices('0123456789', k=8))}"

        # Check if the Delivery_ID already exists in the delivery table
        while Delivery.query.filter_by(Delivery_ID=delivery_id).first():
            delivery_id = f"DEL{''.join(random.choices('0123456789', k=8))}"

        # Create a new delivery entry
        new_delivery = Delivery(
            Delivery_ID=delivery_id,
            Courier_ID=None,  # You can set this later when a courier is assigned
            Deliver_Date=None,  # Set this when the parcel is collected by the courier
            Arrival_Date=None  # Set this when the parcel arrives at the destination
        )
        db.session.add(new_delivery)
        db.session.commit()

        available_locker = SmartLocker.query.filter(
            SmartLocker.Locker_Status == 'Available', 
            SmartLocker.Locker_ID.like(f"{sender_university_prefix}%")  # Match prefix
        ).first()

        if available_locker:
            send_locker_id = available_locker.Locker_ID
            available_locker.Locker_Status = 'Occupied'
            db.session.commit()

            # Get the sender's manager
            send_manager = ParcelManager.query.filter_by(Manager_Work_Branch=sender_university_name).first()

            # Get the receiver's university name
            receiver = StudentStaff.query.filter_by(User_ID=receiver_user_id).first()
            receiver_university_name = receiver.get_university_name()

            # Get the receiver's manager
            receive_manager = ParcelManager.query.filter_by(Manager_Work_Branch=receiver_university_name).first()

            if send_manager is None or receive_manager is None:
                flash('No manager found for the sender or receiver university. Please contact support.', 'error')
                return redirect(url_for('views.send_parcel'))

            new_parcel = Parcel(
                Parcel_ID= f"PAR{''.join(random.choices('0123456789', k=8))}",
                Sender_User_ID=sender_user_id,
                Recipient_User_ID=receiver_user_id,
                Send_Locker_ID=send_locker_id,
                Receive_Locker_ID=None,  # This will be set when the parcel is received
                Delivery_ID=delivery_id,  # Use the Delivery_ID created above
                Parcel_Sent_at=datetime.utcnow(),
                Send_Manager_ID=send_manager.Manager_ID,
                Receive_Manager_ID=receive_manager.Manager_ID  # Set the receive manager
            )
            db.session.add(new_parcel)
            db.session.commit()

            flash(f'Please send your parcel to Locker ID: {send_locker_id}.', 'success')
            return redirect(url_for('views.send_parcel'))

        else:
            flash('No available lockers. Please try again later.', 'error')
            return redirect(url_for('views.send_parcel'))

    return render_template(
        'SendParcel.html',
        user=sender,
        universities=universities,
        all_users=receiver_users,
        sender_university_name=sender.get_university_name()  # Pass the university name
    )

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
    return render_template('ReportLockerIssue.html', lockers=lockers)





