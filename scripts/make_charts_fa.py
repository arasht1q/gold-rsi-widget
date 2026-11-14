"""Regenerate chart 5 (Persian session labels) using Vazirmatn font."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Register Vazirmatn for Persian
fm.fontManager.addfont('/home/z/.fonts/Vazirmatn-Regular.ttf')
fm.fontManager.addfont('/home/z/.fonts/Vazirmatn-Bold.ttf')
fm.fontManager.addfont('/home/z/.fonts/Vazirmatn-Medium.ttf')
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')

# Use Vazirmatn as primary font (it has good Latin + Persian coverage)
plt.rcParams['font.family'] = 'Vazirmatn'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10

DATA_DIR = "/home/z/my-project/data"
CHART_DIR = "/home/z/my-project/data/charts"

events = pd.read_pickle(f"{DATA_DIR}/events_full.pkl")

CAT_COLORS = {
    'PASS_THROUGH': '#e74c3c',
    'REVERSAL':     '#27ae60',
    'DIVERGENCE':   '#f39c12',
}
CAT_LABELS_FA = {
    'PASS_THROUGH': 'گذشتن',
    'REVERSAL':     'برگشت',
    'DIVERGENCE':   'واگرایی',
}

# Regenerate chart 5: By session (Persian labels)
sess = events.pivot_table(index='session_label', columns='category',
                          values='ts', aggfunc='count', fill_value=0)
order = ['صبح (آسیا)','ظهر (اروپا)','عصر (آمریکا)','شب']
sess = sess.reindex([s for s in order if s in sess.index])

fig, ax = plt.subplots(figsize=(10, 4.5))
x = np.arange(len(sess.index))
w = 0.25
for i, c in enumerate(['REVERSAL','DIVERGENCE','PASS_THROUGH']):
    ax.bar(x + (i-1)*w, sess[c].values, w, label=CAT_LABELS_FA[c], color=CAT_COLORS[c])
ax.set_xticks(x); ax.set_xticklabels(sess.index, fontsize=11)
ax.set_ylabel('تعداد رویدادها')
ax.set_title('توزیع رویدادها بر اساس سشن معاملاتی (به وقت تهران)', fontsize=13, fontweight='bold', pad=15)
ax.legend(fontsize=11, loc='upper right')
for i, sess_name in enumerate(sess.index):
    total = sess.loc[sess_name].sum()
    rev_pct = sess.loc[sess_name, 'REVERSAL'] / total * 100 if total else 0
    pt_pct = sess.loc[sess_name, 'PASS_THROUGH'] / total * 100 if total else 0
    ax.text(i, total + 5, f"برگشت: {rev_pct:.0f}%\nگذشتن: {pt_pct:.0f}%", ha='center', fontsize=9)
ax.grid(True, axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart5_by_session.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart5_by_session.png regenerated with Vazirmatn")

# Also regenerate chart 1 distribution with Persian labels
counts = events['category'].value_counts()
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('توزیع رویدادهای برخورد RSI(30) در تایم‌فریم M30 طلا — ۲ سال (۱۳۲۸ رویداد)',
             fontsize=13, fontweight='bold')

# Pie
labels = [f"{CAT_LABELS_FA[c]}\n{counts[c]} ({counts[c]/len(events)*100:.1f}%)" for c in counts.index]
colors = [CAT_COLORS[c] for c in counts.index]
axes[0].pie(counts.values, labels=labels, colors=colors, autopct='',
            startangle=90, wedgeprops={'edgecolor':'white','linewidth':2},
            textprops={'fontsize':11})
axes[0].set_title('توزیع کلی', fontsize=12)

# Grouped bar
lv = events.pivot_table(index='level', columns='category', values='ts', aggfunc='count', fill_value=0)
x = np.arange(len(lv.index))
w = 0.25
for i, c in enumerate(['REVERSAL','DIVERGENCE','PASS_THROUGH']):
    axes[1].bar(x + (i-1)*w, lv[c].values, w, label=CAT_LABELS_FA[c], color=CAT_COLORS[c])
axes[1].set_xticks(x); axes[1].set_xticklabels(['سطح ۴۰\n(اشباع فروش)','سطح ۶۰\n(اشباع خرید)'], fontsize=11)
axes[1].set_ylabel('تعداد رویدادها')
axes[1].set_title('بر اساس سطح', fontsize=12)
axes[1].legend(fontsize=10, loc='upper right')
axes[1].grid(True, axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart1_distribution.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart1_distribution.png regenerated with Vazirmatn")

# Chart 2: yearly
events['year'] = events['ts'].dt.year
yr = events.pivot_table(index='year', columns='category', values='ts', aggfunc='count', fill_value=0)

fig, ax = plt.subplots(figsize=(10, 4.5))
x = np.arange(len(yr.index))
w = 0.25
for i, c in enumerate(['REVERSAL','DIVERGENCE','PASS_THROUGH']):
    ax.bar(x + (i-1)*w, yr[c].values, w, label=CAT_LABELS_FA[c], color=CAT_COLORS[c])
ax.set_xticks(x); ax.set_xticklabels(yr.index, fontsize=11)
ax.set_ylabel('تعداد رویدادها')
ax.set_title('رویدادها بر اساس سال', fontsize=13, fontweight='bold', pad=15)
ax.legend(fontsize=11)
for i, year in enumerate(yr.index):
    total = yr.loc[year].sum()
    ax.text(i, total + 5, f"n={total}", ha='center', fontsize=10, fontweight='bold')
ax.grid(True, axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart2_by_year.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart2_by_year.png regenerated with Vazirmatn")

# Chart 3: candles in zone (Persian)
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('مدت زمان حضور در زون (تعداد کندل) بر اساس دسته — قوی‌ترین پیش‌بینی‌کننده (F=20.13, p<0.001)',
             fontsize=12, fontweight='bold')

e60 = events[events['level']==60]
data60 = [e60[e60['category']==c]['candles_in_zone'].dropna().values for c in ['REVERSAL','DIVERGENCE','PASS_THROUGH']]
bp = axes[0].boxplot(data60, tick_labels=['برگشت','واگرایی','گذشتن'],
                      patch_artist=True, showfliers=False, widths=0.6)
for patch, c in zip(bp['boxes'], ['REVERSAL','DIVERGENCE','PASS_THROUGH']):
    patch.set_facecolor(CAT_COLORS[c]); patch.set_alpha(0.7)
axes[0].set_title('سطح ۶۰ (اشباع خرید)', fontsize=12)
axes[0].set_ylabel('تعداد کندل در زون')
axes[0].set_ylim(0, 25)
for i, d in enumerate(data60):
    if len(d):
        axes[0].scatter(i+1, np.mean(d), marker='D', color='black', s=40, zorder=5)
        axes[0].text(i+1, np.mean(d)+0.6, f"μ={np.mean(d):.1f}", ha='center', fontsize=10)

e40 = events[events['level']==40]
data40 = [e40[e40['category']==c]['candles_in_zone'].dropna().values for c in ['REVERSAL','DIVERGENCE','PASS_THROUGH']]
bp = axes[1].boxplot(data40, tick_labels=['برگشت','واگرایی','گذشتن'],
                      patch_artist=True, showfliers=False, widths=0.6)
for patch, c in zip(bp['boxes'], ['REVERSAL','DIVERGENCE','PASS_THROUGH']):
    patch.set_facecolor(CAT_COLORS[c]); patch.set_alpha(0.7)
axes[1].set_title('سطح ۴۰ (اشباع فروش)', fontsize=12)
axes[1].set_ylabel('تعداد کندل در زون')
axes[1].set_ylim(0, 25)
for i, d in enumerate(data40):
    if len(d):
        axes[1].scatter(i+1, np.mean(d), marker='D', color='black', s=40, zorder=5)
        axes[1].text(i+1, np.mean(d)+0.6, f"μ={np.mean(d):.1f}", ha='center', fontsize=10)

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart3_candles_in_zone.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart3_candles_in_zone.png regenerated with Vazirmatn")

# Chart 4: feature heatmap with Persian labels
features = ['rsi_velocity_10','rsi_velocity_5','price_slope_20','trend_50_pct',
            'avg_vol_20','vol_ratio_5_20','dist_sma50_pct','candles_in_zone',
            'favorable_pct','adverse_pct','max_excursion_rsi']
feat_labels_fa = ['سرعت RSI (۱۰)','سرعت RSI (۵)','شیب قیمت (۲۰)','روند٪ (۵۰)',
               'حجم متوسط (۲۰)','نسبت حجم ۵/۲۰','فاصله از SMA50٪','کندل در زون',
               'حرکت مطلوب٪','حرکت نامطلوب٪','حداکثر جهش RSI']

means = events.groupby('category')[features].mean()
norm = means.copy()
for col in features:
    col_min, col_max = means[col].min(), means[col].max()
    if col_max > col_min:
        norm[col] = (means[col] - col_min) / (col_max - col_min)
    else:
        norm[col] = 0.5

fig, ax = plt.subplots(figsize=(10, 5))
data = norm.T.reindex(['REVERSAL','DIVERGENCE','PASS_THROUGH']).T
im = ax.imshow(data.values, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=1)
ax.set_xticks(range(3)); ax.set_xticklabels(['برگشت','واگرایی','گذشتن'], fontsize=11)
ax.set_yticks(range(len(features))); ax.set_yticklabels(feat_labels_fa, fontsize=10)
for i, f in enumerate(features):
    for j, c in enumerate(['REVERSAL','DIVERGENCE','PASS_THROUGH']):
        v = means.loc[c, f]
        ax.text(j, i, f"{v:.2f}", ha='center', va='center', fontsize=9,
                color='white' if abs(norm.loc[c, f]-0.5) > 0.4 else 'black')
ax.set_title('میانگین ویژگی‌ها بر اساس دسته  (رنگ = نرمال‌شده)', fontsize=12, fontweight='bold', pad=15)
cbar = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.04)
cbar.set_label('نرمال‌شده (min=0, max=1)', fontsize=10)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart4_feature_heatmap.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart4_feature_heatmap.png regenerated with Vazirmatn")

# Chart 6: RSI velocity (Persian)
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('سرعت RSI (تغییر در ۱۰ کندل) بر اساس دسته', fontsize=12, fontweight='bold')

e60 = events[events['level']==60]
data60 = [e60[e60['category']==c]['rsi_velocity_10'].dropna().values for c in ['REVERSAL','DIVERGENCE','PASS_THROUGH']]
bp = axes[0].boxplot(data60, tick_labels=['برگشت','واگرایی','گذشتن'],
                      patch_artist=True, showfliers=False, widths=0.6)
for patch, c in zip(bp['boxes'], ['REVERSAL','DIVERGENCE','PASS_THROUGH']):
    patch.set_facecolor(CAT_COLORS[c]); patch.set_alpha(0.7)
axes[0].set_title('سطح ۶۰ (RSI صعودی به زون)', fontsize=12)
axes[0].set_ylabel('سرعت RSI (۱۰ کندل)')
axes[0].axhline(0, color='gray', linestyle='--', alpha=0.5)
for i, d in enumerate(data60):
    if len(d):
        axes[0].text(i+1, max(d)*0.95, f"μ={np.mean(d):.2f}", ha='center', fontsize=10)

e40 = events[events['level']==40]
data40 = [e40[e40['category']==c]['rsi_velocity_10'].dropna().values for c in ['REVERSAL','DIVERGENCE','PASS_THROUGH']]
bp = axes[1].boxplot(data40, tick_labels=['برگشت','واگرایی','گذشتن'],
                      patch_artist=True, showfliers=False, widths=0.6)
for patch, c in zip(bp['boxes'], ['REVERSAL','DIVERGENCE','PASS_THROUGH']):
    patch.set_facecolor(CAT_COLORS[c]); patch.set_alpha(0.7)
axes[1].set_title('سطح ۴۰ (RSI نزولی به زون)', fontsize=12)
axes[1].set_ylabel('سرعت RSI (۱۰ کندل)')
axes[1].axhline(0, color='gray', linestyle='--', alpha=0.5)
for i, d in enumerate(data40):
    if len(d):
        axes[1].text(i+1, min(d)*0.95, f"μ={np.mean(d):.2f}", ha='center', fontsize=10)

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart6_rsi_velocity.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart6_rsi_velocity.png regenerated with Vazirmatn")

# Chart 8: outcome magnitude (Persian)
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('حرکت قیمت بعد از برخورد (پنجره ۱۵ ساعته)', fontsize=12, fontweight='bold')

for ax, level, title in [(axes[0], 60, 'سطح ۶۰ (اشباع خرید — مطلوب = صعود)'),
                          (axes[1], 40, 'سطح ۴۰ (اشباع فروش — مطلوب = نزول)')]:
    elv = events[events['level']==level]
    cats = ['REVERSAL','DIVERGENCE','PASS_THROUGH']
    fav = [elv[elv['category']==c]['favorable_pct'].median() for c in cats]
    adv = [elv[elv['category']==c]['adverse_pct'].median() for c in cats]
    x = np.arange(3)
    w = 0.35
    ax.bar(x - w/2, fav, w, label='مطلوب٪ (میانه)', color='#27ae60', alpha=0.8)
    ax.bar(x + w/2, adv, w, label='نامطلوب٪ (میانه)', color='#e74c3c', alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(['برگشت','واگرایی','گذشتن'], fontsize=11)
    ax.set_title(title, fontsize=12); ax.set_ylabel('٪ حرکت قیمت')
    ax.legend(fontsize=10)
    ax.grid(True, axis='y', alpha=0.3)
    for i, (f, a) in enumerate(zip(fav, adv)):
        ax.text(i - w/2, f + 0.05, f"{f:.2f}%", ha='center', fontsize=9)
        ax.text(i + w/2, a + 0.05, f"{a:.2f}%", ha='center', fontsize=9)

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/chart8_outcome_magnitude.png", dpi=130, bbox_inches='tight')
plt.close()
print("✓ chart8_outcome_magnitude.png regenerated with Vazirmatn")

print("\nAll charts regenerated with Vazirmatn font.")
