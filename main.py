# main.py
# ACTIVE MODE: Core Folder Edition + Dual Plots

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm 

# --- NEW IMPORTS FOR 'CORE' FOLDER ---
import core.config as config
from core.physics import MarketPhysics
from core.market import OrderBook
from core.agents import Agent

from sample_strategies.my_strategy import UserStrategy

def run_active_simulation():
    print(f"--- INITIALIZING MULTI-ASSET SIMULATION ---")
    print(f"Timeframe: {config.TIMEFRAME} | Total Steps: {config.N_STEPS}")
    print(f"Trading: ALL {config.N_ASSETS} ASSETS")
    
    # 1. Init Physics
    physics = MarketPhysics()
    vol_path = physics.get_volatility_path()
    
    # 2. Init Assets
    books = [OrderBook() for _ in range(config.N_ASSETS)]
    
    # 3. Init Agents (Unique Population per Asset)
    all_asset_agents = []
    for _ in range(config.N_ASSETS):
        local_agents = []
        for _ in range(config.N_TREND_FOLLOWERS): local_agents.append(Agent('Trend'))
        for _ in range(config.N_MEAN_REVERTERS): local_agents.append(Agent('MeanRev'))
        for _ in range(config.N_INSTITUTIONAL): local_agents.append(Agent('Institutional'))
        for _ in range(config.N_NOISE_TRADERS): local_agents.append(Agent('Noise'))
        all_asset_agents.append(local_agents)

    # 4. Init Strategy
    my_algo = UserStrategy(config.N_ASSETS)
    my_pnl_history = []
    
    # 5. Storage (Track prices for ALL assets)
    price_history = np.zeros((config.N_STEPS, config.N_ASSETS))
    
    warmup_noise = np.random.normal(0, 0.5, (config.N_ASSETS)) # 50 cent variance
    
    for i in range(config.N_ASSETS): 
        # Set the starting point to slightly random values (99.5 to 100.5)
        # to ensure StdDev is not zero
        start_price = config.INITIAL_PRICE + warmup_noise[i]
        price_history[0, i] = start_price
        books[i].mid_price = start_price
    
    # --- SIMULATION LOOP ---
    panic_factor = 0.0
    swans_triggered = 0
    swan_cooldown = 0
    
    print("--- STARTING LIVE TRADING LOOP ---")

    # TQDM Progress Bar
    for t in tqdm(range(1, config.N_STEPS), desc="Simulating Market", unit="step"):
        current_vol = vol_path[t] if t < len(vol_path) else vol_path[-1]
        
        # Black Swan Logic
        panic_factor *= 0.92
        if swan_cooldown > 0: swan_cooldown -= 1
        
        if config.ENABLE_BLACK_SWANS:
            if (swans_triggered < config.MAX_SWANS_PER_YEAR and 
                swan_cooldown == 0 and 
                np.random.rand() < config.SWAN_PROBABILITY):
                tqdm.write(f"[!] BLACK SWAN EVENT at Step {t}")
                panic_factor = config.SWAN_SEVERITY
                swans_triggered += 1
                swan_cooldown = config.SWAN_COOLDOWN

        # Generate Correlated Shocks
        shocks = physics.L @ np.random.normal(0, 1, config.N_ASSETS)
        
        step_equity_value = 0 
        
        # --- ASSET LOOP ---
        for i in range(config.N_ASSETS):
            ticker = f"STK_{i:03d}"
            book = books[i]
            
            # Update Market Physics
            book.update_quotes(current_vol, panic_factor)
            drift = 0.0001
            if panic_factor > 0.1: drift -= (panic_factor * 0.08)
            fund_return = drift + (current_vol * np.sqrt(config.DT) * shocks[i])
            book.mid_price *= np.exp(fund_return)
            
            # Gather History
            asset_hist = price_history[:t, i]
            
            # Internal Agents
            net_flow = 0
            current_agents = all_asset_agents[i]
            for agent in current_agents:
                qty = agent.decide(book, asset_hist, current_vol, panic_factor, t)
                net_flow += qty
            
            # INJECT YOUR STRATEGY
            user_trade_size = my_algo.on_data(book, asset_hist, current_vol, t, ticker)
            net_flow += user_trade_size 
            
            # Execute
            exec_price = book.execute(net_flow)
            price_history[t, i] = exec_price
            
            # Mark-to-Market
            if user_trade_size != 0:
                fill_price = book.ask if user_trade_size > 0 else book.bid
                my_algo.positions[ticker] += user_trade_size
                my_algo.cash -= (user_trade_size * fill_price)
            
            step_equity_value += (my_algo.positions[ticker] * exec_price)

        # Record Total Equity
        total_account_value = my_algo.cash + step_equity_value
        my_pnl_history.append({
            'Step': t,
            'Cash': my_algo.cash,
            'Equity': total_account_value
        })

    # --- VISUALIZATION DASHBOARD ---
    print("\n--- Simulation Complete. Generating Dashboard... ---")
    df_res = pd.DataFrame(my_pnl_history)
    df_res.to_csv('my_performance.csv', index=False)
    
    # Calculate Equal-Weighted Market Index (Average of all stocks)
    market_index = np.mean(price_history[:config.N_STEPS], axis=1)
    
    # Create Dual-Axis Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    # Plot 1: My Strategy
    ax1.plot(df_res['Step'], df_res['Equity'], color='#2ca02c', linewidth=1.5, label='My Portfolio Equity')
    ax1.set_title(f'Strategy Performance ({config.TIMEFRAME})', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Total Equity ($)', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='upper left')

    # Plot 2: Simulated Market
    ax2.plot(range(config.N_STEPS), market_index, color='#1f77b4', linewidth=1.5, label='Market Index (Avg Price)')
    # Add faint lines for individual assets to show dispersion
    for i in range(min(5, config.N_ASSETS)): 
        ax2.plot(range(config.N_STEPS), price_history[:config.N_STEPS, i], color='gray', alpha=0.2, linewidth=0.5)
    
    ax2.set_title('Simulated Market Overview', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Asset Price ($)', fontsize=12)
    ax2.set_xlabel('Simulation Step', fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(loc='upper left')

    plt.tight_layout()
    plt.savefig('performance_dashboard.png')
    print(f"Saved dashboard to 'performance_dashboard.png'")
    print(f"Final Equity: ${df_res.iloc[-1]['Equity']:,.2f}")
    plt.show()

if __name__ == "__main__":
    run_active_simulation()