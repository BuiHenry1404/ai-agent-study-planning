from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_events_from_plan(plan: dict):
    """
    Create events from the study plan JSON and add them to the user's Google Calendar.
    """
    if not plan.get("events"):
        raise ValueError("No events found in the study plan.")

    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)

    for event_data in plan["events"]:
        event = {
            "summary": event_data.get("summary", "Study Schedule"),
            "description": event_data.get("description", ""),
            "start": {
                "dateTime": event_data["start"]["dateTime"],
                "timeZone": event_data["start"]["timeZone"],
            },
            "end": {
                "dateTime": event_data["end"]["dateTime"],
                "timeZone": event_data["end"]["timeZone"],
            }
        }

        created_event = service.events().insert(calendarId="primary", body=event).execute()
        print("📅 Successfully created:", created_event.get("htmlLink"))

    return "✅ Study plan has been synced to Google Calendar."
