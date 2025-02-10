from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_required
from .models import  Parcel, ParcelStatus, Waitlist, ParcelManager, Courier, SmartLocker, Delivery, db
from werkzeug.security import generate_password_hash
import random
import string
from datetime import datetime  # Import the datetime class
from sqlalchemy.orm.exc import NoResultFound


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

    return render_template(
        "ParcelManager/ParcelManagerDashboard.html",
        parcel_manager = current_user,
        notifications = notifications,
        total_received_parcels = total_received_parcels,
        total_delivered_parcels = total_delivered_parcels,
        pending_parcels = pending_parcels,
        locker_status = locker_status
    )

@parcel_manager.route('/organize-parcel', methods=['GET', 'POST'])
def organize_parcel():
    parcels = Parcel.query.all()
    statuses = ParcelStatus.query.all()
    deliveries = Delivery.query.all()
    couriers = Courier.query.all()

    if request.method == 'POST':
        selectedParcel = request.form.getlist('selected_parcels[]')
        courierID = request.form.get('courier_id')
        deliveryDate = request.form.get('delivery_date')

        if selectedParcel and courierID and deliveryDate:
            delivery_id = 'D_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            newDelivery = Delivery(Delivery_ID = delivery_id,
                                   Courier_ID = courierID,
                                   Deliver_Date = datetime.strptime(deliveryDate, '%Y-%m-%d')
                                    )

            for parcelID in selectedParcel:
                parcel = Parcel.query.filter_by(Parcel_ID = parcelID).first()
                if parcel:
                    newDelivery.parcels.append(parcel)

            db.session.add(newDelivery)
            db.session.commit()

            flash(f"New delivery created with ID {delivery_id}!", category="success")
    
        else:
            flash("No parcel selected!", category="error")

        return redirect(url_for('parcel_manager.organize_parcel'))

    return render_template(
        'ParcelManager/ParcelManagerOrganizeParcel.html',
        parcels = parcels,
        statuses = statuses,
        deliveries = deliveries,
        couriers = couriers
        )

@parcel_manager.route('/update_parcel_status', methods=['GET', 'POST'])
def update_parcel_status():
    # Fetch all parcels from database
    parcels = Parcel.query.all()
    statuses = ParcelStatus.query.all()


    if request.method == 'POST':
        parcelID = request.form['Parcel_ID']
        updateStatus = request.form.get('Update_Status')

        try:
            # Find the existing parcel status record
            parcel_status = ParcelStatus.query.filter_by(Parcel_ID=parcelID).first()

            if parcel_status:
                # Update the status type and timestamp
                parcel_status.Status_Type = updateStatus
                parcel_status.Updated_by = current_user.Manager_ID  # Make sure this attribute exists
                parcel_status.Updated_At = datetime.utcnow()
            db.session.commit()

            flash('Parcel status updated successfully!', category='success')

            return redirect(url_for('parcel_manager.update_parcel_status'))


        except NoResultFound:
            pass

    return render_template(
        'ParcelManager/ParcelManagerUpdateParcelStatus.html', 
        parcels = parcels, 
        statuses = statuses,
        )

@parcel_manager.route('/monitor_locker_issue', methods=['GET', 'POST'])
def monitor_locker_issue():
    # Get search query
    lockerFilter = request.args.get('filter')

    if lockerFilter:
        lockers = SmartLocker.query.filter(SmartLocker.Locker_ID.ilike(f'%{lockerFilter}%')).all()
    else:
        lockers = SmartLocker.query.all()
    
    return render_template(
        "ParcelManager/ParcelManagerMonitorLockerIssue.html",
        lockers = lockers
    )


@parcel_manager.route('/log_arrival_parcel', methods=['GET', 'POST'])
def log_arrival_parcel():
    parcels = Parcel.query.all()
    statuses = ["Verified", "Missing"]

    if request.method == 'POST':
        parcelID = request.form.get('Parcel_ID')      
        updateStatus = request.form.get('Update_Status')

        try:
            # Find the existing parcel status record
            parcel_status = ParcelStatus.query.filter_by(Parcel_ID=parcelID).first()

            if parcel_status:
                # Update the status type and timestamp
                parcel_status.Status_Type = updateStatus
                parcel_status.Updated_by = current_user.Manager_ID  # Make sure this attribute exists
                parcel_status.Updated_At = datetime.utcnow()
                db.session.commit()
    
                flash('Parcel status updated successfully!', category='success')
                
            else:
                flash('Parcel status not found!', category='error')
                
            return redirect(url_for('parcel_manager.log_arrival_parcel'))


        except NoResultFound:
            pass

    return render_template(
        'ParcelManager/ParcelManagerLogArrivalParcel.html',
        parcels = parcels,
        statuses = statuses,
        )

