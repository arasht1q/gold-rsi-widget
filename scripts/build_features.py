"""
Build predictive features + statistical analysis on the refined events.
"""
import os, json
import numpy as np
import pandas as pd
from scipy import stats

DATA_DIR = "/home/z/my-project/data"

df = pd.read_pickle(f"{DATA_DIR}/price_with_rsi.pkl")
events = pd.read_pickle(f"{DATA_DIR}/events_refined.pkl")
print(f"Events: {len(events)}, candles: {len(df)}")

# Add SMAs
df['sma50']  = df['close'].rolling(50).mean()
df['sma200'] = df['close'].rolling(200).mean()

def session(h):
    if 0 <= h < 7:   return 'Asia'
    if 7 <= h < 13:  return 'Europe'
    if 13 <= h < 21: return 'US'
    return 'Asia2'

def session_label(h):
    # Tehran time = UTC + 3:30. So:
    # Tehran 8-12 = morning = UTC 4:30-8:30 → mostly Asia
    # Tehran 13-17 = afternoon = UTC 9:30-13:30 → Europe
    # Tehran 18-22 = evening = UTC 14:30-18:30 → US
    teh = (h + 3.5) % 24
    if 6 <= teh < 12:  return 'صبح (آسیا)'
    if 12 <= teh < 17: return 'ظهر (اروپا)'
    if 17 <= teh < 22: return 'عصر (آمریکا)'
    return 'شب'

# Build features
feat_rows = []
for _, ev in events.iterrows():
    ts = ev['ts']
    pos = df.index.get_loc(ts)
    if pos < 200:
        continue
    close_pre = df['close'].iloc[pos-20:pos+1].values
    rsi_pre   = df['rsi30'].iloc[pos-10:pos+1].values
    vol_pre   = df['volume'].iloc[pos-20:pos+1].values

    feat = {
        'ts': ts,
        'level': ev['level'],
        'category': ev['category'],
        'rsi_at_touch': ev['rsi_at_touch'],
        'price_at_touch': ev['price_at_touch'],
        'candles_in_zone': ev['candles_in_zone'],
        'favorable_pct': ev['favorable_pct'],
        'adverse_pct': ev['adverse_pct'],
        'max_excursion_rsi': ev['max_excursion_rsi'],
        # RSI momentum / velocity
        'rsi_velocity_5':  df['rsi30'].iloc[pos] - df['rsi30'].iloc[pos-5],
        'rsi_velocity_10': df['rsi30'].iloc[pos] - df['rsi30'].iloc[pos-10],
        'rsi_change_prev_candle': df['rsi30'].iloc[pos] - df['rsi30'].iloc[pos-1],
        # Price slope / momentum (per candle)
        'price_slope_10': np.polyfit(np.arange(10), close_pre[-10:], 1)[0],
        'price_slope_20': np.polyfit(np.arange(20), close_pre[-20:], 1)[0],
        'trend_20_pct':  (close_pre[-1] - close_pre[-20]) / close_pre[-20] * 100,
        'trend_50_pct':  (close_pre[-1] - df['close'].iloc[pos-50]) / df['close'].iloc[pos-50] * 100,
        # Volume
        'avg_vol_5':  np.mean(vol_pre[-5:]),
        'avg_vol_20': np.mean(vol_pre),
        'vol_ratio_5_20': np.mean(vol_pre[-5:]) / max(np.mean(vol_pre), 1),
        # Distance from SMAs (% of price)
        'dist_sma50_pct':  (df['close'].iloc[pos] - df['sma50'].iloc[pos])  / df['sma50'].iloc[pos]  * 100 if not np.isnan(df['sma50'].iloc[pos])  else np.nan,
        'dist_sma200_pct': (df['close'].iloc[pos] - df['sma200'].iloc[pos]) / df['sma200'].iloc[pos] * 100 if not np.isnan(df['sma200'].iloc[pos]) else np.nan,
        # Trend strength: ADJ slope sign over 50 candles
        'trend_dir_50': 'up' if df['close'].iloc[pos] > df['close'].iloc[pos-50] else 'down',
        # Time
        'hour_utc': ts.hour,
        'day_of_week': int(ts.dayofweek),
        'day_name': ['دوشنبه','سه‌شنبه','چهارشنبه','پنجشنبه','جمعه','شنبه','یکشنبه'][int(ts.dayofweek)],
        'session': session(ts.hour),
        'session_label': session_label(ts.hour),
    }
    feat_rows.append(feat)

feat_df = pd.DataFrame(feat_rows)
print(f"Features built: {len(feat_df)}")

# Combine
events_full = events.merge(
    feat_df.drop(columns=['level','category','rsi_at_touch','price_at_touch',
                           'candles_in_zone','favorable_pct','adverse_pct','max_excursion_rsi']),
    on='ts', how='left')

