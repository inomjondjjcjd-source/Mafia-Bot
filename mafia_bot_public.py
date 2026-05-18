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
DATA_FILE = "mega_games_bot_db.json"

# 📊 GLOBAL BAZA TIZIMI
DB = {
    "users": {},
    "promocodes": {},
    "settings": {
        "vip_price": 40000,       # 💰 Kunlik VIP obuna narxi = 40,000 so'm
        "ticket_price": 4000,     # 🎫 1 ta o'yin chiptasi narxi = 4,000 so'm
        "min_withdraw": 15000     # 💳 Minimal pul yechish miqdori
    },
    "stats": {
        "total_games": 0,
        "total_prizes_given": 0
    }
}

# 🎰 G'ILDIRAK MUKOFOTLARI (ENG KAMI 1,000 SO'M)
WHEEL_PRIZES = [
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
            "balance": 5000,         # 🎁 5,000 so'm start bonus!
            "tickets": 0,            # ❌ Boshida tekin chipta yo'q
            "vip_until": 0,
            "total_won": 0,
            "games_played": 0,
            "mines_game": None       # 💣 Aktiv mina o'yini holati
        }
        save_db()
    return DB["users"][user_id]

def spin_wheel():
    prizes_list = []
    for p in WHEEL_PRIZES:
        prizes_list.extend([p] * p["weight"])
    return random.choice(prizes_list)

# 👋 ASOSIY BOSH MENYU
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    ud = check_user(user_id, name)
    current_time = time.time()
    
    is_vip = ud["vip_until"] > current_time
    vip_status = "🔥 FAOL (Cheksiz kirish)" if is_vip else "❌ Faol emas"
    
    txt = (
        f"🎮 *SHOX CASINO & MEGA-GAMES PLATFORMASI* uka\n\n"
        f"O'zingizga yoqqan daxshatli pullik o'yinni tanlang va srazu daromadni boshlang! 🚀\n\n"
        f"💵 *Sizning balansingiz:* {ud['balance']} so'm\n"
        f"🎫 *O'yin chiptalaringiz:* {ud['tickets']} ta\n"
        f"👑 *VIP status:* {vip_status}\n"
    )
    
    buttons = [
        [InlineKeyboardButton("🎰 1-O'yin: Omad G'ildiragi", callback_data="game_wheel"),
         InlineKeyboardButton("💣 2-O'yin: Mina Qidiruvchi", callback_data="game_mines")],
        [InlineKeyboardButton("👑 VIP yoqish (40k)", callback_data="buy_vip"), 
         InlineKeyboardButton("🎫 Chipta sotib olish (4k)", callback_data="buy_ticket")],
        [InlineKeyboardButton("💳 Pul yechish (Lichka)", callback_data="withdraw"),
         InlineKeyboardButton("🎁 Promokod", callback_data="use_promo")],
        [InlineKeyboardButton("📊 Statistika", callback_data="my_stats")]
    ]
    
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("👑 SHOX Boshqaruv Paneli", callback_data="admin_panel")])
        
    reply_markup = InlineKeyboardMarkup(buttons)
    if update.message:
        await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=reply_markup)

