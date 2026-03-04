# generate_data.py
# PASSIVE MODE: Generates 'market_data.csv' without user interference.
# Use this to create datasets for offline backtesting.

import numpy as np
import pandas as pd
import config
from physics import MarketPhysics
from market import OrderBook
from agents import Agent

def generate_passive_data():
    print(f"--- GENERATING PASSIVE DATASET ---")
    print(f"Timeframe: {config.TIMEFRAME} | Total Steps: {config.N_STEPS}")
    
    # 1. Init Physics
    physics = MarketPhysics()
    vol_path = physics.get_volatility_path()
    
    # 2. Init Assets
    books = [OrderBook() for _ in range(config.N_ASSETS)]
    
    # 3. Init Agents
    agents = []
    for _ in range(config.N_TREND_FOLLOWERS): agents.append(Agent('Trend'))
    for _ in range(config.N_MEAN_REVERTERS): agents.append(Agent('MeanRev'))
    for _ in range(config.N_INSTITUTIONAL): agents.append(Agent('Institutional'))
    for _ in range(config.N_NOISE_TRADERS): agents.append(Agent('Noise'))
    
    price_history = np.zeros((config.N_STEPS, config.N_ASSETS))
    for i in range(config.N_ASSETS): 
        price_history[0, i] = config.INITIAL_PRICE
        books[i].mid_price = config.INITIAL_PRICE
        
    all_data = []
    
    # Loop
    panic_factor = 0.0
    swans_triggered = 0
    swan_cooldown = 0
    
    for t in range(1, config.N_STEPS):
        current_vol = vol_path[t] if t < len(vol_path) else vol_path[-1]
        
        # Black Swan Logic
        panic_factor *= 0.92
        if swan_cooldown > 0: swan_cooldown -= 1
        
        if config.ENABLE_BLACK_SWANS:
            if (swans_triggered < config.MAX_SWANS_PER_YEAR and 
                swan_cooldown == 0 and 
                np.random.rand() < config.SWAN_PROBABILITY):
                print(f"[!] BLACK SWAN at Step {t}")
                panic_factor = config.SWAN_SEVERITY
                swans_triggered += 1
                swan_cooldown = config.SWAN_COOLDOWN
        
        # Shocks
        shocks = physics.L @ np.random.normal(0, 1, config.N_ASSETS)
        
        for i in range(config.N_ASSETS):
            book = books[i]
            book.update_quotes(current_vol, panic_factor)
            
            # Drift
            drift = 0.0001
            if panic_factor > 0.1: drift -= (panic_factor * 0.08)
            fund_return = drift + (current_vol * np.sqrt(config.DT) * shocks[i])
            book.mid_price *= np.exp(fund_return)
            
            # Agent Decisions
            asset_hist = price_history[:t, i]
            net_flow = 0
            volume = 0
            
            for agent in agents:
                qty = agent.decide(book, asset_hist, current_vol, panic_factor, t)
                net_flow += qty
                volume += abs(qty)
            
            # Execute
            close_price = book.execute(net_flow)
            price_history[t, i] = close_price
            
            # Save Data (Only saving Asset 0 to keep CSV size manageable if High Freq)
            # Remove "if i == 0:" if you want ALL assets
            if i == 0:
                all_data.append({
                    'Step': t,
                    'Ticker': f"STK_{i:03d}",
                    'Close': close_price,
                    'Volume': int(volume),
                    'Bid': book.bid,
                    'Ask': book.ask,
                    'Spread': book.ask - book.bid,
                    'Panic': panic_factor
                })
                
    # Export
    print("--- Saving CSV ---")
    df = pd.DataFrame(all_data)
    df.to_csv('market_data.csv', index=False)
    print("Saved to 'market_data.csv'")

if __name__ == "__main__":
    generate_passive_data()