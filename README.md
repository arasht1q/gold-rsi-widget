# Gold RSI Widget — استراتژی معاملاتی RSI روی طلا

ویجت وب + اپ اندروید برای پایش RSI(30) روی تایم‌فریم M30 طلا (XAUUSD) با پیش‌بینی واکنش بازار، تشخیص الگوی کندلی، و زون‌های مهم (دوجی روزانه/هفتگی).

## ساختار پروژه

```
.
├── src/                          # Next.js web app (PWA widget)
│   ├── app/
│   │   ├── api/gold/route.ts     # API: live data + analysis
│   │   ├── layout.tsx            # Layout + PWA manifest
│   │   └── page.tsx              # Widget UI (RTL Persian)
│   ├── components/
│   │   ├── install-guide.tsx     # PWA install guide
│   │   └── ui/                   # shadcn/ui components
│   └── lib/
│       └── gold-analysis.ts      # RSI, pattern detection, prediction logic
├── public/                       # PWA assets (manifest, icons, service worker)
├── android-app/                  # React Native (Expo) Android app
│   ├── App.tsx                   # Main app component
│   ├── app.json                  # Expo config
│   ├── eas.json                  # EAS Build config (for APK)
│   ├── src/lib/gold-analysis.ts  # Shared analysis logic (same as web)
│   └── assets/                   # App icons
├── scripts/                      # Python analysis scripts
│   ├── analyze_rsi.py            # Main 2-year backtest
│   ├── analyze_overlap.py        # RSI × Doji zones overlap analysis
│   ├── make_charts.py            # Generate charts
│   └── fetch_data.py             # Data fetching utilities
├── prisma/                       # Prisma schema (if needed)
├── package.json                  # Dependencies
├── .gitignore
└── README.md
```

## ویژگی‌ها

### وب ویجت (Next.js PWA)
- ✅ نمایش زنده قیمت طلا + RSI(30) M30
- ✅ پیش‌بینی احتمال برخورد به سطح ۴۰ یا ۶۰ اول
- ✅ پیش‌بینی واکنش بازار (برگشت / واگرایی / گذشتن) بر اساس ۱۳۲۸ رویداد بک‌تست
- ✅ زون‌های مهم از کندل‌های دوجی روزانه و هفتگی (تاریخ میلادی + open/close)
- ✅ تشخیص الگوی کندلی M5 (دوجی، پین بار، همر، اینگالف)
- ✅ تیکت ورود با حد ضرر/سود و نسبت ریسک/سود
- ✅ تحلیل روز قبل (سشن‌ها، سقف/کف، کندل‌های M5)
- ✅ نصب به‌عنوان PWA روی اندروید و iOS

### اپ اندروید (React Native / Expo)
- ✅ همان ویژگی‌های وب ویجت
- ✅ APK قابل نصب مستقیم روی گوشی
- ✅ رابط فارسی RTL
- ✅ تم خاکستری روشن + رنگ‌های پاستلی

## منابع داده

| منبع | کاربرد |
|------|--------|
| TradingView TVC:GOLD | قیمت لحظه‌ای (تطبیق نزدیک به XAUUSD بروکر) |
| Yahoo Finance GC=F | کندل تاریخی M30، M5، D1، W1 برای محاسبه RSI و زون‌ها |
| Binance PAXG/USDT | Fallback در صورت قطعی Yahoo |

## اجرای وب ویجت

```bash
# نصب
npm install

# اجرای dev server
npm run dev

# باز در مرورگر
# http://localhost:3000
```

## اجرای اپ اندروید

```bash
cd android-app
npm install
npm start
# اسکن QR با Expo Go روی گوشی
```

### ساخت APK
```bash
cd android-app
npm install -g eas-cli
eas login
eas build -p android --profile preview
```

## بک‌تست و تحلیل

این پروژه بر اساس بک‌تست ۲ سال گذشته بازار طلا (۱۳۲۸ رویداد برخورد RSI به ۴۰ یا ۶۰) ساخته شده است.

### یافته‌های کلیدی
- ۲۷٪ برخوردها هم‌زمان با زون‌های مهم (دوجی) بوده‌اند
- وقتی قیمت داخل **هر دو** زون (دیلی + هفتگی) باشد:
  - نرخ «گذشتن» از ۴۷٪ به **۲۸٪** کاهش می‌یابد
  - نرخ «برگشت» از ۳۳٪ به **۴۱٪** افزایش می‌یابد
- میانگین زمان از RSI=۵۰ به سطح ۴۰ یا ۶۰: **۱۹.۴ ساعت**

برای جزئیات کامل، فایل‌های PDF در پوشه `download/` را ببینید:
- `XAUUSD_RSI30_M30_Backtest_2yr.pdf` — گزارش بک‌تست اصلی
- `Overlap_RSI_Zones_Report.pdf` — گزارش همپوشانی با زون‌های مهم

## تکنولوژی‌ها

- **Frontend:** Next.js 16, TypeScript, Tailwind CSS 4, shadcn/ui
- **Mobile:** React Native, Expo
- **Data:** Yahoo Finance, TradingView, Binance APIs
- **Analysis:** Python (pandas, numpy, matplotlib)
- **Fonts:** Vazirmatn (Persian)

## مجوز

MIT License — آزاد برای استفاده شخصی و تجاری.

## اعتبار

تهیه شده با Z.ai
