import os
import asyncio
import pytz
from datetime import datetime
from telegram import Bot
from sync_sheet import merge_reminders

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_IDS = os.environ["TELEGRAM_CHAT_IDS"].split(",")

# The IST times the workflow actually runs. Must match the cron in
# .github/workflows/reminder.yml. A reminder's `time` column picks which of
# these runs it goes out on; blank means every run.
SLOT_TIMES = [s.strip() for s in os.environ.get("SLOT_TIMES", "07:30,18:00").split(",")]

def to_minutes(hhmm):
    try:
        hours, minutes = hhmm.split(":")
        return int(hours) * 60 + int(minutes)
    except (ValueError, AttributeError):
        return None

SLOTS = [s for s in SLOT_TIMES if to_minutes(s) is not None]

def nearest_slot(hhmm):
    """The run closest to the given time, measured around the clock."""
    target = to_minutes(hhmm)
    if target is None or not SLOTS:
        return None
    return min(
        SLOTS,
        key=lambda slot: min((to_minutes(slot) - target) % 1440,
                             (target - to_minutes(slot)) % 1440)
    )

async def send():
    reminders = merge_reminders()

    IST = pytz.timezone("Asia/Kolkata")
    now = datetime.now(IST)
    today = now.date().isoformat()
    current_time = now.strftime("%H:%M")
    current_slot = nearest_slot(current_time)

    if today not in reminders:
        print(f"No reminder for {today}")
        return

    bot = Bot(token=TOKEN)
    for entry in reminders[today]:
        message = entry["message"]
        send_time = entry["time"]
        slot = nearest_slot(send_time) if send_time else None

        if send_time and slot is None:
            print(f"Unreadable time '{send_time}', sending anyway: {message}")
        elif slot and slot != current_slot:
            print(f"Skipped, belongs to the {slot} run: {message}")
            continue

        for chat_id in CHAT_IDS:
            await bot.send_message(
                chat_id=chat_id.strip(),
                text=message,
                parse_mode="HTML"
            )
        print(f"Sent at {current_time} ({current_slot} run): {message}")

asyncio.run(send())
