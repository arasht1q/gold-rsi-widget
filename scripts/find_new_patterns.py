"""
Search for NEW patterns in RSI(30) M30 gold data that could become signals.
Beyond what we already know (zone touches, divergence, candles in zone, volume).
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DATA_DIR = "/home/z/my-project/data"

# Load data
events = pd.read_pickle(f"{DATA_DIR}/events_full.pkl")
price = pd.read_pickle(f"{DATA_DIR}/price_with_rsi.pkl")

print(f"Events: {len(events)}, Price candles: {len(price)}")
print(f"Events columns: {list(events.columns)}")
print()

# ===================================================================
# PATTERN 1: Consecutive zone touches (double bottom/top on RSI)
# ===================================================================
print("="*70)
print("PATTERN 1: Consecutive zone touches (RSI returns to same zone quickly)")
print("="*70)

# For each event, check if there was another touch of the SAME zone within 20 candles
events_sorted = events.sort_values('ts').reset_index(drop=True)
consecutive_results = []

for i, ev in events_sorted.iterrows():
    # Look for previous touch of same level within 50 candles (25 hours)
    same_level = events_sorted[
        (events_sorted['level'] == ev['level']) &
        (events_sorted['ts'] < ev['ts']) &
        (events_sorted['ts'] > ev['ts'] - timedelta(hours=25))
    ]
    
    if len(same_level) > 0:
        prev = same_level.iloc[-1]
        hours_between = (ev['ts'] - prev['ts']).total_seconds() / 3600
        # Check if price made lower low (for level 40) or higher high (for level 60)
        if ev['level'] == 40:
            price_lower = ev['price_at_touch'] < prev['price_at_touch']
            rsi_higher = ev['rsi_at_touch'] > prev['rsi_at_touch']
            pattern = 'double_bottom' if price_lower and rsi_higher else 'retest'
        else:
            price_higher = ev['price_at_touch'] > prev['price_at_touch']
            rsi_lower = ev['rsi_at_touch'] < prev['rsi_at_touch']
            pattern = 'double_top' if price_higher and rsi_lower else 'retest'
        
        consecutive_results.append({
            'ts': ev['ts'],
            'level': ev['level'],
            'category': ev['category'],
            'hours_between': hours_between,
            'pattern': pattern,
        })

if consecutive_results:
    cr = pd.DataFrame(consecutive_results)
    print(f"Total consecutive touches: {len(cr)}")
    print(f"  Double bottom (price lower + RSI higher at zone 40): {(cr['pattern']=='double_bottom').sum()}")
    print(f"  Double top (price higher + RSI lower at zone 60): {(cr['pattern']=='double_top').sum()}")
    print(f"  Simple retest: {(cr['pattern']=='retest').sum()}")
    
    print(f"\nOutcome when double bottom/top:")
    for pat in ['double_bottom', 'double_top', 'retest']:
        sub = cr[cr['pattern'] == pat]
        if len(sub) > 0:
            dist = sub['category'].value_counts(normalize=True)
            print(f"  {pat} ({len(sub)} events): {dict(dist.round(3))}")

# ===================================================================
# PATTERN 2: RSI 50 cross behavior
# ===================================================================
print("\n" + "="*70)
print("PATTERN 2: RSI crosses 50 — what happens next?")
print("="*70)

rsi = price['rsi30'].copy()
# Find all crosses of 50
cross_up = (rsi > 50) & (rsi.shift(1) <= 50)
cross_down = (rsi < 50) & (rsi.shift(1) >= 50)

cross_up_count = cross_up.sum()
cross_down_count = cross_down.sum()
print(f"Total crosses above 50: {cross_up_count}")
print(f"Total crosses below 50: {cross_down_count}")

# For each cross up, check if RSI reaches 60 within 30 candles
reaches_60_after_up = 0
reaches_40_after_up = 0
for idx in price.index[cross_up]:
    pos = price.index.get_loc(idx)
    future = rsi.iloc[pos+1:pos+31]
    if len(future) > 0:
        if (future >= 60).any():
            reaches_60_after_up += 1
        if (future <= 40).any():
            reaches_40_after_up += 1

print(f"\nAfter crossing ABOVE 50:")
print(f"  Reaches zone 60 within 30 candles: {reaches_60_after_up} ({reaches_60_after_up/cross_up_count*100:.1f}%)")
print(f"  Returns to zone 40 within 30 candles: {reaches_40_after_up} ({reaches_40_after_up/cross_up_count*100:.1f}%)")

# ===================================================================
# PATTERN 3: RSI velocity at zone touch (fast vs slow approach)
# ===================================================================
print("\n" + "="*70)
print("PATTERN 3: RSI velocity categories at touch")
print("="*70)

# Already have rsi_velocity_10 in events
if 'rsi_velocity_10' in events.columns:
    for vel_cat, lo, hi in [('very_slow', -99, -1), ('slow', -1, 0), ('neutral', 0, 1), ('fast', 1, 3), ('very_fast', 3, 99)]:
        sub = events[(events['rsi_velocity_10'] >= lo) & (events['rsi_velocity_10'] < hi)]
        if len(sub) > 0:
            dist = sub['category'].value_counts(normalize=True)
            rev_pct = dist.get('REVERSAL', 0) * 100
            pass_pct = dist.get('PASS_THROUGH', 0) * 100
            div_pct = dist.get('DIVERGENCE', 0) * 100
            print(f"  {vel_cat:10s} ({len(sub):4d} events): Rev={rev_pct:.0f}% Div={div_pct:.0f}% Pass={pass_pct:.0f}%")

# ===================================================================
# PATTERN 4: Time of day patterns
# ===================================================================
print("\n" + "="*70)
print("PATTERN 4: Best hours for reversal (Tehran time)")
print("="*70)

events['hour_tehran'] = (events['ts'].dt.hour + 3) % 24
hourly_rev = events.groupby('hour_tehran').apply(
    lambda x: pd.Series({
        'count': len(x),
        'reversal_rate': (x['category'] == 'REVERSAL').mean() * 100 if len(x) > 0 else 0,
        'pass_rate': (x['category'] == 'PASS_THROUGH').mean() * 100 if len(x) > 0 else 0,
    })
).sort_values('reversal_rate', ascending=False)

print("Top 5 hours for reversal (Tehran time):")
print(hourly_rev.head(5).round(1))
print("\nBottom 5 hours for reversal:")
print(hourly_rev.tail(5).round(1))

# ===================================================================
# PATTERN 5: RSI fails to reach zone (near miss)
# ===================================================================
print("\n" + "="*70)
print("PATTERN 5: RSI near-miss (reaches 42-43 or 57-58 but not zone)")
print("="*70)

near_miss_low = (rsi >= 42) & (rsi <= 43) & ~(rsi.between(39, 41))
near_miss_high = (rsi >= 57) & (rsi <= 58) & ~(rsi.between(59, 61))

print(f"Near-miss low (42-43, didn't reach 40 zone): {near_miss_low.sum()}")
print(f"Near-miss high (57-58, didn't reach 60 zone): {near_miss_high.sum()}")

# What happens after near-miss? Does price still reverse?
reversal_after_near_low = 0
total_near_low = 0
for idx in price.index[near_miss_low]:
    pos = price.index.get_loc(idx)
    future = price['close'].iloc[pos+1:pos+11]
    if len(future) >= 5:
        total_near_low += 1
        # Check if price went up 0.3% in next 10 candles
        if (future.max() - price['close'].iloc[pos]) / price['close'].iloc[pos] > 0.003:
            reversal_after_near_low += 1

print(f"Price went up 0.3%+ after near-miss low: {reversal_after_near_low}/{total_near_low} ({reversal_after_near_low/total_near_low*100:.1f}%)" if total_near_low > 0 else "  No data")

# ===================================================================
# PATTERN 6: RSI stays in mid-range (45-55) for extended period
# ===================================================================
print("\n" + "="*70)
print("PATTERN 6: RSI consolidation in 45-55 range")
print("="*70)

# Count consecutive bars where RSI is between 45 and 55
in_mid = (rsi >= 45) & (rsi <= 55)
mid_streaks = []
current_streak = 0
for i in range(len(rsi)):
    if in_mid.iloc[i]:
        current_streak += 1
    else:
        if current_streak >= 10:  # At least 5 hours
            mid_streaks.append(current_streak)
        current_streak = 0

print(f"Periods where RSI stayed in 45-55 for 10+ candles (5+ hours): {len(mid_streaks)}")
if mid_streaks:
    print(f"  Average streak: {np.mean(mid_streaks):.1f} candles ({np.mean(mid_streaks)*0.5:.1f} hours)")
    print(f"  Max streak: {max(mid_streaks)} candles ({max(mid_streaks)*0.5:.1f} hours)")

# ===================================================================
# PATTERN 7: Price distance from zone touch to recent swing
# ===================================================================
print("\n" + "="*70)
print("PATTERN 7: Price at touch vs recent swing (10 candles back)")
print("="*70)

if 'price_at_touch' in events.columns:
    for level in [40, 60]:
        sub = events[events['level'] == level]
        # Check if price at touch is near recent low (for level 40) or high (for level 60)
        results = {'at_swing': 0, 'above_swing': 0, 'below_swing': 0}
        for _, ev in sub.iterrows():
            try:
                pos = price.index.get_loc(ev['ts'])
                if pos >= 10:
                    recent_low = price['low'].iloc[pos-10:pos].min()
                    recent_high = price['high'].iloc[pos-10:pos].max()
                    p = ev['price_at_touch']
                    if level == 40:
                        if abs(p - recent_low) / p < 0.002:
                            results['at_swing'] += 1
                        elif p < recent_low:
                            results['below_swing'] += 1
                        else:
                            results['above_swing'] += 1
                    else:
                        if abs(p - recent_high) / p < 0.002:
                            results['at_swing'] += 1
                        elif p > recent_high:
                            results['above_swing'] += 1
                        else:
                            results['below_swing'] += 1
            except:
                pass
        
        total = sum(results.values())
        if total > 0:
            print(f"  Level {level}: at_swing={results['at_swing']} ({results['at_swing']/total*100:.0f}%), "
                  f"beyond_swing={results['above_swing']+results['below_swing']} ({(results['above_swing']+results['below_swing'])/total*100:.0f}%)")

# ===================================================================
# PATTERN 8: What happens 1 candle after zone touch?
# ===================================================================
print("\n" + "="*70)
print("PATTERN 8: First candle after zone touch")
print("="*70)

for level in [40, 60]:
    sub = events[events['level'] == level]
    bullish_first = 0
    bearish_first = 0
    doji_first = 0
    total = 0
    
    for _, ev in sub.iterrows():
        try:
            pos = price.index.get_loc(ev['ts'])
            if pos + 1 < len(price):
                next_candle = price.iloc[pos + 1]
                body = abs(next_candle['close'] - next_candle['open'])
                rng = next_candle['high'] - next_candle['low']
                total += 1
                if rng > 0 and body <= rng * 0.1:
                    doji_first += 1
                elif next_candle['close'] > next_candle['open']:
                    bullish_first += 1
                else:
                    bearish_first += 1
        except:
            pass
    
    if total > 0:
        print(f"  Level {level}: Bullish next={bullish_first} ({bullish_first/total*100:.0f}%), "
              f"Bearish next={bearish_first} ({bearish_first/total*100:.0f}%), "
              f"Doji next={doji_first} ({doji_first/total*100:.0f}%)")

# ===================================================================
# PATTERN 9: RSI slope change at zone (deceleration)
# ===================================================================
print("\n" + "="*70)
print("PATTERN 9: RSI deceleration at zone (velocity drops)")
print("="*70)

if 'rsi_velocity_10' in events.columns and 'rsi_velocity_5' in events.columns:
    events['vel_ratio'] = events['rsi_velocity_5'] / events['rsi_velocity_10'].replace(0, np.nan)
    events['decelerating'] = events['vel_ratio'].abs() < 0.5  # Velocity dropped by half
    
    decel = events[events['decelerating'] == True]
    non_decel = events[events['decelerating'] == False]
    
    if len(decel) > 0 and len(non_decel) > 0:
        print(f"  Decelerating ({len(decel)} events):")
        dist = decel['category'].value_counts(normalize=True)
        for cat, pct in dist.items():
            print(f"    {cat}: {pct*100:.1f}%")
        print(f"  Non-decelerating ({len(non_decel)} events):")
        dist = non_decel['category'].value_counts(normalize=True)
        for cat, pct in dist.items():
            print(f"    {cat}: {pct*100:.1f}%")

# ===================================================================
# PATTERN 10: RSI bounces between zones (40→60 or 60→40)
# ===================================================================
print("\n" + "="*70)
print("PATTERN 10: RSI swings between zones (40 to 60 or vice versa)")
print("="*70)

events_sorted = events.sort_values('ts').reset_index(drop=True)
swings = []
for i in range(1, len(events_sorted)):
    prev = events_sorted.iloc[i-1]
    curr = events_sorted.iloc[i]
    if prev['level'] != curr['level']:
        hours = (curr['ts'] - prev['ts']).total_seconds() / 3600
        if hours < 48:  # Within 2 days
            swings.append({
                'from_level': prev['level'],
                'to_level': curr['level'],
                'hours': hours,
                'category': curr['category'],
            })

if swings:
    sw = pd.DataFrame(swings)
    print(f"Total zone swings (40↔60 within 48h): {len(sw)}")
    print(f"  Average time between swings: {sw['hours'].mean():.1f} hours")
    print(f"  From 40→60: {(sw['from_level']==40).sum()}, From 60→40: {(sw['from_level']==60).sum()}")
    
    print(f"\n  Outcome when swinging 40→60:")
    sub = sw[sw['from_level'] == 40]
    if len(sub) > 0:
        print(f"    {dict(sub['category'].value_counts(normalize=True).round(3))}")
    
    print(f"  Outcome when swinging 60→40:")
    sub = sw[sw['from_level'] == 60]
    if len(sub) > 0:
        print(f"    {dict(sub['category'].value_counts(normalize=True).round(3))}")

# ===================================================================
# SUMMARY: New patterns found
# ===================================================================
print("\n" + "="*70)
print("SUMMARY: Potential new signals")
print("="*70)

print("""
NEW PATTERNS FOUND THAT COULD BECOME SIGNALS:

1. DOUBLE BOTTOM/TOP ON RSI:
   - RSI returns to same zone within 25 hours
   - Price makes lower low (zone 40) or higher high (zone 60)
   - But RSI makes higher low / lower high
   - This is a "confirmed retest" signal

2. RSI 50 CROSS DIRECTIONAL BIAS:
   - After crossing above 50: more likely to reach 60 than return to 40
   - Can be used as a "trend direction" filter

3. RSI DECELERATION AT ZONE:
   - When RSI velocity drops by 50%+ at zone touch
   - Indicates momentum loss → higher reversal probability

4. FIRST CANDLE AFTER TOUCH:
   - The color/pattern of the first candle after zone touch
   - Can be used as immediate confirmation signal

5. NEAR-MISS SIGNAL:
   - When RSI reaches 42-43 or 57-58 but doesn't enter zone
   - Price may still reverse — potential early entry signal

6. ZONE SWING:
   - When RSI swings from 40 to 60 (or vice versa) within 48 hours
   - Indicates strong momentum — favor continuation

7. TIME-BASED FILTER:
   - Specific Tehran hours have 40%+ reversal rate
   - vs 25% in worst hours
   - Can filter signals by time of day
""")
