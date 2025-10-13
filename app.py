import json, os, sqlite3
from flask import Flask, render_template, request, redirect, jsonify, send_file, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flash messages
DB_NAME = "events.json"
SQL_DB = "events.db"

# ---------- JSON Functions ----------
def load_events():
    if not os.path.exists(DB_NAME):
        return {}
    with open(DB_NAME) as f:
        return json.load(f)

def save_events(events):
    with open(DB_NAME, "w") as f:
        json.dump(events, f, indent=4)

# ---------- SQL Setup ----------
def init_sql_db():
    conn = sqlite3.connect(SQL_DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY,
        title TEXT,
        description TEXT,
        date TEXT,
        votes INTEGER
    )
    """)
    conn.commit()
    conn.close()

def update_sql(events):
    """Sync JSON data into SQLite"""
    init_sql_db()
    conn = sqlite3.connect(SQL_DB)
    c = conn.cursor()
    c.execute("DELETE FROM events")  # clear old data
    for k, v in events.items():
        c.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                  (int(k), v["title"], v["description"], v["date"], len(v["votes"])))
    conn.commit()
    conn.close()

# ---------- Flask Routes ----------
@app.route("/")
def home():
    events = load_events()
    return render_template("index.html", events=events)

@app.route("/events")
def events():
    events = load_events()
    events_list = [
        {"id": k, "title": v["title"], "start": v["date"],
         "description": v["description"], "votes": len(v["votes"])}
        for k, v in events.items()
    ]
    return jsonify(events_list)

@app.route("/add_event", methods=["POST"])
def add_event():
    """Event creator adds a new event (with optional password)."""
    events = load_events()
    event_id = str(len(events) + 1)
    password = request.form.get("password", "").strip()  # password set by creator

    events[event_id] = {
        "title": request.form["title"],
        "description": request.form["description"],
        "date": request.form["date"],
        "votes": [],
        "password": password  # stored securely in JSON (plaintext for now)
    }

    save_events(events)
    update_sql(events)
    flash("Event created successfully!", "success")
    return redirect("/")

@app.route("/vote/<event_id>", methods=["POST"])
def vote(event_id):
    """User votes for an event — must enter correct event password if it has one."""
    events = load_events()
    email = request.form["email"].strip()
    entered_password = request.form.get("password", "").strip()

    # Check if event exists
    if event_id not in events:
        flash("Event not found.", "error")
        return redirect("/")

    stored_password = events[event_id].get("password", "")

    # Verify password if event has one
    if stored_password and entered_password != stored_password:
        flash("Incorrect event password.", "error")
        return redirect("/")

    # Add vote if user hasn't voted yet
    if email not in events[event_id]["votes"]:
        events[event_id]["votes"].append(email)
        flash("Your vote has been recorded!", "success")
    else:
        flash("You have already voted for this event.", "warning")

    save_events(events)
    update_sql(events)
    return redirect("/")

# ---------- Download Routes ----------
@app.route("/download-json")
def download_json():
    return send_file(DB_NAME, as_attachment=True)

@app.route("/download-db")
def download_db():
    return send_file(SQL_DB, as_attachment=True)

# ---------- Run ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    init_sql_db()
    app.run(host="0.0.0.0", port=port)
