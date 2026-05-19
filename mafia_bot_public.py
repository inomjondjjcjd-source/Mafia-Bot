import os
import json
import random
import time
import urllib.request
from flask import Flask
from threading import Thread

import telebot
from telebot import types

# --- ASOSIY SOZLAMALAR ---
TOKEN = "8691200742:AAEz0bAHTK3tSfvS1EwAbvg3T4wGmBt5kks" 
ADMIN_ID = 8086545587
RENDER_URL = "https://mafia-bot-1-cfws.onrender.com"

bot = telebot.TeleBot(TOKEN)

# Pullar yo'qolmasligi uchun onlayn JSON baza
KVDB_URL = "https://kvdb.io/MN86yM86yM86yM86yM86yM/shox_supreme_v8_db"

DB = {
    "users": {},
    "settings": {
        "next_aviator": None,
        "aviator_history": [2.34, 1.55, 4.12, 1.22, 3.05]
    }
}

APPLE_COEFFS = [1.23, 1.54, 1.93, 2.41, 3.02, 4.02, 5.70, 8.55, 13.43, 20.15, 30.22, 45.33, 69.48]

def load_db():
    global DB
    try:
        req = urllib.request.Request(KVDB_URL, method="GET")
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
            if "users" in data:
                DB["users"] = {int(k): v for k, v in data["users"].items()}
            if "settings" in data:
                DB["settings"] = data["settings"]
            print("🚀 Pullar onlayn bazadan yuklandi!")
    except Exception as e:
        print(f"⚠️ Zaxira xotirasi: {e}")

