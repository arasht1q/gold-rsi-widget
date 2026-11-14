# ویجت RSI طلا — استراتژی M30

این پروژه یک ویجت وب (PWA) برای پایش RSI(30) روی تایم‌فریم M30 طلا (XAUUSD) است که شامل:

- نمایش زنده قیمت طلا + RSI(30) M30
- پیش‌بینی احتمال برخورد به سطح ۴۰ یا ۶۰ اول
- پیش‌بینی واکنش بازار (برگشت / واگرایی / گذشتن) بر اساس آمار ۲ سال گذشته
- تشخیص الگوهای کندلی M5 (دوجی، پین بار، همر، اینگالف)
- تیکت ورود با حد ضرر/سود و نسبت ریسک/سود
- زون‌های مهم از کندل‌های دوجی روزانه و هفتگی
- تحلیل روز قبل (سشن‌ها، سقف/کف، کندل‌های M5)
- رابط کاربری فارسی RTL با تم خاکستری + پاستلی

## تکنولوژی‌ها

- **Framework:** Next.js 16 با App Router و TypeScript
- **Styling:** Tailwind CSS 4 + shadcn/ui
- **Data Sources:**
  - قیمت لحظه‌ای: TradingView TVC:GOLD (scanner API)
  - کندل تاریخی M30: Yahoo Finance GC=F (طلای آتی COMEX)
  - Fallback: Binance PAXG/USDT
- **PWA:** manifest.json + service worker + آیکون‌های 192/512/180

## اجرا روی کامپیوتر شخصی

### پیش‌نیازها
- Node.js 18+ (یا Bun)
- npm یا bun

### مراحل
```bash
# نصب وابستگی‌ها
npm install
# یا
bun install

# اجرای dev server
npm run dev
# یا
bun run dev

# باز کردن در مرورگر
# http://localhost:3000
```

### Build برای production
```bash
npm run build
npm start
```

## استقرار (Deploy) برای ۲۴/۷

### گزینه ۱: Vercel (رایگان، آسان)
1. یک حساب روی vercel.com بسازید
2. پروژه را push کنید به GitHub
3. در Vercel، «Import Project» را بزنید و repo را انتخاب کنید
4. Deploy - تمام!

### گزینه ۲: Cloudflare Pages + Workers (رایگان، بدون تحریم ایران)
- برای ایران بهترین گزینه
- ۱۰۰٬۰۰۰ درخواست روزانه رایگان
- CDN جهانی

### گزینه ۳: VPS (Hetzner / Vultr)
- کنترل کامل
- هزینه: $۴-۶/ماه
- مناسب برای scale بالا

## ساختار پروژه

```
src/
├── app/
│   ├── api/
│   │   └── gold/route.ts        # API دریافت داده زنده + تحلیل
│   ├── layout.tsx                # Layout با manifest و meta tags
│   └── page.tsx                  # صفحه اصلی ویجت
├── components/
│   ├── install-guide.tsx         # راهنمای نصب PWA
│   └── ui/                       # shadcn/ui components
├── lib/
│   └── gold-analysis.ts          # منطق RSI، تشخیص الگو، پیش‌بینی
└── public/
    ├── manifest.json             # PWA manifest
    ├── sw.js                     # Service Worker
    └── icon-*.png                # آیکون‌های PWA
```

## اسکریپت‌های تحلیل (Python)

در پوشه `scripts/` چند اسکریپت تحلیل آماری هم وجود دارد:
- `analyze_rsi.py` - تحلیل اصلی ۲ سال گذشته
- `analyze_overlap.py` - تحلیل همپوشانی با زون‌های دوجی
- `make_charts.py` - نمودارهای تحلیلی

این اسکریپت‌ها برای تولید آماری استفاده شده‌اند که در منطق پیش‌بینی ویجت به کار رفته‌اند.

## توجه

- داده TradingView ممکن است rate-limit شود (429). در این حالت به Yahoo GC=F fallback می‌شود.
- بازار طلای اسپات شنبه‌ها تعطیل است. در این زمان، آخرین قیمت جمعه نمایش داده می‌شود.
- RSI روی داده GC=F محاسبه می‌شود (نه XAUUSD اسپات بروکر شما). ممکن است ۲-۱۰ واحد با بروکر شما تفاوت داشته باشد.

## لایسنس

MIT License — آزاد برای استفاده شخصی و تجاری.
