import logging
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

# Telegramdan olingan TOKEN va bot username-ni qo'ying
TOKEN = "8032069795:AAHYs-pNehtSl9VNRF-qu-hNkS1LmoC8aL0"
BOT_USERNAME = "ANONIMSAVOL_JAVOB_BOT"
OWNER_ID = 1031286702  # Bot yaratuvchisining Telegram ID'si

# Logger sozlash
logging.basicConfig(level=logging.INFO)

# Bot va dispatcher obyektlari
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Ma'lumotlar bazasini yaratish
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        user_id INTEGER UNIQUE
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS active_chats (
        user_id INTEGER PRIMARY KEY,
        chat_partner INTEGER
    )
""")
conn.commit()

# Tugmalar menyusi
def main_keyboard(user_id):
    buttons = [[KeyboardButton(text="Havolamni ko'rsat")]]
    
    if user_id == OWNER_ID:
        buttons.append([KeyboardButton(text="Havolani kiriting")])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=False)

# /start buyrug'iga javob
@dp.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    chat_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    args = message.text.split()
    
    if len(args) > 1:  # Kimningdir havolasini bosgan bo'lsa
        chat_partner = int(args[1])
        if chat_partner != user_id:
            cursor.execute("INSERT OR REPLACE INTO active_chats (user_id, chat_partner) VALUES (?, ?)", (user_id, chat_partner))
            conn.commit()
            await message.answer("Xabaringizni kiriting:", reply_markup=main_keyboard(user_id))
            return
    
    await message.answer(f"Assalomu alaykum anonim yozishmalarga xush kelibsiz!\nSizning havolangiz:\n{chat_link}", reply_markup=main_keyboard(user_id))

# Tugmalarni qayta ishlash
@dp.message()
async def handle_buttons(message: Message):
    user_id = message.from_user.id
    text = message.text
    
    if text == "Havolamni ko'rsat":
        chat_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        await message.answer(f"Sizning havolangiz:\n{chat_link}", reply_markup=main_keyboard(user_id))
    
    elif text == "Havolani kiriting" and user_id == OWNER_ID:
        await message.answer("Havolani yuboring:")
    
    elif text.startswith("https://t.me/") and user_id == OWNER_ID:
        user_id_from_link = text.split("?start=")[-1]
        if user_id_from_link.isdigit():
            user_id_from_link = int(user_id_from_link)
            try:
                user_profile = await bot.get_chat(user_id_from_link)
                profile_info = (
                    f"🆔 ID: {user_profile.id}\n"
                    f"👤 Ism: {user_profile.full_name}\n"
                    f"📛 Username: @{user_profile.username if user_profile.username else 'Username yo‘q'}"
                )
                await message.answer(f"Havolaga tegishli profil:\n{profile_info}")
            except Exception as e:
                await message.answer("Bu havolaga tegishli profil topilmadi.")
        else:
            await message.answer("Bu noto‘g‘ri havola.")
    
    else:
        cursor.execute("SELECT chat_partner FROM active_chats WHERE user_id = ?", (user_id,))
        chat_partner = cursor.fetchone()
        
        if chat_partner:
            receiver = chat_partner[0]
            sender_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            reply_text = f"{sender_link}\n<b>{message.text}</b>"
            
            await bot.send_message(receiver, reply_text, parse_mode="HTML")
            await message.answer("Xabaringiz jo'natildi!", reply_markup=main_keyboard(user_id))
            cursor.execute("DELETE FROM active_chats WHERE user_id = ?", (user_id,))
            conn.commit()
        else:
            chat_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            await message.answer(f"Sizning havolangiz:\n{chat_link}", reply_markup=main_keyboard(user_id))

# Botni ishga tushirish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