# 🎛 INLINE DIRECT CONTROL PANEL
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = check_user(user_id)
    current_time = time.time()
    
    if query.data == "to_main":
        await start(update, context)

    # 🎫 CHIPTA SOTIB OLISH (4,000 SO'M)
    elif query.data == "buy_ticket":
        if ud["balance"] < DB["settings"]["ticket_price"]:
            await query.edit_message_text(f"❌ Balansda etarli mablag' yo'q uka. Narxi: {DB['settings']['ticket_price']} so'm. Balans: {ud['balance']} so'm.",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))
            return
        ud["balance"] -= DB["settings"]["ticket_price"]
        ud["tickets"] += 1
        save_db()
        await query.edit_message_text("✅ 1 ta o'yin chiptasi sotib olindi uka!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]]))

    # 👑 VIP OBUNA SOTIB OLISH (40,000 SO'M)
    elif query.data == "buy_vip":
        if ud["balance"] < DB["settings"]["vip_price"]:
            await query.edit_message_text(f"❌ VIP obuna narxi {DB['settings']['vip_price']} so'm. Balans: {ud['balance']} so'm.",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))
            return
        ud["balance"] -= DB["settings"]["vip_price"]
        ud["vip_until"] = max(current_time, ud["vip_until"]) + 86400
        save_db()
        await query.edit_message_text("🔥 Daxshat! 24 soatlik cheksiz VIP yoqildi. Endi o'yinlarga tekinga kirasiz!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ O'yinlarga kirish", callback_data="to_main")]]))

    # 🎰 1-O'YIN: OMAD G'ILDRAK MENYUSI
    elif query.data == "game_wheel":
        txt = f"🎰 *OMAD G'ILDIRAGI TIZIMI*\n\nHar bir aylantirish 1 ta chipta (4,000 so'm) yoki VIP talab qiladi. Eng kam yutuq: 1,000 so'm!\n\n🎫 Chiptalaringiz: {ud['tickets']} ta"
        kb = [
            [InlineKeyboardButton("🔄 G'ildirakni Aylantirish", callback_data="spin_wheel_action")],
            [InlineKeyboardButton("⬅️ Bosh menyuga qaytish", callback_data="to_main")]
        ]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "spin_wheel_action":
        is_vip = ud["vip_until"] > current_time
        if not is_vip and ud["tickets"] < 1:
            await query.edit_message_text("❌ O'yin chiptangiz qolmagan uka! Chipta xarid qiling.", 
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Chipta olish (4k)", callback_data="buy_ticket")], [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))
            return
        if not is_vip: ud["tickets"] -= 1
        
        await query.edit_message_text("🔄 *G'ildirak daxshatli aylanyapti...*")
        await asyncio.sleep(0.6)
        
        prize = spin_wheel()
        result = f"🎰 *NATIJA!* 🎉\n\nSizga omad kuldi:\n* {prize['name']} *\n\n"
        if prize["type"] == "balance":
            ud["balance"] += prize["value"]
            ud["total_won"] += prize["value"]
            result += f"💵 *+{prize['value']} so'm* balansingizga urildi!"
        elif prize["type"] == "ticket":
            ud["tickets"] += prize["value"]
            result += "🎫 +1 ta chipta berildi!"
        else:
            result += "🥺 Bu safar pul chiqmadi, keyingi safar daxshatli yutasiz uka!"
            
        ud["games_played"] += 1
        DB["stats"]["total_games"] += 1
        save_db()
        kb = [[InlineKeyboardButton("🎰 Qayta aylantirish", callback_data="spin_wheel_action")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # 💣 2-O'YIN: MINA QIDIRUVCHI (MINES) TIZIMI
    elif query.data == "game_mines":
        if not ud["mines_game"]:
            txt = (
                f"💣 *MINA QIDIRUVCHI (MINES 3x3)*\n\n"
                f"Maydonda 9 ta katakcha bor. Ulardan 2 tasiga daxshatli mina (bomba) yashirilgan! 💥\n"
                f"Har bir katakchani ochganingizda yutuq summasi daxshatli ko'payib boradi.\n\n"
                f"⚠️ *Shart:* O'yinni boshlash 1 ta chipta (4,000 so'm) yoki VIP talab qiladi!\n"
                f"Xohlagan vaqtda pulni yechib olishingiz mumkin. Minaga tushsangiz, hamma yutuq kuyadi!"
            )
            kb = [
                [InlineKeyboardButton("💣 O'yinni Boshlash (1 chipta / VIP)", callback_data="start_mines")],
                [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]
            ]
            await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await show_mines_grid(query, ud)

    elif query.data == "start_mines":
        is_vip = ud["vip_until"] > current_time
        if not is_vip and ud["tickets"] < 1:
            await query.edit_message_text("❌ O'yin chiptangiz yo'q uka!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Chipta olish (4k)", callback_data="buy_ticket")]]))
            return
        if not is_vip: ud["tickets"] -= 1
        
        grid = ["clean"] * 9
        mina_indexes = random.sample(range(9), 2)
        for idx in mina_indexes:
            grid[idx] = "mine"
            
        ud["mines_game"] = {
            "grid": grid,
            "revealed": [False] * 9,
            "current_bet": 4000,
            "current_payout": 4000,
            "step": 0
        }
        save_db()
        await show_mines_grid(query, ud)

    elif query.data.startswith("mine_click_"):
        idx = int(query.data.split("_")[2])
        mg = ud["mines_game"]
        
        if not mg or mg["revealed"][idx]: return
        
        mg["revealed"][idx] = True
        
        if mg["grid"][idx] == "mine":
            await query.edit_message_text(f"💥 *BOOOM! Minaga tushdingiz uka!* 💥\n\nHamma yig'ilgan yutuqlaringiz yonib ketdi. Xavotir olmang, keyingi safar daxshatli ehtiyotkor bo'lasiz!", parse_mode="Markdown",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💣 Qayta o'ynash", callback_data="start_mines")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))
            ud["mines_game"] = None
            ud["games_played"] += 1
            DB["stats"]["total_games"] += 1
            save_db()
            return
            
        mg["step"] += 1
        mg["current_payout"] += 2500 
        save_db()
        
        if mg["step"] == 7:
            win_amount = mg["current_payout"]
            ud["balance"] += win_amount
            ud["total_won"] += win_amount
            DB["stats"]["total_prizes_given"] += win_amount
            ud["mines_game"] = None
            ud["games_played"] += 1
            DB["stats"]["total_games"] += 1
            save_db()
            await query.edit_message_text(f"👑 *DAXSHATLI G'ALABA!* uka\n\nSiz maydondagi barcha toza kataklarni topdingiz va *+{win_amount} so'm* yutib oldingiz!", parse_mode="Markdown",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]]))
            return
            
        await show_mines_grid(query, ud)

    elif query.data == "mines_cashout":
        mg = ud["mines_game"]
        if not mg: return
        win_amount = mg["current_payout"]
        ud["balance"] += win_amount
        ud["total_won"] += win_amount
        DB["stats"]["total_prizes_given"] += win_amount
        ud["mines_game"] = None
        ud["games_played"] += 1
        DB["stats"]["total_games"] += 1
        save_db()
        await query.edit_message_text(f"💰 *Aqlli qaror uka!* Pul muvaffaqiyatli yechildi.\nBalansingizga *+{win_amount} so'm* qo'shildi!", parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💣 Yana o'ynash", callback_data="start_mines")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))

    # 💳 PUL YECHISH (TO'G'RIDAN-TO'G'RI LICHKANGIZGA)
    elif query.data == "withdraw":
        if ud["balance"] < DB["settings"]["min_withdraw"]:
            await query.edit_message_text(f"❌ Minimal pul yechish miqdori: *{DB['settings']['min_withdraw']} so'm*.\nBalansingiz: {ud['balance']} so'm.",
                                          parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))
        else:
            txt = (
                f"💳 *PUL YECHISH TIZIMI MUKAMMAL*\n\nSizning balansingiz: *{ud['balance']} so'm*\nSizning shaxsiy ID kodingiz: `{user_id}`\n\n"
                f"⚠️ Pulni daxshatli tez yechib olish uchun pastdagi tugma orqali adminga ID kodingizni yuboring, u srazu tushirib beradi uka!"
            )
            kb = [[InlineKeyboardButton("👑 Admin Lichkasi (Shox)", url="https://t.me/shox_admin")], [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]
            await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "use_promo":
        await query.edit_message_text("🎁 *Promokod:* Admin bergan kodni chatga yozib yuboring (Masalan: `OMAD2026`).", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))

    elif query.data == "my_stats":
        txt = f"📊 *Statistikangiz uka:*\n\n🏆 Jami yutilgan pul: *{ud['total_won']} so'm*\n🕹 O'ynalgan o'yinlar: {ud['games_played']} marta\n🎫 Chiptalar: {ud['tickets']} ta\n🆔 ID: `{user_id}`"
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))

    # 👑 ADMIN PANEL
    elif query.data == "admin_panel" and user_id == ADMIN_ID:
        txt = (
            f"👑 *SHOX MEGA-BOT ADMIN PANEL*\n\n👥 Ro'yxatdan o'tganlar: *{len(DB['users'])} ta*\n🎰 Jami o'yinlar: *{DB['stats']['total_games']} marta*\n💰 Jami tarqatilgan summalar: *{DB['stats']['total_prizes_given']} so'm*\n\n"
            f"⚙️ *Buyruqlar:*\n🔹 `/plus ID PUL` | `/minus ID PUL` | `/give_ticket ID SONI` | `/genprom PUL` | `/setprice NARX`"
        )
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]]))

