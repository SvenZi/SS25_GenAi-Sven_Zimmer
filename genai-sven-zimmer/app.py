import gradio as gr
from agents import Runner
from dotenv import load_dotenv
import pandas as pd
import os

from sql_agent import create_sql_agent
from interpreter_agent import create_interpreter_agent
from database_request import DatabaseRequest

# Lädt Umgebungsvariablen
load_dotenv()

# --- SQL-Generierungs-Agent initialisieren ---
sql_generator_agent = create_sql_agent()
interpreter_agent = create_interpreter_agent()


async def generate_sql_and_pass_to_request(user_question: str) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return "FEHLER: OPENAI_API_KEY nicht gefunden in den Umgebungsvariablen. (.env)"

    print(f"\n--- Verarbeitung Ihrer Frage gestartet ---")
    print(f"Benutzerfrage: '{user_question}'")
    
    try:
        generated_sql_output = await Runner.run( 
            sql_generator_agent, 
            user_question
        ) # Out: SQL-Query (Modell: gpt-4o-mini)
        generated_sql = generated_sql_output.final_output.strip()

# !! __________ Zugriffsberechtigung für den Agenten bestimmen!
        if not generated_sql.upper().startswith(("SELECT")): # Nur Leseberechtigung
        #if not generated_sql.upper().startswith(("SELECT", "INSERT", "CREATE",)): # Keine erlaubnis zum Löschen oder Verändern | Einfügen erlaubt!            
# !! __________


#Error-Handling: Prüfen, ob der Agent eine Fehlermeldung generiert ha
            if "FEHLER:" in generated_sql.upper() or "ERROR:" in generated_sql.upper():
                 print(f"FEHLER: Agent hat eine Fehlermeldung statt SQL generiert.")
                 print(f"Agenten-Output war:\n{generated_sql_output.final_output}")
                 return f"FEHLER: Der Agent hat einen internen Fehler gemeldet: {generated_sql_output.final_output}"
            else:
                print(f"FEHLER: Agent konnte keinen gültigen SQL-Code generieren.")
                print(f"Agenten-Output war:\n{generated_sql_output.final_output}")
                return "FEHLER: Der Agent konnte keinen gültigen SQL-Code generieren."
    except Exception as e:
        print(f"FEHLER beim SQL-Agentenlauf: {str(e)}")
        return f"FEHLER beim Generieren der SQL-Abfrage durch den Agenten: {str(e)}"
#-------------------------

    print(f"\n### Generierter SQL-Code:\n```sql\n{generated_sql}\n```")


    df = DatabaseRequest(generated_sql)
    
    if isinstance(df, pd.DataFrame):
        df_result = df.to_csv(index=False) 
    else:
        df_result = str(df) # Wenn es ein Fehler-String ist, einfach konvertieren


    interpreter_agent_inputprompt = f"""
                                    <original_frage>
                                    {user_question}
                                    </original_frage>
                                    <datenbank_ergebnis>
                                    {df_result}
                                    </datenbank_ergebnis>
                                    """
    print(f"\n--- Übergabe an Antwort-Agenten ---")

    try:
        interpreter_agent_output = await Runner.run(
            interpreter_agent,
            interpreter_agent_inputprompt
        )
    except Exception as e:
        print(f"FEHLER beim Antwort-Agentenlauf: {str(e)}")
        return f"FEHLER beim Generieren der Antwort durch den Agenten: {str(e)}"

    final_answer = interpreter_agent_output.final_output.strip()    
    print(f"{final_answer[:40]}...")

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