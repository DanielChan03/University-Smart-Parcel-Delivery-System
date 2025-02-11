from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_required
from .models import Admin, StudentStaff, Parcel, ParcelStatus, Waitlist, ParcelManager, Courier, db
from werkzeug.security import generate_password_hash
import random
from datetime import datetime
from sqlalchemy import func, and_

admin = Blueprint('admin', __name__)

# Admin Dashboard
@admin.route('/admin-dashboard')
@login_required
def admin_dashboard():
    if not isinstance(current_user, Admin):
            flash('Unauthorized access! Please log in as an admin.', category='error')
            return redirect(url_for('admin_auth.admin_login'))
    # Fetch notifications (unresponded feedback) from session
    notifications = session.get('feedbacks', {})  # Get feedbacks from session

    # Fetch parcel statistics
    total_received_parcels = Parcel.query.count()

    # Fetch delivered parcels (status type is "Delivered")
    total_delivered_parcels = db.session.query(ParcelStatus).filter_by(Status_Type='Delivered').count()

    # Fetch pending parcels (status type is not "Delivered")
    pending_parcels = db.session.query(ParcelStatus).filter(ParcelStatus.Status_Type != 'Delivered').count()

    # Count not responded feedback
    not_responded_feedback = len(notifications)  # Number of feedbacks in session

    return render_template(
        "Admin/AdminDashboard.html",
        admin=current_user,
        notifications=notifications,
        total_received_parcels=total_received_parcels,
        total_delivered_parcels=total_delivered_parcels,
        pending_parcels=pending_parcels,
        not_responded_feedback=not_responded_feedback
    )

# Generate Report
@admin.route('/generate-report', methods=['GET', 'POST'])
@login_required
def generate_report():
    if not isinstance(current_user, Admin):
        flash('Unauthorized access! Please log in as an admin.', category='error')
        return redirect(url_for('admin_auth.admin_login'))

    if request.method == 'POST':
        report_type = request.form.get('report_type')
        month = request.form.get('month')
        year = request.form.get('year')

        if report_type == 'monthly':
            return redirect(url_for('admin.monthly_summary_report', month=month, year=year))
        elif report_type == 'courier-activity':
            return redirect(url_for('admin.courier_activity_report', month=month, year=year))
        elif report_type == 'locker-usage':
            return redirect(url_for('admin.locker_usage_report', month=month, year=year))

    return render_template("Admin/AdminGenerateReport.html")

# Monthly Summary Report
@admin.route('/monthly-summary-report/<month>/<year>')
@login_required
def monthly_summary_report(month, year):
    if not isinstance(current_user, Admin):
        flash('Unauthorized access! Please log in as an admin.', category='error')
        return redirect(url_for('admin_auth.admin_login'))

    # Calculate total received parcels for the selected month and year
    total_received = Parcel.query.filter(
        func.extract('month', Parcel.Received_Date) == month,
        func.extract('year', Parcel.Received_Date) == year
    ).count()

    # Calculate total delivered parcels for the selected month and year
    total_delivered = ParcelStatus.query.filter(
        ParcelStatus.Status_Type == 'Delivered',
        func.extract('month', ParcelStatus.Status_Date) == month,
        func.extract('year', ParcelStatus.Status_Date) == year
    ).count()

    # Calculate pending parcels for the selected month and year
    pending_parcels = ParcelStatus.query.filter(
        ParcelStatus.Status_Type != 'Delivered',
        func.extract('month', ParcelStatus.Status_Date) == month,
        func.extract('year', ParcelStatus.Status_Date) == year
    ).count()

    # Calculate average delivery time (in days)
    avg_delivery_time = db.session.query(
        func.avg(func.julianday(ParcelStatus.Status_Date) - func.julianday(Parcel.Received_Date))
    ).filter(
        ParcelStatus.Status_Type == 'Delivered',
        func.extract('month', ParcelStatus.Status_Date) == month,
        func.extract('year', ParcelStatus.Status_Date) == year
    ).scalar()

    # Find the most active sender and recipient
    most_active_sender = db.session.query(
        Parcel.Sender_ID,
        StudentStaff.User_Name,
        func.count(Parcel.Parcel_ID).label('total')
    ).join(StudentStaff, Parcel.Sender_ID == StudentStaff.User_ID).filter(
        func.extract('month', Parcel.Received_Date) == month,
        func.extract('year', Parcel.Received_Date) == year
    ).group_by(Parcel.Sender_ID).order_by(func.count(Parcel.Parcel_ID).desc()).first()

    most_active_recipient = db.session.query(
        Parcel.Recipient_ID,
        StudentStaff.User_Name,
        func.count(Parcel.Parcel_ID).label('total')
    ).join(StudentStaff, Parcel.Recipient_ID == StudentStaff.User_ID).filter(
        func.extract('month', Parcel.Received_Date) == month,
        func.extract('year', Parcel.Received_Date) == year
    ).group_by(Parcel.Recipient_ID).order_by(func.count(Parcel.Parcel_ID).desc()).first()

    return render_template(
        "Admin/MonthlySummaryReport.html",
        total_received=total_received,
        total_delivered=total_delivered,
        pending_parcels=pending_parcels,
        avg_delivery_time=avg_delivery_time,
        most_active_sender=most_active_sender,
        most_active_recipient=most_active_recipient
    )

