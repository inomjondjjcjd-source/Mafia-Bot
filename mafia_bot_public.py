import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Loglarni sozlash
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Tokenni Render'dan yoki toʻgʻridan-toʻgʻri olish
TOKEN = os.environ.get("API_TOKEN", "8798029139:AAFqEcEt-q6BhXr3an0jZMjZjYsBY_C7Z0w")

# /start buyrugʻi kelganda bot beradigan javob
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Mafia bot muvaffaqiyatli ishga tushdi. Oʻyinni boshlashga tayyormisiz?")

def main():
    # Yangi kutubxona standarti bo'yicha botni yaratish
    application = Application.builder().token(TOKEN).build()
    
    # Buyruqlarni ro'yxatga olish
    application.add_handler(CommandHandler("start", start))
    
    # Botni fonda doimiy ishga tushirish (Hech qanday soxta portlarsiz)
    logging.info("Bot ishga tushmoqda...")
    application.run_polling()

if __name__ == '__main__':
    main()
    
