"""
Build the Persian RTL HTML report → convert to PDF via html2pdf-next.js.
"""
import os, base64, json
import pandas as pd
import numpy as np

DATA_DIR = "/home/z/my-project/data"
DOWNLOAD_DIR = "/home/z/my-project/download"
ASSETS_DIR = f"{DOWNLOAD_DIR}/assets"
HTML_PATH = f"{DOWNLOAD_DIR}/XAUUSD_RSI30_M30_Backtest_2yr.html"
PDF_PATH = f"{DOWNLOAD_DIR}/XAUUSD_RSI30_M30_Backtest_2yr.pdf"

# Load data
events = pd.read_pickle(f"{DATA_DIR}/events_full.pkl")
events['year'] = events['ts'].dt.year

# Compute summary stats
total = len(events)
counts = events['category'].value_counts().to_dict()
counts_60 = events[events['level']==60]['category'].value_counts().to_dict()
counts_40 = events[events['level']==40]['category'].value_counts().to_dict()
e60 = events[events['level']==60]
e40 = events[events['level']==40]

# Mean features per category per level
def mean_for(df, cat, col):
    v = df[df['category']==cat][col].dropna()
    return float(v.mean()) if len(v) else float('nan')

# Yearly pivot
yr_pivot = events.pivot_table(index=['year','level'], columns='category',
                              values='ts', aggfunc='count', fill_value=0)
yr_pivot['Total'] = yr_pivot.sum(axis=1)

# Session pivot
sess_pivot = events.pivot_table(index='session_label', columns='category',
                                values='ts', aggfunc='count', fill_value=0)
sess_order = ['صبح (آسیا)','ظهر (اروپا)','عصر (آمریکا)','شب']
sess_pivot = sess_pivot.reindex([s for s in sess_order if s in sess_pivot.index])
sess_pivot['Total'] = sess_pivot.sum(axis=1)

# Encode fonts as base64 for embedding
def font_face(name, path, weight='normal', style='normal'):
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('ascii')
    return f"""@font-face {{
  font-family: '{name}';
  src: url(data:font/ttf;base64,{b64}) format('truetype');
  font-weight: {weight};
  font-style: {style};
}}"""

font_regular = font_face('Vazirmatn', '/home/z/.fonts/Vazirmatn-Regular.ttf', 'normal')
font_medium  = font_face('Vazirmatn', '/home/z/.fonts/Vazirmatn-Medium.ttf', '500')
font_bold    = font_face('Vazirmatn', '/home/z/.fonts/Vazirmatn-Bold.ttf', 'bold')

# Encode charts as base64 for embedding
def img_b64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')

charts = {
    'dist':       img_b64(f"{ASSETS_DIR}/chart1_distribution.png"),
    'year':       img_b64(f"{ASSETS_DIR}/chart2_by_year.png"),
    'candles':    img_b64(f"{ASSETS_DIR}/chart3_candles_in_zone.png"),
    'heatmap':    img_b64(f"{ASSETS_DIR}/chart4_feature_heatmap.png"),
    'session':    img_b64(f"{ASSETS_DIR}/chart5_by_session.png"),
    'velocity':   img_b64(f"{ASSETS_DIR}/chart6_rsi_velocity.png"),
    'example':    img_b64(f"{ASSETS_DIR}/chart7_example_period.png"),
    'outcome':    img_b64(f"{ASSETS_DIR}/chart8_outcome_magnitude.png"),
}

# Build the HTML
html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<title>تحلیل استراتژی RSI(30) روی طلا — تایم‌فریم M30</title>
<style>
{font_regular}
{font_medium}
{font_bold}

@page {{
  size: A4;
  margin: 18mm 16mm 18mm 16mm;
  @bottom-center {{
    content: "صفحه " counter(page) " از " counter(pages);
    font-family: 'Vazirmatn';
    font-size: 9pt;
    color: #6b7280;
  }}
}}

* {{ box-sizing: border-box; }}
html, body {{
  margin: 0; padding: 0;
  font-family: 'Vazirmatn', 'Tahoma', sans-serif;
  font-size: 11pt;
  line-height: 1.7;
  color: #1f2937;
  background: #ffffff;
}}

h1, h2, h3, h4 {{
  font-family: 'Vazirmatn';
  font-weight: bold;
  color: #0f172a;
  line-height: 1.4;
}}

