from flask import Flask, abort
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import oracledb
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://localhost:7012"}})
bcrypt = Bcrypt(app)


# Méthode pour se connecter a la DB
# Retourne une connexion
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


connection = connecter()

# Import des méthodes de User_Queries.py
# NE PAS BOUGER, SINON CONNEXION ERREUR
import User_Queries
import Session
import Boutique_Queries

if __name__ == '__main__':
    app.json.sort_keys = False
    app.run()