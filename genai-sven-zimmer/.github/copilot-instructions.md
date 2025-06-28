# Anweisungen für GitHub Copilot

## 1. Die Goldene Regel: Konsistenz vor allem

Deine oberste Direktive ist die **strikte Einhaltung der Konsistenz mit der bestehenden Codebasis und den Vorgaben in `code-style.md`**. Bevor du Code schreibst, analysiere den relevanten Workspace-Code (`@workspace`), um etablierte Muster, den Stil und die Architektur zu verstehen. Dein Code soll sich nahtlos in das Projekt einfügen.

---

## 2. Projektspezifische Anweisungen und Muster

Halte dich bei der Implementierung strikt an die folgenden Regeln und Code-Muster.

### a) Projektziel
Das Ziel ist die Entwicklung eines **"Produktleistungs-Agenten"**. Das System analysiert Produktdaten aus einer Datenbank, erstellt Berichte und beantwortet Fragen zur Produktleistung. Die Agenten sind spezialisiert (z.B. `DatenanalyseAgent`, `BerichtsAgent`).

### b) Kerntechnologien
-   **Agenten-Framework:** `openai-agents`
-   **KI-Modell:** `gpt-4o-mini` (ausschließlich)
-   **Datenbankzugriff:** `SQLAlchemy` und `pyodbc`
-   **Datenverarbeitung:** `pandas`

### c) Strikte Code-Muster (Nicht verhandelbar)

**1. API-Aufrufe:**
Verwende **ausschließlich** dieses Muster und das Modell `gpt-4o-mini`.
```python
from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "System-Prompt..."},
        {"role": "user", "content": "User-Anfrage..."}
    ],
    temperature=0.2
)
result = response.choices[0].message.content
```

## 2. Datenbankzugriff:
Der Zugriff erfolgt ausschließlich über SQLAlchemy. Zugangsdaten werden immer aus Umgebungsvariablen geladen.
```python
from sqlalchemy import create_engine
import os
import urllib.parse

# In einer Funktion gekapselt
def get_database_engine():
    # ... Logik zum Laden aus .env und Erstellen der Engine ...
    # Siehe code-style.md für das vollständige Beispiel
    pass
```

## 3. Klassenstruktur für Agenten:
Neue Agenten müssen der Struktur bestehender Agenten folgen.

```python
from openai import OpenAI

class NeuerSpezialistAgent:
    def __init__(self):
        self.client = OpenAI()

    def do_specific_task(self, parameter: str) -> str:
        # Agentenlogik hier
        pass
```

d) Allgemeine Richtlinien
Namenskonventionen: PascalCase für Klassen, snake_case für alles andere.

Keep it Simple: Keine unnötig komplexen Design-Patterns. Orientiere dich an der Einfachheit des bestehenden Codes.

Docstrings & Type Hints: Jede Funktion und Methode benötigt einen klaren Docstring und vollständige Type Hints.

3. Anwendung
Ich werde dich oft an den Kontext dieser Datei erinnern. Deine Aufgabe ist es, diese Regeln als deine primäre Quelle der Wahrheit zu betrachten.