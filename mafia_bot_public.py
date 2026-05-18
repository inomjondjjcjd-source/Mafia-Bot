import os, sys, subprocess, json, asyncio, time, random, string
from flask import Flask
from threading import Thread

try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = "8303235336:AAEk3J42idbz1KcamIWPC2L3_IlROPeoadI"
ADMIN_ID = 8086545587  
DATA_FILE = "mega_games_bot_db.json"

DB = {
    "users": {}, 
    "promocodes": {}, 
    "settings": {"ticket_price": 4000, "min_withdraw": 15000}, 
    "stats": {"total_games": 0, "total_prizes_given": 0}
}

def load_db():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f: 
                DB = json.load(f)
                DB["users"] = {int(k): v for k, v in DB.get("users", {}).items()}
                if "promocodes" not in DB: DB["promocodes"] = {}
                if "stats" not in DB: DB["stats"] = {"total_games": 0, "total_prizes_given": 0}
        except: pass

def save_db():
    try:
        to_save = DB.copy()
        to_save["users"] = {str(k): v for k, v in DB["users"].items()}
        with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(to_save, f, indent=4, ensure_ascii=False)
    except: pass

def check_user(user_id, name="Foydalanuvchi"):
    if user_id not in DB["users"]:
        DB["users"][user_id] = {
            "name": name, 
            "balance": 5000, 
            "tickets": 0, 
            "total_won": 0, 
            "games_played": 0, 
            "mines_game": None
        }
        save_db()
    return DB["users"][user_id]

