from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

TOKEN = "8849139822:AAGMl30M3Xm-IOxiWE6n8BS8NVOQyfhACGw"
ADMIN_ID = 5829527078 

# Biz haqimizda matni
ABOUT_TEXT = "Assalomu alaykum! Biz *Tulpor savdo markazi*. 5 yildan beri hizmat ko'rsatamiz. Bizning tovarlar sifati a'lo, narxi esa hamyonbop. Sizlarni do'konimizda kutib qolamiz! 🐎🌐"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Pastki menyu tugmalari
    reply_keyboard = [
        ["📦 Katalog", "🛒 Savat"],
        ["🚚 Yetkazib berish", "ℹ️ Biz haqimizda"],
        ["📞 Aloqa"]
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    # Inline tugmalar (start bosilganda chiqadigan)
    inline_keyboard = [
        [InlineKeyboardButton("🔍 Tovarlarni ko'rish", callback_data='catalog')],
        [InlineKeyboardButton("💬 Admin bilan bog'lanish", url=f"tg://user?id={ADMIN_ID}")],
        [InlineKeyboardButton("ℹ️ Biz haqimizda", callback_data='about')]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)
    
    await update.message.reply_text(
        "Assalomu alaykum! *Tulpor yemlari* savdo botiga xush kelibsiz. Quyidagi menyu orqali kerakli bo'limni tanlang:",
        parse_mode='Markdown', reply_markup=reply_markup
    )
    await update.message.reply_text("Yoki qo'shimcha imkoniyatlardan foydalaning:", reply_markup=inline_markup)

async def handle_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Callback (Inline tugmalar) bosilganda
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == 'about':
            await query.message.reply_text(ABOUT_TEXT, parse_mode='Markdown')
        elif query.data == 'catalog':
            await query.message.reply_text("📦 Katalog bo'limi ustida ishlamoqdamiz...")
    
    # Text (Reply tugmalar) bosilganda
    elif update.message:
        text = update.message.text
        if text == "ℹ️ Biz haqimizda":
            await update.message.reply_text(ABOUT_TEXT, parse_mode='Markdown')
        elif text == "📞 Aloqa":
            # Aynan siz so'ragan alohida inline tugma
            kb = [[InlineKeyboardButton("🔗 Bog'lanish", url=f"tg://user?id={ADMIN_ID}")]]
            await update.message.reply_text("Menejer bilan bog'lanish uchun pastdagi tugmani bosing:", reply_markup=InlineKeyboardMarkup(kb))
        elif text == "📦 Katalog":
            await update.message.reply_text("📦 Katalog bo'limi ustida ishlamoqdamiz...")
        elif text == "🛒 Savat":
            await update.message.reply_text("🛒 Savatingiz bo'sh.")
        elif text == "🚚 Yetkazib berish":
            await update.message.reply_text("🚚 Yetkazib berish shartlari:\nBiz Toshkent shahri bo'ylab yetkazib beramiz.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_interaction))
    app.add_handler(CallbackQueryHandler(handle_interaction))
    print("Bot Tulpor yemlari nomi bilan ishga tushdi...")
    app.run_polling()
            
