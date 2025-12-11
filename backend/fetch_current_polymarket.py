import requests
import datetime
import pytz
from find_new_market import get_current_market_slug

# API Configuration
POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"
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
        # print(f"CLOB Error for {token_id}: {e}")
        return None, None

def fetch_polymarket_data_struct():
    """
    Orchestrates fetching the current market slug, resolving tokens, and getting prices.
    """
    slug = get_current_market_slug()
    
    try:
        # 1. Get Event Details
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

        # 2. Get Prices for YES (Up) and NO (Down)
        # Returns simple price dict for API compatibility
        prices = {}
        market_slug = slug
        
        for idx, outcome in enumerate(outcomes):
            token_id = clob_token_ids[idx]
            bid, ask = get_clob_price(token_id)
            # We use ASK price because we are BUYING
            prices[outcome] = ask if ask is not None else 0.0
            
        # Return structure compatible with api.py
        return {
            "prices": prices, # {'Up': 0.xx, 'Down': 0.xx}
            "slug": market_slug,
            "target_time_utc": datetime.datetime.now().isoformat() # Placeholder
        }, None

    except Exception as e:
        return None, str(e)
