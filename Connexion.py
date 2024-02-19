from flask import Flask, jsonify, abort
import oracledb
import os

app = Flask(__name__)


@app.route('/connexion')
def connexion():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    try:
        connection = oracledb.connect(
            config_dir=os.path.join(script_dir, "wallet"),
            user="admin",
            password="Lebelfranck2297$",
            dsn="franciscloud_high",
            wallet_location=os.path.join(script_dir, "wallet"),
            wallet_password="Lebelfranck2297$")
        print("Connexion à la base de données réussie.")
        connection.close()
        return jsonify({"message": "Connexion à la base de données réussie."})
    except oracledb.DatabaseError as e:
        error_message = "Erreur lors de la connexion à la base de données: " + str(e)
        print(error_message)
        abort(500, error_message)


if __name__ == '__main__':
    app.run(debug=True)
    connexion()
