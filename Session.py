import secrets
import string
from __main__ import app, connexion
import oracledb
from flask import request, abort, jsonify

# In minutes
SESSION_LENGTH = 15

def generate_session_id(length=64):
    alphabet = string.ascii_letters + string.digits + '-_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def validate_session(session_id, ip_address, user_agent):
    cursor = connection.cursor()
    query = "SELECT user_id, expires_at FROM Sessions WHERE session_id = :session_id"
    cursor.execute(query, {'session_id': session_id})
    session_info = cursor.fetchone()

    if session_info:
        user_id, expires_at, stored_ip_address, stored_user_agent = session_info
        if expires_at and expires_at < datetime.now():
            print("Session has expired.")
            return False
        elif stored_ip_address != ip_address:
            print("IP address does not match.")
            return False
        elif stored_user_agent != user_agent:
            print("User agent does not match.")
            return False
        else:
            print("Session is valid for user:", user_id)
            update_query = """
                UPDATE Sessions
                SET length = CURRENT_TIMESTAMP + INTERVAL :session_length MINUTE
                WHERE session_id = :session_id
            """
            cursor.execute(update_query, {'session_length': SESSION_LENGTH, 'session_id': session_id})
            connection.commit()
            return True
    else:
        print("Invalid session ID.")
        return False


# Function to validate login credentials and create a new session
def validate_login(username, password, ip_address, user_agent):
    cursor = connection.cursor()

    # Hash the provided password using SHA-256
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Fetch user ID for the provided username and hashed password
    query = "SELECT user_id FROM USERS WHERE username = :username AND password = :password"
    cursor.execute(query, {'username': username, 'password': hashed_password})
    user_id = cursor.fetchone()

    if user_id:
        # Generate a new session ID
        session_id = generate_session_id()

        # Calculate session expiration time
        expiration_time = datetime.now() + timedelta(minute=SESSION_LENGTH)

        # Insert the new session into the Sessions table
        insert_query = "INSERT INTO Sessions (session_id, user_id, expires_at, ip_address, user_agent) VALUES (:session_id, :user_id, :expires_at, :ip_address, :user_agent)"
        cursor.execute(insert_query, {'session_id': session_id, 'user_id': user_id[0], 'expires_at': expiration_time, 'ip_address': ip_address, 'user_agent': user_agent})
        connection.commit()

        # Return the session ID
        return session_id
    else:
        # If login failed, return None
        return None


# Function to create a new user with encrypted password
def create_user(username, password, role_name, email):
    cursor = connection.cursor()

    # Check if the username is already taken
    query = "SELECT COUNT(*) FROM USERS WHERE username = :username"
    cursor.execute(query, {'username': username})
    user_exists = cursor.fetchone()[0]

    if user_exists:
        print("Username already exists.")
        return False
    else:
        # Hash the password using SHA-256
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Insert the new user into the USERS table
        insert_query = "INSERT INTO USERS (username, password, role_name, email) VALUES (:username, :password, :role_name, :email)"
        cursor.execute(insert_query, {'username': username, 'password': hashed_password, 'role_name': role_name, 'email': email})
        connection.commit()
        print("User created successfully.")
        return True