# Courier Activity Report
@admin.route('/courier-activity-report/<month>/<year>')
@login_required
def courier_activity_report(month, year):
    if not isinstance(current_user, Admin):
        flash('Unauthorized access! Please log in as an admin.', category='error')
        return redirect(url_for('admin_auth.admin_login'))

    # Fetch courier activity data
    courier_activity = db.session.query(
        Courier.Courier_Name,
        func.count(ParcelStatus.Parcel_ID).label('total_deliveries'),
        func.avg(func.julianday(ParcelStatus.Status_Date) - func.julianday(Parcel.Received_Date)).label('avg_delivery_time')
    ).join(ParcelStatus, ParcelStatus.Courier_ID == Courier.Courier_ID).join(
        Parcel, Parcel.Parcel_ID == ParcelStatus.Parcel_ID
    ).filter(
        ParcelStatus.Status_Type == 'Delivered',
        func.extract('month', ParcelStatus.Status_Date) == month,
        func.extract('year', ParcelStatus.Status_Date) == year
    ).group_by(Courier.Courier_ID).all()

    return render_template(
        "Admin/CourierActivityReport.html",
        courier_activity=courier_activity
    )

# Locker Usage Report
@admin.route('/locker-usage-report/<month>/<year>')
@login_required
def locker_usage_report(month, year):
    if not isinstance(current_user, Admin):
        flash('Unauthorized access! Please log in as an admin.', category='error')
        return redirect(url_for('admin_auth.admin_login'))

    # Fetch locker usage data
    locker_usage = db.session.query(
        Parcel.Locker_ID,
        Parcel.Locker_Location,
        func.count(Parcel.Parcel_ID).label('total_parcels'),
        Parcel.Locker_Status
    ).filter(
        func.extract('month', Parcel.Received_Date) == month,
        func.extract('year', Parcel.Received_Date) == year
    ).group_by(Parcel.Locker_ID).all()

    return render_template(
        "Admin/LockerUsageReport.html",
        locker_usage=locker_usage
    )

# Manage Users
@admin.route('/manage-users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if not isinstance(current_user, Admin):
        flash('Unauthorized access! Please log in as an admin.', category='error')
        return redirect(url_for('admin_auth.admin_login'))

    search_term = request.args.get('search', '')
    admin_uni_id = current_user.University_ID

    if search_term:
        users = StudentStaff.query.filter(
            ((StudentStaff.User_Name.ilike(f'%{search_term}%')) |
             (StudentStaff.User_Email.ilike(f'%{search_term}%'))) &
            (StudentStaff.University_ID == admin_uni_id)  
        ).all()
    else:
        users = StudentStaff.query.filter_by(University_ID=admin_uni_id).all()

    return render_template('Admin/AdminManageUser.html', users=users, search_term=search_term)

# Update User
@admin.route('/update-user/<string:user_id>', methods=['POST'])

def update_user(user_id):
    data = request.get_json()
    print("Received data:", data)  # Debugging: Log the received data

    if user:
        # Update User ID if it has changed
        new_user_id = data.get('User_ID')
        if new_user_id and new_user_id != user.User_ID:
            # Check if the new User ID already exists
            if StudentStaff.query.get(new_user_id):
                return jsonify({'success': False, 'message': 'User ID already exists.'})
            user.User_ID = new_user_id

        # Update other fields
        user.User_Name = data.get('User_Name', user.User_Name)
        user.User_Email = data.get('User_Email', user.User_Email)
        user.User_Contact = data.get('User_Contact', user.User_Contact)

        print("Updating user:", user.User_ID)  # Debugging: Log the user ID
        print("New Name:", user.User_Name)  # Debugging: Log the new name
        print("New Email:", user.User_Email)  # Debugging: Log the new email
        print("New Contact:", user.User_Contact)  # Debugging: Log the new contact

        db.session.commit()
        print("User updated successfully")  # Debugging: Log success
        flash('User updated successfully!', 'success')
        return jsonify({'success': True})
    else:
        print("User not found")  # Debugging: Log failure
        return jsonify({'success': False, 'message': 'User not found.'})

# Delete User
@admin.route('/delete-user/<string:user_id>', methods=['POST'])

def delete_user(user_id):
    
    user = StudentStaff.query.get(user_id)  # Replace with your user model

    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'User not found.'})

