import gradio as gr
from agents import Runner
from dotenv import load_dotenv
import pandas as pd
import os

from audio_transcriber import transcribe_audio
from sql_agent import create_sql_agent
from interpreter_agent import create_interpreter_agent
from database_request import DatabaseRequest

# Lädt Umgebungsvariablen
load_dotenv()

# --- SQL-Generierungs-Agent initialisieren ---
sql_generator_agent = create_sql_agent()
interpreter_agent = create_interpreter_agent()


async def transcribe_and_update_textbox(audio_filepath: str):
    """Nimmt Audio auf, transkribiert es und gibt den Text zurück."""
    if not audio_filepath:
        return "" # Gibt leeren Text zurück, wenn keine Aufnahme da ist
    
    print(f"\n--- Starte Transkription für Audiodatei: {audio_filepath} ---")
    transcribed_text = await transcribe_audio(audio_filepath)
    print(f"Transkript in Textbox geschrieben: '{transcribed_text}'")

    if transcribed_text.startswith("FEHLER:"):
        return transcribed_text # Fehler im Textfeld anzeigen
    
    return transcribed_text

async def handle_submission(user_question: str):
    """Nimmt die finale Frage aus dem Textfeld und startet die Analyse."""
    if not user_question:
        # Versteckt die SQL-Spalte und gibt eine Anweisung zurück
        return gr.update(visible=False), "", "Bitte geben Sie zuerst eine Frage ein oder nehmen Sie eine auf."
    
    # Ruft die Kernlogik auf
    sql, answer = await generate_sql_and_pass_to_request(user_question)
    
    # Schaltet die SQL-Spalte sichtbar und gibt die Ergebnisse zurück
    return gr.update(visible=bool(sql)), sql, answer, user_question
async def generate_sql_and_pass_to_request(user_question: str) -> tuple[str, str]:
    """
    Nimmt eine Benutzerfrage, generiert SQL, führt es aus und generiert eine finale Antwort.
    Gibt den generierten SQL-Code und die finale Antwort als Strings zurück.
    """
    generated_sql = ""

    if not os.getenv("OPENAI_API_KEY"):
        error_message = "FEHLER: OPENAI_API_KEY nicht gefunden. (.env)"
        return "", error_message # Gibt SQL (leer) und Antwort (Fehler) zurück

    print(f"\n--- Verarbeitung Ihrer Frage gestartet ---\nBenutzerfrage: '{user_question}'")

    try:
        # 1. SQL-Code generieren
        generated_sql_output = await Runner.run(sql_generator_agent, user_question)
        generated_sql = generated_sql_output.final_output.strip()

        if not generated_sql.upper().startswith("SELECT"):
            error_message = f"FEHLER: Ungültige oder nicht erlaubte SQL-Anweisung generiert.\nAgenten-Output war:\n{generated_sql}"
            return generated_sql, error_message

    except Exception as e:
        error_message = f"FEHLER beim Generieren der SQL-Abfrage: {str(e)}"
        return generated_sql, error_message

    print(f"\n### Generierter SQL-Code:\n```sql\n{generated_sql}\n```")

    # 2. Datenbankabfrage durchführen
    db_result = DatabaseRequest(generated_sql)

    if not isinstance(db_result, pd.DataFrame):
        error_message = f"FEHLER bei der Datenbankabfrage: {str(db_result)}"
        return generated_sql, error_message

    # 3. Finale Antwort generieren
    df_csv_string = db_result.to_csv(index=False)
    interpreter_agent_inputprompt = f"""<original_frage>{user_question}</original_frage><datenbank_ergebnis>{df_csv_string}</datenbank_ergebnis>"""
    
    print(f"\n--- Übergabe an Antwort-Agenten ---")
    try:
        interpreter_agent_output = await Runner.run(interpreter_agent, interpreter_agent_inputprompt)
        final_answer = interpreter_agent_output.final_output.strip()
    except Exception as e:
        error_message = f"FEHLER beim Generieren der finalen Antwort: {str(e)}"
        return generated_sql, error_message

    print(f"Finale Antwort: {final_answer[:60]}...")
    return generated_sql, final_answer



# ----------------------- Gradio Interface -----------------------

with gr.Blocks(theme=gr.themes.Soft(), title="AdventureBikes Analyst") as demo:
    gr.Markdown(
        """
        # AdventureBikes SQL-Generator und Daten-Analyst
        Stellen Sie Ihre Frage per Text oder Sprache. Der Assistent generiert die passende SQL-Abfrage und liefert das Ergebnis.
        *Anfragendauer: ca. 10-20s*
        """
    )

    # --- Die Ausgabespalte (anfangs versteckt) ---
    with gr.Column(visible=False) as output_column:
        user_question_display = gr.Textbox(label="Ihre gestellte Frage", interactive=False, lines=2)
        sql_code_display = gr.Code(label="Generierter SQL-Code", language="sql", interactive=False, lines=8)

    # --- Finale Antwort (immer sichtbar) ---
    final_answer_display = gr.Textbox(label="Analyse des Daten-Analysten", lines=8, interactive=False, show_copy_button=True)

    # --- Die vereinheitlichte Eingabezeile am Ende ---
    with gr.Row():
        # Das Audio-Widget nimmt die Aufnahme entgegen
        audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Aufnahme 🎙️", elem_id="audio-recorder")
        
        # Das zentrale Textfeld für die Eingabe und Bearbeitung
        question_input = gr.Textbox(
            placeholder="Frage hier eingeben oder per Mikrofon aufnehmen...",
            show_label=False,
            lines=1,
            scale=5, # Macht das Textfeld breiter
            elem_id="text-input-box"
        )
        
        # Der finale Senden-Button
        submit_button = gr.Button("Analysieren", variant="primary", scale=1)

    # --- EVENT-HANDLER ---
    
    # 1. Wenn die Audio-Aufnahme stoppt, wird der Text in das Textfeld geschrieben.
    audio_input.stop_recording(
        fn=transcribe_and_update_textbox,
        inputs=audio_input,
        outputs=question_input # Das Ergebnis der Transkription geht direkt in die Textbox
    )
    
    # 2. Wenn der "Analysieren"-Button geklickt wird, startet der ganze Prozess.
    submit_button.click(
        fn=handle_submission,
        inputs=[question_input],
        # Die Ausgaben aktualisieren die versteckte Spalte und die finale Antwort
        outputs=[output_column, sql_code_display, final_answer_display, user_question_display]
    )

# Startet die Web-Anwendung
if __name__ == "__main__":
    demo.launch()