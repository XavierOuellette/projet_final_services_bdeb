import hashlib
import secrets
import string
from __main__ import app, connection
from datetime import datetime, timedelta

import oracledb
from flask import request, abort, jsonify

# In minutes
SESSION_LENGTH = 15


def generate_session_id(length=64):
    alphabet = string.ascii_letters + string.digits + '-_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# Valide la session avec son id, ip_address et user_agent
@app.route('/validate_session', methods=["POST"])
def validate_session(session_id, ip_address, user_agent):
    cursor = connection.cursor()

    # Requête pour la session id
    query = "SELECT user_id, expires_at FROM Sessions WHERE session_id = :session_id"
    cursor.execute(query, {'session_id': session_id})
    session_info = cursor.fetchone()

    if session_info:
        user_id, expires_at, stored_ip_address, stored_user_agent = session_info
        if expires_at and expires_at < datetime.now():
            print("Session has expired.")
            # TODO: Implémenter
            return False
        elif stored_ip_address != ip_address:
            print("IP address does not match.")
            # TODO: Implémenter
            return False
        elif stored_user_agent != user_agent:
            print("User agent does not match.")
            # TODO: Implémenter
            return False
        else:
            print("Session is valid for user:", user_id)
            # Prolonge la durée de la session
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
        # TODO: Implémenter
        return False


# Valide les crédentiels de connexion et utilise l'addresse ip et user_agent
@app.route('/validate_login', methods=["POST"])
def validate_login(username, password, ip_address, user_agent):
    cursor = connection.cursor()

    # Hash le mot de passe
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Requête pour l'utilisateur et son mot de passe
    query = "SELECT user_id FROM USERS WHERE username = :username AND password = :password"
    cursor.execute(query, {'username': username, 'password': hashed_password})
    user_id = cursor.fetchone()

    if user_id:
        session_id = generate_session_id()
        expiration_time = datetime.now() + timedelta(minutes=SESSION_LENGTH)

        # Insère la nouvelle session dans la base de données
        insert_query = ("INSERT INTO Sessions (session_id, user_id, expires_at, ip_address, user_agent) VALUES ("
                        ":session_id, :user_id, :expires_at, :ip_address, :user_agent)")
        cursor.execute(insert_query, {'session_id': session_id, 'user_id': user_id[0], 'expires_at': expiration_time,
                                      'ip_address': ip_address, 'user_agent': user_agent})
        connection.commit()

        return session_id
    else:
        # TODO: Implémenter
        return None
