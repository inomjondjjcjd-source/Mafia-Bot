import os
import sys
import subprocess
import json
import asyncio
import time
import random
import string
from flask import Flask
from threading import Thread

# 📦 KUTUBXONALARNI TEKSHIRISH VA AVTO-O'RNATISH
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
DATA_FILE = "omad_shou_bot_db.json"

# 📊 BAZA TUZILMASI
DB = {
    "users": {},
    "promocodes": {},
    "settings": {
        "vip_price": 40000,       # 💰 Kunlik VIP obuna narxi = 40,000 so'm
        "ticket_price": 2000,     # 🎫 Oddiy 1 ta o'yin chiptasi narxi = 2,000 so'm
        "min_withdraw": 15000     # 💳 Minimal pul yechish miqdori
    },
    "stats": {
        "total_games": 0,
        "total_prizes_given": 0
    }
}

# 🎁 OMAD SHOU SOVG'ALARI VA EHTIMOLLIKLARI
PRIZES = [
    {"name": "🎁 500 so'm bonus", "type": "balance", "value": 500, "weight": 40},
    {"name": "🎁 1,500 so'm bonus", "type": "balance", "value": 1500, "weight": 25},
    {"name": "🎁 5,000 so'm katta bonus!", "type": "balance", "value": 5000, "weight": 10},
    {"name": "🎁 10,000 so'm JEKPOT!", "type": "balance", "value": 10000, "weight": 3},
    {"name": "💎 Free Fire 110 Olmos Kuponi", "type": "code", "value": "FF-DIAMOND-772X", "weight": 5},
    {"name": "💎 Free Fire 231 Olmos Kuponi", "type": "code", "value": "FF-VIP-OLMOS-991A", "weight": 2},
    {"name": "🎫 Tekin O'yin Chiptasi", "type": "ticket", "value": 1, "weight": 10},
    {"name": "❌ Afsuski bu safar omad kelmadi!", "type": "nothing", "value": 0, "weight": 5}
]

def load_db():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                loaded["users"] = {int(k): v for k, v in loaded.get("users", {}).items()}
                loaded["promocodes"] = loaded.get("promocodes", {})
                if "stats" not in loaded: loaded["stats"] = {"total_games": 0, "total_prizes_given": 0}
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
            "balance": 5000,         # 🎁 Yangi kirgan odamga 5,000 so'm start bonus!
            "tickets": 2,            # 🎫 2 ta tekin o'yin chiptasi
            "vip_until": 0,          # 🕒 VIP obuna tugash vaqti
            "total_won": 0,          # 🏆 Jami yutgan pullari
            "games_played": 0
        }
        save_db()
    return DB["users"][user_id]

# 🎰 TASODIFIY SOVG'A TANLASH
def spin_wheel():
    prizes_list = []
    for p in PRIZES:
        prizes_list.extend([p] * p["weight"])
    return random.choice(prizes_list)

# 👋 START BUYRUG'I
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    ud = check_user(user_id, name)
    current_time = time.time()
    
    is_vip = ud["vip_until"] > current_time
    vip_status = "🔥 FAOL (Cheksiz kirish)" if is_vip else "❌ Faol emas"
    
    txt = (
        f"🎰 *Xush kelibsiz daxshatli OMAD SHOU Botiga!* uka\n\n"
        f"Bu yerda siz virtual g'ildirakni aylantirib, balansga haqiqiy pul, omadli chiptalar va Free Fire olmoslarini yutib olishingiz mumkin! 🎉\n\n"
        f"💳 *Sizning balansingiz:* {ud['balance']} so'm\n"
        f"🎫 *O'yin chiptalaringiz:* {ud['tickets']} ta\n"
        f"👑 *VIP status:* {vip_status}\n"
    )
    
    if is_vip:
        rem = int((ud["vip_until"] - current_time) / 60)
        txt += f"🕒 VIP tugashiga: `{rem} daqiqa` qoldi.\n"

    buttons = [
        [InlineKeyboardButton("🎰 G'ildirakni Aylantirish", callback_data="play_game")],
        [InlineKeyboardButton("👑 24 soatlik VIP sotib olish (40k)", callback_data="buy_vip"), 
         InlineKeyboardButton("🎫 Chipta olish (2k)", callback_data="buy_ticket")],
        [InlineKeyboardButton("💳 Pul yechish", callback_data="withdraw"),
         InlineKeyboardButton("🎁 Promokod kiritish", callback_data="use_promo")],
        [InlineKeyboardButton("📊 Shaxsiy statistika", callback_data="my_stats")]
    ]
    
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("👑 SHOX Boshqaruv Paneli", callback_data="admin_panel")])
        
    reply_markup = InlineKeyboardMarkup(buttons)
    if update.message:
        await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=reply_markup)

