from __main__ import app, connexion

import oracledb
from flask import request, abort, jsonify


@app.route('/insert_user', methods=['POST'])
# Méthode pour insérer un user dans la DB
# Retourne confirmation d'insertion du user
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
# Méthode pour aller chercher tout les utilisateurs
# Et qui retourne leur id, username, email et role
def get_all_users():
    cursor = connexion.cursor()

    try:
        cursor.execute("SELECT id, email, username, role FROM users")
        users = cursor.fetchall()

        user_list = []

        # Par defaut les role sont 0 pour admin et 1 pour user
        # Changer le defaut pour retourner admin ou user
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


@app.route('/delete_user', methods=["POST"])
# Méthode pour supprimer un user a l'aide de son id
# Retourne confirmation de la suppression du user
def delete_user():
    data = request.get_json()

    if 'id' not in data:
        return jsonify({"message": "ID de l'utilisateur inexistant."}), 400

    user_id = data['id']
    cursor = connexion.cursor()

    try:
        cursor.execute("DELETE FROM users WHERE id = :1", (user_id,))

        connexion.commit()

        return jsonify({"message": f"Utilisateur avec l'ID {user_id} supprimé avec succès."})
    except oracledb.DatabaseError as e:
        # En cas d'erreur on rollback
        connexion.rollback()
        error_message = f"Erreur lors de la suppression de l'utilisateur avec l'ID {user_id}: {str(e)}"
        print(error_message)
        return jsonify({"message": error_message}), 500
    finally:
        cursor.close()
