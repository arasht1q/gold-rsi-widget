"""
Analyze overlap between RSI touch events (40/60) and important Doji zones (daily/weekly).
For each touch event, check if the price at that moment was inside any Doji zone.
Compute impact of overlap on category outcomes.
"""
import os, json, pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

DATA_DIR = "/home/z/my-project/data"
OUT_DIR = "/home/z/my-project/data"

# ============================================================
# 1. Load data
# ============================================================
print("Loading data...")
price_df = pd.read_csv(f"{DATA_DIR}/xauusd_30m_binance_paxg.csv",
                       parse_dates=['open_time'], index_col='open_time')
price_df = price_df[['open','high','low','close','volume']].dropna().sort_index()
print(f"  M30 candles: {len(price_df):,}  range: {price_df.index.min()} → {price_df.index.max()}")

events = pd.read_pickle(f"{DATA_DIR}/events_full.pkl")
print(f"  Touch events: {len(events):,}")

# ============================================================
# 2. Aggregate to daily and weekly
# ============================================================
print("\nAggregating to daily and weekly...")
daily = price_df.resample('1D').agg({
    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
}).dropna()
weekly = price_df.resample('1W').agg({
    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
}).dropna()
print(f"  Daily candles: {len(daily)}")
print(f"  Weekly candles: {len(weekly)}")

# ============================================================
# 3. Detect Dojis
# ============================================================
def is_doji(row, threshold=0.10):
    range_ = row['high'] - row['low']
    if range_ <= 0:
        return False
    body = abs(row['close'] - row['open'])
    return body <= threshold * range_

daily['is_doji'] = daily.apply(is_doji, axis=1)
weekly['is_doji'] = weekly.apply(is_doji, axis=1)

print(f"\nDaily Dojis: {daily['is_doji'].sum()} / {len(daily)} ({daily['is_doji'].sum()/len(daily)*100:.1f}%)")
print(f"Weekly Dojis: {weekly['is_doji'].sum()} / {len(weekly)} ({weekly['is_doji'].sum()/len(weekly)*100:.1f}%)")

# ============================================================
# 4. Build zone list from Doji candles
# ============================================================
daily_zones = []
for idx, row in daily[daily['is_doji']].iterrows():
    daily_zones.append({
        'date': idx,
        'open': row['open'],
        'close': row['close'],
        'midpoint': (row['open'] + row['close']) / 2,
        'range_high': max(row['open'], row['close']),
        'range_low': min(row['open'], row['close']),
    })

weekly_zones = []
for idx, row in weekly[weekly['is_doji']].iterrows():
    weekly_zones.append({
        'date': idx,
        'open': row['open'],
        'close': row['close'],
        'midpoint': (row['open'] + row['close']) / 2,
        'range_high': max(row['open'], row['close']),
        'range_low': min(row['open'], row['close']),
    })

print(f"Daily Doji zones: {len(daily_zones)}")
print(f"Weekly Doji zones: {len(weekly_zones)}")

# ============================================================
# 5. For each touch event, check overlap with zones
# ============================================================
def find_inside_zones(price, time, zones, tolerance_pct=0.0015):
    """Find zones that contain the price at the given time.
    Only consider zones that existed BEFORE this event (causality)."""
    inside = []
    for z in zones:
        if z['date'] >= time:
            continue  # zone hasn't formed yet
        tolerance = price * tolerance_pct
        if z['range_low'] - tolerance <= price <= z['range_high'] + tolerance:
            inside.append(z)
    return inside

print("\nProcessing touch events...")
results = []
for _, ev in events.iterrows():
    price = ev['price_at_touch']
    time = ev['ts']

    daily_inside = find_inside_zones(price, time, daily_zones)
    weekly_inside = find_inside_zones(price, time, weekly_zones)

    results.append({
        'ts': time,
        'level': ev['level'],
        'category': ev['category'],
        'price': price,
        'inside_daily': len(daily_inside) > 0,
        'inside_weekly': len(weekly_inside) > 0,
        'inside_either': len(daily_inside) > 0 or len(weekly_inside) > 0,
        'inside_both': len(daily_inside) > 0 and len(weekly_inside) > 0,
        'daily_zones_count': len(daily_inside),
        'weekly_zones_count': len(weekly_inside),
    })

results_df = pd.DataFrame(results)
results_df.to_pickle(f"{OUT_DIR}/overlap_analysis.pkl")
results_df.to_csv(f"{OUT_DIR}/overlap_analysis.csv", index=False)

# ============================================================
# 6. Compute statistics
# ============================================================
print("\n" + "="*70)
print("OVERLAP STATISTICS")
print("="*70)

total = len(results_df)
inside_daily = results_df['inside_daily'].sum()
inside_weekly = results_df['inside_weekly'].sum()
inside_either = results_df['inside_either'].sum()
inside_both = results_df['inside_both'].sum()

