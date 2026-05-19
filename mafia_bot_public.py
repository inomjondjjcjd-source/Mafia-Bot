import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8303235336:AAEk3J42idbz1KcamIWPC2L3_IlROPeoadI"
ADMIN_ID = 8086545587

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Admin panel tugmalari
admin_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📊 Foydalanuvchilarni boshqarish")],
    [KeyboardButton(text="🎟 Promokod yaratish")],
    [KeyboardButton(text="🍎 Apple of Fortune Cheat")]
], resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Xush kelibsiz, Admin!", reply_markup=admin_kb)
    else:
        await message.answer("Salom! O'yinimizga xush kelibsiz.")

@dp.message(F.text == "🎟 Promokod yaratish")
async def create_promo(message: types.Message):
    await message.answer("Promokod va narxni yozing (masalan: PROMO100 50000)")

# Bu yerda Apple of Fortune algoritmi va boshqa funksiyalarni yozish kerak.
# Cheat uchun funksiya:
@dp.message(F.text == "🍎 Apple of Fortune Cheat")
async def get_cheat(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        # 10 qator, 120x gacha logic bu yerda bo'ladi
        await message.answer("🍎 Apple of Fortune bashorati: [3, 1, 4, 2, 5...]")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
