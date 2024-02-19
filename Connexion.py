import oracledb
import os

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
    connexion.close()
except oracledb.DatabaseError as e:
    print("Erreur lors de la connexion à la base de données:", e)


