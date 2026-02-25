import os
import json
import ephem
import anthropic
from datetime import datetime
import gspread
import time
from google.oauth2.service_account import Credentials

# Load credentials
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SHEET_ID = os.environ["SHEET_ID"]
GOOGLE_CREDENTIALS = os.environ["GOOGLE_CREDENTIALS"]

#genai.configure(api_key=GEMINI_API_KEY)

def get_moon_phases(year):
    phases = []
    date = ephem.Date(f'{year}/1/1')
    end = ephem.Date(f'{year+1}/1/1')
    seen = set()

    while date < end:
        next_full = ephem.next_full_moon(date)
        next_new = ephem.next_new_moon(date)

        for phase_date, phase_name in [
            (next_full, "Full Moon"),
            (next_new, "New Moon")
        ]:
            dt = ephem.Date(phase_date).datetime()
            date_str = dt.strftime('%Y-%m-%d')
            if date_str not in seen and dt.year == year:
                seen.add(date_str)
                phases.append((date_str, phase_name, dt.strftime('%B')))

        date = min(next_full, next_new) + 1

    return sorted(phases)

def generate_message(phase_name, month):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Write a short astrological meaning for the {phase_name} in {month}. "
                    f"2-3 sentences max. Focus on themes, energy, and what to reflect on. "
                    f"Warm and inspiring tone. Plain text only, no markdown, no bullet points."
                )
            }
        ]
    )
    return response.content[0].text.strip()

def write_to_sheet(phases_with_messages):
    creds_dict = json.loads(GOOGLE_CREDENTIALS)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1

    # Clear existing content
    sheet.clear()

    # Write headers
    sheet.append_row(["date", "message"])

    # Write all moon phase rows
    for date_str, message in phases_with_messages:
        sheet.append_row([date_str, message])
        print(f"Written: {date_str}")

    print("Sheet updated successfully")

# Main
year = datetime.now().year
print(f"Generating moon phases for {year}...")

phases = get_moon_phases(year)
phases_with_messages = []

for date_str, phase_name, month in phases:
    print(f"Generating message for {phase_name} on {date_str}...")
    message = generate_message(phase_name, month)
    phases_with_messages.append((date_str, message))
    time.sleep(5)

write_to_sheet(phases_with_messages)
print("Done!")