h1 {{ font-size: 26pt; margin: 0 0 6pt 0; }}
h2 {{ font-size: 18pt; margin: 24pt 0 10pt 0; padding-bottom: 6pt; border-bottom: 2px solid #2563eb; color: #1e40af; }}
h3 {{ font-size: 14pt; margin: 18pt 0 8pt 0; color: #1e3a8a; }}
h4 {{ font-size: 12pt; margin: 12pt 0 6pt 0; color: #334155; }}

p {{ margin: 0 0 10pt 0; text-align: justify; text-justify: inter-word; }}

ul, ol {{ margin: 6pt 0 10pt 0; padding-right: 22pt; }}
li {{ margin: 4pt 0; }}

.cover {{
  page-break-after: always;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 240mm;
  text-align: center;
  background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 60%, #1e293b 100%);
  color: white;
  padding: 30mm 20mm;
  margin: -18mm -16mm;
}}
.cover h1 {{ color: white; font-size: 32pt; margin-bottom: 12pt; line-height: 1.3; }}
.cover .subtitle {{ font-size: 16pt; opacity: 0.92; margin-bottom: 24pt; font-weight: 500; }}
.cover .meta {{ font-size: 11pt; opacity: 0.75; margin-top: 30pt; line-height: 1.9; }}
.cover .badge {{ display: inline-block; padding: 6pt 14pt; border: 1.5pt solid rgba(255,255,255,0.35); border-radius: 999pt; font-size: 10pt; margin: 4pt; }}
.cover .accent-bar {{ width: 80pt; height: 3pt; background: #fbbf24; margin: 16pt auto; }}

.section {{ page-break-inside: avoid; }}

table {{
  width: 100%;
  border-collapse: collapse;
  margin: 10pt 0 14pt 0;
  font-size: 10pt;
}}
table.stats th {{
  background: #1e40af;
  color: white;
  padding: 6pt 8pt;
  text-align: center;
  font-weight: bold;
  border: 1px solid #1e40af;
}}
table.stats td {{
  padding: 5pt 8pt;
  border: 1px solid #cbd5e1;
  text-align: center;
}}
table.stats tr:nth-child(even) td {{ background: #f8fafc; }}
table.stats tr.total td {{ background: #dbeafe; font-weight: bold; }}

.tag {{
  display: inline-block;
  padding: 2pt 8pt;
  border-radius: 4pt;
  font-size: 9pt;
  font-weight: bold;
  color: white;
}}
.tag.reversal    {{ background: #16a34a; }}
.tag.divergence  {{ background: #ea580c; }}
.tag.passthrough {{ background: #dc2626; }}

.chart-block {{
  margin: 12pt 0 16pt 0;
  text-align: center;
  page-break-inside: avoid;
}}
.chart-block img {{
  max-width: 100%;
  height: auto;
  border: 1px solid #e2e8f0;
  border-radius: 4pt;
}}
.chart-block .caption {{
  font-size: 9pt;
  color: #6b7280;
  margin-top: 4pt;
  text-align: center;
}}

.callout {{
  background: #fef3c7;
  border-right: 4pt solid #f59e0b;
  padding: 10pt 14pt;
  margin: 10pt 0;
  border-radius: 4pt;
  font-size: 10pt;
}}
.callout.blue {{
  background: #dbeafe;
  border-right-color: #2563eb;
}}
.callout.green {{
  background: #d1fae5;
  border-right-color: #16a34a;
}}
.callout.red {{
  background: #fee2e2;
  border-right-color: #dc2626;
}}

.kpi-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 10pt;
  margin: 12pt 0;
}}
.kpi {{
  background: #f1f5f9;
  padding: 12pt;
  border-radius: 6pt;
  text-align: center;
  border-top: 3pt solid;
}}
.kpi.reversal    {{ border-top-color: #16a34a; }}
.kpi.divergence  {{ border-top-color: #ea580c; }}
.kpi.passthrough {{ border-top-color: #dc2626; }}
.kpi .num {{ font-size: 22pt; font-weight: bold; display: block; }}
.kpi .label {{ font-size: 9pt; color: #475569; margin-top: 4pt; }}
.kpi .pct {{ font-size: 11pt; color: #1e40af; font-weight: 500; }}

.summary-block {{
  background: #f8fafc;
  border: 1pt solid #e2e8f0;
  border-radius: 6pt;
  padding: 12pt 14pt;
  margin: 8pt 0;
}}
.summary-block h4 {{ margin-top: 0; }}

.rules-list li {{
  margin: 6pt 0;
  padding: 8pt 12pt;
  background: #f1f5f9;
  border-radius: 4pt;
  border-right: 3pt solid #2563eb;
}}

code, .mono {{ font-family: 'Courier New', monospace; direction: ltr; display: inline-block; }}
.formula {{ direction: ltr; text-align: left; background: #f1f5f9; padding: 8pt 12pt; border-radius: 4pt; font-family: monospace; margin: 8pt 0; font-size: 10pt; }}

.toc {{ page-break-after: always; }}
.toc h2 {{ border-bottom: 2px solid #2563eb; padding-bottom: 6pt; }}
.toc ol {{ list-style: none; padding: 0; counter-reset: tocitem; }}
.toc li {{ counter-increment: tocitem; margin: 8pt 0; padding: 6pt 0; border-bottom: 1px dashed #e2e8f0; }}
.toc li::before {{ content: counter(tocitem) ". "; color: #2563eb; font-weight: bold; margin-left: 8pt; }}

</style>
</head>
<body>

<!-- ===================== COVER ===================== -->
<div class="cover">
  <div style="font-size: 13pt; opacity: 0.8; letter-spacing: 3pt;">گزارش تحلیل بک‌تست</div>
  <div class="accent-bar"></div>
  <h1>استراتژی RSI(30) روی طلا<br>در تایم‌فریم M30</h1>
  <div class="subtitle">بررسی دقیق ۲ سال گذشته (نوامبر ۲۰۲۴ تا نوامبر ۲۰۲۶)</div>
  <div style="margin-top: 24pt;">
    <span class="badge">۱٬۳۲۸ رویداد برخورد</span>
    <span class="badge">۲ سال داده</span>
    <span class="badge">۳۵٬۰۴۱ کندل M30</span>
  </div>
  <div class="meta">
    تحلیل آماری و کشف الگوهای پیش‌بینی‌کننده<br>
    برای نوع واکنش بازار در برخورد به سطوح ۴۰ و ۶۰<br>
    <br>
    تهیه شده توسط: Z.ai<br>
    تاریخ گزارش: ۱۴ نوامبر ۲۰۲۶
  </div>
</div>

<!-- ===================== TOC ===================== -->
<div class="toc">
<h2>فهرست مطالب</h2>
<ol>
<li>خلاصه اجرایی</li>
<li>روش‌شناسی و تعاریف</li>
<li>آمار کلی رویدادها</li>
<li>توزیع سالانه رویدادها</li>
<li>قوی‌ترین پیش‌بینی‌کننده: مدت حضور در زون</li>
<li>تحلیل سایر ویژگی‌ها (هیتمپ)</li>
<li>تحلیل سرعت RSI قبل از برخورد</li>
<li>توزیع بر اساس سشن معاملاتی</li>
<li>توزیع بر اساس روز هفته</li>
<li>تحلیل پیامد قیمت بعد از برخورد</li>
<li>قوانین پیش‌بینی و توصیه‌های عملی</li>
<li>نمونه بصری از رویدادها</li>
<li>محدودیت‌ها و نتیجه‌گیری</li>
</ol>
</div>

<!-- ===================== 1. EXEC SUMMARY ===================== -->
<h2>۱. خلاصه اجرایی</h2>

<p>
این گزارش نتایج بک‌تست استراتژی معاملاتی شما را روی داده‌های واقعی بازار طلا در ۲ سال گذشته ارائه می‌دهد. استراتژی بر اساس اندیکاتور RSI با دوره ۳۰ روی تایم‌فریم ۳۰ دقیقه و سطوح ۴۰ و ۶۰ (با تلورانس ±۱ واحد) طراحی شده است. هدف اصلی، شمارش تعداد دفعاتی است که RSI به این سطوح رسیده و دسته‌بندی واکنش بازار به سه حالت: «تک‌برخورد و برگشت»، «واگرایی ساده»، و «گذشتن از سطح».</p>

<p>
در مجموع <strong>۱٬۳۲۸ رویداد برخورد</strong> در ۲ سال گذشته شناسایی شد که به طور میانگین حدود ۱.۸ رویداد در روز رخ می‌دهد. این حجم رویداد نشان می‌دهد استراتژی شما فرصت‌های معاملاتی متعددی تولید می‌کند، اما کیفیت هر فرصت به متغیرهای متعددی بستگی دارد که در این گزارش با آزمون‌های آماری معتبر بررسی شده‌اند.</p>

<div class="kpi-grid">
  <div class="kpi reversal">
    <span class="num">۴۳۷</span>
    <span class="pct">۳۲.۹٪</span>
    <span class="label">برگشت (Reversal)</span>
  </div>
  <div class="kpi divergence">
    <span class="num">۲۷۹</span>
    <span class="pct">۲۱.۰٪</span>
    <span class="label">واگرایی (Divergence)</span>
  </div>
  <div class="kpi passthrough">
    <span class="num">۶۱۲</span>
    <span class="pct">۴۶.۱٪</span>
    <span class="label">گذشتن (Pass-through)</span>
  </div>
</div>

<p>
یافته کلیدی: تنها حدود <strong>یک‌سوم رویدادها (۳۲.۹٪)</strong> منجر به برگشت قیمت در همان برخورد اول می‌شوند — این یعنی استراتژی شما در حدود ۶۷٪ مواقع با «عدم برگشت فوری» روبرو می‌شود (واگرایی یا گذشتن). این بدان معناست که ورود سریع به معامله پس از برخورد به سطح بدون تأییدیه اضافی، احتمالاً در بیش از نیمی از مواقع منجر به ضرر خواهد شد.</p>

<div class="callout blue">
<strong>یافته کلیدی:</strong> قوی‌ترین پیش‌بینی‌کننده نوع واکنش، <em>«تعداد کندل‌هایی که RSI در زون می‌ماند»</em> است (آزمون ANOVA: F=۲۰.۱۳، p&lt;۰.۰۰۱). هرچه RSI بیشتر در زون بماند (بیش از ۵ کندل)، احتمال برگشت بیشتر می‌شود. هرچه سریع‌تر از زون خارج شود (۱-۲ کندل)، احتمال گذشتن به شدت بالا می‌رود.</div>

<p>
علاوه بر این، حجم معاملات اخیر نسبت به میانگین ۲۰ کندلی (نسبت ۵/۲۰) نیز پیش‌بینی‌کننده معناداری است (F=۵.۰۴، p&lt;۰.۰۱). اگر حجم اخیر به وضوح بیشتر از میانگین باشد، احتمال واگرایی یا گذشتن افزایش می‌یابد، چون نشان‌دهنده قدرت روند است.</p>

<!-- ===================== 2. METHODOLOGY ===================== -->
<h2>۲. روش‌شناسی و تعاریف</h2>

<h3>۲.۱ منبع داده</h3>
<p>
داده‌های بازار از Binance برای جفت‌ارز <code>PAXG/USDT</code> در تایم‌فریم ۳۰ دقیقه استخراج شد. PAXG توکن طلای پشتیبان‌شده فیزیکی است که هر واحد آن معادل یک اونس تروی طلای LBMA است و قیمت آن با طلای اسپات (XAUUSD) تطابق بسیار بالایی دارد. در زمان نگارش این گزارش، قیمت PAXG برابر ۳٬۸۸۰ دلار بود که با قیمت طلای نشان داده شده در پلتفرم معاملاتی شما (۳٬۸۸۳ دلار) تطابق دارد.</p>

<div class="callout">
<strong>توجه:</strong> به دلیل محدودیت دسترسی به داده‌های تاریخی XAUUSD اسپات در تایم‌فریم M30 برای بازه ۲ ساله، از PAXG به عنوان جایگزین استفاده شد. این جایگزین معتبر است زیرا:(۱) PAXG به‌طور ۱:۱ با طلای فیزیکی پشتیبان می‌شود؛ (۲) انحراف قیمت آن با طلای اسپات معمولاً کمتر از ۰.۵٪ است؛ (۳) رفتار RSI روی PAXG به دلیل همبستگی بسیار بالا، تقریباً یکسان با RSI روی XAUUSD است.</div>

<h3>۲.۲ پارامترهای استراتژی</h3>
<table class="stats">
<tr><th style="width: 35%;">پارامتر</th><th>مقدار</th></tr>
<tr><td>شاخص</td><td>RSI (Relative Strength Index)</td></tr>
<tr><td>دوره RSI</td><td>۳۰ (فقط RSI(30)، RSI(14) نادیده گرفته شد)</td></tr>
<tr><td>روش محاسبه</td><td>Wilder smoothing (همانند MT4)</td></tr>
<tr><td>قیمت پایه</td><td>Close (قیمت بسته شدن کندل)</td></tr>
<tr><td>تایم‌فریم</td><td>M30 (۳۰ دقیقه)</td></tr>
<tr><td>سطح اشباع خرید</td><td>۶۰ (زون: ۵۹ تا ۶۱ با تلورانس ±۱)</td></tr>
<tr><td>سطح اشباع فروش</td><td>۴۰ (زون: ۳۹ تا ۴۱ با تلورانس ±۱)</td></tr>
<tr><td>پنجره پیش‌رو برای پیامد</td><td>۳۰ کندل (۱۵ ساعت)</td></tr>
<tr><td>بازه زمانی</td><td>۱۷ نوامبر ۲۰۲۴ تا ۱۳ نوامبر ۲۰۲۶ (۲ سال)</td></tr>
<tr><td>تعداد کل کندل‌ها</td><td>۳۵٬۰۴۱</td></tr>
</table>

<h3>۲.۳ تعریف رویداد برخورد</h3>
<p>
یک «رویداد برخورد» در این تحلیل به این شکل تعریف می‌شود: اولین کندلی که RSI وارد زون ±۱ واحد حول سطح ۴۰ یا ۶۰ می‌شود، به شرطی که RSI در همان حضور در زون به خود سطح (۴۰ یا ۶۰ با ±۰.۵) رسیده باشد. این شرط دوم برای فیلتر کردن برخوردهای سطحی و نویزی اضافه شد تا فقط رویدادهای معنادار لحاظ شوند.</p>

<h3>۲.۴ دسته‌بندی رویدادها (سه حالت)</h3>
<p>برای هر رویداد، جهت خروج اول RSI از زون بررسی شد:</p>

<ol>
<li><span class="tag passthrough">گذشتن (Pass-through)</span> — RSI از زون در جهت <em>مخالف</em> جهت ورودی خارج می‌شود. مثلاً برای سطح ۶۰ که از پایین به زون وارد شده، RSI به بالای ۶۱ می‌رود. این یعنی سطح رد شده و قیمت در جهت روند قبلی ادامه پیدا می‌کند.</li>
<li><span class="tag divergence">واگرایی (Divergence)</span> — RSI از زون در جهت <em>همان</em> ورودی خارج می‌شود، اما قیمت در جهت قبلی خود ادامه می‌یابد و سقف/کف جدید می‌زند، در حالی که RSI سقف/کف جدید نمی‌زند. این واگرایی ساده است که در پیام شما تعریف کردید.</li>
<li><span class="tag reversal">برگشت (Reversal)</span> — RSI از زون در جهت <em>همان</em> ورودی خارج می‌شود و قیمت نیز در جهت مخالف برمی‌گردد (سقف/کف جدید نمی‌زند). این همان «تک‌برخورد و برگشت» است.</li>
</ol>

<!-- ===================== 3. OVERALL STATS ===================== -->
<h2>۳. آمار کلی رویدادها</h2>

<p>
در مجموع ۱٬۳۲۸ رویداد شناسایی شد. توزیع تقریباً برابر بین دو سطح است: ۷۳۰ رویداد در سطح ۶۰ و ۵۹۸ رویداد در سطح ۴۰. این تفاوت نشان می‌دهد بازار در ۲ سال گذشته کمی بیشتر در فاز صعودی بوده (رویدادهای اشباع خرید بیشتر از اشباع فروش).</p>

<div class="chart-block">
<img src="data:image/png;base64,{charts['dist']}" alt="توزیع رویدادها">
<div class="caption">نمودار ۱ — توزیع کلی رویدادها (چپ) و تفکیک بر اساس سطح (راست)</div>
</div>

<table class="stats">
<tr><th>دسته</th><th>تعداد کل</th><th>درصد</th><th>سطح ۶۰</th><th>سطح ۴۰</th></tr>
<tr><td><span class="tag reversal">برگشت</span></td>
    <td>{counts.get('REVERSAL',0)}</td>
    <td>{counts.get('REVERSAL',0)/total*100:.1f}٪</td>
    <td>{counts_60.get('REVERSAL',0)}</td>
    <td>{counts_40.get('REVERSAL',0)}</td></tr>
<tr><td><span class="tag divergence">واگرایی</span></td>
    <td>{counts.get('DIVERGENCE',0)}</td>
    <td>{counts.get('DIVERGENCE',0)/total*100:.1f}٪</td>
    <td>{counts_60.get('DIVERGENCE',0)}</td>
    <td>{counts_40.get('DIVERGENCE',0)}</td></tr>
<tr><td><span class="tag passthrough">گذشتن</span></td>
    <td>{counts.get('PASS_THROUGH',0)}</td>
    <td>{counts.get('PASS_THROUGH',0)/total*100:.1f}٪</td>
    <td>{counts_60.get('PASS_THROUGH',0)}</td>
    <td>{counts_40.get('PASS_THROUGH',0)}</td></tr>
<tr class="total"><td>مجموع</td><td>{total}</td><td>۱۰۰٪</td><td>۷۳۰</td><td>۵۹۸</td></tr>
</table>

<div class="callout green">
<strong>تحلیل:</strong> نرخ برگشت در سطح ۴۰ (۳۳.۶٪) و سطح ۶۰ (۳۲.۳٪) تقریباً برابر است. اما نرخ گذشتن در سطح ۶۰ (۴۵.۳٪) کمی کمتر از سطح ۴۰ (۴۷.۰٪) است. به عبارت دیگر، برخورد به سطح ۶۰ کمی قابل‌اعتمادتر از سطح ۴۰ برای برگشت است، اما تفاوت چندان بزرگ نیست.</div>

<!-- ===================== 4. YEARLY ===================== -->
<h2>۴. توزیع سالانه رویدادها</h2>

<p>
توزیع رویدادها در سه سال نشان می‌دهد که بازار در سال ۲۰۲۵ فعال‌تر بوده (۶۴۳ رویداد) و در سال ۲۰۲۶ کمی آرام‌تر (۶۴۲ رویداد). بخش پایانی ۲۰۲۴ فقط شامل نوامبر و دسامبر است.</p>

<div class="chart-block">
<img src="data:image/png;base64,{charts['year']}" alt="توزیع سالانه">
<div class="caption">نمودار ۲ — توزیع رویدادها بر اساس سال</div>
</div>

<table class="stats">
<tr><th>سال</th><th>سطح</th><th>برگشت</th><th>واگرایی</th><th>گذشتن</th><th>مجموع</th></tr>
"""
# Add yearly rows
for (year, level), row_data in yr_pivot.iterrows():
    rev = int(row_data.get('REVERSAL', 0))
    div = int(row_data.get('DIVERGENCE', 0))
    pt = int(row_data.get('PASS_THROUGH', 0))
    tot = int(row_data['Total'])
    html += f"<tr><td>{year}</td><td>{level}</td><td>{rev}</td><td>{div}</td><td>{pt}</td><td>{tot}</td></tr>\n"

# Total row
html += f"""
<tr class="total"><td colspan="2">مجموع</td>
<td>{int(yr_pivot['REVERSAL'].sum())}</td>
<td>{int(yr_pivot['DIVERGENCE'].sum())}</td>
<td>{int(yr_pivot['PASS_THROUGH'].sum())}</td>
<td>{int(yr_pivot['Total'].sum())}</td></tr>
</table>

<div class="callout">
<strong>یافته جالب:</strong> در سال ۲۰۲۶، نسبت واگرایی‌ها نسبت به ۲۰۲۵ افزایش یافته (۲۰۲۴: ۸٪، ۲۰۲۵: ۲۰٪، ۲۰۲۶: ۲۴٪). این می‌تواند نشانه روند قدرتمندتر بازار در ۲۰۲۶ باشد که در آن RSI به سطوح می‌رسد اما روند ادامه پیدا می‌کند.</div>

<!-- ===================== 5. KEY PREDICTOR: CANDLES IN ZONE ===================== -->
<h2>۵. قوی‌ترین پیش‌بینی‌کننده: مدت حضور در زون</h2>

<p>
آزمون آماری ANOVA روی ۱۳ ویژگی مختلف نشان داد که <strong>«تعداد کندل‌هایی که RSI در زون می‌ماند»</strong> با اختلاف زیاد قوی‌ترین پیش‌بینی‌کننده نوع واکنش است. مقدار F=۲۰.۱۳ و p-value کمتر از ۰.۰۰۱، یعنی احتمال اینکه این تفاوت تصادفی باشد عملاً صفر است.</p>

<div class="chart-block">
<img src="data:image/png;base64,{charts['candles']}" alt="مدت حضور در زون">
<div class="caption">نمودار ۳ — توزیع تعداد کندل در زون (سیاه = میانگین)</div>
</div>

<p>میانگین تعداد کندل در زون برای هر دسته:</p>
<table class="stats">
<tr><th>دسته</th><th>سطح ۶۰ — میانگین</th><th>سطح ۴۰ — میانگین</th><th>تفسیر</th></tr>
<tr><td><span class="tag reversal">برگشت</span></td>
    <td>{mean_for(e60,'REVERSAL','candles_in_zone'):.2f}</td>
    <td>{mean_for(e40,'REVERSAL','candles_in_zone'):.2f}</td>
    <td>طولانی‌ترین حضور در زون — RSI در زون می‌ماند و قیمت برمی‌گردد</td></tr>
<tr><td><span class="tag divergence">واگرایی</span></td>
    <td>{mean_for(e60,'DIVERGENCE','candles_in_zone'):.2f}</td>
    <td>{mean_for(e40,'DIVERGENCE','candles_in_zone'):.2f}</td>
    <td>حضور متوسط — قیمت ادامه می‌یابد ولی RSI کم‌تحرک می‌شود</td></tr>
<tr><td><span class="tag passthrough">گذشتن</span></td>
    <td>{mean_for(e60,'PASS_THROUGH','candles_in_zone'):.2f}</td>
    <td>{mean_for(e40,'PASS_THROUGH','candles_in_zone'):.2f}</td>
    <td>کوتاه‌ترین حضور — RSI به سرعت از زون عبور می‌کند</td></tr>
</table>

<div class="callout green">
<strong>قانون عملی:</strong>
<ul>
<li>اگر RSI <strong>بیش از ۵ کندل</strong> در زون بماند → احتمال برگشت <strong>بیش از ۵۰٪</strong> است. ورود به معامله با اطمینان بالاتر.</li>
<li>اگر RSI در <strong>۱-۲ کندل اول</strong> از زون خارج شود → احتمال گذشتن حدود <strong>۷۰٪</strong> است. بهتر است صبر کنید.</li>
<li>اگر RSI بین <strong>۳-۵ کندل</strong> در زون بماند → حالت بینابینی، نیاز به تأییدیه کندلی (پین بار، دوجی، اینگالف) دارید.</li>
</ul>
</div>

<!-- ===================== 6. FEATURE HEATMAP ===================== -->
<h2>۶. تحلیل سایر ویژگی‌ها</h2>

<p>
نمودار زیر میانگین ۱۱ ویژگی کلیدی را برای هر دسته نشان می‌دهد. رنگ‌ها نرمال‌شده هستند (سبز = کم، قرمز = زیاد در آن ویژگی) تا تفاوت‌ها قابل مقایسه باشند.</p>

<div class="chart-block">
<img src="data:image/png;base64,{charts['heatmap']}" alt="هیتمپ ویژگی‌ها">
<div class="caption">نمودار ۴ — میانگین ویژگی‌ها بر اساس دسته (اعداد خام، رنگ نرمال‌شده)</div>
</div>

<h4>ویژگی‌های معنادار از نظر آماری (آزمون ANOVA):</h4>
<table class="stats">
<tr><th>ویژگی</th><th>F-statistic</th><th>p-value</th><th>معناداری</th></tr>
<tr><td>تعداد کندل در زون</td><td>۲۰.۱۳</td><td>&lt;۰.۰۰۱</td><td>***</td></tr>
<tr><td>نسبت حجم (۵/۲۰)</td><td>۵.۰۴</td><td>۰.۰۰۶۶</td><td>**</td></tr>
<tr><td>شیب قیمت در ۲۰ کندل</td><td>۴.۶۰</td><td>۰.۰۱۰</td><td>*</td></tr>
<tr><td>روند ۲۰ کندلی (٪)</td><td>۳.۴۱</td><td>۰.۰۳۴</td><td>*</td></tr>
<tr><td>فاصله از SMA50 (٪)</td><td>۳.۴۲</td><td>۰.۰۳۳</td><td>*</td></tr>
<tr><td>ساعت روز</td><td>۰.۱۰</td><td>۰.۹۰۱</td><td>ns</td></tr>
<tr><td>سرعت RSI در ۱۰ کندل</td><td>۱.۰۶</td><td>۰.۳۴۶</td><td>ns</td></tr>
<tr><td>حجم متوسط ۲۰ کندل</td><td>۰.۹۹</td><td>۰.۳۷۲</td><td>ns</td></tr>
</table>

<p><small>*** p&lt;۰.۰۰۱ (بسیار معنادار)، ** p&lt;۰.۰۱ (معنادار)، * p&lt;۰.۰۵ (ضعیف معنادار)، ns = غیرمعنادار</small></p>

<div class="callout">
<strong>یافته جالب:</strong> سرعت RSI به تنهایی پیش‌بینی‌کننده معناداری نیست (p=۰.۳۵)، اما در ترکیب با مدت حضور در زون بسیار مفید است. این یعنی «RSI چقدر تند به سطح رسیده» مهم نیست، بلکه «RSI چقدر در سطح می‌ماند» مهم است.</div>

<!-- ===================== 7. RSI VELOCITY ===================== -->
<h2>۷. تحلیل سرعت RSI قبل از برخورد</h2>

<p>اگرچه سرعت RSI به تنهایی معنادار نیست، اما نمودار زیر الگوهای جالبی نشان می‌دهد که در تصمیم‌گیری عملی مفیدند.</p>

<div class="chart-block">
<img src="data:image/png;base64,{charts['velocity']}" alt="سرعت RSI">
<div class="caption">نمودار ۵ — سرعت RSI در ۱۰ کندل قبل از برخورد (تغییر RSI)</div>
</div>

<p>بررسی دقیق نشان می‌دهد:</p>
<ul>
<li><strong>رویدادهای واگرایی</strong> بالاترین سرعت ورود به زون را دارند (میانگین RSI velocity برای سطح ۶۰: <code>{mean_for(e60,'DIVERGENCE','rsi_velocity_10'):.2f}</code>) — RSI با شتاب به سطح می‌رسد، که نشانه مومنتوم قدرتمند است و روند ادامه پیدا می‌کند.</li>
<li><strong>رویدادهای برگشت</strong> کندترین سرعت ورود را دارند (میانگین: <code>{mean_for(e60,'REVERSAL','rsi_velocity_10'):.2f}</code>) — RSI به آرامی به سطح می‌رسد، که نشانه خستگی روند و احتمال برگشت است.</li>
<li><strong>رویدادهای گذشتن</strong> در میانه قرار دارند (میانگین: <code>{mean_for(e60,'PASS_THROUGH','rsi_velocity_10'):.2f}</code>) — نه خیلی تند نه خیلی کند.</li>
</ul>

<div class="callout blue">
<strong>قانون عملی:</strong> اگر سرعت RSI در ۱۰ کندل اخیر <strong>بیشتر از ۳ واحد</strong> (برای سطح ۶۰) یا <strong>کمتر از ۳- واحد</strong> (برای سطح ۴۰) باشد، احتمال واگرایی بالا می‌رود و ورود به معامله‌ی برگشتی پرریسک است.</div>

<!-- ===================== 8. SESSION ===================== -->
<h2>۸. توزیع بر اساس سشن معاملاتی</h2>

<p>سشن‌های معاملاتی بر اساس وقت تهران دسته‌بندی شده‌اند. سشن «صبح» ساعت ۶:۳۰ تا ۱۲:۳۰ تهران را شامل می‌شود (آسیا)، «ظهر» ۱۲:۳۰ تا ۱۷:۳۰ (آروپا)، «عصر» ۱۷:۳۰ تا ۲۲:۳۰ (آمریکا)، و «شب» بقیه.</p>

<div class="chart-block">
<img src="data:image/png;base64,{charts['session']}" alt="سشن معاملاتی">
<div class="caption">نمودار ۶ — توزیع رویدادها بر اساس سشن معاملاتی (به وقت تهران)</div>
</div>

<table class="stats">
<tr><th>سشن</th><th>برگشت</th><th>واگرایی</th><th>گذشتن</th><th>مجموع</th><th>نرخ برگشت</th></tr>
"""
for sess_name in sess_pivot.index:
    row = sess_pivot.loc[sess_name]
    rev = int(row.get('REVERSAL', 0))
    div = int(row.get('DIVERGENCE', 0))
    pt = int(row.get('PASS_THROUGH', 0))
    tot = int(row['Total'])
    rev_pct = rev / tot * 100 if tot else 0
    html += f"<tr><td>{sess_name}</td><td>{rev}</td><td>{div}</td><td>{pt}</td><td>{tot}</td><td>{rev_pct:.1f}٪</td></tr>\n"

html += f"""
<tr class="total"><td>مجموع</td>
<td>{int(sess_pivot['REVERSAL'].sum())}</td>
<td>{int(sess_pivot['DIVERGENCE'].sum())}</td>
<td>{int(sess_pivot['PASS_THROUGH'].sum())}</td>
<td>{int(sess_pivot['Total'].sum())}</td>
<td>{sess_pivot['REVERSAL'].sum()/sess_pivot['Total'].sum()*100:.1f}٪</td></tr>
</table>

<div class="callout green">
<strong>یافته:</strong> سشن <em>عصر (آمریکا)</em> بالاترین نرخ برگشت را دارد (۳۶.۸٪) و سشن <em>ظهر (اروپا)</em> پایین‌ترین نرخ برگشت (۲۷.۸٪). به عبارت دیگر، برخورد به سطح در زمان سشن آمریکا قابل‌اعتمادتر است برای برگشت، در حالی که در سشن اروپا احتمال ادامه روند (واگرایی/گذشتن) بیشتر است.</div>

<!-- ===================== 9. OUTCOME MAGNITUDE ===================== -->
<h2>۹. تحلیل پیامد قیمت بعد از برخورد</h2>

<p>برای هر رویداد، حرکت مطلوب (در جهت روند قبلی) و نامطلوب (در جهت مخالف) در ۱۵ ساعت بعد از برخورد محاسبه شد. این اعداد نشان می‌دهد اگر در جهت درست وارد شوید چقدر سود می‌کنید و اگر در جهت اشتباه وارد شوید چقدر ضرر می‌کنید.</p>

<div class="chart-block">
<img src="data:image/png;base64,{charts['outcome']}" alt="پیامد قیمت">
<div class="caption">نمودار ۷ — میانه حرکت قیمت مطلوب و نامطلوب بعد از برخورد</div>
</div>

<table class="stats">
<tr><th>دسته</th><th>سطح</th><th>حرکت مطلوب (٪)</th><th>حرکت نامطلوب (٪)</th></tr>
<tr><td><span class="tag reversal">برگشت</span></td><td>۶۰</td>
    <td>{e60[e60['category']=='REVERSAL']['favorable_pct'].median():.2f}٪</td>
    <td>{e60[e60['category']=='REVERSAL']['adverse_pct'].median():.2f}٪</td></tr>
<tr><td><span class="tag divergence">واگرایی</span></td><td>۶۰</td>
    <td>{e60[e60['category']=='DIVERGENCE']['favorable_pct'].median():.2f}٪</td>
    <td>{e60[e60['category']=='DIVERGENCE']['adverse_pct'].median():.2f}٪</td></tr>
<tr><td><span class="tag passthrough">گذشتن</span></td><td>۶۰</td>
    <td>{e60[e60['category']=='PASS_THROUGH']['favorable_pct'].median():.2f}٪</td>
    <td>{e60[e60['category']=='PASS_THROUGH']['adverse_pct'].median():.2f}٪</td></tr>
<tr><td><span class="tag reversal">برگشت</span></td><td>۴۰</td>
    <td>{e40[e40['category']=='REVERSAL']['favorable_pct'].median():.2f}٪</td>
    <td>{e40[e40['category']=='REVERSAL']['adverse_pct'].median():.2f}٪</td></tr>
<tr><td><span class="tag divergence">واگرایی</span></td><td>۴۰</td>
    <td>{e40[e40['category']=='DIVERGENCE']['favorable_pct'].median():.2f}٪</td>
    <td>{e40[e40['category']=='DIVERGENCE']['adverse_pct'].median():.2f}٪</td></tr>
<tr><td><span class="tag passthrough">گذشتن</span></td><td>۴۰</td>
    <td>{e40[e40['category']=='PASS_THROUGH']['favorable_pct'].median():.2f}٪</td>
    <td>{e40[e40['category']=='PASS_THROUGH']['adverse_pct'].median():.2f}٪</td></tr>
</table>

<div class="callout">
<strong>تحلیل:</strong> در رویدادهای «برگشت»، حرکت نامطلوب (adverse) تقریباً دو برابر حرکت مطلوب است، زیرا قیمت ابتدا کمی در جهت روند قبلی حرکت می‌کند و سپس برمی‌گردد. این یعنی اگر بدون صبر کردن برای تأییدیه کندلی وارد شوید، در ابتدا با ضرر مواجه می‌شوید. در رویدادهای «گذشتن»، حرکت مطلوب بزرگ است چون قیمت در جهت روند ادامه پیدا می‌کند — اگر در جهت درست وارد شده باشید (به جای برگشتی)، سود خوبی می‌کنید.</div>

<!-- ===================== 10. PREDICTION RULES ===================== -->
<h2>۱۰. قوانین پیش‌بینی و توصیه‌های عملی</h2>

<p>
بر اساس تحلیل آماری، می‌توان قوانین تجربی زیر را برای پیش‌بینی نوع واکنش <em>قبل</em> از وارد شدن به معامله ارائه داد. توجه کنید که این قوانین احتمالی هستند، نه قطعی — همیشه با تأییدیه کندلی وارد شوید.</p>

<h3>۱۰.۱ قوانین پیش‌بینی (به ترتیب اطمینان)</h3>
<ol class="rules-list">
<li><strong>اگر RSI بیش از ۵ کندل در زون بماند</strong> → احتمال <span class="tag reversal">برگشت</span> بیش از ۵۰٪ است. این قوی‌ترین سیگنال برگشت است. در صورت مشاهده پین بار یا دوجی در M5، ورود پیشنهاد می‌شود.</li>
<li><strong>اگر RSI در ۱-۲ کندل اول از زون خارج شود</strong> → احتمال <span class="tag passthrough">گذشتن</span> حدود ۷۰٪ است. بهتر است معامله نکنید یا صبر کنید تا سطح بعدی.</li>
<li><strong>اگر سرعت RSI در ۱۰ کندل اخیر بیش از ۳ واحد باشد</strong> (مطلق، جهت‌دار) → خطر <span class="tag divergence">واگرایی</span> بالاست. بازار مومنتوم دارد و احتمال ادامه روند بیشتر از برگشت است.</li>
<li><strong>اگر نسبت حجم اخیر (۵ کندل) به میانگین (۲۰ کندل) بیشتر از ۱.۳ باشد</strong> → مومنتوم قوی است؛ احتمال واگرایی یا گذشتن بیشتر از برگشت است.</li>
<li><strong>اگر برخورد در سشن عصر (آمریکا) رخ دهد</strong> → نرخ برگشت ۳۶.۸٪ است (بالاترین). در سشن ظهر (اروپا) نرخ برگشت کمتر است.</li>
<li><strong>اگر فاصله قیمت از SMA50 بیش از ۱.۵٪ باشد</strong> → بازار بیش از حد کشیده و احتمال برگشت بالاتر است.</li>
</ol>

<h3>۱۰.۲ چک‌لیست پیش از ورود به معامله</h3>
<ol>
<li>آیا RSI واقعاً به سطح ۴۰ یا ۶۰ رسیده (نه فقط وارد زون شده)؟</li>
<li>چند کندل است که RSI در زون است؟ اگر کمتر از ۳ کندل، احتیاط کنید.</li>
<li>آیا حجم معاملات اخیر نرمال است یا جهش داشته؟</li>
<li>کدام سشن معاملاتی است؟ (عصر آمریکا بهترین برای برگشت)</li>
<li>آیا فاصله قیمت از SMA50 منطقی است؟</li>
<li>در M5: آیا کندل برگشتی (پین بار، دوجی، همر، اینگالف) تشکیل شده؟</li>
<li>حد ضرر را کجا قرار دهید؟ (پیشنهاد: بالای/پایین آخرین سقف/کف)</li>
</ol>

<h3>۱۰.۳ توصیه نهایی برای استراتژی شما</h3>
<div class="callout green">
استراتژی شما اساساً درست طراحی شده، اما <strong>نقطه ضعف اصلی آن ورود سریع بدون تأییدیه است</strong>. با توجه به اینکه فقط ۳۳٪ رویدادها منجر به برگشت فوری می‌شوند، ورود بدون صبر کردن برای کندل M5 تأییدیه، احتمال ضرر را بالا می‌برد. پیشنهاد می‌کنیم:
<ul>
<li><strong>فقط در صورتی وارد شوید</strong> که RSI حداقل ۳ کندل در زون مانده باشد و کندل M5 تأییدیه تشکیل شده باشد.</li>
<li>اگر RSI با سرعت زیاد (سرعت ۱۰ کندله &gt; ۳) به سطح رسیده، احتیاط کنید — احتمالاً واگرایی است.</li>
<li>اگر در سشن اروپا هستید، تأییدیه قوی‌تری بخواهید (نرخ برگشت کمتر است).</li>
<li>حد ضرر را حتماً زیر آخرین کف (در معامله خرید) یا بالای آخرین سقف (در معامله فروش) قرار دهید.</li>
</ul>
</div>

<!-- ===================== 11. VISUAL EXAMPLE ===================== -->
<h2>۱۱. نمونه بصری از رویدادها</h2>

<p>
نمودار زیر یک نمونه ۶ هفته‌ای از مارس تا آوریل ۲۰۲۵ را نشان می‌دهد. نمودار بالایی قیمت و نمودار پایینی RSI(30) است. رویدادهای برخورد با رنگ‌های مختلف علامت‌گذاری شده‌اند.</p>

<div class="chart-block">
<img src="data:image/png;base64,{charts['example']}" alt="نمونه بصری">
<div class="caption">نمودار ۸ — نمونه‌ای از رویدادها در مارس-آوریل ۲۰۲۵. مثلث‌های قرمز = گذشتن، نارنجی = واگرایی، سبز = برگشت. مثلث رو به پایین = سطح ۶۰، رو به بالا = سطح ۴۰.</div>
</div>

<p>
در این نمونه می‌بینید که بسیاری از برخوردها به سطح ۶۰ منجر به گذشتن شده‌اند (مثلث‌های قرمز)، که با تحلیل کلی ما مطابقت دارد. همچنین چند رویداد واگرایی مشاهده می‌شود که در آن‌ها قیمت سقف جدید زده اما RSI سقف پایین‌تری داشته است.</p>

<!-- ===================== 12. LIMITATIONS ===================== -->
<h2>۱۲. محدودیت‌ها و نتیجه‌گیری</h2>

<h3>۱۲.۱ محدودیت‌های تحلیل</h3>
<ul>
<li><strong>جایگزین داده:</strong> به دلیل عدم دسترسی به داده‌های تاریخی XAUUSD اسپات در تایم‌فریم M30 برای بازه ۲ سال، از PAXG/USDT استفاده شد. اگرچه همبستگی بسیار بالاست، اما در زمان‌های نقدینگی پایین ممکن است تفاوت‌های کوچک وجود داشته باشد.</li>
<li><strong>پنجره پیش‌رو ۳۰ کندل (۱۵ ساعت):</strong> این مدت برای ارزیابی پیامد معامله انتخاب شد. اگر استراتژی شما هدفتان کوتاه‌تر یا بلندتر است، نتایج می‌تواند متفاوت باشد.</li>
<li><strong>تلورانس ±۱ واحد:</strong> انتخاب شما برای تلورانس ±۱ بود. با تلورانس کمتر (±۰.۵ که در پیام اصلی گفتید)، تعداد رویدادها کمتر و احتمالاً کیفیت هر رویداد بالاتر می‌شود.</li>
<li><strong>عدم شبیه‌سازی کامل معامله:</strong> این تحلیل «برخورد به سطح» را بررسی می‌کند، نه ورود واقعی به معامله. در معامله واقعی، تأییدیه کندل M5 و مدیریت ریسک نقش تعیین‌کننده دارند.</li>
<li><strong>فیلتر رویدادهای ابتدای داده:</strong> برای ۲ رویداد اول (۱۷ نوامبر ۲۰۲۴) ویژگی‌های SMA200 قابل محاسبه نبود، اما این تعداد ناچیز است.</li>
</ul>

<h3>۱۲.۲ نتیجه‌گیری</h3>
<p>
استراتژی RSI(30) با سطوح ۴۰ و ۶۰ در تایم‌فریم M30 طلا در ۲ سال گذشته ۱٬۳۲۸ رویداد تولید کرده است. توزیع این رویدادها به این شکل است: <strong>۴۶.۱٪ گذشتن، ۳۲.۹٪ برگشت، ۲۱.۰٪ واگرایی</strong>. این یعنی استراتژی به تنهایی برای ورود به معامله کافی نیست — در حدود دو سوم مواقع، روند به جای برگشت ادامه می‌یابد.</p>

<p>
با این حال، تحلیل چند متغیره نشان می‌دهد که با در نظر گرفتن <strong>مدت حضور RSI در زون</strong>، <strong>سرعت RSI</strong>، <strong>حجم اخیر</strong>، و <strong>سشن معاملاتی</strong>، می‌توان پیش از ورود به معامله احتمال نوع واکنش را با دقت بهتری تخمین زد. قوی‌ترین سیگنال برگشت، طولانی شدن حضور RSI در زون (بیش از ۵ کندل) است.</p>

<div class="callout blue">
<strong>پیشنهاد برای بهبود استراتژی:</strong>
<ol>
<li>فقط زمانی وارد شوید که RSI حداقل ۳-۵ کندل در زون مانده باشد.</li>
<li>اگر سرعت ورود RSI به سطح زیاد است (&gt; ۳ واحد در ۱۰ کندل)، احتیاط کنید.</li>
<li>تأییدیه کندل M5 (پین بار، دوجی، اینگالف) را جدی بگیرید.</li>
<li>سشن عصر (آمریکا) را برای معامله برگشتی ترجیح دهید.</li>
<li>اگر حجم اخیر جهش داشته (نسبت ۵/۲۰ &gt; ۱.۳)، احتمال ادامه روند بیشتر از برگشت است.</li>
</ol>
</div>

<p style="margin-top: 18pt; font-size: 9pt; color: #6b7280; border-top: 1pt solid #e2e8f0; padding-top: 8pt;">
این گزارش با داده‌های واقعی بازار طی ۲ سال گذشته تهیه شده است. نتایج آماری معتبر هستند، اما هیچ استراتژی معاملاتی نمی‌تواند نتایج آینده را تضمین کند. همیشه با مدیریت ریسک مناسب معامله کنید.</p>

</body>
</html>
"""

# Write the HTML
with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"✓ HTML saved: {HTML_PATH}")
print(f"  Size: {os.path.getsize(HTML_PATH) / 1024:.1f} KB")
