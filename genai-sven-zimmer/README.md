# SS25_GenAi-Sven_Zimmer 

**- Semesterabgabe: Sommersemester 2025 -**
Einzelprojekt; Interaktive Datenbank | Sven Zimmer (ehemalig: Gruppe 2)
Kurs:
GenAI
bei Jan Kirenz, Professor

# AdventureBikes Datenanalyse-System

## Schnellstart

```bash
# Projektinitialisierung
uv init genai-sven-zimmer --python 3.11

# Projekt starten
cd genai-sven-zimmer
uv-sync
source .venv/bin/activate

python app.py
```

## Projektübersicht

Dieses Projekt implementiert ein intelligentes Datenanalyse-System für AdventureBikes, das natürlichsprachliche Benutzeranfragen in SQL-Abfragen übersetzt und die Ergebnisse benutzerfreundlich aufbereitet. Das System nutzt eine Kombination aus LLM-basierten Agenten und einer SQL-Datenbank, um komplexe Geschäftsfragen zu beantworten.

## Systemarchitektur

### 1. Benutzeroberfläche

**Komponente:** `app.py`  
**Technologie:** Gradio Web Interface

Die Benutzeroberfläche ermöglicht:
- Eingabe von natürlichsprachlichen Fragen
- Anzeige der generierten Antworten
- Debug-Informationen in der Konsole

### 2. Hauptkomponenten

#### 2.1 Orchestrator (`generate_sql_and_pass_to_request`)

**Signatur:**  
`async def generate_sql_and_pass_to_request(user_question: str) -> str`

**Ablauf:**
1. **Validierung der Umgebung**
   - Prüft auf vorhandenen OPENAI_API_KEY
   - Initialisiert Debug-Logging

2. **SQL-Generierung**
   - Übergibt die Benutzerfrage an den SQL-Generator-Agenten
   - Extrahiert den SQL-Code aus den XML-Tags
   - Validiert die generierte SQL-Abfrage

3. **Datenbankabfrage**
   - Führt die generierte SQL-Abfrage aus
   - Wandelt das Ergebnis in das gewünschte Format um

4. **Antwortgenerierung**
   - Übergibt Datenbankresultat an den Antwort-Agenten
   - Formatiert die finale Antwort in natürlicher Sprache

### 3. Agenten-System

#### 3.1 SQL-Generator Agent (`sql_agent.py`)

**Verantwortlichkeiten:**
- Analysiert natürlichsprachliche Anfragen
- Generiert valide SQL-Abfragen
- Berücksichtigt das Datenbankschema
- Markiert SQL-Code mit XML-Tags

#### 3.2 Antwort-Agent (`sql_agent.py`)

**Verantwortlichkeiten:**
- Interpretiert Datenbankergebnisse
- Generiert natürlichsprachliche Antworten
- Formatiert Antworten benutzerfreundlich

### 4. Datenbankzugriff

#### 4.1 Datenbankverbindung (`_database.py`, `database_request.py`)

**Klasse:** `DatabaseTool`  
**Hauptfunktionen:**
```python
def get_database_engine() -> Engine | None
def execute_sql_query(sql_query: str) -> pd.DataFrame | str
```

**Konfiguration:**
- Verwendet Environment-Variablen für Zugangsdaten
- Unterstützt MSSQL über ODBC
- Implementiert Connection Pooling

#### 4.2 Datenmodell

Das System arbeitet mit einem komplexen Datenbankschema für Verkaufsdaten:

**Haupttabellen:**
- `DataSet_Monthly_Sales`: Monatliche Verkaufsübersicht
- `Facts_Daily_Sales`: Tägliche Verkaufstransaktionen
- `Dim_Product`: Produktinformationen
- `Dim_Sales_Office`: Verkaufsbüro-Details
- `Facts_Currency_Rates`: Währungskurse

## Installation & Setup

### 1. Voraussetzungen
- Python 3.11+
- MSSQL Server
- ODBC-Treiber 17 für SQL Server

### 2. Umgebungsvariablen
Erstellen Sie eine `.env`-Datei mit:
```
DB_SERVER=server_name
DB_NAME=database_name
DB_USERNAME=username
DB_PASSWORD=password
OPENAI_API_KEY=your_api_key
```

### 3. Installation
```bash
# Virtual Environment erstellen und aktivieren
python -m venv venv
source venv/bin/activate  # oder unter Windows: venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt
```

## Verwendung

1. Starten Sie die Anwendung:
```bash
python app.py
```

2. Öffnen Sie die Web-Oberfläche (Standard: http://localhost:7860)

3. Stellen Sie Ihre Frage in natürlicher Sprache, zum Beispiel:
   - "Wie hoch war der Umsatz für Mountain Bikes im letzten Monat?"
   - "Zeige mir die Top 5 Verkaufsländer nach Umsatz."
   - "Vergleiche die Verkaufszahlen von Racing Bikes und Mountain Bikes."

## Entwicklertools

### Schema-Analyse (`generate_schema.py`)

**Hauptfunktionen:**
```python
def generate_schema_script(engine: Engine) -> str
def analyze_categorical_data(engine: Engine) -> str
def analyze_date_ranges(engine: Engine) -> str
def generate_product_catalog(engine: Engine) -> str
```

Diese Tools helfen bei der:
- Automatischen Schema-Dokumentation
- Analyse von Datenbereichen
- Erstellung von Produktkatalogen

## Fehlerbehandlung

Das System implementiert eine mehrstufige Fehlerbehandlung:

1. **Umgebungsvariablen-Validierung**
   - Prüft auf vollständige Konfiguration
   - Gibt klare Fehlermeldungen bei fehlenden Werten

2. **SQL-Generierung**
   - Validiert XML-Tags
   - Prüft SQL-Syntax
   - Fehlerberichte bei ungültigen Anfragen

3. **Datenbankzugriff**
   - Connection Pool Management
   - Automatische Reconnect-Versuche
   - Detaillierte Fehlermeldungen

4. **Antwortgenerierung**
   - Validierung der Agenten-Outputs
   - Formatierungsprüfungen
   - Fallback-Antworten bei Fehlern

## Projektstruktur

```
genai-sven-zimmer/
├── app.py                 # Hauptanwendung & Web-Interface
├── _database.py          # Datenbankzugriff & Verbindungsverwaltung
├── database_request.py   # SQL-Ausführung & Ergebnisformatierung
├── generate_schema.py    # Schema-Analyse & Dokumentation
├── sql_agent.py         # LLM-basierte Agenten
└── _utils.py            # Hilfsfunktionen & Utilities
```

## Best Practices für Entwickler

1. **SQL-Generierung**
   - Nutzen Sie vorhandene Views wenn möglich
   - Achten Sie auf Performance bei komplexen Joins
   - Validieren Sie generierte Abfragen

2. **Fehlerbehandlung**
   - Implementieren Sie spezifische Ausnahmen
   - Loggen Sie detaillierte Fehlerinformationen
   - Bieten Sie hilfreiche Fehlermeldungen

3. **Agenten-Entwicklung**
   - Testen Sie verschiedene Prompt-Varianten
   - Dokumentieren Sie Prompt-Strukturen
   - Implementieren Sie Feedback-Schleifen
