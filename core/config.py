# config.py

# ==========================================
# 1. TIME RESOLUTION SETTINGS
# ==========================================
# UNCOMMENT ONE BLOCK BELOW TO CHOOSE TIMEFRAME

# --- OPTION A: DAILY DATA (Swing Trading / Macro) ---
TIMEFRAME = "1D"
STEPS_PER_DAY = 1
TRADING_DAYS = 252  # 1 Year
# ----------------------------------------------------

# --- OPTION B: HOURLY DATA (Swing / Intra-Day) ---
# TIMEFRAME = "1h"
# STEPS_PER_DAY = 7   # 7 bars per day (9:30-4:00)
# TRADING_DAYS = 252  # 1 Year (~1,764 total steps)
# -------------------------------------------------

# --- OPTION C: MINUTE DATA (Day Trading) ---
# TIMEFRAME = "1m"
# STEPS_PER_DAY = 390 # 6.5 hours * 60 mins
# TRADING_DAYS = 252  # 1 Year (~98,000 total steps)
# -------------------------------------------------

# --- OPTION D: SECOND DATA (HFT / Market Making) ---
# TIMEFRAME = "1s"
# STEPS_PER_DAY = 23400 # 6.5 hours * 3600 secs
# TRADING_DAYS = 5      # SAFETY LIMIT: Keep short to avoid RAM explosion (580M+ rows)
# ---------------------------------------------------

# AUTOMATIC CALCULATIONS (DO NOT TOUCH)
N_STEPS = TRADING_DAYS * STEPS_PER_DAY
# Scale DT so that volatility (sigma * sqrt(DT)) is correct for the timeframe
DT = 1 / (252 * STEPS_PER_DAY) 

# ==========================================
# 2. MARKET PHYSICS (HESTON MODEL)
# ==========================================
N_ASSETS = 100          
INITIAL_PRICE = 100.0

# These parameters are time-independent!
# The math engine scales them automatically using sqrt(DT).
MEAN_REVERSION_SPEED = 4.0  
LONG_TERM_VARIANCE = 0.04   
VOL_OF_VOL = 0.7            
INITIAL_VARIANCE = 0.04     

# ==========================================
# 3. MICROSTRUCTURE & LIQUIDITY
# ==========================================
# Base spread in basis points (0.0005 = 5 bps)
BASE_SPREAD = 0.0005    

# IMPACT SCALING:
# As time steps get smaller, liquidity per step gets thinner.
# We scale impact to prevent "infinite liquidity" artifacts on small timeframes.
if TIMEFRAME == "1s":
    PRICE_IMPACT_FACTOR = 0.0005 * 10 # High impact per share (Thin book)
elif TIMEFRAME == "1m":
    PRICE_IMPACT_FACTOR = 0.0005 * 2  # Moderate impact
elif TIMEFRAME == "1h":
    PRICE_IMPACT_FACTOR = 0.0005 * 1.5 # Slightly higher than daily
else:
    PRICE_IMPACT_FACTOR = 0.0005      # Standard Daily impact

BASE_LIQUIDITY = 10000 

# ==========================================
# 4. BLACK SWAN EVENTS & SAFEGUARDS
# ==========================================
# SAFETY INTERLOCK: Disable Black Swans for High-Frequency (1s) data
# to prevent "Flash Crash" artifacts where panic decays in seconds.

if TIMEFRAME == "1s":
    ENABLE_BLACK_SWANS = False
    SWAN_PROBABILITY = 0.0
    SWAN_COOLDOWN = 0
    SWAN_SEVERITY = 0.0
else:
    ENABLE_BLACK_SWANS = True
    MAX_SWANS_PER_YEAR = 2  
    SWAN_SEVERITY = 0.9     
    # Scale probability so we don't crash 390x more often on minute data
    SWAN_PROBABILITY = 0.005 / STEPS_PER_DAY 
    # Scale cooldown so markets don't recover instantly
    SWAN_COOLDOWN = 60 * STEPS_PER_DAY 

# ==========================================
# 5. AGENT POPULATION & BEHAVIOR
# ==========================================
N_TREND_FOLLOWERS = 40
N_MEAN_REVERTERS = 30
N_INSTITUTIONAL = 10
N_NOISE_TRADERS = 20

# AGENT PATIENCE (New Safeguard)
# Prevents agents from over-trading on high-frequency data.
# 1 = Trade every step. 60 = Trade once every 60 steps.
if TIMEFRAME == "1s":
    AGENT_PATIENCE = 60 # Trade once a minute, not every second
elif TIMEFRAME == "1m":
    AGENT_PATIENCE = 5  # Trade every 5 minutes
else:
    AGENT_PATIENCE = 1  # Trade every step (Daily/Hourly)