import datetime
import pytz

# Base URL for Polymarket events
BASE_URL = "https://polymarket.com/event/"

def generate_slug(target_time):
    """
    Generates the Polymarket event slug for a given datetime.
    Format: bitcoin-up-or-down-[month]-[day]-[hour][am/pm]-et
    """
    et_tz = pytz.timezone('US/Eastern')
    # Ensure target_time is in ET
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
    Returns the slug for the CURRENT hour (Round Down).
    Example: If it is 7:05 PM, this returns the 7pm slug.
    """
    et_tz = pytz.timezone('US/Eastern')
    now_et = datetime.datetime.now(et_tz)
    
    # Logic: Take current ET time and simply zero out the minutes.
    # This "rounds down" to the top of the current hour.
    current_hour_top = now_et.replace(minute=0, second=0, microsecond=0)
    
    return generate_slug(current_hour_top)

if __name__ == "__main__":
    # Run this file directly to verify the time calculation
    slug = get_current_market_slug()
    print(f"Calculated Target Slug: {slug}")
    print(f"If it is 7:05 PM, this should now say 7pm.")
