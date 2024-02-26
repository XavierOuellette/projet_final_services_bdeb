from __main__ import app, connexion

import oracledb
from flask import request, abort, jsonify


@app.route('/insert_user', methods=['POST'])
def insert_user():
    data = request.get_json()

    if not all(key in data for key in ('password', 'email', 'username')):
        abort(400, 'Les données incomplètes pour l\'insertion')

    cursor = connexion.cursor()

    try:
        cursor.execute("INSERT INTO users (password, email, username) VALUES (:1, :2, :3)",
                       (data['password'], data['email'], data['username']))

        connexion.commit()
        print("User ajouté avec succès.")
        return jsonify({"message": "User ajouté avec succès."})
    except oracledb.DatabaseError as e:
        error_message = "Erreur lors de l'ajout du user: " + str(e)
        print(error_message)
        connexion.rollback()
        abort(500, error_message)

    finally:
        cursor.close()


@app.route('/all_users', methods=["GET"])
def get_all_users():
    cursor = connexion.cursor()

    try:
        cursor.execute("SELECT id, email, username, role FROM users")
        users = cursor.fetchall()

        user_list = []
        role_dict = {0: "admin", 1: "user"}
        for user in users:
            user_dict = {
                'id': user[0],
                'email': user[1],
                'username': user[2],
                'role': role_dict[user[3]]
            }
            user_list.append(user_dict)

        return jsonify({"users": user_list})
    except oracledb.DatabaseError as e:
        error_message = "Erreur lors de la récupération des utilisateurs: " + str(e)
        print(error_message)
        abort(500, error_message)
    finally:
        cursor.close()
