from flask import Flask, render_template, request, redirect, jsonify
import shelve
import os

app = Flask(__name__)
DB_NAME = "events.db"

@app.route('/')
def home():
    with shelve.open(DB_NAME) as db:
        events = dict(db)
    return render_template('index.html', events=events)

@app.route("/events")
def events():
    with shelve.open(DB_NAME) as db:
        events_list = []
        for event_id, event in db.items():
            events_list.append({
                "id": event_id,
                "title": event["title"],
                "start": event["date"],
                "description": event["description"],
                "votes": len(event["votes"])
            })
    return jsonify(events_list)

@app.route("/add_event", methods=["POST"])
def add_event():
    title = request.form["title"]
    description = request.form["description"]
    date = request.form["date"]

    with shelve.open(DB_NAME, writeback=True) as db:
        event_id = str(len(db) + 1)
        db[event_id] = {
            "title": title,
            "description": description,
            "date": date,
            "votes": []
        }

    return redirect("/")

@app.route("/vote/<event_id>", methods=["POST"])
def vote(event_id):
    email = request.form["email"]

    with shelve.open(DB_NAME, writeback=True) as db:
        event = db[event_id]
        if email not in event["votes"]:
            event["votes"].append(email)
        db[event_id] = event

    return redirect("/")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

