from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_required
from .models import Admin, StudentStaff, Parcel, ParcelStatus,Waitlist, ParcelManager, Courier, db
from werkzeug.security import generate_password_hash
import random

admin = Blueprint('admin', __name__)

# Admin Dashboard
@admin.route('/admin-dashboard')
def admin_dashboard():

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
@admin.route('/generate-report', methods=['GET'])
@login_required
def generate_report():
    return render_template("Admin/AdminGenerateReport.html")

# Manage Users
@admin.route('/manage-users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if not isinstance(current_user, Admin):
        flash('Unauthorized access! Please log in as an admin.', category='error')
        return redirect(url_for('auth.admin_login'))

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
    feedbacks = session.get('feedbacks', {})
    return render_template('Admin/AdminViewFeedback.html', feedbacks=feedbacks)

# Admin route for responding to feedback
@admin.route('/respond_feedback/<user_id>/<int:feedback_index>', methods=['GET', 'POST'])
@login_required
def respond_feedback(user_id, feedback_index):
    feedbacks = session.get('feedbacks', {})

    # Ensure feedback exists for the user
    if str(user_id) not in feedbacks or len(feedbacks[str(user_id)]) <= feedback_index:
        flash('Feedback not found!', 'danger')
        return redirect(url_for('admin.view_feedback'))
    
    # Get the feedback item the admin will respond to
    feedback = feedbacks[str(user_id)][feedback_index]

    if request.method == 'POST':
        response_content = request.form['response']
        
        # Update the feedback with admin's response
        feedback['admin_response'] = response_content  # Store the response

        flash('Response has been submitted successfully.', 'success')

        # Save the updated feedback back to session
        session['feedbacks'][str(user_id)][feedback_index] = feedback

        return redirect(url_for('admin.view_feedback'))  # Redirect back to feedback view page
    
    return render_template('Admin/AdminRespondFeedback.html', feedback=feedback, user_id=user_id, feedback_index=feedback_index)


# Add User
@admin.route('/add-user', methods=['GET', 'POST'])
@login_required
def add_user():
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