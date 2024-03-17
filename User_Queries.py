from __main__ import app, connection
import oracledb
from flask import request, abort, jsonify
from Main import bcrypt
from Session import Session, session_required


@app.route('/insert_user', methods=['POST'])
# Méthode pour insérer un user dans la DB
# Retourne confirmation d'insertion du user
def insert_user():
    data = request.get_json()

    if not all(key in data for key in ('username', 'password', 'email')):
        abort(400, 'Les données incomplètes pour l\'insertion')

    cursor = connection.cursor()

    try:
        # Hash + salt en utilisant bcrypt
        hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

        query = "INSERT INTO users (username, password, email) VALUES (:1, :2, :3)"
        bindings = [data['username'], hashed_password, data['email']]
        cursor.execute(query, bindings)

        connection.commit()
        print("User ajouté avec succès.")
        return jsonify({"message": "User ajouté avec succès."})
    except oracledb.DatabaseError as e:
        error_message = "Erreur lors de l'ajout du user: " + str(e)
        print(error_message)
        connection.rollback()
        abort(500, error_message)

    finally:
        cursor.close()


@app.route('/all_users', methods=["GET"])
@session_required(["user.get_data"])
# Méthode pour aller chercher tout les utilisateurs
# Et qui retourne leur id, username, email et role
def get_all_users():
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT u.user_id, u.username, u.email, r.role_name
            FROM Users u
            JOIN Roles r ON u.role_name = r.role_name
            ORDER BY u.user_id ASC
        """)
        users = cursor.fetchall()

        user_list = []

        for user in users:
            user_dict = {
                'user_id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[3]
            }
            user_list.append(user_dict)

        return jsonify({"users": user_list})
    except oracledb.DatabaseError as e:
        error_message = "Erreur lors de la récupération des utilisateurs: " + str(e)
        print(error_message)
        abort(500, error_message)
    finally:
        cursor.close()


@app.route('/get_user', methods=["GET"])
@session_required(["user.get_data"])
# Méthode pour chercher un user
# Retourne l'id, username, email et role du user
def get_user():
    username = request.args.get('username')
    user_id = request.args.get('user_id')

    cursor = connection.cursor()

    try:
        cursor.execute(f"""
            SELECT u.user_id, u.username, u.email, r.role_name
            FROM Users u
            JOIN Roles r ON u.role_name = r.role_name
            WHERE u.username = :1
        """, [username])
        user = cursor.fetchone()

        if user:
            user_dict = {
                'user_id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[3]
            }
            return jsonify({"user": user_dict})
        else:
            return jsonify({"message": "Utilisateur non trouvé."}), 404
    except oracledb.DatabaseError as e:
        error_message = f"Erreur lors de la récuparation de l'utilisateur avec l'ID {user_id}: {str(e)}"
        print(error_message)
        return jsonify({"message": error_message}), 500
    finally:
        cursor.close()


@app.route('/delete_user', methods=["DELETE"])
@session_required(["admin.delete_user"])
# Méthode pour supprimer un user a l'aide de son id
# Retourne confirmation de la suppression du user
def delete_user():
    cursor = connection.cursor()

    try:
        cursor.execute("DELETE FROM users WHERE user_id = :1", [request.get_json().get("user_id")])

        connection.commit()

        return jsonify({"message": f"Utilisateur supprimé avec succès."})
    except oracledb.DatabaseError as e:
        # En cas d'erreur on rollback
        connection.rollback()
        error_message = f"Erreur lors de la suppression de l'utilisateur: {str(e)}"
        print(error_message)
        return jsonify({"message": error_message}), 500
    finally:
        cursor.close()


@app.route('/update_user', methods=["POST"])
@session_required(["admin.update_user"])
# Méthode pour mettre à jour les informations d'un utilisateur
# Retourne confirmation de changement
def update_user():
    json = request.get_json()

    data = {key.lower(): value for key, value in json.items()} # NE PAS TOUCHER, SINON PROBLÈME
    if 'user_id' not in data:
        return jsonify({"message": "L'ID de l'utilisateur est manquant."}), 400

    # Récupérez les données de l'utilisateur à partir du corps de la requête
    user_id = data['user_id']
    new_username = data.get('username')
    new_email = data.get('email')
    new_role = data.get('role_name')

    # Vérifiez si au moins l'une des données à mettre à jour est présente
    if not any([new_username, new_email]):
        return jsonify({"message": "Aucune donnée à mettre à jour n'a été fournie."}), 400

    cursor = connection.cursor()

    try:
        update_query = "UPDATE users SET"
        bindings = dict()
        if new_username:
            update_query += " username = :username,"
            bindings.update(username=new_username)
        if new_email:
            update_query += " email = :email,"
            bindings.update(email=new_email)
        if new_role:
            update_query += " role_name = :role,"
            bindings.update(role=new_role)

        # Supprimez la virgule supplémentaire à la fin de la requête de mise à jour
        update_query = update_query.rstrip(',')

        # Ajoutez la clause WHERE pour filtrer par ID utilisateur
        update_query += " WHERE user_id = :id"
        bindings.update(id=user_id)

        cursor.execute(update_query, bindings)

        connection.commit()

        return jsonify({"message": "Informations de l'utilisateur mises à jour avec succès."})
    except oracledb.DatabaseError as e:
        # En cas d'erreur, annulez les modifications et renvoyez un message d'erreur
        connection.rollback()
        error_message = f"Erreur lors de la mise à jour des informations de l'utilisateur : {str(e)}"
        print(error_message)
        return jsonify({"message": error_message}), 500
    finally:
        cursor.close()