# 🎮 ASOSIY BOSH MENYU (BELGILANGANLAR QOLDI)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ud = check_user(uid, update.effective_user.first_name)
    
    txt = (
        f"🔥 *SHOX SUPREME PLATFORMA* uka\n\n"
        f"💵 *Balansingiz:* {ud['balance']} so'm\n"
        f"🎫 *O'yin chiptalari:* {ud['tickets']} ta\n\n"
        f"Faqat eng daxshatli va mukammal bo'limlar 👇"
    )
    
    kb = [
        [InlineKeyboardButton("💣 Mines (Mina)", callback_data="g_mines"),
         InlineKeyboardButton("📦 Maxfiy Keyslar", callback_data="g_cases")],
        [InlineKeyboardButton("🎫 Chipta Xarid Qilish (4k)", callback_data="b_ticket")],
    ]
    
    if uid == ADMIN_ID: 
        kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_dashboard")])
        
    rm = InlineKeyboardMarkup(kb)
    if update.message: 
        await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=rm)
    else: 
        await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=rm)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); uid = q.from_user.id; ud = check_user(uid)

    if q.data == "to_main": 
        await start(update, context)
        
    # 🎫 CHIPTA SOTIB OLISH (4,000 SO'M)
    elif q.data == "b_ticket":
        if ud["balance"] < 4000: 
            await q.edit_message_text("❌ Balansda pul yetarli emas uka!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))
            return
        ud["balance"] -= 4000
        ud["tickets"] += 1
        save_db()
        await start(update, context)
    
    # 💣 1. MINES (MINA) O'YINI MUKAMMAL HOLATDA
    elif q.data == "g_mines":
        if not ud["mines_game"]:
            if ud["tickets"] < 1: 
                await q.edit_message_text("❌ O'yinni boshlash uchun chiptangiz yo'q uka! Chipta sotib oling.", 
                                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Chipta olish", callback_data="b_ticket")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))
                return
            ud["tickets"] -= 1
            grid = ["clean"] * 9
            m_idx = random.sample(range(9), 2)  # 2 ta daxshatli mina
            for idx in m_idx: grid[idx] = "mine"
            ud["mines_game"] = {"grid": grid, "revealed": [False] * 9, "payout": 4000, "step": 0}
            save_db()
        await show_mines(q, ud)
        
    elif q.data.startswith("m_clk_"):
        idx = int(q.data.split("_")[2])
        mg = ud["mines_game"]
        if not mg or mg["revealed"][idx]: return
        
        mg["revealed"][idx] = True
        if mg["grid"][idx] == "mine":
            ud["mines_game"] = None
            ud["games_played"] += 1
            DB["stats"]["total_games"] += 1
            save_db()
            await q.edit_message_text("💥 *BOOOM! Daxshatli minaga portladingiz!* 💥\nHamma yig'ilgan summalar yonib ketdi. Keyingi safar omad keladi uka!", parse_mode="Markdown",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💣 Qayta o'ynash", callback_data="g_mines")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))
            return
            
        mg["step"] += 1
        mg["payout"] = int(mg["payout"] * 1.6)  # Koeffitsiyent daxshatli o'sadi
        save_db()
        
        if mg["step"] == 7:  # Jami 7 ta toza katak bor
            win_amt = mg["payout"]
            ud["balance"] += win_amt
            ud["total_won"] += win_amt
            DB["stats"]["total_prizes_given"] += win_amt
            ud["mines_game"] = None
            ud["games_played"] += 1
            DB["stats"]["total_games"] += 1
            save_db()
            await q.edit_message_text(f"👑 *DAXSHATLI G'ALABA!* 👑\n\nMeydondagi hamma toza kataklarni topdingiz va *+{win_amt} so'm* yutdingiz!", parse_mode="Markdown",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]]))
            return
        await show_mines(q, ud)
        
    elif q.data == "m_cash":
        mg = ud["mines_game"]
        if mg: 
            win_amt = mg["payout"]
            ud["balance"] += win_amt
            ud["total_won"] += win_amt
            DB["stats"]["total_prizes_given"] += win_amt
            ud["mines_game"] = None
            ud["games_played"] += 1
            DB["stats"]["total_games"] += 1
            save_db()
            await q.edit_message_text(f"💰 *Aqlli naqd pul yechish!* \n\nBalansingizga *+{win_amt} so'm* qo'shildi uka!", parse_mode="Markdown",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💣 Yana o'ynash", callback_data="g_mines")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))

    # 📦 2. MAXFIY KEYSLAR MUKAMMAL TIZIM
    elif q.data == "g_cases":
        txt = (
            "📦 *FANTASY MAXFIY KEYSLAR TIZIMI*\n\n"
            "Omadingizni daxshatli keyslarda sinab ko'ring, har bir keys ichidan srazu naqd pul chiqadi uka!\n\n"
            "1. 🎫 *BRONZE KEYS* — Narxi: 4,000 so'm (Yutuq: 1,000 - 9,000 so'm)\n"
            "2. 💎 *SILVER KEYS* — Narxi: 15,000 so'm (Yutuq: 5,000 - 35,000 so'm)\n"
            "3. 👑 *GOLD SUPREME* — Narxi: 40,000 so'm (Yutuq: 15,000 - 120,000 so'm)"
        )
        kb = [
            [InlineKeyboardButton("🎫 Bronze", callback_data="op_case_1"), 
             InlineKeyboardButton("💎 Silver", callback_data="op_case_2"), 
             InlineKeyboardButton("👑 Gold", callback_data="op_case_3")],
            [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]
        ]
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        
    elif q.data.startswith("op_case_"):
        ctype = q.data.split("_")[2]
        cost, p_min, p_max = (4000, 1000, 9000) if ctype == "1" else (15000, 5000, 35000) if ctype == "2" else (40000, 15000, 120000)
        
        if ud["balance"] < cost: 
            await q.edit_message_text("❌ Balansda mablag' yetarli emas uka!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Keyslarga", callback_data="g_cases")]]))
            return
            
        ud["balance"] -= cost
        p_win = random.randint(p_min, p_max)
        ud["balance"] += p_win
        ud["total_won"] += p_win
        DB["stats"]["total_prizes_given"] += p_win
        save_db()
        
        await q.edit_message_text(f"📦 Keys daxshatli ochildi! \n\nIchidan daxshatli *+{p_win} so'm* naqd pul chiqdi uka! 🎉", parse_mode="Markdown", 
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📦 Yana ochish", callback_data="g_cases")], [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]]))

    # 👑 3. ADMIN PANEL - DAXSHATLI FANTAZIYALAR BILAN YANGILANDI
    elif q.data == "admin_dashboard" and uid == ADMIN_ID:
        total_balance = sum(u.get("balance", 0) for u in DB["users"].values())
        txt = (
            f"👑 *SHOX SUPREME BOSS PANEL v3.0* 👑\n\n"
            f"👤 Jami a'zolar: *{len(DB['users'])} ta*\n"
            f"🕹 Jami o'ynalgan o'yinlar: *{DB['stats']['total_games']} marta*\n"
            f"💰 Umumiy tarqatilgan pullar: *{DB['stats']['total_prizes_given']} so'm*\n"
            f"💳 Botdagi jami pullar aylanmasi: *{total_balance} so'm*\n\n"
            f"⚙️ *Boss super-fanta buyruqlari:*\n"
            f"🔹 `/plus ID PUL` — Kimningdir balansiga naqd pul urish\n"
            f"🔹 `/minus ID PUL` — Kimgadir jarima solib pulini ayirish\n"
            f"🔹 `/give_ticket ID SONI` — Tekin chiptalar berish\n"
            f"🔹 `/create_promo PUL` — Universal promokod yaratish"
        )
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main")]]))

async def show_mines(q, ud):
    mg = ud["mines_game"]
    kb = []; r = []
    for i in range(9):
        if mg["revealed"][i]:
            em = "💥" if mg["grid"][i] == "mine" else "💵"
            r.append(InlineKeyboardButton(em, callback_data="m_done"))
        else:
            r.append(InlineKeyboardButton("📦", callback_data=f"m_clk_{i}"))
        if len(r) == 3: 
            kb.append(r); r = []
            
    kb.append([InlineKeyboardButton(f"💰 Naqd Cashout ({mg['payout']} so'm)", callback_data="m_cash")])
    kb.append([InlineKeyboardButton("⬅️ Taslim bo'lish (Chiqish)", callback_data="to_main")])
    
    txt = (
        f"💣 *MINES MULTI-TIZIMI* 💣\n\n"
        f"Muvaffaqiyatli qadam: *{mg['step']} / 7*\n"
        f"💵 Hozir to'xtatsangiz yutuq: *{mg['payout']} so'm*\n\n"
        f"Keyingi katak yutug'i yanada daxshatli ko'payadi! Diqqat qiling uka!"
    )
    await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# 💬 FOYDALANUVCHIDAN PROMOKOD QABUL QILISH
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ud = check_user(uid)
    text = update.message.text.strip().upper()
    
    if text in DB["promocodes"]:
        val = DB["promocodes"][text]
        ud["balance"] += val
        del DB["promocodes"][text]
        save_db()
        await update.message.reply_text(f"🎁 *Daxshatli Fantaziya Omad!* Promokod qabul bo'ldi. Balansga *+{val} so'm* qo'shildi uka!")
        return
        
    await update.message.reply_text("🤖 O'yinlarni daxshatli o'ynash uchun pastdagi /start buyrug'ini bosing uka!")

# 👑 ADMIN BUYRUQLARI TIZIMI
async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id, val = int(context.args[0]), int(context.args[1])
        if t_id in DB["users"]:
            DB["users"][t_id]["balance"] += val
            save_db()
            await update.message.reply_text(f"✅ `ID: {t_id}` balansiga *{val} so'm* daxshatli qo'shildi!")
    except: pass

async def admin_minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id, val = int(context.args[0]), int(context.args[1])
        if t_id in DB["users"]:
            DB["users"][t_id]["balance"] = max(0, DB["users"][t_id]["balance"] - val)
            save_db()
            await update.message.reply_text(f"📉 `ID: {t_id}` hisobidan *{val} so'm* chegirib tashlandi.")
    except: pass

async def admin_give_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id, count = int(context.args[0]), int(context.args[1])
        if t_id in DB["users"]:
            DB["users"][t_id]["tickets"] += count
            save_db()
            await update.message.reply_text(f"🎫 `ID: {t_id}` profiliga *{count} ta* tekin chipta sovg'a qilindi!")
    except: pass

async def admin_create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        val = int(context.args[0])
        code = "SHOX-" + "".join(random.choices(string.digits, k=5))
        DB["promocodes"][code] = val
        save_db()
        await update.message.reply_text(f"🎁 *Yangi Fantastik Promokod yaratildi:* `{code}`\n💰 Qiymati: *{val} so'm*")
    except: pass

# 🌐 FLASK SERVER FOR RENDER
app = Flask(__name__)
@app.route('/')
def home(): return "Supreme Multi Games Bot Platform Online!"

def run_flask(): 
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

async def main_bot():
    load_db()
    bot_app = Application.builder().token(TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("plus", admin_plus))
    bot_app.add_handler(CommandHandler("minus", admin_minus))
    bot_app.add_handler(CommandHandler("give_ticket", admin_give_ticket))
    bot_app.add_handler(CommandHandler("create_promo", admin_create_promo))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    await bot_app.initialize(); await bot_app.start(); await bot_app.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    Thread(target=run_flask, daemon=True).start()
    try: loop = asyncio.get_event_loop()
    except RuntimeError: loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    print("Bot daxshatli darajada tozalangan holda ishga tushdi...")
    loop.run_until_complete(main_bot())
            
