# AdventureBikes Analytics Platform

**- Semesterabgabe: Sommersemester 2025 -**  
Einzelprojekt; Interaktive Datenbank | Sven Zimmer (ehemalig: Gruppe 2)  
Kurs: GenAI  
bei Jan Kirenz, Professor

## Projektübersicht

Dieses Projekt implementiert eine intelligente Business Intelligence Plattform für AdventureBikes, die natürlichsprachliche Benutzeranfragen in SQL-Abfragen transformiert und die Ergebnisse benutzerfreundlich aufbereitet. Das System basiert auf einer mehrschichtigen Agenten-Architektur und einer SQL-Datenbank.

## Schnellstart

```bash
# Voraussetzungen
- Python 3.11+
- MSSQL ODBC Driver 17
- OpenAI API Key

# Installation
git clone <repository-url>
cd genai-sven-zimmer

# Virtuelle Umgebung erstellen und aktivieren
python -m venv .venv
source .venv/bin/activate  # Unter Windows: .venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Konfiguration
# Erstellen Sie eine .env Datei mit folgenden Variablen:
# OPENAI_API_KEY=your-api-key
# DB_SERVER=your-server
# DB_NAME=your-database
# DB_USERNAME=your-username
# DB_PASSWORD=your-password

# Anwendung starten
python app.py
```

## Systemarchitektur

### 1. Benutzeroberfläche (`app.py`)

Die Benutzeroberfläche basiert auf Gradio und bietet eine intuitive Interaktion mit dem System.

**Hauptkomponenten:**
- Textuelle Eingabe für Geschäftsanalysefragen
- Spracheingabe mit automatischer Transkription
- SQL-Code-Anzeige für Transparenz
- Ergebnisanzeige mit formatierten Antworten

**Signatur der Hauptfunktion:**
```python
async def generate_sql_and_pass_to_request(user_question: str) -> tuple[dict, str, str]
```

**Ablauf:**
1. **Validierung der Eingabe**
   * Prüft auf leere Eingaben
   * Validiert OpenAI API-Key
   * Logging der Benutzerfrage

2. **SQL-Generierung**
   * Übergibt Frage an SQL-Generator-Agent
   * Validiert generierten SQL-Code
   * Prüft auf erlaubte SELECT-Statements

3. **Datenbankabfrage**
   * Führt generierte SQL-Abfrage aus
   * Konvertiert Ergebnis in DataFrame
   * Fehlerbehandlung bei Datenbankproblemen

4. **Antwortgenerierung**
   * Übergibt Ergebnis an Interpreter-Agent
   * Formatiert finale Antwort
   * Aktualisiert UI-Komponenten

### 2. Audio-Integration (`audio_transcriber.py`)

**Signatur:**
```python
async def transcribe_audio(audio_filepath: str) -> str
```

**Zweck:**
Ermöglicht Spracheingaben durch Integration mit OpenAI's Whisper API.

**Ablauf:**
1. **Initialisierung**
   * Validiert API-Key und Audio-Datei
   * Konfiguriert Whisper-Modell
   * Setzt Kontext-Prompts

2. **Transkription**
   * Öffnet Audio-Datei
   * Sendet an Whisper API
   * Empfängt Transkription

3. **Fehlerbehandlung**
   * Validiert API-Antwort
   * Behandelt Fehler
   * Formatiert Rückgabe

### 3. Agenten-System

#### 3.1 SQL-Generator Agent (`sql_agent.py`)

**Signatur:**
```python
def create_sql_agent() -> Agent
```

**Zweck:**
Transformiert natürlichsprachliche Anfragen in präzise SQL-Abfragen.

**Ablauf:**
1. **Initialisierung**
   * Lädt spezialisierten System-Prompt
   * Konfiguriert GPT-4-Mini-Modell
   * Initialisiert Agent-Tools

2. **Analyse**
   * Verarbeitet Benutzeranfrage
   * Identifiziert Schlüsselkomponenten
   * Validiert Anfrage-Parameter

3. **SQL-Generierung**
   * Erstellt SQL-Template
   * Fügt Parameter ein
   * Validiert SQL-Syntax

#### 3.2 Interpreter Agent (`interpreter_agent.py`)

**Signatur:**
```python
def create_interpreter_agent() -> Agent
```

**Zweck:**
Konvertiert technische Datenbankresultate in verständliche natürlichsprachliche Antworten.

**Ablauf:**
1. **Initialisierung**
   * Lädt Interpreter-Prompt
   * Konfiguriert Modell-Parameter
   * Setzt Formatierungsregeln

