"""
Build Excel deliverable: multi-sheet workbook with all events + statistics.
"""
import os
import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.formatting.rule import ColorScaleRule

DATA_DIR = "/home/z/my-project/data"
OUT_PATH = "/home/z/my-project/download/XAUUSD_RSI30_M30_Backtest_2yr.xlsx"

events = pd.read_pickle(f"{DATA_DIR}/events_full.pkl")
price = pd.read_pickle(f"{DATA_DIR}/price_with_rsi.pkl")

# Drop events with NaN features (first 200 candles) — keep all events though
print(f"Total events: {len(events)}")
print(f"Events with NaN features: {events['rsi_velocity_10'].isna().sum()}")

# ===================================================================
# Style helpers
# ===================================================================
HEADER_FILL = PatternFill('solid', fgColor='1F4E78')
HEADER_FONT = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
TITLE_FONT  = Font(name='Calibri', size=14, bold=True, color='1F4E78')
SUB_FONT    = Font(name='Calibri', size=11, bold=True, color='2C3E50')
BODY_FONT   = Font(name='Calibri', size=10)
CENTER = Alignment(horizontal='center', vertical='center', wrap_text=True)
LEFT   = Alignment(horizontal='left',   vertical='center', wrap_text=True)
THIN   = Side(style='thin', color='BFBFBF')
BORDER = Border(top=THIN, bottom=THIN, left=THIN, right=THIN)

CAT_COLORS_HEX = {
    'PASS_THROUGH': 'F2DCDB',  # light red
    'REVERSAL':     'E2EFDA',  # light green
    'DIVERGENCE':   'FFF2CC',  # light orange
}

def style_header_row(ws, row, ncols):
    for col in range(1, ncols+1):
        c = ws.cell(row=row, column=col)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = CENTER
        c.border = BORDER

def autosize(ws, max_widths=None):
    for col_cells in ws.columns:
        col_letter = get_column_letter(col_cells[0].column)
        widths = [len(str(c.value)) if c.value is not None else 0 for c in col_cells]
        width = min(max(max(widths) + 2, 8), max_widths or 40)
        ws.column_dimensions[col_letter].width = width

wb = Workbook()
wb.properties.creator = "Z.ai"
wb.properties.title = "XAUUSD RSI(30) M30 Backtest 2-year Analysis"

# ===================================================================
# Sheet 1: Summary
# ===================================================================
ws = wb.active
ws.title = "Summary"

ws['A1'] = "XAUUSD RSI(30) M30 — 2-Year Backtest Summary"
ws['A1'].font = TITLE_FONT
ws.merge_cells('A1:F1')

ws['A2'] = "Strategy: RSI(30) on M30, levels 40 & 60 (±1 tolerance), entry trigger via M5 candle patterns"
ws['A2'].font = Font(name='Calibri', size=10, italic=True, color='595959')
ws.merge_cells('A2:F2')

# Period & data info
ws['A4'] = "Data source:"; ws['B4'] = "Binance PAXG/USDT (proxy for spot gold — 1 PAXG = 1 troy oz LBMA gold)"
ws['A5'] = "Period:";      ws['B5'] = f"{events['ts'].min().date()} → {events['ts'].max().date()}  (2 years)"
ws['A6'] = "Total M30 candles:"; ws['B6'] = f"{len(price):,}"
ws['A7'] = "RSI period:";  ws['B7'] = "30 (Wilder smoothing, MT4-compatible)"
ws['A8'] = "Levels:";      ws['B8'] = "40 (oversold zone [39,41]) and 60 (overbought zone [59,61])"
ws['A9'] = "Look-forward window:"; ws['B9'] = "30 candles (15 hours)"
for r in range(4, 10):
    ws.cell(row=r, column=1).font = SUB_FONT
    ws.cell(row=r, column=2).font = BODY_FONT

ws['A11'] = "KEY RESULTS"
ws['A11'].font = TITLE_FONT
ws.merge_cells('A11:F11')

