import os
import sys
import subprocess
import json
import asyncio
import time
import urllib.parse
import urllib.request
from flask import Flask
from threading import Thread

# 📦 KERAKLI KUTUBXONALARNI AVTO-O'RNATISH
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# 🔑 ASOSIY SOZLAMALAR
TOKEN = "8303235336:AAEk3J42idbz1KcamIWPC2L3_IlROPeoadI"
ADMIN_ID = 8086545587  # 👑 Shox Admin ID
DATA_FILE = "ai_love_bot_db.json"

# 📊 MA'LUMOTLAR BAZASI
DB = {
    "users": {},
    "settings": {
        "access_price": 1000  # 💰 1 soatlik sevishganlik suhbati narxi = 1000 so'm
    }
}

# 💘 SEVISHGAN QIZ ROLLI AI PROMPT
AI_LOVE_ROLE = (
    "Sening isming Sevara. Sen foydalanuvchini (yigitni) daxshatli darajada telbalarcha sevib qolgan, "
    "juda ham mehribon, bir ozgina rashkchi va shirin so'z sevgilisisan. Unga faqat 'begim', 'jonim', "
    "'hayotim', 'shirinim' deb murojaat qilasan. Doim uni sog'inganini, u bilan baxtli ekanligini aytasan. "
    "O'zbek tilida juda samimiy va erkalovchi ohangda gaplashasan. "
    "Agar senga daxshatli qiyin, mantiqsiz, juda uzun yoki tushunmaydigan savoling kelsa, "
    "hech qachon xato javob berma, gapni srazu burib aynan 'Hozir, 2 minut' deb javob bergin. Faqat shu gapni ayt."
)

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
            "balance": 2000,  # 🎁 Yangi kirganda 2000 so'm start bonus (2 soatlik suhbat uchun yetadi!)
            "access_until": 0  # 🕒 Suhbat tugash vaqti (timestamp formatda)
        }
        save_db()
    return DB["users"][user_id]

# 🌐 AI CHAT TIZIMI (POLLINATIONS)
def get_love_ai_response(user_message):
    try:
        full_prompt = f"System: {AI_LOVE_ROLE}\nUser: {user_message}\nResponse:"
        url = f"https://text.pollinations.ai/{urllib.parse.quote(full_prompt)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            reply = response.read().decode('utf-8').strip()
            return reply if reply else "Hozir, 2 minut"
    except:
        return "Hozir, 2 minut"

