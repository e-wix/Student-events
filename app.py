import os
import sqlite3
from flask import Flask, render_template, request, redirect, jsonify, send_file, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.debug = True  # show real error messages in dev
SQL_DB = "events.db"



def init_sql_db():
    conn = sqlite3.connect(SQL_DB)
    c = conn.cursor()

    # Events table
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

    # Votes table
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



def get_all_events():
    conn = sqlite3.connect(SQL_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT e.id, e.title, e.description, e.date, e.votes
        FROM events e
    """)
    events = c.fetchall()
    conn.close()
    return events



@app.route("/")
def home():
    try:
        events = get_all_events()
        return render_template("index.html", events=events)
    except Exception as e:
        print("🔥 Error rendering home page:", e)
        flash(f"Error loading events: {e}", "error")
        return "Internal Server Error", 500


@app.route("/events")
def events():
    conn = sqlite3.connect(SQL_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT e.id, e.title, e.description, e.date, e.votes
        FROM events e
    """)
    events_list = [
        {
            "id": row["id"],
            "title": row["title"],
            "start": row["date"],
            "description": row["description"],
            "votes": row["votes"]
        }
        for row in c.fetchall()
    ]
    conn.close()
    return jsonify(events_list)


@app.route("/add_event", methods=["POST"])
def add_event():
    try:
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        date = request.form.get("date", "").strip()
        password = request.form.get("password", "").strip()

        if not title or not date:
            flash("Title and date are required.", "error")
            return redirect("/")

        conn = sqlite3.connect(SQL_DB)
        c = conn.cursor()
        c.execute("""
            INSERT INTO events (title, description, date, password, votes)
            VALUES (?, ?, ?, ?, 0)
        """, (title, description, date, password))
        conn.commit()
        conn.close()

        flash("Event added successfully!", "success")
        return redirect("/")
    except Exception as e:
        print("🔥 Error adding event:", e)
        flash(f"Error adding event: {e}", "error")
        return redirect("/")


@app.route("/vote/<int:event_id>", methods=["POST"])
def vote(event_id):
    try:
        email = request.form.get("email", "").strip()
        entered_password = request.form.get("password", "").strip()

        if not email:
            flash("Email is required to vote.", "error")
            return redirect("/")

        conn = sqlite3.connect(SQL_DB)
        c = conn.cursor()

        # Verify event and password
        c.execute("SELECT password FROM events WHERE id = ?", (event_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            flash("Event not found.", "error")
            return redirect("/")

        stored_password = row[0] or ""
        if stored_password and entered_password != stored_password:
            conn.close()
            flash("Incorrect password for this event.", "error")
            return redirect("/")

        # Record vote if not already voted
        try:
            c.execute("INSERT INTO votes (event_id, email) VALUES (?, ?)", (event_id, email))
            c.execute("UPDATE events SET votes = votes + 1 WHERE id = ?", (event_id,))
            conn.commit()
            flash("Vote recorded!", "success")
        except sqlite3.IntegrityError:
            flash("You’ve already voted for this event.", "warning")

        conn.close()
        return redirect("/")
    except Exception as e:
        print("🔥 Error during voting:", e)
        flash(f"Error voting: {e}", "error")
        return redirect("/")


@app.route("/download-db")
def download_db():
    try:
        return send_file(SQL_DB, as_attachment=True)
    except Exception as e:
        print("🔥 Error sending DB file:", e)
        flash(f"Error downloading database: {e}", "error")
        return redirect("/")



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    init_sql_db()
    print(f"✅ Server running on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
