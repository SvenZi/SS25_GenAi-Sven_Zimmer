# import os
# import urllib.parse
# from dotenv import load_dotenv
# from sqlalchemy import create_engine, inspect
# from sqlalchemy.engine import Engine

# # Lädt die Umgebungsvariablen aus der .env-Datei
# load_dotenv()

# def get_db_engine() -> Engine:
#     """Stellt die Datenbankverbindung her und ist an die spezifische .env-Datei angepasst."""
#     try:
#         # GEÄNDERT: Wir lesen jetzt die Variablennamen aus IHRER .env-Datei
#         server = os.getenv("DB_SERVER")
#         database = os.getenv("DB_NAME")
#         username = os.getenv("DB_USERNAME")
#         password = os.getenv("DB_PASSWORD")

#         # HINWEIS: Der Treiberpfad ist jetzt fest im Code hinterlegt, da er in der .env-Datei fehlt.
#         driver_path = "/opt/homebrew/lib/libmsodbcsql.17.dylib"

#         # Angepasste Überprüfung der geladenen Variablen
#         if not all([server, database, username, password]):
#             print("❌ Fehler: Eine der Umgebungsvariablen (DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD) fehlt oder ist leer.")
#             exit()

#         print(f"Versuche, Verbindung herzustellen zu Host: {server}...")
        
#         # Passwort für die URL maskieren
#         encoded_password = urllib.parse.quote_plus(password)
        
#         # Finale Verbindungszeichenfolge mit dem fest einprogrammierten Treiberpfad
#         connection_string = (
#             f"mssql+pyodbc://{username}:{encoded_password}@{server}/{database}?"
#             f"driver={driver_path}"
#         )
        
#         engine = create_engine(connection_string)
        
#         # Testet die Verbindung
#         connection = engine.connect()
#         print("✅ Datenbankverbindung erfolgreich hergestellt.")
#         connection.close()
#         return engine
        
#     except Exception as e:
#         print(f"\n❌ Fehler bei der Datenbankverbindung: {e}")
#         print("\nÜberprüfen Sie bitte die Zugangsdaten in Ihrer .env-Datei und den festen Treiberpfad im Skript.")
#         exit()

# def generate_schema_script(engine: Engine, schema_name: str = 'dbo') -> str:
#     """Generiert CREATE TABLE-Anweisungen aus den Metadaten der Datenbank."""
#     print("\n--- Generiere Schema-Skript ---\n")
#     inspector = inspect(engine)
#     tables = inspector.get_table_names(schema=schema_name)
#     full_schema_script = ""
#     for table_name in tables:
#         script_part = f"CREATE TABLE [{schema_name}].[{table_name}] (\n"
#         columns = inspector.get_columns(table_name, schema=schema_name)
#         column_definitions = [f"  [{col['name']}] {str(col['type'])}" for col in columns]
#         script_part += ",\n".join(column_definitions)
#         script_part += "\n);\n\n"
#         full_schema_script += script_part
#     return full_schema_script

# if __name__ == "__main__":
#     db_engine = get_db_engine()
#     if db_engine:
#         schema_script = generate_schema_script(db_engine)
#         print("--- Schema-Skript erfolgreich generiert ---")
#         print(schema_script)
#         file_name = "db_schema_for_prompt.txt"
#         with open(file_name, "w", encoding="utf-8") as f:
#             f.write(schema_script)
#         print(f"\n✅ Das Schema wurde auch in der Datei '{file_name}' gespeichert.")

# generate_full_context.py
import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
import pandas as pd

# Lädt die Umgebungsvariablen aus der .env-Datei
load_dotenv()

def get_db_engine() -> Engine:
    """Stellt die Datenbankverbindung her und ist an die spezifische .env-Datei angepasst."""
    try:
        server = os.getenv("DB_SERVER")
        database = os.getenv("DB_NAME")
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        driver_path = "/opt/homebrew/lib/libmsodbcsql.17.dylib"

        if not all([server, database, username, password]):
            print("❌ Fehler: Eine der Umgebungsvariablen (DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD) fehlt oder ist leer.")
            exit()

        print(f"Versuche, Verbindung herzustellen zu Host: {server}...")
        encoded_password = urllib.parse.quote_plus(password)
        
        connection_string = (
            f"mssql+pyodbc://{username}:{encoded_password}@{server}/{database}?"
            f"driver={driver_path}"
        )
        
        engine = create_engine(connection_string)
        
        with engine.connect() as connection:
            print("✅ Datenbankverbindung erfolgreich hergestellt.")
        return engine
        
    except Exception as e:
        print(f"\n❌ Fehler bei der Datenbankverbindung: {e}")
        exit()

def generate_schema_script(engine: Engine, schema_name: str = 'dbo') -> str:
    """Generiert CREATE TABLE-Anweisungen aus den Metadaten der Datenbank."""
    print("\n--- Generiere Schema-Skript...")
    inspector = inspect(engine)
    tables = inspector.get_table_names(schema=schema_name)
    full_schema_script = ""
    for table_name in tables:
        # Ignoriere Tabellen, die wir nicht für die Analyse benötigen
        if 'Quota' in table_name or 'Planning' in table_name:
            continue
        script_part = f"CREATE TABLE [{schema_name}].[{table_name}] (\n"
        columns = inspector.get_columns(table_name, schema=schema_name)
        column_definitions = []
        for col in columns:
            col_def = f"  [{col['name']}] {str(col['type'])}"
            # Füge Kommentare für Datumsformate hinzu, falls bekannt
            if 'date' in col['name'].lower() and 'DATE' in str(col['type']):
                 col_def += ", -- Format: 'YYYY-MM-DD'"
            elif 'month_iso' in col['name'].lower():
                 col_def += ", -- Format: 'YYYY.MM'"
            column_definitions.append(col_def)

        script_part += ",\n".join(column_definitions)
        script_part += "\n);\n\n"
        full_schema_script += script_part
    return full_schema_script

