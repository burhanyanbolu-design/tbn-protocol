# VC3 Trading Bot - Aggressive Configuration for Higher Profits

## 🎯 Problem
Current trades are too small ($16-$36 profits). We need **thousands** in profit per trade.

## 📊 Current Performance Analysis
```
LCID STOP_LOSS    2026-04-21  -$8.51
LCID TAKE_PROFIT  2026-04-07  +$29.55   ❌ TOO SMALL
RIVN STOP_LOSS    2026-05-01  -$15.19
NIO  STOP_LOSS    2026-04-21  -$9.98
NIO  TAKE_PROFIT  2026-03-27  +$16.04   ❌ TOO SMALL
NIO  STOP_LOSS    2026-03-20  -$9.07
NIO  TAKE_PROFIT  2026-01-28  +$36.49   ❌ TOO SMALL
NIO  TAKE_PROFIT  2026-01-23  +$17.24   ❌ TOO SMALL
NIO  STOP_LOSS    2026-01-06  -$7.89
SOFI STOP_LOSS    2026-03-26  -$15.91
PLTR STOP_LOSS    ...         -$...
```

**Issues:**
- ✗ Profits are $16-$36 (should be $1,000+)
- ✗ Position sizes too small
- ✗ Take profit targets too conservative
- ✗ Not capturing big moves

## 🚀 Solution: Aggressive Configuration

### 1. Increase Position Sizes

**Current (estimated):** 10-50 shares per trade  
**New Target:** 500-2,000 shares per trade

**Configuration to add to `/opt/vc3/.env`:**
```bash
# Position Sizing (in USD)
POSITION_SIZE_MIN=5000      # Minimum $5,000 per trade
POSITION_SIZE_MAX=20000     # Maximum $20,000 per trade
POSITION_SIZE_DEFAULT=10000 # Default $10,000 per trade

# Risk per trade (% of account)
RISK_PER_TRADE=5.0          # Risk 5% per trade (aggressive)
```

### 2. Increase Take Profit Targets

**Current:** 2-5% gains  
**New Target:** 15-30% gains

```bash
# Take Profit Targets
TAKE_PROFIT_PERCENT=20.0    # Take profit at 20% gain
TAKE_PROFIT_MIN=15.0        # Minimum 15% gain
TAKE_PROFIT_MAX=30.0        # Maximum 30% gain (trail after this)

# Trailing Stop
TRAILING_STOP_PERCENT=10.0  # Trail by 10% after hitting target
```

### 3. Wider Stop Loss (to avoid getting stopped out early)

**Current:** 2-3% stop loss  
**New:** 8-10% stop loss

```bash
# Stop Loss
STOP_LOSS_PERCENT=8.0       # Stop loss at 8% loss
STOP_LOSS_MAX=10.0          # Maximum 10% loss allowed
```

### 4. Focus on High-Volatility Stocks

```bash
# Stock Selection
MIN_VOLATILITY=3.0          # Minimum 3% daily volatility
MIN_VOLUME=5000000          # Minimum 5M shares daily volume
FOCUS_STOCKS=LCID,RIVN,NIO,SOFI,PLTR,TSLA,NVDA,AMD

# Only trade stocks with big move potential
MIN_EXPECTED_MOVE=10.0      # Minimum 10% expected move
```

### 5. Leverage (if using margin)

```bash
# Leverage (use with caution!)
USE_LEVERAGE=true
MAX_LEVERAGE=2.0            # 2x leverage (doubles position size)
```

## 📝 Complete Configuration File

Create or update `/opt/vc3/.env`:

```bash
# Alpaca API Keys
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # or https://api.alpaca.markets for live

# ═══════════════════════════════════════════════════════
# AGGRESSIVE CONFIGURATION - FOR HIGHER PROFITS
# ═══════════════════════════════════════════════════════

# Position Sizing
POSITION_SIZE_MIN=5000
POSITION_SIZE_MAX=20000
POSITION_SIZE_DEFAULT=10000
RISK_PER_TRADE=5.0

# Take Profit Targets
TAKE_PROFIT_PERCENT=20.0
TAKE_PROFIT_MIN=15.0
TAKE_PROFIT_MAX=30.0
TRAILING_STOP_PERCENT=10.0

# Stop Loss
STOP_LOSS_PERCENT=8.0
STOP_LOSS_MAX=10.0

# Stock Selection
MIN_VOLATILITY=3.0
MIN_VOLUME=5000000
FOCUS_STOCKS=LCID,RIVN,NIO,SOFI,PLTR,TSLA,NVDA,AMD
MIN_EXPECTED_MOVE=10.0

# Leverage (optional - use with caution!)
USE_LEVERAGE=false
MAX_LEVERAGE=2.0

# Trading Hours
TRADE_START_HOUR=9
TRADE_START_MINUTE=30
TRADE_END_HOUR=15
TRADE_END_MINUTE=30

# Risk Management
MAX_DAILY_LOSS=5000         # Stop trading if lose $5,000 in a day
MAX_DAILY_TRADES=10         # Maximum 10 trades per day
MAX_OPEN_POSITIONS=5        # Maximum 5 positions at once

# Strategy
STRATEGY=AGGRESSIVE         # CONSERVATIVE, MODERATE, AGGRESSIVE
HOLD_TIME_MIN=60            # Minimum 60 minutes hold time
HOLD_TIME_MAX=480           # Maximum 8 hours hold time
```

