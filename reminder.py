import os
import json
import asyncio
import pytz
from datetime import datetime
from telegram import Bot

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_IDS = os.environ["TELEGRAM_CHAT_IDS"].split(",")

async def send():
    with open("reminders.json") as f:
        reminders = json.load(f)

    IST = pytz.timezone("Asia/Kolkata")
    today = datetime.now(IST).date().isoformat()

    if today in reminders:
        message = reminders[today]
        bot = Bot(token=TOKEN)
        for chat_id in CHAT_IDS:
            await bot.send_message(chat_id=chat_id.strip(), text=message)
    else:
        print(f"No reminder for {today}")

asyncio.run(send())
