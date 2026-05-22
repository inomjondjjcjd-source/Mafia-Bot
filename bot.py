import logging
import os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Loglarni sozlash
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlamoqda!"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# Bot menyusi
def get_main_menu():
    keyboard = [
        [KeyboardButton("👤 Profil"), KeyboardButton("⚔️ Ligalar")],
        [KeyboardButton("🔑 Vazifalar"), KeyboardButton("🎁 Bonus")],
        [KeyboardButton("🎮 O'yinlar"), KeyboardButton("🧩 Testlar")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Xush kelibsiz! Bot ishga tushdi. Quyidagi menyudan birini tanlang:",
        reply_markup=get_main_menu()
    )

# Xabarlarni boshqarish
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "👤 Profil":
        await update.message.reply_text("Sizning balansingiz: 0 coins.")
    elif text == "🧩 Testlar":
        await update.message.reply_text("Savol: 2 + 2 nechchi bo'ladi?")
    else:
        await update.message.reply_text(f"Siz tanladingiz: {text}")

if __name__ == '__main__':
    # Flask serverini fon rejimida ishga tushirish
    t = Thread(target=run)
    t.start()
    
    TOKEN = "8850891918:AAEXajgiKjFGRq-ZZeXO--Sm8Ck-_LCdZdM"
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    application.run_polling()
    
