import os
import asyncio
import pytz
from datetime import datetime, timedelta
from telegram import Bot
from sync_sheet import merge_reminders

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_IDS = os.environ["TELEGRAM_CHAT_IDS"].split(",")

IST = pytz.timezone("Asia/Kolkata")

# The cron line GitHub matched to start this run, e.g. "30 12 * * *". Blank on
# workflow_dispatch, where there is no cron to attribute the run to.
TRIGGER_CRON = os.environ.get("TRIGGER_CRON", "").strip()

# GitHub starts scheduled runs late -- usually under two hours, but it has
# stretched past ten. Past this many hours the moment has gone and firing the
# reminder does more harm than staying quiet. 0 disables the guard.
MAX_DELAY_HOURS = float(os.environ.get("MAX_DELAY_HOURS", "6"))


def scheduled_run(cron, now):
    """When this run was *meant* to start, as an IST datetime.

    GitHub only ever starts a scheduled run late, never early, so the run
    belongs to the last time its cron came round. When a delay drags a run past
    midnight that is yesterday -- which is the whole reason this exists, and
    the bug that delivered the 28th's reminder at 03:59 on the 28th when it was
    really the 27th's evening run. Returns None if the cron is not a single
    fixed time of day.
    """
    fields = cron.split()
    if len(fields) < 2:
        return None
    try:
        utc_minutes = int(fields[1]) * 60 + int(fields[0])
    except ValueError:
        return None  # a range or list like "0,30" -- no single moment to use
    # Cron is UTC; IST is a fixed +05:30, with no DST to complicate the shift.
    offset = int(IST.utcoffset(datetime(2000, 1, 1)).total_seconds() // 60)
    ist_minutes = (utc_minutes + offset) % 1440
    at = now.replace(hour=ist_minutes // 60, minute=ist_minutes % 60,
                     second=0, microsecond=0)
    return at - timedelta(days=1) if at > now else at


async def send():
    now = datetime.now(IST)
    scheduled = scheduled_run(TRIGGER_CRON, now) if TRIGGER_CRON else None

    late = None
    if scheduled:
        late = (now - scheduled).total_seconds() / 3600
        today = scheduled.date().isoformat()
        print(f"Cron '{TRIGGER_CRON}' is the run for {today}, "
              f"started {late:.2f}h late")
    else:
        # Manual dispatch, or a local run: no cron to attribute, use the clock.
        today = now.date().isoformat()
        print(f"No trigger cron; using today, {today}")

    # Read the sheet before deciding a late run is too late, so the log can say
    # whether anything was actually lost. A silent workflow is hard enough to
    # diagnose without "sent nothing" covering both "dropped your birthday" and
    # "there was nothing to send".
    due = merge_reminders().get(today, [])
    if not due:
        print(f"No reminder for {today}")
        return

    if late is not None and MAX_DELAY_HOURS and late > MAX_DELAY_HOURS:
        print(f"Stale: {late:.2f}h behind the {today} run, dropping {len(due)}:")
        for entry in due:
            print(f"  dropped: {entry['message']}")
        return

    bot = Bot(token=TOKEN)
    for entry in due:
        for chat_id in CHAT_IDS:
            await bot.send_message(chat_id=chat_id.strip(),
                                   text=entry["message"], parse_mode="HTML")
        print(f"Sent {now:%H:%M} ({today}): {entry['message']}")


if __name__ == "__main__":
    asyncio.run(send())
