# main.py
# ACTIVE MODE: Multi-Asset Edition with Progress Bar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm 
import core.config as config
from core.physics import MarketPhysics
from core.market import OrderBook
from core.agents import Agent
from my_strategy import UserStrategy

def run_active_simulation():
    print(f"--- INITIALIZING MULTI-ASSET SIMULATION ---")
    print(f"Timeframe: {config.TIMEFRAME} | Total Steps: {config.N_STEPS}")
    print(f"Trading: ALL {config.N_ASSETS} ASSETS")
    
    # 1. Init Physics
    physics = MarketPhysics()
    vol_path = physics.get_volatility_path()
    
    # 2. Init Assets
    books = [OrderBook() for _ in range(config.N_ASSETS)]
    
    # 3. Init Agents (UNIQUE POPULATION PER ASSET)
    # We create a list of lists so that the agents trading Asset 0 are distinct
    # from those trading Asset 1. This prevents position state contamination.
    all_asset_agents = []
    for _ in range(config.N_ASSETS):
        local_agents = []
        for _ in range(config.N_TREND_FOLLOWERS): local_agents.append(Agent('Trend'))
        for _ in range(config.N_MEAN_REVERTERS): local_agents.append(Agent('MeanRev'))
        for _ in range(config.N_INSTITUTIONAL): local_agents.append(Agent('Institutional'))
        for _ in range(config.N_NOISE_TRADERS): local_agents.append(Agent('Noise'))
        all_asset_agents.append(local_agents)

    # 4. Init Strategy
    # Pass N_ASSETS so the strategy can build a portfolio dictionary
    my_algo = UserStrategy(config.N_ASSETS)
    my_pnl_history = []
    
    # 5. Storage
    price_history = np.zeros((config.N_STEPS, config.N_ASSETS))
    for i in range(config.N_ASSETS): 
        price_history[0, i] = config.INITIAL_PRICE
        books[i].mid_price = config.INITIAL_PRICE
    
    # --- SIMULATION LOOP ---
    panic_factor = 0.0
    swans_triggered = 0
    swan_cooldown = 0
    
    print("--- STARTING LIVE TRADING LOOP ---")
    
    # WRAP RANGE WITH TQDM FOR PROGRESS BAR
    for t in tqdm(range(1, config.N_STEPS), desc="Simulating Market", unit="step"):
        current_vol = vol_path[t] if t < len(vol_path) else vol_path[-1]
        
        # --- BLACK SWAN LOGIC ---
        panic_factor *= 0.92
        if swan_cooldown > 0: swan_cooldown -= 1
        
        if config.ENABLE_BLACK_SWANS:
            if (swans_triggered < config.MAX_SWANS_PER_YEAR and 
                swan_cooldown == 0 and 
                np.random.rand() < config.SWAN_PROBABILITY):
                # Use tqdm.write to avoid breaking the progress bar
                tqdm.write(f"[!] BLACK SWAN EVENT at Step {t}")
                panic_factor = config.SWAN_SEVERITY
                swans_triggered += 1
                swan_cooldown = config.SWAN_COOLDOWN

        # Generate Physics Shocks (Correlated)
        shocks = physics.L @ np.random.normal(0, 1, config.N_ASSETS)
        
        # Track Total Portfolio Value for this step
        # Start with Cash, then add value of all stock holdings
        step_equity_value = 0 
        
        # --- ASSET LOOP ---
        for i in range(config.N_ASSETS):
            ticker = f"STK_{i:03d}"
            book = books[i]
            
            # A. Update Market Physics
            book.update_quotes(current_vol, panic_factor)
            drift = 0.0001
            if panic_factor > 0.1: drift -= (panic_factor * 0.08)
            fund_return = drift + (current_vol * np.sqrt(config.DT) * shocks[i])
            book.mid_price *= np.exp(fund_return)
            
            # B. Gather History
            asset_hist = price_history[:t, i]
            
            # C. Internal Agents (Use the specific population for this asset)
            net_flow = 0
            current_agents = all_asset_agents[i] # <--- Retrieve specific agents
            
            for agent in current_agents:
                qty = agent.decide(book, asset_hist, current_vol, panic_factor, t)
                net_flow += qty
            
            # --- D. INJECT YOUR STRATEGY ---
            # Strategy decides for THIS specific asset 'i'
            user_trade_size = my_algo.on_data(book, asset_hist, current_vol, t, ticker)
            net_flow += user_trade_size 
            
            # E. Execute
            exec_price = book.execute(net_flow)
            price_history[t, i] = exec_price
            
            # F. Mark-to-Market
            if user_trade_size != 0:
                fill_price = book.ask if user_trade_size > 0 else book.bid
                my_algo.positions[ticker] += user_trade_size
                my_algo.cash -= (user_trade_size * fill_price)
            
            # Calculate value of this position for total equity report
            step_equity_value += (my_algo.positions[ticker] * exec_price)

        # End of Step: Record Total Equity (Cash + All Stock Value)
        total_account_value = my_algo.cash + step_equity_value
        
        my_pnl_history.append({
            'Step': t,
            'Cash': my_algo.cash,
            'Equity': total_account_value
        })

    # --- RESULTS & PLOTTING ---
    print("--- Simulation Complete ---")
    df_res = pd.DataFrame(my_pnl_history)
    df_res.to_csv('my_performance.csv', index=False)
    
    final_eq = df_res.iloc[-1]['Equity']
    print(f"Final Equity: ${final_eq:,.2f}")
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(df_res['Step'], df_res['Equity'], label='Total Portfolio Value', color='blue')
    plt.title(f'Multi-Asset Strategy Performance ({config.TIMEFRAME})')
    plt.ylabel('Equity ($)')
    plt.xlabel('Step')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('performance_chart.png')
    print("Saved plot to 'performance_chart.png'")
    plt.show()

if __name__ == "__main__":
    run_active_simulation()