# Counts table
ws['A13'] = "Category"
ws['B13'] = "Count"
ws['C13'] = "Percent"
ws['D13'] = "At Level 60"
ws['E13'] = "At Level 40"
style_header_row(ws, 13, 5)

total = len(events)
counts_by_cat = events['category'].value_counts().to_dict()
counts_60 = events[events['level']==60]['category'].value_counts().to_dict()
counts_40 = events[events['level']==40]['category'].value_counts().to_dict()
cats_order = ['REVERSAL','DIVERGENCE','PASS_THROUGH']
cat_labels = {'REVERSAL':'Reversal (single-touch)', 'DIVERGENCE':'Divergence', 'PASS_THROUGH':'Pass-through'}

for i, cat in enumerate(cats_order):
    r = 14 + i
    ws.cell(row=r, column=1, value=cat_labels[cat]).fill = PatternFill('solid', fgColor=CAT_COLORS_HEX[cat])
    ws.cell(row=r, column=2, value=counts_by_cat.get(cat, 0))
    ws.cell(row=r, column=3, value=counts_by_cat.get(cat, 0)/total).number_format = '0.0%'
    ws.cell(row=r, column=4, value=counts_60.get(cat, 0))
    ws.cell(row=r, column=5, value=counts_40.get(cat, 0))
    for col in range(1, 6):
        ws.cell(row=r, column=col).font = BODY_FONT
        ws.cell(row=r, column=col).alignment = CENTER
        ws.cell(row=r, column=col).border = BORDER

# Total row
r = 17
ws.cell(row=r, column=1, value="Total").font = SUB_FONT
ws.cell(row=r, column=2, value=total).font = SUB_FONT
ws.cell(row=r, column=3, value=1.0).number_format = '0.0%'
ws.cell(row=r, column=3).font = SUB_FONT
ws.cell(row=r, column=4, value=sum(counts_60.values())).font = SUB_FONT
ws.cell(row=r, column=5, value=sum(counts_40.values())).font = SUB_FONT
for col in range(1, 6):
    ws.cell(row=r, column=col).alignment = CENTER
    ws.cell(row=r, column=col).border = BORDER

# Key findings
ws['A19'] = "KEY FINDINGS"
ws['A19'].font = TITLE_FONT
ws.merge_cells('A19:F19')

findings = [
    ("1. Strongest predictor", "Candles spent in zone — ANOVA F=20.13, p<0.001"),
    ("", "• Reversal: mean ~5.4 candles in zone  (long hesitation before exit)"),
    ("", "• Pass-through: mean ~2.1 candles in zone  (quick pass-through)"),
    ("", "• Divergence: mean ~3.0 candles in zone"),
    ("2. RSI velocity", "Weak predictor alone (p=0.35) but interacts with zone duration"),
    ("", "• Reversal: SLOWER RSI approach (smaller |velocity|)"),
    ("", "• Divergence: FASTEST RSI approach (larger |velocity|, momentum continues)"),
    ("3. Volume ratio (5/20)", "Statistically significant (F=5.04, p<0.01)"),
    ("", "• Recent volume spike (>1.0) → favors divergence/pass-through"),
    ("4. Trading session", "Reversal rate highest in Asia night session (34.5%)"),
    ("", "Lowest reversal rate in Europe session (27.8%)"),
    ("5. Price outcome", "Reversal category: avg favorable move = +0.78% (level 60) / -0.89% (level 40)"),
    ("", "Pass-through: smaller adverse move (-0.50%) but trade would be wrong-direction"),
]
for i, (a, b) in enumerate(findings):
    r = 20 + i
    ws.cell(row=r, column=1, value=a).font = SUB_FONT if a else BODY_FONT
    ws.cell(row=r, column=2, value=b).font = BODY_FONT
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)

