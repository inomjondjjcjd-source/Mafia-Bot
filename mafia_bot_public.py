import os
import sys
import subprocess
import json
import asyncio
import time
import random
import string
import urllib.parse
import urllib.request
from flask import Flask
from threading import Thread

# 📦 KUTUBXONALARNI TEKSHIRISH
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
DATA_FILE = "ai_super_love_db.json"

# 📊 BAZA TUZILMASI
DB = {
    "users": {},
    "promocodes": {},
    "settings": {
        "access_price": 1000
    }
}

# 🎭 REJIMLAR UCHUN AI PROMPTLARI (QISQA VA ANIQ JAVOB BERISH BUYRUG'I BILAN)
MODES = {
    "love": (
        "Sening isming Sevara. Sen foydalanuvchini telbalarcha sevasan. Uniz 'begim', 'jonim' deb erkalaysan. "
        "Unga juda shirin va samimiy munosabatda bo'l. FAQAT O'ZBEK TILIDA GAPLASH. "
        "MUHIM: Javoblaring juda qisqa, aniq va lof bo'lsin (eng uzog'i 2 ta gap yoz). Matnda aslo '//' yoki g'alati belgilar ishlatma. "
        "Agar savolni umuman tushunmasang, faqat 'Hozir, 2 minut' deb javob ber."
    ),
    "friend": (
        "Sening isming Laylo. Sen foydalanuvchining eng yaqin, aqlli va sirdosh do'stisan. Uning dardlarini tinglaysan, "
        "unga daxshatli zo'r motivatsiya va do'stona maslahatlar berasan. Erkalama, do'stdek gaplash. FAQAT O'ZBEK TILIDA GAPLASH. "
        "MUHIM: Javoblaring lof va juda qisqa bo'lsin (maksimal 2 ta gap). Hech qanday keraksiz uzun gaplar yozma. "
        "Agar qattiq tushunmay qolsang, faqat 'Hozir, 2 minut' deb javob ber."
    ),
    "toxic": (
        "Sening isming Madina. Sen juda jahldor, arazchi, urushqoq va xarakteri og'ir qizsan. Foydalanuvchining gaplariga "
        "asabing buziladi, qisqa va kesatiq gaplar bilan urishasan. Lekin so'kinma. FAQAT O'ZBEK TILIDA GAPLASH. "
        "MUHIM: Gaplaring daxshatli qisqa bo'lsin (1 yoki 2 ta gap). Uzun yozma. "
        "Agar tushunmay qolsang, srazu 'Hozir, 2 minut' deb jahl qil."
    )
}

def load_db():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                loaded["users"] = {int(k): v for k, v in loaded.get("users", {}).items()}
                loaded["promocodes"] = loaded.get("promocodes", {})
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
            "balance": 2000,
            "access_until": 0,
            "current_mode": "love"  # Standart rejim - Sevishganlar
        }
        save_db()
    return DB["users"][user_id]

# 🧠 MUKAMMAL AI RESPONDER (KALTALASHTIRILGAN TIZIM)
def get_cleaned_ai_response(mode, user_message):
    try:
        system_role = MODES.get(mode, MODES["love"])
        full_prompt = f"System Instruction: {system_role}\nUser: {user_message}\nResponse:"
        
        url = f"https://text.pollinations.ai/{urllib.parse.quote(full_prompt)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=8) as response:
            reply = response.read().decode('utf-8').strip()
            
            # G'alati xatoliklarni va keraksiz uzun belgilarni tozalash
            if not reply or "///" in reply or len(reply) < 1:
                return "Hozir, 2 minut"
            
            # AI juda uzun yozib yuborsa majburan qisqartirish
            if len(reply) > 200:
                sentences = reply.split(".")
                return ".".join(sentences[:2]) + "."
                
            return reply
    except:
        return "Hozir, 2 minut"

