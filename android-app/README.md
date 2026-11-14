# RSI Gold Widget — Android App (React Native / Expo)

برنامه اندروید原生 برای پایش RSI(30) روی طلا (XAUUSD) با تایم‌فریم M30.

## ویژگی‌ها

- نمایش زنده قیمت طلا + RSI(30) M30
- پیش‌بینی احتمال برخورد به سطح ۴۰ یا ۶۰ اول
- پیش‌بینی واکنش بازار (برگشت / واگرایی / گذشتن)
- زون‌های مهم از کندل‌های دوجی روزانه و هفتگی (با تاریخ میلادی و قیمت شروع/پایان)
- تشخیص الگوی کندلی M5
- تیکت ورود با مدیریت ریسک
- رابط فارسی RTL با تم خاکستری + پاستلی

## اجرا

### پیش‌نیازها
- Node.js 18+
- Expo CLI: `npm install -g expo-cli`
- Android Studio (برای emulator) یا دستگاه فیزیکی

### نصب و اجرا
```bash
cd android-app
npm install
npm start
# یا
npx expo start
```

سپس:
- برای اجرا در emulator: `a` را در ترمینال بزنید
- برای اجرا روی گوشی: برنامه **Expo Go** را نصب کنید و QR را اسکن کنید
- برای اجرا در وب: `w` را بزنید

### ساخت APK (برای نصب مستقیم روی گوشی)

#### روش ۱: EAS Build (آنلاین، پیشنهادی)
```bash
# نصب eas-cli
npm install -g eas-cli

# ورود به حساب Expo
eas login

# ساخت پروژه
eas build:configure

# ساخت APK
eas build -p android --profile preview
```

بعد از چند دقیقه، لینک دانلود APK به شما داده می‌شود.

#### روش ۲: Build محلی (نیاز به Android Studio)
```bash
# پیش‌نیاز: Java JDK 17 و Android SDK
npx expo prebuild --platform android
cd android
./gradlew assembleRelease
# APK در android/app/build/outputs/apk/release/
```

## تنظیم API

در فایل `App.tsx`، خط زیر را پیدا کنید:
```typescript
const API_BASE = 'https://preview-chat-43ca7d06-8757-4f60-9c2b-6b4eae683f37.space-z.ai';
```

و آن را به آدرس API خودتان (نسخه deploy شده از پروژه Next.js) تغییر دهید.

## انتشار

برای انتشار در Google Play:
```bash
eas build -p android --profile production
eas submit -p android
```

نیاز به حساب Google Play Developer ($۲۵ یک‌بار).
