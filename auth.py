from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['POST'])
def login():
    db = current_app.config["db"]
    username = request.form.get('username')
    password = request.form.get('password')
    user = db.users.find_one({'username': username})
    if user and check_password_hash(user['password'], password):
        session['username'] = username  # Store username in session
        return jsonify({'status': 'login successful'})
    else:
        return jsonify({'status': 'login failed'}), 401

@auth.route('/signup', methods=['POST'])
def signup():
    db = current_app.config["db"]
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    # Check if username already exists
    if db.users.find_one({'username': username}):
        return jsonify({'status': 'username already exists'}), 400
    hashed_pw = generate_password_hash(password)
    db.users.insert_one({'username': username, 'password': hashed_pw, 'email': email})
    session['username'] = username  # Automatically log in the user after signup
    return jsonify({'status': 'signup successful'})
