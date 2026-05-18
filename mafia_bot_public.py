import os, json, random, asyncio
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = "8303235336:AAEk3J42idbz1KcamIWPC2L3_IlROPeoadI"
ADMIN_ID = 8086545587  
DATA_FILE = "mega_games_bot_db.json"

DB = {"users": {}, "settings": {"next_aviator": None, "next_apple": None, "cheat_mines": False}}
APPLE_COEFFS = [1.23, 1.54, 1.93, 2.41, 3.02, 4.02, 5.70, 8.55, 13.43, 69.48]

def load_db():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                DB = json.load(f)
                DB["users"] = {int(k): v for k, v in DB.get("users", {}).items()}
        except: pass

def save_db():
    try:
        to_save = DB.copy()
        to_save["users"] = {str(k): v for k, v in DB["users"].items()}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=4, ensure_ascii=False)
    except: pass

def check_user(uid, name="Foydalanuvchi"):
    load_db()
    if uid not in DB["users"]:
        DB["users"][uid] = {"name": name, "balance": 5000, "tickets": 3, "mines_game": None, "apple_game": None, "aviator_game": None}
        save_db()
    return DB["users"][uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; ud = check_user(uid, update.effective_user.first_name)
    txt = f"👑 *SHOX SUPREME PLATFORMA*\n\n💵 *Balans:* {ud['balance']} so'm\n🎫 *Chiptalar:* {ud['tickets']} ta"
    kb = [
        [InlineKeyboardButton("💣 Mines (Mina)", callback_data="g_mines"), InlineKeyboardButton("🎰 Slot (777)", callback_data="g_slot")],
        [InlineKeyboardButton("🍏 Apple of Fortune", callback_data="g_apple"), InlineKeyboardButton("✈️ Aviator", callback_data="g_aviator")],
        [InlineKeyboardButton("🎫 1 Chipta (4k)", callback_data="b_ticket_1"), InlineKeyboardButton("🎁 10 Chipta (30k)", callback_data="b_ticket_10")],
        [InlineKeyboardButton("👑 Admin Panel", callback_data="admin_dashboard")] if uid == ADMIN_ID else []
    ]
    kb = [x for x in kb if x]
    if update.message: await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    else: await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); uid = q.from_user.id; ud = check_user(uid)
    if q.data == "to_main": await start(update, context)
    
    elif q.data == "b_ticket_1" and ud["balance"] >= 4000:
        ud["balance"] -= 4000; ud["tickets"] += 1; save_db(); await start(update, context)
    elif q.data == "b_ticket_10" and ud["balance"] >= 30000:
        ud["balance"] -= 30000; ud["tickets"] += 10; save_db(); await start(update, context)

    elif q.data == "g_slot":
        if ud["balance"] < 3000: return
        ud["balance"] -= 3000; res = [random.choice(["🍒", "🍋", "7️⃣"]) for _ in range(3)]
        win = 30000 if res[0]==res[1]==res[2]=="7️⃣" else 10000 if res[0]==res[1]==res[2] else 4000 if (res[0]==res[1] or res[1]==res[2]) else 0
        ud["balance"] += win; save_db()
        txt = f"🎰 [ {' | '.join(res)} ]\n\n" + (f"👑 *YUTUQ:* +{win} so'm!" if win > 0 else "💀 Omad kelmadi!")
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎰 Qayta (3k)", callback_data="g_slot")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))

    elif q.data == "g_mines":
        if not ud["mines_game"]:
            if ud["tickets"] < 1: return
            ud["tickets"] -= 1; grid = ["clean"] * 9
            for idx in random.sample(range(9), 2): grid[idx] = "mine"
            ud["mines_game"] = {"grid": grid, "revealed": [False] * 9, "payout": 4000, "step": 0}; save_db()
        await show_mines(q, ud)
    elif q.data.startswith("m_clk_"):
        idx = int(q.data.split("_")[2]); mg = ud["mines_game"]
        if not mg or mg["revealed"][idx]: return
        mg["revealed"][idx] = True
        if mg["grid"][idx] == "mine":
            ud["mines_game"] = None; save_db()
            await q.edit_message_text("💥 PORTLADINGIZ!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💣 Qayta", callback_data="g_mines")], [InlineKeyboardButton("⬅️", callback_data="to_main")]])); return
        mg["step"] += 1; mg["payout"] = int(mg["payout"] * 1.6); save_db()
        if mg["step"] == 7:
            ud["balance"] += mg["payout"]; ud["mines_game"] = None; save_db()
            await q.edit_message_text(f"👑 G'ALABA! +{mg['payout']} so'm", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="to_main")]])); return
        await show_mines(q, ud)
    elif q.data == "m_cash" and ud["mines_game"]:
        ud["balance"] += ud["mines_game"]["payout"]; ud["mines_game"] = None; save_db(); await start(update, context)

    elif q.data == "g_apple":
        if not ud["apple_game"]:
            if ud["balance"] < 3000: return
            ud["balance"] -= 3000; fg = []; force_col = DB["settings"].get("next_apple"); DB["settings"]["next_apple"] = None
            for r in range(10):
                items = ["good"] * 5; bads = random.sample(range(5), 1 if r < 4 else 2)
                if r == 0 and force_col is not None and force_col in bads:
                    bads.remove(force_col)
                    bads.append(random.choice([i for i in range(5) if i != force_col]))
                for bi in bads: items[bi] = "bad"
                fg.append(items)
            ud["apple_game"] = {"grid": fg, "current_row": 0, "payout": 3000}; save_db()
        await show_apple(q, ud)
    elif q.data.startswith("ap_select_"):
        idx = int(q.data.split("_")[2]); ag = ud["apple_game"]
        if not ag or ag["grid"][ag["current_row"]][idx] == "bad":
            ud["apple_game"] = None; save_db()
            await q.edit_message_text("💀 Chirigan olma!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🍏 Qayta", callback_data="g_apple")], [InlineKeyboardButton("⬅️", callback_data="to_main")]])); return
        ag["payout"] = int(3000 * APPLE_COEFFS[ag["current_row"]]); ag["current_row"] += 1; save_db()
        if ag["current_row"] == 10:
            ud["balance"] += ag["payout"]; ud["apple_game"] = None; save_db(); await start(update, context); return
        await show_apple(q, ud)
    elif q.data == "ap_cashout" and ud["apple_game"]:
        ud["balance"] += ud["apple_game"]["payout"]; ud["apple_game"] = None; save_db(); await start(update, context)

    elif q.data == "g_aviator":
        if ud["balance"] < 2000: return
        crash = DB["settings"].get("next_aviator") or round(random.uniform(1.3, 4.5), 2)
        DB["settings"]["next_aviator"] = None
        win_p = round(random.uniform(1.1, max(1.2, crash - 0.2)), 2)
        ud["balance"] -= 2000; ud["aviator_game"] = {"win": win_p, "crash": crash}; save_db()
        txt = f"✈️ *AVIATOR*\n\n📈 Koeffitsiyent: *x{win_p}*\n(Portlash: x{crash})"
        kb = [[InlineKeyboardButton(f"🛑 CASHOUT (x{win_p})", callback_data="av_cash")], [InlineKeyboardButton("🚀 Kutish (Tavakkal)", callback_data="av_risk")]]
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data == "av_cash" and ud["aviator_game"]:
        w = int(2000 * ud["aviator_game"]["win"]); ud["balance"] += w; ud["aviator_game"] = None; save_db(); await start(update, context)
    elif q.data == "av_risk" and ud["aviator_game"]:
        c = ud["aviator_game"]["crash"]; ud["aviator_game"] = None; save_db()
        await q.edit_message_text(f"💥 Portladi! Nuqta: x{c}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✈️ Qayta", callback_data="g_aviator")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))

    elif q.data == "admin_dashboard" and uid == ADMIN_ID:
        st = DB["settings"]; next_av = st.get("next_aviator") or "Avto"; next_ap = st.get("next_apple") or "Avto"
        txt = f"👑 *ADMIN PANEL*\n\n✈️ Aviator: x{next_av}\n🍏 Apple: {next_ap}\n\n/setav KOEFF\n/setapple USTUN(1-5)\n/plus ID PUL"
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="to_main")]]))