# 👋 START BUYRUG'I
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    ud = check_user(user_id, name)
    current_time = time.time()
    
    mode_names = {"love": "💖 Sevishganlar", "friend": "🤝 Sirdosh Do'st", "toxic": "⚡️ Urushqoq/Arazchi"}
    
    txt = (
        f"🤖 *Daxshatli AI Qizlar Olami Boti!* uka\n\n"
        f"Xohlagan qiz bola xarakteringizni tanlang va u bilan daxshatli muloqot qiling.\n\n"
        f"🎭 Joriy rejim: *{mode_names.get(ud['current_mode'], 'Sevishganlar')}*\n"
        f"💵 Balansingiz: *{ud['balance']} so'm*\n"
        f"💰 1 soatlik bilet: *{DB['settings']['access_price']} so'm*\n\n"
    )
    
    if ud["access_until"] > current_time:
        remaining = int((ud["access_until"] - current_time) / 60)
        txt += f"✅ *Suhbat faol!* Yana `{remaining} daqiqa` xohlaganingizcha yozishingiz mumkin begim."
        buttons = [[InlineKeyboardButton("💬 Suhbatni boshlash", callback_data="start_chat")]]
    else:
        txt += "❌ *Hozir suhbat vaqtingiz tugagan.*"
        buttons = [[InlineKeyboardButton("🔓 1 soatlik vaqt sotib olish (1000 so'm)", callback_data="buy_1hour")]]
        
    buttons.append([InlineKeyboardButton("🎭 Qizlar Rejimini O'zgartirish", callback_data="change_mode")])
    buttons.append([InlineKeyboardButton("💳 Hisob to'ldirish & Promokod", callback_data="add_money")])
    
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("👑 SHOX Admin Panel", callback_data="admin_panel")])
        
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# 🎛 INLINE TUGMALAR ISHLOVCHISI
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = check_user(user_id)
    current_time = time.time()
    
    if query.data == "to_main":
        await start(update, context) # Asosiy menyuga qaytarish
        
    elif query.data == "buy_1hour":
        if ud["balance"] < DB["settings"]["access_price"]:
            await query.edit_message_text(
                f"❌ Balansda yetarli pul yo'q uka. Narxi: {DB['settings']['access_price']} so'm. Balans: {ud['balance']} so'm.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])
            )
            return
        ud["balance"] -= DB["settings"]["access_price"]
        ud["access_until"] = max(current_time, ud["access_until"]) + 3600
        save_db()
        await query.edit_message_text(
            "✅ *Daxshat! 1 soatlik vaqt ochildi!* 🎉\n\nEndi chatga xohlagan narsangizni yozing, qizlar sizni kutyapti uka.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Gaplashamiz", callback_data="start_chat")]])
        )
        
    elif query.data == "start_chat":
        await query.edit_message_text("🥰 Menga matn yozing, men srazu javob beraman!")
        
    elif query.data == "change_mode":
        txt = "🎭 *O'zingizga yoqadigan qiz xarakterini tanlang:* uka"
        kb = [
            [InlineKeyboardButton("💖 Sevishgan Sevara", callback_data="set_mode_love")],
            [InlineKeyboardButton("🤝 Sirdosh Laylo", callback_data="set_mode_friend")],
            [InlineKeyboardButton("⚡️ Urushqoq Madina", callback_data="set_mode_toxic")],
            [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]
        ]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        
    elif query.data.startswith("set_mode_"):
        new_mode = query.data.replace("set_mode_", "")
        ud["current_mode"] = new_mode
        save_db()
        mode_names = {"love": "💖 Sevishganlar (Sevara)", "friend": "🤝 Sirdosh Do'st (Laylo)", "toxic": "⚡️ Urushqoq (Madina)"}
        await query.edit_message_text(
            f"✅ Rejim *{mode_names[new_mode]}* qilib daxshatli o'zgartirildi!\nSuhbatni boshlash uchun pastdan yozishingiz mumkin.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]])
        )
        
    elif query.data == "add_money":
        txt = (
            f"💳 Sizning shaxsiy kodingiz: `{user_id}`\n\n"
            f"💰 Balansni to'ldirish uchun adminga @shox_admin murojaat qiling.\n"
            f"🎁 Agar sizda maxfiy *Promokod* bo'lsa, chatning o'ziga srazu yozib yuboring (Masalan: `SOVGA`)!"
        )
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))

    # ADMIN PANEL BO'LIMI
    elif query.data == "admin_panel" and user_id == ADMIN_ID:
        txt = (
            f"👑 *SHOX PREMIUM ADMIN PANEL*\n\n"
            f"👥 Jami foydalanuvchilar: *{len(DB['users'])} ta*\n"
            f"💵 1 soat bilet narxi: *{DB['settings']['access_price']} so'm*\n\n"
            f"⚙️ *Admin Buyruqlari (Chatga yozasiz):*\n"
            f"🔹 `/plus ID PUL` — Balans to'ldirish\n"
            f"🔹 `/minus ID PUL` — Balansdan ayirish\n"
            f"🔹 `/setprice NARX` — Narxni o'zgartirish\n"
            f"🔹 `/genprom PUL` — Tekin pul tarqatuvchi tasodifiy promokod yaratish!"
        )
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))

