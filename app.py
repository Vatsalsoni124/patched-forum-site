from flask import Flask, render_template, request, session, redirect, url_for, send_file
import os
import random
import string
import sqlite3
import subprocess

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB = 'forum.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        )
        """)
init_db()

def get_guest_name():
    if "guest_name" not in session:
        words = ["rose", "wolf", "eagle", "lion", "tiger", "hawk", "phantom"]
        session["guest_name"] = "guest_" + random.choice(words) + ''.join(random.choices(string.digits, k=3))
    return session["guest_name"]

@app.route("/")
def index():
    user = get_guest_name()
    return render_template("index.html", user=user)

@app.route("/tools", methods=["GET", "POST"])
def tools():
    user = get_guest_name()
    if request.method == "POST":
        try:
            file = request.files["combo"]
            filepath = os.path.join(UPLOAD_FOLDER, "combo.txt")
            file.save(filepath)

            # Rename to match checker expectation
            os.rename(filepath, "combo.txt")

            # RUN CHECKER — use 'python' not 'python3' for Render
            result = subprocess.run(["python", "rdphost_threaded_tagged.py"], capture_output=True, text=True)

            # DEBUG: Print stdout/stderr to webpage if hits.txt not found
            if os.path.exists("hits.txt"):
                return send_file("hits.txt", as_attachment=True)
            else:
                return f"""
                <h2>❌ Checker did not generate hits.txt</h2>
                <h3>🔍 Debug Output:</h3>
                <pre>STDOUT:\n{result.stdout}</pre>
                <pre>STDERR:\n{result.stderr}</pre>
                """
        except Exception as e:
            return f"<h2>❌ An error occurred</h2><pre>{str(e)}</pre>"

    return render_template("tools.html", user=user)


@app.route("/forum", methods=["GET", "POST"])
def forum():
    user = get_guest_name()
    db = get_db()
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        db.execute("INSERT INTO posts (author, title, content) VALUES (?, ?, ?)", (user, title, content))
        db.commit()
        return redirect(url_for("forum"))
    posts = db.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    return render_template("forum.html", posts=posts, user=user)

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render sets this automatically
    app.run(debug=False, host="0.0.0.0", port=port)

