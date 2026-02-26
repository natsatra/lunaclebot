import os
import json
import time
import ephem
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from datetime import timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

SHEET_ID = os.environ["SHEET_ID"]
GOOGLE_CREDENTIALS = os.environ["GOOGLE_CREDENTIALS"]

# One line descriptions for each event
DESCRIPTIONS = {
    "Full Moon": "The moon is at peak illumination — a time for release, reflection, and culmination.",
    "New Moon": "The moon begins a new cycle — ideal for setting intentions and new beginnings.",
    "First Quarter Moon": "The moon is half lit — a time to take action and push through challenges.",
    "Last Quarter Moon": "The moon wanes to half — a time to let go, rest, and tie up loose ends.",
    "Spring Equinox": "Day and night are equal length — the season of renewal and fresh starts begins.",
    "Summer Solstice": "The longest day of the year — celebrate abundance, light, and full energy.",
    "Autumn Equinox": "Day and night are equal length — a time for harvest, balance, and gratitude.",
    "Winter Solstice": "The shortest day of the year — embrace stillness, rest, and inner reflection.",
    "Mercury Retrograde Start": "Mercury appears to move backward — double check plans, communication, and travel.",
    "Mercury Retrograde End": "Mercury returns to direct motion — clarity and forward momentum resume.",
    "Venus Opposition": "Venus is closest to Earth and fully illuminated — themes of love and beauty are heightened.",
    "Mars Opposition": "Mars is closest to Earth — energy, ambition, and drive are at their peak.",
    "Jupiter Opposition": "Jupiter is closest to Earth — expansion, luck, and growth are amplified.",
    "Saturn Opposition": "Saturn is closest to Earth — themes of discipline, karma, and structure come into focus.",
    "Perseid Meteor Shower": "One of the best meteor showers of the year — up to 100 meteors per hour at peak.",
    "Leonid Meteor Shower": "The Leonids peak tonight — known for occasional meteor storms, best viewed after midnight.",
    "Geminid Meteor Shower": "The most reliable meteor shower of the year — up to 120 multicolored meteors per hour.",
    "Quadrantid Meteor Shower": "The first major meteor shower of the year — short but intense peak, best before dawn.",
    "Eta Aquarid Meteor Shower": "Debris from Halley's Comet lights up the sky — best viewed in the Southern Hemisphere.",
    "Orionid Meteor Shower": "Halley's Comet debris produces fast bright meteors — best viewed after midnight.",
}

def format_message(event_name):
    description = DESCRIPTIONS.get(event_name, "A notable celestial event worth marking.")
    return f"{event_name} — {description}"

def get_celestial_events(year):
    events = {}

    def add_event(date_str, event_name):
        message = format_message(event_name)
        if date_str in events:
            events[date_str] = events[date_str] + f"\n\n{message}"
        else:
            events[date_str] = message

    # Moon phases
    date = ephem.Date(f'{year}/1/1')
    end = ephem.Date(f'{year+1}/1/1')
    seen = set()

    while date < end:
        for func, name in [
            (ephem.next_full_moon, "Full Moon"),
            (ephem.next_new_moon, "New Moon"),
            (ephem.next_first_quarter_moon, "First Quarter Moon"),
            (ephem.next_last_quarter_moon, "Last Quarter Moon"),
        ]:
            result = func(date)
            dt = ephem.Date(result).datetime().replace(tzinfo=timezone.utc).astimezone(IST)
            date_str = dt.strftime('%Y-%m-%d')
            key = f"{date_str}-{name}"
            if dt.year == year and key not in seen:
                seen.add(key)
                add_event(date_str, name)

        # Advance by roughly one week
        date = ephem.next_new_moon(date) if ephem.next_new_moon(date) < ephem.next_full_moon(date) else ephem.next_full_moon(date)
        date = ephem.Date(date + 1)

    # Solstices and equinoxes
    seasons = [
        (ephem.next_vernal_equinox, "Spring Equinox"),
        (ephem.next_summer_solstice, "Summer Solstice"),
        (ephem.next_autumnal_equinox, "Autumn Equinox"),
        (ephem.next_winter_solstice, "Winter Solstice"),
    ]
    for func, name in seasons:
        result = func(f'{year}/1/1')
        dt = ephem.Date(result).datetime().replace(tzinfo=timezone.utc).astimezone(IST)
        if dt.year == year:
            add_event(dt.strftime('%Y-%m-%d'), name)

    # Planet oppositions
    planets = [
        (ephem.Mars(), "Mars Opposition"),
        (ephem.Jupiter(), "Jupiter Opposition"),
        (ephem.Saturn(), "Saturn Opposition"),
        (ephem.Venus(), "Venus Opposition"),
    ]
    for planet, name in planets:
        try:
            obs_date = ephem.Date(f'{year}/1/1')
            end_date = ephem.Date(f'{year+1}/1/1')
            while obs_date < end_date:
                planet.compute(obs_date)
                sun = ephem.Sun(obs_date)
                diff = abs(planet.hlong - sun.hlong)
                if abs(diff - ephem.pi) < 0.05:
                    dt = ephem.Date(obs_date).datetime()
                    if dt.year == year:
                        add_event(dt.strftime('%Y-%m-%d'), name)
                    break
                obs_date = ephem.Date(obs_date + 10)
        except Exception as e:
            print(f"Skipping {name}: {e}")

    # Fixed meteor showers
    meteor_showers = {
        f"{year}-01-03": "Quadrantid Meteor Shower",
        f"{year}-05-06": "Eta Aquarid Meteor Shower",
        f"{year}-08-12": "Perseid Meteor Shower",
        f"{year}-11-17": "Leonid Meteor Shower",
        f"{year}-10-21": "Orionid Meteor Shower",
        f"{year}-12-13": "Geminid Meteor Shower",
    }
    for date_str, name in meteor_showers.items():
        add_event(date_str, name)

    return dict(sorted(events.items()))

def write_to_sheet(events):
    creds_dict = json.loads(GOOGLE_CREDENTIALS)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet("moon_phases")

    sheet.clear()
    sheet.append_row(["date", "message"])

    for date_str, message in events.items():
        sheet.append_row([date_str, message])
        print(f"Written: {date_str} — {message[:40]}...")
        time.sleep(1)  # avoid hitting Google Sheets API rate limit

    print(f"Done! {len(events)} events written to sheet.")

year = datetime.now().year
print(f"Generating celestial events for {year}...")
events = get_celestial_events(year)
write_to_sheet(events)