# 💣 MINES GRID GENERATOR
async def show_mines_grid(query, ud):
    mg = ud["mines_game"]
    buttons = []
    row = []
    
    for i in range(9):
        if mg["revealed"][i]:
            emoji = "💥" if mg["grid"][i] == "mine" else "💵"
            row.append(InlineKeyboardButton(emoji, callback_data="mine_already_done"))
        else:
            row.append(InlineKeyboardButton("📦", callback_data=f"mine_click_{i}"))
            
        if len(row) == 3:
            buttons.append(row)
            row = []
            
    buttons.append([InlineKeyboardButton(f"💰 Pulni yechib olish ({mg['current_payout']} so'm)", callback_data="mines_cashout")])
    buttons.append([InlineKeyboardButton("⬅️ Taslim bo'lish (Chiqish)", callback_data="to_main")])
    
    txt = (
        f"💣 *MINA QIDIRUVCHI (MINES)*\n\n"
        f"Qadam: *{mg['step']} / 7*\n"
        f"💵 Hozir yechib olsangiz naqd: *{mg['current_payout']} so'm* yutasiz!\n"
        f"Keyingi toza katak uchun mukofot yanada daxshatli ko'payadi! Omad uka!"
    )
    await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# 💬 FOYDALANUVCHI PROMOKOD YOZGANDA
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
        await update.message.reply_text(f"🎁 *Daxshatli Omad!* Promokod qabul qilindi. Balansingizga *+{bonus_amount} so'm* urildi uka!")
        return
        
    await update.message.reply_text("🎮 O'yinlarni boshlash uchun pastdagi tugmani bosing uka!", 
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Mega-Menyuni ochish", callback_data="to_main")]]))

# 👑 ADMIN BUYRUQLARI
async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id, val = int(context.args[0]), int(context.args[1])
        if t_id in DB["users"]:
            DB["users"][t_id]["balance"] += val
            save_db()
            await update.message.reply_text(f"✅ `ID: {t_id}` balansiga *{val} so'm* qo'shildi uka!")
    except: pass

async def admin_minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id, val = int(context.args[0]), int(context.args[1])
        if t_id in DB["users"]:
            DB["users"][t_id]["balance"] = max(0, DB["users"][t_id]["balance"] - val)
            save_db()
            await update.message.reply_text(f"📉 `ID: {t_id}` hisobidan *{val} so'm* ayrildi.")
    except: pass

async def admin_give_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id, count = int(context.args[0]), int(context.args[1])
        if t_id in DB["users"]:
            DB["users"][t_id]["tickets"] += count
            save_db()
            await update.message.reply_text(f"🎫 `ID: {t_id}` profiliga *{count} ta* chipta berildi!")
    except: pass

async def admin_setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        val = int(context.args[0])
        DB["settings"]["vip_price"] = val
        save_db()
        await update.message.reply_text(f"⚙️ VIP obuna narxi yangilandi: *{val} so'm*")
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

# 🌐 FLASK WEB SERVER (RENDER)
app = Flask(__name__)
@app.route('/')
def home(): return "Mega Games Multi-System Platform Bot Onlayn!"

def run_flask():
    port = int(os.environ.get("PORT", 10000)
