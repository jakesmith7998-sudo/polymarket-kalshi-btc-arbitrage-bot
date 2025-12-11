import datetime
import pytz

# Base URL for Polymarket events
BASE_URL = "https://polymarket.com/event/"
ET_TZ = pytz.timezone('US/Eastern')

def _format_time(target_time):
    """Formats the time part of the slug: [month]-[day]-[hour][am/pm]-et"""
    if target_time.tzinfo is None:
        target_time = pytz.utc.localize(target_time).astimezone(ET_TZ)
    else:
        target_time = target_time.astimezone(ET_TZ)

    month = target_time.strftime("%B").lower()
    day = target_time.day
    # Hour formatting: 12-hour format with am/pm (e.g., 2pm, 11am)
    hour_int = int(target_time.strftime("%I"))
    am_pm = target_time.strftime("%p").lower()
    
    # Check for 15-minute markets by seeing if the minute is non-zero
    minute_part = f"-{target_time.minute}m" if target_time.minute != 0 else ""

    return f"bitcoin-up-or-down-{month}-{day}-{hour_int}{am_pm}{minute_part}-et"

def get_market_slug(timeframe_minutes):
    """Returns the slug for the NEAREST resolving market based on the timeframe."""
    now = datetime.datetime.now(pytz.utc)
    
    if timeframe_minutes == 60: # Hourly Market
        # Round up to the next hour
        target_time = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
    elif timeframe_minutes == 15: # 15-Minute Market
        # Calculate time difference to the nearest 15-minute mark (00, 15, 30, 45)
        current_minute = now.minute
        remainder = current_minute % 15
        minutes_to_add = 15 - remainder
        
        target_time = now + datetime.timedelta(minutes=minutes_to_add)
        target_time = target_time.replace(second=0, microsecond=0)
    else:
        raise ValueError("Unsupported timeframe. Use 15 or 60.")
        
    return _format_time(target_time)

def get_active_market_slugs():
    """Returns slugs for both 1-hour and 15-minute markets."""
    return {
        "1hr": get_market_slug(60),
        "15min": get_market_slug(15)
    }

if __name__ == "__main__":
    slugs = get_active_market_slugs()
    print(f"1-Hour Target Slug: {slugs['1hr']}")
    print(f"15-Minute Target Slug: {slugs['15min']}")
