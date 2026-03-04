import numpy as np
import pandas as pd

class UserStrategy:
    def __init__(self, n_assets):
        self.cash = 100_000.0
        self.positions = {f"STK_{i:03d}": 0 for i in range(n_assets)} 
        self.name = "Minute_MACD_Scalper"
        
        # PARAMETERS FOR 1-MINUTE DATA
        self.fast_period = 12    # Fast moving average (12 mins)
        self.slow_period = 26    # Slow moving average (26 mins)
        self.signal_period = 9   # Signal line smoothing (9 mins)
        
        self.trade_size = 500    # Larger size for scalping (small moves)

    def on_data(self, book, history, volatility, step_index, ticker):
        """
        MACD Momentum Logic
        """
        # 1. Warmup: We need at least 35 mins of data for MACD
        if len(history) < 35:
            return 0
            
        # 2. Calculate EMAs (Exponential Moving Averages)
        # We slice the last 35 prices to keep calculation fast
        prices = history[-35:]
        
        # Helper function to calculate EMA
        def calc_ema(values, span):
            return pd.Series(values).ewm(span=span, adjust=False).mean().values

        ema_fast = calc_ema(prices, self.fast_period)
        ema_slow = calc_ema(prices, self.slow_period)
        
        # 3. Calculate MACD Line and Signal Line
        macd_line = ema_fast - ema_slow
        signal_line = calc_ema(macd_line, self.signal_period)
        
        # We only care about the very last values (Current Minute)
        current_macd = macd_line[-1]
        current_signal = signal_line[-1]
        
        # Previous minute (to detect the "Crossover")
        prev_macd = macd_line[-2]
        prev_signal = signal_line[-2]
        
        # 4. TRADING LOGIC (Crossover Strategy)
        current_pos = self.positions[ticker]
        target_pos = current_pos 

        # BULLISH CROSSOVER: MACD crosses ABOVE Signal Line
        # This means upside momentum is accelerating -> BUY
        if prev_macd < prev_signal and current_macd > current_signal:
            target_pos = self.trade_size # Go Long

        # BEARISH CROSSOVER: MACD crosses BELOW Signal Line
        # This means downside momentum is accelerating -> SELL
        elif prev_macd > prev_signal and current_macd < current_signal:
            target_pos = -self.trade_size # Go Short

        # 5. Execute
        trade_qty = int(target_pos - current_pos)
        return trade_qty