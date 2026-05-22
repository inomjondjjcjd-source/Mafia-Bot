import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, 
                          filters, CallbackQueryHandler, ContextTypes, ConversationHandler)

TOKEN = "8850891918:AAEXajgiKjFGRq-ZZeXO--Sm8Ck-_LCdZdM"
ADMIN_ID = 8086545587
NAME, REWARD, LINK = range(3)

logging.basicConfig(level=logging.INFO)

# --- Baza ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, refs INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, reward INTEGER, link TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS referrals (referred_id INTEGER PRIMARY KEY, inviter_id INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS completed_tasks (user_id INTEGER, task_id INTEGER)')
    conn.commit()
    conn.close()

init_db()

# --- Funksiyalar ---
def get_main_menu(user_id):
    keyboard = [["👤 Profil", "🔑 Vazifalar"], ["🎁 Bonus", "🎮 O'yinlar"]]
    if user_id == ADMIN_ID: keyboard.append(["🛠 Admin Panel"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- Start & Profil ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if args and args[0].startswith('ref_'):
        inviter_id = int(args[0].split('_')[1])
        if inviter_id != user_id:
            conn = sqlite3.connect('bot_data.db')
            if conn.execute("SELECT 1 FROM referrals WHERE referred_id = ?", (user_id,)).fetchone() is None:
                conn.execute("INSERT INTO referrals (referred_id, inviter_id) VALUES (?, ?)", (user_id, inviter_id))
                conn.execute("UPDATE users SET balance = balance + 5000, refs = refs + 1 WHERE user_id = ?", (inviter_id,))
                conn.commit()
            conn.close()
    
    conn = sqlite3.connect('bot_data.db')
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("Xush kelibsiz!", reply_markup=get_main_menu(user_id))

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = sqlite3.connect('bot_data.db').execute("SELECT balance, refs FROM users WHERE user_id = ?", (user_id,)).fetchone()
    text = f"👤 Profilingiz\n💰 Balans: {data[0]} coin\n👥 Referallar: {data[1]} ta"
    kb = [[InlineKeyboardButton("🔗 Referal havola", callback_data='get_ref')],
          [InlineKeyboardButton("📤 Do'st taklif qilish", switch_inline_query="Gresscoin botiga qo'shiling!")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

# --- Vazifalar ---
async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = sqlite3.connect('bot_data.db').execute("SELECT id, name, reward, link FROM tasks").fetchall()
    for t_id, name, reward, link in tasks:
        kb = [[InlineKeyboardButton("🔗 Obuna", url=link), InlineKeyboardButton("✅ Tasdiqlash", callback_data=f'check_{t_id}')]]
        await update.message.reply_text(f"Vazifa: {name}\nMukofot: {reward} coin", reply_markup=InlineKeyboardMarkup(kb))

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    t_id = query.data.split('_')[1]
    task = sqlite3.connect('bot_data.db').execute("SELECT reward, link FROM tasks WHERE id = ?", (t_id,)).fetchone()
    channel = task[1].split('/')[-1]
    try:
        member = await context.bot.get_chat_member(chat_id=f"@{channel}", user_id=update.effective_user.id)
        if member.status in ['member', 'administrator', 'creator']:
            sqlite3.connect('bot_data.db').execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (task[0], update.effective_user.id)).connection.commit()
            await query.answer("✅ Tabriklaymiz! Coin qo'shildi.")
        else: await query.answer("❌ Obuna bo'lmagansiz!", show_alert=True)
    except: await query.answer("Bot kanal admini emas!", show_alert=True)

# --- Admin Panel ---
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Admin:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Vazifa qo'shish", callback_data='add_task')]]))

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text("👤 Profil"), profile))
    app.add_handler(MessageHandler(filters.Text("🔑 Vazifalar"), show_tasks))
    app.add_handler(MessageHandler(filters.Text("🛠 Admin Panel"), admin_menu))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.message.reply_text(f"Link: https://t.me/{c.bot.username}?start=ref_{u.effective_user.id}"), pattern='get_ref'))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern='check_'))
    
    conv = ConversationHandler(entry_points=[CallbackQueryHandler(lambda u, c: u.callback_query.message.reply_text("Nomi:") or NAME, pattern='add_task')],
                               states={NAME: [MessageHandler(filters.TEXT, lambda u, c: c.user_data.update({'n': u.message.text}) or u.message.reply_text("Narxi:") or REWARD)],
                                       REWARD: [MessageHandler(filters.TEXT, lambda u, c: c.user_data.update({'r': u.message.text}) or u.message.reply_text("Link:") or LINK)],
                                       LINK: [MessageHandler(filters.TEXT, lambda u, c: sqlite3.connect('bot_data.db').execute("INSERT INTO tasks (name, reward, link) VALUES (?, ?, ?)", (c.user_data['n'], c.user_data['r'], u.message.text)).connection.commit() or u.message.reply_text("✅") or ConversationHandler.END)]}, fallbacks=[])
    app.add_handler(conv)
    app.run_polling()
  
