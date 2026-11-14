"""
Refined RSI(30) touch-event analysis — use FIRST exit from zone, not 'any exit'.
Also adds: 'real touch' filter (must touch level itself ±0.5).
"""
import os, json
import numpy as np
import pandas as pd

DATA_DIR = "/home/z/my-project/data"
OUT_DIR  = "/home/z/my-project/data"

df = pd.read_csv(f"{DATA_DIR}/xauusd_30m_with_rsi.csv",
                 parse_dates=['open_time'], index_col='open_time')
df = df[['open','high','low','close','volume','trades','rsi30']].dropna().sort_index()
print(f"Loaded {len(df):,} candles")

# ----------------------------------------------------------------------
# Find touch events with stricter rule:
#   - RSI must touch the LEVEL itself within ±0.5 (e.g. 39.5-40.5 for level 40)
#   - Otherwise we ignore the zone grazing
# ----------------------------------------------------------------------
def find_real_touches(rsi_series, level, zone_tol=1.0, touch_tol=0.5):
    """
    A 'real touch' event starts at the first candle where RSI is in the zone
    [level-zone_tol, level+zone_tol] AND within ±touch_tol of the level itself.
    The event ends when RSI exits the zone.
    """
    z_lo = level - zone_tol
    z_hi = level + zone_tol
    t_lo = level - touch_tol
    t_hi = level + touch_tol
    in_zone  = (rsi_series >= z_lo) & (rsi_series <= z_hi)
    near_lvl = (rsi_series >= t_lo) & (rsi_series <= t_hi)
    n = len(rsi_series)
    events = []
    i = 1
    while i < n:
        if in_zone.iloc[i] and not in_zone.iloc[i-1]:
            # scan this in-zone run for whether RSI came near the level
            j = i
            run_min = rsi_series.iloc[i]
            run_max = rsi_series.iloc[i]
            while j < n and in_zone.iloc[j]:
                run_min = min(run_min, rsi_series.iloc[j])
                run_max = max(run_max, rsi_series.iloc[j])
                j += 1
            # For level 60: 'real touch' if run_max >= t_lo (i.e. >= 59.5)
            # For level 40: 'real touch' if run_min <= t_hi (i.e. <= 40.5)
            if level >= 50:
                touched = run_max >= t_lo
            else:
                touched = run_min <= t_hi
            if touched:
                # Determine entry direction by scanning back before i
                k = i - 1
                entry_dir = None
                while k >= 0:
                    if rsi_series.iloc[k] < z_lo:
                        entry_dir = 'from_below'; break
                    if rsi_series.iloc[k] > z_hi:
                        entry_dir = 'from_above'; break
                    k -= 1
                if entry_dir is None:
                    entry_dir = 'from_below' if level >= 50 else 'from_above'
                # find exact touch index within this run
                if level >= 50:
                    rel_idx = i + int(np.argmax(rsi_series.iloc[i:j].values))
                else:
                    rel_idx = i + int(np.argmin(rsi_series.iloc[i:j].values))
                events.append({
                    'entry_idx': i,
                    'touch_idx': rel_idx,
                    'exit_idx': j if j < n else n-1,
                    'rsi_at_entry': rsi_series.iloc[i],
                    'rsi_at_touch': rsi_series.iloc[rel_idx],
                    'rsi_at_exit':  rsi_series.iloc[j-1] if j < n else rsi_series.iloc[-1],
                    'entry_dir':    entry_dir,
                })
            i = j
        else:
            i += 1
    return events

events_60 = find_real_touches(df['rsi30'], 60)
events_40 = find_real_touches(df['rsi30'], 40)
print(f"\nReal touch events at 60: {len(events_60)}")
print(f"Real touch events at 40: {len(events_40)}")

# ----------------------------------------------------------------------
# Classify using FIRST exit direction
# ----------------------------------------------------------------------
FORWARD = 30  # candles look-forward for outcome (15h)

