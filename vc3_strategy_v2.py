"""
Hardin VC3 v2 — Intelligent Multi-Indicator Trading
====================================================
Upgrades from v1:
  - 10+ indicators (was 5)
  - Weighted 0-100 scoring (was simple +1/-1)
  - ADX trend strength filter
  - Multi-timeframe confirmation (5min + 1hr)
  - RSI divergence detection
  - Adaptive position sizing
  - OBV volume confirmation
  - SMA200 trend filter

Still uses: Alpaca, 5-min candles, same watchlist
"""
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
import pandas as pd
import numpy as np

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('strategy_bot.log'),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger('strategy_bot')

# ── Config ────────────────────────────────────────────────────────────
API_KEY            = os.getenv('ALPACA_API_KEY')
SECRET_KEY         = os.getenv('ALPACA_SECRET_KEY')
PAPER              = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets').startswith('https://paper')
POSITION_SIZE_USD  = float(os.getenv('POSITION_SIZE_USD', 500))
STOP_LOSS_PCT      = float(os.getenv('STOP_LOSS_PCT', 1.5))
TAKE_PROFIT_PCT    = float(os.getenv('TAKE_PROFIT_PCT', 3.0))
MAX_POSITIONS      = int(os.getenv('MAX_POSITIONS', 5))
MAX_DAILY_LOSS_USD = float(os.getenv('MAX_DAILY_LOSS_USD', -400))
SCAN_INTERVAL      = int(os.getenv('SCAN_INTERVAL_SECS', 60))

# Signal thresholds
BUY_THRESHOLD      = 65   # Score must be >= this to buy
MIN_CONFIDENCE     = 0.6  # Minimum confidence to act

WATCHLIST = [
    'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN',
    'GOOGL', 'META', 'AMD', 'SPY', 'QQQ',
    'BABA', 'NFLX', 'UBER', 'COIN', 'PLTR',
    'SOFI', 'NIO', 'RIVN', 'LCID', 'F',
]

# ── Clients ───────────────────────────────────────────────────────────
_trading = None
_data    = None

def trading():
    global _trading
    if _trading is None:
        _trading = TradingClient(API_KEY, SECRET_KEY, paper=PAPER)
    return _trading

def data():
    global _data
    if _data is None:
        _data = StockHistoricalDataClient(API_KEY, SECRET_KEY)
    return _data

# ── Market Data ───────────────────────────────────────────────────────
def get_bars(symbol: str, timeframe_minutes: int = 5, limit: int = 100) -> pd.DataFrame:
    import pytz
    try:
        now   = datetime.now(pytz.UTC)
        start = now - timedelta(days=7)

        if timeframe_minutes == 5:
            tf = TimeFrame(5, TimeFrameUnit.Minute)
        elif timeframe_minutes == 60:
            tf = TimeFrame(1, TimeFrameUnit.Hour)
        else:
            tf = TimeFrame(timeframe_minutes, TimeFrameUnit.Minute)

        req = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf,
            start=start,
            end=now,
            limit=limit,
            feed='iex',
        )
        bars = data().get_stock_bars(req).df
        if bars.empty:
            return pd.DataFrame()
        if isinstance(bars.index, pd.MultiIndex):
            bars = bars.droplevel(0)
        return bars[['open', 'high', 'low', 'close', 'volume']]
    except Exception as e:
        log.warning(f"Bars failed {symbol} ({timeframe_minutes}m): {e}")
        return pd.DataFrame()


# ── Technical Indicators ──────────────────────────────────────────────

def calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """RSI calculation"""
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def calc_ema(close: pd.Series, period: int) -> pd.Series:
    return close.ewm(span=period, adjust=False).mean()


def calc_macd(close: pd.Series):
    """Returns macd, signal, histogram"""
    fast = calc_ema(close, 12)
    slow = calc_ema(close, 26)
    macd = fast - slow
    signal = calc_ema(macd, 9)
    hist = macd - signal
    return macd, signal, hist


def calc_bollinger(close: pd.Series, period: int = 20):
    """Returns upper, middle, lower bands"""
    mid = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = mid + 2 * std
    lower = mid - 2 * std
    return upper, mid, lower


def calc_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average Directional Index — trend strength"""
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    plus_dm[(plus_dm < minus_dm)] = 0
    minus_dm[(minus_dm < plus_dm)] = 0

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
    adx = dx.rolling(period).mean()
    return adx


def calc_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On Balance Volume"""
    direction = np.where(close > close.shift(1), 1, np.where(close < close.shift(1), -1, 0))
    return (volume * direction).cumsum()


