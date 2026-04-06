# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from dotenv import load_dotenv
import yt_dlp

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN غير موجود")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# مسار ملف الكوكيز (ضعه في نفس مجلد البوت)
COOKIES_FILE = 'cookies.txt'

async def download_content(url: str, message: types.Message):
    await message.reply("جاري التحميل بجودة عالية...")

    ydl_opts = {
        'outtmpl': 'media_%(id)s.%(ext)s',
        'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
    }

    # إضافة الكوكيز إذا كان الرابط من إنستغرام
    if os.path.exists(COOKIES_FILE):
        if "instagram.com" in url.lower() or "instagr.am" in url.lower():
            ydl_opts['cookiefile'] = COOKIES_FILE
            print(f"✅ تم استخدام ملف الكوكيز لإنستغرام")
        else:
            # يمكنك استخدامه لتيك توك أيضاً إذا أردت
            ydl_opts['cookiefile'] = COOKIES_FILE
    else:
        if "instagram.com" in url.lower() or "instagr.am" in url.lower():
            print("⚠️ ملف cookies.txt غير موجود! إنستغرام قد يفشل.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            await message.reply("❌ فشل التحميل، جرب رابط آخر")
            return

        await bot.send_video(
            chat_id=message.chat.id,
            video=FSInputFile(filename),
            caption="✅ تم التحميل بنجاح",
            supports_streaming=True
        )

        # حذف الملف بعد الإرسال
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        error_str = str(e).lower()
        if "rate-limit" in error_str or "login required" in error_str:
            await message.reply("❌ فشل التحميل بسبب قيود إنستغرام (rate limit)\nتأكد من وجود ملف cookies.txt أو حدثه")
        else:
            await message.reply("❌ فشل التحميل\nجرب رابط ريلز آخر")

@dp.message()
async def handle_message(message: types.Message):
    text = message.text.strip()

    if re.search(r'https?://(www\.)?(tiktok\.com|vt\.tiktok\.com|vm\.tiktok\.com)', text) or \
       re.search(r'https?://(www\.)?instagram\.com/(reel|p|stories|tv)/', text):
        await download_content(text, message)

    elif text.startswith('/start'):
        await message.reply(
            "أرسل رابط تيك توك أو إنستغرام ريلز\n\n"
            "✅ تيك توك: يعمل ممتاز\n"
            "✅ إنستغرام: يحتاج ملف cookies.txt للعمل بشكل مستقر"
        )
    else:
        await message.reply("أرسل رابط فيديو تيك توك أو إنستغرام ريلز فقط")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ البوت شغال الآن")
    print(f"📁 ملف الكوكيز المتوقع: {COOKIES_FILE} (ضعه بجانب الكود)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
   
