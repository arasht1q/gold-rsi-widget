"""Generate charts for the overlap analysis PDF report."""
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Persian font
for p in ['/home/z/.fonts/Vazirmatn-Regular.ttf',
          '/home/z/.fonts/Vazirmatn-Bold.ttf',
          '/home/z/.fonts/Vazirmatn-Medium.ttf']:
    if os.path.exists(p):
        fm.fontManager.addfont(p)

plt.rcParams['font.family'] = 'Vazirmatn'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10

DATA_DIR = "/home/z/my-project/data"
CHART_DIR = "/home/z/my-project/data/charts_overlap"
os.makedirs(CHART_DIR, exist_ok=True)

results = pd.read_pickle(f"{DATA_DIR}/overlap_analysis.pkl")
with open(f"{DATA_DIR}/overlap_summary.json") as f:
    summary = json.load(f)

# Colors (matching widget palette)
CAT_COLORS = {
    'PASS_THROUGH': '#e89090',  # soft coral
    'REVERSAL':     '#9ec99e',  # soft sage
    'DIVERGENCE':   '#f0b870',  # soft peach
}
CAT_LABELS_FA = {
    'PASS_THROUGH': 'گذشتن',
    'REVERSAL':     'برگشت',
    'DIVERGENCE':   'واگرایی',
}

# ============================================================
# Chart 1: Overlap pie — % of touches inside vs outside zones
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
fig.suptitle('همپوشانی برخوردهای RSI با زون‌های مهم (دوجی)',
             fontsize=13, fontweight='bold')

# Pie 1: Inside vs outside
total = summary['total_events']
inside = summary['inside_either']
outside = total - inside
axes[0].pie([inside, outside],
            labels=[f'داخل زون\n{inside} ({inside/total*100:.1f}%)',
                    f'خارج از زون\n{outside} ({outside/total*100:.1f}%)'],
            colors=['#f0b870', '#c8c8c8'],
            autopct='', startangle=90,
            wedgeprops={'edgecolor':'white','linewidth':2})
axes[0].set_title('برخوردها: داخل vs خارج زون', fontsize=11)

# Pie 2: Daily vs Weekly vs Both
inside_d = summary['inside_daily']
inside_w = summary['inside_weekly']
inside_b = summary['inside_both']
inside_d_only = inside_d - inside_b
inside_w_only = inside_w - inside_b
axes[1].pie([inside_d_only, inside_w_only, inside_b],
            labels=[f'فقط دیلی\n{inside_d_only}',
                    f'فقط هفتگی\n{inside_w_only}',
                    f'هر دو\n{inside_b}'],
            colors=['#c8c8c8', '#f5b87a', '#e89090'],
            autopct='', startangle=90,
            wedgeprops={'edgecolor':'white','linewidth':2})
axes[1].set_title('تفکیک نوع زون (در بین برخوردهای داخل زون)', fontsize=11)

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart1_overlap_pie.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart1_overlap_pie.png")

# ============================================================
# Chart 2: Category distribution — Inside vs Outside vs Both
# ============================================================
fig, ax = plt.subplots(figsize=(11, 5))

cats = ['REVERSAL', 'DIVERGENCE', 'PASS_THROUGH']
labels = [CAT_LABELS_FA[c] for c in cats]

# Get distributions
dist_inside = summary['category_dist_inside']
dist_outside = summary['category_dist_outside']
dist_both = summary['category_dist_both']

vals_inside = [dist_inside.get(c, 0) * 100 for c in cats]
vals_outside = [dist_outside.get(c, 0) * 100 for c in cats]
vals_both = [dist_both.get(c, 0) * 100 for c in cats]

x = np.arange(len(cats))
w = 0.25

bars1 = ax.bar(x - w, vals_outside, w, label='خارج از زون (baseline)', color='#c8c8c8')
bars2 = ax.bar(x, vals_inside, w, label='داخل حداقل یک زون', color='#f0b870')
bars3 = ax.bar(x + w, vals_both, w, label='داخل هر دو زون (دیلی+هفتگی)', color='#e89090')

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11)
ax.set_ylabel('درصد وقوع', fontsize=11)
ax.set_title('تأثیر همپوشانی زون‌ها بر نوع واکنش بازار',
             fontsize=13, fontweight='bold', pad=15)
