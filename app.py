from flask import Flask, render_template, request, flash, redirect, url_for, session, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, inspect, text, exc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.types import Integer, String, VARCHAR, Float, DateTime
from datetime import datetime
import os
import psycopg2
from users import *
from creator import *
from art_piece import *
from transaction import *

#function written by Blake Dejohn
init_db()

@app.route("/", methods=['GET','POST'])
def index():
    session['admin'] = False
    if request.method == 'POST':
        #get the email and password from the form
        email = request.form['email']
        password = request.form['password']

        #find the user with the inputted email in the database
        user = users.query.filter_by(email=email).first()
        #if the user exists and the password is correct, log them in
        if user and user.password == password:
            # flash('You have been logged in', 'success')
            session["user_email"] = email
            session["user_password"] = password
            session["user_id"] = users.query.filter(users.email == email).first().user_id
            session["admin"] = users.query.filter(users.email == email).first().role == 'A'
            return redirect(url_for('home'))
        else:
            #if the user does not exist or the password is incorrect, flash an error message
            flash('Invalid email or password', 'danger')
            return render_template("index.html")
    return render_template("index.html")

# function to direct user to home after login
@app.route('/home')
def home():
    # Written by Kyle Easton
    if session['admin']:
        return render_template('home.html')
    else:
        return redirect(url_for('home_patron'))

# Written by Kyle Easton
@app.route('/home_patron')
def home_patron():
    return render_template('home_patron.html')


#this is the main function that runs the app
if __name__ == '__main__':
    app.run(debug = True)

