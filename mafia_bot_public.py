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
DATA_FILE = "omad_shou_premium_db.json"

# 📊 PREMIUM BAZA TUZILMASI
DB = {
    "users": {},
    "promocodes": {},
    "settings": {
        "vip_price": 40000,       # 💰 Kunlik VIP obuna narxi = 40,000 so'm
        "ticket_price": 4000,     # 🎫 1 ta o'yin chiptasi narxi = 4,000 so'm (Pullik qilindi!)
        "min_withdraw": 15000     # 💳 Minimal pul yechish miqdori
    },
    "stats": {
        "total_games": 0,
        "total_prizes_given": 0
    }
}

# 🎁 YANGILANGAN MUKOFOTLAR TIZIMI (ENG KAMI 1,000 SO'M, FF YO'QOTILDI)
PRIZES = [
    {"name": "💰 1,000 so'm naqd bonus", "type": "balance", "value": 1000, "weight": 45},
    {"name": "💰 3,000 so'm o'rtacha bonus", "type": "balance", "value": 3000, "weight": 25},
    {"name": "🔥 7,000 so'm daxshatli bonus!", "type": "balance", "value": 7000, "weight": 12},
    {"name": "👑 15,000 so'm SUPREME JEKPOT!", "type": "balance", "value": 15000, "weight": 3},
    {"name": "🎫 1 ta O'yin Chiptasi", "type": "ticket", "value": 1, "weight": 10},
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
            "balance": 5000,         # 🎁 Yangi kirgan odamga 5,000 so'm start bonus! (Chipta sotib olishga yetadi)
            "tickets": 0,            # ❌ Boshida tekin chipta berilmaydi!
            "vip_until": 0,          # 🕒 VIP obuna tugash vaqti
            "total_won": 0,          # 🏆 Jami yutgan pullari
            "games_played": 0
        }
        save_db()
    return DB["users"][user_id]

# 🎰 OMAD G'ILDIRAGI TASODIFIY TANLOV
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
    vip_status = "🔥 FAOL (Cheksiz o'yin)" if is_vip else "❌ Faol emas"
    
    txt = (
        f"🎰 *MUKAMMAL OMAD SHOU PREMIUM BOTI* uka\n\n"
        f"G'ildirakni daxshatli aylantiring va balansga real pullar yutib oling! 🎉\n\n"
        f"💵 *Sizning balansingiz:* {ud['balance']} so'm\n"
        f"🎫 *O'yin chiptalaringiz:* {ud['tickets']} ta\n"
        f"👑 *VIP Status (24 soat):* {vip_status}\n"
    )
    
    if is_vip:
        rem = int((ud["vip_until"] - current_time) / 60)
        txt += f"🕒 VIP tugashiga: `{rem} daqiqa` qoldi.\n"

    buttons = [
        [InlineKeyboardButton("🎰 G'ildirakni Aylantirish", callback_data="play_game")],
        [InlineKeyboardButton("👑 VIP rejimni yoqish (40k)", callback_data="buy_vip"), 
         InlineKeyboardButton("🎫 Chipta sotib olish (4k)", callback_data="buy_ticket")],
        [InlineKeyboardButton("💳 Pul yechish", callback_data="withdraw"),
         InlineKeyboardButton("🎁 Promokod kiritish", callback_data="use_promo")],
        [InlineKeyboardButton("📊 Shaxsiy statistika", callback_data="my_stats")]
    ]
    
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("👑 SHOX Admin Panel", callback_data="admin_panel")])
        
    reply_markup = InlineKeyboardMarkup(buttons)
    if update.message:
        await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=reply_markup)