def save_db():
    try:
        serializable_users = {str(k): v for k, v in DB["users"].items()}
        payload = json.dumps({"users": serializable_users, "settings": DB["settings"]}).encode("utf-8")
        req = urllib.request.Request(KVDB_URL, data=payload, method="PUT", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r: pass
    except Exception as e:
        print(f"⚠️ Saqlashda xato: {e}")

def check_user(uid, name="Foydalanuvchi"):
    if uid not in DB["users"]:
        DB["users"][uid] = {
            "name": name,
            "balance": 10000,
            "tickets": 5,
            "last_bonus": 0,
            "apple_game": None,
            "aviator_game": None,
            "mines_game": None,
            "state": None,
            "temp_bet": None
        }
        save_db()
    u = DB["users"][uid]
    if "last_bonus" not in u: u["last_bonus"] = 0
    for field in ["apple_game", "aviator_game", "mines_game", "state", "temp_bet"]:
        if field not in u: u[field] = None
    return u

def get_main_keyboard(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🍏 Apple of Fortune", callback_data="prep_apple"),
        types.InlineKeyboardButton("🚀 Aviator (Auto-CO)", callback_data="prep_aviator")
    )
    kb.add(types.InlineKeyboardButton("💣 MINES (YANGI Cheat x100)", callback_data="prep_mines"))
    kb.add(
        types.InlineKeyboardButton("🎁 KUNDALIK BONUS", callback_data="get_daily_bonus"),
        types.InlineKeyboardButton("👑 Admin Panel" if uid == ADMIN_ID else "ℹ️ Profil", callback_data="admin_dashboard" if uid == ADMIN_ID else "to_main")
    )
    kb.add(
        types.InlineKeyboardButton("💸 Pul Kiritish", url=f"tg://user?id={ADMIN_ID}"),
        types.InlineKeyboardButton("💳 Pul Yechish", url=f"tg://user?id={ADMIN_ID}")
    )
    return kb

def get_mines_coeff(mines_count, opened_count):
    if opened_count == 0: return 1.0
    total_cells = 30
    coeff = 1.0
    for i in range(opened_count):
        safe_cells_left = 30 - mines_count - i
        total_cells_left = 30 - i
        if safe_cells_left <= 0: break
        coeff *= (total_cells_left / safe_cells_left)
    return round(coeff * 0.95, 2)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    ud = check_user(uid, message.from_user.first_name)
    ud["state"] = None
    save_db()
    txt = (
        f"👑 *SHOX SUPREME PLATFORMA v9.0*\n\n"
        f"💵 *Balans:* {ud['balance']} so'm\n"
        f"🎫 *Chiptalar:* {ud['tickets']} ta\n\n"
        f"⚡️ *Bot muvaffaqiyatli yangilandi va tezlashtirildi!*"
    )
    bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=get_main_keyboard(uid))

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    ud = check_user(uid)
    
    if call.data == "to_main":
        ud["state"] = None
        ud["apple_game"] = None
        ud["aviator_game"] = None
        ud["mines_game"] = None
        save_db()
        txt = f"👑 *SHOX SUPREME PLATFORMA v9.0*\n\n💵 *Balans:* {ud['balance']} so'm\n🎫 *Chiptalar:* {ud['tickets']} ta"
        try: bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard(uid))
        except: pass

    elif call.data == "get_daily_bonus":
        current_time = int(time.time())
        if current_time - ud["last_bonus"] < 86400:
            rem = 86400 - (current_time - ud["last_bonus"])
            hours = rem // 3600
            mins = (rem % 3600) // 60
            bot.answer_callback_query(call.id, f"❌ Bonus olingan! Keyingi bonusga {hours} soat, {mins} daqiqa bor.", show_alert=True)
            return
        bonus_amount = random.randint(500, 3000)
        ud["balance"] += bonus_amount
        ud["last_bonus"] = current_time
        save_db()
        bot.answer_callback_query(call.id, f"🎁 Balansga {bonus_amount} so'm qo'shildi!", show_alert=True)
        txt = f"👑 *SHOX SUPREME PLATFORMA v9.0*\n\n💵 *Balans:* {ud['balance']} so'm\n🎫 *Chiptalar:* {ud['tickets']} ta"
        try: bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard(uid))
        except: pass

    # --- MINES ---
    elif call.data == "prep_mines":
        ud["state"] = None
        kb = types.InlineKeyboardMarkup(row_width=3)
        kb.add(*[types.InlineKeyboardButton(f"{b} so'm", callback_data=f"m_bet_{b}") for b in [2000, 3000, 5000, 8000, 10000]])
        kb.add(types.InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main"))
        try: bot.edit_message_text("💣 *MINES O'YINI*\n\nTikish summasini tanlang:", call.message.chat.id, call.message.message_id, reply_markup=kb)
        except: pass

    elif call.data.startswith("m_bet_"):
        bet = int(call.data.split("_")[2])
        if bet > ud["balance"]:
            bot.answer_callback_query(call.id, "❌ Balans yetarli emas!", show_alert=True)
            return
        ud["temp_bet"] = bet
        save_db()
        kb = types.InlineKeyboardMarkup(row_width=3)
        kb.add(*[types.InlineKeyboardButton(f"💣 {b}", callback_data=f"m_bomb_{b}") for b in [1, 2, 3, 4, 7, 10, 15, 20, 24]])
        kb.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="prep_mines"))
        try: bot.edit_message_text(f"💣 Tikilgan: *{bet} so'm*\n\nMinalar sonini tanlang:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

    elif call.data.startswith("m_bomb_"):
        bombs = int(call.data.split("_")[2])
        bet = ud.get("temp_bet")
        if not bet or bet > ud["balance"]: return
        ud["balance"] -= bet
        mines_positions = random.sample(range(30), bombs)
        ud["mines_game"] = {"bet": bet, "mines_count": bombs, "mines": mines_positions, "opened": [], "current_kf": 1.0, "payout": bet, "status": "playing"}
        ud["temp_bet"] = None
        save_db()
        show_mines_board(call.message, ud, uid)

    elif call.data.startswith("mine_open_"):
        mg = ud.get("mines_game")
        if not mg or mg["status"] != "playing": return
        idx = int(call.data.split("_")[2])
        if idx in mg["opened"]: return
        if idx in mg["mines"]:
            mg["status"] = "lost"; save_db()
            show_mines_board(call.message, ud, uid, lost=True)
            return
        mg["opened"].append(idx)
        mg["current_kf"] = get_mines_coeff(mg["mines_count"], len(mg["opened"]))
        mg["payout"] = int(mg["bet"] * mg["current_kf"])
        save_db()
        if len(mg["opened"]) == (30 - mg["mines_count"]):
            ud["balance"] += mg["payout"]; mg["status"] = "won"; save_db()
            show_mines_board(call.message, ud, uid, won=True)
            return
        show_mines_board(call.message, ud, uid)

    elif call.data == "mines_cashout":
        mg = ud.get("mines_game")
        if not mg or mg["status"] != "playing" or len(mg["opened"]) == 0: return
        ud["balance"] += mg["payout"]; mg["status"] = "won"; save_db()
        show_mines_board(call.message, ud, uid, won=True)

    # --- APPLE OF FORTUNE ---
    elif call.data == "prep_apple":
        ud["state"] = None
        kb = types.InlineKeyboardMarkup(row_width=3)
        kb.add(*[types.InlineKeyboardButton(f"🍏 {b} so'm", callback_data=f"ap_bet_{b}") for b in [2000, 3000, 5000, 8000, 10000]])
        kb.add(types.InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main"))
        try: bot.edit_message_text("🍏 *APPLE OF FORTUNE*\n\nTikish summasini tanlang:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

    elif call.data.startswith("ap_bet_"):
        bet = int(call.data.split("_")[2])
        if bet > ud["balance"]:
            bot.answer_callback_query(call.id, "❌ Balans yetarli emas!", show_alert=True)
            return
        ud["balance"] -= bet
        grid = []
        for r in range(13):
            items = ["good"] * 5
            bad = 1 if r < 4 else 2 if r < 8 else 3 if r < 11 else 4
            for bi in random.sample(range(5), bad): items[bi] = "bad"
            grid.append(items)
        ud["apple_game"] = {"grid": grid, "current_row": 0, "bet": bet, "payout": bet}
        save_db()
        show_apple(call.message, ud)

    elif call.data.startswith("ap_select_"):
        ag = ud.get("apple_game")
        if not ag: return
        idx = int(call.data.split("_")[2])
        if ag["grid"][ag["current_row"]][idx] == "bad":
            ud["apple_game"] = None; save_db()
            kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🍏 Qayta o'ynash", callback_data="prep_apple"))
            try: bot.edit_message_text("💀 *Chirigan olma! Mag'lubiyat.*", call.message.chat.id, call.message.message_id, reply_markup=kb)
            except: pass
            return
        ag["payout"] = int(ag["bet"] * APPLE_COEFFS[ag["current_row"]])
        ag["current_row"] += 1
        save_db()
        if ag["current_row"] == 13:
            ud["balance"] += ag["payout"]; ud["apple_game"] = None; save_db()
            try: bot.edit_message_text(f"👑 *JACKPOT!* \n💰 +{ag['payout']} so'm!", call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard(uid))
            except: pass
            return
        show_apple(call.message, ud)

    elif call.data == "ap_cashout" and ud.get("apple_game"):
        ud["balance"] += ud["apple_game"]["payout"]; ud["apple_game"] = None; save_db()
        try: bot.edit_message_text("💰 Olma o'yinidan pul yechib olindi!", call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard(uid))
        except: pass

    # --- AVIATOR ---
    elif call.data == "prep_aviator":
        ud["state"] = None
        kb = types.InlineKeyboardMarkup(row_width=3)
        kb.add(*[types.InlineKeyboardButton(f"🚀 {b} so'm", callback_data=f"av_bet_{b}") for b in [2000, 3000, 5000, 8000, 10000]])
        kb.add(types.InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main"))
        try: bot.edit_message_text("🚀 *AVIATOR CRASH*\n\nTikish summasini tanlang:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

    elif call.data.startswith("av_bet_"):
        bet = int(call.data.split("_")[2])
        if bet > ud["balance"]:
            bot.answer_callback_query(call.id, "❌ Balans yetarli emas!", show_alert=True)
            return
        ud["temp_bet"] = bet
        save_db()
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("📈 Auto x1.5", callback_data="av_mode_1.5"),
            types.InlineKeyboardButton("📈 Auto x2.0", callback_data="av_mode_2.0"),
            types.InlineKeyboardButton("📈 Auto x3.0", callback_data="av_mode_3.0"),
            types.InlineKeyboardButton("🔥 Tavakkal (Qo'lda)", callback_data="av_mode_manual")
        )
        try: bot.edit_message_text(f"🚀 Tikilgan: *{bet} so'm*\n\nAuto Cash-out koeffitsiyentini tanlang:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

    elif call.data.startswith("av_mode_"):
        mode = call.data.split("_")[2]
        bet = ud.get("temp_bet")
        if not bet or bet > ud["balance"]: return
        ud["balance"] -= bet
        crash = DB["settings"].get("next_aviator") if DB["settings"].get("next_aviator") else round(random.uniform(1.10, 4.50), 2)
        DB["settings"]["next_aviator"] = None
        ud["aviator_game"] = {"bet": bet, "current_win": 1.0, "crash": crash, "auto_co": None if mode == "manual" else float(mode), "status": "flying"}
        ud["temp_bet"] = None
        save_db()
        Thread(target=run_aviator_thread, args=(call.message.chat.id, call.message.message_id, uid), daemon=True).start()

    elif call.data == "av_cashout_manual":
        ag = ud.get("aviator_game")
        if not ag or ag["status"] != "flying": return
        ag["status"] = "cashout"
        win = int(ag["bet"] * ag["current_win"])
        ud["balance"] += win; ud["aviator_game"] = None; save_db()
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 Qayta Uchish", callback_data="prep_aviator"))
        try: bot.edit_message_text(f"💰 *CASHOUT DONE!*\n📈 Koeffitsiyent: *x{ag['current_win']}*\n💰 Yutuq: +{win} so'm!", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

    elif call.data == "admin_dashboard" and uid == ADMIN_ID:
        total_users = len(DB["users"])
        total_balance = sum([u.get("balance", 0) for u in DB["users"].values()])
        txt = f"👑 *ADMIN PANEL*\n\n👥 Foydalanuvchilar: {total_users} ta\n💰 Jami balans: {total_balance} so'm"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="to_main"))
        try: bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=kb)
        except: pass

def show_mines_board(message_obj, ud, uid, lost=False, won=False):
    mg = ud["mines_game"]
    kb = types.InlineKeyboardMarkup(row_width=5)
    btns = []
    for i in range(30):
        if lost:
            if i in mg["mines"]: btns.append(types.InlineKeyboardButton("💥", callback_data="lock"))
            elif i in mg["opened"]: btns.append(types.InlineKeyboardButton("💎", callback_data="lock"))
            else: btns.append(types.InlineKeyboardButton("⬜️", callback_data="lock"))
        elif won:
            if i in mg["mines"]: btns.append(types.InlineKeyboardButton("💣", callback_data="lock"))
            else: btns.append(types.InlineKeyboardButton("💎", callback_data="lock"))
        else:
            if i in mg["opened"]: 
                btns.append(types.InlineKeyboardButton("💎", callback_data="lock"))
            else:
                if uid == ADMIN_ID:
                    if i in mg["mines"]: btns.append(types.InlineKeyboardButton("🟢", callback_data=f"mine_open_{i}"))
                    else: btns.append(types.InlineKeyboardButton("❓", callback_data=f"mine_open_{i}"))
                else:
                    btns.append(types.InlineKeyboardButton("❓", callback_data=f"mine_open_{i}"))
    kb.add(*btns)
    if not lost and not won:
        if len(mg["opened"]) > 0: kb.add(types.InlineKeyboardButton(f"💰 Naqdlashtirish ({mg['payout']} so'm)", callback_data="mines_cashout"))
        kb.add(types.InlineKeyboardButton("⬅ Chiqish", callback_data="to_main"))
    else:
        kb.add(types.InlineKeyboardButton("🔄 Yangi O'yin", callback_data="prep_mines"), types.InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="to_main"))
    if lost: txt = f"💥 *MAG'LUBIYAT!*\n💣 Bombaga duch keldingiz.\n💸 -{mg['bet']} so'm."
    elif won: txt = f"👑 *G'ALABA!*\n📈 Koeffitsiyent: *x{mg['current_kf']}*\n💰 Sof yutuq: +{mg['payout']} so'm!"
    else: txt = f"💣 *MINES (30 katak)*\n\n💵 Tikilgan: *{mg['bet']}* so'm | Minalar: *{mg['mines_count']}*\n📈 Koeffitsiyent: *x{mg['current_kf']}*\n💰 Naqd Yutuq: *{mg['payout']}* so'm"
    try: bot.edit_message_text(txt, message_obj.chat.id, message_obj.message_id, parse_mode="Markdown", reply_markup=kb)
    except: pass

def show_apple(message_obj, ud):
    ag = ud["apple_game"]
    crow = ag["current_row"]
    kb = types.InlineKeyboardMarkup(row_width=6)
    for ri in range(12, -1, -1):
        row_btns = [types.InlineKeyboardButton(f"x{APPLE_COEFFS[ri]}", callback_data="lock")]
        for ci in range(5):
            if ri < crow: row_btns.append(types.InlineKeyboardButton("🍏", callback_data="lock"))
            elif ri == crow: row_btns.append(types.InlineKeyboardButton("🟫", callback_data=f"ap_select_{ci}"))
            else: row_btns.append(types.InlineKeyboardButton("🔒", callback_data="lock"))
        kb.row(*row_btns)
    if crow > 0: kb.add(types.InlineKeyboardButton(f"💰 Naqdlashtirish ({ag['payout']})", callback_data="ap_cashout"))
    kb.add(types.InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main"))
    try: bot.edit_message_text(f"🍏 *APPLE OF FORTUNE*\nMavjud yutuq: *{ag['payout']}* so'm", message_obj.chat.id, message_obj.message_id, parse_mode="Markdown", reply_markup=kb)
    except: pass

def run_aviator_thread(chat_id, message_id, uid):
    for _ in range(60):
        time.sleep(0.6)
        ud = DB["users"].get(uid)
        if not ud or not ud.get("aviator_game") or ud["aviator_game"]["status"] != "flying": break
        ag = ud["aviator_game"]
        ag["current_win"] = round(ag["current_win"] + random.uniform(0.10, 0.22), 2)
        
        if ag["auto_co"] and ag["current_win"] >= ag["auto_co"] and ag["current_win"] < ag["crash"]:
            ag["status"] = "cashout"
            win = int(ag["bet"] * ag["auto_co"])
            ud["balance"] += win; ud["aviator_game"] = None; save_db()
            kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 Yangi Parvoz", callback_data="prep_aviator"))
            try: bot.edit_message_text(f"🤖 *AUTO CASHOUT DONE!*\n📈 Belgilangan kf: *x{ag['auto_co']}* ga yetdi.\n💰 Yutuq: +{win} so'm!", chat_id, message_id, parse_mode="Markdown", reply_markup=kb)
            except: pass
            break

        if ag["current_win"] >= ag["crash"]:
            cp = ag["crash"]
            ud["aviator_game"] = None; save_db()
            kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 Qayta Uchish", callback_data="prep_aviator"))
            try: bot.edit_message_text(f"💥 *BOOM! Samolyot x{cp} da portlab ketdi!*", chat_id, message_id, parse_mode="Markdown", reply_markup=kb)
            except: pass
            break
            
        current_payout = int(ag["bet"] * ag["current_win"])
        kb = types.InlineKeyboardMarkup()
        if not ag["auto_co"]:
            kb.add(types.InlineKeyboardButton(f"🛑 CASHOUT ({current_payout})", callback_data="av_cashout_manual"))
        else:
            kb.add(types.InlineKeyboardButton(f"🎯 Auto-CO faol: x{ag['auto_co']}", callback_data="lock"))
        try: bot.edit_message_text(f"✈️ *AVIATOR LIVE*\n\n📈 Koeffitsiyent: *x{ag['current_win']}* 🔥\n💰 Kutilayotgan yutuq: {current_payout} so'm", chat_id, message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

app = Flask(__name__)
@app.route('/')
def home(): return "Mines-v9-Active"

def keep_alive():
    while True:
        time.sleep(150)
        try: urllib.request.urlopen(RENDER_URL)
        except: pass

if __name__ == '__main__':
    load_db()
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))), daemon=True).start(
