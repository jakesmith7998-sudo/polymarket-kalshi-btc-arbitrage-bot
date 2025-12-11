from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fetch_current_polymarket import fetch_polymarket_data_struct
from fetch_current_kalshi import fetch_kalshi_data_struct
import asyncio
import datetime
import numpy as np

# --- STRATEGY LOGIC ---
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

# --- FASTAPI APP ---
app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Simulation Instance
sim = StrategySimulator()
latest_market_data = None
last_action = "Waiting for market..."

# Background Task
async def run_simulation_loop():
    global latest_market_data, last_action
    while True:
        try:
            data, err = fetch_polymarket_data_struct()
            if data:
                latest_market_data = data
                action = sim.tick(data)
                last_action = action
            else:
                print(f"Fetch error: {err}")
        except Exception as e:
            print(f"Loop error: {e}")
        await asyncio.sleep(2)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_simulation_loop())

@app.get("/arbitrage")
def get_arbitrage_data():
    # Fetch Data
    poly_data, poly_err = fetch_polymarket_data_struct()
    kalshi_data, kalshi_err = fetch_kalshi_data_struct()
    
    response = {
        "polymarket": poly_data,
        "kalshi": kalshi_data,
        "checks": [],
        "opportunities": [],
        "errors": []
    }
    
    if poly_err:
        response["errors"].append(poly_err)
    if kalshi_err:
        response["errors"].append(kalshi_err)
        
    if not poly_data or not kalshi_data:
        return response

    # Logic
    poly_strike = poly_data['price_to_beat']
    poly_up_cost = poly_data['prices'].get('Up', 0.0)
    poly_down_cost = poly_data['prices'].get('Down', 0.0)
    
    if poly_strike is None:
        response["errors"].append("Polymarket Strike is None")
        return response

    kalshi_markets = kalshi_data.get('markets', [])
    
    # Ensure sorted by strike
    kalshi_markets.sort(key=lambda x: x['strike'])
    
    # Find index closest to poly_strike
    closest_idx = 0
    min_diff = float('inf')
    for i, m in enumerate(kalshi_markets):
        diff = abs(m['strike'] - poly_strike)
        if diff < min_diff:
            min_diff = diff
            closest_idx = i
            
    # Select 4 below and 4 above (approx 8-9 markets total)
    # If closest is at index C, we want [C-4, C+5] roughly
    start_idx = max(0, closest_idx - 4)
    end_idx = min(len(kalshi_markets), closest_idx + 5) # +5 to include the closest and 4 above
    
    selected_markets = kalshi_markets[start_idx:end_idx]
    
    for km in selected_markets:
        kalshi_strike = km['strike']
        kalshi_yes_cost = km['yes_ask'] / 100.0
        kalshi_no_cost = km['no_ask'] / 100.0
        
        # Only check markets within range (removed previous hardcoded range check)
            
        check_data = {
            "kalshi_strike": kalshi_strike,
            "kalshi_yes": kalshi_yes_cost,
            "kalshi_no": kalshi_no_cost,
            "type": "",
            "poly_leg": "",
            "kalshi_leg": "",
            "poly_cost": 0,
            "kalshi_cost": 0,
            "total_cost": 0,
            "is_arbitrage": False,
            "margin": 0
        }

        if poly_strike > kalshi_strike:
            check_data["type"] = "Poly > Kalshi"
            check_data["poly_leg"] = "Down"
            check_data["kalshi_leg"] = "Yes"
            check_data["poly_cost"] = poly_down_cost
            check_data["kalshi_cost"] = kalshi_yes_cost
            check_data["total_cost"] = poly_down_cost + kalshi_yes_cost
            
        elif poly_strike < kalshi_strike:
            check_data["type"] = "Poly < Kalshi"
            check_data["poly_leg"] = "Up"
            check_data["kalshi_leg"] = "No"
            check_data["poly_cost"] = poly_up_cost
            check_data["kalshi_cost"] = kalshi_no_cost
            check_data["total_cost"] = poly_up_cost + kalshi_no_cost
            
        elif poly_strike == kalshi_strike:
            # Check 1
            check1 = check_data.copy()
            check1["type"] = "Equal"
            check1["poly_leg"] = "Down"
            check1["kalshi_leg"] = "Yes"
            check1["poly_cost"] = poly_down_cost
            check1["kalshi_cost"] = kalshi_yes_cost
            check1["total_cost"] = poly_down_cost + kalshi_yes_cost
            
            if check1["total_cost"] < 1.00:
                check1["is_arbitrage"] = True
                check1["margin"] = 1.00 - check1["total_cost"]
                response["opportunities"].append(check1)
            response["checks"].append(check1)
            
            # Check 2
            check2 = check_data.copy()
            check2["type"] = "Equal"
            check2["poly_leg"] = "Up"
            check2["kalshi_leg"] = "No"
            check2["poly_cost"] = poly_up_cost
            check2["kalshi_cost"] = kalshi_no_cost
            check2["total_cost"] = poly_up_cost + kalshi_no_cost
            
            if check2["total_cost"] < 1.00:
                check2["is_arbitrage"] = True
                check2["margin"] = 1.00 - check2["total_cost"]
                response["opportunities"].append(check2)
            response["checks"].append(check2)
            continue # Skip adding the base check_data

        if check_data["total_cost"] < 1.00:
            check_data["is_arbitrage"] = True
            check_data["margin"] = 1.00 - check_data["total_cost"]
            response["opportunities"].append(check_data)
            
        response["checks"].append(check_data)
        
    return response

@app.get("/simulation")
def get_simulation_state():
    state = sim.get_state()
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "market": latest_market_data,
        "portfolio": state,
        "last_action": last_action
    }
    
@app.post("/reset")
def reset_simulation():
    global sim
    sim = StrategySimulator()
    return {"message": "Simulation reset"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
