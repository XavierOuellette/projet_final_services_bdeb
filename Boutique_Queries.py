from __main__ import app, connection
import oracledb
from flask import request, abort, jsonify

from Session import validate_session


@app.route('/insert_item', methods=['POST'])
def insert_item():
    data = request.get_json()

    if not all(key in data for key in ('name', 'description', 'price', 'available')):
        abort(400, 'Les données incomplètes pour l\'insertion')
    if data['available'] not in (0, 1):
        abort(400, "La valeur de 'available' doit être 0 ou 1.")
    cursor = connection.cursor()

    try:
        cursor.execute(
            "INSERT INTO products (name, description, price, image_path, available) VALUES (:1, :2, :3, :4, :5)",
            (data['name'], data['description'], data['price'], data.get('image_path', None), data.get('available')))

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
    # DÉCOMMENTER XAVIER
    # id = request.args.get('id')
    # name = request.args.get('name')
    # description = request.args.get('description')
    # price = request.args.get('price')
    # image_path = request.args.get('image_path')

    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT p.id, p.name, p.description, p.price, p.image_path
            FROM Products p
            WHERE p.available = 1
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
                'image_path': item[4]
            }
            items_list.append(item_dict)

        return jsonify({"items": items_list})
    except oracledb.DatabaseError as e:
        error_message = "Erreur lors de la récupération des items: " + str(e)
        print(error_message)
        abort(500, error_message)
    finally:
        cursor.close()