ax.legend(fontsize=10, loc='upper right')
ax.grid(True, axis='y', alpha=0.3)
ax.set_ylim(0, 60)

# Add value labels
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 1, f'{h:.0f}%',
                ha='center', fontsize=9)

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart2_impact_comparison.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart2_impact_comparison.png")

# ============================================================
# Chart 3: By level — overlap rate
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
fig.suptitle('نرخ همپوشانی بر اساس سطح RSI', fontsize=13, fontweight='bold')

for ax, level in [(axes[0], 40), (axes[1], 60)]:
    by_lvl = summary['by_level'][str(level)]
    total_lvl = by_lvl['total']
    inside_lvl = by_lvl['inside_either']
    outside_lvl = total_lvl - inside_lvl
    ax.pie([inside_lvl, outside_lvl],
           labels=[f'داخل زون\n{inside_lvl} ({inside_lvl/total_lvl*100:.1f}%)',
                   f'خارج\n{outside_lvl} ({outside_lvl/total_lvl*100:.1f}%)'],
           colors=['#f0b870', '#c8c8c8'],
           startangle=90, wedgeprops={'edgecolor':'white','linewidth':2})
    ax.set_title(f'سطح {level} (total: {total_lvl})', fontsize=11)

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart3_by_level.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart3_by_level.png")

# ============================================================
# Chart 4: Category by level — inside vs outside
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('تفکیک واکنش بازار بر اساس سطح و وضعیت زون',
             fontsize=13, fontweight='bold')

for ax, level in [(axes[0], 40), (axes[1], 60)]:
    by_lvl = summary['by_level'][str(level)]
    dist_in = by_lvl['category_dist_inside']
    dist_out = by_lvl['category_dist_outside']
    vals_in = [dist_in.get(c, 0) * 100 for c in cats]
    vals_out = [dist_out.get(c, 0) * 100 for c in cats]

    x = np.arange(len(cats))
    w = 0.35
    b1 = ax.bar(x - w/2, vals_out, w, label='خارج از زون', color='#c8c8c8')
    b2 = ax.bar(x + w/2, vals_in, w, label='داخل زون', color='#f0b870')

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel('درصد', fontsize=10)
    ax.set_title(f'سطح {level}', fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(True, axis='y', alpha=0.3)
    ax.set_ylim(0, 60)
    for bars in [b1, b2]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 1, f'{h:.0f}%',
                    ha='center', fontsize=8)

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart4_by_level_category.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart4_by_level_category.png")

# ============================================================
# Chart 5: Time-to-touch distribution
# ============================================================
ttd = pd.read_pickle(f"{DATA_DIR}/overlap_analysis.pkl")
# Recompute time-to-touch from events
events = pd.read_pickle(f"{DATA_DIR}/events_full.pkl")
rsi_series = pd.read_pickle(f"{DATA_DIR}/price_with_rsi.pkl")['rsi30']

time_data_40 = []
time_data_60 = []
for _, ev in events.iterrows():
    try:
        pos = rsi_series.index.get_loc(ev['ts'])
    except KeyError:
        continue
    walk_back = 0
    for k in range(pos - 1, max(0, pos - 100), -1):
        walk_back += 1
        if 49 <= rsi_series.iloc[k] <= 51:
            break
    if ev['level'] == 40:
        time_data_40.append(walk_back * 0.5)  # hours
    else:
        time_data_60.append(walk_back * 0.5)

fig, ax = plt.subplots(figsize=(10, 4.5))
bins = np.arange(0, 50, 2)
ax.hist(time_data_40, bins=bins, alpha=0.7, color='#9ec99e', label=f'سطح 40 (میانگین: {np.mean(time_data_40):.1f}h)')
ax.hist(time_data_60, bins=bins, alpha=0.7, color='#e89090', label=f'سطح 60 (میانگین: {np.mean(time_data_60):.1f}h)')
ax.axvline(np.mean(time_data_40), color='#5b8c5a', linestyle='--', linewidth=2)
ax.axvline(np.mean(time_data_60), color='#b56b6b', linestyle='--', linewidth=2)
ax.set_xlabel('زمان از RSI=50 تا برخورد (ساعت)', fontsize=11)
ax.set_ylabel('تعداد رویداد', fontsize=11)
ax.set_title('زمان رسیدن RSI از ۵۰ (خنثی) به سطح ۴۰ یا ۶۰',
             fontsize=13, fontweight='bold', pad=15)
