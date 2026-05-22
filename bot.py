import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)

# Baza yaratish
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    # Foydalanuvchilar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, refs INTEGER DEFAULT 0)''')
    # Kim kimni chaqirganini saqlash uchun jadval
    cursor.execute('''CREATE TABLE IF NOT EXISTS referrals 
                      (referred_id INTEGER PRIMARY KEY, inviter_id INTEGER)''')
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

def try_add_referral(inviter_id, referred_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    # Avval bu odam oldin chaqirilganmi deb tekshiramiz
    cursor.execute("SELECT inviter_id FROM referrals WHERE referred_id = ?", (referred_id,))
    if cursor.fetchone() is None:
        # Agar chaqirilmagan bo'lsa, yozib qo'yamiz va bonus beramiz
        cursor.execute("INSERT INTO referrals (referred_id, inviter_id) VALUES (?, ?)", (referred_id, inviter_id))
        cursor.execute("UPDATE users SET balance = balance + 5000, refs = refs + 1 WHERE user_id = ?", (inviter_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    if args and args[0].startswith('ref_'):
        inviter_id = int(args[0].split('_')[1])
        if inviter_id != user_id:
            if try_add_referral(inviter_id, user_id):
                try:
                    await context.bot.send_message(inviter_id, "✅ Tabriklaymiz! Referal havolangizdan yangi odam o'tdi. 5000 coin qo'shildi.")
                except: pass
    
    get_or_create_user(user_id)
    keyboard = [["👤 Profil", "⚔️ Ligalar"], ["🔑 Vazifalar", "🎁 Bonus"], ["🎮 O'yinlar", "🧩 Testlar"]]
    await update.message.reply_text("Xush kelibsiz!", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance, refs = get_or_create_user(user_id)
    text = f"👤 Foydalanuvchi: {update.effective_user.first_name}\n💰 Balans: {balance} coin\n👥 Referallar: {refs} ta"
    keyboard = [[InlineKeyboardButton("🔗 Referal havola olish", callback_data='get_ref')],
                [InlineKeyboardButton("📤 Do'st taklif qilish", switch_inline_query="Gresscoin botiga qo'shiling!")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == 'get_ref':
        ref_link = f"https://t.me/{context.bot.username}?start=ref_{update.effective_user.id}"
        await query.message.reply_text(f"Sizning referal havolangiz:\n\n`{ref_link}`", parse_mode='Markdown')
        await query.answer()

if __name__ == '__main__':
    TOKEN = "8850891918:AAEXajgiKjFGRq-ZZeXO--Sm8Ck-_LCdZdM"
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Text("👤 Profil"), profile))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.run_polling()
    
