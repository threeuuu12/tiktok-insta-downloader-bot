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
    await message.reply("جاري التحميل... ⏳")

    ydl_opts = {
        'outtmpl': 'media_%(id)s.%(ext)s',
        'format': 'best[ext=mp4]/best',
        'noplaylist': True,
        'quiet': False,
        'no_warnings': False,
        'merge_output_format': 'mp4',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'
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

    except Exception as e:
        logging.error(f"Download error: {e}")
        await message.reply("❌ فشل التحميل\nجرب رابط آخر أو انتظر قليلاً")

@dp.message()
async def handle_message(message: types.Message):
    text = message.text.strip()

    if re.search(r'https?://(www\.)?(tiktok\.com|vt\.tiktok\.com|vm\.tiktok\.com)', text) or \
       re.search(r'https?://(www\.)?instagram\.com/(reel|p)/', text):
        await download_content(text, message)
    elif text.startswith('/start'):
        await message.reply("أرسل رابط تيك توك أو إنستغرام ريلز")
    else:
        await message.reply("أرسل رابط فيديو فقط")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ البوت شغال الآن")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