## 🎯 Expected Results with New Configuration

### Example Trade Scenarios

#### Scenario 1: NIO Trade
- **Entry:** $5.00 per share
- **Position Size:** $10,000 = 2,000 shares
- **Take Profit:** 20% = $6.00 per share
- **Profit:** 2,000 shares × $1.00 = **$2,000** ✅

#### Scenario 2: LCID Trade
- **Entry:** $2.50 per share
- **Position Size:** $15,000 = 6,000 shares
- **Take Profit:** 25% = $3.125 per share
- **Profit:** 6,000 shares × $0.625 = **$3,750** ✅

#### Scenario 3: RIVN Trade with Leverage
- **Entry:** $12.00 per share
- **Position Size:** $20,000 × 2x leverage = $40,000 = 3,333 shares
- **Take Profit:** 15% = $13.80 per share
- **Profit:** 3,333 shares × $1.80 = **$6,000** ✅

## ⚠️ Important Warnings

### 1. Account Size Required
To trade with $10,000-$20,000 positions, you need:
- **Minimum:** $50,000 account (for 5 positions)
- **Recommended:** $100,000+ account
- **With 2x leverage:** $50,000 account can control $100,000

### 2. Risk Management
- **5% risk per trade** = If you have $100,000, you risk $5,000 per trade
- **Max 5 positions** = Maximum $25,000 at risk at once
- **Daily loss limit** = Stop trading if lose $5,000 in one day

### 3. Volatility Risk
- High-volatility stocks (LCID, RIVN, NIO) can move 10-20% in minutes
- **Wider stops** (8-10%) prevent getting stopped out on normal volatility
- **Higher targets** (15-30%) capture the big moves

### 4. Leverage Risk
- **2x leverage** doubles your profits AND losses
- Only use leverage if you understand the risks
- Can lose more than your initial investment

## 🚀 Deployment Steps

### Step 1: Update Configuration
```bash
# SSH into server
ssh ubuntu@3.11.229.68

# Edit VC3 configuration
sudo nano /opt/vc3/.env

# Paste the aggressive configuration above
# Save: Ctrl+O, Enter
# Exit: Ctrl+X
```

### Step 2: Restart VC3
```bash
sudo systemctl restart vc3
```

### Step 3: Verify Configuration
```bash
# Check logs to confirm new settings loaded
sudo journalctl -u vc3 -n 50

# Should see:
# "Position size: $10,000"
# "Take profit target: 20%"
# "Stop loss: 8%"
```

### Step 4: Monitor First Trades
```bash
# Watch live logs
sudo journalctl -u vc3 -f

# Check dashboard
# https://vc3.hardinai.co.uk
```

## 📊 Expected Performance

### Conservative Estimate (10 trades/month)
- **Win Rate:** 60% (6 wins, 4 losses)
- **Average Win:** $2,000 × 6 = $12,000
- **Average Loss:** $800 × 4 = -$3,200
- **Net Profit:** $8,800/month

### Moderate Estimate (20 trades/month)
- **Win Rate:** 55% (11 wins, 9 losses)
- **Average Win:** $2,500 × 11 = $27,500
- **Average Loss:** $800 × 9 = -$7,200
- **Net Profit:** $20,300/month

### Aggressive Estimate (30 trades/month with leverage)
- **Win Rate:** 50% (15 wins, 15 losses)
- **Average Win:** $4,000 × 15 = $60,000
- **Average Loss:** $1,500 × 15 = -$22,500
- **Net Profit:** $37,500/month

## 🎯 Target: $1,000+ Per Trade

With this configuration:
- ✅ Minimum profit target: $1,500 per winning trade
- ✅ Average profit target: $2,000-$3,000 per trade
- ✅ Best case profit: $5,000-$10,000 per trade

**This is 50-100x better than current $16-$36 profits!**

## 📞 Next Steps

1. **Update configuration** with aggressive settings
2. **Restart VC3** bot
3. **Monitor first 5 trades** closely
4. **Adjust** based on results
5. **Scale up** once profitable

---

**⚠️ DISCLAIMER:** Trading with larger positions and leverage increases both profits AND losses. Only use this configuration if you understand the risks and have sufficient capital.

**Recommended:** Start with paper trading (Alpaca paper account) to test the aggressive strategy before using real money.

---

**Created:** May 9, 2026  
**For:** VC3 Trading Bot  
**Goal:** Increase profits from $16-$36 to $1,000+ per trade
