# my_strategy.py
import numpy as np

class UserStrategy:
    def __init__(self, n_assets):
        self.cash = 100_000.0  # Starting Cash
        # Now a dictionary to track position for EACH asset
        # Format: { 'STK_000': 0, 'STK_001': 0, ... }
        self.positions = {f"STK_{i:03d}": 0 for i in range(n_assets)} 
        self.name = "Multi_Asset_Trend_Bot"

    def on_data(self, book, history, volatility, step_index, ticker):
        """
        Called for EVERY asset, EVERY time step.
        Input:
            ticker: The name of the asset being traded (e.g. "STK_000")
        """
        # 1. Warmup: Need enough history
        if len(history) < 50:
            return 0
            
        # 2. Strategy Logic (Example: Trend Following)
        sma_fast = np.mean(history[-10:])
        sma_slow = np.mean(history[-50:])
        
        current_pos = self.positions[ticker]
        target_pos = 0
        
        # Trend Logic:
        # If Fast > Slow, buy 100 shares. If Fast < Slow, sell/short 100.
        if sma_fast > sma_slow:
            target_pos = 100
        elif sma_fast < sma_slow:
            target_pos = -100
            
        # 3. Calculate Trade to reach target
        trade_size = target_pos - current_pos
        
        return int(trade_size)