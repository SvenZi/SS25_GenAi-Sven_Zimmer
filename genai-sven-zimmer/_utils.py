import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

def get_database_engine() -> Engine | None:
    """
    Stellt eine Verbindung zur Datenbank her und gibt eine SQLAlchemy Engine zurück.
    Liest die Anmeldeinformationen aus einer .env-Datei.
    """
    load_dotenv()

    db_server = os.getenv("DB_SERVER")
    db_name = os.getenv("DB_NAME")
    db_username = os.getenv("DB_USERNAME")
    db_password = os.getenv("DB_PASSWORD")
    
    if not all([db_server, db_name, db_username, db_password]):
        print("Fehler: Nicht alle erforderlichen DB-Umgebungsvariablen sind gesetzt.")
        return None

    try:
        quoted_password = urllib.parse.quote_plus(db_password)
        connection_string = f"mssql+pyodbc://{db_username}:{quoted_password}@{db_server}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server"

        print("Verbinde mit der Datenbank...")
        engine = create_engine(connection_string)

        with engine.connect() as connection:
            print("Datenbankverbindung erfolgreich hergestellt.")
        return engine

    except Exception as e:
        print(f"Fehler beim Herstellen der Datenbankverbindung: {e}")
        return None