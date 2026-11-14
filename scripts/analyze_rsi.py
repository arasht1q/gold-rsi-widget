"""
RSI(30) touch-event analysis on M30 gold (PAXG/USDT proxy).

Settings (per user):
- RSI period: 30 (close prices, Wilder smoothing — matches MT4)
- Levels: 40 (oversold zone) and 60 (overbought zone)
- Touch tolerance: ±1 unit → zones are [39,41] and [59,61]
- Look-forward window for outcome: 30 candles (15 hours)
- Categorization:
    1) PASS_THROUGH  = RSI exits zone on the OPPOSITE side it entered from
                       (e.g. entered 60-zone from below 59, exits above 61)
    2) DIVERGENCE    = RSI does NOT pass through, but price continues in
                       direction of approach (makes new extreme)
    3) REVERSAL      = RSI does NOT pass through and price does NOT make a
                       new extreme in direction of approach (price reverses)
"""
import os, json
import numpy as np
import pandas as pd
from datetime import timedelta

DATA_DIR  = "/home/z/my-project/data"
OUT_DIR   = "/home/z/my-project/data"
os.makedirs(OUT_DIR, exist_ok=True)

# ----------------------------------------------------------------------
# 1. Load M30 data
# ----------------------------------------------------------------------
df = pd.read_csv(f"{DATA_DIR}/xauusd_30m_binance_paxg.csv",
                 parse_dates=['open_time'], index_col='open_time')
df = df[['open','high','low','close','volume','trades']].copy()
df = df.dropna().sort_index()
print(f"Loaded {len(df):,} M30 candles  ({df.index.min()} → {df.index.max()})")

# ----------------------------------------------------------------------
# 2. RSI(30) — Wilder smoothing (MT4-compatible)
# ----------------------------------------------------------------------
def rsi_wilder(close, period=30):
    """Standard Wilder RSI, identical to MT4/MetaTrader implementation."""
    delta = close.diff()
    gain  = delta.where(delta > 0, 0.0)
    loss  = (-delta).where(delta < 0, 0.0)
    # Wilder smoothing == EMA with alpha = 1/period
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)  # first few NaNs
    return rsi

df['rsi30'] = rsi_wilder(df['close'], 30)
print(f"RSI(30) computed. Range: {df['rsi30'].min():.2f} – {df['rsi30'].max():.2f}  last={df['rsi30'].iloc[-1]:.2f}")

# Save enriched data for later reference
df.to_csv(f"{DATA_DIR}/xauusd_30m_with_rsi.csv")

# ----------------------------------------------------------------------
# 3. Identify touch events at level 40 (zone [39,41]) and 60 (zone [59,61])
# ----------------------------------------------------------------------
TOL = 1.0
LEVELS = {'overbought': 60, 'oversold': 40}
FORWARD = 30  # candles to look forward for outcome (15 hours on M30)

def find_touch_events(rsi_series, level, tol=TOL):
    """Return list of (idx_pos, rsi_value, entry_direction) for each touch event.
    A touch event is the FIRST candle of a contiguous run inside the zone.
    entry_direction = 'from_below' if RSI was below (level-tol) before entering,
                      'from_above' if RSI was above (level+tol) before entering.
    """
    lower = level - tol
    upper = level + tol
    in_zone = (rsi_series >= lower) & (rsi_series <= upper)
    events = []
    n = len(rsi_series)
    i = 1
    while i < n:
        if in_zone.iloc[i] and not in_zone.iloc[i-1]:
            # Determine entry direction by scanning back
            j = i - 1
            entry_dir = None
            while j >= 0:
                if rsi_series.iloc[j] < lower:
                    entry_dir = 'from_below'
                    break
                if rsi_series.iloc[j] > upper:
                    entry_dir = 'from_above'
                    break
                j -= 1
            # If never exited zone before (rare at start), default by level
            if entry_dir is None:
                entry_dir = 'from_below' if level >= 50 else 'from_above'
            events.append((i, rsi_series.iloc[i], entry_dir))
            # Skip until we leave the zone
            while i < n and in_zone.iloc[i]:
                i += 1
        else:
            i += 1
    return events