# View Feedback
@admin.route('/view-feedback', methods=['GET'])
@login_required

def view_feedback():
    if not isinstance(current_user, Admin):
            flash('Unauthorized access! Please log in as an admin.', category='error')
            return redirect(url_for('admin_auth.admin_login'))
    all_feedbacks = session.get('feedbacks', {})

    # Filter out only "Not Responded" feedbacks
    filtered_feedbacks = {
        user_id: [
            feedback for feedback in feedback_list if feedback.get('admin_response') == 'Not Responded'
        ]
        for user_id, feedback_list in all_feedbacks.items()
    }

    # Remove users with no pending feedback
    filtered_feedbacks = {user: fb for user, fb in filtered_feedbacks.items() if fb}

    return render_template('Admin/AdminViewFeedback.html', feedbacks=filtered_feedbacks)


# Admin route for responding to feedback
@admin.route('/respond_feedback/<user_id>/<int:feedback_index>', methods=['GET', 'POST'])
@login_required
def respond_feedback(user_id, feedback_index):
    if not isinstance(current_user, Admin):
            flash('Unauthorized access! Please log in as an admin.', category='error')
            return redirect(url_for('admin_auth.admin_login'))
    feedbacks = session.get('feedbacks', {})

    # Ensure feedback exists for the user
    if str(user_id) not in feedbacks or len(feedbacks[str(user_id)]) <= feedback_index:
        flash('Feedback not found!', 'danger')
        return redirect(url_for('admin.view_feedback'))
    
    # Get the feedback list for this user
    user_feedback_list = feedbacks[str(user_id)]
    
    if request.method == 'POST':
        response_content = request.form['response']

        # Update the feedback with admin's response
        user_feedback_list[feedback_index]['admin_response'] = response_content

        # Remove responded feedback from the list
       # user_feedback_list.pop(feedback_index)  

        # If user has no more feedback, remove them from session
        if not user_feedback_list:
            del feedbacks[str(user_id)]  # Remove user from feedbacks

        #  Reassign and mark session as modified
        session['feedbacks'] = feedbacks  
        session.modified = True  

        flash('Response has been submitted successfully.', 'success')
        return redirect(url_for('admin.view_feedback'))  # Redirect back to feedback view
    
    return render_template('Admin/AdminRespondFeedback.html', feedback=feedbacks[str(user_id)][feedback_index], user_id=user_id, feedback_index=feedback_index)



# Add User
@admin.route('/add-user', methods=['GET', 'POST'])
@login_required
def add_user():
    if not isinstance(current_user, Admin):
            flash('Unauthorized access! Please log in as an admin.', category='error')
            return redirect(url_for('admin_auth.admin_login'))
    if request.method == 'POST':
        user_type = request.form.get('userType')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        contact = request.form.get('contact')
        work_branch = request.form.get('workBranch')
        assigned_parcels = request.form.get('assignedParcels')

        # Generate a unique user ID
        if user_type == "ParcelManager":
            user_id = f"MGR{random.randint(100000, 999999)}"
            new_user = ParcelManager(
                Manager_ID=user_id,
                Manager_Name=name,
                Manager_Email=email,
                Manager_Password=generate_password_hash(password, method='pbkdf2:sha256'),
                Manager_Contact=contact,
                Manager_Work_Branch=work_branch
            )
        elif user_type == "Courier":
            user_id = f"COU{random.randint(100000, 999999)}"
            new_user = Courier(
                Courier_ID=user_id,
                Courier_Name=name,
                Courier_Email=email,
                Courier_Password=generate_password_hash(password, method='pbkdf2:sha256'),
                Courier_Contact=contact,
                Assigned_Parcels_Count=assigned_parcels
            )

        db.session.add(new_user)
        db.session.commit()
        flash('User added successfully!', 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template("Admin/AdminAddUser.html")