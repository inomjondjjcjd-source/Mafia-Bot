import os, json, random, time, urllib.request, telebot
from flask import Flask
from threading import Thread
from telebot import types

TOKEN = "8691200742:AAGX4RR1ThorK3FUuVzdeNPrqHxRTIli8c8"
ADMIN_ID = 8086545587
KVDB_URL = "https://kvdb.io/MN86yM86yM86yM86yM86yM/shox_sup_v10_db"

bot = telebot.TeleBot(TOKEN)
DB = {"users": {}, "settings": {"next_aviator": None, "aviator_history": [1.4, 2.1, 3.5]}}
COEFFS = [1.23, 1.54, 1.93, 2.41, 3.02, 4.02, 5.7, 8.55, 13.43, 20.15, 30.22, 45.33, 69.48]

def load_db():
    global DB
    try:
        req = urllib.request.Request(KVDB_URL, method="GET")
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
            if "users" in data: DB["users"] = {int(k): v for k, v in data["users"].items()}
            if "settings" in data: DB["settings"] = data["settings"]
    except: pass

def save_db():
    try:
        payload = json.dumps({"users": {str(k): v for k, v in DB["users"].items()}, "settings": DB["settings"]}).encode("utf-8")
        req = urllib.request.Request(KVDB_URL, data=payload, method="PUT", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10): pass
    except: pass

def check_user(uid, name="Foydalanuvchi"):
    if uid not in DB["users"]:
        DB["users"][uid] = {"name": name, "balance": 10000, "last_bonus": 0, "apple_game": None, "aviator_game": None, "mines_game": None, "state": None, "temp_bet": None}
        save_db()
    u = DB["users"][uid]
    for f in ["apple_game", "aviator_game", "mines_game", "state", "temp_bet"]:
        if f not in u: u[f] = None
    return u

def get_main_keyboard(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🍏 Apple of Fortune", callback_data="prep_apple"), types.InlineKeyboardButton("🚀 Aviator (Auto-CO)", callback_data="prep_aviator"))
    kb.add(types.InlineKeyboardButton("💣 MINES", callback_data="prep_mines"), types.InlineKeyboardButton("🐊 Swamp Land", callback_data="swamp_soon"))
    kb.add(types.InlineKeyboardButton("🎁 KUNDALIK BONUS", callback_data="get_daily_bonus"), types.InlineKeyboardButton("👑 Admin Panel" if uid == ADMIN_ID else "ℹ️ Profil", callback_data="admin_dashboard" if uid == ADMIN_ID else "to_main"))
    kb.add(types.InlineKeyboardButton("💸 Pul Kiritish", url=f"tg://user?id={ADMIN_ID}"), types.InlineKeyboardButton("💳 Pul Yechish", url=f"tg://user?id={ADMIN_ID}"))
    return kb

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    ud = check_user(uid, message.from_user.first_name)
    ud["state"] = None; save_db()
    txt = f"👑 *SHOX SUPREME PLATFORMA v10.0*\n\n💵 *Balans:* {ud['balance']} so'm\nStatus: 🟢 Live (Uyg'oq)"
    bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=get_main_keyboard(uid))

