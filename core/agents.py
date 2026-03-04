import numpy as np
import core.config as config

class Agent:
    def __init__(self, strategy_name):
        self.strategy = strategy_name
        self.position = 0 
        
    def decide(self, book, history, vol, panic, step_index): # <--- Correctly accepts step_index
        # SAFEGUARD: Don't trade if it's not my turn
        # This uses the variable from your config.py
        if step_index % config.AGENT_PATIENCE != 0:
            return 0 
        
        signal = 0
        
        # --- PANIC OVERRIDE ---
        if panic > 0.4:
            # Trend followers panic sell, Institutions step aside
            if self.strategy == 'Trend': return -200 
            if self.strategy == 'Noise': return np.random.choice([-50, 50])
            if self.strategy == 'Institutional': return 0 
            
        # --- NORMAL STRATEGIES ---
        current_price = book.mid_price
        # Safety check: Ensure enough history exists
        if len(history) < 20: return 0

        ma_short = np.mean(history[-5:])
        ma_long = np.mean(history[-20:])
        
        if self.strategy == 'Trend':
            if ma_short > ma_long: signal = 1
            else: signal = -1
            
        elif self.strategy == 'MeanRev':
            std = np.std(history[-20:])
            # Z-Score Reversion
            z_score = (current_price - ma_long) / (std + 1e-5)
            if z_score > 2: signal = -1   # Sell Overbought
            elif z_score < -2: signal = 1 # Buy Oversold
            
        elif self.strategy == 'Institutional':
            # Risk Control: Reduce size if vol is high
            if vol > 0.03 and abs(self.position) > 0:
                signal = -1 if self.position > 0 else 1 # Liquidate
            else:
                signal = 1.0 # Accumulate standard size (100 shares)
        
        elif self.strategy == 'Noise':
            signal = np.random.normal(0, 1)

        return int(100 * signal) # Ensure integer share count