def classify_v2(df, ev, level, zone_tol=1.0, forward=FORWARD):
    """
    1) Determine first exit direction from zone.
       - For level 60 (entered from below): 'opposite' = exit above upper
       - For level 40 (entered from above): 'opposite' = exit below lower
    2) If first exit is opposite → PASS_THROUGH
    3) Else look at the forward window (until first exit, or full window if no exit):
       - price_continued = price made new extreme in direction of approach
       - rsi_continued    = RSI  made new extreme in direction of approach
       - If price_continued and not rsi_continued → DIVERGENCE
       - Else → REVERSAL
    """
    z_lo = level - zone_tol
    z_hi = level + zone_tol
    entry_idx = ev['entry_idx']
    n = len(df)
    end_i = min(entry_idx + forward, n - 1)

    # Find first exit direction (relative to entry direction)
    first_exit_dir = None
    first_exit_idx = None
    for k in range(entry_idx+1, end_i+1):
        r = df['rsi30'].iloc[k]
        if r > z_hi:
            first_exit_dir = 'above'; first_exit_idx = k; break
        if r < z_lo:
            first_exit_dir = 'below'; first_exit_idx = k; break

    if level >= 50:
        # entered from below; opposite exit = above
        opposite = (first_exit_dir == 'above')
    else:
        # entered from above; opposite exit = below
        opposite = (first_exit_dir == 'below')

    if opposite:
        category = 'PASS_THROUGH'
    else:
        # Same-side exit (or no exit) → check divergence vs reversal
        check_end = first_exit_idx if first_exit_idx else end_i
        rsi_fwd = df['rsi30'].iloc[entry_idx+1:check_end+1]
        hi_fwd  = df['high'].iloc[entry_idx+1:check_end+1]
        lo_fwd  = df['low'].iloc[entry_idx+1:check_end+1]

        if level >= 50:
            price_continued = (hi_fwd.max() > df['high'].iloc[entry_idx]) if len(hi_fwd) else False
            rsi_continued   = (rsi_fwd.max() > ev['rsi_at_touch']) if len(rsi_fwd) else False
        else:
            price_continued = (lo_fwd.min() < df['low'].iloc[entry_idx]) if len(lo_fwd) else False
            rsi_continued   = (rsi_fwd.min() < ev['rsi_at_touch']) if len(rsi_fwd) else False

        if price_continued and not rsi_continued:
            category = 'DIVERGENCE'
        else:
            category = 'REVERSAL'

    # Outcome magnitude
    rsi_fwd_full = df['rsi30'].iloc[entry_idx+1:end_i+1]
    px_fwd_full  = df['close'].iloc[entry_idx+1:end_i+1]
    hi_fwd_full  = df['high'].iloc[entry_idx+1:end_i+1]
    lo_fwd_full  = df['low'].iloc[entry_idx+1:end_i+1]
    ts_touch = df.index[ev['touch_idx']]
    price_touch = df['close'].iloc[ev['touch_idx']]

    if level >= 50:
        max_rsi_after = rsi_fwd_full.max() if len(rsi_fwd_full) else ev['rsi_at_touch']
        max_hi_after  = hi_fwd_full.max()  if len(hi_fwd_full)  else price_touch
        min_lo_after  = lo_fwd_full.min()  if len(lo_fwd_full)  else price_touch
        max_excursion_rsi = max_rsi_after - ev['rsi_at_touch']
        favorable_pct = (max_hi_after - price_touch) / price_touch * 100  # how far up it went
        adverse_pct   = (min_lo_after - price_touch) / price_touch * 100  # how far down it went
    else:
        min_rsi_after = rsi_fwd_full.min() if len(rsi_fwd_full) else ev['rsi_at_touch']
        max_hi_after  = hi_fwd_full.max()  if len(hi_fwd_full)  else price_touch
        min_lo_after  = lo_fwd_full.min()  if len(lo_fwd_full)  else price_touch
        max_excursion_rsi = ev['rsi_at_touch'] - min_rsi_after
        favorable_pct = (price_touch - min_lo_after) / price_touch * 100
        adverse_pct   = (max_hi_after - price_touch) / price_touch * 100

    return {
        'ts': ts_touch,
        'entry_ts': df.index[entry_idx],
        'exit_ts':  df.index[first_exit_idx] if first_exit_idx else df.index[end_i],
        'level': level,
        'entry_dir': ev['entry_dir'],
        'rsi_at_touch': ev['rsi_at_touch'],
        'price_at_touch': price_touch,
        'category': category,
        'first_exit_dir': first_exit_dir or 'none',
        'candles_in_zone': ev['exit_idx'] - ev['entry_idx'],
        'max_excursion_rsi': max_excursion_rsi,
        'favorable_pct': favorable_pct,
        'adverse_pct': adverse_pct,
    }

rows = []
for ev in events_60:
    rows.append(classify_v2(df, ev, 60))
for ev in events_40:
    rows.append(classify_v2(df, ev, 40))

events_df = pd.DataFrame(rows).sort_values('ts').reset_index(drop=True)
print(f"\nClassified {len(events_df)} events")

print("\n=== Summary (refined: FIRST exit + real-touch filter) ===")
piv = events_df.pivot_table(index='level', columns='category',
                            values='ts', aggfunc='count', fill_value=0, margins=True)
print(piv)

print("\n=== Overall distribution ===")
dist = events_df['category'].value_counts()
total = len(events_df)
for cat, cnt in dist.items():
    print(f"  {cat:14s}  {cnt:5d}  ({cnt/total*100:.1f}%)")

events_df.to_csv(f"{OUT_DIR}/events_refined.csv", index=False)
print(f"\nSaved: {OUT_DIR}/events_refined.csv")

# Save events_df to a pickle for use by downstream script
events_df.to_pickle(f"{OUT_DIR}/events_refined.pkl")
df.to_pickle(f"{OUT_DIR}/price_with_rsi.pkl")
