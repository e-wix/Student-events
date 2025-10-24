import os
import sqlite3
import json
import io
from flask import Flask, render_template, request, redirect, jsonify, send_file, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"
SQL_DB = "events.db"


def init_sql_db():
    conn = sqlite3.connect(SQL_DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        date TEXT,
        password TEXT,
        votes INTEGER DEFAULT 0
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        email TEXT,
        UNIQUE(event_id, email),
        FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()

    # Migrate any plaintext passwords to hashed form (best-effort).
    _migrate_plaintext_passwords()


def _migrate_plaintext_passwords():
    """
    If there are existing passwords stored in plaintext, this function will
    hash them. We detect already-hashed passwords by checking the typical
    Werkzeug PBKDF2 prefix ('pbkdf2:').
    This is a best-effort migration — if you used a different hash format
    previously, adjust detection logic.
    """
    conn = sqlite3.connect(SQL_DB)
    c = conn.cursor()
    c.execute("SELECT id, password FROM events WHERE password IS NOT NULL AND password != ''")
    rows = c.fetchall()
    for event_id, pwd in rows:
        if not pwd.startswith("pbkdf2:"):  # Werkzeug hashes start with 'pbkdf2:'
            hashed = generate_password_hash(pwd)
            c.execute("UPDATE events SET password = ? WHERE id = ?", (hashed, event_id))
    conn.commit()
    conn.close()


def get_all_events():
    conn = sqlite3.connect(SQL_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, title, description, date, votes FROM events")
    events = c.fetchall()
    conn.close()
    return events


@app.route("/")
def home():
    # You may want to adapt index.html to accept events as rows (sqlite Row objects)
    events = get_all_events()
    return render_template("index.html", events=events)


@app.route("/events")
def events():
    conn = sqlite3.connect(SQL_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, title, description, date, votes FROM events")
    events_list = [
        {"id": row["id"], "title": row["title"], "start": row["date"],
         "description": row["description"], "votes": row["votes"]}
        for row in c.fetchall()
    ]
    conn.close()
    return jsonify(events_list)


@app.route("/add_event", methods=["POST"])
def add_event():
    title = request.form["title"]
    description = request.form["description"]
    date = request.form["date"]
    password = request.form.get("password", "").strip()

    # Hash the password before storing (empty string allowed for no password)
    hashed_password = generate_password_hash(password) if password else ""

    conn = sqlite3.connect(SQL_DB)
    c = conn.cursor()
    c.execute("""
        INSERT INTO events (title, description, date, password, votes)
        VALUES (?, ?, ?, ?, 0)
    """, (title, description, date, hashed_password))
    conn.commit()
    conn.close()

    flash("Event added successfully!", "success")
    return redirect("/")


@app.route("/vote/<int:event_id>", methods=["POST"])
def vote(event_id):
    email = request.form["email"].strip()
    entered_password = request.form.get("password", "")

    conn = sqlite3.connect(SQL_DB)
    c = conn.cursor()

    # Verify event exists and password (hashed) if set
    c.execute("SELECT password FROM events WHERE id = ?", (event_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        flash("Event not found.", "error")
        return redirect("/")

    stored_password = row[0] or ""
    if stored_password:
        # stored_password is hashed — verify
        if not check_password_hash(stored_password, entered_password):
            conn.close()
            flash("Incorrect password for this event.", "error")
            return redirect("/")

    # Record vote if not already present
    try:
        c.execute("INSERT INTO votes (event_id, email) VALUES (?, ?)", (event_id, email))
        c.execute("UPDATE events SET votes = votes + 1 WHERE id = ?", (event_id,))
        conn.commit()
        flash("Vote recorded!", "success")
    except sqlite3.IntegrityError:
        # UNIQUE constraint violation => already voted
        flash("You’ve already voted for this event.", "warning")
    finally:
        conn.close()

    return redirect("/")


@app.route("/download-db")
def download_db():
    """
    Provide a sanitized export (JSON) that excludes:
      - password hashes
      - individual voter emails

    The user requested that passwords not be downloadable; we therefore
    return only non-sensitive fields and vote counts.
    """
    conn = sqlite3.connect(SQL_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, title, description, date, votes FROM events")
    rows = c.fetchall()
    conn.close()

    export = []
    for r in rows:
        export.append({
            "id": r["id"],
            "title": r["title"],
            "description": r["description"],
            "date": r["date"],
            "votes": r["votes"],  # aggregated count only
        })

    json_bytes = json.dumps({"events": export}, indent=2).encode("utf-8")
    return send_file(
        io.BytesIO(json_bytes),
        as_attachment=True,
        download_name="events_export.json",
        mimetype="application/json"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    init_sql_db()
    app.run(host="0.0.0.0", port=port)
