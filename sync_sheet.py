import os
import csv
import json
import requests

SHEET_ID: str = os.environ["SHEET_ID"]

def fetch_tab(tab_name: str) -> list[dict[str, str]]:
    url: str = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={tab_name}"
    response = requests.get(url)
    response.encoding = "utf-8"
    response.raise_for_status()

    reminders: list[dict[str, str]] = []
    reader = csv.DictReader(response.text.splitlines())
    for row in reader:
        if row["date"] and row["message"]:
            reminders.append({
                "date": row["date"].strip(),
                "message": row["message"].strip(),
                "time": row.get("time", "").strip()
            })
    return reminders

def merge_reminders() -> dict[str, list[dict[str, str]]]:
    moon: list[dict[str, str]] = fetch_tab("moon_phases")
    personal: list[dict[str, str]] = fetch_tab("personal")

    merged: dict[str, list[dict[str, str]]] = {}
    for entry in moon + personal:
        date: str = entry["date"]
        if date not in merged:
            merged[date] = []
        merged[date].append({
            "message": entry["message"],
            "time": entry["time"]
        })

    return merged

def write_json(reminders: dict[str, list[dict[str, str]]]) -> None:
    content: str = json.dumps(reminders, indent=2, ensure_ascii=False)
    with open("reminders.json", "w", encoding="utf-8") as f:
        f.write(content)
    print("reminders.json updated successfully")

reminders = merge_reminders()
write_json(reminders)
