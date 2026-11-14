"""Generate charts for the PDF report."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Persian font: Vazirmatn or Noto Sans Arabic if available
# Try DejaVu first as fallback; then check Chinese fonts directory
for p in ['/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf',
          '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
    if os.path.exists(p):
        fm.fontManager.addfont(p)

# Try to find an Arabic/Persian capable font
PERSIAN_FONT = None
for fp in [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
]:
    if os.path.exists(fp):
        fm.fontManager.addfont(fp)

plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Noto Sans SC']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10

DATA_DIR = "/home/z/my-project/data"
CHART_DIR = "/home/z/my-project/data/charts"
os.makedirs(CHART_DIR, exist_ok=True)

events = pd.read_pickle(f"{DATA_DIR}/events_full.pkl")
price = pd.read_pickle(f"{DATA_DIR}/price_with_rsi.pkl")

# Colors per category
CAT_COLORS = {
    'PASS_THROUGH': '#e74c3c',  # red
    'REVERSAL':     '#27ae60',  # green
    'DIVERGENCE':   '#f39c12',  # orange
}
CAT_LABELS_FA = {
    'PASS_THROUGH': 'Gozashtan (Pass-through)',
    'REVERSAL':     'Bargasht (Reversal)',
    'DIVERGENCE':   'Vaghrayi (Divergence)',
}

# ===================================================================
# Chart 1: Distribution pie/bar
# ===================================================================
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
fig.suptitle('Distribution of RSI(30) M30 Touch Events  (2-year gold, 1328 events)',
             fontsize=12, fontweight='bold')

# Overall pie
counts = events['category'].value_counts()
labels = [f"{CAT_LABELS_FA[c]}\n{counts[c]} ({counts[c]/len(events)*100:.1f}%)" for c in counts.index]
colors = [CAT_COLORS[c] for c in counts.index]
axes[0].pie(counts.values, labels=labels, colors=colors, autopct='',
            startangle=90, wedgeprops={'edgecolor':'white','linewidth':2})
axes[0].set_title('Overall Distribution')

# By level grouped bar
lv = events.pivot_table(index='level', columns='category', values='ts', aggfunc='count', fill_value=0)
x = np.arange(len(lv.index))
w = 0.25
for i, c in enumerate(['REVERSAL','DIVERGENCE','PASS_THROUGH']):
    axes[1].bar(x + (i-1)*w, lv[c].values, w, label=CAT_LABELS_FA[c], color=CAT_COLORS[c])
axes[1].set_xticks(x); axes[1].set_xticklabels(['Level 40\n(oversold)','Level 60\n(overbought)'])
axes[1].set_ylabel('Number of events')
axes[1].set_title('By Level')
axes[1].legend(fontsize=8, loc='upper right')

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart1_distribution.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart1_distribution.png")

# ===================================================================
# Chart 2: Yearly distribution
# ===================================================================
events['year'] = events['ts'].dt.year
yr = events.pivot_table(index='year', columns='category', values='ts', aggfunc='count', fill_value=0)

fig, ax = plt.subplots(figsize=(10, 4))
x = np.arange(len(yr.index))
w = 0.25
for i, c in enumerate(['REVERSAL','DIVERGENCE','PASS_THROUGH']):
    ax.bar(x + (i-1)*w, yr[c].values, w, label=CAT_LABELS_FA[c], color=CAT_COLORS[c])
ax.set_xticks(x); ax.set_xticklabels(yr.index)
ax.set_ylabel('Number of events')
ax.set_title('Touch Events by Year', fontweight='bold')
ax.legend(fontsize=9)
for i, year in enumerate(yr.index):
    total = yr.loc[year].sum()
    ax.text(i, total + 5, f"n={total}", ha='center', fontsize=9, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart2_by_year.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart2_by_year.png")

# ===================================================================
# Chart 3: candles_in_zone distribution by category (KEY FINDING)
# ===================================================================
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
fig.suptitle('Time Spent in Zone (candles) by Category — Strongest Predictor (F=20.13, p<0.001)',
             fontsize=11, fontweight='bold')

# Level 60
e60 = events[events['level']==60]
data60 = [e60[e60['category']==c]['candles_in_zone'].dropna().values for c in ['REVERSAL','DIVERGENCE','PASS_THROUGH']]
bp = axes[0].boxplot(data60, labels=['Reversal','Divergence','Pass-through'],
                      patch_artist=True, showfliers=False, widths=0.6)
for patch, c in zip(bp['boxes'], ['REVERSAL','DIVERGENCE','PASS_THROUGH']):
    patch.set_facecolor(CAT_COLORS[c]); patch.set_alpha(0.7)
axes[0].set_title('Level 60 (overbought)')
axes[0].set_ylabel('Candles in zone')
axes[0].set_ylim(0, 25)
# Mean markers
for i, d in enumerate(data60):
    if len(d):
        axes[0].scatter(i+1, np.mean(d), marker='D', color='black', s=30, zorder=5)
        axes[0].text(i+1, np.mean(d)+0.5, f"μ={np.mean(d):.1f}", ha='center', fontsize=8)

# Level 40
e40 = events[events['level']==40]
data40 = [e40[e40['category']==c]['candles_in_zone'].dropna().values for c in ['REVERSAL','DIVERGENCE','PASS_THROUGH']]
bp = axes[1].boxplot(data40, labels=['Reversal','Divergence','Pass-through'],
                      patch_artist=True, showfliers=False, widths=0.6)
for patch, c in zip(bp['boxes'], ['REVERSAL','DIVERGENCE','PASS_THROUGH']):
    patch.set_facecolor(CAT_COLORS[c]); patch.set_alpha(0.7)
axes[1].set_title('Level 40 (oversold)')
axes[1].set_ylabel('Candles in zone')
axes[1].set_ylim(0, 25)
for i, d in enumerate(data40):
    if len(d):
        axes[1].scatter(i+1, np.mean(d), marker='D', color='black', s=30, zorder=5)
        axes[1].text(i+1, np.mean(d)+0.5, f"μ={np.mean(d):.1f}", ha='center', fontsize=8)

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart3_candles_in_zone.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart3_candles_in_zone.png")

# ===================================================================
# Chart 4: Feature means by category (heatmap-style)
# ===================================================================
features = ['rsi_velocity_10','rsi_velocity_5','price_slope_20','trend_50_pct',
            'avg_vol_20','vol_ratio_5_20','dist_sma50_pct','candles_in_zone',
            'favorable_pct','adverse_pct','max_excursion_rsi']
feat_labels = ['RSI vel (10)','RSI vel (5)','Price slope (20)','Trend % (50)',
               'Avg vol (20)','Vol ratio 5/20','Dist SMA50 %','Candles in zone',
               'Favorable %','Adverse %','Max RSI excursion']

means = events.groupby('category')[features].mean()

# Normalize each feature to 0-1 for color comparison
from sklearn.preprocessing import MinMaxScaler
# For 'adverse_pct' lower is better for buyer; but for visualization just normalize raw
norm = means.copy()
for col in features:
    col_min, col_max = means[col].min(), means[col].max()
    if col_max > col_min:
        norm[col] = (means[col] - col_min) / (col_max - col_min)
    else:
        norm[col] = 0.5

fig, ax = plt.subplots(figsize=(9, 4))
data = norm.T.reindex(['REVERSAL','DIVERGENCE','PASS_THROUGH']).T
im = ax.imshow(data.values, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=1)
ax.set_xticks(range(3)); ax.set_xticklabels(['Reversal','Divergence','Pass-through'])
ax.set_yticks(range(len(features))); ax.set_yticklabels(feat_labels)
# Annotate raw values
for i, f in enumerate(features):
    for j, c in enumerate(['REVERSAL','DIVERGENCE','PASS_THROUGH']):
        v = means.loc[c, f]
        ax.text(j, i, f"{v:.2f}", ha='center', va='center', fontsize=8,
                color='white' if abs(norm.loc[c, f]-0.5) > 0.4 else 'black')
ax.set_title('Mean Feature Values by Category  (color = normalized)', fontweight='bold', fontsize=11)
plt.colorbar(im, ax=ax, fraction=0.04, pad=0.04, label='Normalized (min=0, max=1)')
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart4_feature_heatmap.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart4_feature_heatmap.png")

# ===================================================================
# Chart 5: Session × category
# ===================================================================
sess = events.pivot_table(index='session_label', columns='category',
                          values='ts', aggfunc='count', fill_value=0)
order = ['صبح (آسیا)','ظهر (اروپا)','عصر (آمریکا)','شب']
sess = sess.reindex([s for s in order if s in sess.index])

fig, ax = plt.subplots(figsize=(9, 4))
x = np.arange(len(sess.index))
w = 0.25
for i, c in enumerate(['REVERSAL','DIVERGENCE','PASS_THROUGH']):
    ax.bar(x + (i-1)*w, sess[c].values, w, label=CAT_LABELS_FA[c], color=CAT_COLORS[c])
ax.set_xticks(x); ax.set_xticklabels(sess.index)
ax.set_ylabel('Number of events')
ax.set_title('Touch Events by Trading Session (Tehran time)', fontweight='bold')
ax.legend(fontsize=9)
# Add reversal % labels
for i, sess_name in enumerate(sess.index):
    total = sess.loc[sess_name].sum()
    rev_pct = sess.loc[sess_name, 'REVERSAL'] / total * 100 if total else 0
    ax.text(i, total + 3, f"Reversal:\n{rev_pct:.0f}%", ha='center', fontsize=8)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart5_by_session.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart5_by_session.png")

# ===================================================================
# Chart 6: RSI velocity distribution by category
# ===================================================================
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
fig.suptitle('RSI Velocity (10-candle change) by Category', fontsize=11, fontweight='bold')

# Level 60 — RSI velocity is positive (approaching from below)
e60 = events[events['level']==60]
data60 = [e60[e60['category']==c]['rsi_velocity_10'].dropna().values for c in ['REVERSAL','DIVERGENCE','PASS_THROUGH']]
bp = axes[0].boxplot(data60, labels=['Reversal','Divergence','Pass-through'],
                      patch_artist=True, showfliers=False, widths=0.6)
for patch, c in zip(bp['boxes'], ['REVERSAL','DIVERGENCE','PASS_THROUGH']):
    patch.set_facecolor(CAT_COLORS[c]); patch.set_alpha(0.7)
axes[0].set_title('Level 60 (RSI rising into zone)')
axes[0].set_ylabel('RSI velocity (10 candles)')
axes[0].axhline(0, color='gray', linestyle='--', alpha=0.5)
for i, d in enumerate(data60):
    if len(d):
        axes[0].text(i+1, max(d)*0.95, f"μ={np.mean(d):.2f}", ha='center', fontsize=8)

# Level 40 — RSI velocity is negative
e40 = events[events['level']==40]
data40 = [e40[e40['category']==c]['rsi_velocity_10'].dropna().values for c in ['REVERSAL','DIVERGENCE','PASS_THROUGH']]
bp = axes[1].boxplot(data40, labels=['Reversal','Divergence','Pass-through'],
                      patch_artist=True, showfliers=False, widths=0.6)
for patch, c in zip(bp['boxes'], ['REVERSAL','DIVERGENCE','PASS_THROUGH']):
    patch.set_facecolor(CAT_COLORS[c]); patch.set_alpha(0.7)
axes[1].set_title('Level 40 (RSI falling into zone)')
axes[1].set_ylabel('RSI velocity (10 candles)')
axes[1].axhline(0, color='gray', linestyle='--', alpha=0.5)
for i, d in enumerate(data40):
    if len(d):
        axes[1].text(i+1, min(d)*0.95, f"μ={np.mean(d):.2f}", ha='center', fontsize=8)

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart6_rsi_velocity.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart6_rsi_velocity.png")

# ===================================================================
# Chart 7: Example price+RSI chart with annotated events
# ===================================================================
# Pick a 1-month slice for visualization
slice_df = price.loc['2025-03-01':'2025-04-15'].copy()
slice_events = events[(events['ts'] >= '2025-03-01') & (events['ts'] <= '2025-04-15')]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True,
                                gridspec_kw={'height_ratios':[2.5, 1]})
ax1.plot(slice_df.index, slice_df['close'], color='#2c3e50', linewidth=1)
ax1.set_ylabel('Price (USD)')
ax1.set_title('Gold M30 + RSI(30) — Mar/Apr 2025 sample with annotated touch events',
              fontweight='bold', fontsize=11)

# Mark events on price chart
for _, ev in slice_events.iterrows():
    color = CAT_COLORS[ev['category']]
    marker = 'v' if ev['level']==60 else '^'
    ax1.scatter(ev['ts'], ev['price_at_touch'], color=color, marker=marker, s=60,
                edgecolor='black', linewidth=0.8, zorder=5)

# Legend
from matplotlib.lines import Line2D
legend_elems = [
    Line2D([0],[0], marker='v', color='w', markerfacecolor=CAT_COLORS['REVERSAL'],
           markersize=10, label='Reversal (60)'),
    Line2D([0],[0], marker='v', color='w', markerfacecolor=CAT_COLORS['DIVERGENCE'],
           markersize=10, label='Divergence (60)'),
    Line2D([0],[0], marker='v', color='w', markerfacecolor=CAT_COLORS['PASS_THROUGH'],
           markersize=10, label='Pass-through (60)'),
    Line2D([0],[0], marker='^', color='w', markerfacecolor=CAT_COLORS['REVERSAL'],
           markersize=10, label='Reversal (40)'),
]
ax1.legend(handles=legend_elems, fontsize=7, loc='upper left', ncol=2)

# RSI subplot
ax2.plot(slice_df.index, slice_df['rsi30'], color='#2980b9', linewidth=1)
ax2.axhline(60, color='red', linestyle='--', alpha=0.5)
ax2.axhline(40, color='green', linestyle='--', alpha=0.5)
ax2.axhspan(59, 61, alpha=0.15, color='red')
ax2.axhspan(39, 41, alpha=0.15, color='green')
ax2.set_ylabel('RSI(30)')
ax2.set_ylim(15, 85)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart7_example_period.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart7_example_period.png")

# ===================================================================
# Chart 8: Outcome magnitude — favorable vs adverse % per category
# ===================================================================
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
fig.suptitle('Price Outcome After Touch (15-hour forward window)', fontsize=11, fontweight='bold')

for ax, level, title in [(axes[0], 60, 'Level 60 (overbought — favorable = up)'),
                          (axes[1], 40, 'Level 40 (oversold — favorable = down)')]:
    elv = events[events['level']==level]
    cats = ['REVERSAL','DIVERGENCE','PASS_THROUGH']
    fav = [elv[elv['category']==c]['favorable_pct'].median() for c in cats]
    adv = [elv[elv['category']==c]['adverse_pct'].median() for c in cats]
    x = np.arange(3)
    w = 0.35
    ax.bar(x - w/2, fav, w, label='Favorable % (median)', color='#27ae60', alpha=0.8)
    ax.bar(x + w/2, adv, w, label='Adverse % (median)', color='#e74c3c', alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(['Reversal','Divergence','Pass-through'])
    ax.set_title(title); ax.set_ylabel('% price move')
    ax.legend(fontsize=8)
    ax.grid(True, axis='y', alpha=0.3)
    for i, (f, a) in enumerate(zip(fav, adv)):
        ax.text(i - w/2, f + 0.05, f"{f:.2f}%", ha='center', fontsize=7)
        ax.text(i + w/2, a + 0.05, f"{a:.2f}%", ha='center', fontsize=7)

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart8_outcome_magnitude.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart8_outcome_magnitude.png")

print("\nAll charts saved to", CHART_DIR)
