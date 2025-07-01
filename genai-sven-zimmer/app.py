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

# --- Agenten initialisieren ---
sql_generator_agent = create_sql_agent()
interpreter_agent = create_interpreter_agent()


async def transcribe_and_update_textbox(audio_filepath: str):
    """Nimmt Audio auf, transkribiert es und gibt den Text zurück."""
    if not audio_filepath:
        return ""
    
    print(f"\n--- Starte Transkription für Audiodatei: {audio_filepath} ---")
    transcribed_text = await transcribe_audio(audio_filepath)
    print(f"Transkript in Textbox geschrieben: '{transcribed_text}'")

    if transcribed_text.startswith("FEHLER:"):
        return transcribed_text
    
    return transcribed_text

async def generate_sql_and_pass_to_request(user_question: str) -> tuple[dict, str, str]:
    """
    Nimmt eine Benutzerfrage, generiert SQL, führt es aus und generiert eine finale Antwort.
    Gibt Updates für das Gradio Interface zurück (sichtbare Spalte, SQL-Code, finale Antwort).
    """
    generated_sql = ""

    if not user_question:
        return gr.update(visible=False), "", "Bitte geben Sie zuerst eine Frage ein oder nehmen Sie eine auf."

    if not os.getenv("OPENAI_API_KEY"):
        error_message = "FEHLER: OPENAI_API_KEY nicht gefunden. (.env)"
        return gr.update(visible=False), "", error_message

    print(f"\n--- Verarbeitung Ihrer Frage gestartet ---\nBenutzerfrage: '{user_question}'")

    try:
        # 1. SQL-Code generieren
        generated_sql_output = await Runner.run(sql_generator_agent, user_question)
        generated_sql = generated_sql_output.final_output.strip()

        if not generated_sql.upper().startswith("SELECT"):
            error_message = f"FEHLER: Ungültige oder nicht erlaubte SQL-Anweisung generiert."
            print(f"{error_message}\nAgenten-Output war:\n{generated_sql}")
            return gr.update(visible=True), generated_sql, error_message

    except Exception as e:
        error_message = f"FEHLER beim Generieren der SQL-Abfrage: {str(e)}"
        return gr.update(visible=bool(generated_sql)), generated_sql, error_message

    print(f"\n### Generierter SQL-Code:\n```sql\n{generated_sql}\n```")

    # 2. Datenbankabfrage durchführen
    db_result = DatabaseRequest(generated_sql)

    if not isinstance(db_result, pd.DataFrame):
        error_message = f"FEHLER bei der Datenbankabfrage: {str(db_result)}"
        return gr.update(visible=True), generated_sql, error_message

    # 3. Finale Antwort generieren
    df_csv_string = db_result.to_csv(index=False)
    interpreter_agent_inputprompt = f"""<original_frage>{user_question}</original_frage><datenbank_ergebnis>{df_csv_string}</datenbank_ergebnis>"""
    
    print(f"\n--- Übergabe an Antwort-Agenten ---")
    try:
        interpreter_agent_output = await Runner.run(interpreter_agent, interpreter_agent_inputprompt)
        final_answer = interpreter_agent_output.final_output.strip()
    except Exception as e:
        error_message = f"FEHLER beim Generieren der finalen Antwort: {str(e)}"
        return gr.update(visible=True), generated_sql, error_message

    print(f"Finale Antwort: {final_answer[:60]}...")
    return gr.update(visible=True), generated_sql, final_answer

# ----------------------- Gradio Interface (Neues Layout) -----------------------

with gr.Blocks(
    theme=gr.themes.Soft(),
    title="AdventureBikes Business Intelligence",
    css=".container { max-width: 1000px; margin: auto; padding: 20px; }"
) as demo:
    # Header-Bereich
    gr.Markdown(
        """
        # 🚲 AdventureBikes Analytics
        ### Ihr KI-gestützter Business Intelligence Assistent
        """
    )

    gr.Markdown(
            """
            > - Beispiel: "Erlöse von jedem Monat von 2021 bis Februar 2022."
            > - Beispiel: "Wie oft haben wir im Januar 2021 City Bikes verkauft?"
            """
        )
    
    # Haupteingabefeld für Text
    question_input = gr.Textbox(
        label="Ihre Frage zur Geschäftsanalyse",
        placeholder="z.B. Zeige mir den Umsatz für 'Mountain Bikes' im letzten Jahr.",
        lines=3
    )

    # Zeile für Audio-Eingabe (links) und SQL-Ausgabe (rechts)
    with gr.Row():
        with gr.Column(scale=1, min_width=250):
             audio_input = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label="🎙️ ODER Spracheingabe nutzen"
            )
        
        # Diese Spalte ist anfangs unsichtbar und wird bei Bedarf eingeblendet
        with gr.Column(scale=3, visible=False) as sql_output_column:
            sql_code_display = gr.Code(
                label="Generierter SQL-Code",
                language="sql",
                interactive=False,
                lines=8
            )
    
    # Senden-Button
    submit_button = gr.Button("🔍 Analyse starten", variant="primary")
    
    # Finale Antwort-Box
    final_answer_display = gr.Textbox(
        label="Ergebnis der Analyse",
        lines=8,
        interactive=False,
        show_copy_button=True
    )

    # Footer
    gr.Markdown(
        "*⏱️ Die Verarbeitung dauert typischerweise 10-20 Sekunden.*"
    )

    # --- EVENT-HANDLER ---
    
    # 1. Audio-Aufnahme verarbeiten
    audio_input.stop_recording(
        fn=transcribe_and_update_textbox,
        inputs=audio_input,
        outputs=question_input
    )
    
    # 2. Text-Eingabe verarbeiten
    submit_button.click(
        fn=generate_sql_and_pass_to_request,
        inputs=question_input,
        outputs=[sql_output_column, sql_code_display, final_answer_display]
    )

# Startet die Web-Anwendung
if __name__ == "__main__":
    demo.launch()