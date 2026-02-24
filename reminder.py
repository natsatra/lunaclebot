import os
import json
import asyncio
from datetime import date
from telegram import Bot

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

async def send():
    with open("reminders.json") as f:
        reminders = json.load(f)
    
    today = date.today().isoformat()  # format: "2026-03-01"
    if today in reminders:
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=reminders[today])
    else:
        print(f"No reminder for {today}")

asyncio.run(send())