2. **Analyse**
   * Verarbeitet Datenbankresultat
   * Extrahiert relevante Daten
   * Identifiziert Schlüsselmetriken

3. **Antwortgenerierung**
   * Formuliert natürliche Antwort
   * Formatiert Zahlen und Daten
   * Strukturiert Ausgabe

### 4. Datenbank-Integration (`database_request.py`)

**Hauptfunktion:**
```python
def DatabaseRequest(sql_query: str) -> pd.DataFrame | str
```

**Zweck:**
Handhabt die sichere Ausführung von SQL-Abfragen und Ergebnisformatierung.

**Ablauf:**
1. **Verbindungsaufbau**
   * Lädt Konfiguration aus .env
   * Initialisiert SQLAlchemy Engine
   * Validiert Verbindung
   * Implementiert Connection Pooling

2. **Query-Ausführung**
   * Validiert SQL-Statement
   * Führt Abfrage aus
   * Konvertiert zu DataFrame
   * Optimiert Performance

3. **Fehlerbehandlung**
   * Erkennt Verbindungsprobleme
   * Behandelt SQL-Fehler
   * Implementiert Timeouts
   * Formatiert Fehlermeldungen

## Datenbankschema

### Haupttabellen

1. **DataSet_Monthly_Sales**
   - Monatliche Verkaufsübersicht
   - Enthält: Revenue, Sales_Amount, Discounts
   - Währungs- und Regionsinformationen
   - Produktkategorisierung

2. **Facts_Daily_Sales**
   - Tägliche Verkaufstransaktionen
   - Order- und Shipping-Dates
   - Revenue und Discounts
   - Verkaufsmengen

3. **Dim_Product**
   - Produktstammdaten
   - Material_Description
   - Product_Category
   - Preise und Transfer_Price_EUR
   - Shipping_Days

4. **Dim_Sales_Office**
   - Verkaufsbüro-Details
   - Geografische Zuordnung
   - Währungszuordnung
   - Regionale Hierarchie

### Dimensionstabellen

1. **Dim_Calendar**
   - Datumshierarchien
   - ISO-Formate
   - Geschäftsperioden
   - Month/Quarter Aggregationen

2. **Dim_Currency**
   - Währungscodes
   - Wechselkurse
   - Formatierungsinformationen
   - Referenzwährungen

## Fehlerbehandlung

### 1. Eingabevalidierung
- Prüft Benutzereingaben auf Vollständigkeit
- Validiert API-Keys und Konfiguration
- Protokolliert Eingabefehler
- Formatvalidierung

### 2. SQL-Generierung
- Validiert SQL-Syntax
- Prüft auf erlaubte Operationen
- Behandelt Injection-Versuche
- Loggt Generierungsprozess

### 3. Datenbankzugriff
- Connection Pool Management
- Automatische Reconnects
- Query Timeouts
- Error Logging

### 4. Antwortgenerierung
- Validiert Agenten-Outputs
- Prüft Datenformate
- Implementiert Fallbacks
- Fehlerbenachrichtigungen

## Konfiguration

### Umgebungsvariablen (.env)
```plaintext
# OpenAI Konfiguration
OPENAI_API_KEY=your-api-key
OPENAI_WHISPER_MODEL=whisper-1

# Datenbank Konfiguration
DB_SERVER=your-server
DB_NAME=your-database
DB_USERNAME=your-username
DB_PASSWORD=your-password
DB_PORT=1433
```

## Entwicklung

### Voraussetzungen
- Python 3.11+
- MSSQL ODBC Driver 17
- OpenAI API Zugang
- Gradio 5.34.2+
- SQLAlchemy 2.0.41+

### Bibliotheken & Tools
- `openai-agents`: KI-Agenten Framework
- `gradio`: Web Interface
- `sqlalchemy`: DB Access
- `pandas`: Datenverarbeitung
- `python-dotenv`: Konfiguration

### Best Practices

1. **Code-Qualität**
   - PEP 8 Konformität
   - Type Hints
   - Docstrings
   - Unit Tests

2. **Sicherheit**
   - SQL-Injection Prevention
   - API-Key Management
   - Logging Standards
   - Error Handling

3. **Performance**
   - Connection Pooling
   - Query Optimization
   - Caching Strategien
   - Async Operations

4. **Dokumentation**
   - Code-Kommentare
   - API-Dokumentation
   - Changelog
   - Setup-Guide

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.
