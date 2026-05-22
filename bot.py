import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, 
                          filters, CallbackQueryHandler, ContextTypes, ConversationHandler)

ADMIN_ID = 8086545587
# Admin bosqichlari
ADDING_TASK = 1

logging.basicConfig(level=logging.INFO)

# DB INIT
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, refs INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, reward INTEGER, link TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS referrals (referred_id INTEGER PRIMARY KEY, inviter_id INTEGER)')
    conn.commit()
    conn.close()

init_db()

# Menyu funksiyasi
def get_main_menu(user_id):
    keyboard = [["👤 Profil", "⚔️ Ligalar"], ["🔑 Vazifalar", "🎁 Bonus"], ["🎮 O'yinlar", "🧩 Testlar"]]
    if user_id == ADMIN_ID:
        keyboard.append(["🛠 Admin Panel"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Admin Panel
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    keyboard = [
        [InlineKeyboardButton("➕ Vazifa qo'shish", callback_data='add_task')],
        [InlineKeyboardButton("📋 Vazifalarni ko'rish", callback_data='view_tasks')]
    ]
    await update.message.reply_text("Admin boshqaruv paneli:", reply_markup=InlineKeyboardMarkup(keyboard))

# Vazifa qo'shish jarayoni
async def ask_task_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("Vazifa ma'lumotlarini 'Nomi|Narxi|Link' formatida yozing:")
    return ADDING_TASK

async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = update.message.text.split("|")
        conn = sqlite3.connect('bot_data.db')
        conn.execute("INSERT INTO tasks (name, reward, link) VALUES (?, ?, ?)", (data[0], int(data[1]), data[2]))
        conn.commit()
        conn.close()
        await update.message.reply_text("✅ Vazifa qo'shildi!", reply_markup=get_main_menu(ADMIN_ID))
    except:
        await update.message.reply_text("❌ Xatolik! Qaytadan urinib ko'ring (format: Nomi|Narxi|Link)")
    return ConversationHandler.END

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("Salom! Botimizga xush kelibsiz.", reply_markup=get_main_menu(user_id))

# Conversation Handler
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_task_details, pattern='add_task')],
    states={ADDING_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_task)]},
    fallbacks=[]
)

if __name__ == '__main__':
    TOKEN = "8850891918:AAEXajgiKjFGRq-ZZeXO--Sm8Ck-_LCdZdM"
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Text("🛠 Admin Panel"), admin_menu))
    application.add_handler(conv_handler)
    application.run_polling()
        
