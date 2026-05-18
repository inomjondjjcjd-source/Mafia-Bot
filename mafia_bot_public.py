import os
import sys
import subprocess
import json
import asyncio
from flask import Flask
from threading import Thread

# 📦 KERAKLI KUTUBXONALARNI O'RNATISH
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# 🔑 SOZLAMALAR
TOKEN = "8303235336:AAEk3J42idbz1KcamIWPC2L3_IlROPeoadI"
ADMIN_ID = 8086545587  # 👑 Sening aniq shaxsiy ID'ngiz
DATA_FILE = "smm_reaction_bot_db.json"

# 📊 BAZA STRUKTURASI
DB = {
    "users": {},
    "settings": {
        "emoji_name": "😁 Kulgi Emojisi",
        "count": 1990,
        "price": 100  # 💰 Siz xohlagandek: 1990 ta reaksiya = 100 so'm!
    }
}

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
        DB["users"][user_id] = {
            "name": name,
            "balance": 500,  # 🎁 Yangi a'zoga 500 so'm start bonus!
            "orders": 0
        }
        save_db()
    return DB["users"][user_id]

# 👋 START BUYRUG'I
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    check_user(user_id, name)
    
    txt = (
        f"🚀 *SMM Reaksiya Urish Botiga Xush Kelibsiz!*\n\n"
        f"Kanal va guruhlardagi postlarga haqiqiy daxshatli tezlikda emojilar va reaksiyalar urib berish xizmati.\n\n"
        f"🔥 *Hozirgi super aksiya:*\n"
        f"👉 1990 ta 😁 emojisi — bor-yo'g'i *100 so'm*!"
    )
    
    buttons = [
        [InlineKeyboardButton("🛍 Reaksiya sotib olish", callback_data="buy_reaction")],
        [InlineKeyboardButton("💳 Hisobim / Balans", callback_data="my_balance"), InlineKeyboardButton("📖 Qo'llanma", callback_data="guide")],
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("👑 SHOX Admin Paneli", callback_data="admin_p")])
        
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# 🎛 TUGMALAR ISHLOVCHISI
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = check_user(user_id)
    
    # ASOSIY MENYUGA QAYTISH
    if query.data == "to_main":
        txt = (
            f"🚀 *SMM Reaksiya Urish Botiga Xush Kelibsiz!*\n\n"
            f"🔥 *Hozirgi super aksiya:*\n"
            f"👉 1990 ta 😁 emojisi — bor-yo'g'i *100 so'm*!"
        )
        buttons = [
            [InlineKeyboardButton("🛍 Reaksiya sotib olish", callback_data="buy_reaction")],
            [InlineKeyboardButton("💳 Hisobim / Balans", callback_data="my_balance"), InlineKeyboardButton("📖 Qo'llanma", callback_data="guide")],
        ]
        if user_id == ADMIN_ID:
            buttons.append([InlineKeyboardButton("👑 SHOX Admin Paneli", callback_data="admin_p")])
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

    # BALANS MA'LUMOTI
    elif query.data == "my_balance":
        txt = (
            f"💳 *Sizning hisobingiz:*\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"💰 Balans: *{ud['balance']} so'm*\n"
            f"📦 Jami buyurtmalar: {ud['orders']} ta"
        )
        kb = [[InlineKeyboardButton("💰 Hisob to'ldirish", callback_data="add_money")], [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # REAKSIYA SOTIB OLISH
    elif query.data == "buy_reaction":
        txt = (
            f"🛍 *Reaksiya paketini tanlang:*\n\n"
            f"📦 Paket: *{DB['settings']['count']} ta {DB['settings']['emoji_name']}*\n"
            f"💰 Narxi: *{DB['settings']['price']} so'm*\n\n"
            f"Buyurtma berishni istaysizmi uka? Hisobingizdan {DB['settings']['price']} so'm yechiladi."
        )
        kb = [
            [InlineKeyboardButton("✅ Sotib olish (Buyurtma)", callback_data="confirm_order")],
            [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]
        ]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # BUYURTMANI TASDIQLASH
    elif query.data == "confirm_order":
        if ud["balance"] < DB["settings"]["price"]:
            await query.edit_message_text(
                f"❌ Xato! Balansingizda mablag' yetarli emas uka.\nSizga {DB['settings']['price']} so'm kerak. Balans: {ud['balance']} so'm.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="buy_reaction")]])
            )
            return
        
        context.user_data["action"] = "waiting_post_link"
        await query.edit_message_text(
            "🔗 *Daxshat! Endi reaksiyalar urilishi kerak bo'lgan kanal postining havolasini (linkini) yuboring:*\n\n"
            "Masalan: `https://t.me/Bdnxbx/2`",
            parse_mode="Markdown"
        )

    # QO'LLANMA
    elif query.data == "guide":
        txt = "📖 *Bot qo'llanmasi:*\n\n1. Hisobingizni pul bilan to'ldirasiz.\n2. Reaksiya bo'limidan buyurtma berib, kanalingizdagi post havolasini tashlaysiz.\n3. Bizning daxshatli akkauntlar bazamiz srazu ishga tushib, 1990 ta reaksiyani postga daxshatli tezlikda urib beradi!"
        kb = [[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "add_money":
        txt = f"💰 Hisobingizni to'ldirish uchun `ID: {user_id}` kodini admin @shox_admin ga yuboring."
        kb = [[InlineKeyboardButton("⬅️ Ortga", callback_data="my_balance")]]
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

    # ADMIN PANEL
    elif query.data == "admin_p" and user_id == ADMIN_ID:
        txt = (
            f"👑 *SHOX ADMIN PANEL*\n\n"
            f"👥 Jami mijozlar: *{len(DB['users'])} ta*\n"
            f"⚙️ Paket narxi: *{DB['settings']['price']} so'm*\n\n"
            f"Sozlash buyruqlari:\n"
            f"🔹 `/plus ID PUL` — Balans to'ldirish\n"
            f"🔹 `/setprice NARX` — Paket narxini o'zgartirish"
        )
        kb = [[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# ✉️ LINKLARNI QABUL QILISH TIZIMI
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = check_user(user_id)
    text = update.message.text.strip()
    action = context.user_data.get("action")
    
    if action == "waiting_post_link":
        context.user_data["action"] = None
        if "t.me/" not in text:
            await update.message.reply_text("❌ Xato havola! Iltimos haqiqiy Telegram post linkini yuboring uka.")
            return
            
        # Balansni yechish va buyurtmani rasmiylashtirish
        ud["balance"] -= DB["settings"]["price"]
        ud["orders"] += 1
        save_db()
        
        success_txt = (
            f"✅ *Buyurtma muvaffaqiyatli qabul qilindi!*\n\n"
            f"🔗 Post havolasi: {text}\n"
            f"📦 Miqdori: *{DB['settings']['count']} ta {DB['settings']['emoji_name']}*\n"
            f"💸 Yechilgan mablag': {DB['settings']['price']} so'm\n\n"
            f"⚡ Reaksiyalar yaqin 5-10 daqiqa ichida postga to'liq urib tugatiladi uka!"
        )
        await update.message.reply_text(success_txt, parse_mode="Markdown")
        
        # Adminga xabar berish
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"👑 *Yangi Buyurtma uka!*\n\nFoydalanuvchi: `{user_id}`\nPost: {text}\nPaket: {DB['settings']['count']} ta 😁"
            )
        except: pass

# 👑 ADMIN COMMANDS
async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        if target_id in DB["users"]:
            DB["users"][target_id]["balance"] += amount
            save_db()
            await update.message.reply_text(f"✅ `ID: {target_id}` balansiga *{amount} so'm* qo'shildi uka!")
    except: pass

async def admin_setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        price = int(context.args[0])
        DB["settings"]["price"] = price
        save_db()
        await update.message.reply_text(f"✅ Yangi aksiya narxi o'rnatildi: *{price} so'm*")
    except: pass

# 🌐 FLASK SERVER
app = Flask(__name__)

@app.route('/')
def home():
    return "SMM Reaksiya Do'koni Faol!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 🚀 ASINXRON MAIN
async def main_bot():
    load_db()
    bot_app = Application.builder().token(TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("plus", admin_plus))
    bot_app.add_handler(CommandHandler("setprice", admin_setprice))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    Thread(target=run_flask, daemon=True).start()
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    print("SMM Reaksiya do'koni boti daxshatli tarzda ishga tushmoqda...")
    loop.run_until_complete(main_bot())
    
