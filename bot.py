import logging
import os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Loglarni sozlash
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)

@app.route('/')
def home():
    return "Gresscoin Bot Profil ishlamoqda!"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# Asosiy menyu
def get_main_menu():
    keyboard = [
        [KeyboardButton("👤 Profil"), KeyboardButton("⚔️ Ligalar")],
        [KeyboardButton("🔑 Vazifalar"), KeyboardButton("🎁 Bonus")],
        [KeyboardButton("🎮 O'yinlar"), KeyboardButton("🧩 Testlar")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Profil menyusi
def get_profile_inline_menu():
    keyboard = [
        [InlineKeyboardButton("🔗 Referal havolani olish", callback_data='get_ref')],
        [InlineKeyboardButton("👥 Referallarni ko'rish", callback_data='see_refs')],
        [InlineKeyboardButton("🔏 Xavfsizlik", callback_data='security'), InlineKeyboardButton("📊 Statistika", callback_data='stats')]
    ]
    return InlineKeyboardMarkup(keyboard)

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Xush kelibsiz! Quyidagi menyudan birini tanlang:",
        reply_markup=get_main_menu()
    )

# Profil xabarini yuborish
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    profile_text = (
        f"👤 Foydalanuvchi: {user.mention_html()}\n"
        f"▪ Gresscoin: 0 ta\n"
        f"👥 Referal: 0 ta\n"
        f"🏆 Liga: Boshlang'ich (Keyingi liga: Bilimdon)\n"
        f"📈 Liga bo'yicha reyting: N/A\n"
        f"🇺🇿 O'zbekiston bo'yicha reyting: N/A"
    )
    if update.message:
        await update.message.reply_html(profile_text, reply_markup=get_profile_inline_menu())

# Xabarlarni boshqarish
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "👤 Profil":
        await show_profile(update, context)
    else:
        await update.message.reply_text(f"Siz tanladingiz: {text}. Tez orada funksiyalar ishga tushadi!")

if __name__ == '__main__':
    t = Thread(target=run)
    t.start()
    
    # YANGI TOKEN
    TOKEN = "8850891918:AAEXajgiKjFGRq-ZZeXO--Sm8Ck-_LCdZdM"
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    application.run_polling()
    
