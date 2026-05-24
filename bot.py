from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8849139822:AAGMl30M3Xm-IOxiWE6n8BS8NVOQyfhACGw"
ADMIN_ID = 5829527078 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Pastki menyu tugmalari (Yangilangan)
    reply_keyboard = [
        ["📦 Katalog", "🛒 Savat"],
        ["🚚 Yetkazib berish", "ℹ️ Biz haqimizda"],
        ["📞 Aloqa"]
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Assalomu alaykum! *Tulpor yemlari* savdo botiga xush kelibsiz. "
        "Quyidagi menyu orqali kerakli bo'limni tanlang:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "ℹ️ Biz haqimizda":
        # Siz so'ragan alohida va ko'rinarli xabar
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━\n"
            "🐎 *BIZ HAQIMIZDA*\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Assalomu alaykum! Biz *Tulpor savdo markazi*. "
            "5 yildan beri hizmat ko'rsatamiz. \n\n"
            "✅ Bizning tovarlar sifati a'lo\n"
            "💰 Narxi esa hamyonbop\n\n"
            "Sizlarni do'konimizda kutib qolamiz! 🐎🌐",
            parse_mode='Markdown'
        )
    elif text == "📞 Aloqa":
        await update.message.reply_text(f"Admin bilan bog'lanish uchun: tg://user?id={ADMIN_ID}")
    else:
        await update.message.reply_text("Siz tanladingiz: " + text)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    # Barcha matnli xabarlarni qayta ishlaydigan handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot Tulpor yemlari nomi bilan ishga tushdi...")
    app.run_polling()
    
