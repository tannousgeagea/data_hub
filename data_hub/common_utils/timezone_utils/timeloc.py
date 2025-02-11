import requests
from datetime import datetime, timezone
import pytz
import logging

def get_location_and_timezone():
    timezone = "Europe/Berlin"
    try:
        response = requests.get("https://ipinfo.io")
        if response.status_code != 200:
            raise ValueError(f"{response.text}")

        data = response.json()
        timezone = data['timezone']
    except Exception as err:
        logging.error(f'Error Fetching IP info: {err}')
    
    return timezone

def convert_to_local_time(utc_time:datetime, timezone_str:str):
    if utc_time.tzinfo is None:
        utc_time = pytz.utc.localize(utc_time)
        
    local_timezone = pytz.timezone(timezone_str)
    local_time = utc_time.astimezone(local_timezone)
    return local_time