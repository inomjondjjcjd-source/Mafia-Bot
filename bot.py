import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# Ma'lumotlar bazasini sozlash
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, balance INTEGER, refs INTEGER, inviter_id INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# Baza bilan ishlash funksiyalari
def update_user(user_id, balance=None, refs=None, inviter_id=None):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, balance, refs, inviter_id) VALUES (?, 0, 0, ?)", (user_id, inviter_id))
    if balance is not None: cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (balance, user_id))
    if refs is not None: cursor.execute("UPDATE users SET refs = refs + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance, refs FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    return data or (0, 0)

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    # Referal orqali kirish
    if args and args[0].startswith('ref_'):
        inviter_id = int(args[0].split('_')[1])
        if inviter_id != user_id:
            update_user(user_id, inviter_id=inviter_id)
            update_user(inviter_id, balance=5000, refs=1)
            await context.bot.send_message(inviter_id, "Tabriklaymiz! 1 ta yangi referal qo'shildi. Hisobingizga 5000 coin qo'shildi.")
    else:
        update_user(user_id)

    await update.message.reply_text("Xush kelibsiz! Asosiy menyu:", reply_markup=ReplyKeyboardMarkup([["👤 Profil"]], resize_keyboard=True))

# Profil ko'rsatish
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance, refs = get_user(user_id)
    ref_link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"
    
    text = (f"👤 Foydalanuvchi: {update.effective_user.first_name}\n"
            f"💰 Balans: {balance} coin\n"
            f"👥 Referallar: {refs} ta\n\n"
            f"🔗 Sizning havolangiz: {ref_link}")
    
    await update.message.reply_text(text)

if __name__ == '__main__':
    TOKEN = "8850891918:AAEXajgiKjFGRq-ZZeXO--Sm8Ck-_LCdZdM"
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Text("👤 Profil"), profile))
    application.run_polling()
    
