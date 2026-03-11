import os
import json
import requests
import csv
import time

SHEET_ID = os.environ["SHEET_ID"]

def fetch_tab(tab_name, retries=3, delay=5):
     url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={tab_name}"
     
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
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

        except requests.RequestException as e:
            print(f"Attempt {attempt + 1} failed for tab '{tab_name}': {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise RuntimeError(f"Failed to fetch tab '{tab_name}' after {retries} attempts.") from e

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

if __name__ == "__main__":
    reminders = merge_reminders()
    write_json(reminders)
