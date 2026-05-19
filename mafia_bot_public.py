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
TOKEN = "8691200742:AAHWVQwjNLXHTuYBU3sI9TdroKMcZZ0C0aA"
ADMIN_ID = 8086545587
RENDER_URL = "https://mafia-bot-1-cfws.onrender.com"

bot = telebot.TeleBot(TOKEN)

# Render tekin xizmatida pullar mutloq o'chmasligi uchun xavfsiz onlayn JSON baza tizimi
# Har bir bot uchun alohida toza va ishlaydigan kalit yaratildi
KVDB_URL = "https://kvdb.io/MN86yM86yM86yM86yM86yM/shox_supreme_v8_db"

DB = {
    "users": {},
    "settings": {
        "next_aviator": None,
        "aviator_history": [2.34, 1.55, 4.12, 1.22, 3.05]
    }
}

APPLE_COEFFS = [1.23, 1.54, 1.93, 2.41, 3.02, 4.02, 5.70, 8.55, 13.43, 20.15, 30.22, 45.33, 69.48]

# --- BAZANI INTERNETGA SAQLASH VA YUKLASH ---
def load_db():
    global DB
    try:
        req = urllib.request.Request(KVDB_URL, method="GET")
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode("utf-8"))
            if "users" in data:
                DB["users"] = {int(k): v for k, v in data["users"].items()}
            if "settings" in data:
                DB["settings"] = data["settings"]
            print("🚀 Pullar va ma'lumotlar onlayn bazadan muvaffaqiyatli yuklandi!")
    except Exception as e:
        print(f"⚠️ Onlayn bazada xato yoki u bo'sh (Zaxira ishlatiladi): {e}")

