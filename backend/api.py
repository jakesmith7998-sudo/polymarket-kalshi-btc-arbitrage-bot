from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fetch_current_polymarket import fetch_polymarket_data_struct
import asyncio
import datetime
import numpy as np

# --- GLOBAL MEMORY ---
GLOBAL_BALANCE = 10.00 

class StrategySimulator:
    def __init__(self, starting_balance):
        self.cash_balance = starting_balance  
        self.qty_yes = 0.0
        self.qty_no = 0.0
        self.total_cost_yes = 0.0
        self.total_cost_no = 0.0
        
        # --- LIVE PRICE TRACKING ---
        self.current_price_yes = 0.0
        self.current_price_no = 0.0
        
        # --- SETTINGS ---
        self.buy_size = 0.05  
        self.safety_margin = 0.99 
        self.window_size = 10 
        self.min_price_threshold = 0.05   
        
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

    @property
    def total_equity(self):
        # --- REAL-TIME MARK-TO-MARKET ---
        # Values your portfolio at the exact current market price.
        # If the price crashes, your Equity crashes immediately.
        val_yes = self.qty_yes * self.current_price_yes
        val_no = self.qty_no * self.current_price_no
        return self.cash_balance + val_yes + val_no

    def tick(self, market_data):
        if not market_data or 'prices' not in market_data: return "No Data"

        price_yes = market_data['prices'].get('Up')
        price_no = market_data['prices'].get('Down')
        
        if price_yes is None or price_no is None: return "No liquidity"

        # UPDATE LIVE PRICES (For Equity Calculation)
        self.current_price_yes = price_yes
        self.current_price_no = price_no

        # Update History
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
        
        # 2. Check Pair Cost & Balance
        if is_cheap_yes:
            cost = price_yes * self.buy_size
            if self.cash_balance >= cost:
                potential_pair_cost = ((self.total_cost_yes + cost)/(self.qty_yes + self.buy_size)) + self.avg_cost_no if self.qty_no > 0 else 0
                if self.qty_no == 0 or potential_pair_cost < self.safety_margin:
                    self._execute_trade("YES", price_yes, cost)
                    action = f"Bought YES @ {price_yes:.3f}"
            else:
                action = "Insufficient Funds"

        elif is_cheap_no:
            cost = price_no * self.buy_size
            if self.cash_balance >= cost:
                potential_pair_cost = self.avg_cost_yes + ((self.total_cost_no + cost)/(self.qty_no + self.buy_size)) if self.qty_yes > 0 else 0
                if self.qty_yes == 0 or potential_pair_cost < self.safety_margin:
                    self._execute_trade("NO", price_no, cost)
                    action = f"Bought NO @ {price_no:.3f}"
            else:
                action = "Insufficient Funds"
        
        return action

    def _execute_trade(self, side, price, cost):
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
            "cash_balance": round(self.cash_balance, 4),
            "total_equity": round(self.total_equity, 4),
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
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

sim = StrategySimulator(starting_balance=GLOBAL_BALANCE)
latest_market_data = None
last_action = "Waiting for market..."

async def run_simulation_loop():
    global latest_market_data, last_action, sim, GLOBAL_BALANCE
    while True:
        try:
            data, err = fetch_polymarket_data_struct()
            if data:
                # --- THE HARD WAY: BINARY DEATH ---
                if latest_market_data and data['slug'] != latest_market_data['slug']:
                    print(f"💀 MARKET ENDED: {latest_market_data['slug']}")
                    
                    # 1. Determine Winner (Based on LAST KNOWN PRICE)
                    # No guessing. If YES was higher, YES wins.
                    last_price_yes = latest_market_data['prices'].get('Up', 0)
                    last_price_no = latest_market_data['prices'].get('Down', 0)
                    
                    winner = "NONE"
                    if last_price_yes > last_price_no: winner = "YES"
                    elif last_price_no > last_price_yes: winner = "NO"
                    
                    print(f"⚖️  VERDICT: {winner} WINS (YES: {last_price_yes}, NO: {last_price_no})")

                    # 2. BINARY PAYOUT (Winner takes $1.00, Loser takes $0.00)
                    payout = 0.0
                    
                    if winner == "YES":
                        payout = sim.qty_yes * 1.00
                        print(f"   - YES Holdings: {sim.qty_yes} shares -> ${payout:.2f}")
                        print(f"   - NO Holdings:  {sim.qty_no} shares -> $0.00 (BURNED)")
                        
                    elif winner == "NO":
                        payout = sim.qty_no * 1.00
                        print(f"   - NO Holdings:  {sim.qty_no} shares -> ${payout:.2f}")
                        print(f"   - YES Holdings: {sim.qty_yes} shares -> $0.00 (BURNED)")
                    
                    # 3. Update Balance
                    GLOBAL_BALANCE = sim.cash_balance + payout
                    print(f"🩸 New Global Balance: ${GLOBAL_BALANCE:.2f}")

                    # 4. Immediate Restart (No Pausing)
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
    # Manual reset uses equity check to be nice, but hourly reset is brutal.
    GLOBAL_BALANCE = sim.total_equity 
    sim = StrategySimulator(starting_balance=GLOBAL_BALANCE)
    return {"message": "Simulation reset", "new_balance": GLOBAL_BALANCE}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