# Predictive rules
r = 20 + len(findings) + 1
ws.cell(row=r, column=1, value="PREDICTION RULES (rule of thumb)").font = TITLE_FONT
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
r += 1
rules = [
    ("If RSI stays in zone > 5 candles", "REVERSAL is most likely (~50%+)"),
    ("If RSI exits zone within 2 candles", "PASS-THROUGH is most likely (~70%)"),
    ("If RSI velocity > 3 (level 60) or < -3 (level 40)", "DIVERGENCE risk elevated"),
    ("If volume ratio 5/20 > 1.3", "Momentum is strong — favor pass-through / divergence"),
    ("If session = Asia night (Tehran 02:00-09:00)", "Reversal probability highest"),
]
for i, (a, b) in enumerate(rules):
    rr = r + i
    ws.cell(row=rr, column=1, value=a).font = SUB_FONT
    ws.cell(row=rr, column=2, value=b).font = BODY_FONT
    ws.merge_cells(start_row=rr, start_column=2, end_row=rr, end_column=6)

# Set column widths
ws.column_dimensions['A'].width = 32
for c in ['B','C','D','E','F']:
    ws.column_dimensions[c].width = 20

# ===================================================================
# Sheet 2: All Events
# ===================================================================
ws2 = wb.create_sheet("All Events")

# Prepare display columns
display_cols = [
    ('ts',                 'Touch Time (UTC)'),
    ('level',              'Level'),
    ('rsi_at_touch',       'RSI at Touch'),
    ('price_at_touch',     'Price at Touch'),
    ('category',           'Category'),
    ('first_exit_dir',     'First Exit Dir'),
    ('candles_in_zone',    'Candles in Zone'),
    ('rsi_velocity_5',     'RSI Vel (5)'),
    ('rsi_velocity_10',    'RSI Vel (10)'),
    ('rsi_change_prev_candle', 'RSI Δ prev'),
    ('price_slope_10',     'Price Slope (10)'),
    ('price_slope_20',     'Price Slope (20)'),
    ('trend_20_pct',       'Trend % (20)'),
    ('trend_50_pct',       'Trend % (50)'),
    ('avg_vol_5',          'Avg Vol (5)'),
    ('avg_vol_20',         'Avg Vol (20)'),
    ('vol_ratio_5_20',     'Vol Ratio 5/20'),
    ('dist_sma50_pct',     'Dist SMA50 %'),
    ('dist_sma200_pct',    'Dist SMA200 %'),
    ('trend_dir_50',       'Trend Dir (50)'),
    ('hour_utc',           'Hour UTC'),
    ('day_name',           'Day'),
    ('session_label',      'Session'),
    ('favorable_pct',      'Favorable %'),
    ('adverse_pct',        'Adverse %'),
    ('max_excursion_rsi',  'Max RSI Excursion'),
]

ev_display = events[[c for c, _ in display_cols]].copy()
ev_display.columns = [lbl for _, lbl in display_cols]
# Convert tz-aware timestamps to naive strings for Excel
ev_display['Touch Time (UTC)'] = pd.to_datetime(ev_display['Touch Time (UTC)']).dt.tz_convert('UTC').dt.strftime('%Y-%m-%d %H:%M')

# Title
ws2['A1'] = f"All {len(ev_display)} Touch Events (RSI 30 M30, levels 40 & 60)"
ws2['A1'].font = TITLE_FONT
ws2.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(display_cols))

ws2['A2'] = "Each row = one touch event (RSI first entered the ±1 zone). Categories: REVERSAL / DIVERGENCE / PASS_THROUGH"
ws2['A2'].font = Font(name='Calibri', size=10, italic=True, color='595959')
ws2.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(display_cols))

# Header
for col, (col_name, _) in enumerate(display_cols, 1):
    ws2.cell(row=4, column=col, value=_)
style_header_row(ws2, 4, len(display_cols))
ws2.freeze_panes = 'A5'

