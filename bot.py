from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8849139822:AAGMl30M3Xm-IOxiWE6n8BS8NVOQyfhACGw"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Asosiy menyu (Pastki tugmalar)
    reply_keyboard = [
        ["📦 Katalog", "🛒 Savat"],
        ["🚚 Yetkazib berish", "📞 Aloqa"]
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    # 2. Inline menyu (Xabar ichidagi tugmalar)
    inline_keyboard = [
        [InlineKeyboardButton("🔍 Tovarlarni ko'rish", callback_data='catalog')],
        [InlineKeyboardButton("💬 Admin bilan bog'lanish", url="https://t.me/SizningUsernameingiz")],
        [InlineKeyboardButton("ℹ️ Biz haqimizda", callback_data='about')]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)
    
    await update.message.reply_text(
        "Assalomu alaykum! Yem-xashak savdo botiga xush kelibsiz. "
        "Quyidagi menyu orqali kerakli bo'limni tanlang:",
        reply_markup=reply_markup
    )
    await update.message.reply_text("Yoki qo'shimcha imkoniyatlardan foydalaning:", reply_markup=inline_markup)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot ishga tushdi...")
    app.run_polling()
  
