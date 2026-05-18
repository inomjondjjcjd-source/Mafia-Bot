import os
import sys
import subprocess
import json
import asyncio
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
DATA_FILE = "ai_image_bot_db.json"

# 📊 MA'LUMOTLAR BAZASI
DB = {
    "users": {},
    "settings": {
        "gen_price": 1000  # 💰 Har bir rasm 1000 so'm
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
            "balance": 5000,  # 🎁 Yangi a'zoga bonus
            "generated_count": 0
        }
        save_db()
    return DB["users"][user_id]

# 🌐 O'ZBEKCHADAN INGLIZCHAGA AVTO-TARJIMON FUNKSIYASI
def translate_to_english(text):
    try:
        # Google Translate bepul API orqali tarjima qilish
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(text)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res[0][0][0]
    except:
        return text  # Agar tarjimada xato bo'lsa, matnni o'zini qaytaradi

# 👋 START BUYRUG'I
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    check_user(user_id, name)
    
    txt = (
        f"🎨 *AI Rasm Chizuvchi Botga xush kelibsiz!* uka\n\n"
        f"Menga endi bemalol *O'zbek tilida* xohlagan rasmingizni yozib yuboring! Bot uni o'zi tarjima qilib, daxshatli va aniq qilib chizib beradi.\n\n"
        f"💰 *Narxi:* 1 ta rasm = *{DB['settings']['gen_price']} so'm*"
    )
    
    buttons = [
        [InlineKeyboardButton("💳 Hisobim / Balans", callback_data="my_balance")],
        [InlineKeyboardButton("📖 Botdan foydalanish", callback_data="bot_guide")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("👑 SHOX Admin Panel", callback_data="admin_panel")])
        
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# 🎛 INLINE TUGMALAR ISHLOVCHISI
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = check_user(user_id)
    
    if query.data == "to_main":
        txt = (
            f"🎨 *AI Rasm Generatsiya qiluvchi bot uka!*\n"
            f"Menga shunchaki rasm matnini yozib yuboring.\n\n"
            f"💰 Narxi: *{DB['settings']['gen_price']} so'm*"
        )
        buttons = [
            [InlineKeyboardButton("💳 Hisobim / Balans", callback_data="my_balance")],
            [InlineKeyboardButton("📖 Botdan foydalanish", callback_data="bot_guide")]
        ]
        if user_id == ADMIN_ID:
            buttons.append([InlineKeyboardButton("👑 SHOX Admin Panel", callback_data="admin_panel")])
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data == "my_balance":
        txt = (
            f"💳 *Sizning hisobingiz kodi:* `{user_id}`\n\n"
            f"💰 Balans: *{ud['balance']} so'm*\n"
            f"🖼 Chizilgan rasmlar: {ud['generated_count']} ta"
        )
        kb = [[InlineKeyboardButton("💰 Pul solish", callback_data="add_cash")], [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "add_cash":
        txt = f"💰 Hisobingizni to'ldirish uchun o'z ID kodingizni (`{user_id}`) admin @shox_admin ga yuboring uka."
        kb = [[InlineKeyboardButton("⬅️ Ortga", callback_data="my_balance")]]
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "bot_guide":
        txt = "📖 *Bot qanday ishlaydi?*\n\nBotga o'zbekcha yozasiz. Masalan: `Dengiz bo'yida qizil nexia`. Bot hisobingizdan 1000 so'm yechib, daxshatli va aniq rasmni tayyorlab beradi!"
        kb = [[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "admin_panel" and user_id == ADMIN_ID:
        txt = (
            f"👑 *SHOX ADMIN PANEL*\n\n"
            f"👥 Jami foydalanuvchilar: *{len(DB['users'])} ta*\n"
            f"💵 Rasm narxi: *{DB['settings']['gen_price']} so'm*\n\n"
            f"👑 *Balansni boshqarish buyruqlari:*\n"
            f"🔹 `/plus ID PUL` — Pul qo'shish\n"
            f"🔹 `/minus ID PUL` — Pul ayirish\n"
            f"🔹 `/setprice NARX` — Narxni o'zgartirish"
        )
        kb = [[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# 🎨 RASM GENERATSIYA QILISH TIZIMI (ANIQ VA TARJIMONLI)
async def image_generation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = check_user(user_id)
    prompt_text = update.message.text.strip()
    
    if ud["balance"] < DB["settings"]["gen_price"]:
        await update.message.reply_text(f"❌ Hisobingizda mablag' yetarli emas uka! Balans: {ud['balance']} so'm.")
        return

    waiting_msg = await update.message.reply_text("⏳ *AI siz yozgan so'rovni tahlil qilib, daxshatli va aniq rasm chizmoqda...* Kuting uka...", parse_mode="Markdown")

    try:
        # 🔄 O'zbekcha so'zni inglizchaga o'giramiz (Aniq chizishi uchun)
        english_prompt = translate_to_english(prompt_text)
        
        # Sifatni va aniqlikni oshiruvchi daxshatli SMM teglar qo'shamiz (Ultra-realistic, 4k, highly detailed)
        final_prompt = f"{english_prompt}, ultra realistic, 4k resolution, highly detailed, cinematic lighting"
        encoded_prompt = urllib.parse.quote(final_prompt)
        
        # Pollinations yangi Flux/Aniq modeli yordamida rasm generatsiyasi
        image_url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1080&height=1080&enhanced=true"
        
        # Balansdan yechish
        ud["balance"] -= DB["settings"]["gen_price"]
        ud["generated_count"] += 1
        save_db()
        
        # Rasmni yuborish
        await context.bot.send_photo(
            chat_id=user_id,
            photo=image_url,
            caption=f"✅ *Sizning aniq rasmingiz tayyor uka!*\n\n📝 *So'rov:* `{prompt_text}`\n🇬🇧 *AI tushungan tili:* `{english_prompt}`\n💸 *Yechildi:* {DB['settings']['gen_price']} so'm\n💳 *Qolgan balans:* {ud['balance']} so'm",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Rasmni yaratishda xatolik: {str(e)}")
    finally:
        await waiting_msg.delete()

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
            await update.message.reply_text(f"📉 `ID: {target_id}` balansidan *{amount} so'm* ayirildi!")
    except: pass

async def admin_setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        price = int(context.args[0])
        DB["settings"]["gen_price"] = price
        save_db()
        await update.message.reply_text(f"✅ Yangi narx belgilandi: *{price} so'm*")
    except: pass

# 🌐 FLASK SERVER
app = Flask(__name__)

@app.route('/')
def home():
    return "AI Rasm Tarjimonli Boti Faol!"

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
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, image_generation_handler))
    
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
        
    print("Tarjimonli AI rasm boti ishga tushdi...")
    loop.run_until_complete(main_bot())
                  
