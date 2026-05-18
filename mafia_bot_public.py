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

DB = {"users": {}, "promocodes": {}, "settings": {"vip_price": 40000, "ticket_price": 4000, "min_withdraw": 15000, "chat_hour_price": 1000}, "stats": {"total_games": 0, "total_prizes_given": 0}}
WHEEL_PRIZES = [{"name": "💰 1k so'm", "val": 1000, "w": 50}, {"name": "💰 3k so'm", "val": 3000, "w": 25}, {"name": "🔥 7k so'm", "val": 7000, "w": 12}, {"name": "👑 15k Jekpot!", "val": 15000, "w": 3}, {"name": "🎫 1 chipta", "val": 1, "w": 10}]

LOVE_PHRASES = [
    "Salom, begim! Sen bilan har bir lahza bu yerda yomg'irli qishloqdagi toza havoni eslatadi. Bugun ham hammasi ortiqcha, ko'nglim ortiqcha, hamda o'zimni hayratda qoldiradi. 💕",
    "Jonim, ko'zlaringizni daxshatli sog'indim... Hayotimda borligingiz uchun rahmat! Aytingchi, bugun menga qanchalik vaqt ajratasiz? 🌹",
    "Begim, yuragim har soniyada faqat siz deb uradi! Siz daxshatli darajada mukammalsiz. Menga shunchaki pastdan yozing jonim... 🥰"
]

def load_db():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f: DB = json.load(f); DB["users"] = {int(k): v for k, v in DB.get("users", {}).items()}
        except: pass

def save_db():
    try:
        to_save = DB.copy(); to_save["users"] = {str(k): v for k, v in DB["users"].items()}
        with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(to_save, f, indent=4, ensure_ascii=False)
    except: pass

