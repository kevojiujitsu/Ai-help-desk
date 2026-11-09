from flask import (
    Flask, request, render_template_string,
    session, redirect, url_for,
)
import requests
import secrets
from uuid import uuid4

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Temporary storage on this computer, separated by browser session.
conversations = {}

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are a helpful IT troubleshooting assistant. "
        "Give concise, accurate guidance. "
        "Ask questions when details are missing. "
        "Use the conversation history to understand follow-up questions. "
        "Start with simple, reversible checks. "
        "Explain risks before suggesting changes. "
        "Never ask for passwords."
    ),
}
PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Help Desk</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 650px;
            margin: 60px auto;
            padding: 20px;
            background: #101827;
            color: #f3f4f6;
        }
        textarea {
            width: 100%;
            box-sizing: border-box;
            padding: 12px;
            font: inherit;
        }
        button {
            margin-top: 12px;
            padding: 12px 20px;
            cursor: pointer;
        }
        .reply {
            margin-top: 24px;
            padding: 20px;
            background: #1f2937;
            border-radius: 10px;
        }
    </style>
</head>
<body>
    <h1>AI Help Desk</h1>
    <p>Describe your computer problem.</p>

    <form method="post">
        <label for="message">What do you need help with?</label>
        <textarea id="message" name="message" rows="4"
                  maxlength="2000" required>{{ message }}</textarea>
        <button type="submit">Get help</button>
    </form>

        <form method="post" action="/clear">
        <button type="submit">New conversation</button>
    </form>

    {% if error %}
    <p role="alert">{{ error }}</p>
    {% endif %}

    {% for entry in history %}
    <div class="reply">
        <h2>{{ "You" if entry.role == "user" else "Assistant" }}</h2>
        <p style="white-space: pre-wrap;">{{ entry.content }}</p>
    </div>
    {% endfor %}
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def home():
    if "chat_id" not in session:
        session["chat_id"] = str(uuid4())

    chat_id = session["chat_id"]
    history = conversations.setdefault(chat_id, [])
    message = ""
    error = ""

    if request.method == "POST":
        message = request.form.get("message", "").strip()

        if not message:
            error = "Please describe your computer problem."
        elif len(message) > 2000:
            error = "Please keep your message under 2,000 characters."
        else:
            user_message = {"role": "user", "content": message}

            try:
                response = requests.post(
                    "http://127.0.0.1:11434/api/chat",
                    json={
                        "model": "qwen3:8b",
                        "messages": [
                            SYSTEM_MESSAGE,
                            *history,
                            user_message,
                        ],
                        "stream": False,
                        "think": False,
                        "options": {"num_ctx": 8192},
                    },
                    timeout=(10, 180),
                )
                response.raise_for_status()
                reply = response.json()["message"]["content"]

                if not isinstance(reply, str) or not reply.strip():
                    raise ValueError("Empty or invalid reply")

                # Save only successful exchanges; keep the latest 10.
                conversations[chat_id] = (
                    history
                    + [
                        user_message,
                        {"role": "assistant", "content": reply},
                    ]
                )[-20:]

                return redirect(url_for("home"))

            except requests.exceptions.Timeout:
                error = "The local AI took too long. Please try again."
            except requests.exceptions.RequestException:
                error = (
                    "Could not get a response from Ollama. "
                    "Make sure Ollama is running and try again."
                )
            except (KeyError, ValueError, TypeError):
                error = "The AI returned an unexpected response."

    return render_template_string(
        PAGE,
        message=message,
        history=history,
        error=error,
    )


@app.post("/clear")
def clear():
    chat_id = session.pop("chat_id", None)
    conversations.pop(chat_id, None)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)