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

async def download_content(url: str, message: types.Message):
    await message.reply("جاري التحميل بجودة عالية...")

    ydl_opts = {
        'outtmpl': 'media_%(id)s.%(ext)s',
        # أفضل خيار لإنستغرام: يفضل فيديو مدمج جاهز
        'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        
        # تقليل مشاكل الدمج
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
    }

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

        if os.path.exists(filename):
            os.remove(filename)

    except Exception:
        await message.reply("❌ فشل التحميل\nجرب رابط ريلز آخر")

@dp.message()
async def handle_message(message: types.Message):
    text = message.text.strip()

    if re.search(r'https?://(www\.)?(tiktok\.com|vt\.tiktok\.com|vm\.tiktok\.com)', text) or \
       re.search(r'https?://(www\.)?instagram\.com/(reel|p)/', text):
        await download_content(text, message)
    
    elif text.startswith('/start'):
        await message.reply("أرسل رابط تيك توك أو إنستغرام ريلز\n(تيك توك يعمل ممتاز - إنستغرام يحاول أفضل جودة)")
    else:
        await message.reply("أرسل رابط فيديو فقط")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ البوت شغال الآن")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