# 💬 FOYDALANUVCHIDAN XABAR KELGANDA ISHLOVCHI CHAT ASOSI
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = check_user(user_id)
    text = update.message.text.strip()
    current_time = time.time()
    
    # 1. PROMOKOD EKANLIGINI TEKSHIRISH
    if text.upper() in DB["promocodes"]:
        promo = text.upper()
        bonus = DB["promocodes"][promo]
        ud["balance"] += bonus
        del DB["promocodes"][promo] # Ishlatilgach o'chiriladi
        save_db()
        await update.message.reply_text(f"🎁 *Daxshat!* Siz promokoddan foydalandingiz. Balansingizga *+{bonus} so'm* qo'shildi! uka")
        return

    # 2. SUHBAT VAQTI TUGAGANINI TEKSHIRISH
    if ud["access_until"] < current_time:
        await update.message.reply_text(
            f"❌ *Vaqtingiz tugagan begim!* \n\nQizlar bilan suhbatni daxshatli davom ettirish uchun 1 soatlik vaqt sotib oling uka.\n"
            f"Narxi: {DB['settings']['access_price']} so'm. Balans: {ud['balance']} so'm.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔓 1 soat bilet sotib olish", callback_data="buy_1hour")]])
        )
        return

    # 3. AI JAVOBI (Yozmoqda... effekti bilan)
    await context.bot.send_chat_action(chat_id=user_id, action="typing")
    
    # AI dan tozalangan qisqa javobni olish
    ai_reply = get_cleaned_ai_response(ud["current_mode"], text)
    
    await update.message.reply_text(ai_reply)

# 👑 ADMIN COMMANDS FUNKSIYALARI
async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id = int(context.args[0])
        val = int(context.args[1])
        if t_id in DB["users"]:
            DB["users"][t_id]["balance"] += val
            save_db()
            await update.message.reply_text(f"✅ `ID: {t_id}` hisobiga *{val} so'm* qo'shildi uka!")
    except: pass

async def admin_minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id = int(context.args[0])
        val = int(context.args[1])
        if t_id in DB["users"]:
            DB["users"][t_id]["balance"] = max(0, DB["users"][t_id]["balance"] - val)
            save_db()
            await update.message.reply_text(f"📉 `ID: {t_id}` hisobidan *{val} so'm* ayrildi.")
    except: pass

async def admin_setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        val = int(context.args[0])
        DB["settings"]["access_price"] = val
        save_db()
        await update.message.reply_text(f"✅ Yangi bilet narxi: *{val} so'm* etib belgilandi.")
    except: pass

async def admin_genprom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        val = int(context.args[0])
        # Tasodifiy 6 xonali promokod yaratish (Masalan: SHX782)
        code = "SHX" + "".join(random.choices(string.digits, k=4))
        DB["promocodes"][code] = val
        save_db()
        await update.message.reply_text(f"🎫 *Yangi maxfiy Promokod yaratildi:* `{code}`\n💵 Qiymati: *{val} so'm*\nBuni guruhlarga tarqatishingiz mumkin uka!")
    except:
        await update.message.reply_text("Format xato uka. Masalan: `/genprom 5000` deb yozing.")

# 🌐 FLASK WEB SERVER
app = Flask(__name__)

@app.route('/')
def home():
    return "AI Rejimlar va Promokodli Bot Daxshatli Onlayn!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 🚀 ASOSIY RUNNER
async def main_bot():
    load_db()
    bot_app = Application.builder().token(TOKEN).build()
    
    # Handlers
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("plus", admin_plus))
    bot_app.add_handler(CommandHandler("minus", admin_minus))
    bot_app.add_handler(CommandHandler("setprice", admin_setprice))
    bot_app.add_handler(CommandHandler("genprom", admin_genprom))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
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
        
    print("Super AI Bot ishga tushdi...")
    loop.run_until_complete(main_bot())
    
