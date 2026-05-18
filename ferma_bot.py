import os
import sys
import subprocess
import asyncio
import time
import json
from threading import Thread
from flask import Flask

# 📦 KUTUBXONANI TEKSHIRISH VA O'RNATISH
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "Flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

# 🌐 WEB SERVER (PORT: 8000 - ESKI BOT BILAN URUSHMAYDI)
server = Flask('')
@server.route('/')
def home(): return "Ferma Aktiv!"

def run_server():
    port = int(os.environ.get("PORT", 8000))
    server.run(host='0.0.0.0', port=port)

# 🔑 PARAMETRLAR
TOKEN = "8829005476:AAGc-b-dQ1NJycS3vMf0-tRn7H15y4kFtn4"
MAIN_ADMIN = 7920504062
MY_LICHKA = "https://t.me/inomjondjjcjd"

DATA_FILE = "ferma_db.json"
USER_DATA = {}

# 🐉 AJDAHOLAR (Foydasi soatlik oltinda)
DRAGONS = {
    "d1": {"name": "🐉 Kichik Ajdaho", "price": 0, "income": 100},
    "d2": {"name": "🔥 Olovli Ajdaho", "price": 15000, "income": 2500},
    "d3": {"name": "⚡️ Imperator Ajdaho", "price": 50000, "income": 10000}
}

def load_data():
    global USER_DATA
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                USER_DATA = {int(k): v for k, v in json.load(f).items()}
        except: USER_DATA = {}

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in USER_DATA.items()}, f, indent=4)
    except: pass

def get_user(user_id):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "money": 0, "gold": 0, "last_time": time.time(),
            "dragons": {"d1": 1, "d2": 0, "d3": 0}, "state": None
        }
        save_data()
    return USER_DATA[user_id]

def main_menu(user_id):
    kb = [
        [InlineKeyboardButton("🐉 Fermam", callback_data="farm"), InlineKeyboardButton("🧺 Yig'ish", callback_data="collect")],
        [InlineKeyboardButton("🏪 Do'kon", callback_data="shop"), InlineKeyboardButton("🗄 Kabinet", callback_data="cab")],
        [InlineKeyboardButton("💳 Pul solish", callback_data="dep"), InlineKeyboardButton("💸 Pul yechish", callback_data="with")]
    ]
    if user_id == MAIN_ADMIN:
        kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="adm")])
    return InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ud = get_user(uid)
    ud["state"] = None
    save_data()
    await update.message.reply_text(f"🐉 *Mifologik Ferma O'yiniga Xush Kelibsiz!*\n\nBalans: {ud['money']:,} UZS\nOltin: {ud['gold']:,} 🪙", parse_mode="Markdown", reply_markup=main_menu(uid))