def save_db():
    try:
        serializable_users = {str(k): v for k, v in DB["users"].items()}
        payload = json.dumps({"users": serializable_users, "settings": DB["settings"]}).encode("utf-8")
        req = urllib.request.Request(KVDB_URL, data=payload, method="PUT", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            pass
    except Exception as e:
        print(f"⚠️ Onlayn bazaga saqlashda xato: {e}")

def check_user(uid, name="Foydalanuvchi"):
    if uid not in DB["users"]:
        DB["users"][uid] = {
            "name": name,
            "balance": 10000,
            "tickets": 5,
            "apple_game": None,
            "aviator_game": None,
            "mines_game": None,
            "state": None,
            "target_user": None,
            "temp_bet": None
        }
        save_db()
    u = DB["users"][uid]
    # Yangi maydonlar yo'qolib qolmasligi uchun zaxira tekshirish
    for field in ["apple_game", "aviator_game", "mines_game", "state", "target_user", "temp_bet"]:
        if field not in u:
            u[field] = None
    return u

def get_main_keyboard(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🍏 Apple of Fortune", callback_data="prep_apple"),
        types.InlineKeyboardButton("🚀 Aviator (Real-Time)", callback_data="prep_aviator")
    )
    kb.add(
        types.InlineKeyboardButton("💣 MINES (YANGI x100)", callback_data="prep_mines")
    )
    kb.add(
        types.InlineKeyboardButton("💸 Pul Kiritish", url=f"tg://user?id={ADMIN_ID}"),
        types.InlineKeyboardButton("💳 Pul Yechish", url=f"tg://user?id={ADMIN_ID}")
    )
    kb.add(
        types.InlineKeyboardButton("🎫 1 chipta (4k)", callback_data="b_ticket_1"),
        types.InlineKeyboardButton("🎁 10 chipta (30k)", callback_data="b_ticket_10")
    )
    if uid == ADMIN_ID:
        kb.add(types.InlineKeyboardButton("👑 Admin Panel", callback_data="admin_dashboard"))
    return kb

# --- MINES MATHEMATICS (MUKAMMAL KF TIZIMI) ---
def get_mines_coeff(mines_count, opened_count):
    # Kombinatorika asosida minalar ko'payganda kf geosmetrik o'sadi (Max x100+)
    if opened_count == 0:
        return 1.0
    total_cells = 30
    coeff = 1.0
    for i in range(opened_count):
        safe_cells_left = total_cells - mines_count - i
        total_cells_left = total_cells - i
        if safe_cells_left <= 0:
            break
        coeff *= (total_cells_left / safe_cells_left)
    return round(coeff * 0.95, 2) # 5% platforma haqi

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    ud = check_user(uid, message.from_user.first_name)
    ud["state"] = None
    ud["apple_game"] = None
    ud["aviator_game"] = None
    ud["mines_game"] = None
    save_db()
    
    txt = (
        f"👑 *SHOX SUPREME PLATFORMA v8.0*\n\n"
        f"💵 *Balans:* {ud['balance']} so'm\n"
        f"🎫 *Chiptalar:* {ud['tickets']} ta\n\n"
        f"💣 *YANGILIK:* Strategik va daromadli MINES o'yini qo'shildi!"
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
        txt = (
            f"👑 *SHOX SUPREME PLATFORMA v8.0*\n\n"
            f"💵 *Balans:* {ud['balance']} so'm\n"
            f"🎫 *Chiptalar:* {ud['tickets']} ta\n"
        )
        try: bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard(uid))
        except: pass

    # --- MINES O'YINI LOGIKASI ---
    elif call.data == "prep_mines":
        if ud["apple_game"] or ud["aviator_game"] or ud["mines_game"]: return
        ud["state"] = "mines_expect_bet"
        save_db()
        try: bot.edit_message_text("💣 *MINES (30 ta Katak)*\n\nTikish summasini kiriting (Masalan: `5000`):", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except: pass

    elif call.data.startswith("mine_open_"):
        mg = ud.get("mines_game")
        if not mg or mg["status"] != "playing": return
        idx = int(call.data.split("_")[2])
        
        if idx in mg["opened"]: return
        
        # Agar bombaga bossa - Mag'lubiyat
        if idx in mg["mines"]:
            mg["status"] = "lost"
            save_db()
            show_mines_board(call.message, ud, lost=True)
            return
            
        mg["opened"].append(idx)
        mg["current_kf"] = get_mines_coeff(mg["mines_count"], len(mg["opened"]))
        mg["payout"] = int(mg["bet"] * mg["current_kf"])
        save_db()
        
        # Maksimal hamma xavfsiz katak ochilsa - Avtomatik g'alaba
        if len(mg["opened"]) == (30 - mg["mines_count"]):
            ud["balance"] += mg["payout"]
            mg["status"] = "won"
            save_db()
            show_mines_board(call.message, ud, won=True)
            return
            
        show_mines_board(call.message, ud)

    elif call.data == "mines_cashout":
        mg = ud.get("mines_game")
        if not mg or mg["status"] != "playing" or len(mg["opened"]) == 0: return
        
        ud["balance"] += mg["payout"]
        mg["status"] = "won"
        save_db()
        show_mines_board(call.message, ud, won=True)

    # --- ESKI O'YINLAR VA ADMIN PANEL ---
    elif call.data == "admin_dashboard" and uid == ADMIN_ID:
        total_users = len(DB["users"])
        total_balance = sum([u.get("balance", 0) for u in DB["users"].values()])
        next_av = DB["settings"].get("next_aviator", "Auto")
        txt = (
            f"👑 *ADMIN PANEL*\n\n"
            f"👥 Foydalanuvchilar: {total_users} ta\n"
            f"💰 Jami balans: {total_balance} so'm\n"
            f"🚀 Keyingi Aviator: `x{next_av}`"
        )
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("📈 Aviator x2.00", callback_data="ad_setav_2"),
            types.InlineKeyboardButton("📈 Aviator x5.00", callback_data="ad_setav_5"),
            types.InlineKeyboardButton("🎲 Avtomatik (Auto)", callback_data="ad_setav_rand")
        )
        kb.add(types.InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="to_main"))
        try: bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

    elif call.data.startswith("ad_setav_") and uid == ADMIN_ID:
        mode = call.data.split("_")[2]
        DB["settings"]["next_aviator"] = None if mode == "rand" else float(mode)
        save_db()
        bot.answer_callback_query(call.id, "Aviator koeffitsiyenti o'rnatildi!")

    elif call.data in ["b_ticket_1", "b_ticket_10"]:
        cost, tix = (4000, 1) if call.data == "b_ticket_1" else (30000, 10)
        if ud["balance"] < cost:
            bot.answer_callback_query(call.id, "Mablag' yetarli emas!")
            return
        ud["balance"] -= cost
        ud["tickets"] += tix
        save_db()
        bot.answer_callback_query(call.id, f"Muvaffaqiyatli xarid! +{tix}")
        txt = f"👑 *SHOX SUPREME PLATFORMA v8.0*\n\n💵 *Balans:* {ud['balance']} so'm\n🎫 *Chiptalar:* {ud['tickets']} ta"
        try: bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard(uid))
        except: pass

    elif call.data == "prep_apple":
        if ud["apple_game"] or ud["aviator_game"] or ud["mines_game"]: return
        ud["state"] = "input_apple_bet"
        save_db()
        try: bot.edit_message_text("🍏 *APPLE OF FORTUNE*\n\nTikish summasini yozing:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except: pass

    elif call.data.startswith("ap_select_"):
        ag = ud.get("apple_game")
        if not ag: return
        idx = int(call.data.split("_")[2])
        if ag["grid"][ag["current_row"]][idx] == "bad":
            ud["apple_game"] = None
            save_db()
            kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🍏 Qayta o'ynash", callback_data="prep_apple"))
            try: bot.edit_message_text("💀 *Chirigan olma! Mag'lubiyat.*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
            except: pass
            return
        ag["payout"] = int(ag["bet"] * APPLE_COEFFS[ag["current_row"]])
        ag["current_row"] += 1
        save_db()
        if ag["current_row"] == 13:
            ud["balance"] += ag["payout"]
            ud["apple_game"] = None
            save_db()
            try: bot.edit_message_text(f"👑 *JACKPOT!* \n💰 +{ag['payout']} so'm!", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard(uid))
            except: pass
            return
        show_apple(call.message, ud)

    elif call.data == "ap_cashout" and ud.get("apple_game"):
        ud["balance"] += ud["apple_game"]["payout"]
        ud["apple_game"] = None
        save_db()
        try: bot.edit_message_text("💰 Pul yechib olindi!", call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard(uid))
        except: pass

    elif call.data == "prep_aviator":
        if ud["apple_game"] or ud["aviator_game"] or ud["mines_game"]: return
        ud["state"] = "input_aviator_bet"
        save_db()
        try: bot.edit_message_text("🚀 *AVIATOR REAL-TIME*\n\nTikish summasini kiriting:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except: pass

    elif call.data == "av_realtime_cashout":
        ag = ud.get("aviator_game")
        if not ag or ag["status"] != "flying": return
        ag["status"] = "cashout"
        win = int(ag["bet"] * ag["current_win"])
        ud["balance"] += win
        ud["aviator_game"] = None
        save_db()
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 Qayta Uchish", callback_data="prep_aviator"))
        try: bot.edit_message_text(f"💰 *CASHOUT DONE!*\n📈 Koeffitsiyent: *x{ag['current_win']}*\n💰 Yutuq: +{win} so'm!", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

# --- MINES TAXTASINI CHIZISH ---
def show_mines_board(message_obj, ud, lost=False, won=False):
    mg = ud["mines_game"]
    kb = types.InlineKeyboardMarkup(row_width=5) # 5 ta ustun, 6 ta qator = 30 ta katak
    
    btns = []
    for i in range(30):
        if lost:
            if i in mg["mines"]:
                btns.append(types.InlineKeyboardButton("💥", callback_data="lock"))
            elif i in mg["opened"]:
                btns.append(types.InlineKeyboardButton("💎", callback_data="lock"))
            else:
                btns.append(types.InlineKeyboardButton("⬜️", callback_data="lock"))
        elif won:
            if i in mg["mines"]:
                btns.append(types.InlineKeyboardButton("💣", callback_data="lock"))
            else:
                btns.append(types.InlineKeyboardButton("💎", callback_data="lock"))
        else:
            if i in mg["opened"]:
                btns.append(types.InlineKeyboardButton("💎", callback_data="lock"))
            else:
                btns.append(types.InlineKeyboardButton("❓", callback_data=f"mine_open_{i}"))
                
    kb.add(*btns)
    
    if not lost and not won:
        if len(mg["opened"]) > 0:
            kb.add(types.InlineKeyboardButton(f"💰 Naqdlashtirish ({mg['payout']} so'm)", callback_data="mines_cashout"))
        kb.add(types.InlineKeyboardButton("⬅️ Taslim bo'lish", callback_data="to_main"))
    else:
        kb.add(types.InlineKeyboardButton("🔄 Yangi O'yin", callback_data="prep_mines"))
        kb.add(types.InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="to_main"))

    if lost:
        txt = f"💥 *MAG'LUBIYAT!*\n💣 Bombaga duch keldingiz.\n💸 Tikilgan summa: -{mg['bet']} so'm."
    elif won:
        txt = f"👑 *G'ALABA!*\n📈 Yakuniy koeffitsiyent: *x{mg['current_kf']}*\n💰 Sof yutuq: +{mg['payout']} so'm!"
    else:
        txt = (
            f"💣 *MINES SEKTORI (30 katak)*\n\n"
            f"💵 Tikilgan: *{mg['bet']}* so'm | Minalar: *{mg['mines_count']}* ta\n"
            f"📈 Joriy Koeffitsiyent: *x{mg['current_kf']}*\n"
            f"💰 Naqd Yutuq: *{mg['payout']}* so'm\n\n"
            f"💎 _Keyingi katakni tanlang!_"
        )
        
    try: bot.edit_message_text(txt, message_obj.chat.id, message_obj.message_id, parse_mode="Markdown", reply_markup=kb)
    except: pass

def start_apple_game(message_obj, ud, bet):
    ud["balance"] -= bet
    grid = []
    for r in range(13):
        items = ["good"] * 5
        bad = 1 if r < 4 else 2 if r < 8 else 3 if r < 11 else 4
        for bi in random.sample(range(5), bad): items[bi] = "bad"
        grid.append(items)
    ud["apple_game"] = {"grid": grid, "current_row": 0, "bet": bet, "payout": bet}
    ud["state"] = None
    save_db()
    show_apple(message_obj, ud)

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

def start_aviator_game(message_obj, ud, bet):
    ud["balance"] -= bet
    crash = DB["settings"].get("next_aviator") if DB["settings"].get("next_aviator") else round(random.uniform(1.15, 5.0), 2)
    DB["settings"]["next_aviator"] = None
    ud["aviator_game"] = {"current_win": 1.0, "crash": crash, "bet": bet, "status": "flying"}
    ud["state"] = None
    save_db()
    Thread(target=run_realtime_aviator, args=(message_obj.chat.id, message_obj.message_id, message_obj.from_user.id), daemon=True).start()

def run_realtime_aviator(chat_id, message_id, uid):
    # Server qotmasligi va Render bloklamasligi uchun xavfsiz sikl algoritmi
    for _ in range(80): 
        time.sleep(0.5)
        ud = DB["users"].get(uid)
        if not ud or not ud.get("aviator_game") or ud["aviator_game"]["status"] != "flying": break
        ag = ud["aviator_game"]
        
        ag["current_win"] = round(ag["current_win"] + random.uniform(0.08, 0.15), 2)
        
        if ag["current_win"] >= ag["crash"]:
            cp = ag["crash"]
            ud["aviator_game"] = None
            save_db()
            kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 Qayta Parvoz", callback_data="prep_aviator"))
            try: bot.edit_message_text(f"💥 *BOOM! Samolyot x{cp} da portladi!*", chat_id, message_id, parse_mode="Markdown", reply_markup=kb)
            except: pass
            break
            
        current_payout = int(ag["bet"] * ag["current_win"])
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(f"🛑 CASHOUT ({current_payout})", callback_data="av_realtime_cashout"))
        try: bot.edit_message_text(f"✈️ *AVIATOR LIVE*\n\n📈 Koeffitsiyent: *x{ag['current_win']}* 🔥\n💰 Naqd yutuq: {current_payout} so'm", chat_id, message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

@bot.message_handler(func=lambda msg: True)
def text_handler(msg):
    uid = msg.from_user.id
    ud = check_user(uid)
    if not ud["state"]: return
    
    # MINES SUMMASI KIRITILGANDA
    if ud["state"] == "mines_expect_bet":
        try:
            bet = int(msg.text.strip())
            if bet < 1000 or bet > ud["balance"]:
                bot.reply_to(msg, "❌ Noto'g'ri summa kiritildi yoki balans yetarli emas!")
                return
            ud["temp_bet"] = bet
            ud["state"] = "mines_expect_bombs"
            save_db()
            bot.reply_to(msg, "💣 O'yinda nechta bomba bo'lsin? *(1 tadan 24 tagacha raqam yozing)*:")
        except:
            ud["state"] = None; save_db()
        return

    # MINES BOMBALAR SONI KIRITILGANDA
    if ud["state"] == "mines_expect_bombs":
        try:
            bombs = int(msg.text.strip())
            if bombs < 1 or bombs > 24:
                bot.reply_to(msg, "❌ Minalar soni 1 va 24 oraliqida bo'lishi shart!")
                return
            
            bet = ud["temp_bet"]
            ud["balance"] -= bet
            
            # 30 ta indeks ichidan tasodifiy minalarni joylashtirish
            mines_positions = random.sample(range(30), bombs)
            
            ud["mines_game"] = {
                "bet": bet,
                "mines_count": bombs,
                "mines": mines_positions,
                "opened": [],
                "current_kf": 1.0,
                "payout": bet,
                "status": "playing"
            }
            ud["state"] = None; ud["temp_bet"] = None
            save_db()
            
            st_msg = bot.send_message(msg.chat.id, "🔄 Mines matritsasi yuklanmoqda...")
            show_mines_board(st_msg, ud)
        except:
            ud["state"] = None; save_db()
        return

    # ESKI O'YINLARNING INPUT TIZIMI
    try:
        bet = int(msg.text.strip())
        if bet < 1000 or ud["balance"] < bet: return
    except: return
    
    st_msg = bot.send_message(msg.chat.id, "🔄...")
    if ud["state"] == "input_apple_bet": start_apple_game(st_msg, ud, bet)
    elif ud["state"] == "input_aviator_bet": start_aviator_game(st_msg, ud, bet)

# --- FLASK VEB SERVER VA ANTI-SLEEP ---
app = Flask(__name__)
@app.route('/')
def home(): return "Mines System Active"

def keep_alive():
    while True:
        time.sleep(120)
        try: urllib.request.urlopen(RENDER_URL)
        except: pa
