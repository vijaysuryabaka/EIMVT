from flask import Blueprint, request, session, redirect, url_for, flash, current_app, render_template
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['POST'])
def login():
    db = current_app.config["db"]
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Please enter both username and password.', 'error')
        return redirect('/user')

    user = db.users.find_one({'username': username})
    if user and 'password' in user and check_password_hash(user['password'], password):
        session['username'] = username  # Store username in session
        return redirect(url_for('main'))
    else:
        flash('Invalid username or password.', 'error')
        return redirect('/user')

@auth.route('/signup', methods=['POST'])
def signup():
    db = current_app.config["db"]
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    
    # Check if username already exists
    if db.users.find_one({'username': username}):
        flash('Username already exists. Please choose a different one.', 'error')
        return redirect(url_for('signup'))

    hashed_pw = generate_password_hash(password)
    db.users.insert_one({'username': username, 'password': hashed_pw, 'email': email})
    session['username'] = username
    
    # Redirect after successful signup, optionally to a user preferences page
    return redirect('/user-prefer') # Assuming you have a view function for user preferences

@auth.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    return render_template('main.html')
