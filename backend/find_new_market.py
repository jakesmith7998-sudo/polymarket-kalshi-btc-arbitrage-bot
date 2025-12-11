import datetime
import pytz

# Base URL for Polymarket events
BASE_URL = "https://polymarket.com/event/"
ET_TZ = pytz.timezone('US/Eastern')

def _format_time(target_time):
    """Generates the time part of the slug: [month]-[day]-[hour][am/pm]-et"""
    if target_time.tzinfo is None:
        target_time = pytz.utc.localize(target_time).astimezone(ET_TZ)
    else:
        target_time = target_time.astimezone(ET_TZ)

    month = target_time.strftime("%B").lower()
    day = target_time.day
    # Hour formatting: 12-hour format with am/pm (e.g., 2pm, 11am)
    hour_int = int(target_time.strftime("%I"))
    am_pm = target_time.strftime("%p").lower()
    
    # Minute formatting: Adds '-15m', '-30m', or '-45m' if not on the hour.
    minute_part = f"-{target_time.minute}m" if target_time.minute != 0 else ""

    return f"bitcoin-up-or-down-{month}-{day}-{hour_int}{am_pm}{minute_part}-et"

def get_current_market_slug():
    """
    Returns the slug for the NEAREST resolving 15-minute market.
    Rounds up to the next 15-minute mark (00, 15, 30, 45).
    """
    now = datetime.datetime.now(pytz.utc)
    
    # Calculate time difference to the nearest 15-minute mark
    current_minute = now.minute
    remainder = current_minute % 15
    minutes_to_add = 15 - remainder
    
    target_time = now + datetime.timedelta(minutes=minutes_to_add)
    target_time = target_time.replace(second=0, microsecond=0)
    
    return _format_time(target_time)

def generate_market_url(target_time):
    return f"{BASE_URL}{_format_time(target_time)}"

if __name__ == "__main__":
    print(f"Current Target Slug: {get_current_market_slug()}")
