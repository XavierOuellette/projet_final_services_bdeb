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