events_60 = find_touch_events(df['rsi30'], 60, TOL)
events_40 = find_touch_events(df['rsi30'], 40, TOL)
print(f"\nTouch events at 60 (zone [59,61]): {len(events_60)}")
print(f"Touch events at 40 (zone [39,41]): {len(events_40)}")

# ----------------------------------------------------------------------
# 4. Classify each event
# ----------------------------------------------------------------------
def classify_event(df, idx, level, tol, forward=FORWARD):
    """
    Returns dict with category + diagnostics.
    For level 60 (overbought):
      - Approach direction = up (RSI was below zone, came up)
      - 'opposite exit' = RSI exits above (level+tol) → PASS THROUGH
      - 'same-side exit' = RSI exits below (level-tol) → either REVERSAL or DIVERGENCE
    For level 40 (oversold): mirror logic.
    """
    lower = level - tol
    upper = level + tol
    n = len(df)
    end_i = min(idx + forward, n - 1)

    rsi_at_touch = df['rsi30'].iloc[idx]
    price_at_touch = df['close'].iloc[idx]
    ts_at_touch = df.index[idx]

    # Forward slice
    rsi_fwd = df['rsi30'].iloc[idx+1:end_i+1]
    px_fwd  = df['close'].iloc[idx+1:end_i+1]
    hi_fwd  = df['high'].iloc[idx+1:end_i+1]
    lo_fwd  = df['low'].iloc[idx+1:end_i+1]

    if level == 60:
        # overbought: approach was upward; opposite exit = above upper
        opposite_exit = (rsi_fwd > upper).any()
        max_rsi_after  = rsi_fwd.max() if len(rsi_fwd) else rsi_at_touch
        max_hi_after   = hi_fwd.max() if len(hi_fwd) else price_at_touch
        price_continued = max_hi_after > df['high'].iloc[idx]
        rsi_continued   = max_rsi_after > rsi_at_touch
        # 'divergence' = price makes higher high while RSI does NOT make higher high
        divergence_flag = price_continued and (not rsi_continued)
    else:
        # oversold: approach was downward; opposite exit = below lower
        opposite_exit = (rsi_fwd < lower).any()
        min_rsi_after  = rsi_fwd.min() if len(rsi_fwd) else rsi_at_touch
        min_lo_after   = lo_fwd.min() if len(lo_fwd) else price_at_touch
        price_continued = min_lo_after < df['low'].iloc[idx]
        rsi_continued   = min_rsi_after < rsi_at_touch
        divergence_flag = price_continued and (not rsi_continued)

    # Categorize with priority: PASS THROUGH > DIVERGENCE > REVERSAL
    if opposite_exit:
        category = 'PASS_THROUGH'
    elif divergence_flag:
        category = 'DIVERGENCE'
    else:
        category = 'REVERSAL'

    # Diagnostics for outcome magnitude
    if level == 60:
        max_excursion_rsi = max_rsi_after - rsi_at_touch
        price_change_pct = (max_hi_after - price_at_touch) / price_at_touch * 100
        worst_case_pct = (px_fwd.min() - price_at_touch) / price_at_touch * 100  # adverse
    else:
        max_excursion_rsi = rsi_at_touch - min_rsi_after
        price_change_pct = (price_at_touch - min_lo_after) / price_at_touch * 100
        worst_case_pct = (px_fwd.max() - price_at_touch) / price_at_touch * 100

    return {
        'ts': ts_at_touch,
        'level': level,
        'rsi_at_touch': rsi_at_touch,
        'price_at_touch': price_at_touch,
        'category': category,
        'opposite_exit': opposite_exit,
        'price_continued': price_continued,
        'rsi_continued': rsi_continued,
        'max_excursion_rsi': max_excursion_rsi,
        'price_change_pct': price_change_pct,
        'worst_case_pct': worst_case_pct,
    }

# Build events table
rows = []
for ev in events_60:
    r = classify_event(df, ev[0], 60, TOL)
    rows.append(r)
for ev in events_40:
    r = classify_event(df, ev[0], 40, TOL)
    rows.append(r)

events_df = pd.DataFrame(rows).sort_values('ts').reset_index(drop=True)
print(f"\nClassified {len(events_df)} events total.")

# Save intermediate
events_df.to_csv(f"{OUT_DIR}/events_raw.csv", index=False)