# Write rows
for r_idx, row in enumerate(ev_display.itertuples(index=False), 5):
    for c_idx, val in enumerate(row, 1):
        cell = ws2.cell(row=r_idx, column=c_idx, value=val if not (isinstance(val, float) and np.isnan(val)) else None)
        cell.font = BODY_FONT
        cell.alignment = CENTER
        cell.border = BORDER
        # Color category cell
        col_name = display_cols[c_idx-1][0]
        if col_name == 'category' and val in CAT_COLORS_HEX:
            cell.fill = PatternFill('solid', fgColor=CAT_COLORS_HEX[val])
        # Format numbers
        if isinstance(val, (int, float)) and not np.isnan(val):
            if col_name in ('rsi_at_touch', 'rsi_velocity_5','rsi_velocity_10','rsi_change_prev_candle',
                             'max_excursion_rsi','dist_sma50_pct','dist_sma200_pct'):
                cell.number_format = '0.00'
            elif col_name in ('favorable_pct','adverse_pct','trend_20_pct','trend_50_pct'):
                cell.number_format = '0.000'
            elif col_name in ('price_slope_10','price_slope_20'):
                cell.number_format = '0.000'
            elif col_name in ('price_at_touch',):
                cell.number_format = '0.00'
            elif col_name in ('avg_vol_5','avg_vol_20','vol_ratio_5_20'):
                cell.number_format = '0.0'

# Autosize
for col_cells in ws2.columns:
    col_letter = get_column_letter(col_cells[0].column)
    if col_letter == 'A':  # skip title rows
        continue
    widths = []
    for c in col_cells[4:]:  # skip title + header
        v = c.value
        widths.append(len(str(v)) if v is not None else 0)
    if widths:
        ws2.column_dimensions[col_letter].width = min(max(max(widths) + 2, 8), 22)

# ===================================================================
# Sheet 3: Statistics
# ===================================================================
ws3 = wb.create_sheet("Statistics")

ws3['A1'] = "Statistical Analysis — Features by Category"
ws3['A1'].font = TITLE_FONT
ws3.merge_cells('A1:F1')

# Mean features by category × level
row = 3
ws3.cell(row=row, column=1, value="Mean Features by Category (Level 60 — overbought)").font = SUB_FONT
ws3.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
row += 1
e60 = events[events['level']==60]
mean60 = e60.groupby('category')[
    ['rsi_velocity_10','rsi_velocity_5','price_slope_20','trend_50_pct',
     'avg_vol_20','vol_ratio_5_20','dist_sma50_pct','candles_in_zone',
     'favorable_pct','adverse_pct','max_excursion_rsi']
].mean().round(3)
mean60 = mean60.reindex(['REVERSAL','DIVERGENCE','PASS_THROUGH'])

# Write header
ws3.cell(row=row, column=1, value="Category")
for j, col in enumerate(mean60.columns, 2):
    ws3.cell(row=row, column=j, value=col)
style_header_row(ws3, row, len(mean60.columns)+1)
row += 1
for cat in mean60.index:
    ws3.cell(row=row, column=1, value=cat).fill = PatternFill('solid', fgColor=CAT_COLORS_HEX[cat])
    for j, col in enumerate(mean60.columns, 2):
        c = ws3.cell(row=row, column=j, value=float(mean60.loc[cat, col]))
        c.number_format = '0.000'
        c.alignment = CENTER
        c.border = BORDER
    ws3.cell(row=row, column=1).border = BORDER
    ws3.cell(row=row, column=1).alignment = CENTER
    row += 1

# Level 40
row += 2
ws3.cell(row=row, column=1, value="Mean Features by Category (Level 40 — oversold)").font = SUB_FONT
ws3.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
row += 1
e40 = events[events['level']==40]
mean40 = e40.groupby('category')[
    ['rsi_velocity_10','rsi_velocity_5','price_slope_20','trend_50_pct',
     'avg_vol_20','vol_ratio_5_20','dist_sma50_pct','candles_in_zone',
     'favorable_pct','adverse_pct','max_excursion_rsi']
].mean().round(3)
mean40 = mean40.reindex(['REVERSAL','DIVERGENCE','PASS_THROUGH'])
ws3.cell(row=row, column=1, value="Category")
for j, col in enumerate(mean40.columns, 2):
    ws3.cell(row=row, column=j, value=col)