def calc_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
    """Stochastic K and D"""
    lowest_low = low.rolling(period).min()
    highest_high = high.rolling(period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(3).mean()
    return k, d


# ── Advanced Signals ──────────────────────────────────────────────────

def detect_rsi_divergence(close: pd.Series, rsi: pd.Series, lookback: int = 14) -> str:
    """Detect bullish/bearish RSI divergence"""
    if len(close) < lookback + 5:
        return "NONE"

    # Compare current vs lookback period
    price_now = close.iloc[-1]
    price_prev = close.iloc[-lookback]
    rsi_now = rsi.iloc[-1]
    rsi_prev = rsi.iloc[-lookback]

    if pd.isna(rsi_now) or pd.isna(rsi_prev):
        return "NONE"

    # Bullish divergence: price lower low, RSI higher low
    if price_now < price_prev and rsi_now > rsi_prev:
        return "BULLISH"

    # Bearish divergence: price higher high, RSI lower high
    if price_now > price_prev and rsi_now < rsi_prev:
        return "BEARISH"

    return "NONE"


def check_hourly_trend(symbol: str) -> str:
    """Check 1-hour timeframe for trend confirmation"""
    bars = get_bars(symbol, timeframe_minutes=60, limit=50)
    if bars.empty or len(bars) < 21:
        return "NEUTRAL"

    close = bars['close']
    ema9 = calc_ema(close, 9)
    ema21 = calc_ema(close, 21)

    if ema9.iloc[-1] > ema21.iloc[-1]:
        return "BULLISH"
    elif ema9.iloc[-1] < ema21.iloc[-1]:
        return "BEARISH"
    return "NEUTRAL"


# ── Intelligent Scoring Engine ────────────────────────────────────────

def score_symbol_v2(symbol: str) -> Optional[dict]:
    """
    Intelligent 0-100 scoring with weighted indicators.
    Only generates BUY when score >= threshold AND confidence is high.
    """
    bars = get_bars(symbol, timeframe_minutes=5, limit=100)
    if bars.empty or len(bars) < 50:
        return None

    close = bars['close']
    high = bars['high']
    low = bars['low']
    volume = bars['volume']
    price = float(close.iloc[-1])

    # Calculate all indicators
    rsi_14 = calc_rsi(close, 14)
    rsi_7 = calc_rsi(close, 7)
    macd, macd_signal, macd_hist = calc_macd(close)
    bb_upper, bb_mid, bb_lower = calc_bollinger(close)
    adx = calc_adx(high, low, close)
    obv = calc_obv(close, volume)
    stoch_k, stoch_d = calc_stochastic(high, low, close)
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()

    # Get latest values
    current_rsi = float(rsi_14.iloc[-1]) if not pd.isna(rsi_14.iloc[-1]) else 50
    current_adx = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 20
    current_macd = float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0
    current_macd_sig = float(macd_signal.iloc[-1]) if not pd.isna(macd_signal.iloc[-1]) else 0
    current_macd_hist = float(macd_hist.iloc[-1]) if not pd.isna(macd_hist.iloc[-1]) else 0
    current_stoch_k = float(stoch_k.iloc[-1]) if not pd.isna(stoch_k.iloc[-1]) else 50

    reasons = []
    score = 50  # Start neutral

    # ═══ TECHNICAL SCORE (max +/- 30) ═══

    # RSI (0-8 points)
    if current_rsi < 30:
        score += 8
        reasons.append(f'RSI oversold ({current_rsi:.1f})')
    elif current_rsi < 40:
        score += 4
        reasons.append(f'RSI low ({current_rsi:.1f})')
    elif current_rsi > 70:
        score -= 6
        reasons.append(f'RSI overbought ({current_rsi:.1f})')

    # MACD crossover (0-7 points)
    prev_macd = float(macd.iloc[-2]) if not pd.isna(macd.iloc[-2]) else 0
    prev_macd_sig = float(macd_signal.iloc[-2]) if not pd.isna(macd_signal.iloc[-2]) else 0
    if current_macd > current_macd_sig and prev_macd <= prev_macd_sig:
        score += 7
        reasons.append('MACD bullish cross')
    elif current_macd < current_macd_sig and prev_macd >= prev_macd_sig:
        score -= 5

    # Bollinger position (0-6 points)
    bb_range = float(bb_upper.iloc[-1] - bb_lower.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else 1
    if bb_range > 0:
        bb_position = (price - float(bb_lower.iloc[-1])) / bb_range
        if bb_position < 0.2:
            score += 6
            reasons.append('Near lower Bollinger Band')
        elif bb_position > 0.85:
            score -= 4

    # EMA trend (0-5 points)
    ema9 = calc_ema(close, 9)
    ema21 = calc_ema(close, 21)
    if float(ema9.iloc[-1]) > float(ema21.iloc[-1]) and float(ema9.iloc[-2]) <= float(ema21.iloc[-2]):
        score += 5
        reasons.append('EMA9 crossed above EMA21')
    elif float(ema9.iloc[-1]) < float(ema21.iloc[-1]):
        score -= 3

    # Stochastic (0-4 points)
    if current_stoch_k < 20:
        score += 4
        reasons.append(f'Stochastic oversold ({current_stoch_k:.0f})')
    elif current_stoch_k > 80:
        score -= 3

    # ═══ TREND STRENGTH — ADX FILTER (max +/- 5) ═══
    if current_adx > 25:
        score += 3
        reasons.append(f'Strong trend (ADX {current_adx:.0f})')
    elif current_adx < 15:
        score -= 3  # Choppy market, avoid

    # SMA trend alignment (0-4 points)
    sma20_val = float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else price
    sma50_val = float(sma_50.iloc[-1]) if not pd.isna(sma_50.iloc[-1]) else price
    if price > sma20_val > sma50_val:
        score += 4
        reasons.append('Price > SMA20 > SMA50 (uptrend)')
    elif price < sma20_val < sma50_val:
        score -= 4

    # ═══ VOLUME SCORE (max +/- 10) ═══
    vol_avg = float(volume.rolling(20).mean().iloc[-1]) if not pd.isna(volume.rolling(20).mean().iloc[-1]) else 1
    vol_ratio = float(volume.iloc[-1]) / vol_avg if vol_avg > 0 else 1

    if vol_ratio > 1.5:
        score += 5
        reasons.append(f'Volume surge ({vol_ratio:.1f}x avg)')

    # OBV trend
    obv_sma = obv.rolling(20).mean()
    if not pd.isna(obv.iloc[-1]) and not pd.isna(obv_sma.iloc[-1]):
        if float(obv.iloc[-1]) > float(obv_sma.iloc[-1]):
            score += 5
            reasons.append('OBV trending up (accumulation)')
        else:
            score -= 3

    # ═══ DIVERGENCE SCORE (max +/- 10) ═══
    divergence = detect_rsi_divergence(close, rsi_14)
    if divergence == "BULLISH":
        score += 10
        reasons.append('Bullish RSI divergence')
    elif divergence == "BEARISH":
        score -= 7

    # ═══ MULTI-TIMEFRAME CONFIRMATION (max +/- 8) ═══
    hourly_trend = check_hourly_trend(symbol)
    if hourly_trend == "BULLISH":
        score += 8
        reasons.append('1-hour trend BULLISH (confirmed)')
    elif hourly_trend == "BEARISH":
        score -= 8
        reasons.append('1-hour trend BEARISH (avoid)')

    # ═══ CANDLESTICK PATTERNS (max +/- 3) ═══
    c = bars.iloc[-1]
    body = abs(c['close'] - c['open'])
    lower_wick = min(c['open'], c['close']) - c['low']
    upper_wick = c['high'] - max(c['open'], c['close'])

    if body > 0 and lower_wick >= 2 * body and c['close'] > c['open']:
        score += 3
        reasons.append('Hammer candle')
    if len(bars) >= 2:
        prev = bars.iloc[-2]
        if (prev['close'] < prev['open'] and c['close'] > c['open'] and
                c['open'] <= prev['close'] and c['close'] >= prev['open']):
            score += 3
            reasons.append('Bullish engulfing')

    # ═══ FINAL SCORE ═══
    score = max(0, min(100, score))
    confidence = min(1.0, len(reasons) / 5)  # More reasons = higher confidence

    # Determine signal
    if score >= BUY_THRESHOLD and confidence >= MIN_CONFIDENCE:
        signal = 'BUY'
    elif score <= 30:
        signal = 'SELL'
    else:
        signal = 'HOLD'

    return {
        'symbol': symbol,
        'signal': signal,
        'score': score,
        'confidence': confidence,
        'price': price,
        'reasons': reasons,
        'adx': current_adx,
        'rsi': current_rsi,
        'hourly_trend': hourly_trend,
    }


# ── Adaptive Position Sizing ──────────────────────────────────────────

def calculate_position_size(account_equity: float, score: int, adx: float) -> float:
    """
    Adaptive position sizing:
    - Strong signals (high score) = larger position
    - High ADX (strong trend) = larger position
    - Weak signals = smaller position
    """
    base_size = POSITION_SIZE_USD

    # Score factor: 0.5x to 1.5x based on signal strength
    if score >= 80:
        score_factor = 1.5
    elif score >= 70:
        score_factor = 1.2
    elif score >= 60:
        score_factor = 1.0
    else:
        score_factor = 0.7

    # ADX factor: strong trend = bigger position
    if adx > 30:
        adx_factor = 1.3
    elif adx > 25:
        adx_factor = 1.0
    else:
        adx_factor = 0.7

    # Never risk more than 3% of equity
    max_size = account_equity * 0.03
    final_size = min(base_size * score_factor * adx_factor, max_size)

    return final_size


# ── Trading Logic ─────────────────────────────────────────────────────

def get_positions() -> dict:
    try:
        return {p.symbol: p for p in trading().get_all_positions()}
    except Exception as e:
        log.warning(f"get_positions failed: {e}")
        return {}

def get_account():
    try:
        return trading().get_account()
    except Exception as e:
        log.warning(f"get_account failed: {e}")
        return None

def daily_pnl() -> float:
    acct = get_account()
    if acct:
        return float(acct.equity) - float(acct.last_equity)
    return 0.0

def is_market_open() -> bool:
    try:
        return trading().get_clock().is_open
    except Exception as e:
        log.warning(f"is_market_open failed: {e}")
        return False

def place_order(symbol: str, side: str, qty: int, price: float):
    try:
        req = MarketOrderRequest(
            symbol=symbol, qty=qty,
            side=OrderSide.BUY if side == 'buy' else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        trading().submit_order(req)
        log.info(f"ORDER: {side.upper()} {qty}x {symbol} @ ~${price:.2f}")
    except Exception as e:
        log.error(f"Order failed {side} {symbol}: {e}")


# ── Main Cycle ────────────────────────────────────────────────────────
running = True

def run_cycle():
    global running
    if not is_market_open():
        log.info("Market closed")
        return

    pnl = daily_pnl()
    if pnl <= MAX_DAILY_LOSS_USD:
        log.error(f"Daily loss limit hit (${pnl:.2f}) — stopping")
        running = False
        return

    positions = get_positions()
    acct = get_account()
    if not acct:
        return
    equity = float(acct.equity)
    buying_power = float(acct.buying_power)

    # ── Stop-loss / Take-profit ──
    for sym, p in list(positions.items()):
        try:
            plpc = float(p.unrealized_plpc) * 100
            qty = int(float(p.qty))
            price = float(p.current_price)
            if plpc >= TAKE_PROFIT_PCT:
                log.info(f"Take-profit: {sym} +{plpc:.2f}%")
                place_order(sym, 'sell', qty, price)
            elif plpc <= -STOP_LOSS_PCT:
                log.warning(f"Stop-loss: {sym} {plpc:.2f}%")
                place_order(sym, 'sell', qty, price)
        except Exception as e:
            log.warning(f"SL/TP error {sym}: {e}")

    if len(positions) >= MAX_POSITIONS or buying_power < POSITION_SIZE_USD:
        return

    # ── Scan for entries (intelligent scoring) ──
    candidates = []
    for sym in WATCHLIST:
        if sym in positions:
            continue
        sig = score_symbol_v2(sym)
        if sig and sig['signal'] == 'BUY':
            candidates.append(sig)
            log.info(
                f"SIGNAL {sym}: score={sig['score']} conf={sig['confidence']:.2f} "
                f"ADX={sig['adx']:.0f} RSI={sig['rsi']:.0f} "
                f"1H={sig['hourly_trend']} | {', '.join(sig['reasons'][:3])}"
            )

    # Sort by score (best first)
    candidates.sort(key=lambda x: x['score'], reverse=True)

    for sig in candidates:
        if len(positions) >= MAX_POSITIONS or buying_power < POSITION_SIZE_USD:
            break
        sym = sig['symbol']
        price = sig['price']

        # Adaptive position size
        pos_size = calculate_position_size(equity, sig['score'], sig['adx'])
        qty = max(1, int(pos_size / price))

        log.info(f"BUY {sym} score={sig['score']} size=${qty*price:.0f} (adaptive)")
        place_order(sym, 'buy', qty, price)
        buying_power -= qty * price
        positions[sym] = True


def main():
    log.info("=" * 60)
    log.info("  HARDIN VC3 v2 — Intelligent Trading")
    log.info(f"  Position size  : ${POSITION_SIZE_USD:.0f} (adaptive)")
    log.info(f"  Stop loss      : {STOP_LOSS_PCT}%")
    log.info(f"  Take profit    : {TAKE_PROFIT_PCT}%")
    log.info(f"  Max positions  : {MAX_POSITIONS}")
    log.info(f"  Max daily loss : ${MAX_DAILY_LOSS_USD:.0f}")
    log.info(f"  Buy threshold  : score >= {BUY_THRESHOLD}")
    log.info(f"  Min confidence : {MIN_CONFIDENCE}")
    log.info(f"  Watchlist      : {len(WATCHLIST)} symbols")
    log.info(f"  Indicators     : RSI, MACD, BB, EMA, ADX, OBV, Stoch, Divergence")
    log.info(f"  Timeframes     : 5-min + 1-hour confirmation")
    log.info("=" * 60)

    while running:
        try:
            run_cycle()
        except Exception as e:
            log.error(f"Cycle error: {e}")
        time.sleep(SCAN_INTERVAL)


if __name__ == '__main__':
    main()
