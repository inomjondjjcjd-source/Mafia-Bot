import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, 
                          filters, CallbackQueryHandler, ContextTypes, ConversationHandler)

# Sozlamalar
TOKEN = "8850891918:AAEXajgiKjFGRq-ZZeXO--Sm8Ck-_LCdZdM"
ADMIN_ID = 8086545587
NAME, REWARD, LINK = range(3)

logging.basicConfig(level=logging.INFO)

# Baza
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, refs INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, reward INTEGER, link TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS referrals (referred_id INTEGER PRIMARY KEY, inviter_id INTEGER)')
    conn.commit()
    conn.close()

init_db()

# Menyu
def get_main_menu(user_id):
    keyboard = [["👤 Profil", "⚔️ Ligalar"], ["🔑 Vazifalar", "🎁 Bonus"], ["🎮 O'yinlar", "🧩 Testlar"]]
    if user_id == ADMIN_ID:
        keyboard.append(["🛠 Admin Panel"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Referal logikasi
def try_add_referral(inviter_id, referred_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT inviter_id FROM referrals WHERE referred_id = ?", (referred_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO referrals (referred_id, inviter_id) VALUES (?, ?)", (referred_id, inviter_id))
        cursor.execute("UPDATE users SET balance = balance + 5000, refs = refs + 1 WHERE user_id = ?", (inviter_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if args and args[0].startswith('ref_'):
        inviter_id = int(args[0].split('_')[1])
        if inviter_id != user_id:
            if try_add_referral(inviter_id, user_id):
                try: await context.bot.send_message(inviter_id, "✅ Referal havolangizdan 1 kishi o'tdi. 5000 coin qo'shildi.")
                except: pass
    
    conn = sqlite3.connect('bot_data.db')
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("Xush kelibsiz!", reply_markup=get_main_menu(user_id))

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('bot_data.db')
    data = conn.execute("SELECT balance, refs FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    text = f"👤 Profilingiz\n💰 Balans: {data[0]} coin\n👥 Referallar: {data[1]} ta"
    kb = [[InlineKeyboardButton("🔗 Referal havola olish", callback_data='get_ref')],
          [InlineKeyboardButton("📤 Do'st taklif qilish", switch_inline_query="Gresscoin botiga qo'shiling!")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

# Admin funksiyalari
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    kb = [[InlineKeyboardButton("➕ Vazifa qo'shish", callback_data='add_task')]]
    await update.message.reply_text("Admin paneli:", reply_markup=InlineKeyboardMarkup(kb))

async def start_add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("Vazifa nomini kiriting:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Vazifa uchun coin miqdori:")
    return REWARD

async def get_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reward'] = int(update.message.text)
    await update.message.reply_text("Kanal linkini kiriting:")
    return LINK

async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('bot_data.db')
    conn.execute("INSERT INTO tasks (name, reward, link) VALUES (?, ?, ?)", 
                 (context.user_data['name'], context.user_data['reward'], update.message.text))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ Vazifa qo'shildi!")
    return ConversationHandler.END

# Main
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text("👤 Profil"), profile))
    app.add_handler(MessageHandler(filters.Text("🛠 Admin Panel"), admin_menu))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.message.reply_text(f"Link: https://t.me/{c.bot.username}?start=ref_{u.effective_user.id}"), pattern='get_ref'))
    
    conv = ConversationHandler(entry_points=[CallbackQueryHandler(start_add_task, pattern='add_task')],
                               states={NAME: [MessageHandler(filters.TEXT, get_name)],
                                       REWARD: [MessageHandler(filters.TEXT, get_reward)],
                                       LINK: [MessageHandler(filters.TEXT, save_task)]}, fallbacks=[])
    app.add_handler(conv)
    app.run_polling()
  
