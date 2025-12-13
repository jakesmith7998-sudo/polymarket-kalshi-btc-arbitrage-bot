from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fetch_current_polymarket import fetch_polymarket_data_struct
import asyncio
import datetime
import numpy as np

# --- GLOBAL MEMORY ---
# We store the running balance here so it persists across resets.
GLOBAL_BALANCE = 10.00 

class StrategySimulator:
    def __init__(self, starting_balance):
        # Portfolio State
        self.cash_balance = starting_balance  # Starts with $10 (or whatever is passed)
        self.qty_yes = 0.0
        self.qty_no = 0.0
        self.total_cost_yes = 0.0
        self.total_cost_no = 0.0
        
        # --- FIXED BUY SIZE ---
        self.buy_size = 0.05  # 0.05 shares per trade
        
        self.safety_margin = 0.99 
        self.window_size = 10 
        self.min_price_threshold = 0.05  
        
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
        # Profit locked in specifically from arbitrage pairs
        matched_pairs = min(self.qty_yes, self.qty_no)
        if matched_pairs == 0: return 0.0
        cost_of_pairs = matched_pairs * self.pair_cost
        return matched_pairs - cost_of_pairs

    @property
    def total_equity(self):
        # Cash + Value of Locked Pairs (Conservative Estimate)
        # We value unmatched shares at 0 for safety, matched pairs at $1.00
        matched_pairs = min(self.qty_yes, self.qty_no)
        return self.cash_balance + matched_pairs

    def tick(self, market_data):
        if not market_data or 'prices' not in market_data:
            return "No Data"

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
        
        # 1. Identify "Cheapness"
        avg_recent_yes = np.mean(self.price_history_yes)
        avg_recent_no = np.mean(self.price_history_no)
        
        is_cheap_yes = price_yes < (avg_recent_yes - 0.005) 
        is_cheap_no = price_no < (avg_recent_no - 0.005)
        
        if price_yes < self.min_price_threshold: is_cheap_yes = False
        if price_no < self.min_price_threshold: is_cheap_no = False
        
        # 2. Check Pair Cost Impact
        if is_cheap_yes:
            cost = price_yes * self.buy_size
            # --- CRITICAL: BALANCE CHECK ---
            if self.cash_balance >= cost:
                potential_pair_cost = ((self.total_cost_yes + cost)/(self.qty_yes + self.buy_size)) + self.avg_cost_no if self.qty_no > 0 else 0
                
                if self.qty_no == 0 or potential_pair_cost < self.safety_margin:
                    self._execute_trade("YES", price_yes, cost)
                    action = f"Bought YES @ {price_yes:.3f}"
            else:
                action = "Insufficient Funds"

        elif is_cheap_no:
            cost = price_no * self.buy_size
            # --- CRITICAL: BALANCE CHECK ---
            if self.cash_balance >= cost:
                potential_pair_cost = self.avg_cost_yes + ((self.total_cost_no + cost)/(self.qty_no + self.buy_size)) if self.qty_yes > 0 else 0
                
                if self.qty_yes == 0 or potential_pair_cost < self.safety_margin:
                    self._execute_trade("NO", price_no, cost)
                    action = f"Bought NO @ {price_no:.3f}"
            else:
                action = "Insufficient Funds"
        
        return action

    def _execute_trade(self, side, price, cost):
        # Deduct Cash
        self.cash_balance -= cost
        
        if side == "YES":
            self.qty_yes += self.buy_size
            self.total_cost_yes += cost
        else:
            self.qty_no += self.buy_size
            self.total_cost_no += cost
            
        self.history.append({
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "side": side,
            "price": price,
            "size": self.buy_size
        })

    def get_state(self):
        return {
            "cash_balance": round(self.cash_balance, 4), # NEW FIELD
            "total_equity": round(self.total_equity, 4), # NEW FIELD
            "qty_yes": round(self.qty_yes, 3),
            "qty_no": round(self.qty_no, 3),
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

# Initialize Global Sim with $10.00
sim = StrategySimulator(starting_balance=GLOBAL_BALANCE)
latest_market_data = None
last_action = "Waiting for market..."

async def run_simulation_loop():
    global latest_market_data, last_action, sim, GLOBAL_BALANCE
    while True:
        try:
            data, err = fetch_polymarket_data_struct()
            if data:
                # ROLLOVER LOGIC (Hourly Reset)
                if latest_market_data and data['slug'] != latest_market_data['slug']:
                    print(f"Market Rollover detected: {data['slug']}")
                    
                    # 1. CALCULATE PAYOUT
                    # Matches pay $1.00. Unmatched shares expire worthless ($0).
                    payout = min(sim.qty_yes, sim.qty_no) * 1.00
                    
                    # 2. UPDATE GLOBAL BALANCE
                    # New Balance = Leftover Cash + Payout
                    GLOBAL_BALANCE = sim.cash_balance + payout
                    
                    print(f"Round Ended. Payout: ${payout:.2f}. New Balance: ${GLOBAL_BALANCE:.2f}")

                    # 3. RESTART BOT WITH NEW BALANCE
                    sim = StrategySimulator(starting_balance=GLOBAL_BALANCE)
                    
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
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "market": latest_market_data,
        "portfolio": sim.get_state(),
        "last_action": last_action
    }

@app.post("/reset")
def reset_simulation():
    global sim, GLOBAL_BALANCE
    # Manual Reset: Assume we sell/payout immediately
    payout = min(sim.qty_yes, sim.qty_no) * 1.00
    GLOBAL_BALANCE = sim.cash_balance + payout
    
    sim = StrategySimulator(starting_balance=GLOBAL_BALANCE)
    return {"message": "Simulation reset", "new_balance": GLOBAL_BALANCE}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