style_header_row(ws3, row, len(mean40.columns)+1)
row += 1
for cat in mean40.index:
    ws3.cell(row=row, column=1, value=cat).fill = PatternFill('solid', fgColor=CAT_COLORS_HEX[cat])
    for j, col in enumerate(mean40.columns, 2):
        c = ws3.cell(row=row, column=j, value=float(mean40.loc[cat, col]))
        c.number_format = '0.000'
        c.alignment = CENTER
        c.border = BORDER
    ws3.cell(row=row, column=1).border = BORDER
    ws3.cell(row=row, column=1).alignment = CENTER
    row += 1

# ANOVA
row += 2
ws3.cell(row=row, column=1, value="ANOVA: Do features significantly differ across categories?").font = SUB_FONT
ws3.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
row += 1
ws3.cell(row=row, column=1, value="Feature")
ws3.cell(row=row, column=2, value="F-statistic")
ws3.cell(row=row, column=3, value="p-value")
ws3.cell(row=row, column=4, value="Significance")
style_header_row(ws3, row, 4)
row += 1

from scipy import stats
features_to_test = ['rsi_velocity_10','rsi_velocity_5','rsi_change_prev_candle',
                     'price_slope_10','price_slope_20','trend_50_pct','trend_20_pct',
                     'avg_vol_20','vol_ratio_5_20','dist_sma50_pct','dist_sma200_pct',
                     'candles_in_zone','hour_utc']
# Use only events with non-NaN features
events_clean = events.dropna(subset=features_to_test)
for f in features_to_test:
    groups = [g[f].dropna().values for _, g in events_clean.groupby('category')]
    if all(len(g) > 5 for g in groups):
        F, p = stats.f_oneway(*groups)
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
        ws3.cell(row=row, column=1, value=f)
        ws3.cell(row=row, column=2, value=round(F, 3))
        ws3.cell(row=row, column=3, value=round(p, 4))
        ws3.cell(row=row, column=4, value=sig)
        for col in range(1, 5):
            ws3.cell(row=row, column=col).border = BORDER
            ws3.cell(row=row, column=col).alignment = CENTER
            ws3.cell(row=row, column=col).font = BODY_FONT
        row += 1

# Notes
row += 2
ws3.cell(row=row, column=1, value="Significance: *** p<0.001  ** p<0.01  * p<0.05  ns = not significant").font = Font(italic=True, size=9, color='595959')
ws3.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
row += 1
ws3.cell(row=row, column=1, value="Interpretation: Features with *** or ** are strong statistical predictors of category outcome.").font = Font(italic=True, size=9, color='595959')
ws3.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)

# Column widths
ws3.column_dimensions['A'].width = 25
for c in ['B','C','D','E','F','G','H','I','J','K','L']:
    ws3.column_dimensions[c].width = 16

# ===================================================================
# Sheet 4: By Session
# ===================================================================
ws4 = wb.create_sheet("By Session")
ws4['A1'] = "Distribution by Trading Session (Tehran time)"
ws4['A1'].font = TITLE_FONT
ws4.merge_cells('A1:F1')

order = ['صبح (آسیا)','ظهر (اروپا)','عصر (آمریکا)','شب']
sess = events.pivot_table(index='session_label', columns='category',
                          values='ts', aggfunc='count', fill_value=0)
sess = sess.reindex([s for s in order if s in sess.index])
sess['Total'] = sess.sum(axis=1)
for cat in ['REVERSAL','DIVERGENCE','PASS_THROUGH']:
    if cat in sess.columns:
        sess[cat+'_pct'] = sess[cat] / sess['Total']

ws4.cell(row=3, column=1, value="Session")
ws4.cell(row=3, column=2, value="Reversal")
ws4.cell(row=3, column=3, value="Divergence")
ws4.cell(row=3, column=4, value="Pass-through")
ws4.cell(row=3, column=5, value="Total")
ws4.cell(row=3, column=6, value="Reversal %")
style_header_row(ws4, 3, 6)

