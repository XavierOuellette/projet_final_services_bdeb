import secrets
import string
from __main__ import app, connection
from datetime import datetime, timedelta
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
    cursor.execute(query, [session_id])
    session_info = cursor.fetchone()

    if session_info is None:
        return {"error": "Session invalide"}

    expires_at, stored_ip_address, stored_user_agent = session_info

    if expires_at < datetime.now() + timedelta(hours=3) or stored_ip_address != ip_address or stored_user_agent != user_agent:
        return {"error": "Session invalide"}
    else:
        # Prolonge la durée de la session
        update_query = "UPDATE Sessions SET expires_at = SYSTIMESTAMP + NUMTODSINTERVAL(:1, 'MINUTE') WHERE session_id = :2"
        bindings = [SESSION_LENGTH, session_id]

        cursor = connection.cursor()
        cursor.execute(update_query, bindings)
        connection.commit()
        cursor.close()
        return {"message": "Valide"}


@app.route("/validate_session", methods=["POST"])
def validate_session_route():
    data = request.get_json()
    response = validate_session(data.get("session_id"), data.get("ip_address"), data.get("user_agent"))
    if "error" in response.keys():
        return jsonify(response), 400
    return jsonify(response), 200


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
    query = "SELECT user_id, password FROM USERS WHERE username = :1"
    cursor.execute(query, [username])
    data = cursor.fetchone()

    encoded_password = password.encode("utf-8")
    hashed_password = bytes(data[1], "utf-8")
    if data is None or not bcrypt.check_password_hash(hashed_password, encoded_password):
        return jsonify({"error": "Crédentiels invalide"}), 400

    user_id = data[0]
    if user_id:
        session_id = generate_session_id()

        query = """
                SELECT SYSTIMESTAMP + NUMTODSINTERVAL(:my_variable, 'MINUTE')
                FROM DUAL
                """
        cursor.execute(query, my_variable=SESSION_LENGTH)
        result = cursor.fetchone()

        # Extract the calculated expiration timestamp from the result tuple
        expires_at = result[0]

        # Insérer la nouvelle session dans la base de données
        insert_query = "INSERT INTO SESSIONS (session_id, user_id, expires_at, ip_address, user_agent) VALUES (:1, :2, :3, :4, :5)"
        bindings = [session_id, user_id, expires_at, ip_address, user_agent]
        cursor.execute(insert_query, bindings)
        connection.commit()
        cursor.close()

        return jsonify({"session_id": session_id}), 200
    else:
        return jsonify({"error": "Crédentiels invalides."}), 401


@app.route("/disconnect", methods=["POST"])
def disconnect():
    session_id = request.json.get("session_id")
    ip_address = request.json.get('ip_address')
    user_agent = request.json.get('user_agent')
    if not all([session_id, ip_address, user_agent]):
        return jsonify({"error": "Certains paramètres sont manquants."}), 400

    cursor = connection.cursor()

    # Requête pour l'utilisateur et son mot de passe
    query = ("DELETE FROM SESSIONS "
             "WHERE session_id = :1"
             "AND user_agent = :2"
             "AND ip_address = :3")

    bindings = [session_id, user_agent, ip_address]
    cursor.execute(query, bindings)
    cursor.close()

    return jsonify({"message": "Success"}, 200)
