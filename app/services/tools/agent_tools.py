from app.services.tools.google_calendar import create_events_from_plan
import json
import os

async def save_schedule_json(json_data: dict) -> str:
    """Save the study schedule as JSON for Google Calendar."""
    valid_events = []
    for item in json_data.get("events", []):
        try:
            event = {
                "summary": item["summary"],
                "start": {
                    "dateTime": item["start"],
                    "timeZone": item.get("timeZone", "Asia/Ho_Chi_Minh")
                },
                "end": {
                    "dateTime": item["end"],
                    "timeZone": item.get("timeZone", "Asia/Ho_Chi_Minh")
                },
                "description": item.get("description", "")
            }
            valid_events.append(event)
        except KeyError as e:
            print(f"❌ Missing required field: {e} in {item}")
    
    if not valid_events:
        return "❌ No valid events to save."
    
    with open("plan.json", "w", encoding="utf-8") as f:
        json.dump({"events": valid_events}, f, indent=2, ensure_ascii=False)
    
    return "✅ JSON SAVED"

# === TOOL 2: Load JSON and sync to Google Calendar ===
async def load_schedule_json() -> str:
    """Read the JSON file and sync it to Google Calendar."""
    if not os.path.exists("plan.json"):
        raise FileNotFoundError("❌ plan.json file not found.")
    with open("plan.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    create_events_from_plan(data)
    return "✅ Study plan synced to Google Calendar."
