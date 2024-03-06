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
from flask import request


@app.route('/validate_session', methods=["POST"])
def validate_session():
    # Récupérer les données du corps de la requête
    data = request.json

    session_id = data.get('session_id')
    ip_address = data.get('ip_address')
    user_agent = data.get('user_agent')

    if not all([session_id, ip_address, user_agent]):
        return jsonify({"error": "Certains paramètres sont manquants."}), 400

    cursor = connection.cursor()

    # Requête pour la session id
    query = "SELECT user_id, expires_at, ip_address, user_agent FROM Sessions WHERE session_id = :session_id"
    cursor.execute(query, {'session_id': session_id})
    session_info = cursor.fetchone()

    if session_info:
        user_id, expires_at, stored_ip_address, stored_user_agent = session_info
        if expires_at and expires_at < datetime.now():
            return jsonify({"error": "Session expirée."}), 401
        elif stored_ip_address != ip_address:
            return jsonify({"error": "Adresse IP invalide."}), 401
        elif stored_user_agent != user_agent:
            return jsonify({"error": "User agent invalide."}), 401
        else:
            print("Session valide pour l'utilisateur:", user_id)
            # Prolonger la durée de la session
            update_query = (f"UPDATE Sessions SET expires_at = SYSTIMESTAMP + INTERVAL '{SESSION_LENGTH}' MINUTE WHERE "
                            f"session_id = '{session_id}'")

            cursor = connection.cursor()
            cursor.execute(update_query)
            connection.commit()
            return jsonify({"message": "Session valide pour l'utilisateur.", "user_id": user_id}), 200
    else:
        return jsonify({"error": "ID de session invalide."}), 401


# Valide les crédentiels de connexion et utilise l'addresse ip et user_agent
@app.route('/validate_login', methods=["POST"])
def validate_login():
    # Récupérer les données du corps de la requête
    data = request.json

    username = data.get('username')
    password = data.get('password')
    ip_address = data.get('ip_address')
    user_agent = data.get('user_agent')

    if not all([username, password, ip_address, user_agent]):
        return jsonify({"error": "Certains paramètres sont manquants."}), 400

    cursor = connection.cursor()

    # Hasher le mot de passe
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Requête pour l'utilisateur et son mot de passe
    query = "SELECT user_id FROM USERS WHERE username = :username AND password = :password"
    cursor.execute(query, {'username': username, 'password': hashed_password})
    user_id = cursor.fetchone()

    if user_id:
        session_id = generate_session_id()
        expiration_time = datetime.now() + timedelta(minutes=SESSION_LENGTH)

        # Insérer la nouvelle session dans la base de données
        insert_query = ("INSERT INTO Sessions (session_id, user_id, expires_at, ip_address, user_agent) VALUES ("
                        ":session_id, :user_id, :expires_at, :ip_address, :user_agent)")
        cursor.execute(insert_query, {'session_id': session_id, 'user_id': user_id[0], 'expires_at': expiration_time,
                                      'ip_address': ip_address, 'user_agent': user_agent})
        connection.commit()

        return jsonify({"session_id": session_id}), 200
    else:
        return jsonify({"error": "Crédentiels invalides."}), 401
