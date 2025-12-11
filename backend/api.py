from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fetch_current_polymarket import fetch_polymarket_data_struct
from find_new_market import get_active_market_slugs # <-- NEW IMPORT
import asyncio
import datetime
import numpy as np

# --- STRATEGY LOGIC (StrategySimulator class remains unchanged) ---
# ... (Keep the StrategySimulator class exactly as it was) ...
class StrategySimulator:
    def __init__(self):
        # Portfolio State
        self.qty_yes = 0
        self.qty_no = 0
        self.total_cost_yes = 0.0
        self.total_cost_no = 0.0
        
        # Strategy Parameters
        self.buy_size = 10  
        self.safety_margin = 0.99 
        self.window_size = 10 
        
        # History
        self.price_history_yes = []
        self.price_history_no = []
        self.history = []

    @property
    def avg_cost_yes(self):
        return (self.total_cost_yes / self.qty_yes) if self.qty_yes > 0 else 0.0

    @property
    def avg_cost_no(self):
        return (self.total_cost_no / self.qty_no) if self.qty_no > 0 else 0.0

    @property
    def pair_cost(self):
        return self.avg_cost_yes + self.avg_cost_no

    @property
    def locked_profit(self):
        matched_pairs = min(self.qty_yes, self.qty_no)
        if matched_pairs == 0: return 0.0
        cost_of_pairs = matched_pairs * self.pair_cost
        return matched_pairs - cost_of_pairs

    def tick(self, market_data):
        if not market_data or 'prices' not in market_data:
            return "No Data"

        # Map 'Up' -> YES, 'Down' -> NO
        price_yes = market_data['prices'].get('Up')
        price_no = market_data['prices'].get('Down')
        
        if price_yes is None or price_no is None:  
            return "No liquidity"

        # Update Price History
        self.price_history_yes.append(price_yes)
        self.price_history_no.append(price_no)
        if len(self.price_history_yes) > self.window_size:
            self.price_history_yes.pop(0)
            self.price_history_no.pop(0)

        action = "Hold"
        
        # 1. Identify "Cheapness" (Dip Buying)
        avg_recent_yes = np.mean(self.price_history_yes)
        avg_recent_no = np.mean(self.price_history_no)
        
        # Buy if price is cheaper than average
        is_cheap_yes = price_yes < (avg_recent_yes - 0.005) 
        is_cheap_no = price_no < (avg_recent_no - 0.005)
        
        # 2. Check Pair Cost Impact
        if is_cheap_yes:
            # Simulate buy
            new_total_cost = self.total_cost_yes + (price_yes * self.buy_size)
            new_qty = self.qty_yes + self.buy_size
            new_avg = new_total_cost / new_qty
            
            # If we have NO shares, check if this buy keeps pair cost low
            potential_pair_cost = new_avg + self.avg_cost_no if self.qty_no > 0 else 0
            
            # Execute if safe or if establishing position
            if self.qty_no == 0 or potential_pair_cost < self.safety_margin:
                self._execute_trade("YES", price_yes)
                action = f"Bought YES @ {price_yes:.3f}"

        elif is_cheap_no:
            new_total_cost = self.total_cost_no + (price_no * self.buy_size)
            new_qty = self.qty_no + self.buy_size
            new_avg = new_total_cost / new_qty
            
            potential_pair_cost = self.avg_cost_yes + new_avg if self.qty_yes > 0 else 0
            
            if self.qty_yes == 0 or potential_pair_cost < self.safety_margin:
                self._execute_trade("NO", price_no)
                action = f"Bought NO @ {price_no:.3f}"
        
        return action

    def _execute_trade(self, side, price):
        if side == "YES":
            self.qty_yes += self.buy_size
            self.total_cost_yes += (price * self.buy_size)
        else:
            self.qty_no += self.buy_size
            self.total_cost_no += (price * self.buy_size)
            
        self.history.append({
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "side": side,
            "price": price,
            "size": self.buy_size
        })

    def get_state(self):
        return {
            "qty_yes": self.qty_yes,
            "qty_no": self.qty_no,
            "avg_cost_yes": self.avg_cost_yes,
            "avg_cost_no": self.avg_cost_no,
            "pair_cost": self.pair_cost,
            "locked_profit": self.locked_profit,
            "history": self.history[-10:]
        }
# --------------------------------------------------------------------------

# --- FASTAPI APP ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State Dictionary to hold both markets
market_state = {
    "1hr": {
        "sim": StrategySimulator(),
        "market_data": None,
        "last_action": "Waiting for market...",
        "slug": ""
    },
    "15min": {
        "sim": StrategySimulator(),
        "market_data": None,
        "last_action": "Waiting for market...",
        "slug": ""
    }
}

# Background Task for a specific market type
async def run_market_loop(market_key):
    global market_state
    
    # 1. Get the initial slugs
    slugs = get_active_market_slugs()
    market_state[market_key]["slug"] = slugs[market_key]
    
    while True:
        try:
            # 2. Fetch data for the market's current slug
            data, err = fetch_polymarket_data_struct(slug_override=market_state[market_key]["slug"]) # fetch_polymarket_data_struct must be modified to accept a slug_override
            
            if data:
                market_state[market_key]["market_data"] = data
                
                # 3. Run the strategy tick
                action = market_state[market_key]["sim"].tick(data)
                market_state[market_key]["last_action"] = action
            else:
                print(f"{market_key} Fetch error: {err}")
                
            # 4. Check if the market has resolved (by checking the time) or if a new market has appeared
            current_slug = market_state[market_key]["slug"]
            new_slugs = get_active_market_slugs()
            new_target_slug = new_slugs[market_key]
            
            if current_slug != new_target_slug:
                print(f"Market Rollover: {market_key} from {current_slug} to {new_target_slug}")
                market_state[market_key]["slug"] = new_target_slug
                market_state[market_key]["sim"] = StrategySimulator() # Reset simulation for new market
            
        except Exception as e:
            print(f"Loop error for {market_key}: {e}")
            
        await asyncio.sleep(2) # Fetch every 2 seconds

@app.on_event("startup")
async def startup_event():
    # Start both loops
    asyncio.create_task(run_market_loop("1hr"))
    asyncio.create_task(run_market_loop("15min"))

@app.get("/simulation")
def get_simulation_state():
    # Return the entire state object
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "1hr": {
            "market": market_state["1hr"]["market_data"],
            "portfolio": market_state["1hr"]["sim"].get_state(),
            "last_action": market_state["1hr"]["last_action"],
            "slug": market_state["1hr"]["slug"]
        },
        "15min": {
            "market": market_state["15min"]["market_data"],
            "portfolio": market_state["15min"]["sim"].get_state(),
            "last_action": market_state["15min"]["last_action"],
            "slug": market_state["15min"]["slug"]
        }
    }

@app.post("/reset/{market_key}")
def reset_simulation(market_key: str):
    global market_state
    if market_key in market_state:
        market_state[market_key]["sim"] = StrategySimulator()
        return {"message": f"Simulation for {market_key} reset"}
    return {"message": "Invalid market key", "status": 400}

if __name__ == "__main__":
    import uvicorn
    # Make sure to run the app with the correct entry point
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
