import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Loglarni sozlash
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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
        "Xush kelibsiz! QuizCash botiga xush kelibsiz. Quyidagi menyudan birini tanlang:",
        reply_markup=get_main_menu()
    )

# Menyudagi tugmalar uchun handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "👤 Profil":
        await update.message.reply_text("Sizning balansingiz: 0 coins. Hozircha darajangiz: Yangi boshlovchi.")
    elif text == "🧩 Testlar":
        await update.message.reply_text("Savol: 2 + 2 nechchi bo'ladi? (Javobni yozing)")
    else:
        await update.message.reply_text(f"Siz tanladingiz: {text}. Bu funksiya tez orada ishga tushadi!")

if __name__ == '__main__':
    # Tokeningiz qo'yildi
    TOKEN = "7224154869:AAESKaJhYAPiu-tFFSS6pFYrsCmmMvWlbQ8"
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot ishga tushdi...")
    application.run_polling()
  
