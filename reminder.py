import os
import json
import asyncio
import pytz
from datetime import datetime
from telegram import Bot

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_IDS = os.environ["TELEGRAM_CHAT_IDS"].split(",")
DEFAULT_TIME = "07:30"  # used when time column is empty

async def send():
    with open("reminders.json", encoding="utf-8") as f:
        reminders = json.load(f)

    IST = pytz.timezone("Asia/Kolkata")
    now = datetime.now(IST)
    today = now.date().isoformat()
    current_time = now.strftime("%H:%M")

    if today in reminders:
        bot = Bot(token=TOKEN)
        for entry in reminders[today]:
            message = entry["message"]
            send_time = entry["time"] if entry["time"] else DEFAULT_TIME

            if not send_time or send_time == current_time:
                for chat_id in CHAT_IDS:
                    await bot.send_message(
                        chat_id=chat_id.strip(),
                        text=message,
                        parse_mode="HTML"
                    )
                    print(f"Sent: {message} at {current_time}")
    else:
        print(f"No reminder for {today}")

asyncio.run(send())
