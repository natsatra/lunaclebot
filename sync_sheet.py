import os
import json
import requests
import csv

SHEET_ID = os.environ["SHEET_ID"]

def fetch_tab(tab_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={tab_name}"
    response = requests.get(url)
    response.encoding = "utf-8"
    response.raise_for_status()

    reminders = {}
    reader = csv.DictReader(response.text.splitlines())
    for row in reader:
        if row["date"] and row["message"]:
            reminders[row["date"].strip()] = row["message"].strip()
    return reminders

def merge_reminders():
    moon = fetch_tab("moon_phases")
    personal = fetch_tab("personal")

    # Combine both — personal entries are added separately
    merged = {}
    all_dates = set(moon.keys()) | set(personal.keys())

    for date in all_dates:
        messages = []
        if date in moon:
            messages.append(moon[date])
        if date in personal:
            messages.append(personal[date])
        merged[date] = messages  # list of messages for that date

    return merged

def write_json(reminders):
    content = json.dumps(reminders, indent=2, ensure_ascii=False)
    with open("reminders.json", "w", encoding="utf-8") as f:
        f.write(content)
    print("reminders.json updated successfully")

reminders = merge_reminders()
write_json(reminders)