async def handle_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    ud = get_user(uid)
    back = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]])

    # Oltinlarni hisoblash
    speed = ud["dragons"]["d1"]*100 + ud["dragons"]["d2"]*2500 + ud["dragons"]["d3"]*10000
    pending = int(((time.time() - ud["last_time"]) / 3600.0) * speed)

    if query.data == "home":
        ud["state"] = None
        save_data()
        await query.edit_message_text(f"🐉 *Asosiy Menyu*\n\nBalans: {ud['money']:,} UZS\nOmborda: {pending:,} 🪙", parse_mode="Markdown", reply_markup=main_menu(uid))

    elif query.data == "farm":
        txt = f"🐉 *Sizning Fermangiz:*\n• Kichik: {ud['dragons']['d1']} ta\n• Olovli: {ud['dragons']['d2']} ta\n• Imperator: {ud['dragons']['d3']} ta\n\n📈 Tezlik: {speed} oltin/soat\n🧺 Omborda: {pending} 🪙"
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=back)

    elif query.data == "collect":
        ud["gold"] += pending
        ud["last_time"] = time.time()
        save_data()
        await query.edit_message_text(f"🧺 Oltinlar yig'ildi! Jami oltiningiz: {ud['gold']:,} 🪙", reply_markup=back)

    elif query.data == "shop":
        skb = [[InlineKeyboardButton(f"Sotib olish: {DRAGONS[k]['name']}", callback_data=f"b_{k}")] for k in ["d2", "d3"]]
        skb.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="home")])
        txt = f"🏪 *Do'kon:*\n\n🔥 Olovli: 15,000 UZS (+2500/sh)\n⚡️ Imperator: 50,000 UZS (+10000/sh)\n\nBalans: {ud['money']:,} UZS"
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(skb))

    elif query.data.startswith("b_"):
        k = query.data.split("_")[1]
        if ud["money"] < DRAGONS[k]["price"]:
            await query.edit_message_text("❌ Mablag' yetarli emas uka!", reply_markup=back)
        else:
            ud["money"] -= DRAGONS[k]["price"]
            ud["dragons"][k] += 1
            save_data()
            await query.edit_message_text(f"🎉 {DRAGONS[k]['name']} sotib olindi!", reply_markup=back)

    elif query.data == "cab":
        ckb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Oltinni Pulga Almashtirish", callback_data="ex")], [InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]])
        await query.edit_message_text(f"🗄 *Profil:*\n\nID: `{uid}`\nBalans: {ud['money']:,} UZS\nOltin: {ud['gold']:,} 🪙\n\nKurs: 1,000 oltin = 100 UZS", parse_mode="Markdown", reply_markup=ckb)

    elif query.data == "ex":
        if ud["gold"] < 1000:
            await query.edit_message_text("❌ Kamida 1,000 ta oltin bo'lishi kerak!", reply_markup=back)
        else:
            gain = int((ud["gold"] / 1000) * 100)
            ud["money"] += gain
            ud["gold"] = 0
            save_data()
            await query.edit_message_text(f"🔄 Almashtirildi! Hisobga +{gain:,} UZS qo'shildi.", reply_markup=back)

    elif query.data in ["dep", "with"]:
        await query.edit_message_text(f"💳 *To'lov va Pul yechish:*\n\nAdmin lichkasiga yozing:\n👉 [Lichka]({MY_LICHKA})", parse_mode="Markdown", reply_markup=back)

    elif query.data == "adm" and uid == MAIN_ADMIN:
        akb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Balans Berish", callback_data="a_bal"), InlineKeyboardButton("🐉 Ajdaho Berish", callback_data="a_drg")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]
        ])
        await query.edit_message_text("👑 *Admin Panel:*", reply_markup=akb)

    elif query.data == "a_bal" and uid == MAIN_ADMIN:
        ud["state"] = "w_bal"
        save_data()
        await query.edit_message_text("💰 Format: `ID +pul` yoki `ID -pul` (Masalan: `7920504062 +50000`) ")

    elif query.data == "a_drg" and uid == MAIN_ADMIN:
        ud["state"] = "w_drg"
        save_data()
        await query.edit_message_text("🐉 Format: `ID AJDAHO_KODI`\nKodlar: `d1`, `d2`, `d3` (Masalan: `7920504062 d3`) ")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    ud = get_user(uid)
    back = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menyu", callback_data="home")]])

    if uid == MAIN_ADMIN and ud["state"] == "w_bal":
        try:
            tid, op = text.split()
            tid = int(tid)
            t_ud = get_user(tid)
            if op.startswith("+"): t_ud["money"] += int(op.replace("+", ""))
            elif op.startswith("-"): t_ud["money"] -= int(op.replace("-", ""))
            ud["state"] = None
            save_data()
            await update.message.reply_text("✅ Balans o'zgartirildi!", reply_markup=back)
        except: await update.message.reply_text("❌ Xato! Namuna: `7920504062 +10000`", reply_markup=back)
        return

    if uid == MAIN_ADMIN and ud["state"] == "w_drg":
        try:
            tid, dk = text.split()
            tid = int(tid)
            if dk in ["d1", "d2", "d3"]:
                t_ud = get_user(tid)
                t_ud["dragons"][dk] += 1
                ud["state"] = None
                save_data()
                await update.message.reply_text("✅ Ajdaho berildi!", reply_markup=back)
            else: raise ValueError
        except: await update.message.reply_text("❌ Xato! Namuna: `7920504062 d3`", reply_markup=back)
        return

def main():
    load_data()
    Thread(target=run_server).start()
    app = Application.builder().token(TOKEN).build()
    
    try: loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(app.bot.delete_webhook(drop_pending_updates=True))
    time.sleep(1.0)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    print("Bot yoqildi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
        
