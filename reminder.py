import os
import json
import asyncio
import pytz
from datetime import datetime
from telegram import Bot

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_IDS = os.environ["TELEGRAM_CHAT_IDS"].split(",")

async def send():
    with open("reminders.json", encoding="utf-8") as f:
        reminders = json.load(f)

    IST = pytz.timezone("Asia/Kolkata")
    today = datetime.now(IST).date().isoformat()

    if today in reminders:
        bot = Bot(token=TOKEN)
        messages = reminders[today]  # this is now a list
        for message in messages:
            for chat_id in CHAT_IDS:
                await bot.send_message(
                    chat_id=chat_id.strip(),
                    text=message,
                    parse_mode="HTML"
                )
    else:
        print(f"No reminder for {today}")

asyncio.run(send())