events_full.to_csv(f"{DATA_DIR}/events_full.csv", index=False)
events_full.to_pickle(f"{DATA_DIR}/events_full.pkl")
print(f"Saved {DATA_DIR}/events_full.csv")

# ===================================================================
# Statistical analysis
# ===================================================================
print("\n" + "="*70)
print("STATISTICAL ANALYSIS")
print("="*70)

# 1. Counts by year, level, category
events_full['year'] = events_full['ts'].dt.year
print("\n--- Counts by year × level × category ---")
yr = events_full.pivot_table(index=['year','level'], columns='category',
                              values='ts', aggfunc='count', fill_value=0, margins=True)
print(yr)

# 2. Means of key features per category
print("\n--- Mean features by category (level 60) ---")
e60 = events_full[events_full['level']==60]
print(e60.groupby('category')[['rsi_velocity_10','rsi_velocity_5',
    'price_slope_10','trend_50_pct','avg_vol_20','vol_ratio_5_20',
    'dist_sma50_pct','dist_sma200_pct','candles_in_zone',
    'favorable_pct','adverse_pct','max_excursion_rsi']].mean().round(3))

print("\n--- Mean features by category (level 40) ---")
e40 = events_full[events_full['level']==40]
print(e40.groupby('category')[['rsi_velocity_10','rsi_velocity_5',
    'price_slope_10','trend_50_pct','avg_vol_20','vol_ratio_5_20',
    'dist_sma50_pct','dist_sma200_pct','candles_in_zone',
    'favorable_pct','adverse_pct','max_excursion_rsi']].mean().round(3))

# 3. Session distribution
print("\n--- Distribution by session ---")
sess = events_full.pivot_table(index='session_label', columns='category',
                                values='ts', aggfunc='count', fill_value=0, margins=True)
print(sess)

# 4. Day-of-week distribution
print("\n--- Distribution by day of week ---")
dow = events_full.pivot_table(index='day_name', columns='category',
                               values='ts', aggfunc='count', fill_value=0, margins=True)
# Reorder
order = ['دوشنبه','سه‌شنبه','چهارشنبه','پنجشنبه','جمعه','شنبه','یکشنبه']
dow = dow.reindex(order + ['All'])
print(dow)

# 5. Trend direction
print("\n--- Distribution by prior trend (50-candle) ---")
tdir = events_full.pivot_table(index='trend_dir_50', columns='category',
                                values='ts', aggfunc='count', fill_value=0, margins=True)
print(tdir)

# 6. Statistical tests (one-way ANOVA) — do feature means differ across categories?
print("\n--- ANOVA: do features differ significantly by category? ---")
features_to_test = ['rsi_velocity_10','rsi_velocity_5','rsi_change_prev_candle',
                     'price_slope_10','price_slope_20','trend_50_pct','trend_20_pct',
                     'avg_vol_20','vol_ratio_5_20','dist_sma50_pct','dist_sma200_pct',
                     'candles_in_zone','hour_utc']
for f in features_to_test:
    groups = [g[f].dropna().values for _, g in events_full.groupby('category')]
    if all(len(g) > 5 for g in groups):
        F, p = stats.f_oneway(*groups)
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
        print(f"  {f:30s}  F={F:7.3f}  p={p:.4f}  {sig}")

# 7. Save aggregate stats to JSON for use in PDF/Excel
agg = {
    'total_events': len(events_full),
    'by_category': events_full['category'].value_counts().to_dict(),
    'by_level_category': events_full.pivot_table(index='level', columns='category',
                                                  values='ts', aggfunc='count', fill_value=0).to_dict(),
    'by_year': events_full.groupby(['year','level','category']).size().to_dict(),
    'mean_features_by_category': events_full.groupby('category')[
        ['rsi_velocity_10','rsi_velocity_5','rsi_change_prev_candle',
         'price_slope_10','price_slope_20','trend_50_pct','trend_20_pct',
         'avg_vol_20','vol_ratio_5_20','dist_sma50_pct','dist_sma200_pct',
         'candles_in_zone','favorable_pct','adverse_pct','max_excursion_rsi']
    ].mean().round(4).to_dict(),
    'by_session': events_full.pivot_table(index='session_label', columns='category',
                                           values='ts', aggfunc='count', fill_value=0).to_dict(),
    'by_day': events_full.pivot_table(index='day_name', columns='category',
                                       values='ts', aggfunc='count', fill_value=0).to_dict(),
    'by_trend_dir': events_full.pivot_table(index='trend_dir_50', columns='category',
                                             values='ts', aggfunc='count', fill_value=0).to_dict(),
}
with open(f"{DATA_DIR}/stats.json", 'w') as f:
    json.dump(agg, f, indent=2, default=str)
print(f"\nSaved stats to {DATA_DIR}/stats.json")
