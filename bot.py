import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)

# Baza sozlamasi
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, refs INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

def get_or_create_user(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    cursor.execute("SELECT balance, refs FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    return data

def add_referral(inviter_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + 5000, refs = refs + 1 WHERE user_id = ?", (inviter_id,))
    conn.commit()
    conn.close()

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    # Referal tizimi
    if args and args[0].startswith('ref_'):
        inviter_id = int(args[0].split('_')[1])
        if inviter_id != user_id:
            add_referral(inviter_id)
            try:
                await context.bot.send_message(inviter_id, "✅ Tabriklaymiz! Referal havolangizdan 1 kishi o'tdi. Hisobingizga 5000 coin qo'shildi.")
            except: pass
    
    get_or_create_user(user_id)
    
    keyboard = [
        ["👤 Profil", "⚔️ Ligalar"],
        ["🔑 Vazifalar", "🎁 Bonus"],
        ["🎮 O'yinlar", "🧩 Testlar"]
    ]
    await update.message.reply_text("Xush kelibsiz! Asosiy menyu:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

# Profil ko'rsatish
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance, refs = get_or_create_user(user_id)
    
    # Inline tugmalar
    keyboard = [
        [InlineKeyboardButton("🔗 Referal havola olish", callback_data='get_ref')],
        [InlineKeyboardButton("👥 Do'st taklif qilish", switch_inline_query="Do'stlaringizni taklif qiling!")]
    ]
    
    text = (f"👤 Foydalanuvchi: {update.effective_user.first_name}\n"
            f"💰 Balans: {balance} coin\n"
            f"👥 Referallar: {refs} ta")
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == 'get_ref':
        bot_username = context.bot.username
        ref_link = f"https://t.me/{bot_username}?start=ref_{update.effective_user.id}"
        await query.answer()
        await query.message.reply_text(f"Sizning shaxsiy referal havolangiz:\n{ref_link}")

if __name__ == '__main__':
    TOKEN = "8850891918:AAEXajgiKjFGRq-ZZeXO--Sm8Ck-_LCdZdM"
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Text("👤 Profil"), profile))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.run_polling()
    
