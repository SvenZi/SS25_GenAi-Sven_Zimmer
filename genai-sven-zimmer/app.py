import gradio as gr
from agents import Runner
from dotenv import load_dotenv
import os
import re
import pandas as pd

from sql_agent import create_sql_agent, create_response_agent
from database_request import DatabaseRequest

# Lädt Umgebungsvariablen
load_dotenv()

# --- SQL-Generierungs-Agent initialisieren ---
sql_generator_agent = create_sql_agent()
response_agent = create_response_agent()


# --- Asynchrone Funktion für die Gradio-Schnittstelle (Der Orchestrator) ---
async def generate_sql_and_pass_to_request(user_question: str) -> str:
    """
    Nimmt die Nutzerfrage, lässt den Agenten die SQL-Abfrage generieren,
    führt diese aus und lässt das Ergebnis von einem weiteren Agenten analysieren,
    um eine Antwort in natürlicher Sprache zu erstellen.
    """
    if not os.getenv("OPENAI_API_KEY"):
        return "FEHLER: OPENAI_API_KEY nicht gefunden in den Umgebungsvariablen."

    print(f"\n--- Verarbeitung Ihrer Frage gestartet ---")
    print(f"Benutzerfrage: '{user_question}'")
    
    # 1. SQL-Abfrage durch den Agenten generieren lassen
    try:
        sql_agent_response = await Runner.run( # Variable umbenannt
            sql_generator_agent, 
            user_question
        )
    except Exception as e:
        print(f"FEHLER beim SQL-Agentenlauf: {str(e)}")
        return f"FEHLER beim Generieren der SQL-Abfrage durch den Agenten: {str(e)}"
    
    sql_match = re.search(r'<sql>(.*?)</sql>', sql_agent_response.final_output, re.DOTALL)
    
# Fehlerbehandlung: Wenn kein gültiger SQL-Code gefunden wurde
    if not sql_match:
        print(f"FEHLER: Agent konnte keinen gültigen SQL-Code im <sql>-Tag finden.")
        print(f"Agentenantwort war:\n{sql_agent_response.final_output}")
        return "FEHLER: Der Agent konnte keinen gültigen SQL-Code generieren."
#-------

    generated_sql = sql_match.group(1).strip()
    print(f"\n### Generierter SQL-Code:\n```sql\n{generated_sql}\n```") # Zeige SQL auch in der Konsole

    # 2. Den generierten SQL-Code an die DatabaseRequest-Funktion weitergeben
    db_result = DatabaseRequest(generated_sql)
    
    # 3. Ergebnis der Datenbankabfrage an den Antwort-Agenten übergeben
    # Erstelle den Prompt für den Antwort-Agenten
    # WICHTIG: DataFrame muss in einen String umgewandelt werden, damit der Agent ihn lesen kann.
    if isinstance(db_result, pd.DataFrame):
        db_result_str = db_result.to_string() # Konvertiert DataFrame zu String
    else:
        db_result_str = str(db_result) # Wenn es ein Fehler-String ist, einfach konvertieren

    response_agent_prompt = f"""
<original_frage>
{user_question}
</original_frage>
<datenbank_ergebnis>
{db_result_str}
</datenbank_ergebnis>
"""
    print(f"\n--- Übergabe an Antwort-Agenten ---")
    print(f"Prompt für Antwort-Agenten:\n{response_agent_prompt}")

    try:
        final_response_agent_output = await Runner.run(
            response_agent,
            response_agent_prompt
        )
    except Exception as e:
        print(f"FEHLER beim Antwort-Agentenlauf: {str(e)}")
        return f"FEHLER beim Generieren der Antwort durch den Agenten: {str(e)}"

    # Extrahiere die finale Antwort aus den <antwort>-Tags
    response_match = re.search(r'<antwort>(.*?)</antwort>', final_response_agent_output.final_output, re.DOTALL)

    if not response_match:
        print(f"FEHLER: Antwort-Agent konnte keine gültige Antwort im <antwort>-Tag finden.")
        print(f"Antwort-Agenten-Output war:\n{final_response_agent_output.final_output}")
        return "FEHLER: Der Antwort-Agent konnte keine gültige Antwort generieren."

    final_answer = response_match.group(1).strip()
    print(f"\n--- Finale Antwort des Agenten ---")
    print(final_answer)

    # Rückgabe der finalen Antwort für das Gradio-UI
    return final_answer

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # AdventureBikes SQL-Generator & Daten-Analyst
        Stellen Sie eine Frage in natürlicher Sprache. Der Assistent generiert die passende SQL-Abfrage,
        führt diese aus und analysiert das Ergebnis, um eine Antwort zu erstellen.
        Die generierte SQL-Abfrage und detaillierte Debug-Informationen werden in der Konsole ausgegeben.
        """
    )
    
    question_input = gr.Textbox(
        label="Ihre Frage an den Daten-Analysten", 
        placeholder="z.B. Zeige mir den Umsatz für 'Mountain Bikes' im letzten Jahr.",
        lines=3
    )
    
    submit_button = gr.Button("Antwort generieren", variant="primary")
    
    
    final_answer_display = gr.Textbox(
        label="Antwort des Daten-Analysten", 
        lines=10,
        interactive=False,
        show_copy_button=True
    )

    submit_button.click(
        fn=generate_sql_and_pass_to_request,
        inputs=question_input,
        outputs=final_answer_display
    )

# Startet die Web-Anwendung
if __name__ == "__main__":
    demo.launch()