# 🎛 TUGMALAR ISHLOVCHISI
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = check_user(user_id)
    current_time = time.time()
    
    if query.data == "to_main":
        await start(update, context)

    # 🎰 O'YIN O'YNASh
    elif query.data == "play_game":
        is_vip = ud["vip_until"] > current_time
        
        if not is_vip and ud["tickets"] < 1:
            await query.edit_message_text(
                "❌ *Afsuski chiptalaringiz tugadi uka!*\n\nG'ildirakni aylantirish uchun chipta sotib oling yoki 40,000 so'mga 24 soatlik cheksiz VIP rejimini yoqing!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎫 1 ta chipta olish (2,000 so'm)", callback_data="buy_ticket")],
                    [InlineKeyboardButton("👑 VIP rejimni yoqish (40,000 so'm)", callback_data="buy_vip")],
                    [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]
                ])
            )
            return
            
        if not is_vip:
            ud["tickets"] -= 1
            
        ud["games_played"] += 1
        DB["stats"]["total_games"] += 1
        
        await query.edit_message_text("🔄 *Omad g'ildiragi daxshatli aylanyapti...* \n[ 🟥 🟨 🟩 🟦 🟪 ]")
        await asyncio.sleep(1)
        await query.edit_message_text("🔄 *Sovg'a aniqlanyapti...* \n[ 💎 🎁 🎫 ❌ 💰 ]")
        await asyncio.sleep(0.8)
        
        prize = spin_wheel()
        result_text = f"🎰 *OMAD SHOU NATIJASI!* 🎉\n\nSizga daxshatli omad kulib boqdi:\n* {prize['name']} * \n\n"
        
        if prize["type"] == "balance":
            ud["balance"] += prize["value"]
            ud["total_won"] += prize["value"]
            DB["stats"]["total_prizes_given"] += prize["value"]
            result_text += f"💵 Hisobingizga *+{prize['value']} so'm* qo'shildi!"
        elif prize["type"] == "ticket":
            ud["tickets"] += prize["value"]
            result_text += f"🎫 Balansingizga *+{prize['value']} ta chipta* qo'shildi!"
        elif prize["type"] == "code":
            secret_code = "WIN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
            result_text += f"💎 Maxfiy Olmos kodi: `{secret_code}`\nBuni adminga topshirib olmosni yuklab oling!"
        else:
            result_text += "🥺 Xavotir olmang, keyingi safar albatta yutasiz uka!"
            
        save_db()
        kb = [[InlineKeyboardButton("🎰 Yana aylantirish", callback_data="play_game")], [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]]
        await query.edit_message_text(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # 🎫 CHIPTA SOTIB OLISH
    elif query.data == "buy_ticket":
        if ud["balance"] < DB["settings"]["ticket_price"]:
            await query.edit_message_text(
                f"❌ Balansda etarli mablag' yo'q uka. Balans: {ud['balance']} so'm.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])
            )
            return
        ud["balance"] -= DB["settings"]["ticket_price"]
        ud["tickets"] += 1
        save_db()
        await query.edit_message_text("✅ 1 ta o'yin chiptasi muvaffaqiyatli sotib olindi!", 
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎰 O'yinga kirish", callback_data="play_game")]]))

    # 👑 VIP REJIM SOTIB OLISH (40,000 SO'M)
    elif query.data == "buy_vip":
        if ud["balance"] < DB["settings"]["vip_price"]:
            await query.edit_message_text(
                f"❌ VIP rejim narxi {DB['settings']['vip_price']} so'm. Balans: {ud['balance']} so'm.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])
            )
            return
        ud["balance"] -= DB["settings"]["vip_price"]
        ud["vip_until"] = max(current_time, ud["vip_until"]) + 86400  # +24 soat
        save_db()
        await query.edit_message_text("🔥 daxshat! 24 soatlik cheksiz VIP obuna yoqildi. Endi tekinga aylantirasiz!", 
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎰 O'yinni boshlash", callback_data="play_game")]]))

    # 💳 PUL YECHISH
    elif query.data == "withdraw":
        if ud["balance"] < DB["settings"]["min_withdraw"]:
            await query.edit_message_text(
                f"❌ Minimal pul yechish miqdori: *{DB['settings']['min_withdraw']} so'm*.\nBalans: {ud['balance']} so'm.",
                parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])
            )
        else:
            await query.edit_message_text(
                f"💳 Balansizda pul bor uka: {ud['balance']} so'm.\n\nPulni yechish uchun ID kodingizni (`{user_id}`) admin @shox_admin ga yuboring!",
                parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])
            )

    elif query.data == "use_promo":
        await query.edit_message_text("🎁 *Promokod:* Maxfiy kodni to'g'ridan-to'g'ri chatga yozib yuboring (Masalan: `OMAD2026`).", 
                                      parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))

    elif query.data == "my_stats":
        txt = (
            f"📊 *Sizning statistikangiz uka:*\n\n"
            f"🏆 Jami yutib olingan pul: *{ud['total_won']} so'm*\n"
            f"🕹 G'ildirak aylantirilgan soni: {ud['games_played']} ta\n"
            f"🎫 Chiptalar qoldig'i: {ud['tickets']} ta\n"
            f"🆔 Shaxsiy ID: `{user_id}`"
        )
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))

    # 👑 ADMIN PANEL
    elif query.data == "admin_panel" and user_id == ADMIN_ID:
        txt = (
            f"👑 *SHOX OMAD SHOU BOSHQARUV PANELI*\n\n"
            f"👥 Jami ro'yxatdan o'tganlar: *{len(DB['users'])} ta*\n"
            f"🎰 Jami o'ynalgan o'yinlar: *{DB['stats']['total_games']} marta*\n"
            f"💰 Jami tarqatilgan bonuslar: *{DB['stats']['total_prizes_given']} so'm*\n"
            f"🎫 Aktiv promokodlar: *{len(DB['promocodes'])} ta*\n\n"
            f"⚙️ *Admin buyruqlari (Chatga yozasiz):*\n"
            f"🔸 `/plus ID PUL` — Balans qo'shish\n"
            f"🔸 `/minus ID PUL` — Balansdan ayirish\n"
            f"🔸 `/give_ticket ID SONI` — Tekin chipta berish\n"
            f"🔸 `/genprom PUL` — Promokod yaratish\n"
            f"🔸 `/setprice NARX` — VIP narxini o'zgartirish"
        )
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]]))

