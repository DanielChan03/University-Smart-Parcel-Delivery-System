from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_required
from .models import  Parcel, ParcelStatus,Waitlist, ParcelManager, Courier, SmartLocker, db
from werkzeug.security import generate_password_hash
import random

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
                flash(f"Parcel {parcel_id} is already assigned!", "warning")
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
        else:
            flash("Invalid parcel or courier selected!", "error")

        return redirect(url_for('parcel_manager.assign_parcel_to_courier'))

    # Get all unassigned parcels (where Delivery_ID is NULL)
    parcels = Parcel.query.filter(Parcel.Delivery_ID.is_(None)).all()
    couriers = Courier.query.all()

    return render_template('ParcelManager/AssignParcelToCourier.html', parcels=parcels, couriers=couriers)

    
    

