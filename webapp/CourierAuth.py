from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from .models import Courier
from . import db

courier_auth = Blueprint('courier_auth', __name__)

# Courier Login
@courier_auth.route('/courier-login', methods=['GET', 'POST'])
def courier_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the user is a Courier
        courier = Courier.query.filter_by(Courier_Email=email).first()
        if courier:
            if check_password_hash(courier.Courier_Password, password):
                flash('Logged in successfully as Courier!', category='success')
                login_user(courier, remember=True)
                return render_template("CourierDashBoard.html")
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("CourierLogin.html")

# Courier Logout
@courier_auth.route('/courier-logout')
@login_required
def courier_logout():
    logout_user()
    flash('Logged out successfully.', category='success')
    return render_template("CourierLogin.html")