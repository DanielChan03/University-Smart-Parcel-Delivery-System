from flask import Blueprint, render_template, request, jsonify
from datetime import datetime, date
from flask_login import current_user, login_required
from sqlalchemy import func
from webapp.models import Delivery, Parcel, ParcelStatus,StudentStaff,University, db
import random

collect_parcel_bp = Blueprint('collect_parcel', __name__)

# Collect parcel
@collect_parcel_bp.route('/collect-parcel', methods=['GET', 'POST'])
@login_required
def collect_parcel():
    if request.method == 'POST':
        # Handle POST request to update parcel status
        data = request.get_json()
        collected_parcels = data.get('collectedParcels', [])
        uncollected_parcels = data.get('uncollectedParcels', [])

        # Handle collected parcels (Ready to Pickup to Parcel Collected)
        for parcel_id in collected_parcels:
            # Check the latest status of the parcel
            latest_status = ParcelStatus.query.filter_by(Parcel_ID=parcel_id).order_by(ParcelStatus.Updated_At.desc()).first()
            if latest_status and latest_status.Status_Type != 'Parcel Collected':
                # Generate a unique status ID
                new_status_id = f"COL{random.randint(100000, 999999)}"
                while db.session.query(ParcelStatus).filter_by(Status_ID=new_status_id).first():
                    new_status_id = f"COL{random.randint(100000, 999999)}"  # Regenerate until unique

                # Create a new status entry for Parcel Collected
                new_status_entry = ParcelStatus(
                    Status_ID=new_status_id,
                    Parcel_ID=parcel_id,
                    Status_Type='Parcel Collected',
                    Updated_by=current_user.Courier_ID,
                    Updated_At=datetime.now()
                )
                db.session.add(new_status_entry)

        # Handle uncollected parcels (Parcel Collected to Ready to Pickup)
        for parcel_id in uncollected_parcels:
            # Check if the current status is "Parcel Collected"
            latest_status = ParcelStatus.query.filter_by(Parcel_ID=parcel_id).order_by(ParcelStatus.Updated_At.desc()).first()

            if latest_status and latest_status.Status_Type == 'Parcel Collected':
                # Delete the latest "Parcel Collected" status entry
                db.session.delete(latest_status)

        db.session.commit()  # Commit all status updates
        return jsonify({'success': True})

    # Handle GET request to render the page
    search_date = request.args.get('searchDate')  # Get searchDate from query parameters

    if search_date:
        # Convert the string to a date object
        search_date = datetime.strptime(search_date, '%Y-%m-%d').date()

        deliveries = Delivery.query.filter(
            func.date(Delivery.Deliver_Date) == search_date,
            Delivery.Courier_ID == current_user.Courier_ID
            ).all()
        
        if not deliveries:
            return jsonify({'message': 'No deliveries found for this date'})
        
    else:
        # Query deliveries for the current courier until today (default if no searchDate is provided)
        deliveries = Delivery.query.filter_by(Courier_ID=current_user.Courier_ID)\
            .filter(Delivery.Deliver_Date <= date.today())\
            .order_by(Delivery.Deliver_Date.desc()).all()  # Get all deliveries until today

    # Prepare the data for the frontend
    delivery_data = []
    for delivery in deliveries:
        # Query the parcels associated with each delivery
        parcels = Parcel.query.filter_by(Delivery_ID=delivery.Delivery_ID).order_by(Parcel.Parcel_ID.asc()).all()

        parcel_data = []
        for parcel in parcels:
            # Get the most recent status for the parcel
            latest_status = ParcelStatus.query.filter_by(Parcel_ID=parcel.Parcel_ID).order_by(ParcelStatus.Updated_At.desc()).first()

            # If a status update exists, use it; otherwise, use 'Not Updated'
            status = latest_status.Status_Type if latest_status else 'Not Updated'

            # Get recipient details
            recipient = StudentStaff.query.filter_by(User_ID=parcel.Recipient_User_ID).first()
            if recipient:
                university = University.query.filter_by(University_ID=recipient.University_ID).first()
                destination = university.University_Name if university else 'University Not Found'
            else:
                destination = 'Recipient information not found'

            parcel_data.append({
                'Parcel_ID': parcel.Parcel_ID,
                'Sender': parcel.sender.User_Name,
                'Recipient': recipient.User_Name if recipient else 'Unknown',
                'Destination': destination,
                'Status': status,
            })

        # Append the parcel data to the respective delivery
        delivery_data.append({
            'Delivery_ID': delivery.Delivery_ID,
            'Delivery_Date': delivery.Deliver_Date,
            'Parcels': parcel_data
        })

    # Return JSON for AJAX requests
    if request.args.get('searchDate'):
        return jsonify({'deliveries': delivery_data})
    else:
        return render_template("Courier/CourierCollectParcel.html", deliveries=delivery_data)
