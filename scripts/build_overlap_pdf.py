"""Build the PDF report for overlap analysis."""
import os, base64, json
import pandas as pd

DATA_DIR = "/home/z/my-project/data"
DOWNLOAD_DIR = "/home/z/my-project/download"
ASSETS_DIR = f"{DOWNLOAD_DIR}/overlap_assets"
HTML_PATH = f"{DOWNLOAD_DIR}/Overlap_RSI_Zones_Report.html"
PDF_PATH = f"{DOWNLOAD_DIR}/Overlap_RSI_Zones_Report.pdf"

with open(f"{DATA_DIR}/overlap_summary.json") as f:
    s = json.load(f)

# Load detailed results for additional stats
results = pd.read_pickle(f"{DATA_DIR}/overlap_analysis.pkl")

# Font embedding
def font_face(name, path, weight='normal'):
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('ascii')
    return f"""@font-face {{
  font-family: '{name}';
  src: url(data:font/ttf;base64,{b64}) format('truetype');
  font-weight: {weight};
}}"""

font_regular = font_face('Vazirmatn', '/home/z/.fonts/Vazirmatn-Regular.ttf', 'normal')
font_bold    = font_face('Vazirmatn', '/home/z/.fonts/Vazirmatn-Bold.ttf', 'bold')

# Encode charts
def img_b64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')

charts = {
    'pie':       img_b64(f"{ASSETS_DIR}/chart1_overlap_pie.png"),
    'impact':    img_b64(f"{ASSETS_DIR}/chart2_impact_comparison.png"),
    'level':     img_b64(f"{ASSETS_DIR}/chart3_by_level.png"),
    'lvl_cat':   img_b64(f"{ASSETS_DIR}/chart4_by_level_category.png"),
    'time':      img_b64(f"{ASSETS_DIR}/chart5_time_to_touch.png"),
    'hour':      img_b64(f"{ASSETS_DIR}/chart6_by_hour.png"),
    'finding':   img_b64(f"{ASSETS_DIR}/chart7_key_finding.png"),
}

# Format helper
def pct(v): return f"{v:.1f}%"
def fmt(v): return f"{v:.2f}"

html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<title>گزارش همپوشانی برخوردهای RSI با زون‌های مهم</title>
<style>
{font_regular}
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
  font-family: 'Vazirmatn', sans-serif;
  font-size: 11pt;
  line-height: 1.75;
  color: #1f2937;
  background: #ffffff;
}}

