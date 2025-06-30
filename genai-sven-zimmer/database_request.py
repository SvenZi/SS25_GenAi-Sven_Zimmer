# database_request.py
import os
import urllib.parse
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

_db_engine: Engine | None = None

def _get_db_engine() -> Engine | None:
    try:
        server = os.getenv("DB_SERVER")
        database = os.getenv("DB_NAME")
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        driver_path = "/opt/homebrew/lib/libmsodbcsql.17.dylib" # Fester Treiberpfad

        if not all([server, database, username, password]):
            print("FEHLER: Eine der Umgebungsvariablen (DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD) fehlt oder ist leer.")
            return None

        encoded_password = urllib.parse.quote_plus(password or "")
        
        connection_string = (
            f"mssql+pyodbc://{username}:{encoded_password}@{server}/{database}?"
            f"driver={driver_path}"
        )
        
        engine = create_engine(connection_string, connect_args={'autocommit': True})
        
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✅ Datenbankverbindung erfolgreich hergestellt (in database_request.py).")
        return engine
        
    except Exception as e:
        print(f"\n❌ FEHLER BEI DB-VERBINDUNG (in database_request.py): {e}")
        print("Überprüfen Sie Zugangsdaten in .env und den Treiberpfad.")
        return None

_db_engine = _get_db_engine()

def DatabaseRequest(sql_query: str) -> pd.DataFrame | str:
    print(f"\n--- DatabaseRequest Funktion aufgerufen ---")
    print(f"Empfangener SQL-Code zur Ausführung:\n{sql_query}")

    if _db_engine is None:
        error_msg = "FEHLER: Abfrage konnte aufgrund fehlender Datenbankverbindung nicht ausgeführt werden."
        print(error_msg)
        return error_msg

    if not sql_query.strip().upper().startswith("SELECT"):
        error_msg = "FEHLER: Nur SELECT-Abfragen sind erlaubt. Abfrage blockiert."
        print(error_msg)
        return error_msg

    try:
        with _db_engine.connect() as connection:
            result = connection.execute(text(sql_query))
            
            if result.returns_rows:
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                print(f"\n--- Datenbankabfrage erfolgreich, DataFrame erstellt ---")
                print(df)
                return df
            else:
                success_msg = "Abfrage erfolgreich, aber keine Zeilen zurückgegeben."
                print(success_msg)
                return success_msg

    except SQLAlchemyError as e:
        error_msg = f"FEHLER: Datenbankfehler bei der SQL-Ausführung." # Konsolidierte Fehlermeldung
        print(f"Detaillierter DB-Fehler (nur für Debugging): {str(e)}") # Detailliertes internes Logging
        return error_msg
    except Exception as e:
        error_msg = f"FEHLER: Ein unerwartetes Problem bei der SQL-Ausführung ist aufgetreten." # Konsolidierte Fehlermeldung
        print(f"Detaillierter unerwarteter Fehler (nur für Debugging): {str(e)}") # Detailliertes internes Logging
        return error_msg
    finally:
        print(f"\n--- DatabaseRequest: Abfrage abgeschlossen ---")