import secrets
import string
from __main__ import app, connection
from datetime import datetime, timedelta
from functools import wraps

from flask import request, jsonify, g
from Main import bcrypt

# In minutes
SESSION_LENGTH = 15


def generate_session_id(length=64):
    alphabet = string.ascii_letters + string.digits + '-_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@app.route("/validate_session", methods=["POST"])
def validate_session_route():
    session = Session(request)
    return session.get_json_response()


# Valide les crédentiels de connexion et utilise l'addresse ip et user_agent
@app.route('/validate_login', methods=["POST"])
def validate_login():
    # Récupérer les données du corps de la requête
    data = request.get_json()
    ip_address = data.get("ip_address")
    user_agent = data.get("user_agent")
    username = data.get("username")
    password = data.get("password")

    if not all([ip_address, user_agent, username, password]):
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
    session = Session(request)
    if not session.isValid:
        return session.get_json_response()

    cursor = connection.cursor()

    # Requête pour l'utilisateur et son mot de passe
    query = ("DELETE FROM SESSIONS "
             "WHERE session_id = :1"
             "AND user_agent = :2"
             "AND ip_address = :3")

    bindings = [session.session_id, session.user_agent, session.ip_address]
    cursor.execute(query, bindings)
    cursor.close()

    return jsonify({"response: ": "Success"}, 200)


class Session:

    def __init__(self, rest_request):
        self.isValid = False
        self.session_id = -1
        self.ip_address = -1
        self.user_agent = -1
        self.response_message = "Texte par défaut"
        self.response_code = 400
        if rest_request.is_json:
            json = rest_request.get_json()
            self.session_id = json.get("session_id")
            self.ip_address = json.get("ip_address")
            self.user_agent = json.get("user_agent")
        elif rest_request.args is not None:
            args = rest_request.args
            self.session_id = args.get("session_id")
            self.ip_address = args.get("ip_address")
            self.user_agent = args.get("user_agent")
        else:
            return

        self.validate_session()

    def validate_session(self):
        cursor = connection.cursor()

        # Requête pour la session id
        query = "SELECT expires_at, ip_address, user_agent FROM Sessions WHERE session_id = :1"
        cursor.execute(query, [self.session_id])
        session_info = cursor.fetchone()

        if session_info is None:
            self.response_message = "Session invalide"
            self.response_code = 400
            return

        expires_at, stored_ip_address, stored_user_agent = session_info

        if expires_at < datetime.now() + timedelta(
                hours=3) or stored_ip_address != self.ip_address or stored_user_agent != self.user_agent:
            self.response_message = "Session invalide"
            self.response_code = 400
            return
        else:
            # Prolonge la durée de la session
            update_query = "UPDATE Sessions SET expires_at = SYSTIMESTAMP + NUMTODSINTERVAL(:1, 'MINUTE') WHERE session_id = :2"
            bindings = [SESSION_LENGTH, self.session_id]

            cursor = connection.cursor()
            cursor.execute(update_query, bindings)
            connection.commit()
            cursor.close()
            self.response_code = 200
            self.response_message = "Valide"
            self.isValid = True
            return

    def has_permission(self, permission):
        cursor = connection.cursor()

        # Retourne les permissions de l'utilisateur
        perm_query = ("SELECT rp.permission_name "
                      "FROM SESSIONS s "
                      "JOIN USERS u ON s.user_id = u.user_id "
                      "JOIN ROLES r on u.role_name = r.role_name "
                      "JOIN ROLE_PERMISSIONS rp ON r.role_name = rp.role_name "
                      "WHERE s.session_id = :1 AND rp.permission_name = :2")
        bindings = [self.session_id, permission]
        cursor.execute(perm_query, bindings)
        perm = cursor.fetchone()
        if perm is None or permission not in perm:
            return False
        return True

    def get_json_response(self):
        return jsonify({"error: ": self.response_message}), self.response_code


def session_required(permissions=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            session = Session(request)
            if not session.isValid:
                return session.get_json_response()
            if permissions:
                for permission in permissions:
                    if not session.has_permission(permission):
                        return jsonify({"error": "Access denied"}), 403
            g.session = session
            return func(*args, **kwargs)

        return wrapper

    return decorator
