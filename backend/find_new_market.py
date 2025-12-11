import datetime
import pytz

# Base URL for Polymarket events
BASE_URL = "https://polymarket.com/event/"

def generate_slug(target_time):
    """
    Generates the Polymarket event slug for a given datetime.
    Format: bitcoin-up-or-down-[month]-[day]-[hour][minutes][am/pm]-et
    Example: bitcoin-up-or-down-december-12-215pm-et
    """
    et_tz = pytz.timezone('US/Eastern')
    if target_time.tzinfo is None:
        target_time = pytz.utc.localize(target_time).astimezone(et_tz)
    else:
        target_time = target_time.astimezone(et_tz)

    month = target_time.strftime("%B").lower()
    day = target_time.day
    hour_int = int(target_time.strftime("%I"))  # 12-hour format
    am_pm = target_time.strftime("%p").lower()
    minutes = target_time.strftime("%M")       # Include minutes

    # Format slug for 15-min intervals: e.g., 215pm, 230pm, 245pm, 300pm (for 3:00)
    # Polymarket might use 00 for :00, otherwise include the minutes
    if minutes == "00":
        return f"bitcoin-up-or-down-{month}-{day}-{hour_int}{am_pm}-et"
    else:
        return f"bitcoin-up-or-down-{month}-{day}-{hour_int}{minutes}{am_pm}-et"


def get_current_market_slug():
    """
    Returns the slug for the NEAREST resolving 15-minute market.
    Rounds up to the next 15-minute mark.
    """
    now = datetime.datetime.now(pytz.utc)
    et_tz = pytz.timezone('US/Eastern')
    now_et = now.astimezone(et_tz)

    # Calculate minutes past the hour
    current_minute = now_et.minute
    current_second = now_et.second

    # Determine the next 15-minute mark
    # Intervals: 00, 15, 30, 45
    target_minute = ((current_minute // 15) + 1) * 15

    if target_minute >= 60:  # Handle hour/day rollover
        target_time = now_et.replace(minute=target_minute, second=0, microsecond=0) + datetime.timedelta(hours=1)
        target_time = target_time.replace(minute=0)
    else:
        target_time = now_et.replace(minute=target_minute, second=0, microsecond=0)

    return generate_slug(target_time)


if __name__ == "__main__":
    print(f"Nearest 15-min Target Slug: {get_current_market_slug()}")
    print(f"Target Time (ET): {datetime.datetime.now(pytz.utc).astimezone(pytz.timezone('US/Eastern')) + datetime.timedelta(minutes=15 - datetime.datetime.now(pytz.timezone('US/Eastern')).minute % 15)}")
