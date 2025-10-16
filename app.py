import json, os, sqlite3
from flask import Flask, render_template, request, redirect, jsonify, send_file, flash
from werkzeug.security import generate_password_hash, check_password_hash

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
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (id TEXT PRIMARY KEY, name TEXT, date TEXT, description TEXT, password TEXT)''')
    conn.commit()
    conn.close()

def update_sql(events):
    conn = sqlite3.connect(SQL_DB)
    c = conn.cursor()
    c.execute("DELETE FROM events")
    for event_id, event_data in events.items():
        c.execute("INSERT OR REPLACE INTO events VALUES (?, ?, ?, ?, ?)",
                  (event_id, event_data["name"], event_data["date"],
                   event_data["description"], event_data["password"]))
    conn.commit()
    conn.close()

# ---------- Routes ----------
@app.route("/")
def index():
    events = load_events()
    return render_template("index.html", events=events)

@app.route("/create-event", methods=["POST"])
def create_event():
    events = load_events()

    event_id = request.form["id"]
    name = request.form["name"]
    date = request.form["date"]
    description = request.form["description"]
    password = request.form["password"]

    # ✅ Hash the password before saving
    hashed_password = generate_password_hash(password)

    events[event_id] = {
        "name": name,
        "date": date,
        "description": description,
        "password": hashed_password  # stored as hash
    }

    save_events(events)
    update_sql(events)
    flash("Event created successfully!", "success")
    return redirect("/")

@app.route("/delete-event", methods=["POST"])
def delete_event():
    events = load_events()

    event_id = request.form["id"]
    password = request.form["password"]

    if event_id not in events:
        flash("Event not found.", "danger")
        return redirect("/")

    stored_password_hash = events[event_id].get("password", "")

    # ✅ Verify hashed password
    if not check_password_hash(stored_password_hash, password):
        flash("Incorrect password.", "danger")
        return redirect("/")

    del events[event_id]
    save_events(events)
    update_sql(events)
    flash("Event deleted successfully!", "success")
    return redirect("/")

@app.route("/download-db")
def download_db():
    return send_file(SQL_DB, as_attachment=True)

# ---------- Run ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    init_sql_db()
    app.run(host="0.0.0.0", port=port)
