import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

# Lädt die Umgebungsvariablen aus der .env-Datei
load_dotenv()

def get_db_engine() -> Engine:
    """Stellt die Datenbankverbindung her und ist an die spezifische .env-Datei angepasst."""
    try:
        # GEÄNDERT: Wir lesen jetzt die Variablennamen aus IHRER .env-Datei
        server = os.getenv("DB_SERVER")
        database = os.getenv("DB_NAME")
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")

        # HINWEIS: Der Treiberpfad ist jetzt fest im Code hinterlegt, da er in der .env-Datei fehlt.
        driver_path = "/opt/homebrew/lib/libmsodbcsql.17.dylib"

        # Angepasste Überprüfung der geladenen Variablen
        if not all([server, database, username, password]):
            print("❌ Fehler: Eine der Umgebungsvariablen (DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD) fehlt oder ist leer.")
            exit()

        print(f"Versuche, Verbindung herzustellen zu Host: {server}...")
        
        # Passwort für die URL maskieren
        encoded_password = urllib.parse.quote_plus(password)
        
        # Finale Verbindungszeichenfolge mit dem fest einprogrammierten Treiberpfad
        connection_string = (
            f"mssql+pyodbc://{username}:{encoded_password}@{server}/{database}?"
            f"driver={driver_path}"
        )
        
        engine = create_engine(connection_string)
        
        # Testet die Verbindung
        connection = engine.connect()
        print("✅ Datenbankverbindung erfolgreich hergestellt.")
        connection.close()
        return engine
        
    except Exception as e:
        print(f"\n❌ Fehler bei der Datenbankverbindung: {e}")
        print("\nÜberprüfen Sie bitte die Zugangsdaten in Ihrer .env-Datei und den festen Treiberpfad im Skript.")
        exit()

def generate_schema_script(engine: Engine, schema_name: str = 'dbo') -> str:
    """Generiert CREATE TABLE-Anweisungen aus den Metadaten der Datenbank."""
    print("\n--- Generiere Schema-Skript ---\n")
    inspector = inspect(engine)
    tables = inspector.get_table_names(schema=schema_name)
    full_schema_script = ""
    for table_name in tables:
        script_part = f"CREATE TABLE [{schema_name}].[{table_name}] (\n"
        columns = inspector.get_columns(table_name, schema=schema_name)
        column_definitions = [f"  [{col['name']}] {str(col['type'])}" for col in columns]
        script_part += ",\n".join(column_definitions)
        script_part += "\n);\n\n"
        full_schema_script += script_part
    return full_schema_script

if __name__ == "__main__":
    db_engine = get_db_engine()
    if db_engine:
        schema_script = generate_schema_script(db_engine)
        print("--- Schema-Skript erfolgreich generiert ---")
        print(schema_script)
        file_name = "db_schema_for_prompt.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(schema_script)
        print(f"\n✅ Das Schema wurde auch in der Datei '{file_name}' gespeichert.")