ax.legend(fontsize=10)
ax.grid(True, axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart5_time_to_touch.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart5_time_to_touch.png")

# ============================================================
# Chart 6: Touch events by Tehran hour
# ============================================================
results['hour_tehran'] = (results['ts'].dt.hour + 3.5) % 24
hour_dist = results.groupby('hour_tehran').size()

fig, ax = plt.subplots(figsize=(11, 4))
hours = np.arange(0, 24)
counts = [int(hour_dist.get(h, 0)) for h in hours]
colors = []
for h in hours:
    if 6 <= h < 12: colors.append('#9ec99e')      # Asia morning
    elif 12 <= h < 17: colors.append('#f0b870')   # Europe
    elif 17 <= h < 22: colors.append('#e89090')   # US
    else: colors.append('#c8c8c8')                # Night

ax.bar(hours, counts, color=colors, edgecolor='white', linewidth=0.5)
ax.set_xlabel('ساعت (به وقت تهران)', fontsize=11)
ax.set_ylabel('تعداد برخورد', fontsize=11)
ax.set_title('توزیع زمانی برخوردهای RSI به سطوح ۴۰ و ۶۰',
             fontsize=13, fontweight='bold', pad=15)
ax.set_xticks(hours)
ax.set_xticklabels([f'{int(h)}' for h in hours], fontsize=9)
ax.grid(True, axis='y', alpha=0.3)

# Legend
from matplotlib.patches import Patch
legend_elems = [
    Patch(facecolor='#9ec99e', label='صبح (آسیا)'),
    Patch(facecolor='#f0b870', label='ظهر (اروپا)'),
    Patch(facecolor='#e89090', label='عصر (آمریکا)'),
    Patch(facecolor='#c8c8c8', label='شب'),
]
ax.legend(handles=legend_elems, fontsize=9, loc='upper right')

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart6_by_hour.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart6_by_hour.png")

# ============================================================
# Chart 7: Key finding summary — pass-through rate comparison
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))

# Show pass-through rate in different scenarios
scenarios = ['خارج از زون\n(baseline)', 'داخل یک زون\n(دیلی یا هفتگی)', 'داخل هر دو زون\n(دیلی+هفتگی)']
pt_rates = [
    summary['category_dist_outside'].get('PASS_THROUGH', 0) * 100,
    summary['category_dist_inside'].get('PASS_THROUGH', 0) * 100,
    summary['category_dist_both'].get('PASS_THROUGH', 0) * 100,
]
rev_rates = [
    summary['category_dist_outside'].get('REVERSAL', 0) * 100,
    summary['category_dist_inside'].get('REVERSAL', 0) * 100,
    summary['category_dist_both'].get('REVERSAL', 0) * 100,
]
div_rates = [
    summary['category_dist_outside'].get('DIVERGENCE', 0) * 100,
    summary['category_dist_inside'].get('DIVERGENCE', 0) * 100,
    summary['category_dist_both'].get('DIVERGENCE', 0) * 100,
]

x = np.arange(len(scenarios))
w = 0.25
b1 = ax.bar(x - w, rev_rates, w, label='برگشت', color='#9ec99e')
b2 = ax.bar(x, div_rates, w, label='واگرایی', color='#f0b870')
b3 = ax.bar(x + w, pt_rates, w, label='گذشتن', color='#e89090')

ax.set_xticks(x)
ax.set_xticklabels(scenarios, fontsize=10)
ax.set_ylabel('درصد وقوع', fontsize=11)
ax.set_title('یافته کلیدی: تأثیر همپوشانی زون‌ها بر احتمالات',
             fontsize=13, fontweight='bold', pad=15)
ax.legend(fontsize=10)
ax.grid(True, axis='y', alpha=0.3)
ax.set_ylim(0, 60)

for bars in [b1, b2, b3]:
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 1, f'{h:.0f}%',
                ha='center', fontsize=9)

# Annotate the key finding
ax.annotate('وقتی داخل هر دو زون باشیم:\nگذشتن از ۴۷٪ به ۲۸٪ کاهش می‌یابد!',
            xy=(2 + w, pt_rates[2]), xytext=(2.3, 50),
            fontsize=10, color='#b56b6b', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#b56b6b', lw=1.5))

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart7_key_finding.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart7_key_finding.png")

print(f"\nAll charts saved to {CHART_DIR}")
