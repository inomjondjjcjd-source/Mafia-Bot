import os, json, random, asyncio
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8303235336:AAEk3J42idbz1KcamIWPC2L3_IlROPeoadI"
ADMIN_ID = 8086545587  
DATA_FILE = "mega_games_bot_db.json"

DB = {"users": {}, "settings": {"next_aviator": None, "cheaters": []}}
COEFFS = [1.23, 1.54, 1.93, 2.41, 3.02, 4.02, 5.70, 8.55, 13.43, 69.48]

def load_db():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                DB = json.load(f); DB["users"] = {int(k): v for k, v in DB.get("users", {}).items()}
                if "cheaters" not in DB["settings"]: DB["settings"]["cheaters"] = []
        except: pass

def save_db():
    try:
        to_save = DB.copy(); to_save["users"] = {str(k): v for k, v in DB["users"].items()}
        with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(to_save, f, indent=4, ensure_ascii=False)
    except: pass

def check_user(uid, name="Foydalanuvchi"):
    load_db()
    if uid not in DB["users"]:
        DB["users"][uid] = {"name": name, "balance": 10000, "tickets": 5, "mines": None, "apple": None, "chicken": None, "aviator": None}
        save_db()
    return DB["users"][uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; ud = check_user(uid, update.effective_user.first_name)
    txt = f"👑 *SHOX SUPREME PLATFORMA*\n\n💵 *Balans:* {ud['balance']} so'm\n🎫 *Chiptalar:* {ud['tickets']} ta"
    kb = [
        [InlineKeyboardButton("🍏 Apple of Fortune", callback_data="g_apple"), InlineKeyboardButton("💣 Mines (Mina)", callback_data="g_mines")],
        [InlineKeyboardButton("🐥 Chicken Road", callback_data="g_chicken"), InlineKeyboardButton("✈️ Aviator", callback_data="g_aviator")],
        [InlineKeyboardButton("🎫 1 Chipta (4k)", callback_data="b_1"), InlineKeyboardButton("🎁 10 Chipta (30k)", callback_data="b_10")],
        [InlineKeyboardButton("👑 Admin Panel", callback_data="admin_dash")] if uid == ADMIN_ID else []
    ]
    kb = [x for x in kb if x]
    if update.message: await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    else: await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); uid = q.from_user.id; ud = check_user(uid)
    is_cheat = (uid == ADMIN_ID or uid in DB["settings"].get("cheaters", []))

    if q.data == "to_main": await start(update, context)
    elif q.data == "b_1" and ud["balance"] >= 4000: ud["balance"] -= 4000; ud["tickets"] += 1; save_db(); await start(update, context)
    elif q.data == "b_10" and ud["balance"] >= 30000: ud["balance"] -= 30000; ud["tickets"] += 10; save_db(); await start(update, context)

    # 🍏 APPLE OF FORTUNE
    elif q.data == "g_apple":
        if not ud["apple"]:
            if ud["balance"] < 3000: return
            ud["balance"] -= 3000; grid = []
            for r in range(10):
                row = ["good"] * 5; row[random.randint(0, 4)] = "bad"
                grid.append(row)
            ud["apple"] = {"grid": grid, "row": 0, "payout": 3000}; save_db()
        await show_apple(q, ud, is_cheat)
    elif q.data.startswith("ap_s_"):
        idx = int(q.data.split("_")[2]); ag = ud["apple"]
        if not ag or ag["grid"][ag["row"]][idx] == "bad":
            ud["apple"] = None; save_db()
            await q.edit_message_text("💀 Chirigan olma! Yutqazdingiz.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🍏 Qayta", callback_data="g_apple")],[InlineKeyboardButton("⬅️", callback_data="to_main")]])); return
        ag["payout"] = int(3000 * COEFFS[ag["row"]]); ag["row"] += 1; save_db()
        if ag["row"] == 10: ud["balance"] += ag["payout"]; ud["apple"] = None; save_db(); await start(update, context); return
        await show_apple(q, ud, is_cheat)
    elif q.data == "ap_cash" and ud["apple"]:
        ud["balance"] += ud["apple"]["payout"]; ud["apple"] = None; save_db(); await start(update, context)

    # 💣 MINES
    elif q.data == "g_mines":
        if not ud["mines"]:
            if ud["tickets"] < 1: return
            ud["tickets"] -= 1; grid = ["clean"] * 9
            for i in random.sample(range(9), 2): grid[i] = "mine"
            ud["mines"] = {"grid": grid, "rev": [False] * 9, "pay": 4000, "step": 0}; save_db()
        await show_mines(q, ud, is_cheat)
    elif q.data.startswith("m_c_"):
        idx = int(q.data.split("_")[2]); mg = ud["mines"]
        if not mg or mg["rev"][idx]: return
        mg["rev"][idx] = True
        if mg["grid"][idx] == "mine":
            ud["mines"] = None; save_db()
            await q.edit_message_text("💥 BOMBA! Portladingiz.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💣 Qayta", callback_data="g_mines")],[InlineKeyboardButton("⬅️", callback_data="to_main")]])); return
        mg["step"] += 1; mg["pay"] = int(mg["pay"] * 1.5); save_db()
        if mg["step"] == 7: ud["balance"] += mg["pay"]; ud["mines"] = None; save_db(); await q.edit_message_text(f"👑 G'ALABA! +{mg['pay']} so'm", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="to_main")]])); return
        await show_mines(q, ud, is_cheat)
    elif q.data == "m_cash" and ud["mines"]:
        ud["balance"] += ud["mines"]["pay"]; ud["mines"] = None; save_db(); await start(update, context)

    # 🐥 CHICKEN ROAD
    elif q.data == "g_chicken":
        if not ud["chicken"]:
            if ud["balance"] < 4000: return
            ud["balance"] -= 4000; grid = []
            for r in range(5):
                row = ["coin", "coin", "coin"]; row[random.randint(0, 2)] = "bone"
                grid.append(row)
            ud["chicken"] = {"grid": grid, "row": 0, "pay": 4000}; save_db()
        await show_chicken(q, ud, is_cheat)
    elif q.data.startswith("ch_s_"):
        idx = int(q.data.split("_")[2]); cg = ud["chicken"]
        if not cg or cg["grid"][cg["row"]][idx] == "bone":
            ud["chicken"] = None; save_db()
            await q.edit_message_text("☠️ Suyakka duch keldingiz! Tovuq o'ldi.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🐥 Qayta", callback_data="g_chicken")],[InlineKeyboardButton("⬅️", callback_data="to_main")]])); return
        cg["pay"] = int(cg["pay"] * 1.8); cg["row"] += 1; save_db()
        if cg["row"] == 5: ud["balance"] += cg["pay"]; ud["chicken"] = None; save_db(); await start(update, context); return
        await show_chicken(q, ud, is_cheat)
    elif q.data == "ch_cash" and ud["chicken"]:
        ud["balance"] += ud["chicken"]["pay"]; ud["chicken"] = None; save_db(); await start(update, context)

    # ✈️ AVIATOR
    elif q.data == "g_aviator":
        if ud["balance"] < 2000: return
        crash = DB["settings"].get("next_aviator") or round(random.uniform(1.3, 4.5), 2)
        win_p = round(random.uniform(1.1, max(1.2, crash - 0.1)), 2)
        ud["balance"] -= 2000; ud["aviator"] = {"win": win_p, "crash": crash, "bet": 2000}; save_db()
        txt = f"✈️ *AVIATOR PLATFORMA*\n\n📈 Joriy Koeffitsiyent: *x{win_p}*\n(Portlash: x{crash})"
        kb = [[InlineKeyboardButton(f"🛑 CASHOUT (x{win_p})", callback_data="av_cash")], [InlineKeyboardButton("🚀 Kutish", callback_data="av_risk")]]
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data == "av_cash" and ud["aviator"]:
        ud["balance"] += int(ud["aviator"]["bet"] * ud["aviator"]["win"]); ud["aviator"] = None; DB["settings"]["next_aviator"] = None; save_db(); await start(update, context)
    elif q.data == "av_risk" and ud["aviator"]:
        c = ud["aviator"]["crash"]; ud["aviator"] = None; DB["settings"]["next_aviator"] = None; save_db()
        await q.edit_message_text(f"💥 Portladi! Nuqta: x{c}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✈️ Qayta", callback_data="g_aviator")],[InlineKeyboardButton("⬅️", callback_data="to_main")]]))

    # 👑 ADMIN PANEL
    elif q.data == "admin_dash" and uid == ADMIN_ID:
        ch_list = ", ".join(map(str, DB["settings"]["cheaters"])) or "Hech kim"
        txt = f"👑 *MUKAMMAL ADMIN PANEL*\n\n🎯 *Cheat yoqilganlar:* `{ch_list}`\n✈️ *Keyingi Aviator:* x{DB['settings'].get('next_aviator') or 'Avto'}\n\n*Buyruqlar:*\n`/cheat ID` - O'yinchiga cheat yoqish/o'chirish\n`/setav KOEFF` - Aviatorni qotirish\n`/plus ID PUL` - Balans to'ldirish"
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="to_main")]]))

