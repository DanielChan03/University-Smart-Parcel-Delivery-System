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
    return render_template("StudentStaff/home.html", user=current_user)

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

@views.route('/send_parcel', methods=['GET', 'POST'])
@login_required
def send_parcel():
    # Get all universities for the dropdown
    universities = University.query.all()
    sender = StudentStaff.query.filter_by(User_ID=current_user.User_ID).first()
    sender_university_id = sender.University_ID  # Get sender's university ID

    if request.method == 'POST':
        sender_user_id = request.form['sender_user_id']
        receiver_identifier = request.form['receiver_identifier']
        receiver_university_id = request.form['receiver_university']

        # Ensure the sender and receiver are not the same person
        if str(receiver_identifier) == str(sender_user_id):
            flash('You cannot send a parcel to yourself.', 'error')
            return redirect(url_for('views.send_parcel'))

        # Ensure the sender and receiver are from different universities
        if str(receiver_university_id) == str(sender_university_id):
            flash('Receiver cannot be from the same university as the sender.', 'error')
            return redirect(url_for('views.send_parcel'))

        # Try to find the receiver by name first
        receiver = StudentStaff.query.filter_by(User_Name=receiver_identifier, University_ID=receiver_university_id).first()

        # If not found by name, try to find by user ID
        if not receiver:
            receiver = StudentStaff.query.filter_by(User_ID=receiver_identifier, University_ID=receiver_university_id).first()

        # Ensure receiver exists in the selected university
        if receiver is None:
            flash('Receiver not found in the selected university. Please check the name or user ID.', 'error')
            return redirect(url_for('views.send_parcel'))

        receiver_user_id = receiver.User_ID  # Receiver's User ID

        # Find an available locker at the sender's university
        sender_university_prefix = sender.get_university_prefix()
        available_locker = SmartLocker.query.filter(
            SmartLocker.Locker_Status == 'Available',
            SmartLocker.Locker_ID.like(f"{sender_university_prefix}LOC%")
        ).first()

        if not available_locker:
            flash('No available lockers. Please try again later.', 'error')
            return redirect(url_for('views.send_parcel'))

        # Locker found, update the status
        send_locker_id = available_locker.Locker_ID
        available_locker.Locker_Status = 'Occupied'
        db.session.commit()

        # Generate a unique Delivery_ID
        delivery_id = f"DEL{''.join(random.choices('0123456789', k=8))}"

        # Ensure the Delivery_ID is unique
        while Delivery.query.filter_by(Delivery_ID=delivery_id).first():
            delivery_id = f"DEL{''.join(random.choices('0123456789', k=8))}"

        # Create a new delivery entry
        new_delivery = Delivery(
            Delivery_ID=delivery_id,
            Courier_ID=None,
            Deliver_Date=None,
            Arrival_Date=None
        )
        db.session.add(new_delivery)
        db.session.commit()

        # Get sender's manager
        sender_university_name = sender.get_university_name()
        send_manager = ParcelManager.query.filter_by(Manager_Work_Branch=sender_university_name).first()

        if send_manager is None:
            flash('No manager found for the sender university. Please contact support.', 'error')
            return redirect(url_for('views.send_parcel'))

        # Get receiver's university name
        receiver_university = University.query.get(receiver_university_id)
        receiver_university_name = receiver_university.University_Name

        # Get receiver's manager
        receive_manager = ParcelManager.query.filter_by(Manager_Work_Branch=receiver_university_name).first()

        if receive_manager is None:
            flash('No manager found for the receiver university. Please contact support.', 'error')
            return redirect(url_for('views.send_parcel'))

        # Create a new parcel entry
        new_parcel = Parcel(
            Parcel_ID=f"PAR{''.join(random.choices('0123456789', k=8))}",
            Sender_User_ID=sender_user_id,
            Recipient_User_ID=receiver_user_id,
            Send_Locker_ID=send_locker_id,
            Receive_Locker_ID=None,
            Delivery_ID=delivery_id,
            Parcel_Sent_at=datetime.utcnow(),
            Send_Manager_ID=send_manager.Manager_ID,
            Receive_Manager_ID=receive_manager.Manager_ID
        )
        db.session.add(new_parcel)
        db.session.commit()

        flash(f'Your parcel has been sent. Please place it in Locker ID: {send_locker_id}.', 'success')
        return redirect(url_for('views.send_parcel'))

    return render_template(
        'StudentStaff/SendParcel.html',
        user=sender,
        universities=universities,
        sender_university_name=sender.get_university_name()
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
    return render_template('StudentStaff/ReportLockerIssue.html', lockers=lockers)