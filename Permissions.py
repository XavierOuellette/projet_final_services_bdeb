from __main__ import app, connection
from flask import request, jsonify


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


@app.route("/has_permission", methods=["GET"])
def has_permission():
    session_id = request.args.get('session_id')
    permission = request.args.get('permission')
    cursor = connection.cursor()

    # Retourne les permissions de l'utilisateur
    perm_query = (f"SELECT rp.permission_name"
                  "FROM SESSIONS s"
                  "JOIN USERS u ON s.user_id = u.user_id"
                  "JOIN ROLES r on u.user_id = r.user_id"
                  "JOIN ROLE_PERMISSIONS rp ON r.role_name = rp.role_name"
                  f"WHERE s.session_id = '{session_id}' AND rp.permission_name = '{permission}'")
    cursor.execute(perm_query)
    perm = cursor.fetchone()
    if permission not in perm:
        return jsonify({"response": "false"})
    return jsonify({"response": "true"})


def has_permission(session_id, permission):
    cursor = connection.cursor()

    # Retourne les permissions de l'utilisateur
    perm_query = (f"SELECT rp.permission_name "
                  "FROM SESSIONS s "
                  "JOIN USERS u ON s.user_id = u.user_id "
                  "JOIN ROLES r on u.role_name = r.role_name "
                  "JOIN ROLE_PERMISSIONS rp ON r.role_name = u.role_name "
                  f"WHERE s.session_id = '{session_id}' AND rp.permission_name = '{permission}'")
    cursor.execute(perm_query)
    perm = cursor.fetchone()
    if perm is None or permission not in perm:
        return False
    return True
