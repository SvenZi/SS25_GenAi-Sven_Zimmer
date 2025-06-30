import gradio as gr
from agents import Runner, Tool
from dotenv import load_dotenv
import os
import re
import json # Für das Parsen der JSON-Antwort des Datenbank-Tools

# Importiert die Bausteine aus den anderen Dateien
from sql_agent import create_sql_agent
from database import DatabaseTool

# Lädt die Umgebungsvariablen
load_dotenv()

# --- 1. Werkzeug und Agent initialisieren ---
# Instanz des Datenbank-Tools mit den Guardrails erstellen
db_tool_instance = DatabaseTool()

# WICHTIG: Das Datenbank-Tool WIRD NICHT DIREKT an den Agenten gegeben,
# da der Agent NUR SQL GENERIEREN soll.
# Das Tool wird MANUELL im Workflow aufgerufen.
# Das Tool(name=..., func=..., description=...) wird hier nicht benötigt,
# da der Agent es nicht selbst aufrufen soll.
# Stattdessen verwenden wir direkt db_tool_instance.execute_sql_query()

# Den finalen, intelligenten Agenten erstellen.
# Er erhält KEINE Tools in diesem Workflow, da er nur SQL generieren soll.
sql_analyst_agent = create_sql_agent(
    # Keine Tools für den SQL-Generierungs-Agenten, da er sie nicht ausführen soll.
    # Sein Prompt ist darauf ausgelegt, SQL als Text auszugeben.
    db_tool=None # Wir übergeben hier explizit None oder lassen es weg, je nach create_sql_agent Signatur
)


# --- 2. Asynchrone Funktion für die Gradio-Schnittstelle ---
async def get_sql_from_agent(user_question: str) -> str:
    """
    Nimmt die Nutzerfrage, lässt den Agenten die SQL-Abfrage generieren,
    führt diese dann aus und gibt das Ergebnis zurück.
    """
    if not os.getenv("OPENAI_API_KEY"):
        return "FEHLER: OPENAI_API_KEY nicht gefunden."

    print(f"Schritt 1: Anfrage wird an den Agenten gesendet, um SQL zu generieren: '{user_question}'")
    
    # Führe den Agenten aus, um den SQL-Code zu erhalten
    # Der Agent ist hier ein reiner Textgenerator basierend auf dem Prompt
    try:
        agent_result = await Runner.run(
            sql_analyst_agent, 
            user_question,
            #max_output_tokens=1500 # Sicherheitsnetz für die Kostenkontrolle
        )
    except Exception as e:
        return f"FEHLER beim Generieren der SQL-Abfrage durch den Agenten: {str(e)}"
    
    # Extrahiere den SQL-Code sicher aus den <sql>-Tags.
    match = re.search(r'<sql>(.*?)</sql>', agent_result.final_output, re.DOTALL)
    
    if not match:
        # Falls der Agent keine gültige SQL-Antwort im Tag-Format gibt
        print(f"Fehler: Konnte keine SQL-Abfrage im <sql>-Tag finden. Antwort war:\n{agent_result.final_output}")
        return "Fehler: Der Agent konnte keine gültige SQL-Abfrage generieren."
    
    sql_query = match.group(1).strip()
    print(f"Schritt 2: Generierte SQL-Abfrage:\n{sql_query}")

    # Schritt 3: Die generierte SQL-Abfrage manuell über das Datenbank-Tool ausführen
    print("Schritt 3: Führe die SQL-Abfrage über das Datenbank-Tool aus...")
    try:
        db_response_json_str = db_tool_instance.execute_sql_query(sql_query)
        db_response = json.loads(db_response_json_str)

        if "error" in db_response:
            return f"FEHLER bei der Datenbankabfrage: {db_response['error']}"
        else:
            # Erfolgreiche Abfrage
            # Formatiere das JSON-Ergebnis für eine bessere Lesbarkeit in Gradio
            formatted_output = "### SQL-Abfrage:\n```sql\n" + sql_query + "\n```\n\n### Datenbankergebnis:\n```json\n" + json.dumps(db_response, indent=2) + "\n```"
            return formatted_output

    except json.JSONDecodeError:
        return f"FEHLER: Ungültige JSON-Antwort vom Datenbank-Tool: {db_response_json_str}"
    except Exception as e:
        return f"FEHLER beim Ausführen der SQL-Abfrage: {str(e)}"


# --- 3. Erstellung der Gradio-App ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # AdventureBikes SQL-Generator & Ausführer
        Stellen Sie eine Frage in natürlicher Sprache. Der Assistent generiert die passende SQL-Abfrage und führt sie direkt aus.
        """
    )
    
    question_input = gr.Textbox(
        label="Ihre Frage an die Datenbank", 
        placeholder="z.B. Was war der Umsatz für Mountain Bikes im Jahr 2024?",
        lines=3
    )
    
    submit_button = gr.Button("SQL generieren & ausführen", variant="primary")
    
    answer_output = gr.Textbox(
        label="Generierte SQL-Abfrage & Datenbankergebnis", 
        lines=15, # Mehr Zeilen, da jetzt SQL UND Ergebnis angezeigt werden
        interactive=False,
        show_copy_button=True
    )

    submit_button.click(
        fn=get_sql_from_agent,
        inputs=question_input,
        outputs=answer_output
    )

# Startet die Web-Anwendung
if __name__ == "__main__":
    demo.launch()
