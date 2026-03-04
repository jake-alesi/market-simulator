import numpy as np

class UserStrategy:
    def __init__(self, n_assets):
        self.cash = 100_000.0
        self.positions = {f"STK_{i:03d}": 0 for i in range(n_assets)} 
        self.name = "Hourly_Bollinger_Reversion"
        
        # PARAMETERS FOR HOURLY DATA
        # 20 Hours = Approx 3 Trading Days of data (if 7 hours/day)
        self.lookback = 20       
        self.std_devs = 2.0      # The "width" of the bands
        self.trade_size = 100    # Shares to trade per signal

    def on_data(self, book, history, volatility, step_index, ticker):
        """
        Hourly Mean Reversion Logic
        """
        # 1. Warmup: We need 20 hours of data before we can calculate Bands
        if len(history) < self.lookback:
            return 0
            
        # 2. Calculate Indicators (Bollinger Bands)
        # Slice the last 20 hours of prices
        recent_prices = history[-self.lookback:]
        
        sma = np.mean(recent_prices)           # Middle Band (Fair Value)
        std = np.std(recent_prices)            # Volatility
        
        upper_band = sma + (self.std_devs * std)
        lower_band = sma - (self.std_devs * std)
        
        current_price = history[-1]
        current_pos = self.positions[ticker]
        target_pos = current_pos # Default: Hold current position
        
        # 3. TRADING LOGIC
        
        # CASE A: Price is CHEAP (Below Lower Band) -> BUY
        if current_price < lower_band:
            # We want to be Long (Buy the dip)
            target_pos = self.trade_size
            
        # CASE B: Price is EXPENSIVE (Above Upper Band) -> SHORT
        elif current_price > upper_band:
            # We want to be Short (Sell the rip)
            target_pos = -self.trade_size
            
        # CASE C: Price returned to NORMAL (Crossed SMA) -> EXIT
        # If we are Long and price went back up to SMA, take profit
        elif current_pos > 0 and current_price >= sma:
            target_pos = 0
            
        # If we are Short and price went back down to SMA, take profit
        elif current_pos < 0 and current_price <= sma:
            target_pos = 0
            
        # 4. Calculate Trade Size
        trade_qty = int(target_pos - current_pos)
        
        return trade_qty