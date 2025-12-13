import requests
import datetime

# API Endpoints
POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"
CLOB_API_URL = "https://clob.polymarket.com/book"

def get_market_slug():
    # 1. Get LOCAL system time (No UTC, matches your PC clock)
    now = datetime.datetime.now()
    
    # 2. User Rule: "1 hour behind the calculation"
    # If it is 9:XX PM, we target the 9 PM market (not 10 PM).
    # We simply take the current hour.
    target_time = now.replace(minute=0, second=0, microsecond=0)
    
    # 3. Format the slug parts
    month = target_time.strftime("%B").lower()  # e.g., "december"
    day = target_time.day                       # e.g., 12
    hour_int = int(target_time.strftime("%I"))  # e.g., 9 (12-hour format)
    am_pm = target_time.strftime("%p").lower()  # e.g., "pm"
    
    # 4. Construct Slug
    slug = f"bitcoin-up-or-down-{month}-{day}-{hour_int}{am_pm}-et"
    return slug

def get_clob_price(token_id):
    try:
        response = requests.get(CLOB_API_URL, params={"token_id": token_id})
        data = response.json()
        
        # Original Logic: Get the lowest seller (Ask)
        asks = data.get('asks', [])
        if asks:
            return min(float(a['price']) for a in asks)
        else:
            return 0.0
            
    except Exception as e:
        print(f"CLOB Error: {e}")
        return 0.0

def fetch_polymarket_data_struct():
    slug = get_market_slug()
    
    try:
        # 1. Get Event Data
        response = requests.get(POLYMARKET_API_URL, params={"slug": slug})
        if response.status_code != 200:
            return None, f"Event not found: {slug}"
            
        data = response.json()
        if not data:
            return None, "Empty data response"

        # 2. Extract Token IDs
        market = data[0]['markets'][0]
        clob_token_ids = eval(market.get("clobTokenIds", "[]"))
        outcomes = eval(market.get("outcomes", "[]")) 
        
        if len(clob_token_ids) != 2:
            return None, "Market does not have exactly 2 outcomes"

        # 3. Fetch Prices for each Outcome
        prices = {}
        for idx, outcome in enumerate(outcomes):
            token_id = clob_token_ids[idx]
            price = get_clob_price(token_id)
            prices[outcome] = price
            
        return {
            "prices": prices,
            "slug": slug,
            "target_time_utc": datetime.datetime.now().isoformat()
        }, None

    except Exception as e:
        return None, str(e)

if __name__ == "__main__":
    data, err = fetch_polymarket_data_struct()
    print(data)
