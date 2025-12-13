import requests
import datetime
import pytz

# API Configuration
POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"
CLOB_API_URL = "https://clob.polymarket.com/book"

def get_market_slug():
    """
    Returns the slug for the NEAREST resolving market (next hour top).
    """
    now = datetime.datetime.now(pytz.utc)
    next_hour = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
    
    month = next_hour.strftime("%B").lower()
    day = next_hour.day
    hour_int = int(next_hour.strftime("%I"))
    am_pm = next_hour.strftime("%p").lower()
    
    return f"bitcoin-up-or-down-{month}-{day}-{hour_int}{am_pm}-et"

def get_clob_price(token_id):
    """
    Fetches price with a safety fallback.
    1. Try getting the lowest SELL price (Ask).
    2. If no sellers, try getting the highest BUY price (Bid).
    3. If neither, assume 0.
    """
    try:
        response = requests.get(CLOB_API_URL, params={"token_id": token_id})
        data = response.json()
        
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        
        best_ask = None
        best_bid = None

        if asks:
            best_ask = min(float(a['price']) for a in asks)
        
        if bids:
            best_bid = max(float(b['price']) for b in bids)

        # --- THE FIX: SMART PRICING ---
        # If we can buy it (Ask exists), use Ask.
        if best_ask is not None:
            return best_ask
        
        # If no one is selling (Ask is empty), maybe it's because it's worth $1.00?
        # Check the Bid. If Bid is high (e.g. 0.99), use that.
        if best_bid is not None:
            return best_bid
            
        return 0.0
        
    except Exception as e:
        print(f"CLOB Error for {token_id}: {e}")
        return 0.0

def fetch_polymarket_data_struct():
    slug = get_market_slug()
    
    try:
        response = requests.get(POLYMARKET_API_URL, params={"slug": slug})
        if response.status_code != 200:
            return None, f"Event not found: {slug}"
            
        data = response.json()
        if not data:
            return None, "Empty data response"

        market = data[0]['markets'][0]
        clob_token_ids = eval(market.get("clobTokenIds", "[]"))
        outcomes = eval(market.get("outcomes", "[]")) 
        
        if len(clob_token_ids) != 2:
            return None, "Market does not have exactly 2 outcomes"

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