# 💬 FOYDALANUVCHIDAN XABAR KELGANDA (PROMOKOD TEKSHIRISH TIZIMI)
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = check_user(user_id)
    text = update.message.text.strip()
    
    if text.upper() in DB["promocodes"]:
        promo = text.upper()
        bonus_amount = DB["promocodes"][promo]
        ud["balance"] += bonus_amount
        del DB["promocodes"][promo]
        save_db()
        await update.message.reply_text(f"🎁 *Daxshatli Omad!* Promokod qabul qilindi. *+{bonus_amount} so'm* qo'shildi uka!")
        return
        
    await update.message.reply_text("🎰 Omad shouni boshlash uchun pastdagi tugmani bosing uka!", 
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 O'yin menyusini ochish", callback_data="to_main")]]))

# 👑 ADMIN COMMANDS FUNKSIYALARI
async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id = int(context.args[0])
        val = int(context.args[1])
        if t_id in DB["users"]:
            DB["users"][t_id]["balance"] += val
            save_db()
            await update.message.reply_text(f"✅ `ID: {t_id}` balansiga *{val} so'm* qo'shildi uka!")
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

async def admin_give_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id = int(context.args[0])
        count = int(context.args[1])
        if t_id in DB["users"]:
            DB["users"][t_id]["tickets"] += count
            save_db()
            await update.message.reply_text(f"🎫 `ID: {t_id}` profiliga *{count} ta* tekin chipta sovg'a qilindi!")
    except: pass

async def admin_setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        val = int(context.args[0])
        DB["settings"]["vip_price"] = val
        save_db()
        await update.message.reply_text(f"⚙️ Kunlik VIP obuna narxi yangilandi: *{val} so'm*")
    except: pass

async def admin_genprom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        val = int(context.args[0])
        code = "OMAD-" + "".join(random.choices(string.digits, k=5))
        DB["promocodes"][code] = val
        save_db()
        await update.message.reply_text(f"🎫 *Yangi universal Promokod yaratildi:* `{code}`\n💰 Qiymati: *{val} so'm*")
    except: pass

# 🌐 FLASK WEB SERVER (RENDER UCHUN SRAZU CHURILADI)
app = Flask(__name__)

@app.route('/')
def home():
    return "Omad Shou Mukammal Tizim Boti Daxshatli Onlayn!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 🚀 ASOSIY RUNNER TIZIM
async def main_bot():
    load_db()
    bot_app = Application.builder().token(TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("plus", admin_plus))
    bot_app.add_handler(CommandHandler("minus", admin_minus))
    bot_app.add_handler(CommandHandler("give_ticket", admin_give_ticket))
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
        
    print("Omad Shou Tizimli Boti daxshatli ishga tushdi...")
    loop.run_until_complete(main_bot())
