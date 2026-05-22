import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, 
                          filters, CallbackQueryHandler, ContextTypes, ConversationHandler)

ADMIN_ID = 8086545587
# Bosqichlar
NAME, REWARD, LINK = range(3)

logging.basicConfig(level=logging.INFO)

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, reward INTEGER, link TEXT)')
    conn.commit()
    conn.close()

init_db()

# Admin Panel
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    keyboard = [[InlineKeyboardButton("➕ Vazifa qo'shish", callback_data='start_add_task')]]
    await update.message.reply_text("Admin boshqaruv paneli:", reply_markup=InlineKeyboardMarkup(keyboard))

# 1. Nomi
async def start_add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("Vazifa nomini kiriting:")
    return NAME

# 2. Narxi
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Vazifa uchun necha coin beriladi? (faqat raqam):")
    return REWARD

# 3. Link
async def get_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reward'] = int(update.message.text)
    await update.message.reply_text("Kanal yoki guruh linkini kiriting:")
    return LINK

# Saqlash
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('bot_data.db')
    conn.execute("INSERT INTO tasks (name, reward, link) VALUES (?, ?, ?)", 
                 (context.user_data['name'], context.user_data['reward'], update.message.text))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ Vazifa muvaffaqiyatli saqlandi!")
    return ConversationHandler.END

# Conversation Handler
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_add_task, pattern='start_add_task')],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        REWARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_reward)],
        LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)],
    },
    fallbacks=[]
)

if __name__ == '__main__':
    TOKEN = "8850891918:AAEXajgiKjFGRq-ZZeXO--Sm8Ck-_LCdZdM"
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Assalomu alaykum!")))
    application.add_handler(MessageHandler(filters.Text("🛠 Admin Panel"), admin_menu))
    application.add_handler(conv_handler)
    application.run_polling()
  
