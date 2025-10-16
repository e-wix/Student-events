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
    c.execute(
        """CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            date TEXT,
            password TEXT
        )"""
    )
    conn.commit()
    conn.close()

# ---------- Create Event ----------
@app.route("/create", methods=["POST"])
def create_event():
    events = load_events()
    event_id = str(len(events) + 1)
    name = request.form.get("name")
    description = request.form.get("description")
    date = request.form.get("date")
    password = generate_password_hash(request.form.get("password"))

    events[event_id] = {
        "name": name,
        "description": description,
        "date": date,
        "password": password  # stored in JSON
    }

    save_events(events)
    update_sql(events)
    flash("Event created successfully!", "success")
    return redirect("/")

# ---------- Delete Event ----------
@app.route("/delete/<event_id>", methods=["POST"])
def delete_event(event_id):
    events = load_events()
    stored_password_hash = events[event_id].get("password", "")

    password_input = request.form.get("password")
    if check_password_hash(stored_password_hash, password_input):
        del events[event_id]
        save_events(events)
        update_sql(events)
        flash("Event deleted successfully!", "success")
    else:
        flash("Incorrect password.", "danger")

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
