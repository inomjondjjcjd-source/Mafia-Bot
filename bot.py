from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes, ConversationHandler

TOKEN = "8849139822:AAGMl30M3Xm-IOxiWE6n8BS8NVOQyfhACGw"
ADMIN_ID = 8086545587 # Sizning ID (Admin)

# Biz haqimizda matni
ABOUT_TEXT = "Assalomu alaykum! Biz *Tulpor savdo markazi*. 5 yildan beri hizmat ko'rsatamiz. Bizning tovarlar sifati a'lo, narxi esa hamyonbop. Sizlarni do'konimizda kutib qolamiz! 🐎🌐"

# Admin paneli holatlari
NAME, PRICE = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Pastki menyu
    reply_keyboard = [
        ["TOVARLAR 🌐", "🛒 Savat"],
        ["🚚 Yetkazib berish", "ℹ️ Biz haqimizda"],
        ["📞 Aloqa"]
    ]
    if user_id == ADMIN_ID:
        reply_keyboard.append(["🛠 Admin Panel"])
        
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Assalomu alaykum! *Tulpor yemlari* savdo botiga xush kelibsiz.",
        parse_mode='Markdown', reply_markup=reply_markup
    )

async def handle_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "ℹ️ Biz haqimizda":
        await update.message.reply_text(ABOUT_TEXT, parse_mode='Markdown')
        
    elif text == "📞 Aloqa":
        kb = [[InlineKeyboardButton("🔗 Bog'lanish", url=f"tg://user?id=5829527078")]] # Bog'lanish ID
        await update.message.reply_text("Menejer bilan bog'lanish uchun tugmani bosing:", reply_markup=InlineKeyboardMarkup(kb))
        
    elif text == "TOVARLAR 🌐":
        await update.message.reply_text("📦 Hozirda tovarlar ro'yxati tayyorlanmoqda...")
        
    elif text == "🛠 Admin Panel" and update.effective_user.id == ADMIN_ID:
        kb = [[InlineKeyboardButton("➕ Tovar qo'shish", callback_data='add_item')]]
        await update.message.reply_text("Admin boshqaruv paneli:", reply_markup=InlineKeyboardMarkup(kb))
        
    elif text == "🛒 Savat":
        await update.message.reply_text("🛒 Savatingiz bo'sh.")
    elif text == "🚚 Yetkazib berish":
        await update.message.reply_text("🚚 Yetkazib berish shartlari:\nBiz Toshkent shahri bo'ylab yetkazib beramiz.")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'add_item':
        await query.message.reply_text("Tovar nomini kiriting:")
        return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Tovar narxini kiriting:")
    return PRICE

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data['name']
    price = update.message.text
    await update.message.reply_text(f"✅ Tovar qo'shildi!\nNomi: {name}\nNarxi: {price}")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callback, pattern='add_item')],
        states={NAME: [MessageHandler(filters.TEXT, get_name)],
                PRICE: [MessageHandler(filters.TEXT, get_price)]},
        fallbacks=[]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_interaction))
    app.add_handler(conv_handler)
    app.run_polling()
    
