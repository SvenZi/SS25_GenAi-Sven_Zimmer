import pandas as pd
from sqlalchemy.engine import Engine
from utils import get_database_engine # Wir importieren unsere Hilfsfunktion

class DatenbankAgent:
    """
    Ein spezialisierter Agent, der ausschließlich für die Ausführung
    von SQL-Abfragen auf der Datenbank zuständig ist.
    """
    def __init__(self):
        self.engine: Engine | None = get_database_engine()

    def fuehre_abfrage_aus(self, query: str) -> pd.DataFrame | str:
        """
        Führt eine gegebene SQL-Abfrage aus und gibt das Ergebnis als
        Pandas DataFrame zurück. Bei einem Fehler wird eine Fehlermeldung
        als String zurückgegeben.
        """
        if self.engine is None:
            error_message = "Datenbank-Engine nicht initialisiert. Verbindung fehlgeschlagen."
            print(error_message)
            return error_message
        
        print(f"Führe Abfrage aus:\n---\n{query}\n---")
        try:
            with self.engine.connect() as connection:
                df = pd.read_sql_query(query, connection)
            return df
        except Exception as e:
            error_message = f"Fehler bei der SQL-Abfrage: {e}"
            print(error_message)
            return error_message
        finally:
            self.engine.dispose()
