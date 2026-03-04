import numpy as np

class UserStrategy:
    def __init__(self, n_assets):
        self.cash = 100_000.0
        self.positions = {f"STK_{i:03d}": 0 for i in range(n_assets)} 
        self.name = "Zero_Beta_Long_Short"
        
        # MEMORY: Store the momentum score of every asset
        # We need this to "Rank" Asset A against Asset B
        self.scores = np.zeros(n_assets)
        
        # SETTINGS
        self.lookback = 20        # Calculate return over last 20 steps
        self.rebalance_freq = 5   # Only trade every 5 steps (to save costs)
        self.percentile = 15      # Top/Bottom 15% get traded
        self.trade_size = 200     # Shares to buy/sell

    def on_data(self, book, history, volatility, step_index, ticker):
        # 1. Warmup: We need enough history to calculate momentum
        if len(history) < self.lookback:
            return 0
            
        # 2. Extract Asset ID (e.g., "STK_042" -> 42)
        asset_id = int(ticker.split('_')[1])
        
        # 3. Calculate Momentum (Price change %)
        # "Where is price today vs 20 steps ago?"
        start_price = history[-self.lookback]
        end_price = history[-1]
        momentum = (end_price - start_price) / start_price
        
        # Store score in our memory bank
        self.scores[asset_id] = momentum
        
        # 4. TRADING LOGIC (Only runs on rebalance steps)
        if step_index % self.rebalance_freq != 0:
            return 0
            
        # --- RANKING LOGIC ---
        # Calculate the thresholds for "Top Tier" and "Bottom Tier"
        # We use the scores we collected from all assets
        score_high = np.percentile(self.scores, 100 - self.percentile) # e.g. 85th percentile
        score_low = np.percentile(self.scores, self.percentile)        # e.g. 15th percentile
        
        current_pos = self.positions[ticker]
        target_pos = 0
        
        # If this stock is a "Winner" (Top 15%) -> Go Long
        if momentum >= score_high:
            target_pos = self.trade_size
            
        # If this stock is a "Loser" (Bottom 15%) -> Go Short
        elif momentum <= score_low:
            target_pos = -self.trade_size
            
        # If it's mediocre -> Go Flat (Exit Position)
        else:
            target_pos = 0
            
        # 5. Execute Trade
        # If we have 100 and want 200, we buy 100.
        # If we have 100 and want -200, we sell 300.
        trade_qty = target_pos - current_pos
        
        return int(trade_qty)