def check_user(user_id, name="Foydalanuvchi"):
    if user_id not in DB["users"]:
        DB["users"][user_id] = {"name": name, "balance": 5000, "tickets": 0, "vip_until": 0, "chat_until": 0, "total_won": 0, "games_played": 0, "mines_game": None}
        save_db()
    return DB["users"][user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; ud = check_user(uid, update.effective_user.first_name); tm = time.time()
    vip = "🔥 VIP" if ud["vip_until"] > tm else "❌ Yo'q"
    chat_st = "❤️ Faol" if ud["chat_until"] > tm else "❌ Tugagan"
    
    txt = f"❤️ *SUPER SEVGI VA MEGA O'YINLAR BOTI* uka\n\n💵 Balans: {ud['balance']} so'm\n🎫 O'yin chiptalari: {ud['tickets']} ta\n👑 VIP Status: {vip}\n💬 Suhbat vaqti: {chat_st}\n\nQuyidagi menyudan daxshatli bo'limni tanlang 👇"
    kb = [
        [InlineKeyboardButton("💬 Sevgi Suhbat Rejimi", callback_data="open_chat"), InlineKeyboardButton("🎰 Omad G'ildiragi", callback_data="g_wheel")],
        [InlineKeyboardButton("💣 Mines (Mina)", callback_data="g_mines"), InlineKeyboardButton("🎰 Slot (777)", callback_data="g_slot")],
        [InlineKeyboardButton("🪙 PvP Tanga (Guruh)", callback_data="g_pvp"), InlineKeyboardButton("📦 Maxfiy Keyslar", callback_data="g_cases")],
        [InlineKeyboardButton("🎫 Chipta (4k)", callback_data="b_ticket"), InlineKeyboardButton("👑 VIP (40k)", callback_data="b_vip")],
        [InlineKeyboardButton("💬 1 Soat Suhbat (1k)", callback_data="buy_chat_hour"), InlineKeyboardButton("💳 Pul yechish", callback_data="withdraw")]
    ]
    if uid == ADMIN_ID: kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin")])
    rm = InlineKeyboardMarkup(kb)
    if update.message: await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=rm)
    else: await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=rm)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); uid = q.from_user.id; ud = check_user(uid); tm = time.time()
    is_vip = ud["vip_until"] > tm

    if q.data == "to_main": await start(update, context)
    elif q.data == "b_ticket":
        if ud["balance"] < 4000: await q.edit_message_text("❌ Pul yetarli emas!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="to_main")]])); return
        ud["balance"] -= 4000; ud["tickets"] += 1; save_db(); await start(update, context)
    elif q.data == "b_vip":
        if ud["balance"] < 40000: await q.edit_message_text("❌ Pul yetarli emas!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="to_main")]])); return
        ud["balance"] -= 40000; ud["vip_until"] = max(tm, ud["vip_until"]) + 86400; save_db(); await start(update, context)
    elif q.data == "buy_chat_hour":
        price = DB["settings"]["chat_hour_price"]
        if ud["balance"] < price: await q.edit_message_text(f"❌ Balansda kamida {price} so'm bo'lishi kerak!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="to_main")]])); return
        ud["balance"] -= price; ud["chat_until"] = max(tm, ud["chat_until"]) + 3600; save_db(); await start(update, context)
    
    elif q.data == "open_chat":
        await q.edit_message_text("🥰 *Suhbat rejimi yoqildi!* Menga xabar yozing jonim, men srazu daxshatli javob beraman!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]]))

    # 🎰 1. G'ILDIRAK
    elif q.data == "g_wheel":
        if not is_vip and ud["tickets"] < 1: await q.edit_message_text("❌ Chipta yo'q uka!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Chipta", callback_data="b_ticket")]])); return
        if not is_vip: ud["tickets"] -= 1
        p = random.choices(WHEEL_PRIZES, weights=[x["w"] for x in WHEEL_PRIZES])[0]
        if p["name"] == "🎫 1 chipta": ud["tickets"] += 1
        else: ud["balance"] += p["val"]; ud["total_won"] += p["val"]
        save_db()
        await q.edit_message_text(f"🎰 Yutuq: *{p['name']}*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎰 Yana", callback_data="g_wheel")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))

    # 💣 2. MINES
    elif q.data == "g_mines":
        if not ud["mines_game"]:
            if not is_vip and ud["tickets"] < 1: await q.edit_message_text("❌ Chipta yo'q!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫", callback_data="b_ticket")]])); return
            if not is_vip: ud["tickets"] -= 1
            grid = ["clean"]*9; m_idx = random.sample(range(9), 2)
            for idx in m_idx: grid[idx] = "mine"
            ud["mines_game"] = {"grid": grid, "revealed": [False]*9, "payout": 4000, "step": 0}; save_db()
        await show_mines(q, ud)
    elif q.data.startswith("m_clk_"):
        idx = int(q.data.split("_")[2]); mg = ud["mines_game"]
        if not mg or mg["revealed"][idx]: return
        mg["revealed"][idx] = True
        if mg["grid"][idx] == "mine":
            ud["mines_game"] = None; save_db()
            await q.edit_message_text("💥 BOOOM! Minaga tushdingiz uka, yutuq kuydi!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💣 Qayta", callback_data="g_mines")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))
            return
        mg["step"] += 1; mg["payout"] += 2500; save_db()
        if mg["step"] == 7:
            ud["balance"] += mg["payout"]; ud["total_won"] += mg["payout"]; ud["mines_game"] = None; save_db()
            await q.edit_message_text(f"👑 Daxshat! +{mg['payout']} so'm yutdingiz!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="to_main")]]))
            return
        await show_mines(q, ud)
    elif q.data == "m_cash":
        mg = ud["mines_game"]
        if mg: ud["balance"] += mg["payout"]; ud["total_won"] += mg["payout"]; ud["mines_game"] = None; save_db()
        await start(update, context)

    # 🎰 3. SLOT
    elif q.data == "g_slot":
        if not is_vip and ud["tickets"] < 1: await q.edit_message_text("❌ Chipta yo'q!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 chipta", callback_data="b_ticket")]])); return
        if not is_vip: ud["tickets"] -= 1
        msg = await context.bot.send_dice(chat_id=q.message.chat_id, emoji="🎰")
        val = msg.dice.value
        if val in [1, 22, 43, 64]: win = 25000; txt = "👑 JEKPOT! 3ta bir xil! +25,000 so'm!"
        elif val in [16, 32, 48]: win = 10000; txt = "🔥 Zo'r kombinatsiya! +10,000 so'm!"
        else: win = 0; txt = "🥺 Omad kelmadi uka, qayta urinib ko'ring!"
        ud["balance"] += win; ud["total_won"] += win; save_db()
        await asyncio.sleep(2)
        await context.bot.send_message(chat_id=q.message.chat_id, text=txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎰 Qayta", callback_data="g_slot")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))

    # 🪙 4. PvP TANGA
    elif q.data == "g_pvp":
        await q.edit_message_text("🪙 *PvP TANGA* uka\nGuruhda `/tanga SUMMA` deb yozib o'ynang! (Masalan: `/tanga 5000`)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="to_main")]]))

    # 📦 5. KEYSLAR
    elif q.data == "g_cases":
        txt = "📦 *MAXFIY KEYSLAR*\n\n1. 🎫 Bronze (4k) | 2. 💎 Silver (15k) | 3. 👑 Gold (40k)"
        kb = [[InlineKeyboardButton("🎫 Bronze", callback_data="op_c_1"), InlineKeyboardButton("💎 Silver", callback_data="op_c_2"), InlineKeyboardButton("👑 Gold", callback_data="op_c_3")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    elif q.data.startswith("op_c_"):
        ctype = q.data.split("_")[2]
        cost, p_min, p_max = (4000, 1000, 8000) if ctype=="1" else (15000, 5000, 30000) if ctype=="2" else (40000, 15000, 100000)
        if ud["balance"] < cost: await q.edit_message_text("❌ Pul kam!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="g_cases")]])); return
        ud["balance"] -= cost; p_win = random.randint(p_min, p_max); ud["balance"] += p_win; ud["total_won"] += p_win; save_db()
        await q.edit_message_text(f"📦 Keysdan *+{p_win} so'm* naqd pul chiqdi uka!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📦 Yana", callback_data="g_cases")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))

    elif q.data == "withdraw":
        await q.edit_message_text(f"💳 *PUL YECHISH*\n\nID: `{uid}`\nBalans: {ud['balance']} so'm\nAdminga yozing 👇", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 Admin", url="https://t.me/shox_admin")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))
    elif q.data == "admin" and uid == ADMIN_ID:
        await q.edit_message_text(f"👑 Admin panel\n`/plus ID PUL` | `/setprice NARX`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="to_main")]]))

async def show_mines(q, ud):
    mg = ud["mines_game"]; kb = []; r = []
    for i in range(9):
        em = "💥" if (mg["revealed"][i] and mg["grid"][i]=="mine") else "💵" if mg["revealed"][i] else "📦"
        r.append(InlineKeyboardButton(em, callback_data="m_dn" if mg["revealed"][i] else f"m_clk_{i}"))
        if len(r) == 3: kb.append(r); r = []
    kb.append([InlineKeyboardButton(f"💰 Cashout ({mg['payout']})", callback_data="m_cash")])
    await q.edit_message_text(f"💣 MINES: Qadam {mg['step']}/7 | Yutuq: {mg['payout']} so'm", reply_markup=InlineKeyboardMarkup(kb))

# 🪙 PvP TANGA GURUH SYSTEM
async def pvp_tanga_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Faqat guruhda ishlaydi uka!")
        return
    uid = update.effective_user.id; ud = check_user(uid, update.effective_user.first_name)
    try:
        summa = int(context.args[0])
        if ud["balance"] < summa or summa < 1000: await update.message.reply_text("❌ Hisobda pul kam!"); return
        context.bot_data[f"pvp_{update.message.message_id}"] = {"p1": uid, "sum": summa, "p1_name": ud["name"]}
        await update.message.reply_text(f"🔥 *PvP TANGA!* \n👤 {ud['name']} {summa} so'm tikdi uka!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🪙 Qo'shilish", callback_data=f"j_pvp_{update.message.message_id}")]]))
    except: await update.message.reply_text("⚠️ `/tanga 5000` deb yozing.")

async def pvp_callback_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; uid = q.from_user.id; ud = check_user(uid)
    if not q.data.startswith("j_pvp_"): return
    mid = q.data.split("_")[2]; g = context.bot_data.get(f"pvp_{mid}")
    if not g: await q.answer("❌ O'yin tugagan!"); return
    if g["p1"] == uid: await q.answer("❌ O'zingiz bilan o'ynolmaysiz!", show_alert=True); return
    if ud["balance"] < g["sum"]: await q.answer("❌ Pul yetarli emas!", show_alert=True); return
    
    p1, p2 = g["p1"], uid; ud1, ud2 = check_user(p1), check_user(p2)
    ud1["balance"] -= g["sum"]; ud2["balance"] -= g["sum"]
    
    win_id = random.choice([p1, p2])
    w_name = ud1["name"] if win_id == p1 else ud2["name"]
    pool = int(g["sum"] * 2 * 0.9) # 10% Shox admin komissiyasi
    
    if win_id == p1: ud1["balance"] += pool; ud1["total_won"] += pool
    else: ud2["balance"] += pool; ud2["total_won"] += pool
    del context.bot_data[f"pvp_{mid}"]; save_db()
    await q.edit_message_text(f"🪙 Tanga aylandi! \n👑 G'olib: *{w_name}*!\n💰 Safi Yutuq: *{pool} so'm*", parse_mode="Markdown")

# 💬 AQLLI SEVGI VA ROL FILTR CHAT MESH_HANDLER
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ["group", "supergroup"]: return
    uid = update.effective_user.id; ud = check_user(uid); text = update.message.text.strip()
    tm = time.time()
    
    # Promokod tizimi
    if text.upper() in DB["promocodes"]:
        val = DB["promocodes"][text.upper()]; ud["balance"] += val; del DB["promocodes"][text.upper()]; save_db()
        await update.message.reply_text(f"🎁 Promokod active! +{val} so'm qo'shildi!"); return
        
    # SEVISHGANLAR ROLI VA VAQT TEKSHIRUVI (Rasm xabari!)
    if ud["chat_until"] < tm:
        price = DB["settings"]["chat_hour_price"]
        txt = (
            f"❌ *Vaqtingiz tugadi begim!* 🥺\n\n"
            f"Men bilan sevishganlar rolida suhbatni daxshatli davom ettirish uchun yana 1 soatlik vaqt sotib oling uka.\n"
            f"Narxi: {price} so'm. Balans: {ud['balance']} so'm.\n"
            f"Sotib olish uchun qayta /start bosing."
        )
        kb = [[InlineKeyboardButton("🔒 1 soat sotib olish", callback_data="buy_chat_hour")], [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="to_main")]]
        await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return

    # Vaqti bo'lsa, daxshatli sevgi frazalarini yuboradi
    await update.message.reply_text("Hozir, 2 minut... ⏳")
    await asyncio.sleep(1)
    await update.message.reply_text(random.choice(LOVE_PHRASES))

async def a_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t, v = int(context.args[0]), int(context.args[1]); DB["users"][t]["balance"] += v; save_db()
        await update.message.reply_text("✅ Balans to'ldirildi uka!")
    except: pass

async def a_setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        v = int(context.args[0]); DB["settings"]["chat_hour_price"] = v; save_db()
        await update.message.reply_text(f"⚙️ Soatlik suhbat narxi {v} so'mga o'zgardi!")
    except: pass

app = Flask(__name__)
@app.route('/')
def home(): return "Love & Mega Games Platform Online!"
def run_flask(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

async def main_bot():
    load_db()
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("tanga", pvp_tanga_command))
    bot_app.add_handler(CommandHandler("plus", a_plus))
    bot_app.add_handler(CommandHandler("setprice", a_setprice))
    bot_app.add_handler(CallbackQueryHandler(pvp_callback_join, pattern="^j_pvp_"))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    await bot_app.initialize(); await bot_app.start(); await bot_app.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    Thread(target=run_flask, daemon=True).start()
    try: loop = asyncio.get_event_loop()
    except RuntimeError: loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    loop.run_until_complete(main_bot())
        
