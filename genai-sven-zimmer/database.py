import pandas as pd
from utils import get_database_engine

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
