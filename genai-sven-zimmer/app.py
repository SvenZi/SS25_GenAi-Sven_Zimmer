import gradio as gr
import pandas as pd
from datenbank_agent import DatenbankAgent

# --- Unser "Motor" ---
# Diese Funktion kapselt den Workflow, den wir testen wollen.
# Später wird hier die Logik des ManagerAgenten stehen.
def run_query_workflow(user_question: str):
    """
    Führt einen vordefinierten Workflow aus, um Daten aus der Datenbank abzufragen.
    Nimmt eine Benutzerfrage entgegen (wird derzeit aber noch ignoriert).
    """
    print(f"Workflow gestartet für die Frage: '{user_question}'")
    
    # 1. Definiere die SQL-Abfrage.
    #    HINWEIS: Dies ist noch ein Platzhalter. Später wird ein KI-Agent
    #    diese Abfrage basierend auf der 'user_question' generieren.
    sql_query = "SELECT TOP 10 * FROM dbo.Dim_Product ORDER BY Product_Price_EUR DESC"

    # 2. Erstelle eine Instanz unseres spezialisierten Agenten.
    db_agent = DatenbankAgent()

    # 3. Beauftrage den Agenten mit der Ausführung der Aufgabe.
    print("Beauftrage den DatenbankAgent...")
    ergebnis = db_agent.fuehre_abfrage_aus(sql_query)

    # 4. Gib das Ergebnis zurück, damit Gradio es anzeigen kann.
    if isinstance(ergebnis, pd.DataFrame):
        return ergebnis
    else:
        # Im Fehlerfall geben wir einen leeren DataFrame mit einer Fehlermeldung zurück.
        # Gradio kann DataFrames besser darstellen als reinen Text.
        return pd.DataFrame({'Fehler': [str(ergebnis)]})


# --- Die Gradio-Oberfläche ---
# Hier bauen wir das "Armaturenbrett" für unseren Motor.
with gr.Blocks(title="Produktleistungs-Agent") as demo:
    gr.Markdown("# 🚀 Prototyp des Produktleistungs-Agenten")
    gr.Markdown("Dies ist eine erste interaktive Oberfläche. Momentan wird die Eingabe ignoriert und immer die gleiche Abfrage für die 10 teuersten Produkte ausgeführt.")
    
    with gr.Row():
        question_input = gr.Textbox(
            label="Stelle deine Frage hier:",
            placeholder="z.B. Zeige mir die teuersten Produkte.",
            scale=4
        )
        submit_button = gr.Button("Anfrage senden", variant="primary", scale=1)

    output_dataframe = gr.DataFrame(label="Ergebnis aus der Datenbank")

    submit_button.click(
        fn=run_query_workflow,
        inputs=question_input,
        outputs=output_dataframe
    )

# --- Start der Anwendung ---
if __name__ == "__main__":
    print("Starte die Gradio-Oberfläche...")
    print("Du kannst sie im Browser unter der angezeigten URL öffnen.")
    demo.launch()
