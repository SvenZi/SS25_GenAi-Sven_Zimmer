import gradio as gr
from agents import Runner
from dotenv import load_dotenv
import pandas as pd
import os

from audio_transcriber import transcribe_audio
from sql_agent import create_sql_agent
from interpreter_agent import create_interpreter_agent
from database_request import DatabaseRequest

custom_css = """
/* --- Globaler Stil & Hintergrund --- */
body {
    font-family: 'Helvetica Neue', sans-serif !important;
}

.gradio-container {
    width: 80% !important;
    background-color: none !important;
    border-radius: 5px !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2) !important;
    margin: 40px auto !important;
}

textarea {
    background-color: rgba(255, 255, 255, 0.5) !important;
    border-radius: 12px !important;
    border: none !important;
    color: #333 !important;
}

/* --- Buttons --- */
#submit_button {
    background: #007bff !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: bold !important;
    align-self: center !important;
    width: 33% !important;
    height: 50px;
}

#audio_input button {
     background: rgba(255, 255, 255, 0.3) !important;
    border: 1px solid rgba(255, 255, 255, 0.5) !important;
    color: #333 !important;
    border-radius: 10px !important;
    
    min-width: 44px !important; 
    height: 44px !important;
    text-align: center !important;
}


/* --- Labels der Komponenten anpassen --- */
.label-wrap {
    color: rgba(240, 240, 255, 0.9) !important;
    font-weight: 500 !important;
}

/* --- Spezielles Styling für Überschriften --- */
#header h1, #header h3, #examples {
    text-align: center;
    color: white;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

#examples {
    text-align: left;
    font-size: 0.75em;
    opacity: 0.8;
}

/* Code-Block Styling */
#sql_code_display pre {
    background: rgba(0,0,0,0.7) !important;
    border-radius: 10px !important;
}

#sql_code_display code {
    color: #a7d1ff !important;
}
"""


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

# ----------------------- Gradio Interface -----------------------

with gr.Blocks(
    title="AdventureBikes Business Intelligence",
    css=custom_css,
) as demo:
    
    # Header-Bereich
    gr.Markdown(
        """
        # 🚲 AdventureBikes Databasetool
        ### Generative AI in der Unternehmenspraxis
        """,
        elem_id="header"
    )

    gr.Markdown(
            """
            > - **Umsatz:** "Was war der Gesamtumsatz im letzten Jahr in Deutschland?"
            > - **Verkaufsmenge:** "Zeige die Verkaufsmenge für Kid Bikes im Jahr 2023."
            > - **Bestseller:** "Was waren die Renner in den Kategorien Mountain Bikes und Race Bikes im Jahr 2024?"
            """,
            elem_id="examples" 
        )
    
    # Haupteingabefeld für Text
    question_input = gr.Textbox(
        label="Ihre Frage zur Geschäftsanalyse",
        placeholder="z.B. Zeige mir den Umsatz für 'Mountain Bikes' im letzten Jahr.",
        lines=3,
        elem_id="question_input" 
    )

    # Zeile für Audio-Eingabe (links) und SQL-Ausgabe (rechts)
    with gr.Row():
        with gr.Column(scale=1, min_width=250):
             audio_input = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label="🎙️ ODER Spracheingabe nutzen",
                elem_id="audio_input" 
            )
        
        # Diese Spalte ist anfangs unsichtbar und wird bei Bedarf eingeblendet
        with gr.Column(scale=3, visible=False) as sql_output_column:
            sql_code_display = gr.Code(
                label="Generierter SQL-Code",
                language="sql",
                interactive=False,
                lines=8,
                elem_id="sql_code_display" 
            )
    
    # Senden-Button
    submit_button = gr.Button("🔍 Analyse starten", variant="primary", elem_id="submit_button") # HINZUGEFÜGT: ID für CSS
    
    # Finale Antwort-Box
    final_answer_display = gr.Textbox(
        label="Ergebnis der Analyse",
        lines=8,
        interactive=False,
        show_copy_button=True,
        elem_id="final_answer_display"
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