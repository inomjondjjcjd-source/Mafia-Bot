from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

TOKEN = "8849139822:AAGMl30M3Xm-IOxiWE6n8BS8NVOQyfhACGw"
ADMIN_ID = 5829527078 # Sizning shaxsiy ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Pastki (Reply) tugmalar
    reply_keyboard = [
        ["📦 Katalog", "🛒 Savat"],
        ["🚚 Yetkazib berish", "📞 Aloqa"]
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    # Inline tugmalar
    inline_keyboard = [
        [InlineKeyboardButton("🔍 Tovarlarni ko'rish", callback_data='catalog')],
        # Admin bilan bog'lanish (tg://user?id=... orqali to'g'ridan-to'g'ri lichkaga olib o'tadi)
        [InlineKeyboardButton("💬 Admin bilan bog'lanish", url=f"tg://user?id={ADMIN_ID}")],
        [InlineKeyboardButton("ℹ️ Biz haqimizda", callback_data='about')]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)
    
    await update.message.reply_text(
        "Assalomu alaykum! *Tulpor yemlari* savdo botiga xush kelibsiz. "
        "Quyidagi menyu orqali kerakli bo'limni tanlang:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    await update.message.reply_text("Yoki qo'shimcha imkoniyatlardan foydalaning:", reply_markup=inline_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'about':
        await query.message.reply_text(
            "Assalomu alaykum! Biz *Tulpor savdo markazi*. "
            "5 yildan beri hizmat ko'rsatamiz. Bizning tovarlar sifati a'lo, narxi esa hamyonbop. "
            "Sizlarni do'konimizda kutib qolamiz! 🐎🌐",
            parse_mode='Markdown'
        )
    elif query.data == 'catalog':
        await query.message.reply_text("Hozircha tovarlar yuklanmoqda...")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot Tulpor yemlari nomi bilan ishga tushdi...")
    app.run_polling()
    
