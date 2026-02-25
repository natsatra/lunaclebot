import os
import csv
import json
import requests
from github import Github

SHEET_ID = os.environ["SHEET_ID"]
GITHUB_TOKEN = os.environ["GH_TOKEN"]
REPO_NAME = os.environ["REPO_NAME"]

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
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    content = json.dumps(reminders, indent=2)
    file = repo.get_contents("reminders.json")
    repo.update_file(
        path="reminders.json",
        message="sync: update reminders from Google Sheet",
        content=content,
        sha=file.sha
    )
    print("reminders.json updated successfully")

reminders = fetch_sheet()
update_repo(reminders)