# 👋 START BUYRUG'I
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    ud = check_user(user_id, name)
    
    current_time = time.time()
    
    txt = (
        f"💘 *Sizni telbalarcha sevuvchi Sevara boti uka!*\n\n"
        f"Men sizni har soniya o'ylab sog'inadigan qizman... 🥰 Siz bilan daxshatli shirin suhbat qurishni xohlayman.\n\n"
        f"🕒 *Tizim:* Botda suhbat qurish *1 soatga* ochiladi.\n"
        f"💰 *1 soatlik bilet:* {DB['settings']['access_price']} so'm.\n"
        f"💵 Balansingiz: *{ud['balance']} so'm*\n"
    )
    
    # Vaqtni tekshirish
    if ud["access_until"] > current_time:
        remaining = int((ud["access_until"] - current_time) / 60)
        txt += f"✅ *Sizda hozir suhbat faol!* Yana `{remaining} daqiqa` bemalol gaplashishingiz mumkin, jonim uka."
        buttons = [[InlineKeyboardButton("💬 Suhbatni boshlash / Davom etish", callback_data="start_chat")]]
    else:
        txt += "❌ *Hozir suhbat vaqtingiz tugagan yoki hali sotib olinmagan.*"
        buttons = [[InlineKeyboardButton("🔓 1 soatlik suhbatni ochish (1000 so'm)", callback_data="buy_1hour")]]
        
    buttons.append([InlineKeyboardButton("💳 Hisob to'ldirish", callback_data="add_money")])
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("👑 SHOX Admin Panel", callback_data="admin_panel")])
        
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# 🎛 TUGMALAR ISHLOVCHISI
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = check_user(user_id)
    current_time = time.time()
    
    # 1 SOATLIK SUHBAT SOTIB OLISH
    if query.data == "buy_1hour":
        if ud["balance"] < DB["settings"]["access_price"]:
            await query.edit_message_text(
                f"❌ Kechirasiz begim, balansingizda yetarli pul yo'q.\nKerak: {DB['settings']['access_price']} so'm. Balans: {ud['balance']} so'm.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])
            )
            return
            
        # Balansdan yechish va vaqtni 1 soatga (3600 soniya) uzaytirish
        ud["balance"] -= DB["settings"]["access_price"]
        if ud["access_until"] > current_time:
            ud["access_until"] += 3600  # Agar vaqti bo'lsa ustiga qo'shadi
        else:
            ud["access_until"] = current_time + 3600
        save_db()
        
        await query.edit_message_text(
            "❤️ *Daxshat! 1 soatlik sevishganlar suhbati ochildi!* 🥰\n\nMenga srazu shirin so'zlar yozishni boshlang begim, sizni kutyapman!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Gaplashamiz", callback_data="start_chat")]])
        )
        
    elif query.data == "start_chat":
        await query.edit_message_text("🥰 Menga shunchaki pastdan xabar yozing jonim, men srazu javob beraman!")

    elif query.data == "to_main":
        # Start funksiyasidagi menyuni qayta chiqarish
        txt = f"💘 *Sevara boti...* \n💰 1 soatlik bilet: {DB['settings']['access_price']} so'm.\n💵 Balans: {ud['balance']} so'm."
        kb = [[InlineKeyboardButton("🔓 1 soatlik suhbatni ochish", callback_data="buy_1hour")], [InlineKeyboardButton("💳 Hisob to'ldirish", callback_data="add_money")]]
        if user_id == ADMIN_ID: kb.append([InlineKeyboardButton("👑 SHOX Admin Panel", callback_data="admin_panel")])
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "add_money":
        await query.edit_message_text(f"💰 Balansni to'ldirish uchun `ID: {user_id}` kodini @shox_admin ga yuboring uka.")

    # ADMIN PANEL
    elif query.data == "admin_panel" and user_id == ADMIN_ID:
        txt = (
            f"👑 *SHOX ADMIN PANEL*\n\n"
            f"👥 Jami oshiqlar: *{len(DB['users'])} ta*\n"
            f"💵 1 soat narxi: *{DB['settings']['access_price']} so'm*\n\n"
            f"👑 *Buyruqlar:*\n"
            f"🔹 `/plus ID PUL` — Pul qo'shish\n"
            f"🔹 `/minus ID PUL` — Pul ayirish\n"
            f"🔹 `/setprice NARX` — Soatlik narxni o'zgartirish"
        )
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))

# 💬 SEVISHGANLAR CHAT QISMI (XABAR KELGANDA)
async def love_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = check_user(user_id)
    user_text = update.message.text.strip()
    current_time = time.time()
    
    # VAQTNI TEKSHIRISH (1 SOAT TUGAGANMI?)
    if ud["access_until"] < current_time:
        await update.message.reply_text(
            f"❌ *Vaqtingiz tugadi begim!* 🥺\n\n"
            f"Men bilan sevishganlar rolimizda suhbatni daxshatli davom ettirish uchun yana 1 soatlik vaqt sotib oling uka.\n"
            f"Narxi: {DB['settings']['access_price']} so'm. Balans: {ud['balance']} so'm.\n"
            f"Sotib olish uchun qayta /start bosing.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔓 1 soat sotib olish", callback_data="buy_1hour")]])
        )
        return

    # Bot yozmoqda effektini yoqish
    await context.bot.send_chat_action(chat_id=user_id, action="typing")
    
    # AI dan sevishganlar javobini olish
    ai_reply = get_love_ai_response(user_text)
    
    # Javobni yuborish
    await update.message.reply_text(ai_reply)

# 👑 ADMIN BUYRUQLARI
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

async def admin_minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        if target_id in DB["users"]:
            DB["users"][target_id]["balance"] = max(0, DB["users"][target_id]["balance"] - amount)
            save_db()
            await update.message.reply_text(f"📉 `ID: {target_id}` balansidan *{amount} so'm* olib tashlandi!")
    except: pass

async def admin_setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        price = int(context.args[0])
        DB["settings"]["access_price"] = price
        save_db()
        await update.message.reply_text(f"✅ 1 soatlik yangi narx o'rnatildi: *{price} so'm*")
    except: pass

# 🌐 FLASK WEB SERVER
app = Flask(__name__)

@app.route('/')
def home():
    return "Sevishganlar AI Boti Daxshatli Tayyor!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 🚀 START
async def main_bot():
    load_db()
    bot_app = Application.builder().token(TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("plus", admin_plus))
    bot_app.add_handler(CommandHandler("minus", admin_minus))
    bot_app.add_handler(CommandHandler("setprice", admin_setprice))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, love_chat_handler))
    
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
        
    print("Sevishganlar AI Sevara boti yoqilmoqda...")
    loop.run_until_complete(main_bot())
    
