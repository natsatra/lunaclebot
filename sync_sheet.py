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

    reminders = []
    reader = csv.DictReader(response.text.splitlines())
    for row in reader:
        if row["date"] and row["message"]:
            reminders.append({
                "date": row["date"].strip(),
                "message": row["message"].strip(),
                "time": row.get("time", "").strip()
            })
    return reminders

def merge_reminders():
    moon = fetch_tab("moon_phases")
    personal = fetch_tab("personal")

    merged = {}
    for entry in moon + personal:
        date = entry["date"]
        if date not in merged:
            merged[date] = []
        merged[date].append({
            "message": entry["message"],
            "time": entry["time"]
        })

    return merged

def write_json(reminders):
    content = json.dumps(reminders, indent=2, ensure_ascii=False)
    with open("reminders.json", "w", encoding="utf-8") as f:
        f.write(content)
    print("reminders.json updated successfully")

reminders = merge_reminders()
write_json(reminders)