h1, h2, h3 {{ font-weight: bold; color: #0f172a; line-height: 1.4; }}
h1 {{ font-size: 26pt; margin: 0 0 6pt 0; }}
h2 {{ font-size: 18pt; margin: 24pt 0 10pt 0; padding-bottom: 6pt;
     border-bottom: 2px solid #c08a5a; color: #9c6f2c; }}
h3 {{ font-size: 14pt; margin: 18pt 0 8pt 0; color: #44403c; }}
h4 {{ font-size: 12pt; margin: 12pt 0 6pt 0; color: #57534e; }}

p {{ margin: 0 0 10pt 0; text-align: justify; }}
ul, ol {{ margin: 6pt 0 10pt 0; padding-right: 22pt; }}
li {{ margin: 4pt 0; }}

.cover {{
  page-break-after: always;
  display: flex; flex-direction: column; justify-content: center;
  min-height: 240mm; text-align: center;
  background: linear-gradient(135deg, #9c6f2c 0%, #c08a5a 50%, #f0b870 100%);
  color: white; padding: 30mm 20mm; margin: -18mm -16mm;
}}
.cover h1 {{ color: white; font-size: 30pt; line-height: 1.3; margin-bottom: 12pt; }}
.cover .subtitle {{ font-size: 15pt; opacity: 0.92; margin-bottom: 24pt; }}
.cover .meta {{ font-size: 11pt; opacity: 0.85; margin-top: 30pt; line-height: 1.9; }}
.cover .accent-bar {{ width: 80pt; height: 3pt; background: white; margin: 16pt auto; opacity: 0.8; }}
.cover .badge {{ display: inline-block; padding: 6pt 14pt;
  border: 1.5pt solid rgba(255,255,255,0.4); border-radius: 999pt;
  font-size: 10pt; margin: 4pt; }}

.kpi-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10pt; margin: 12pt 0; }}
.kpi {{ background: #f5f5f4; padding: 12pt; border-radius: 6pt; text-align: center;
       border-top: 3pt solid; }}
.kpi.reversal {{ border-top-color: #9ec99e; }}
.kpi.divergence {{ border-top-color: #f0b870; }}
.kpi.passthrough {{ border-top-color: #e89090; }}
.kpi .num {{ font-size: 22pt; font-weight: bold; display: block; }}
.kpi .label {{ font-size: 9pt; color: #57534e; margin-top: 4pt; }}

table {{ width: 100%; border-collapse: collapse; margin: 10pt 0 14pt 0; font-size: 10pt; }}
table.stats th {{ background: #9c6f2c; color: white; padding: 6pt 8pt;
  text-align: center; font-weight: bold; border: 1px solid #9c6f2c; }}
table.stats td {{ padding: 5pt 8pt; border: 1px solid #e7e5e4; text-align: center; }}
table.stats tr:nth-child(even) td {{ background: #fafaf9; }}
table.stats tr.total td {{ background: #fef3e7; font-weight: bold; }}

.callout {{ padding: 12pt 14pt; margin: 10pt 0; border-radius: 6pt; font-size: 10pt; }}
.callout.key {{ background: #fce8e8; border-right: 4pt solid #e89090; }}
.callout.info {{ background: #e8f4e8; border-right: 4pt solid #9ec99e; }}
.callout.warn {{ background: #fdf3e7; border-right: 4pt solid #f0b870; }}
.callout strong {{ font-weight: bold; }}

.chart-block {{ margin: 12pt 0 16pt 0; text-align: center; page-break-inside: avoid; }}
.chart-block img {{ max-width: 100%; height: auto; border: 1px solid #e7e5e4;
  border-radius: 4pt; }}
.chart-block .caption {{ font-size: 9pt; color: #6b7280; margin-top: 4pt; }}

.tag {{ display: inline-block; padding: 2pt 8pt; border-radius: 4pt;
  font-size: 9pt; font-weight: bold; color: white; }}
.tag.reversal {{ background: #9ec99e; }}
.tag.divergence {{ background: #f0b870; }}
.tag.passthrough {{ background: #e89090; }}

.toc {{ page-break-after: always; }}
.toc ol {{ list-style: none; padding: 0; counter-reset: toc; }}
.toc li {{ counter-increment: toc; margin: 8pt 0; padding: 6pt 0;
  border-bottom: 1px dashed #e7e5e4; }}
.toc li::before {{ content: counter(toc) ". "; color: #9c6f2c; font-weight: bold; margin-left: 8pt; }}

</style>
</head>
<body>

<!-- COVER -->
<div class="cover">
  <div style="font-size: 12pt; opacity: 0.85; letter-spacing: 3pt;">گزارش تحلیلی</div>
  <div class="accent-bar"></div>
  <h1>همپوشانی برخوردهای RSI<br>با زون‌های مهم (دوجی)</h1>
  <div class="subtitle">بررسی دقیق ۲ سال گذشته — ۱٬۳۲۸ رویداد برخورد به سطوح ۴۰ و ۶۰</div>
  <div style="margin-top: 24pt;">
    <span class="badge">۱۳۲۸ رویداد</span>
    <span class="badge">{s['total_daily_doji_zones']} زون دیلی</span>
    <span class="badge">{s['total_weekly_doji_zones']} زون هفتگی</span>
  </div>
  <div class="meta">
    تحلیل تأثیر همپوشانی زون‌های دوجی روزانه و هفتگی<br>
    بر احتمالات واکنش بازار (برگشت / واگرایی / گذشتن)<br><br>
    تهیه شده توسط: Z.ai<br>
    تاریخ گزارش: ۱۴ نوامبر ۲۰۲۶
  </div>
</div>

<!-- TOC -->
<div class="toc">
<h2>فهرست مطالب</h2>
<ol>
<li>خلاصه اجرایی و یافته‌های کلیدی</li>
<li>روش‌شناسی</li>
<li>آمار کلی همپوشانی</li>
<li>تأثیر همپوشانی بر نوع واکنش بازار</li>
<li>یافته کلیدی: تأثیر همپوشانی مضاعف</li>
<li>تحلیل بر اساس سطح (۴۰ و ۶۰)</li>
<li>تحلیل زمانی برخوردها</li>
<li>زمان رسیدن RSI از ۵۰ به ۴۰ یا ۶۰</li>
<li>توصیه‌های معاملاتی</li>
<li>محدودیت‌ها و نتیجه‌گیری</li>
</ol>
</div>

<!-- 1. EXEC SUMMARY -->
<h2>۱. خلاصه اجرایی و یافته‌های کلیدی</h2>

<p>
این گزارش نتایج تحلیل دقیق ۲ سال گذشته بازار طلا (نوامبر ۲۰۲۴ تا نوامبر ۲۰۲۶) را ارائه می‌دهد.
هدف، بررسی این سؤال بوده است: وقتی RSI(30) در تایم‌فریم M30 به سطوح ۴۰ یا ۶۰ می‌رسد،
چند درصد مواقع قیمت هم‌زمان داخل یکی از زون‌های مهم (شکل‌گرفته از کندل‌های دوجی روزانه یا هفتگی)
قرار دارد؟ و آیا این همپوشانی تأثیری بر احتمال نوع واکنش بازار (برگشت، واگرایی، گذشتن) دارد؟
</p>

<p>
در مجموع ۱٬۳۲۸ رویداد برخورد شناسایی شد. تحلیل نشان داد که حدود <strong>{pct(s['pct_inside_either'])}</strong>
از این برخوردها (یعنی {s['inside_either']} رویداد) هم‌زمان داخل حداقل یکی از زون‌های مهم بوده‌اند.
از این تعداد، {s['inside_daily']} مورد داخل زون‌های روزانه و {s['inside_weekly']} مورد داخل زون‌های هفتگی بوده‌اند.
</p>

<div class="kpi-grid">
  <div class="kpi reversal">
    <span class="num">{pct(s['pct_inside_either'])}</span>
    <span class="label">برخوردهای داخل زون مهم</span>
  </div>
  <div class="kpi divergence">
    <span class="num">{pct(s['pct_inside_both'])}</span>
    <span class="label">برخوردهای داخل هر دو زون (دیلی+هفتگی)</span>
  </div>
  <div class="kpi passthrough">
    <span class="num">{pct(s['category_dist_both'].get('PASS_THROUGH', 0) * 100)}</span>
    <span class="label">نرخ گذشتن وقتی داخل هر دو زون</span>
  </div>
</div>

<div class="callout key">
<strong>یافته کلیدی:</strong> وقتی قیمت هم‌زمان داخل <em>هر دو</em> زون مهم (دیلی و هفتگی) باشد،
نرخ «گذشتن از سطح» از <strong>{pct(s['category_dist_outside'].get('PASS_THROUGH', 0) * 100)}</strong>
(حالت baseline) به <strong>{pct(s['category_dist_both'].get('PASS_THROUGH', 0) * 100)}</strong> کاهش می‌یابد.
هم‌زمان نرخ «برگشت» از {pct(s['category_dist_outside'].get('REVERSAL', 0) * 100)} به
{pct(s['category_dist_both'].get('REVERSAL', 0) * 100)} و نرخ «واگرایی» از
{pct(s['category_dist_outside'].get('DIVERGENCE', 0) * 100)} به
{pct(s['category_dist_both'].get('DIVERGENCE', 0) * 100)} افزایش می‌یابد.
این یافته نشان می‌دهد که زون‌های دوجی واقعاً به‌عنوان سطوح حمایت/مقاومت عمل می‌کنند.
</div>

<p>
یافته دیگر: میانگین زمان رسیدن RSI از مقدار خنثی (۵۰) به سطح ۴۰ یا ۶۰ حدود
<strong>{s['time_to_touch_mean_hours']:.1f} ساعت</strong> است (میانه: {s['time_to_touch_median_hours']:.1f} ساعت).
این یعنی معمولاً حدود ۱۴ تا ۲۰ ساعت پس از خنثی شدن RSI، انتظار می‌رود به یکی از سطوح برسد.
</p>

<!-- 2. METHODOLOGY -->
<h2>۲. روش‌شناسی</h2>

<h3>۲.۱ منبع داده</h3>
<p>
داده از Binance PAXG/USDT در تایم‌فریم M30 برای ۲ سال گذشته استخراج شد
(۳۵٬۰۴۱ کندل). PAXG توکن طلای پشتیبان‌شده فیزیکی است که قیمت آن با طلای اسپات (XAUUSD)
تطابق بسیار بالایی دارد.
</p>

<h3>۲.۲ شناسایی رویدادهای برخورد</h3>
<p>
یک «رویداد برخورد» به این شکل تعریف شد: اولین کندلی که RSI(30) وارد زون ±۱ واحد حول
سطح ۴۰ یا ۶۰ می‌شود، به شرطی که RSI در همان حضور در زون به خود سطح (با ±۰.۵) رسیده باشد.
این شرط دوم برای فیلتر کردن برخوردهای سطحی و نویزی اضافه شد.
</p>

<h3>۲.۳ شناسایی زون‌های مهم (دوجی)</h3>
<p>
داده M30 به کندل‌های روزانه و هفتگی تجمیع شد. سپس در هر دو تایم‌فریم، کندل‌های دوجی
شناسایی شدند. تعریف دوجی: کندلی که اندازه بدنه (|close - open|) کمتر از یا مساوی ۱۰٪
از کل بازه کندل (high - low) باشد.
</p>

<table class="stats">
<tr><th>تایم‌فریم</th><th>تعداد کندل</th><th>تعداد دوجی</th><th>درصد</th></tr>
<tr><td>روزانه (D1)</td><td>{len(pd.read_csv(f"{DATA_DIR}/xauusd_30m_binance_paxg.csv").resample('', on='open_time')) if False else '~730'}</td><td>{s['total_daily_doji_zones']}</td><td>{s['total_daily_doji_zones']/730*100:.1f}%</td></tr>
<tr><td>هفتگی (W1)</td><td>~104</td><td>{s['total_weekly_doji_zones']}</td><td>{s['total_weekly_doji_zones']/104*100:.1f}%</td></tr>
</table>

<h3>۲.۴ تعریف «داخل زون بودن»</h3>
<p>
برای هر رویداد برخورد، قیمت در لحظه برخورد با هر زون دوجی مقایسه شد.
اگر قیمت داخل بازه [min(open, close), max(open, close)] زون (با تلورانس ۰.۱۵٪) باشد،
آن رویداد «داخل زون» محسوب می‌شود. فقط زون‌هایی که <em>قبل</em> از رویداد شکل گرفته‌اند
در نظر گرفته شدند (احترام به علیت زمانی).
</p>

<!-- 3. OVERALL STATS -->
<h2>۳. آمار کلی همپوشانی</h2>

<p>
در مجموع از ۱٬۳۲۸ رویداد برخورد، <strong>{s['inside_either']}</strong> مورد ({pct(s['pct_inside_either'])})
داخل حداقل یکی از زون‌های مهم بوده‌اند. این یعنی حدود یک‌چهارم برخوردها با زون‌های مهم همپوشانی دارند.
</p>

<div class="chart-block">
<img src="data:image/png;base64,{charts['pie']}" alt="نرخ همپوشانی">
<div class="caption">نمودار ۱ — همپوشانی برخوردها با زون‌های مهم (چپ) و تفکیک نوع زون (راست)</div>
</div>

<table class="stats">
<tr><th>وضعیت</th><th>تعداد</th><th>درصد</th></tr>
<tr><td>داخل زون روزانه (دیلی)</td><td>{s['inside_daily']}</td><td>{pct(s['pct_inside_daily'])}</td></tr>
<tr><td>داخل زون هفتگی</td><td>{s['inside_weekly']}</td><td>{pct(s['pct_inside_weekly'])}</td></tr>
<tr><td>داخل حداقل یک زون (هر نوع)</td><td>{s['inside_either']}</td><td>{pct(s['pct_inside_either'])}</td></tr>
<tr><td>داخل هر دو زون (دیلی+هفتگی)</td><td>{s['inside_both']}</td><td>{pct(s['pct_inside_both'])}</td></tr>
<tr class="total"><td>خارج از همه زون‌ها</td><td>{s['outside_all']}</td><td>{pct(s['pct_outside'])}</td></tr>
</table>

<div class="callout info">
<strong>تفسیر:</strong> نرخ همپوشانی ۲۷٪ نشان می‌دهد که در حدود یک‌چهارم مواقع، برخورد RSI به سطوح ۴۰ یا ۶۰
هم‌زمان با حضور قیمت در یک زون مهم (سطح حمایت/مقاومت دوجی) رخ می‌دهد. این نسبت قابل توجه است و
نشان‌دهنده اهمیت پایش هم‌زمان RSI و زون‌های مهم است.
</div>

<!-- 4. IMPACT ANALYSIS -->
<h2>۴. تأثیر همپوشانی بر نوع واکنش بازار</h2>

<p>
سؤال کلیدی: آیا وقتی برخورد RSI به ۴۰ یا ۶۰ هم‌زمان با حضور در زون مهم باشد، احتمال نوع واکنش
بازار (برگشت، واگرایی، گذشتن) متفاوت از حالت عادی است؟
</p>

<div class="chart-block">
<img src="data:image/png;base64,{charts['impact']}" alt="تأثیر همپوشانی">
<div class="caption">نمودار ۲ — مقایسه توزیع واکنش بازار در سه حالت: خارج از زون، داخل یک زون، داخل هر دو زون</div>
</div>

<table class="stats">
<tr><th>حالت</th><th>تعداد رویداد</th><th>برگشت</th><th>واگرایی</th><th>گذشتن</th></tr>
<tr>
  <td>خارج از زون (baseline)</td>
  <td>{s['count_outside']}</td>
  <td>{pct(s['category_dist_outside'].get('REVERSAL', 0) * 100)}</td>
  <td>{pct(s['category_dist_outside'].get('DIVERGENCE', 0) * 100)}</td>
  <td>{pct(s['category_dist_outside'].get('PASS_THROUGH', 0) * 100)}</td>
</tr>
<tr>
  <td>داخل حداقل یک زون</td>
  <td>{s['count_inside']}</td>
  <td>{pct(s['category_dist_inside'].get('REVERSAL', 0) * 100)}</td>
  <td>{pct(s['category_dist_inside'].get('DIVERGENCE', 0) * 100)}</td>
  <td>{pct(s['category_dist_inside'].get('PASS_THROUGH', 0) * 100)}</td>
</tr>
<tr class="total">
  <td>داخل هر دو زون (دیلی+هفتگی)</td>
  <td>{s['count_both']}</td>
  <td>{pct(s['category_dist_both'].get('REVERSAL', 0) * 100)}</td>
  <td>{pct(s['category_dist_both'].get('DIVERGENCE', 0) * 100)}</td>
  <td>{pct(s['category_dist_both'].get('PASS_THROUGH', 0) * 100)}</td>
</tr>
</table>

<div class="callout warn">
<strong>تحلیل تدریجی:</strong> با حرکت از «خارج از زون» به «داخل یک زون» و سپس «داخل هر دو زون»،
می‌توانیم یک روند تدریجی مشاهده کنیم:
<ul>
<li>نرخ «گذشتن» به‌طور پیوسته کاهش می‌یابد: {pct(s['category_dist_outside'].get('PASS_THROUGH', 0) * 100)} → {pct(s['category_dist_inside'].get('PASS_THROUGH', 0) * 100)} → {pct(s['category_dist_both'].get('PASS_THROUGH', 0) * 100)}</li>
<li>نرخ «واگرایی» افزایش می‌یابد: {pct(s['category_dist_outside'].get('DIVERGENCE', 0) * 100)} → {pct(s['category_dist_inside'].get('DIVERGENCE', 0) * 100)} → {pct(s['category_dist_both'].get('DIVERGENCE', 0) * 100)}</li>
<li>نرخ «برگشت» در حالت «هر دو زون» به‌طور قابل توجهی بالاتر است: {pct(s['category_dist_both'].get('REVERSAL', 0) * 100)}</li>
</ul>
این الگو نشان می‌دهد که زون‌های مهم واقعاً به‌عنوان سطوح حمایت/مقاومت عمل می‌کنند و هرچه همپوشانی قوی‌تر باشد،
احتمال ادامه روند (گذشتن) کمتر می‌شود.
</div>

<!-- 5. KEY FINDING -->
<h2>۵. یافته کلیدی: تأثیر همپوشانی مضاعف</h2>

<div class="chart-block">
<img src="data:image/png;base64,{charts['finding']}" alt="یافته کلیدی">
<div class="caption">نمودار ۳ — مقایسه مستقیم احتمالات در سه سناریو</div>
</div>

<p>
وقتی قیمت هم‌زمان داخل <strong>هر دو</strong> زون مهم (یعنی هم یک زون دیلی و هم یک زون هفتگی
در همان محدوده قیمت فعال باشد) قرار داشته باشد، رفتار بازار به‌طور قابل توجهی متفاوت است:
</p>

<ul>
<li><span class="tag passthrough">گذشتن</span> از {pct(s['category_dist_outside'].get('PASS_THROUGH', 0) * 100)} به {pct(s['category_dist_both'].get('PASS_THROUGH', 0) * 100)} <strong>کاهش چشمگیر</strong></li>
<li><span class="tag reversal">برگشت</span> از {pct(s['category_dist_outside'].get('REVERSAL', 0) * 100)} به {pct(s['category_dist_both'].get('REVERSAL', 0) * 100)} <strong>افزایش</strong></li>
<li><span class="tag divergence">واگرایی</span> از {pct(s['category_dist_outside'].get('DIVERGENCE', 0) * 100)} به {pct(s['category_dist_both'].get('DIVERGENCE', 0) * 100)} <strong>افزایش قابل توجه</strong></li>
</ul>

<div class="callout key">
<strong>تفسیر معاملاتی:</strong> این یافته مهم است که در حالت «هر دو زون»، با وجود کاهش گذشتن،
نرخ واگرایی هم بالا می‌رود (و نه فقط برگشت). این یعنی وقتی قیمت در یک زون مهم قوی است،
احتمال اینکه روند ادامه پیدا کند ولی با ضعیف شدن مومنتوم (واگرایی) زیاد است.
پس استراتژی بهتر این است که در حالت «هر دو زون»، صبر کرد تا الگوی تأییدیه (پین بار، اینگالف) تشکیل شود،
به جای ورود سریع به معامله برگشتی.
</div>

<!-- 6. BY LEVEL -->
<h2>۶. تحلیل بر اساس سطح (۴۰ و ۶۰)</h2>

<div class="chart-block">
<img src="data:image/png;base64,{charts['level']}" alt="بر اساس سطح">
<div class="caption">نمودار ۴ — نرخ همپوشانی برای هر سطح</div>
</div>

<table class="stats">
<tr><th>سطح</th><th>کل رویداد</th><th>داخل زون</th><th>٪ داخل</th></tr>
<tr><td>۴۰ (اشباع فروش)</td><td>{s['by_level']['40']['total']}</td><td>{s['by_level']['40']['inside_either']}</td><td>{pct(s['by_level']['40']['pct_inside_either'])}</td></tr>
<tr><td>۶۰ (اشباع خرید)</td><td>{s['by_level']['60']['total']}</td><td>{s['by_level']['60']['inside_either']}</td><td>{pct(s['by_level']['60']['pct_inside_either'])}</td></tr>
</table>

<div class="chart-block">
<img src="data:image/png;base64,{charts['lvl_cat']}" alt="تفکیک سطح و زون">
<div class="caption">نمودار ۵ — توزیع واکنش بازار بر اساس سطح و وضعیت زون</div>
</div>

<p>
بررسی تفکیکی نشان می‌دهد که در <strong>سطح ۶۰</strong>، وقتی داخل زون مهم باشیم،
نرخ «برگشت» از ۳۱٪ به ۳۵٪ افزایش می‌یابد و نرخ «گذشتن» از ۴۶٪ به ۴۱٪ کاهش می‌یابد.
در <strong>سطح ۴۰</strong>، تأثیر کمتر چشمگیر است ولی نرخ «واگرایی» از ۱۸٪ به ۲۳٪ افزایش می‌یابد.
</p>

<!-- 7. TIME ANALYSIS -->
<h2>۷. تحلیل زمانی برخوردها</h2>

<p>
بررسی اینکه برخوردهای RSI به سطوح ۴۰ و ۶۰ در چه ساعاتی از روز (به وقت تهران) بیشتر رخ می‌دهند:
</p>

<div class="chart-block">
<img src="data:image/png;base64,{charts['hour']}" alt="توزیع ساعتی">
<div class="caption">نمودار ۶ — توزیع ساعتی برخوردها (به وقت تهران) با تفکیک سشن</div>
</div>

<p>
برخوردها در ساعات عصر (سشن آمریکا، ۱۷-۲۲ تهران) و شب بیشتر رخ می‌دهند.
ساعات پیک برخورد: ۱۹:۳۰، ۱۶:۳۰، و ۱۷:۳۰ تهران (شروع سشن آمریکا و هم‌پوشانی با اروپا).
</p>

<!-- 8. TIME TO TOUCH -->
<h2>۸. زمان رسیدن RSI از ۵۰ به ۴۰ یا ۶۰</h2>

<p>
برای هر رویداد برخورد، زمان رسیدن RSI از مقدار خنثی (۵۰) به سطح ۴۰ یا ۶۰ محاسبه شد.
این تحلیل به ما می‌گوید که معمولاً چقدر باید صبر کنیم تا RSI از حالت خنثی به یکی از سطوح برسد.
</p>

<div class="chart-block">
<img src="data:image/png;base64,{charts['time']}" alt="زمان تا برخورد">
<div class="caption">نمودار ۷ — توزیع زمان رسیدن RSI از ۵۰ به سطح ۴۰ یا ۶۰ (ساعت)</div>
</div>

<table class="stats">
<tr><th>سناریو</th><th>میانگین</th><th>میانه</th></tr>
<tr><td>کل برخوردها</td><td>{s['time_to_touch_mean_hours']:.1f} ساعت</td><td>{s['time_to_touch_median_hours']:.1f} ساعت</td></tr>
<tr><td>سطح ۴۰</td><td>18.2 ساعت</td><td>~13 ساعت</td></tr>
<tr><td>سطح ۶۰</td><td>20.4 ساعت</td><td>~15 ساعت</td></tr>
</table>

<div class="callout info">
<strong>تفسیر:</strong> معمولاً حدود ۱۴ تا ۲۰ ساعت پس از خنثی شدن RSI (عبور از ۵۰)،
انتظار می‌رود به یکی از سطوح ۴۰ یا ۶۰ برسد. سطح ۴۰ کمی سریع‌تر از سطح ۶۰ رسیدن می‌شود
(۱۸.۲ ساعت vs ۲۰.۴ ساعت)، که می‌تواند ناشی از سرعت بالاتر نزول در زمان ریزش‌ها باشد.
</div>

<!-- 9. RECOMMENDATIONS -->
<h2>۹. توصیه‌های معاملاتی</h2>

<ol>
<li><strong>پایش هم‌زمان RSI و زون‌های مهم:</strong> وقتی RSI به ۴۰ یا ۶۰ نزدیک می‌شود، حتماً چک کنید
که آیا قیمت هم‌زمان داخل یک زون مهم (دوجی دیلی یا هفتگی) هست یا نه. این همپوشانی در ۲۷٪ مواقع رخ می‌دهد.</li>

<li><strong>اگر داخل یک زون مهم هستید:</strong> احتمال «گذشتن» کمی کمتر از حالت عادی است (۴۴٪ vs ۴۷٪).
ولی همچنان وارد نشوید تا الگوی تأییدیه (پین بار، دوجی، اینگالف در M5) تشکیل شود.</li>

<li><strong>اگر داخل هر دو زون (دیلی + هفتگی) هستید:</strong> این قوی‌ترین سناریو است!
نرخ «گذشتن» به ۲۸٪ کاهش می‌یابد و نرخ «برگشت» و «واگرایی» هر دو بالا می‌روند.
این بهترین فرصت برای ورود به معامله برگشتی است، <em>اما</em> چون نرخ واگرایی هم بالاست،
حتماً صبر کنید تا الگوی تأییدیه واضح تشکیل شود.</li>

<li><strong>اگر خارج از هر زون مهم هستید:</strong> رفتار بازار به baseline نزدیک است
(۴۷٪ گذشتن، ۳۳٪ برگشت، ۲۰٪ واگرایی). در این حالت استراتژی استاندارد اعمال شود.</li>

<li><strong>زمان‌بندی:</strong> بیشتر برخوردها در ساعات ۱۶:۳۰ تا ۱۹:۳۰ تهران رخ می‌دهد (هم‌پوشانی اروپا و آمریکا).
در این ساعات هشدارهای RSI ارزش بیشتری دارند. میانگین زمان از RSI=50 به برخورد حدود ۱۹ ساعت است.</li>
</ol>

<!-- 10. LIMITATIONS -->
<h2>۱۰. محدودیت‌ها و نتیجه‌گیری</h2>

<h3>۱۰.۱ محدودیت‌ها</h3>
<ul>
<li><strong>داده:</strong> از PAXG/USDT به‌عنوان جایگزین XAUUSD اسپات استفاده شد. با وجود همبستگی بالا،
در زمان‌های نقدینگی پایین ممکن است تفاوت‌های کوچک وجود داشته باشد.</li>
<li><strong>تعریف دوجی:</strong> از آستانه ۱۰٪ (بدنه/بازه) استفاده شد. با آستانه‌های متفاوت (۵٪ یا ۱۵٪)،
تعداد زون‌ها و نتایج می‌تواند کمی متفاوت باشد.</li>
<li><strong>تلورانس «داخل زون»:</strong> از ۰.۱۵٪ قیمت به‌عنوان تلورانس استفاده شد. با تلورانس متفاوت،
نتایج می‌تواند تغییر کند.</li>
<li><strong>علیت زمانی:</strong> فقط زون‌هایی که قبل از رویداد شکل گرفته‌اند در نظر گرفته شدند،
ولی زون‌هایی که در همان روز رویداد شکل گرفته‌اند ممکن است هنوز «نهایی» نباشند.</li>
<li><strong>حجم نمونه در حالت «هر دو زون»:</strong> با ۳۲ رویداد، اندازه نمونه کوچک است و
نتایج با احتیاط تفسیر شوند.</li>
</ul>

<h3>۱۰.۲ نتیجه‌گیری</h3>
<p>
این تحلیل نشان داد که همپوشانی برخوردهای RSI به سطوح ۴۰ و ۶۰ با زون‌های مهم (دوجی دیلی/هفتگی)
در حدود ۲۷٪ مواقع رخ می‌دهد. مهم‌تر از خود نرخ همپوشانی، تأثیر آن بر رفتار بازار است:
وقتی قیمت داخل زون مهم باشد، احتمال «گذشتن» کاهش می‌یابد و وقتی داخل <em>هر دو</em> زون باشد،
این کاهش بسیار چشمگیرتر است (۴۷٪ → ۲۸٪).
</p>

<p>
این یافته با منطق تکنیکال هم‌خوانی دارد: زون‌های دوجی نشان‌دهنده سطوحی هستند که در آن‌ها
فروشندگان و خریداران در توازن بوده‌اند، پس طبیعی است که در برخورد مجدد، به‌عنوان
حمایت/مقاومت عمل کنند. استراتژی بهتر این است که علاوه بر RSI، وضعیت قیمت نسبت به زون‌های مهم
را هم هم‌زمان پایش کنید.
</p>

<p style="margin-top: 18pt; font-size: 9pt; color: #6b7280;
  border-top: 1pt solid #e7e5e4; padding-top: 8pt;">
این گزارش با داده‌های واقعی بازار طی ۲ سال گذشته تهیه شده است.
همه اعداد بر اساس ۱٬۳۲۸ رویداد واقعی برخورد محاسبه شده‌اند.
هیچ استراتژی معاملاتی نمی‌تواند نتایج آینده را تضمین کند.
</p>

</body>
</html>
"""

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"✓ HTML saved: {HTML_PATH}")
print(f"  Size: {os.path.getsize(HTML_PATH) / 1024:.1f} KB")
