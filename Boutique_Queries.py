from __main__ import app, connection
import oracledb
from flask import request, abort, jsonify

import Permissions
from Session import Session, session_required


@app.route('/insert_item', methods=['POST'])
@session_required(["shop.insert"])
def insert_item():
    data = request.get_json()

    if not all(key in data for key in ('name', 'description', 'price', 'available')):
        abort(400, 'Les données incomplètes pour l\'insertion')
    if data['available'] not in (0, 1):
        abort(400, "La valeur de 'available' doit être 0 ou 1.")
    cursor = connection.cursor()

    try:
        query = "INSERT INTO products (name, description, price, image_path, available) VALUES (:1, :2, :3, :4, :5)"
        bindings = [data['name'], data['description'], data['price'], data.get('image_path', None), data.get('available')]

        cursor.execute(query, bindings)
        connection.commit()
        print("Item ajouté avec succès.")
        return jsonify({"message": "Item ajouté avec succès."})
    except oracledb.DatabaseError as e:
        error_message = "Erreur lors de l'ajout de l'item: " + str(e)
        print(error_message)
        connection.rollback()
        abort(500, error_message)
    finally:
        cursor.close()


@app.route('/all_items', methods=["GET"])
# Méthode pour aller chercher tout les items
# Et qui retourne leur id, name, description, price et image
def get_all_items():
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT p.id, p.name, p.description, p.price, p.image_path, p.available
            FROM Products p
            ORDER BY p.id ASC
        """)
        items = cursor.fetchall()

        items_list = []

        for item in items:
            item_dict = {
                'id': item[0],
                'name': item[1],
                'description': item[2],
                'price': item[3],
                'image_path': item[4],
                'available': item[5]
            }
            items_list.append(item_dict)

        return jsonify({"items": items_list})
    except oracledb.DatabaseError as e:
        error_message = "Erreur lors de la récupération des items: " + str(e)
        print(error_message)
        abort(500, error_message)
    finally:
        cursor.close()


@app.route('/get_item', methods=["GET"])
# Méthode pour chercher un item
# Retourne l'id, name, description, price et image_path
def get_item():
    name = request.args.get('name').lower()
    cursor = connection.cursor()

    try:
        cursor.execute(f"""
            SELECT p.id, p.name, p.description, p.price, p.image_path, p.available
            FROM Products p
            WHERE p.name = :1
        """, [name])
        item = cursor.fetchone()

        if item:
            item_dict = {
                'id': item[0],
                'name': item[1],
                'description': item[2],
                'price': item[3],
                'image_path': item[4],
                'available': item[5]
            }
            return jsonify({"item": item_dict})
        else:
            return jsonify({"message": "Item non trouvé."}), 404
    except oracledb.DatabaseError as e:
        error_message = f"Erreur lors de la récuparation de l'item avec le nom {name}: {str(e)}"
        print(error_message)
        return jsonify({"message": error_message}), 500
    finally:
        cursor.close()


@app.route('/delete_item', methods=["DELETE"])
@session_required(["shop.delete"])
# Méthode pour supprimer un item a l'aide de son id
# Retourne confirmation de la suppression de l'item
def delete_item():
    data = request.get_json()

    if 'id' not in data:
        return jsonify({"message": "ID de l'item inexistant."}), 400

    cursor = connection.cursor()

    try:
        cursor.execute("DELETE FROM products WHERE id = :1", [data["id"]])

        connection.commit()

        return jsonify({"message": f"Item avec l'ID {data["id"]} supprimé avec succès."})
    except oracledb.DatabaseError as e:
        # En cas d'erreur on rollback
        connection.rollback()
        error_message = f"Erreur lors de la suppression de l'item avec l'ID {data["id"]}: {str(e)}"
        print(error_message)
        return jsonify({"message": error_message}), 500
    finally:
        cursor.close()


@app.route('/update_item', methods=["POST"])
@session_required(["shop.update"])
def update_item():
    data = request.get_json()

    data = {key.lower(): value for key, value in data.items()}  # NE PAS TOUCHER, SINON PROBLÈME
    if 'id' not in data:
        return jsonify({"message": "L'ID de l'item est inexistant."}), 400

    id = data['id']
    new_name = data.get('name')
    new_description = data.get('description')
    new_price = data.get('price')
    new_image = data.get('image_path')
    new_available = data.get('available')

    if not any([new_name, new_description, new_price, new_image, new_available]):
        return jsonify({"message": "Aucune donnée à mettre à jour n'a été fournie."}), 400

    cursor = connection.cursor()

    try:
        update_query = "UPDATE products SET"

        bindings = dict()
        if new_name:
            update_query.append(" name = :name,")
            bindings.update(name=new_name)
        if new_description:
            update_query.append(" description = :description,")
            bindings.update(description=new_description)
        if new_price:
            update_query.append(" price = :price,")
            bindings.update(price=new_price)
        if new_image:
            update_query.append(" image_path = :image_path,")
            bindings.update(image=new_image)
        if new_available is not None:
            update_query.append(" available = :available,")
            bindings.update(available=new_available)

        update_query = update_query.rstrip(',')
        update_query += " WHERE id = :product_id"
        bindings.update(product_id=id)

        cursor.execute(update_query, bindings)

        connection.commit()

        return jsonify({"message": "Informations de l'item mises à jour avec succès."})
    except oracledb.DatabaseError as e:
        connection.rollback()
        error_message = f"Erreur lors de la mise à jour des informations de l'item : {str(e)}"
        print(error_message)
        return jsonify({"message": error_message}), 500
    finally:
        cursor.close()