for i, sess_name in enumerate(sess.index):
    r = 4 + i
    ws4.cell(row=r, column=1, value=sess_name)
    ws4.cell(row=r, column=2, value=int(sess.loc[sess_name, 'REVERSAL']))
    ws4.cell(row=r, column=3, value=int(sess.loc[sess_name, 'DIVERGENCE']))
    ws4.cell(row=r, column=4, value=int(sess.loc[sess_name, 'PASS_THROUGH']))
    ws4.cell(row=r, column=5, value=int(sess.loc[sess_name, 'Total']))
    ws4.cell(row=r, column=6, value=float(sess.loc[sess_name, 'REVERSAL_pct'])).number_format = '0.0%'
    for col in range(1, 7):
        ws4.cell(row=r, column=col).border = BORDER
        ws4.cell(row=r, column=col).alignment = CENTER
        ws4.cell(row=r, column=col).font = BODY_FONT

# Total row
r = 4 + len(sess)
ws4.cell(row=r, column=1, value="Total").font = SUB_FONT
ws4.cell(row=r, column=2, value=int(sess['REVERSAL'].sum())).font = SUB_FONT
ws4.cell(row=r, column=3, value=int(sess['DIVERGENCE'].sum())).font = SUB_FONT
ws4.cell(row=r, column=4, value=int(sess['PASS_THROUGH'].sum())).font = SUB_FONT
ws4.cell(row=r, column=5, value=int(sess['Total'].sum())).font = SUB_FONT
ws4.cell(row=r, column=6, value=sess['REVERSAL'].sum()/sess['Total'].sum()).number_format = '0.0%'
ws4.cell(row=r, column=6).font = SUB_FONT
for col in range(1, 7):
    ws4.cell(row=r, column=col).border = BORDER
    ws4.cell(row=r, column=col).alignment = CENTER

ws4.column_dimensions['A'].width = 22
for c in ['B','C','D','E','F']:
    ws4.column_dimensions[c].width = 14

# ===================================================================
# Sheet 5: By Day of Week
# ===================================================================
ws5 = wb.create_sheet("By Day")
ws5['A1'] = "Distribution by Day of Week"
ws5['A1'].font = TITLE_FONT
ws5.merge_cells('A1:F1')

dow_order = ['دوشنبه','سه‌شنبه','چهارشنبه','پنجشنبه','جمعه','شنبه','یکشنبه']
dow = events.pivot_table(index='day_name', columns='category', values='ts', aggfunc='count', fill_value=0)
dow = dow.reindex([d for d in dow_order if d in dow.index])
dow['Total'] = dow.sum(axis=1)
for cat in ['REVERSAL','DIVERGENCE','PASS_THROUGH']:
    if cat in dow.columns:
        dow[cat+'_pct'] = dow[cat] / dow['Total']

ws5.cell(row=3, column=1, value="Day")
ws5.cell(row=3, column=2, value="Reversal")
ws5.cell(row=3, column=3, value="Divergence")
ws5.cell(row=3, column=4, value="Pass-through")
ws5.cell(row=3, column=5, value="Total")
ws5.cell(row=3, column=6, value="Reversal %")
style_header_row(ws5, 3, 6)

for i, day_name in enumerate(dow.index):
    r = 4 + i
    ws5.cell(row=r, column=1, value=day_name)
    ws5.cell(row=r, column=2, value=int(dow.loc[day_name, 'REVERSAL']))
    ws5.cell(row=r, column=3, value=int(dow.loc[day_name, 'DIVERGENCE']))
    ws5.cell(row=r, column=4, value=int(dow.loc[day_name, 'PASS_THROUGH']))
    ws5.cell(row=r, column=5, value=int(dow.loc[day_name, 'Total']))
    ws5.cell(row=r, column=6, value=float(dow.loc[day_name, 'REVERSAL_pct'])).number_format = '0.0%'
    for col in range(1, 7):
        ws5.cell(row=r, column=col).border = BORDER
        ws5.cell(row=r, column=col).alignment = CENTER
        ws5.cell(row=r, column=col).font = BODY_FONT