# Summary by level + category
print("\n=== Summary by level × category ===")
piv = events_df.pivot_table(index='level', columns='category',
                            values='ts', aggfunc='count', fill_value=0, margins=True)
print(piv)

# Save
events_df.to_csv(f"{OUT_DIR}/events_classified.csv", index=False)
print(f"\nSaved events to {OUT_DIR}/events_classified.csv")

# ----------------------------------------------------------------------
# 5. Compute predictive features for each event
# ----------------------------------------------------------------------
# SMA(50) and SMA(200) on M30 close
df['sma50']  = df['close'].rolling(50).mean()
df['sma200'] = df['close'].rolling(200).mean()

# Slope of price in last 20 candles (linear fit)
def slope_last_n(close_arr, n=20):
    if len(close_arr) < n:
        return np.nan
    y = close_arr[-n:]
    x = np.arange(n)
    coef = np.polyfit(x, y, 1)
    return coef[0]  # price change per candle

def rsi_velocity(rsi_arr, n=10):
    if len(rsi_arr) < n:
        return np.nan
    return rsi_arr[-1] - rsi_arr[-n]

# Session by hour (UTC): Asia 00-07, Europe 07-13, US 13-21, Asia2 21-24
def session(hour_utc):
    if 0 <= hour_utc < 7:   return 'Asia'
    if 7 <= hour_utc < 13:  return 'Europe'
    if 13 <= hour_utc < 21: return 'US'
    return 'Asia2'

# Build features
feat_rows = []
for _, ev in events_df.iterrows():
    ts = ev['ts']
    pos = df.index.get_loc(ts)
    if pos < 200:
        continue
    close_pre = df['close'].iloc[max(0,pos-20):pos+1].values
    rsi_pre   = df['rsi30'].iloc[max(0,pos-10):pos+1].values
    vol_pre   = df['volume'].iloc[max(0,pos-20):pos+1].values

    feat = {
        'ts': ts,
        'level': ev['level'],
        'category': ev['category'],
        'rsi_at_touch': ev['rsi_at_touch'],
        'price_at_touch': ev['price_at_touch'],
        # Velocity / momentum
        'rsi_velocity_10': rsi_velocity(rsi_pre, 10),
        'price_slope_20': slope_last_n(close_pre, 20),
        # Volume
        'avg_vol_20': np.mean(vol_pre) if len(vol_pre) else np.nan,
        # Distance from SMAs (% of price)
        'dist_sma50_pct':  (df['close'].iloc[pos] - df['sma50'].iloc[pos])  / df['sma50'].iloc[pos]  * 100 if not np.isnan(df['sma50'].iloc[pos])  else np.nan,
        'dist_sma200_pct': (df['close'].iloc[pos] - df['sma200'].iloc[pos]) / df['sma200'].iloc[pos] * 100 if not np.isnan(df['sma200'].iloc[pos]) else np.nan,
        # Trend prior: 50-candle return %
        'trend_50_pct': (df['close'].iloc[pos] - df['close'].iloc[pos-50]) / df['close'].iloc[pos-50] * 100,
        # Time
        'hour_utc': ts.hour,
        'day_of_week': ts.dayofweek,  # 0=Mon
        'session': session(ts.hour),
    }
    feat_rows.append(feat)

feat_df = pd.DataFrame(feat_rows)
print(f"\nFeatures built for {len(feat_df)} events.")
print(feat_df.head())

# Save
feat_df.to_csv(f"{OUT_DIR}/events_features.csv", index=False)
print(f"Saved features to {OUT_DIR}/events_features.csv")

# Final combined table
combined = events_df.merge(feat_df.drop(columns=['level','category','rsi_at_touch','price_at_touch']),
                            on='ts', how='left')
combined.to_csv(f"{OUT_DIR}/events_full.csv", index=False)
print(f"Saved combined events to {OUT_DIR}/events_full.csv")

# Quick stats
print("\n=== Category distribution ===")
print(combined['category'].value_counts())
print("\n=== Mean features per category ===")
print(combined.groupby('category')[['rsi_velocity_10','avg_vol_20','dist_sma50_pct',
                                     'dist_sma200_pct','trend_50_pct','price_slope_20']].mean().round(3))