# 🎛 INLINE TUGMALAR ISHLOVCHISI (DETALLASHTIRILGAN)
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = check_user(user_id)
    current_time = time.time()
    
    if query.data == "to_main":
        await start(update, context)

    # 🎰 O'YIN O'YNASh TIZIMI
    elif query.data == "play_game":
        is_vip = ud["vip_until"] > current_time
        
        if not is_vip and ud["tickets"] < 1:
            await query.edit_message_text(
                f"❌ *Sizda o'yin chiptasi yo'q uka!*\n\nG'ildirakni aylantirish uchun chipta sotib oling ({DB['settings']['ticket_price']} so'm) yoki 24 soatlik cheksiz VIP yoqing!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"🎫 1 ta chipta sotib olish ({DB['settings']['ticket_price']} so'm)", callback_data="buy_ticket")],
                    [InlineKeyboardButton("👑 VIP rejimni yoqish (40,000 so'm)", callback_data="buy_vip")],
                    [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]
                ])
            )
            return
            
        if not is_vip:
            ud["tickets"] -= 1
            
        ud["games_played"] += 1
        DB["stats"]["total_games"] += 1
        
        await query.edit_message_text("🔄 *Omad g'ildiragi mukammal aylanyapti...* \n[ 🟩 🟦 🟨 🟥 🟪 ]")
        await asyncio.sleep(0.8)
        await query.edit_message_text("🔄 *Yutuq hisoblanmoqda...* \n[ 💰 🎁 🎫 ❌ 💰 ]")
        await asyncio.sleep(0.6)
        
        prize = spin_wheel()
        result_text = f"🎰 *OMAD SHOU NATIJASI!* 🎉\n\nSizga daxshatli omad kulib boqdi:\n* {prize['name']} * \n\n"
        
        if prize["type"] == "balance":
            ud["balance"] += prize["value"]
            ud["total_won"] += prize["value"]
            DB["stats"]["total_prizes_given"] += prize["value"]
            result_text += f"💵 Hisobingizga *+{prize['value']} so'm* qo'shildi!"
        elif prize["type"] == "ticket":
            ud["tickets"] += prize["value"]
            result_text += f"🎫 Hisobingizga *+{prize['value']} ta yangi chipta* qo'shildi!"
        else:
            result_text += "🥺 Xavotir olmang, keyingi safar albatta yirik pul yutasiz uka!"
            
        save_db()
        kb = [[InlineKeyboardButton("🎰 Yana aylantirish", callback_data="play_game")], [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]]
        await query.edit_message_text(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # 🎫 CHIPTA SOTIB OLISH (PULLIK — 4,000 SO'M)
    elif query.data == "buy_ticket":
        if ud["balance"] < DB["settings"]["ticket_price"]:
            await query.edit_message_text(
                f"❌ Balansda etarli mablag' yo'q uka. 1 ta chipta: {DB['settings']['ticket_price']} so'm. Balans: {ud['balance']} so'm.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])
            )
            return
        ud["balance"] -= DB["settings"]["ticket_price"]
        ud["tickets"] += 1
        save_db()
        await query.edit_message_text(f"✅ 1 ta o'yin chiptasi {DB['settings']['ticket_price']} so'mga sotib olindi!", 
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
        ud["vip_until"] = max(current_time, ud["vip_until"]) + 86400
        save_db()
        await query.edit_message_text("🔥 Daxshat! 24 soatlik cheksiz VIP obuna yoqildi. Endi chiptasiz mutlaqo tekin aylantirasiz!", 
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎰 Cheksiz o'yinni boshlash", callback_data="play_game")]]))

    # 💳 PUL YECHISH (TO'G'RIDAN-TO'G'RI LICHKANGIZGA O'TADIGAN QILINDI!)
    elif query.data == "withdraw":
        if ud["balance"] < DB["settings"]["min_withdraw"]:
            await query.edit_message_text(
                f"❌ Minimal pul yechish miqdori: *{DB['settings']['min_withdraw']} so'm*.\nSizning balansingiz: {ud['balance']} so'm uka.",
                parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])
            )
        else:
            txt = (
                f"💳 *PUL YECHISH TIZIMI MUKAMMAL* uka\n\n"
                f"Sizning balansingiz: *{ud['balance']} so'm*\n"
                f"Sizning shaxsiy ID kodingiz: `{user_id}`\n\n"
                f"⚠️ *Diqqat:* Pulni karta yoki telefon raqamingizga daxshatli tez yechib olish uchun pastdagi *'👑 Admin Lichkasi'* tugmasini bosing va adminga shaxsiy ID kodingizni yuboring!"
            )
            # Lichkangizga havola beruvchi tugma
            kb = [
                [InlineKeyboardButton("👑 Admin Lichkasi (Shox)", url="https://t.me/shox_admin")],
                [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]
            ]
            await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "use_promo":
        await query.edit_message_text("🎁 *Promokod:* Admin bergan maxfiy pul kodini srazu chatning o'ziga yozib yuboring (Masalan: `OMAD2026`). Pulingiz avtomat hisobga o'tadi!", 
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

    # 👑 MUKAMMAL ADMIN PANEL
    elif query.data == "admin_panel" and user_id == ADMIN_ID:
        txt = (
            f"👑 *SHOX PREMIUM ADMIN PANEL*\n\n"
            f"👥 Jami oshiqlar (A'zolar): *{len(DB['users'])} ta*\n"
            f"🎰 Jami aylantirilgan g'ildirak: *{DB['stats']['total_games']} marta*\n"
            f"💰 Jami yutilgan summalar: *{DB['stats']['total_prizes_given']} so'm*\n"
            f"🎫 Aktiv promokodlar: *{len(DB['promocodes'])} ta*\n\n"
            f"⚙️ *Admin boshqaruv buyruqlari:*\n"
            f"🔹 `/plus ID PUL` — Hisob to'ldirish\n"
            f"🔹 `/minus ID PUL` — Hisobdan ayirish\n"
            f"🔹 `/give_ticket ID SONI` — Tekin chipta berish\n"
            f"🔹 `/genprom PUL` — Promokod yaratish\n"
            f"🔹 `/setprice NARX` — VIP narxini o'zgartirish"
        )
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]]))

# 💬 PROMOKOD TEKSHIRISH CHAT TIZIMI
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
        await update.message.reply_text(f"🎁 *Daxshatli Omad!* Promokod qabul qilindi. Balansingizga *+{bonus_amount} so'm* tekin pul qo'shildi uka!")
        return
        
    await update.message.reply_text("🎰 Omad shouni daxshatli davom ettirish uchun pastdagi tugmani bosing uka!", 
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

# 🌐 FLASK WEB SERVER (RENDER UCHUN ONLAYN SAQLASH)
app = Flask(__name__)

@app.route('/')
def home():
    return "Mukammal Omad Shou Premium Boti Daxshatli Onlayn!"

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
        
    print("Mukammal Omad Shou Premium boti ishga tushdi...")
    loop.run_until_complete(main_bot())
        
