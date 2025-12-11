import datetime
import pytz

# Base URL for Polymarket events
BASE_URL = "https://polymarket.com/event/  "

def generate_slug(target_time):
    """
    Generates the Polymarket event slug for a given datetime.
    Format: bitcoin-up-or-down-[month]-[day]-[hour][am/pm]-et
    """
    et_tz = pytz.timezone('US/Eastern')
    if target_time.tzinfo is None:
        target_time = pytz.utc.localize(target_time).astimezone(et_tz)
    else:
        target_time = target_time.astimezone(et_tz)

    month = target_time.strftime("%B").lower()
    day = target_time.day
    # Hour formatting: 12-hour format with am/pm (e.g., 2pm, 11am)
    hour_int = int(target_time.strftime("%I"))
    am_pm = target_time.strftime("%p").lower()
    
    return f"bitcoin-up-or-down-{month}-{day}-{hour_int}{am_pm}-et"

def generate_market_url(target_time):
    return f"{BASE_URL}{generate_slug(target_time)}"

def get_current_market_slug():
    """
    Returns the slug for the NEAREST resolving market (next hour top).
    """
    now = datetime.datetime.now(pytz.utc)
    # Round up to the next hour
    next_hour = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
    return generate_slug(next_hour)

if __name__ == "__main__":
    print(f"Current Target Slug: {get_current_market_slug()}")