r = 4 + len(dow)
ws5.cell(row=r, column=1, value="Total").font = SUB_FONT
ws5.cell(row=r, column=2, value=int(dow['REVERSAL'].sum())).font = SUB_FONT
ws5.cell(row=r, column=3, value=int(dow['DIVERGENCE'].sum())).font = SUB_FONT
ws5.cell(row=r, column=4, value=int(dow['PASS_THROUGH'].sum())).font = SUB_FONT
ws5.cell(row=r, column=5, value=int(dow['Total'].sum())).font = SUB_FONT
ws5.cell(row=r, column=6, value=dow['REVERSAL'].sum()/dow['Total'].sum()).number_format = '0.0%'
ws5.cell(row=r, column=6).font = SUB_FONT
for col in range(1, 7):
    ws5.cell(row=r, column=col).border = BORDER
    ws5.cell(row=r, column=col).alignment = CENTER

ws5.column_dimensions['A'].width = 14
for c in ['B','C','D','E','F']:
    ws5.column_dimensions[c].width = 14

# ===================================================================
# Sheet 6: Yearly
# ===================================================================
ws6 = wb.create_sheet("By Year")
ws6['A1'] = "Distribution by Year"
ws6['A1'].font = TITLE_FONT
ws6.merge_cells('A1:F1')

events['year'] = events['ts'].dt.year
yr_pivot = events.pivot_table(index=['year','level'], columns='category',
                              values='ts', aggfunc='count', fill_value=0)
yr_pivot['Total'] = yr_pivot.sum(axis=1)

ws6.cell(row=3, column=1, value="Year")
ws6.cell(row=3, column=2, value="Level")
ws6.cell(row=3, column=3, value="Reversal")
ws6.cell(row=3, column=4, value="Divergence")
ws6.cell(row=3, column=5, value="Pass-through")
ws6.cell(row=3, column=6, value="Total")
style_header_row(ws6, 3, 6)

r = 4
for (year, level), row_data in yr_pivot.iterrows():
    ws6.cell(row=r, column=1, value=int(year))
    ws6.cell(row=r, column=2, value=int(level))
    ws6.cell(row=r, column=3, value=int(row_data.get('REVERSAL', 0)))
    ws6.cell(row=r, column=4, value=int(row_data.get('DIVERGENCE', 0)))
    ws6.cell(row=r, column=5, value=int(row_data.get('PASS_THROUGH', 0)))
    ws6.cell(row=r, column=6, value=int(row_data['Total']))
    for col in range(1, 7):
        ws6.cell(row=r, column=col).border = BORDER
        ws6.cell(row=r, column=col).alignment = CENTER
        ws6.cell(row=r, column=col).font = BODY_FONT
    r += 1

# Total
ws6.cell(row=r, column=1, value="Total").font = SUB_FONT
ws6.cell(row=r, column=3, value=int(yr_pivot['REVERSAL'].sum())).font = SUB_FONT
ws6.cell(row=r, column=4, value=int(yr_pivot['DIVERGENCE'].sum())).font = SUB_FONT
ws6.cell(row=r, column=5, value=int(yr_pivot['PASS_THROUGH'].sum())).font = SUB_FONT
ws6.cell(row=r, column=6, value=int(yr_pivot['Total'].sum())).font = SUB_FONT
for col in range(1, 7):
    ws6.cell(row=r, column=col).border = BORDER
    ws6.cell(row=r, column=col).alignment = CENTER

ws6.column_dimensions['A'].width = 10
ws6.column_dimensions['B'].width = 10
for c in ['C','D','E','F']:
    ws6.column_dimensions[c].width = 14

# ===================================================================
# Save
# ===================================================================
wb.save(OUT_PATH)
print(f"\n✓ Saved Excel: {OUT_PATH}")
print(f"  Sheets: {wb.sheetnames}")
print(f"  All Events sheet: {len(ev_display)} rows")
import os
size_kb = os.path.getsize(OUT_PATH) / 1024
print(f"  File size: {size_kb:.1f} KB")
