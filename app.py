import os
import sqlite3
from flask import Flask, render_template, request, redirect, jsonify, send_file, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"
SQL_DB = "events.db"


# ---------- DATABASE SETUP ----------
def init_sql_db():
    """Initialize the database and create tables if not present."""
    conn = sqlite3.connect(SQL_DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        date TEXT,
        votes INTEGER DEFAULT 0,
        password_hash TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        email TEXT,
        FOREIGN KEY (event_id) REFERENCES events(id)
    )
    """)
    conn.commit()
    conn.close()


# ---------- HELPER FUNCTIONS ----------
def get_all_events():
    """Retrieve all events from the database."""
    conn = sqlite3.connect(SQL_DB)
    c = conn.cursor()
    c.execute("SELECT id, title, description, date, votes FROM events ORDER BY date ASC")
    rows = c.fetchall()
    conn.close()
    return [
        {"id": r[0], "title": r[1], "description": r[2], "date": r[3], "votes": r[4]}
        for r in rows
    ]


def get_event(event_id):
    """Retrieve a single event by ID."""
    conn = sqlite3.connect(SQL_DB)
    c = conn.cursor()
    c.execute("SELECT id, title, description, date, votes, password_hash FROM events WHERE id=?", (event_id,))
    row = c.fetchone()
    conn.close()
    return row


def has_voted(event_id, email):
    """Check if a user has already voted for this event."""
    conn = sqlite3.connect(SQL_DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM votes WHERE event_id=? AND email=?", (event_id, email))
    exists = c.fetchone() is not None
    conn.close()
    return exists


# ---------- ROUTES ----------
@app.route("/")
def home():
    """Display all events."""
    events = get_all_events()
    return render_template("index.html", events=events)


@app.route("/events")
def events():
    """Return all events as JSON."""
    return jsonify(get_all_events())


@app.route("/add_event", methods=["POST"])
def add_event():
    """Add a new event to the database."""
    title = request.form["title"]
    description = request.form["description"]
    date = request.form["date"]
    password = request.form.get("password", "").strip()

    password_hash = generate_password_hash(password) if password else None

    conn = sqlite3.connect(SQL_DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO events (title, description, date, password_hash) VALUES (?, ?, ?, ?)",
        (title, description, date, password_hash)
    )
    conn.commit()
    conn.close()

    flash("Event created successfully!", "success")
    return redirect("/")


@app.route("/vote", methods=["POST"])
def vote():
    """Record a user's vote for an event."""
    event_id = request.form["event_id"]
    email = request.form["email"].strip().lower()
    entered_password = request.form.get("password", "").strip()

    event = get_event(event_id)
    if not event:
        flash("Event not found.", "error")
        return redirect("/")

    stored_password_hash = event[5]

    # Verify password if event has one
    if stored_password_hash:
        if not entered_password:
            flash("This event requires a password to vote.", "error")
            return redirect("/")
        if not check_password_hash(stored_password_hash, entered_password):
            flash("Incorrect event password.", "error")
            return redirect("/")

    # Check if user already voted
    if has_voted(event_id, email):
        flash("You have already voted for this event.", "warning")
        return redirect("/")

    # Record the vote
    conn = sqlite3.connect(SQL_DB)
    c = conn.cursor()
    c.execute("INSERT INTO votes (event_id, email) VALUES (?, ?)", (event_id, email))
    c.execute("UPDATE events SET votes = votes + 1 WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

    flash("Your vote has been recorded!", "success")
    return redirect("/")


@app.route("/download-db")
def download_db():
    """Download the SQLite database file."""
    return send_file(SQL_DB, as_attachment=True)


@app.route("/reset-db")
def reset_db():
    """Reset the database (for development/testing)."""
    if os.path.exists(SQL_DB):
        os.remove(SQL_DB)
    init_sql_db()
    flash("Database has been reset.", "info")
    return redirect("/")


# ---------- MAIN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    init_sql_db()
    app.run(host="0.0.0.0", port=port)
