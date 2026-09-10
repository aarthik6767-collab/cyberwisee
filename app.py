import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from google import genai

from chatbot_config import SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-key")

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.1-flash-lite"

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not configured in the .env file.")

client = genai.Client(api_key=API_KEY)


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    try:
        previous_id = session.get("interaction_id")

        request_data = {
            "model": MODEL_NAME,
            "input": message,
            "system_instruction": SYSTEM_PROMPT,
            "generation_config": {
                "thinking_level": "minimal"
            },
        }

        if previous_id:
            request_data["previous_interaction_id"] = previous_id

        interaction = client.interactions.create(**request_data)

        session["interaction_id"] = interaction.id

        return jsonify({
            "reply": interaction.output_text.strip(),
            "interaction_id": interaction.id
        })

    except Exception as exc:
        app.logger.exception("Gemini request failed")
        return jsonify({
            "error": "I couldn't process that request right now. Please try again."
        }), 500


@app.post("/api/new-chat")
def new_chat():
    session.pop("interaction_id", None)
    return jsonify({"success": True})


@app.get("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL_NAME})


if __name__ == "__main__":
    app.run(debug=True)