def analyze_categorical_data(engine: Engine) -> str:
    """Analysiert wichtige kategoriale Spalten und listet ihre einzigartigen Werte auf."""
    print("--- Analysiere kategoriale Daten...")
    analysis = ""
    # Definiere hier die Spalten, die du analysieren möchtest
    columns_to_analyze = {
        "Dim_Product": ["Product_Category", "Product_Line"],
        "Dim_Sales_Office": ["Sales_Country", "Global_Region", "Sales_Region"],
        "Dim_Sales_Channel": ["Sales_Channel"]
    }
    
    for table, columns in columns_to_analyze.items():
        for column in columns:
            try:
                df = pd.read_sql_query(f"SELECT DISTINCT [{column}] FROM dbo.[{table}] WHERE [{column}] IS NOT NULL ORDER BY [{column}];", engine)
                values = df[column].tolist()
                analysis += f"Einzigartige Werte für '{column}' in Tabelle '{table}':\n"
                analysis += f"- {', '.join(map(str, values))}\n\n"
            except Exception as e:
                print(f"Konnte Spalte {column} in Tabelle {table} nicht analysieren: {e}")
                
    return analysis

def analyze_date_ranges(engine: Engine) -> str:
    """Analysiert den MIN- und MAX-Zeitraum in den Verkaufstabellen."""
    print("--- Analysiere Datenzeiträume...")
    analysis = "DATENZEITRAUM:\n"
    try:
        # Monatliche Daten
        df_monthly = pd.read_sql_query("SELECT MIN(Calendar_Month_ISO) as min_month, MAX(Calendar_Month_ISO) as max_month FROM dbo.DataSet_Monthly_Sales;", engine)
        min_month = df_monthly['min_month'].iloc[0]
        max_month = df_monthly['max_month'].iloc[0]
        analysis += f"- Monatliche Verkaufsdaten verfügbar von {min_month} bis {max_month}.\n"
    except Exception as e:
        analysis += f"- Konnte monatliche Zeiträume nicht analysieren: {e}\n"

    try:
        # Tägliche Daten
        df_daily = pd.read_sql_query("SELECT MIN(ID_Order_Date) as min_date, MAX(ID_Order_Date) as max_date FROM dbo.Facts_Daily_Sales;", engine)
        min_date = df_daily['min_date'].iloc[0].strftime('%Y-%m-%d')
        max_date = df_daily['max_date'].iloc[0].strftime('%Y-%m-%d')
        analysis += f"- Tägliche Verkaufsdaten verfügbar von {min_date} bis {max_date}.\n"
    except Exception as e:
        analysis += f"- Konnte tägliche Zeiträume nicht analysieren: {e}\n"
        
    return analysis + "\n"

def generate_product_catalog(engine: Engine) -> str:
    """Erstellt einen strukturierten Produktkatalog aus der Dim_Product Tabelle."""
    print("--- Generiere Produktkatalog...")
    analysis = "PRODUKTKATALOG:\n"
    try:
        query = """
        SELECT
            Product_Category,
            Material_Description
        FROM
            dbo.Dim_Product
        WHERE
            Product_Category IS NOT NULL AND Material_Description IS NOT NULL
        ORDER BY
            Product_Category, Material_Description;
        """
        df = pd.read_sql_query(query, engine)
        
        current_category = ""
        for index, row in df.iterrows():
            if row['Product_Category'] != current_category:
                current_category = row['Product_Category']
                analysis += f"\n- Product_Category: {current_category}\n"
            analysis += f"  - Material_Description: \"{row['Material_Description']}\"\n"
            
        return analysis + "\n"
    except Exception as e:
        return f"Konnte Produktkatalog nicht erstellen: {e}\n\n"


if __name__ == "__main__":
    db_engine = get_db_engine()
    if db_engine:
        # Führe alle Analysen durch
        schema_script = generate_schema_script(db_engine)
        date_analysis = analyze_date_ranges(db_engine)
        categorical_analysis = analyze_categorical_data(db_engine)
        product_catalog = generate_product_catalog(db_engine)
        
        # Kombiniere alle Informationen
        full_context = (
            "================================\n"
            "DATENBANK-KONTEXT-ANALYSE\n"
            "================================\n\n"
            + date_analysis
            + categorical_analysis
            + product_catalog
            + "================================\n"
            "DATENBANK-SCHEMA (CREATE TABLES)\n"
            "================================\n\n"
            + schema_script
        )

        print("\n\n--- Vollständige Analyse erfolgreich abgeschlossen ---")
        
        # Speichere das Ergebnis in einer Datei
        file_name = "database_analysis_for_prompt.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(full_context)
        print(f"\n✅ Alle Analyseergebnisse wurden in der Datei '{file_name}' gespeichert.")
        print("Bitte verwenden Sie den Inhalt dieser Datei als Grundlage für den nächsten Schritt.")