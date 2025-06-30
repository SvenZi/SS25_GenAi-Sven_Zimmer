import pandas as pd

class DatabaseTool:
    """
    Ein Werkzeug zur Interaktion mit einer Datenbank über SQLAlchemy und Pandas.
    """
    def __init__(self):
        """
        Initialisiert das DatabaseTool, indem eine Datenbank-Engine abgerufen wird.
        """
        self.engine = get_database_engine()
        if self.engine is None:
            # Dies stellt sicher, dass ein Fehler ausgelöst wird, wenn die Engine nicht erstellt werden konnte.
            # Alternativ könnte man hier auch einfach eine Fehlermeldung printen und self.engine auf None lassen,
            # aber dann müssten alle Methoden das explizit prüfen.
            raise ConnectionError("Datenbank-Engine konnte nicht initialisiert werden. Überprüfen Sie die Konfiguration und Fehlermeldungen.")

    def execute_sql_query(self, sql_query: str):
        """
        Führt eine SQL-Abfrage mithilfe der gespeicherten Engine aus und gibt das Ergebnis als Pandas DataFrame zurück.

        Args:
            sql_query (str): Die auszuführende SQL-Abfrage.

        Returns:
            pandas.DataFrame: Das Ergebnis der Abfrage als DataFrame.
            str: Eine Fehlermeldung, falls bei der Ausführung ein Fehler auftritt.
        """
        if self.engine is None:
            return "Fehler: Keine Datenbank-Engine verfügbar. Die Initialisierung ist möglicherweise fehlgeschlagen."

        try:
            df = pd.read_sql_query(sql_query, self.engine)
            return df
        except ImportError:
            # Dieser Fall sollte eigentlich nicht auftreten, wenn Pandas oben erfolgreich importiert wurde,
            # aber zur Sicherheit.
            return "Fehler: Pandas nicht gefunden. Bitte stellen Sie sicher, dass es installiert ist."
        except Exception as e:
            return f"Fehler bei der Ausführung der SQL-Abfrage: {e}"

if __name__ == '__main__':
    # Beispielhafte Verwendung (erfordert eine .env Datei und eine laufende DB)
    print("Initialisiere DatabaseTool...")
    try:
        db_tool = DatabaseTool()
        print("DatabaseTool initialisiert.")

        # Beispielabfrage (abhängig von Ihrem Datenbankschema)
        # Ersetzen Sie dies durch eine gültige Abfrage für Ihre Datenbank.
        # query = "SELECT TOP 10 * FROM YourTable;"
        query = "SELECT 1 AS TestColumn;" # Einfache Testabfrage, die auf den meisten SQL-Servern funktioniert

        print(f"Führe Testabfrage aus: {query}")
        result = db_tool.execute_sql_query(query)

        if isinstance(result, pd.DataFrame):
            print("Abfrage erfolgreich. Ergebnis:")
            print(result)
        else:
            print("Fehler bei der Abfrage:")
            print(result)

    except ConnectionError as ce:
        print(f"Fehler bei der Initialisierung von DatabaseTool: {ce}")
    except Exception as ex:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {ex}")


@ -0,0 +1,89 @@
import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv

def get_database_engine():
    """
    Stellt eine Verbindung zur Datenbank her und gibt eine SQLAlchemy Engine zurück.

    Liest die Datenbank-Anmeldeinformationen aus einer .env-Datei,
    maskiert das Passwort und verwendet einen festen Treiberpfad.

    Returns:
        sqlalchemy.engine.Engine: Die konfigurierte SQLAlchemy Engine oder None bei einem Fehler.
    """
    load_dotenv()

    db_server = os.getenv("DB_SERVER")
    db_name = os.getenv("DB_NAME")
    db_username = os.getenv("DB_USERNAME")
    db_password = os.getenv("DB_PASSWORD")
    driver_path = "/opt/homebrew/lib/libmsodbcsql.17.dylib"  # Fester Treiberpfad

    if not all([db_server, db_name, db_username, db_password]):
        print("Fehler: Nicht alle erforderlichen Umgebungsvariablen (DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD) sind gesetzt.")
        return None

    try:
        # Maskieren des Passworts für die Verwendung in der Verbindungszeichenfolge
        quoted_password = urllib.parse.quote_plus(db_password)

        # Erstellen der Verbindungszeichenfolge
        # Beachten Sie, dass der ODBC-Treiber explizit im Connection String angegeben wird.
        # Der dialect+driver://username:password@host:port/database Aufbau wird hier verwendet.
        # Für SQL Server mit pyodbc sieht das typischerweise so aus:
        # 'mssql+pyodbc://<username>:<password>@<dsnname>'
        # oder 'mssql+pyodbc://<username>:<password>@<host>/<database>?driver=<drivername>'

        # Da wir einen spezifischen Treiberpfad haben, ist es üblicher, diesen
        # über einen DSN zu konfigurieren oder sicherzustellen, dass der ODBC-Manager
        # ihn korrekt findet. SQLAlchemy selbst konfiguriert nicht direkt den Treiberpfad
        # auf Dateisystemebene. Der `driver` Parameter in der URL bezieht sich auf den
        # Namen des ODBC-Treibers, wie er vom ODBC-Manager erkannt wird.
        # Der feste Treiberpfad ist eher eine Systemkonfigurationsangelegenheit.
        # Wir gehen davon aus, dass der ODBC-Manager so konfiguriert ist,
        # dass er diesen Treiber unter einem bekannten Namen (z.B. 'ODBC Driver 17 for SQL Server') findet.
        # Wenn der Treibername direkt im String verwendet werden soll:
        connection_string = f"mssql+pyodbc://{db_username}:{quoted_password}@{db_server}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server"

        # Alternative, falls ein DSN verwendet wird (weniger wahrscheinlich gegeben die Anforderung des Treiberpfads)
        # connection_url = URL.create(
        # "mssql+pyodbc",
        # username=db_username,
        # password=quoted_password,
        # host=db_server,
        # database=db_name,
        # query={"driver": "ODBC Driver 17 for SQL Server"} # Sicherstellen, dass dieser Treibername korrekt ist
        # )

        print(f"Verbinde mit: mssql+pyodbc://{db_username}:<MASKED_PASSWORD>@{db_server}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server")
        engine = create_engine(connection_string)

        # Testen der Verbindung (optional, aber gut für sofortiges Feedback)
        with engine.connect() as connection:
            print("Datenbankverbindung erfolgreich hergestellt.")
        return engine

    except ImportError:
        print("Fehler: Die 'python-dotenv' oder 'SQLAlchemy' Bibliothek wurde nicht gefunden. Bitte installieren Sie sie.")
        return None
    except Exception as e:
        print(f"Fehler beim Herstellen der Datenbankverbindung: {e}")
        return None

if __name__ == '__main__':
    # Beispielaufruf zum Testen (erfordert eine .env Datei und eine laufende DB)
    # Erstellen Sie eine .env Datei im selben Verzeichnis mit Ihren DB-Anmeldeinformationen:
    # DB_SERVER=dein_server
    # DB_NAME=deine_datenbank
    # DB_USERNAME=dein_benutzer
    # DB_PASSWORD=dein_passwort

    print("Versuche, eine Datenbank-Engine zu erhalten...")
    engine = get_database_engine()
    if engine:
        print("Engine erfolgreich erstellt.")
    else:
        print("Engine konnte nicht erstellt werden.")