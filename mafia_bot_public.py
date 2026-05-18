import os
import sys
import subprocess
import json
import asyncio
from flask import Flask
from threading import Thread

# 📦 KERAKLI KUTUBXONALARNI AVTO-O'RNATISH
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# 🔑 SOZLAMALAR
TOKEN = "8303235336:AAEk3J42idbz1KcamIWPC2L3_IlROPeoadI"
ADMIN_ID = 8086545587  # 👑 Sening aniq shaxsiy ID'ngiz
DATA_FILE = "new_reaction_bot_db.json"

# 📊 MA'LUMOTLAR BAZASI
DB = {"users": {}, "promocodes": {}, "settings": {"service_price": 500}}

def load_db():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                loaded["users"] = {int(k): v for k, v in loaded.get("users", {}).items()}
                DB = loaded
        except: pass

def save_db():
    try:
        to_save = DB.copy()
        to_save["users"] = {str(k): v for k, v in DB["users"].items()}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=4, ensure_ascii=False)
    except: pass

def check_user(user_id, name="Foydalanuvchi"):
    if user_id not in DB["users"]:
        DB["users"][user_id] = {"name": name, "balance": 100, "channels": [], "limit": 0, "tarif": "Bepul"}
        save_db()
    return DB["users"][user_id]

# 👋 START BUYRUG'I
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    check_user(user_id, name)
    
    txt = (
        f"📣 *@ReaksiyauzBot — Kanal va Guruhlarga Reaksiya qo'shish boti!*\n\n"
        f"✨ Endi siz ham o'z kanal yoki guruhingizdagi postlarga qulay va chiroyli Reaksiyalar qo'shishingiz mumkin.\n"
        f"👍❤️🔥😮😂 — xohlagancha emojilarni tanlang va obunachilaringizni yanada faol qiling!"
    )
    
    buttons = [
        [InlineKeyboardButton("🎁 Reaksiyalar sozlamalar", callback_data="reaction_settings")],
        [InlineKeyboardButton("💰 Hisobni ko'rish", callback_data="view_balance"), InlineKeyboardButton("🛍 Yangi xizmatlar", callback_data="new_services")],
        [InlineKeyboardButton("📖 Bot qo'llanmasi", callback_data="bot_guide"), InlineKeyboardButton("⭐ Sovg'alar olish", callback_data="get_gifts")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("👑 SHOX (Admin) Paneli", callback_data="admin_panel")])
        
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# 🎛 TUGMALAR BOSILGANDAGI MEXANIZM
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = check_user(user_id)
    
    if query.data == "reaction_settings":
        txt = (
            f"📣 *Reaksiyalarni ishlatish uchun avval botni kanal yoki guruhga qo'shishingiz kerak.*\n\n"
            f"👉 Quyidagi tugmalardan foydalanib, kerakli reaksiyalarni tanlang yoki ko'rish uchun bosing."
        )
        kb = [
            [InlineKeyboardButton("➕ Kanal qo'shish", callback_data="add_channel"), InlineKeyboardButton("🗑 Kanal o'chirish", callback_data="del_channel")],
            [InlineKeyboardButton("📄 Kanallar ro'yxati", callback_data="list_channels")],
            [InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="back_main")]
        ]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        
    elif query.data == "view_balance":
        txt = (
            f"💳 *Hisobingiz haqida:*\n\n"
            f"🆔 *ID:* `{user_id}`\n"
            f"💰 *Balans:* {ud['balance']} so'm\n"
            f"⏰ *Limit:* {ud['limit']}\n"
            f"💎 *Tarif:* {ud['tarif']}\n\n"
            f"⭐️ *Premium obunga qo'shiling!*"
        )
        kb = [
            [InlineKeyboardButton("💰 Hisob to'ldirish", callback_data="refill_balance")],
            [InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="back_main")]
        ]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        
    elif query.data == "back_main":
        txt = (
            f"📣 *@ReaksiyauzBot — Kanal va Guruhlarga Reaksiya qo'shish boti!*\n\n"
            f"👍❤️🔥 — xohlagancha emojilarni tanlang va obunachilaringizni faol qiling!"
        )
        buttons = [
            [InlineKeyboardButton("🎁 Reaksiyalar sozlamalar", callback_data="reaction_settings")],
            [InlineKeyboardButton("💰 Hisobni ko'rish", callback_data="view_balance"), InlineKeyboardButton("🛍 Yangi xizmatlar", callback_data="new_services")],
            [InlineKeyboardButton("📖 Bot qo'llanmasi", callback_data="bot_guide"), InlineKeyboardButton("⭐ Sovg'alar olish", callback_data="get_gifts")]
        ]
        if user_id == ADMIN_ID:
            buttons.append([InlineKeyboardButton("👑 SHOX (Admin) Paneli", callback_data="admin_panel")])
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data == "admin_panel" and user_id == ADMIN_ID:
        txt = (
            f"👑 *REAKSIYA BOT - SHOX PANELI*\n\n"
            f"👥 Jami a'zolar: *{len(DB['users'])} ta*\n"
            f"💰 Xizmat narxi: *{DB['settings']['service_price']} so'm*\n\n"
            f"Admin buyruqlari:\n"
            f"🔹 `/plus ID PUL`\n🔹 `/minus ID PUL`"
        )
        kb = [[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="back_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data in ["add_channel", "del_channel", "list_channels", "new_services", "bot_guide", "get_gifts", "refill_balance"]:
        txt = f"⚙️ Bu bo'lim tez orada ishga tushadi uka! Hozircha menyu va balans tizimi daxshat ishlamoqda."
        kb = [[InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="back_main")]]
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

# 👑 ADMIN COMMANDS
async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        if target_id in DB["users"]:
            DB["users"][target_id]["balance"] += amount
            save_db()
            await update.message.reply_text(f"✅ `ID: {target_id}` balansiga *{amount} so'm* qo'shildi!")
    except: pass

# 🌐 RENDER PORTINI TINGLOVCHI FLASK SERVER
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running daxshat!"

def run_flask():
    # Render beradigan portni avtomatik oladi, bo'lmasa 10000 portda ishlaydi
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 🚀 BOTNI ASINXRON RUN QILISH
async def main_bot():
    load_db()
    bot_app = Application.builder().token(TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("plus", admin_plus))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))
    
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    
    # Render o'chib qolmasligi uchun cheksiz sikl
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    # 1. Flask serverni alohida oqimda yoqamiz (Render o'chib qolmasligi uchun)
    Thread(target=run_flask, daemon=True).start()
    
    # 2. Asosiy event loopni xatosiz ishga tushiramiz
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    print("Yangi asinxron kod ishga tushdi...")
    loop.run_until_complete(main_bot())
    
