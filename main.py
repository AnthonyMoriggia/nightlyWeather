import logging
import os
import requests
import schedule
import time
from datetime import datetime, timedelta
from twilio.rest import Client
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    filename="nightly_weather.log",
    format="%(asctime)s [%(levelname)s] %(message)s"
)

load_dotenv()
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM_NUMBER")
TWILIO_TO = os.getenv("TWILIO_TO_NUMBER")

# Washington, D.C. longitude and latitude
LAT = 38.9072
LON = -77.0369

# Minimum allowed temperature
LOWEST_ALLOWED_TEMP = 65


def fetch_hourly_weather():
    # Url for Weather API to pull only hourly weather
    url = (
        f"https://api.openweathermap.org/data/3.0/onecall?"
        f"lat={LAT}&lon={LON}"
        f"&exclude=minutely,daily,alerts"
        f"&appid={WEATHER_API_KEY}&units=imperial"
    )
    # Get response from API as JSON
    response = requests.get(url)
    response.raise_for_status()
    # Return JSON information converted to dict
    return response.json()["hourly"]


def alert(hourly_data):
    now = datetime.now()
    night_start = now.replace(hour=21, minute=0, second=0, microsecond=0)
    night_end = (now + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)

    for hour in hourly_data:
        dt = datetime.fromtimestamp(hour["dt"])
        if night_start <= dt <= night_end and hour["temp"] < LOWEST_ALLOWED_TEMP:
            return "No A/C tonight"

    return "🔥 Run that A/C!"


def send_sms(message):
    #logging.info("[TEST MODE] Message to be sent: %s", message)
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    sms = client.messages.create(
        body=message,
        from_=TWILIO_FROM,
        to=TWILIO_TO
    )
    logging.info("SMS sent, SID: %s", sms.sid)


def run_weather_check():
    try:
        hourly = fetch_hourly_weather()
        message = alert(hourly)
        send_sms(message)
    except Exception as e:
        logging.exception("Something went wrong.")


def start_scheduler():
    schedule.every().day.at("20:45").do(run_weather_check)
    logging.info("Weather checker started. Daily checks at 8:50 PM.")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    start_scheduler()
    # Testing without sms
    # hourly = fetch_hourly_weather()
    # message = alert(hourly)
    # print(message)

