
# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import re
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from dotenv import load_dotenv
import yt_dlp

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN غير موجود في ملف .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ====================== تحديث yt-dlp تلقائياً ======================
async def update_ytdlp():
    try:
        print("🔄 جاري تحديث yt-dlp إلى أحدث إصدار...")
        result = subprocess.run(["pip", "install", "--upgrade", "yt-dlp"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ تم تحديث yt-dlp بنجاح")
        else:
            print(f"⚠️ تحذير: فشل تحديث yt-dlp\n{result.stderr}")
    except Exception as e:
        print(f"⚠️ خطأ أثناء تحديث yt-dlp: {e}")

# ====================== خيارات التحميل المحسنة ======================
def get_ydl_opts():
    return {
        'outtmpl': 'media_%(id)s.%(ext)s',
        'format': 'bestvideo*+bestaudio/best',  # أفضل جودة ممكنة
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'retries': 10,
        'fragment_retries': 10,
        'concurrent_fragment_downloads': 5,      # أسرع تحميل
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'
        },
        # إذا أردت تفعيل الكوكيز (مفيد جداً لإنستغرام):
        # 'cookiesfrombrowser': ('chrome',),     # أو 'firefox'
        # 'cookiefile': 'cookies.txt',           # أو استخدم ملف cookies
    }

async def download_content(url: str, message: types.Message):
    await message.reply("⏳ جاري التحميل... يرجى الانتظار")

    ydl_opts = get_ydl_opts()

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            await message.reply("❌ فشل في حفظ الملف، جرب رابط آخر")
            return

        # إرسال الفيديو
        await bot.send_video(
            chat_id=message.chat.id,
            video=FSInputFile(filename),
            caption="✅ تم التحميل بنجاح\n@Wdmakkitetrisbot",
            supports_streaming=True,
            # يمكنك إضافة: thumb=thumbnail إذا أردت
        )

        # حذف الملف بعد الإرسال
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        logging.error(f"خطأ في تحميل {url}: {str(e)}")
        await message.reply("❌ فشل التحميل\nالرابط قد يكون خاص أو محمي\nجرب رابط آخر أو انتظر قليلاً")

@dp.message()
async def handle_message(message: types.Message):
    text = message.text.strip() if message.text else ""

    # كشف الروابط
    if re.search(r'https?://', text):
        if re.search(r'(tiktok\.com|vt\.tiktok\.com|vm\.tiktok\.com)', text) or \
           re.search(r'instagram\.com/(reel|p|stories|tv)/', text):
            await download_content(text, message)
        else:
            await message.reply("❌ الرابط غير مدعوم\nأرسل رابط تيك توك أو إنستغرام ريلز فقط")
    
    elif text.startswith('/start'):
        await message.reply(
            "👋 مرحبا!\n"
            "أرسل رابط فيديو من **تيك توك** أو **إنستغرام ريلز** وسأقوم بتحميله لك.\n\n"
            "مثال:\n"
            "https://www.tiktok.com/@user/video/123456789\n"
            "https://www.instagram.com/reel/ABC123/"
        )
    else:
        await message.reply("❌ أرسل رابط فيديو من تيك توك أو إنستغرام فقط")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # تحديث yt-dlp عند بدء البوت
    await update_ytdlp()
    
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ البوت يعمل الآن...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