async def show_mines(q, ud):
    mg = ud["mines_game"]; kb = []
    for i in range(9):
        lbl = "💵" if mg["revealed"][i] else "📦"
        if len(kb) == 0 or len(kb[-1]) == 3: kb.append([])
        kb[-1].append(InlineKeyboardButton(lbl, callback_data=f"m_clk_{i}"))
    kb.append([InlineKeyboardButton(f"💰 Cashout ({mg['payout']})", callback_data="m_cash")])
    await q.edit_message_text(f"💣 Mines (Bosqich: {mg['step']}/7)", reply_markup=InlineKeyboardMarkup(kb))

async def show_apple(q, ud):
    ag = ud["apple_game"]; crow = ag["current_row"]; kb = []
    for ri in range(4, -1, -1):
        kb.append([InlineKeyboardButton("🍏" if ri < crow else "🟫" if ri == crow else "🔒", callback_data=f"ap_select_{ci}" if ri == crow else "ap_lock") for ci in range(5)])
    if crow > 0: kb.append([InlineKeyboardButton(f"💰 Olish ({ag['payout']})", callback_data="ap_cashout")])
    kb.append([InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main")])
    await q.edit_message_text(f"🍏 Apple (Etap: {crow+1})", reply_markup=InlineKeyboardMarkup(kb))

async def admin_set_aviator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        DB["settings"]["next_aviator"] = float(context.args[0]); save_db()
        await update.message.reply_text("✅ Aviator qotirildi!")

async def admin_set_apple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        DB["settings"]["next_apple"] = int(context.args[0]) - 1; save_db()
        await update.message.reply_text("✅ Apple 1-qatordagi ustun qotirildi!")

async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        t, v = int(context.args[0]), int(context.args[1]); load_db()
        if t in DB["users"]: DB["users"][t]["balance"] += v; save_db(); await update.message.reply_text("✅ To'ldirildi!")

app = Flask(__name__)
@app.route('/')
def home(): return "Online"

if __name__ == '__main__':
    load_db()
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("setav", admin_set_aviator))
    bot.add_handler(CommandHandler("setapple", admin_set_apple))
    bot.add_handler(CommandHandler("plus", admin_plus))
    bot.add_handler(CallbackQueryHandler(callback_handler))
    bot.run_polling(drop_pending_updates=True)
                                                        
