import secrets
import string
from __main__ import app, connection
from datetime import datetime
import bcrypt

import oracledb
from flask import request, jsonify

# In minutes
SESSION_LENGTH = 15


def generate_session_id(length=64):
    alphabet = string.ascii_letters + string.digits + '-_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# Vérifie qu'une session est valide
def validate_session(session_id, ip_address, user_agent):
    if not all([session_id, ip_address, user_agent]):
        return jsonify({"error": "Certains paramètres sont manquants."}), 400

    cursor = connection.cursor()

    # Requête pour la session id
    query = "SELECT user_id, expires_at, ip_address, user_agent FROM Sessions WHERE session_id = :session_id"
    cursor.execute(query, {'session_id': session_id})
    session_info = cursor.fetchone()

    if session_info is not None:
        expires_at, stored_ip_address, stored_user_agent = session_info
        if expires_at and expires_at < datetime.now():
            return jsonify({"error": "Session expirée."}), 401
        elif stored_ip_address != ip_address:
            return jsonify({"error": "Adresse IP invalide."}), 401
        elif stored_user_agent != user_agent:
            return jsonify({"error": "User agent invalide."}), 401
        else:
            # Prolonge la durée de la session
            update_query = (f"UPDATE Sessions SET expires_at = SYSTIMESTAMP + INTERVAL '{SESSION_LENGTH}' MINUTE WHERE "
                            f"session_id = '{session_id}'")

            cursor = connection.cursor()
            cursor.execute(update_query)
            connection.commit()
            cursor.close()
            return jsonify({"message": "Valide"}), 200
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

    # Requête pour l'utilisateur et son mot de passe
    query = f"SELECT user_id, password FROM USERS WHERE username = '{username}'"
    cursor.execute(query)
    data = cursor.fetchone()

    if not data or bcrypt.checkpw(password, data[1]):
        return jsonify({"error": "Crédentiels invalide"}), 200

    user_id = data[0]
    if user_id:
        session_id = generate_session_id()

        # Insérer la nouvelle session dans la base de données
        insert_query = (
            "INSERT INTO Sessions (session_id, user_id, expires_at, ip_address, user_agent) "
            f"VALUES ('{session_id}', {user_id}, SYSTIMESTAMP + INTERVAL '{SESSION_LENGTH}' MINUTE, '{ip_address}', '{user_agent}')"
        )

        cursor.execute(insert_query)
        connection.commit()
        cursor.close()

        return jsonify({"session_id": session_id}), 200
    else:
        return jsonify({"error": "Crédentiels invalides."}), 401


@app.route("/get_permissions", methods=["GET"])
def get_permissions(session_id):
    session_id = request.args.get('session_id')
    cursor = connection.cursor()

    # Retourne les permissions de l'utilisateur
    perm_query = (f"SELECT rp.permission_name"
                  "FROM SESSIONS s"
                  "JOIN USERS u ON s.user_id = u.user_id"
                  "JOIN ROLES r on u.user_id = r.user_id"
                  "JOIN ROLE_PERMISSIONS rp ON r.role_name = rp.role_name"
                  f"WHERE s.session_id = '{session_id}'")
    cursor.execute(perm_query)
    return cursor.fetchall()
