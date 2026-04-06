# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import re
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import yt_dlp

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN غير موجود")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# قاعدة بيانات بسيطة للحد اليومي
conn = sqlite3.connect('users.db')
conn.execute('''CREATE TABLE IF NOT EXISTS users 
                (user_id INTEGER PRIMARY KEY, count INTEGER, last_reset TEXT)''')
conn.commit()

def check_daily_limit(user_id: int) -> bool:
    today = datetime.now().date().isoformat()
    cursor = conn.execute("SELECT count, last_reset FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    
    if not row or row[1] != today:
        conn.execute("REPLACE INTO users (user_id, count, last_reset) VALUES (?, 1, ?)", (user_id, today))
        conn.commit()
        return True
    
    if row[0] < 10:
        conn.execute("UPDATE users SET count = count + 1 WHERE user_id=?", (user_id,))
        conn.commit()
        return True
    return False

async def download_content(url: str, message: types.Message):
    user_id = message.from_user.id
    
    if not check_daily_limit(user_id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="اشتراك بريميوم (غير محدود)", callback_data="premium")]
        ])
        await message.reply(
            "❌ لقد وصلت إلى الحد اليومي (10 تحميلات).\n\n"
            "اشترك في البريميوم لتحميل غير محدود + جودة أعلى:",
            reply_markup=keyboard
        )
        return

    await message.reply("جاري التحميل بجودة عالية... ⏳")

    ydl_opts = {
        'outtmpl': 'media_%(id)s.%(ext)s',
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
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
            caption="✅ تم التحميل بنجاح\n(10 تحميلات يوميًا للمجاني)",
            supports_streaming=True
        )

        if os.path.exists(filename):
            os.remove(filename)

    except Exception:
        await message.reply("❌ فشل التحميل، جرب رابط ريلز أو تيك توك آخر")

@dp.message()
async def handle_message(message: types.Message):
    text = message.text.strip()

    if re.search(r'https?://(www\.)?(tiktok\.com|vt\.tiktok\.com|vm\.tiktok\.com)', text) or \
       re.search(r'https?://(www\.)?instagram\.com/(reel|p)/', text):
        await download_content(text, message)
    
    elif text.startswith('/start'):
        await message.reply(
            "👋 مرحبا!\n\n"
            "أرسل رابط تيك توك أو إنستغرام ريلز\n"
            "• حد يومي: 10 تحميلات مجانية\n"
            "• بريميوم: غير محدود + جودة أعلى"
        )
    else:
        await message.reply("أرسل رابط فيديو فقط")

# معالجة زر البريميوم
@dp.callback_query(lambda c: c.data == "premium")
async def premium_handler(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.reply(
        "✅ نظام البريميوم قيد التطوير...\n\n"
        "حالياً يمكنك التواصل معي للاشتراك اليدوي.\n"
        "البريميوم = تحميل غير محدود + أولوية + جودة HD"
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ البوت شغال الآن - مع حد يومي + بريميوم")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
