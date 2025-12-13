from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fetch_current_polymarket import fetch_polymarket_data_struct
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

        # --- ADD THIS LOGIC HERE ---
        if price_yes < 0.05: is_cheap_yes = False
        if price_no < 0.05: is_cheap_no = False

        
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
