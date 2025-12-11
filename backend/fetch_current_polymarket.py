import requests
import datetime
import pytz
import re # Import regex for slug matching

# API Configuration
POLYMARKET_EVENTS_URL = "https://gamma-api.polymarket.com/events"  # Main events feed
CLOB_API_URL = "https://clob.polymarket.com/book"

def get_clob_price(token_id):
    """
    Fetches the best BUY price (Ask) and best SELL price (Bid).
    """
    try:
        response = requests.get(CLOB_API_URL, params={"token_id": token_id})
        response.raise_for_status()
        data = response.json()

        bids = data.get('bids', [])
        asks = data.get('asks', [])

        # Best Ask (Lowest seller) - This is the price we BUY at
        best_ask = min(float(a['price']) for a in asks) if asks else None

        # Best Bid (Highest buyer) - This is the price we SELL at
        best_bid = max(float(b['price']) for b in bids) if bids else None

        return best_bid, best_ask
    except Exception as e:
        print(f"CLOB Error for {token_id}: {e}")
        return None, None

def fetch_polymarket_data_struct():
    """
    Fetches the nearest resolving 15-minute Bitcoin Up/Down market.
    """
    try:
        # 1. Get All Events
        response = requests.get(POLYMARKET_EVENTS_URL)
        response.raise_for_status()
        events_data = response.json()

        # 2. Filter for Active "Bitcoin Up or Down" Markets
        btc_markets = []
        for event in events_data:
             # Check if the event title matches "Bitcoin Up or Down" pattern (case-insensitive)
             if re.search(r'^Bitcoin Up or Down\b', event.get('title', ''), re.IGNORECASE):
                 markets = event.get('markets', [])
                 for market in markets:
                     # Ensure it's active/resolving and has 2 outcomes (Up/Down)
                     if market.get('active', False) and len(eval(market.get("outcomes", "[]"))) == 2:
                         # Parse the resolution date (end_date) from the market
                         end_date_str = market.get('end_date')
                         if end_date_str:
                             try:
                                 # Polymarket API often uses ISO format
                                 resolution_time = datetime.datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                                 resolution_time_utc = resolution_time.astimezone(pytz.utc)
                                 btc_markets.append({
                                     'market': market,
                                     'resolution_time_utc': resolution_time_utc,
                                     'event_slug': event.get('slug') # Include the event slug part
                                 })
                             except ValueError:
                                 print(f"Could not parse end_date: {end_date_str}")

        if not btc_markets:
            return None, "No active Bitcoin Up or Down markets found."

        # 3. Find the Nearest Future Resolution Time (Potential 15-min window)
        now_utc = datetime.datetime.now(pytz.utc)
        nearest_market_data = None
        min_time_diff = float('inf')

        for item in btc_markets:
            time_diff = (item['resolution_time_utc'] - now_utc).total_seconds()
            if 0 < time_diff < min_time_diff: # Only consider future markets
                min_time_diff = time_diff
                nearest_market_data = item

        if not nearest_market_data:
             return None, "No future Bitcoin Up or Down markets found."

        # 4. Extract details for the nearest market
        market_details = nearest_market_data['market']
        resolution_time_utc = nearest_market_data['resolution_time_utc']
        # Use the event slug, assuming it's the full slug needed for UI or further lookups
        event_slug = nearest_market_data['event_slug']

        clob_token_ids = eval(market_details.get("clobTokenIds", "[]"))
        outcomes = eval(market_details.get("outcomes", "[]"))

        if len(clob_token_ids) != 2:
            return None, f"Nearest market ({event_slug}) does not have exactly 2 outcomes"

        # 5. Get Prices for YES (Up) and NO (Down) from CLOB
        prices = {}

        for idx, outcome in enumerate(outcomes):
            token_id = clob_token_ids[idx]
            bid, ask = get_clob_price(token_id)
            # We use ASK price because we are BUYING
            prices[outcome] = ask if ask is not None else 0.0

        # Return structure compatible with api.py, including resolution time
        return {
            "prices": prices, # {'Up': 0.xx, 'Down': 0.xx}
            "slug": event_slug, # Use the slug from the event details
            "target_time_utc": resolution_time_utc.isoformat() # Actual resolution time from API
        }, None

    except Exception as e:
        return None, str(e)

# Example usage if run directly
if __name__ == "__main__":
    data, err = fetch_polymarket_data_struct()
    if err:
        print(f"Error: {err}")
    else:
        print(f"Data: {data}")
