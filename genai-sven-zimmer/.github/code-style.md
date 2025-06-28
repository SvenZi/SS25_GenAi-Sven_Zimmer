# Code Style Guide für den "Produktleistungs-Agenten"

Dieses Dokument definiert die Code-Konventionen und Best Practices für dieses Projekt. Alle Beiträge müssen sich an diese Richtlinien halten.

## 1. Reihenfolge der Imports
Imports werden in drei Blöcken organisiert, getrennt durch eine Leerzeile:
1.  **Standard-Bibliothek** (z.B. `os`, `datetime`)
2.  **Externe Bibliotheken** (z.B. `pandas`, `sqlalchemy`, `openai`)
3.  **Lokale Anwendungsmodule** (z.B. `datenanalyse_agent`)

**Beispiel:**
```python
import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

from datenanalyse_agent import DatenanalyseAgent
from berichts_agent import BerichtsAgent
```

## 2. Definition von Klassen
Klassen folgen einem konsistenten Aufbau. Der OpenAI-Client wird einmal in der __init__-Methode initialisiert.

**Beispiel für einen spezialisierten Agenten:**
```python
from openai import OpenAI

class DatenanalyseAgent:
    def __init__(self):
        self.client = OpenAI()

    def analyze_performance(self, product_id: str, metrics: list[str]) -> dict:
        """Analysiert die Leistung eines Produkts basierend auf gegebenen Metriken."""
        # ... Implementierung ...
```

## 3. API-Aufrufe (Strikte Vorgabe)
Im gesamten Projekt wird ausschließlich das Modell gpt-4o-mini verwendet. Abweichungen sind nicht gestattet. API-Aufrufe müssen dem folgenden Muster folgen:

```python
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Client-Initialisierung
client = OpenAI()

# Standard-API-Aufruf
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "System-Prompt für die spezifische Aufgabe."},
        {"role": "user", "content": "Die konkrete Anfrage oder Daten für den User."}
    ],
    temperature=0.2 # Niedrige Temperatur für präzise, faktenbasierte Analyse
)

result = response.choices[0].message.content
```

## 4. Datenbank-Verbindungen (Strikte Vorgabe)
Der Datenbankzugriff erfolgt ausschließlich über die SQLAlchemy-Bibliothek. Sensible Zugangsdaten (Username, Passwort etc.) müssen aus einer .env-Datei geladen werden.

**Beispiel für eine Verbindungsfunktion:**

```python
import os
import urllib.parse
from sqlalchemy import create_engine
from dotenv import load_dotenv

def get_database_engine():
    """Erstellt und testet eine SQLAlchemy-Engine basierend auf Umgebungsvariablen."""
    load_dotenv()
    
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_DATABASE')
    username = os.getenv('DB_USER')
    password = urllib.parse.quote_plus(os.getenv('DB_PASSWORD'))
    
    # Der Treiberpfad ist spezifisch für eine Mac/Homebrew-Installation
    driver_path = '?driver=/opt/homebrew/lib/libmsodbcsql.17.dylib'
    
    conn_str = f'mssql+pyodbc://{username}:{password}@{server}/{database}{driver_path}'

    try:
        engine = create_engine(conn_str)
        # Kurzer Verbindungstest
        connection = engine.connect()
        connection.close()
        print("Datenbankverbindung erfolgreich hergestellt.")
        return engine
    except Exception as e:
        print(f"Fehler bei der Datenbankverbindung: {e}")
        return None
```


## 5. Kommentare und Docstrings
Methoden und Funktionen werden mit Triple-Quote Docstrings dokumentiert, die den Zweck, die Parameter (:param:) und den Rückgabewert (:return:) beschreiben.

```python
def analyze_performance(self, product_id: str, metrics: list[str]) -> dict:
    """
    Analysiert die Leistung eines Produkts und gibt ein Ergebnis-Dictionary zurück.

    :param product_id: Die ID des zu analysierenden Produkts.
    :param metrics: Eine Liste von Metriken, die analysiert werden sollen.
    :return: Ein Dictionary mit den Analyseergebnissen.
    """
    # Inline-Kommentare erklären komplexe Logik
    pass
```

## 6. Namenskonventionen
Klassen: PascalCase (z.B. ProduktleistungsAgent, DatenanalyseAgent)

Variablen & Funktionen: snake_case (z.B. performance_data, get_sales_figures)

Dateien: snake_case (z.B. datenanalyse_agent.py)