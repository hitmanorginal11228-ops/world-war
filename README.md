# 🌍 World War Telegram Bot

ربات استراتژی جنگ جهانی برای تلگرام.

## امکانات
- انتخاب و تغییر کشور
- پنل دارایی‌ها
- نیروی زمینی، هوایی، دریایی
- پدافند، تانک، توپخانه، موشک و تجهیزات استراتژیک
- آیتم هسته‌ای صرفاً به‌عنوان مکانیک بازی
- اقتصاد و درآمد روزانه
- کارخانه، صنعت خودرو، معدن و نفت
- هتل، بندر، فرودگاه و پایگاه جنگی
- تعیین فرمانده
- بیانیه رسمی
- اتحاد و اتحاد دوستانه
- وام تا 100 میلیون با سررسید دو روز
- تجارت دریایی و هوایی به‌عنوان اسکلت
- دعوت دوستان
- PostgreSQL/SQLite
- Render Worker
- Docker

## اجرای محلی
```bash
pip install -r requirements.txt
```

Linux/macOS:
```bash
export BOT_TOKEN="TOKEN"
python bot.py
```

Windows PowerShell:
```powershell
$env:BOT_TOKEN="TOKEN"
python bot.py
```

## Render
یک Worker بساز، Repository را وصل کن و این Environment Variables را قرار بده:
- `BOT_TOKEN`
- `DATABASE_URL`

برای PostgreSQL مقدار `DATABASE_URL` را از دیتابیس Render بگیر.

توکن BotFather را داخل GitHub commit نکن.
