# my_strategy.py
import numpy as np

# replace this with your own strategy logic

class UserStrategy:
    def __init__(self):
        self.cash = 100_000.0  # Starting Cash
        self.position = 0      # Current shares held
        self.name = "My_Trend_Bot"

    def on_data(self, book, history, volatility, step_index):
        """
        Called every time step.
        Input:
            book: The OrderBook object (has .bid, .ask, .mid_price)
            history: Numpy array of past prices for this asset
            volatility: Current market volatility
            step_index: Current simulation step (t)
        Output:
            Signed Integer (Order Size)
        """
        # 1. Warmup Period: Don't trade if we don't have enough data
        if len(history) < 50:
            return 0
            
        # 2. Calculate Indicators
        # Simple Moving Average Crossover
        sma_fast = np.mean(history[-10:])
        sma_slow = np.mean(history[-50:])
        
        # 3. Decision Logic
        target_position = 0
        
        # If Fast > Slow, we want to be Long
        if sma_fast > sma_slow:
            target_position = 500
        # If Fast < Slow, we want to be Short
        elif sma_fast < sma_slow:
            target_position = -500
            
        # 4. Calculate Trade Size needed to reach target
        trade_size = target_position - self.position
        
        return int(trade_size)