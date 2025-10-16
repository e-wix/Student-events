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
@@ -77,11 +66,10 @@
    "password": password  # stored in JSON



    save_events(events)
    update_sql(events)
    flash("Event created successfully!", "success")
    return redirect("/")
save_events(events)
update_sql(events)
flash("Event created successfully!", "success")
return redirect("/")

stored_password_hash = events[event_id].get("password", "")

@@ -117,16 +105,14 @@
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
