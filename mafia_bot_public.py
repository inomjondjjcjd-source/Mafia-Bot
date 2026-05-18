import os
import sys
import subprocess
import json
import asyncio
import urllib.parse
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
ADMIN_ID = 8086545587  # 👑 Sening aniq shaxsiy ID'ngiz (Shox Admin)
DATA_FILE = "ai_image_bot_db.json"

# 📊 MA'LUMOTLAR BAZASI
DB = {
    "users": {},
    "settings": {
        "gen_price": 1000  # 💰 Siz aytgandek: Har bir rasm 1000 so'm!
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
            "balance": 5000,  # 🎁 Yangi kirgandagi daxshatli 5,000 so'm bonus (5 ta rasm uchun)
            "generated_count": 0
        }
        save_db()
    return DB["users"][user_id]

# 👋 START BUYRUG'I
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    check_user(user_id, name)
    
    txt = (
        f"🎨 *AI Rasm Generatsiya qiluvchi botga xush kelibsiz!* uka\n\n"
        f"Menga ingliz yoki o'zbek tilida xohlagan rasmingiz tasvirini yozib yuboring, men uni sun'iy intellekt (AI) yordamida chizib beraman!\n\n"
        f"💰 *Xizmat narxi:* Har bir rasm generatsiyasi = *{DB['settings']['gen_price']} so'm*\n"
        f"👇 Quyidagi tugmalar orqali balansingizni ko'rishingiz mumkin."
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
    
    # BOSH MENYUGA QAYTISH
    if query.data == "to_main":
        txt = (
            f"🎨 *AI Rasm Generatsiya qiluvchi bot uka!*\n\n"
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

    # BALANSNI KO'RISH
    elif query.data == "my_balance":
        txt = (
            f"💳 *Sizning hisobingiz kodi:* `{user_id}`\n\n"
            f"💰 Balans: *{ud['balance']} so'm*\n"
            f"🖼 Chizilgan rasmlar: {ud['generated_count']} ta"
        )
        kb = [[InlineKeyboardButton("💰 Pul solish", callback_data="add_cash")], [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # PUL SOLISH KO'RSATMASI
    elif query.data == "add_cash":
        txt = f"💰 Hisobingizni to'ldirish uchun o'z ID kodingizni (`{user_id}`) admin @shox_admin ga yuboring uka."
        kb = [[InlineKeyboardButton("⬅️ Ortga", callback_data="my_balance")]]
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

    # QO'LLANMA
    elif query.data == "bot_guide":
        txt = "📖 *Bot qanday ishlaydi?*\n\nBotga shunchaki xabar yozasiz. Masalan: `Red sport car in future city`. Bot hisobingizdan 1000 so'm yechib, daxshatli rasmni tayyorlab beradi!"
        kb = [[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # ADMIN PANEL
    elif query.data == "admin_panel" and user_id == ADMIN_ID:
        txt = (
            f"👑 *SHOX ADMIN PANEL*\n\n"
            f"👥 Jami foydalanuvchilar: *{len(DB['users'])} ta*\n"
            f"💵 Rasm narxi: *{DB['settings']['gen_price']} so'm*\n\n"
            f"👑 *Balansni boshqarish buyruqlari:* (Botga to'g'ridan-to'g'ri yozasiz)\n"
            f"🔹 `/plus ID PUL` — Foydalanuvchiga pul qo'shish\n"
            f"🔹 `/minus ID PUL` — Foydalanuvchidan pul ayirish\n"
            f"🔹 `/setprice NARX` — Rasm narxini o'zgartirish"
        )
        kb = [[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# 🎨 RASM GENERATSIYA QILISH TIZIMI (MATN KELGANDA)
async def image_generation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = check_user(user_id)
    prompt_text = update.message.text.strip()
    
    # Balansni tekshirish
    if ud["balance"] < DB["settings"]["gen_price"]:
        await update.message.reply_text(
            f"❌ Hisobingizda mablag' yetarli emas uka!\n"
            f"Rasm chizish: {DB['settings']['gen_price']} so'm.\n"
            f"Sizning balansingiz: {ud['balance']} so'm.\n"
            f"To'ldirish uchun adminga yozing."
        )
        return

    # Kutish xabari
    waiting_msg = await update.message.reply_text("⏳ *AI so'rovingiz bo'yicha daxshatli rasm chizmoqda...* Iltimos biroz kuting uka...", parse_mode="Markdown")

    try:
        # Pollinations AI yordamida mutlaqo bepul va xatosiz rasm URL manzilini yaratish
        encoded_prompt = urllib.parse.quote(prompt_text)
        image_url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1080&height=1080&enhanced=true&seed=42"
        
        # Balansdan pul yechish
        ud["balance"] -= DB["settings"]["gen_price"]
        ud["generated_count"] += 1
        save_db()
        
        # Rasmni foydalanuvchiga yuborish
        await context.bot.send_photo(
            chat_id=user_id,
            photo=image_url,
            caption=f"✅ *Sizning rasmingiz tayyor uka!*\n\n📝 *So'rov:* `{prompt_text}`\n💸 *Yechildi:* {DB['settings']['gen_price']} so'm\n💳 *Qolgan balans:* {ud['balance']} so'm",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Rasmni yaratishda xatolik yuz berdi uka: {str(e)}")
    finally:
        # Kutish xabarini o'chirish
        await waiting_msg.delete()

# 👑 ADMIN BUYRUQLARI TIZIMI
async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        if target_id in DB["users"]:
            DB["users"][target_id]["balance"] += amount
            save_db()
            await update.message.reply_text(f"✅ `ID: {target_id}` balansiga *{amount} so'm* muvaffaqiyatli qo'shildi uka!")
        else:
            await update.message.reply_text("❌ Bunday ID'li foydalanuvchi botda ro'yxatdan o'tmagan.")
    except:
        await update.message.reply_text("❌ Xato format. To'g'ri foydalanish: `/plus ID PUL`")

async def admin_minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        if target_id in DB["users"]:
            DB["users"][target_id]["balance"] = max(0, DB["users"][target_id]["balance"] - amount)
            save_db()
            await update.message.reply_text(f"📉 `ID: {target_id}` balansidan *{amount} so'm* ayirib tashlandi!")
    except:
        await update.message.reply_text("❌ Xato format. To'g'ri foydalanish: `/minus ID PUL`")

async def admin_setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        price = int(context.args[0])
        DB["settings"]["gen_price"] = price
        save_db()
        await update.message.reply_text(f"✅ Rasm generatsiyasining yangi narxi belgilandi: *{price} so'm*")
    except:
        await update.message.reply_text("❌ To'g'ri foydalanish: `/setprice NARX`")

# 🌐 FLASK WEB SERVER (RENDER PANELI UCHUN)
app = Flask(__name__)

@app.route('/')
def home():
    return "AI Rasm Generatsiya Boti Daxshatli Rejimda Ishlamoqda!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 🚀 BOTNI ISHGA TUSHIRISH
async def main_bot():
    load_db()
    bot_app = Application.builder().token(TOKEN).build()
    
    # Handlerlarni ulash
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
    # Flaskni alohida oqimda yoqish
    Thread(target=run_flask, daemon=True).start()
    
    # Asinxron tizim
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    print("AI Rasm Generatsiya boti daxshatli muvaffaqiyat bilan yoqildi...")
    loop.run_until_complete(main_bot())
    
