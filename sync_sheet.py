import os
import csv
import json
import requests

SHEET_ID = os.environ["SHEET_ID"]

def fetch_sheet():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    response = requests.get(url)
    response.raise_for_status()
    
    reminders = {}
    reader = csv.DictReader(response.text.splitlines())
    for row in reader:
        if row["date"] and row["message"]:
            reminders[row["date"].strip()] = row["message"].strip()
    return reminders

def update_repo(reminders):
    content = json.dumps(reminders, indent=2)
    with open("reminders.json", "w") as f:
        f.write(content)
    print("reminders.json updated successfully")

reminders = fetch_sheet()
update_repo(reminders)
