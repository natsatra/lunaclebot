import os
import json
import asyncio
import pytz
from datetime import datetime
from telegram import Bot

TOKEN: str = os.environ["TELEGRAM_TOKEN"]
CHAT_IDS: list[str] = os.environ["TELEGRAM_CHAT_IDS"].split(",")
DEFAULT_TIME: str = "07:30"

async def send() -> None:
    with open("reminders.json", encoding="utf-8") as f:
        reminders: dict[str, list[dict[str, str]]] = json.load(f)

    IST = pytz.timezone("Asia/Kolkata")
    now: datetime = datetime.now(IST)
    today: str = now.date().isoformat()
    current_time: str = now.strftime("%H:%M")

    if today in reminders:
        bot = Bot(token=TOKEN)
        for entry in reminders[today]:
            message: str = entry["message"]
            send_time: str = entry["time"] if entry["time"] else DEFAULT_TIME

            if send_time == current_time:
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