async def show_apple(q, ud, is_cheat):
    ag = ud["apple"]; kb = []
    for ri in range(9, -1, -1):
        row_b = []
        for ci in range(5):
            if ri < ag["row"]: lbl = "🍏"
            elif ri == ag["row"]: lbl = "🔥" if (is_cheat and ag["grid"][ri][ci] == "good") else "🟫"
            else: lbl = "🔒"
            row_b.append(InlineKeyboardButton(lbl, callback_data=f"ap_s_{ci}" if ri == ag["row"] else "lock"))
        kb.append(row_b)
    if ag["row"] > 0: kb.append([InlineKeyboardButton(f"💰 Cashout ({ag['payout']})", callback_data="ap_cash")])
    kb.append([InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main")])
    await q.edit_message_text(f"🍏 Apple (Bosqich: {ag['row'] + 1}/10)", reply_markup=InlineKeyboardMarkup(kb))

async def show_mines(q, ud, is_cheat):
    mg = ud["mines"]; kb = []
    for i in range(9):
        if mg["rev"][i]: lbl = "💵"
        else: lbl = "💣" if is_cheat and mg["grid"][i] == "mine" else "📦"
        if len(kb) == 0 or len(kb[-1]) == 3: kb.append([])
        kb[-1].append(InlineKeyboardButton(lbl, callback_data=f"m_c_{i}"))
    kb.append([InlineKeyboardButton(f"💰 Cashout ({mg['pay']})", callback_data="m_cash")])
    await q.edit_message_text(f"💣 Mines (Minalar: {mg['step']}/7)", reply_markup=InlineKeyboardMarkup(kb))

async def show_chicken(q, ud, is_cheat):
    cg = ud["chicken"]; kb = []
    for ri in range(4, -1, -1):
        row_b = []
        for ci in range(3):
            if ri < cg["row"]: lbl = "🐥"
            elif ri == cg["row"]: lbl = "⭐" if (is_cheat and cg["grid"][ri][ci] == "coin") else "🌾"
            else: lbl = "🔒"
            row_b.append(InlineKeyboardButton(lbl, callback_data=f"ch_s_{ci}" if ri == cg["row"] else "lock"))
        kb.append(row_b)
    if cg["row"] > 0: kb.append([InlineKeyboardButton(f"💰 Cashout ({cg['pay']})", callback_data="ch_cash")])
    kb.append([InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main")])
    await q.edit_message_text(f"🐥 Chicken Road (Qator: {cg['row'] + 1}/5)", reply_markup=InlineKeyboardMarkup(kb))

async def admin_cheat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        tgt = int(context.args[0]); load_db()
        if tgt in DB["settings"]["cheaters"]:
            DB["settings"]["cheaters"].remove(tgt); txt = f"❌ {tgt} uchun cheat o'chirildi."
        else:
            DB["settings"]["cheaters"].append(tgt); txt = f"✅ {tgt} uchun cheat YOQILDI! Endi u hamma narsani ko'radi."
        save_db(); await update.message.reply_text(txt)

async def admin_setav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        DB["settings"]["next_aviator"] = float(context.args[0]); save_db(); await update.message.reply_text("✅ Aviator koeffitsiyenti qotirildi!")

async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        t, v = int(context.args[0]), int(context.args[1]); load_db()
        if t in DB["users"]: DB["users"][t]["balance"] += v; save_db(); await update.message.reply_text("✅ Balans to'ldirildi!")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Online"

async def main():
    load_db()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("cheat", admin_cheat))
    bot.add_handler(CommandHandler("setav", admin_setav))
    bot.add_handler(CommandHandler("plus", admin_plus))
    bot.add_handler(CallbackQueryHandler(callback_handler))
    
    async with bot:
        await bot.initialize(); await bot.start()
        await bot.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    asyncio.run(main())
        
