import secrets
import string
from __main__ import app, connection
from datetime import datetime
from flask import request, jsonify
from Main import bcrypt

# In minutes
SESSION_LENGTH = 15


def generate_session_id(length=64):
    alphabet = string.ascii_letters + string.digits + '-_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# Vérifie qu'une session est valide
def validate_session(session_id, ip_address, user_agent):
    if not all([session_id, ip_address, user_agent]):
        return {"error": "Certains paramètres sont manquants."}

    cursor = connection.cursor()

    # Requête pour la session id
    query = "SELECT expires_at, ip_address, user_agent FROM Sessions WHERE session_id = :session_id"
    cursor.execute(query, {'session_id': session_id})
    session_info = cursor.fetchone()

    if session_info is None:
        return {"error": "Session invalide"}

    expires_at, stored_ip_address, stored_user_agent = session_info

    if expires_at < datetime.now() + datetime.hour(5) or stored_ip_address != ip_address or stored_user_agent != user_agent:
        return {"error": "Session invalide"}
    else:
        # Prolonge la durée de la session
        update_query = (f"UPDATE Sessions SET expires_at = SYSTIMESTAMP + INTERVAL '{SESSION_LENGTH}' MINUTE WHERE "
                        f"session_id = '{session_id}'")

        cursor = connection.cursor()
        cursor.execute(update_query)
        connection.commit()
        cursor.close()
        return {"message": "Valide"}


@app.route("/validate_session", methods=["POST"])
def validate_session_route():
    data = request.args;
    return jsonify(data.get("session_id"), data.get("ip_address"), data.get("user_agent"))


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

    encoded_password = password.encode("utf-8")
    hashed_password = bytes(data[1], "utf-8")
    if data is None or not bcrypt.check_password_hash(hashed_password, encoded_password):
        return jsonify({"error": "Crédentiels invalide"}), 400

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
