import shelve

DB_NAME = "events.db"  # use the same name you used in Flask

# Open the shelve database
with shelve.open(DB_NAME) as db:
    if not db:
        print("No events found!")
    else:
        for event_id, event in db.items():
            print(f"Event ID: {event_id}")
            print(f"Title: {event['title']}")
            print(f"Description: {event['description']}")
            print(f"Date: {event['date']}")
            print(f"Votes ({len(event['votes'])}): {event['votes']}")
            print("-" * 40)
