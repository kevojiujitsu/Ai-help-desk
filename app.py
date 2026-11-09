from flask import Flask, request, render_template_string

app = Flask(__name__)

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

    {% if reply %}
    <div class="reply">
        <h2>Assistant</h2>
        <p>{{ reply }}</p>
    </div>
    {% endif %}
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def home():
    message = ""
    reply = ""

    if request.method == "POST":
        message = request.form.get("message", "").strip()

        if message:
            reply = (
                "Thanks for describing the problem. "
                "What operating system are you using, "
                "and do you see an error message?"
            )
        else:
            reply = "Please describe your computer problem."

    return render_template_string(PAGE, message=message, reply=reply)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)