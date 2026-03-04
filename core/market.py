# market.py, order book, spreads, execution, liquidity, panic factor, volatility, price impact
import core.config as config

class OrderBook:
    def __init__(self, start_price=config.INITIAL_PRICE):
        self.mid_price = start_price
        self.bid = start_price * (1 - config.BASE_SPREAD/2)
        self.ask = start_price * (1 + config.BASE_SPREAD/2)
        self.liquidity = config.BASE_LIQUIDITY
        
    def update_quotes(self, volatility, panic_factor):
        """Dynamic Spreads based on Volatility and Panic."""
        # 1. Volatility Impact
        vol_impact = 1 + (volatility * 20)
        
        # 2. Panic Impact (Exponential widening)
        panic_impact = 1 + (panic_factor * 10) 
        
        # Calculate new spread
        current_spread = self.mid_price * config.BASE_SPREAD * vol_impact * panic_impact
        
        self.bid = self.mid_price - (current_spread / 2)
        self.ask = self.mid_price + (current_spread / 2)
        
        # Liquidity Vacuum: Depth shrinks during panic
        self.liquidity = config.BASE_LIQUIDITY / (1 + panic_factor * 20)

    def execute(self, net_order_flow):
        """Executes order flow and returns the Close price."""
        # Price Impact (Kyle's Lambda)
        impact = (net_order_flow / self.liquidity) * (self.mid_price * config.PRICE_IMPACT_FACTOR)
        self.mid_price += impact
        
        # Determine execution side
        if net_order_flow > 0: return self.ask
        else: return self.bid