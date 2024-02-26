from flask import Flask, jsonify, abort
import oracledb
import os

app = Flask(__name__)




def connecter():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    try:
        connexion = oracledb.connect(
            config_dir=os.path.join(script_dir, "wallet"),
            user="admin",
            password="Lebelfranck2297$",
            dsn="franciscloud_high",
            wallet_location=os.path.join(script_dir, "wallet"),
            wallet_password="Lebelfranck2297$")
        print("Connexion à la base de données réussie.")
        return connexion
    except oracledb.DatabaseError as e:
        error_message = "Erreur lors de la connexion à la base de données: " + str(e)
        print(error_message)
        abort(500, error_message)


connexion = connecter()

import Database_Operation

if __name__ == '__main__':
    app.run()
