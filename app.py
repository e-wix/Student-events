import json, os
from flask import Flask, render_template, request, redirect, jsonify, send_file

app = Flask(__name__)
DB_NAME = "events.json"

def load_events():
    if not os.path.exists(DB_NAME):
        return {}
    with open(DB_NAME) as f:
        return json.load(f)

def save_events(events):
    with open(DB_NAME, "w") as f:
        json.dump(events, f, indent=4)

@app.route("/")
def home():
    events = load_events()
    return render_template("index.html", events=events)

@app.route("/events")
def events():
    events = load_events()
    events_list = [
        {"id": k,
         "title": v["title"],
         "start": v["date"],
         "description": v["description"],
         "votes": len(v["votes"])}
        for k, v in events.items()
    ]
    return jsonify(events_list)

@app.route("/add_event", methods=["POST"])
def add_event():
    events = load_events()
    event_id = str(len(events) + 1)
    events[event_id] = {
        "title": request.form["title"],
        "description": request.form["description"],
        "date": request.form["date"],
        "votes": []
    }
    save_events(events)
    return redirect("/")

@app.route("/vote/<event_id>", methods=["POST"])
def vote(event_id):
    events = load_events()
    email = request.form["email"]
    if email not in events[event_id]["votes"]:
        events[event_id]["votes"].append(email)
    save_events(events)
    return redirect("/")

@app.route("/download-json")
def download_db():
    return send_file(DB_NAME, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


