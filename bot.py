import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# ADMIN ID ni o'z ID raqamingizga almashtiring
ADMIN_ID = 123456789  # <--- Buni o'z ID raqamingiz bilan almashtiring!

logging.basicConfig(level=logging.INFO)

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, refs INTEGER DEFAULT 0)''')
    # Vazifalar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, reward INTEGER, link TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Admin panel menyusi
def get_main_menu(user_id):
    keyboard = [["👤 Profil", "⚔️ Ligalar"], ["🔑 Vazifalar", "🎁 Bonus"], ["🎮 O'yinlar", "🧩 Testlar"]]
    if user_id == ADMIN_ID:
        keyboard.append(["🛠 Admin Panel"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("Xush kelibsiz!", reply_markup=get_main_menu(user_id))

# Admin Panel funksiyasi
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    keyboard = [
        [InlineKeyboardButton("➕ Vazifa qo'shish", callback_data='add_task')],
        [InlineKeyboardButton("📋 Vazifalarni ko'rish", callback_data='view_tasks')]
    ]
    await update.message.reply_text("Admin boshqaruv paneli:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == 'add_task':
        await query.message.reply_text("Vazifa qo'shish uchun format: /add_task Nomi|Narxi|Link")
    await query.answer()

async def add_task_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    data = " ".join(context.args).split("|")
    if len(data) == 3:
        conn = sqlite3.connect('bot_data.db')
        conn.execute("INSERT INTO tasks (name, reward, link) VALUES (?, ?, ?)", (data[0], int(data[1]), data[2]))
        conn.commit()
        conn.close()
        await update.message.reply_text("✅ Vazifa muvaffaqiyatli qo'shildi!")

if __name__ == '__main__':
    TOKEN = "8850891918:AAEXajgiKjFGRq-ZZeXO--Sm8Ck-_LCdZdM"
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_task", add_task_cmd))
    application.add_handler(MessageHandler(filters.Text("🛠 Admin Panel"), admin_panel))
    application.run_polling()
            