print(f"\nTotal touch events: {total}")
print(f"Inside daily Doji zones:   {inside_daily:5d}  ({inside_daily/total*100:.1f}%)")
print(f"Inside weekly Doji zones:  {inside_weekly:5d}  ({inside_weekly/total*100:.1f}%)")
print(f"Inside either (any):       {inside_either:5d}  ({inside_either/total*100:.1f}%)")
print(f"Inside both (daily+weekly):{inside_both:5d}  ({inside_both/total*100:.1f}%)")
print(f"Outside all zones:         {total-inside_either:5d}  ({(total-inside_either)/total*100:.1f}%)")

# By level
print("\n--- By level ---")
for level in [40, 60]:
    sub = results_df[results_df['level'] == level]
    n = len(sub)
    in_d = sub['inside_daily'].sum()
    in_w = sub['inside_weekly'].sum()
    in_e = sub['inside_either'].sum()
    in_b = sub['inside_both'].sum()
    print(f"  Level {level}: total={n}")
    print(f"    Inside daily:   {in_d:4d} ({in_d/n*100:.1f}%)")
    print(f"    Inside weekly:  {in_w:4d} ({in_w/n*100:.1f}%)")
    print(f"    Inside either:  {in_e:4d} ({in_e/n*100:.1f}%)")
    print(f"    Inside both:    {in_b:4d} ({in_b/n*100:.1f}%)")

# ============================================================
# 7. Impact analysis: category distribution when inside vs outside zones
# ============================================================
print("\n" + "="*70)
print("IMPACT ANALYSIS — category distribution")
print("="*70)

# Inside zones
inside_sub = results_df[results_df['inside_either']]
outside_sub = results_df[~results_df['inside_either']]

print(f"\nWhen INSIDE a zone ({len(inside_sub)} events):")
if len(inside_sub) > 0:
    in_dist = inside_sub['category'].value_counts(normalize=True)
    for cat, pct in in_dist.items():
        cnt = (inside_sub['category'] == cat).sum()
        print(f"  {cat:14s}  {cnt:4d}  ({pct*100:.1f}%)")

print(f"\nWhen OUTSIDE zones ({len(outside_sub)} events):")
if len(outside_sub) > 0:
    out_dist = outside_sub['category'].value_counts(normalize=True)
    for cat, pct in out_dist.items():
        cnt = (outside_sub['category'] == cat).sum()
        print(f"  {cat:14s}  {cnt:4d}  ({pct*100:.1f}%)")

# Inside both daily AND weekly
both_sub = results_df[results_df['inside_both']]
print(f"\nWhen INSIDE BOTH daily AND weekly zones ({len(both_sub)} events):")
if len(both_sub) > 0:
    both_dist = both_sub['category'].value_counts(normalize=True)
    for cat, pct in both_dist.items():
        cnt = (both_sub['category'] == cat).sum()
        print(f"  {cat:14s}  {cnt:4d}  ({pct*100:.1f}%)")

# By level — inside vs outside
print("\n--- By level: inside vs outside ---")
for level in [40, 60]:
    print(f"\n  Level {level}:")
    in_lvl = results_df[(results_df['level'] == level) & (results_df['inside_either'])]
    out_lvl = results_df[(results_df['level'] == level) & (~results_df['inside_either'])]
    if len(in_lvl) > 0:
        print(f"    INSIDE ({len(in_lvl)}): ", end='')
        dist = in_lvl['category'].value_counts(normalize=True)
        print(' | '.join([f"{k}={v*100:.0f}%" for k, v in dist.items()]))
    if len(out_lvl) > 0:
        print(f"    OUTSIDE ({len(out_lvl)}): ", end='')
        dist = out_lvl['category'].value_counts(normalize=True)
        print(' | '.join([f"{k}={v*100:.0f}%" for k, v in dist.items()]))

# ============================================================
# 8. Time analysis - hour of day for touches
# ============================================================
print("\n" + "="*70)
print("TIME ANALYSIS — when do touches happen?")
print("="*70)

results_df['hour_utc'] = results_df['ts'].dt.hour
results_df['day_of_week'] = results_df['ts'].dt.dayofweek

# Tehran hour = UTC + 3:30
results_df['hour_tehran'] = (results_df['hour_utc'] + 3.5) % 24

# Group by Tehran hour
hour_dist = results_df.groupby('hour_tehran').size()
print(f"\nTouch events by Tehran hour (top 5):")
print(hour_dist.sort_values(ascending=False).head())

# Session breakdown
def session(h):
    if 6 <= h < 12: return 'صبح (آسیا)'
    if 12 <= h < 17: return 'ظهر (اروپا)'
    if 17 <= h < 22: return 'عصر (آمریکا)'
    return 'شب'

