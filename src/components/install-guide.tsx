'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { X, Smartphone, Download, Share, Bell } from 'lucide-react';

export function InstallGuide({ onClose }: { onClose: () => void }) {
  const [platform, setPlatform] = useState<'android' | 'ios' | null>(null);

  // Detect platform
  useState(() => {
    if (typeof navigator !== 'undefined') {
      const ua = navigator.userAgent.toLowerCase();
      if (/iphone|ipad|ipod/.test(ua)) setPlatform('ios');
      else if (/android/.test(ua)) setPlatform('android');
    }
  });

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-4">
      <Card className="w-full max-w-md bg-slate-900 border-slate-700 p-5 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Smartphone className="w-5 h-5 text-amber-400" />
            <h2 className="text-base font-bold">نصب روی گوشی</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="space-y-4 text-sm">
          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
            <div className="font-bold text-amber-300 mb-1">این یک PWA است</div>
            <p className="text-xs text-slate-300 leading-relaxed">
              این ویجت یک وب‌اپلیکیشن قابل نصب (PWA) است. روی گوشی نصب می‌شود،
              آیکون روی صفحه اصلی می‌گذارد، تمام‌صفحه باز می‌شود و آفلاین هم کار می‌کند.
            </p>
          </div>

          <div className="flex gap-2">
            <Button
              variant={platform === 'android' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setPlatform('android')}
              className={platform === 'android' ? 'bg-amber-500 text-slate-900' : ''}
            >
              اندروید
            </Button>
            <Button
              variant={platform === 'ios' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setPlatform('ios')}
              className={platform === 'ios' ? 'bg-amber-500 text-slate-900' : ''}
            >
              آیفون
            </Button>
          </div>

          {platform === 'android' && (
            <div className="space-y-3">
              <h3 className="font-bold text-amber-300">نصب روی اندروید (Chrome)</h3>
              <ol className="space-y-2 text-xs text-slate-300 list-decimal pr-4">
                <li>این صفحه را در <strong>Chrome</strong> باز کنید (اگر در مرورگر دیگری هستید، کپی کنید و در Chrome باز کنید).</li>
                <li>منوی سه‌نقطه (<strong>⋮</strong>) را در بالا سمت راست بزنید.</li>
                <li>گزینه <strong>«Add to Home screen»</strong> یا <strong>«افزودن به صفحه اصلی»</strong> را انتخاب کنید.</li>
                <li>نام «RSI طلا» را تأیید کنید (یا تغییر دهید).</li>
                <li>آیکون روی صفحه اصلی گوشی ظاهر می‌شود.</li>
                <li>با لمس آن، ویجت تمام‌صفحه و بدون نوار مرورگر باز می‌شود.</li>
              </ol>
              <div className="p-2 rounded bg-slate-800/50 text-[11px] text-slate-400">
                <strong className="text-slate-300">نکته:</strong> اگر گزینه Add to Home screen را نمی‌بینید،
                چند ثانیه صبر کنید تا صفحه کامل لود شود، سپس دوباره منو را باز کنید.
                در Samsung Internet هم گزینه مشابهی به نام «Add page to» وجود دارد.
              </div>
            </div>
          )}

          {platform === 'ios' && (
            <div className="space-y-3">
              <h3 className="font-bold text-amber-300">نصب روی آیفون (Safari)</h3>
              <ol className="space-y-2 text-xs text-slate-300 list-decimal pr-4">
                <li>این صفحه را در <strong>Safari</strong> باز کنید (فقط Safari از PWA پشتیبانی می‌کند).</li>
                <li>دکمه <strong>Share</strong> (آیکون مربع با فلش رو به بالا <Share className="w-3 h-3 inline" />) را در پایین بزنید.</li>
                <li>در منوی باز شده، <strong>«Add to Home Screen»</strong> یا <strong>«افزودن به صفحه اصلی»</strong> را انتخاب کنید.</li>
                <li>نام «RSI طلا» را تأیید کنید.</li>
                <li>دکمه <strong>Add</strong> را بزنید.</li>
                <li>آیکون روی صفحه اصلی ظاهر می‌شود.</li>
              </ol>
              <div className="p-2 rounded bg-slate-800/50 text-[11px] text-slate-400">
                <strong className="text-slate-300">نکته:</strong> در آیفون، Chrome و Firefox از PWA پشتیبانی نمی‌کنند.
                حتماً از Safari استفاده کنید.
              </div>
            </div>
          )}

          {!platform && (
            <div className="text-xs text-slate-400 p-3 rounded bg-slate-800/40 text-center">
              پلتفرم خود را انتخاب کنید تا راهنمای نصب را ببینید
            </div>
          )}

          <div className="border-t border-slate-800 pt-3 space-y-2">
            <h3 className="font-bold text-amber-300 text-sm">ویژگی‌های بعد از نصب</h3>
            <ul className="space-y-1.5 text-xs text-slate-300">
              <li className="flex items-start gap-2">
                <Smartphone className="w-3 h-3 text-amber-400 mt-0.5 flex-shrink-0" />
                تمام‌صفحه باز می‌شود، بدون نوار آدرس و نوار وضعیت
              </li>
              <li className="flex items-start gap-2">
                <Download className="w-3 h-3 text-amber-400 mt-0.5 flex-shrink-0" />
                آفلاین کار می‌کند (صفحه اصلی cache شده است)
              </li>
              <li className="flex items-start gap-2">
                <Bell className="w-3 h-3 text-amber-400 mt-0.5 flex-shrink-0" />
                هر ۳۰ ثانیه داده زنده از Binance دریافت می‌کند
              </li>
            </ul>
          </div>

          <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30 text-xs text-blue-200">
            <strong>تفاوت با ویجت واقعی اندروید:</strong> این PWA یک آیکون اپ است که با یک ضربه باز می‌شود.
            برای داشتن ویجتی که مستقیماً روی صفحه اصلی بدون باز کردن اپ نمایش داده شود،
            باید نسخه native با Kotlin ساخته شود که در صورت تمایل می‌توانم کد آن را هم بنویسم.
          </div>
        </div>
      </Card>
    </div>
  );
}
