import os
import urllib.parse
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

def get_database_engine():
    """
    Erstellt und gibt eine SQLAlchemy-Engine für die Datenbankverbindung zurück.
    Liest die Konfiguration aus der .env-Datei.
    """
    load_dotenv()
    
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')

    if not all([server, database, username, password]):
        print("❌ Fehler: Umgebungsvariablen für die DB sind unvollständig.")
        return None

    try:
        encoded_password = urllib.parse.quote_plus(password)
        driver_path = '?driver=/opt/homebrew/lib/libmsodbcsql.17.dylib'
        connection_string = f"mssql+pyodbc://{username}:{encoded_password}@{server}/{database}{driver_path}"
        
        engine = create_engine(connection_string)
        # Teste die Verbindung, indem eine tatsächliche Verbindung geöffnet wird
        connection = engine.connect()
        connection.close()
        return engine
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Datenbank-Engine: {e}")
        return None