results_df['session'] = results_df['hour_tehran'].apply(session)
print(f"\nBy session:")
sess_dist = results_df.groupby('session').size()
print(sess_dist)

# ============================================================
# 9. Time-to-touch analysis (how long does it take for RSI to go from neutral to 40/60?)
# ============================================================
print("\n" + "="*70)
print("TIME-TO-TOUCH ANALYSIS")
print("="*70)

# For each touch event, find the previous time RSI was at 50 (neutral) and count candles
# This gives us an idea of how fast RSI typically moves from neutral to extreme
rsi_series = pd.read_pickle(f"{DATA_DIR}/price_with_rsi.pkl")['rsi30']

time_to_touch = []
for _, ev in events.iterrows():
    ev_time = ev['ts']
    # Find position in rsi_series
    try:
        pos = rsi_series.index.get_loc(ev_time)
    except KeyError:
        continue
    # Walk back until RSI crosses 50
    walk_back = 0
    for k in range(pos - 1, max(0, pos - 100), -1):
        walk_back += 1
        if 49 <= rsi_series.iloc[k] <= 51:
            break
    time_to_touch.append({
        'level': ev['level'],
        'category': ev['category'],
        'candles_from_neutral': walk_back,
        'minutes': walk_back * 30,  # M30 candles
        'hours': walk_back * 0.5,
    })

ttd = pd.DataFrame(time_to_touch)
print(f"\nTime from RSI=50 to touch (candles):")
print(f"  Mean: {ttd['candles_from_neutral'].mean():.1f} candles ({ttd['hours'].mean():.1f} hours)")
print(f"  Median: {ttd['candles_from_neutral'].median():.1f} candles ({ttd['hours'].median():.1f} hours)")
print(f"  Std: {ttd['candles_from_neutral'].std():.1f}")

print(f"\nBy level:")
for level in [40, 60]:
    sub = ttd[ttd['level'] == level]
    print(f"  Level {level}: mean={sub['candles_from_neutral'].mean():.1f} candles ({sub['hours'].mean():.1f}h)")

# ============================================================
# 10. Save summary stats to JSON
# ============================================================
summary = {
    'total_events': int(total),
    'inside_daily': int(inside_daily),
    'inside_weekly': int(inside_weekly),
    'inside_either': int(inside_either),
    'inside_both': int(inside_both),
    'outside_all': int(total - inside_either),
    'pct_inside_daily': float(inside_daily / total * 100),
    'pct_inside_weekly': float(inside_weekly / total * 100),
    'pct_inside_either': float(inside_either / total * 100),
    'pct_inside_both': float(inside_both / total * 100),
    'pct_outside': float((total - inside_either) / total * 100),
    'total_daily_doji_zones': len(daily_zones),
    'total_weekly_doji_zones': len(weekly_zones),
    'category_dist_inside': inside_sub['category'].value_counts(normalize=True).to_dict() if len(inside_sub) > 0 else {},
    'category_dist_outside': outside_sub['category'].value_counts(normalize=True).to_dict() if len(outside_sub) > 0 else {},
    'category_dist_both': both_sub['category'].value_counts(normalize=True).to_dict() if len(both_sub) > 0 else {},
    'count_inside': int(len(inside_sub)),
    'count_outside': int(len(outside_sub)),
    'count_both': int(len(both_sub)),
    'time_to_touch_mean_hours': float(ttd['hours'].mean()),
    'time_to_touch_median_hours': float(ttd['hours'].median()),
}

# Add by-level stats
by_level = {}
for level in [40, 60]:
    sub = results_df[results_df['level'] == level]
    n = len(sub)
    by_level[str(level)] = {
        'total': n,
        'inside_daily': int(sub['inside_daily'].sum()),
        'inside_weekly': int(sub['inside_weekly'].sum()),
        'inside_either': int(sub['inside_either'].sum()),
        'inside_both': int(sub['inside_both'].sum()),
        'pct_inside_either': float(sub['inside_either'].sum() / n * 100) if n > 0 else 0,
        'category_dist_inside': sub[sub['inside_either']]['category'].value_counts(normalize=True).to_dict() if sub['inside_either'].sum() > 0 else {},
        'category_dist_outside': sub[~sub['inside_either']]['category'].value_counts(normalize=True).to_dict() if (~sub['inside_either']).sum() > 0 else {},
    }
summary['by_level'] = by_level

with open(f"{OUT_DIR}/overlap_summary.json", 'w') as f:
    json.dump(summary, f, indent=2, default=str)

print(f"\n✓ Saved: {OUT_DIR}/overlap_analysis.csv")
print(f"✓ Saved: {OUT_DIR}/overlap_analysis.pkl")
print(f"✓ Saved: {OUT_DIR}/overlap_summary.json")