@bot.message_handler(func=lambda m: check_user(m.from_user.id).get("state") is not None)
def handle_text(message):
    uid, text = message.from_user.id, message.text
    ud = check_user(uid)
    if uid != ADMIN_ID: return
    if ud["state"] == "set_kf":
        try:
            DB["settings"]["next_aviator"] = round(float(text), 2); save_db()
            bot.send_message(message.chat.id, f"✅ Keyingi kf *x{text}* bo'ldi!", parse_mode="Markdown")
        except: bot.send_message(message.chat.id, "❌ Xato son.")
    elif ud["state"] == "add_money":
        try:
            tid, amt = map(int, text.split())
            if tid in DB["users"]:
                DB["users"][tid]["balance"] += amt; save_db()
                bot.send_message(message.chat.id, f"✅ ID {tid} ga {amt} qo'shildi!")
        except: bot.send_message(message.chat.id, "❌ Format: `ID summa`")
    ud["state"] = None; save_db()

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid, cid, mid = call.from_user.id, call.message.chat.id, call.message.message_id
    ud = check_user(uid)
    
    if call.data == "to_main":
        ud["state"] = ud["apple_game"] = ud["aviator_game"] = ud["mines_game"] = None; save_db()
        try: bot.edit_message_text(f"👑 *SHOX SUPREME PLATFORMA v10.0*\n\n💵 *Balans:* {ud['balance']} so'm", cid, mid, parse_mode="Markdown", reply_markup=get_main_keyboard(uid))
        except: pass
    elif call.data == "swamp_soon":
        bot.answer_callback_query(call.id, "🐊 Swamp Land o'yini yaqin orada platformaga qo'shiladi!", show_alert=True)
    elif call.data == "get_daily_bonus":
        t_now = int(time.time())
        if t_now - ud.get("last_bonus", 0) < 86400:
            bot.answer_callback_query(call.id, "❌ Kuniga 1 marta beriladi.", show_alert=True); return
        amt = random.randint(1000, 5000); ud["balance"] += amt; ud["last_bonus"] = t_now; save_db()
        bot.answer_callback_query(call.id, f"🎁 +{amt} so'm!", show_alert=True)
        try: bot.edit_message_text(f"👑 *SHOX SUPREME PLATFORMA v10.0*\n\n💵 *Balans:* {ud['balance']} so'm", cid, mid, parse_mode="Markdown", reply_markup=get_main_keyboard(uid))
        except: pass
    elif call.data == "admin_dashboard" and uid == ADMIN_ID:
        kb = types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton("📈 Aviator Cheat", callback_data="adm_set_kf"),
            types.InlineKeyboardButton("💰 Pul Qo'shish", callback_data="adm_add_money"),
            types.InlineKeyboardButton("🔄 Global Reset (10k)", callback_data="adm_reset"),
            types.InlineKeyboardButton("⬅ Bosh Menyu", callback_data="to_main")
        )
        bot.edit_message_text(f"👑 *ADMIN PANEL*\n\n👥 Jami: {len(DB['users'])} ta", cid, mid, reply_markup=kb)
    elif call.data == "adm_set_kf" and uid == ADMIN_ID:
        ud["state"] = "set_kf"; save_db(); bot.edit_message_text("🚀 Keyingi kf yozing:", cid, mid)
    elif call.data == "adm_add_money" and uid == ADMIN_ID:
        ud["state"] = "add_money"; save_db(); bot.edit_message_text("💰 `ID summa` ko'rinishida yozing:", cid, mid, parse_mode="Markdown")
    elif call.data == "adm_reset" and uid == ADMIN_ID:
        for u in DB["users"].values(): u["balance"] = 10000
        save_db(); bot.answer_callback_query(call.id, "🔄 Pullar 10k qilindi!", show_alert=True)

    # --- MINES ---
    elif call.data == "prep_mines":
        kb = types.InlineKeyboardMarkup(row_width=3)
        v = [5000, 20000, 50000, 100000, 500000] if uid == ADMIN_ID else [2000, 5000, 10000, 15000]
        kb.add(*[types.InlineKeyboardButton(f"{b} so'm", callback_data=f"m_bet_{b}") for b in v])
        kb.add(types.InlineKeyboardButton("⬅ Chiqish", callback_data="to_main"))
        bot.edit_message_text("💣 *MINES O'YINI*\n\nTikish summasini tanlang:", cid, mid, reply_markup=kb)
    elif call.data.startswith("m_bet_"):
        bet = int(call.data.split("_")[2])
        if bet > ud["balance"]: bot.answer_callback_query(call.id, "❌ Balans yetarli emas!", show_alert=True); return
        ud["temp_bet"] = bet; save_db()
        kb = types.InlineKeyboardMarkup(row_width=3).add(*[types.InlineKeyboardButton(f"💣 {b}", callback_data=f"m_bomb_{b}") for b in [1, 3, 5, 10, 24]]).add(types.InlineKeyboardButton("⬅ Orqaga", callback_data="prep_mines"))
        bot.edit_message_text(f"💣 Tikilgan: *{bet} so'm*\n\nMinalar soni:", cid, mid, parse_mode="Markdown", reply_markup=kb)
    elif call.data.startswith("m_bomb_"):
        bombs = int(call.data.split("_")[2])
        bet = ud.get("temp_bet")
        if not bet or bet > ud["balance"]: return
        ud["balance"] -= bet
        ud["mines_game"] = {"bet": bet, "mines_count": bombs, "mines": random.sample(range(30), bombs), "opened": [], "current_kf": 1.0, "payout": bet, "status": "playing"}
        ud["temp_bet"] = None; save_db(); show_mines_board(call.message, ud, uid)
    elif call.data.startswith("mine_open_"):
        mg = ud.get("mines_game")
        if not mg or mg["status"] != "playing": return
        idx = int(call.data.split("_")[2])
        if idx in mg["opened"]: return
        if idx in mg["mines"]:
            mg["status"] = "lost"; save_db(); show_mines_board(call.message, ud, uid, lost=True); return
        mg["opened"].append(idx)
        coeff = 1.0
        for i in range(len(mg["opened"])):
            sl = 30 - mg["mines_count"] - i
            if sl <= 0: break
            coeff *= ((30 - i) / sl)
        mg["current_kf"] = round(coeff * 0.95, 2); mg["payout"] = int(mg["bet"] * mg["current_kf"]); save_db()
        if len(mg["opened"]) == (30 - mg["mines_count"]):
            ud["balance"] += mg["payout"]; mg["status"] = "won"; save_db(); show_mines_board(call.message, ud, uid, won=True); return
        show_mines_board(call.message, ud, uid)
    elif call.data == "mines_cashout":
        mg = ud.get("mines_game")
        if mg and mg["status"] == "playing" and mg["opened"]:
            ud["balance"] += mg["payout"]; mg["status"] = "won"; save_db(); show_mines_board(call.message, ud, uid, won=True)

    # --- APPLE ---
    elif call.data == "prep_apple":
        kb = types.InlineKeyboardMarkup(row_width=3)
        v = [5000, 20000, 50000, 100000, 500000] if uid == ADMIN_ID else [2000, 5000, 10000, 15000]
        kb.add(*[types.InlineKeyboardButton(f"🍏 {b} so'm", callback_data=f"ap_bet_{b}") for b in v])
        kb.add(types.InlineKeyboardButton("⬅ Chiqish", callback_data="to_main"))
        bot.edit_message_text("🍏 *APPLE OF FORTUNE*\n\nTikish summasini tanlang:", cid, mid, parse_mode="Markdown", reply_markup=kb)
    elif call.data.startswith("ap_bet_"):
        bet = int(call.data.split("_")[2])
        if bet > ud["balance"]: bot.answer_callback_query(call.id, "❌ Balans kam!", show_alert=True); return
        ud["balance"] -= bet; grid = []
        for r in range(13):
            items = ["good"] * 5
            bad = 1 if r < 4 else 2 if r < 8 else 3 if r < 11 else 4
            for bi in random.sample(range(5), bad): items[bi] = "bad"
            grid.append(items)
        ud["apple_game"] = {"grid": grid, "current_row": 0, "bet": bet, "payout": bet}; save_db(); show_apple(call.message, ud, uid)
    elif call.data.startswith("ap_select_"):
        ag = ud.get("apple_game")
        if not ag: return
        idx = int(call.data.split("_")[2])
        if ag["grid"][ag["current_row"]][idx] == "bad":
            ud["apple_game"] = None; save_db()
            bot.edit_message_text("💀 *Chirigan olma!*", cid, mid, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🍏 Qayta", callback_data="prep_apple")))
            return
        ag["payout"] = int(ag["bet"] * COEFFS[ag["current_row"]]); ag["current_row"] += 1; save_db()
        if ag["current_row"] == 13:
            ud["balance"] += ag["payout"]; ud["apple_game"] = None; save_db()
            bot.edit_message_text(f"👑 *JACKPOT!* \n💰 +{ag['payout']} so'm!", cid, mid, reply_markup=get_main_keyboard(uid))
            return
        show_apple(call.message, ud, uid)
    elif call.data == "ap_cashout" and ud.get("apple_game"):
        ud["balance"] += ud["apple_game"]["payout"]; ud["apple_game"] = None; save_db()
        bot.edit_message_text("💰 Pul yechildi!", cid, mid, reply_markup=get_main_keyboard(uid))

    # --- AVIATOR ---
    elif call.data == "prep_aviator":
        if not DB["settings"].get("next_aviator"): DB["settings"]["next_aviator"] = round(random.uniform(1.1, 4.5), 2); save_db()
        h_tx = " | ".join([f"x{h}" for h in DB["settings"].get("aviator_history", [1.2, 2.5])[-5:]])
        cm = f"🔮 *CHEAT: x{DB['settings']['next_aviator']}*\n\n" if uid == ADMIN_ID else ""
        kb = types.InlineKeyboardMarkup(row_width=3)
        v = [5000, 20000, 50000, 100000, 500000] if uid == ADMIN_ID else [2000, 5000, 10000, 15000]
        kb.add(*[types.InlineKeyboardButton(f"🚀 {b} so'm", callback_data=f"av_bet_{b}") for b in v]).add(types.InlineKeyboardButton("⬅ Chiqish", callback_data="to_main"))
        bot.edit_message_text(f"📊 *Tarix:* [{h_tx}]\n\n{cm}🚀 *AVIATOR*\n\nTikish:", cid, mid, parse_mode="Markdown", reply_markup=kb)
    elif call.data.startswith("av_bet_"):
        bet = int(call.data.split("_")[2])
        if bet > ud["balance"]: bot.answer_callback_query(call.id, "❌ Balans kam!", show_alert=True); return
        ud["temp_bet"] = bet; save_db()
        kb = types.InlineKeyboardMarkup(row_width=2).add(types.InlineKeyboardButton("📈 Auto x1.5", callback_data="av_mode_1.5"), types.InlineKeyboardButton("📈 Auto x2.0", callback_data="av_mode_2.0"), types.InlineKeyboardButton("📈 Auto x3.0", callback_data="av_mode_3.0"), types.InlineKeyboardButton("🔥 Qo'lda", callback_data="av_mode_manual"))
        bot.edit_message_text(f"🚀 Tikilgan: *{bet} so'm*", cid, mid, parse_mode="Markdown", reply_markup=kb)
    elif call.data.startswith("av_mode_"):
        mode = call.data.split("_")[2]; bet = ud.get("temp_bet")
        if not bet or bet > ud["balance"]: return
        ud["balance"] -= bet; crash = DB["settings"].get("next_aviator", 2.0); DB["settings"]["next_aviator"] = None
        if "aviator_history" not in DB["settings"]: DB["settings"]["aviator_history"] = []
        DB["settings"]["aviator_history"].append(crash)
        if len(DB["settings"]["aviator_history"]) > 5: DB["settings"]["aviator_history"].pop(0)
        ud["aviator_game"] = {"bet": bet, "current_win": 1.0, "crash": crash, "auto_co": None if mode == "manual" else float(mode), "status": "flying"}
        ud["temp_bet"] = None; save_db(); Thread(target=run_aviator_thread, args=(cid, mid, uid), daemon=True).start()
    elif call.data == "av_cashout_manual":
        ag = ud.get("aviator_game")
        if ag and ag["status"] == "flying":
            ag["status"] = "cashout"; win = int(ag["bet"] * ag["current_win"]); ud["balance"] += win; ud["aviator_game"] = None; save_db()
            bot.edit_message_text(f"💰 *YUTUQ:* +{win} so'm (x{ag['current_win']})", cid, mid, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 Qayta", callback_data="prep_aviator")))

def show_mines_board(mo, ud, uid, lost=False, won=False):
    mg = ud["mines_game"]; kb, btns = types.InlineKeyboardMarkup(row_width=5), []
    for i in range(30):
        if lost: btns.append(types.InlineKeyboardButton("💥" if i in mg["mines"] else "💎" if i in mg["opened"] else "⬜️", callback_data="lock"))
        elif won: btns.append(types.InlineKeyboardButton("💣" if i in mg["mines"] else "💎", callback_data="lock"))
        else:
            if i in mg["opened"]: btns.append(types.InlineKeyboardButton("💎", callback_data="lock"))
            else: btns.append(types.InlineKeyboardButton("🟢" if (uid == ADMIN_ID and i in mg["mines"]) else "❓", callback_data=f"mine_open_{i}"))
    kb.add(*btns)
    if not lost and not won:
        if mg["opened"]: kb.add(types.InlineKeyboardButton(f"💰 Yechish ({mg['payout']})", callback_data="mines_cashout"))
        kb.add(types.InlineKeyboardButton("⬅ Chiqish", callback_data="to_main"))
    else: kb.add(types.InlineKeyboardButton("🔄 Qayta", callback_data="prep_mines"), types.InlineKeyboardButton("⬅️ Menyu", callback_data="to_main"))
    txt = "💥 *MAG'LUBIYAT!*" if lost else f"👑 *G'ALABA!* +{mg['payout']} so'm!" if won else f"💣 *MINES* \n📈 Kf: *x{mg['current_kf']}* | Yutuq: *{mg['payout']}*"
    try: bot.edit_message_text(txt, mo.chat.id, mo.message_id, parse_mode="Markdown", reply_markup=kb)
    except: pass

def show_apple(mo, ud, uid):
    ag = ud["apple_game"]; kb = types.InlineKeyboardMarkup(row_width=6)
    for ri in range(12, -1, -1):
        r_btns = [types.InlineKeyboardButton(f"x{COEFFS[ri]}", callback_data="lock")]
        for ci in range(5):
            if ri == ag["current_row"] and uid == ADMIN_ID: r_btns.append(types.InlineKeyboardButton("🍏" if ag["grid"][ri][ci] == "good" else "🔻", callback_data=f"ap_select_{ci}"))
            else: r_btns.append(types.InlineKeyboardButton("🍏" if ri < ag["current_row"] else "🟫" if ri == ag["current_row"] else "🔒", callback_data=f"ap_select_{ci}" if ri == ag["current_row"] else "lock"))
        kb.row(*r_btns)
    if ag["current_row"] > 0: kb.add(types.InlineKeyboardButton(f"💰 Yechish ({ag['payout']})", callback_data="ap_cashout"))
    kb.add(types.InlineKeyboardButton("⬅ Chiqish", callback_data="to_main"))
    try: bot.edit_message_text(f"🍏 *APPLE OF FORTUNE*\nYutuq: *{ag['payout']}*", mo.chat.id, mo.message_id, parse_mode="Markdown", reply_markup=kb)
    except: pass

def run_aviator_thread(chat_id, message_id, uid):
    for _ in range(60):
        time.sleep(0.6); ud = DB["users"].get(uid)
        if not ud or not ud.get("aviator_game") or ud["aviator_game"]["status"] != "flying": break
        ag = ud["aviator_game"]; ag["current_win"] = round(ag["current_win"] + random.uniform(0.1, 0.22), 2)
        if ag["auto_co"] and ag["current_win"] >= ag["auto_co"] and ag["current_win"] < ag["crash"]:
            ag["status"] = "cashout"; w = int(ag["bet"] * ag["auto_co"]); ud["balance"] += w; ud["aviator_game"] = None; save_db()
            bot.edit_message_text(f"🤖 *AUTO CO:* +{w} so'm (x{ag['auto_co']})", chat_id, message_id, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 Qayta", callback_data="prep_aviator"))); break
        if ag["current_win"] >= ag["crash"]:
            cp = ag["crash"]; ud["aviator_game"] = None; save_db()
            bot.edit_message_text(f"💥 *BOOM! x{cp}*", chat_id, message_id, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 Qayta", callback_data="prep_aviator"))); break
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(f"🛑 CASHOUT ({int(ag['bet'] * ag['current_win'])})", callback_data="av_cashout_manual") if not ag["auto_co"] else types.InlineKeyboardButton(f"🎯 Auto: x{ag['auto_co']}", callback_data="lock"))
        try: bot.edit_message_text(f"✈️ *AVIATOR*\n📈 Kf: *x{ag['current_win']}*", chat_id, message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

app = Flask(__name__)
@app.route('/')
def home(): return "Active"

if __name__ == '__main__':
    load_db(); port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: app.run(host="0.0.0.0", port=port), daemon=True).start()
    bot.infinity_polling(skip_pending=True)
