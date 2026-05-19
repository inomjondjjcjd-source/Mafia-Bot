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

# Pullar va balanslar o'chib ketmasligi uchun xavfsiz onlayn JSON baza
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
            print("🚀 Pullar onlayn bazadan muvaffaqiyatli yuklandi!")
    except Exception as e:
        print(f"⚠️ Zaxira xotirasi ishga tushdi: {e}")

def save_db():
    try:
        serializable_users = {str(k): v for k, v in DB["users"].items()}
        payload = json.dumps({"users": serializable_users, "settings": DB["settings"]}).encode("utf-8")
        req = urllib.request.Request(KVDB_URL, data=payload, method="PUT", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            pass
    except Exception as e:
        print(f"⚠️ Saqlashda xato: {e}")

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
    for field in ["apple_game", "aviator_game", "mines_game", "state", "target_user", "temp_bet"]:
        if field not in u: u[field] = None
    return u

def get_main_keyboard(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🍏 Apple of Fortune", callback_data="prep_apple"),
        types.InlineKeyboardButton("🚀 Aviator (VIP)", callback_data="prep_aviator")
    )
    kb.add(types.InlineKeyboardButton("💣 MINES (YANGI x100)", callback_data="prep_mines"))
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

def get_mines_coeff(mines_count, opened_count):
    if opened_count == 0: return 1.0
    total_cells = 30
    coeff = 1.0
    for i in range(opened_count):
        safe_cells_left = total_cells - mines_count - i
        total_cells_left = total_cells - i
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
        f"👑 *SHOX SUPREME PLATFORMA v8.0*\n\n"
        f"💵 *Balans:* {ud['balance']} so'm\n"
        f"🎫 *Chiptalar:* {ud['tickets']} ta\n\n"
        f"💣 *Mines o'yini yangilandi! Inline tugmalar qo'shildi.*"
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
        txt = f"👑 *SHOX SUPREME PLATFORMA v8.0*\n\n💵 *Balans:* {ud['balance']} so'm\n🎫 *Chiptalar:* {ud['tickets']} ta"
        try: bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard(uid))
        except: pass

    elif call.data == "prep_mines":
        ud["state"] = "mines_expect_bet"
        save_db()
        kb = types.InlineKeyboardMarkup(row_width=3)
        kb.add(
            types.InlineKeyboardButton("2000 so'm", callback_data="m_bet_2000"),
            types.InlineKeyboardButton("3000 so'm", callback_data="m_bet_3000"),
            types.InlineKeyboardButton("5000 so'm", callback_data="m_bet_5000")
        )
        kb.add(
            types.InlineKeyboardButton("8000 so'm", callback_data="m_bet_8000"),
            types.InlineKeyboardButton("10000 so'm", callback_data="m_bet_10000")
        )
        kb.add(types.InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main"))
        try: bot.edit_message_text("💣 *MINES O'YINI*\n\nTikish summasini tanlang yoki o'zingiz yozing:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

    elif call.data.startswith("m_bet_"):
        bet = int(call.data.split("_")[2])
        if bet > ud["balance"]:
            bot.answer_callback_query(call.id, "❌ Balansda yetarli mablag' yo'q!", show_alert=True)
            return
        ud["temp_bet"] = bet
        ud["state"] = "mines_expect_bombs"
        save_db()
        
        kb = types.InlineKeyboardMarkup(row_width=3)
        kb.add(*[types.InlineKeyboardButton(f"💣 {b}", callback_data=f"m_bomb_{b}") for b in [1, 2, 3, 4, 7, 10, 15, 20, 24]])
        kb.add(types.InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main"))
        try: bot.edit_message_text(f"💣 Tikilgan summa: *{bet} so'm*\n\nO'yinda nechta bomba bo'lsin? Tanlang:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

    elif call.data.startswith("m_bomb_"):
        bombs = int(call.data.split("_")[2])
        bet = ud.get("temp_bet")
        if not bet or bet > ud["balance"]: return
        
        ud["balance"] -= bet
        mines_positions = random.sample(range(30), bombs)
        ud["mines_game"] = {"bet": bet, "mines_count": bombs, "mines": mines_positions, "opened": [], "current_kf": 1.0, "payout": bet, "status": "playing"}
        ud["state"] = None
        ud["temp_bet"] = None
        save_db()
        show_mines_board(call.message, ud)

    elif call.data.startswith("mine_open_"):
        mg = ud.get("mines_game")
        if not mg or mg["status"] != "playing": return
        idx = int(call.data.split("_")[2])
        if idx in mg["opened"]: return
        
        if idx in mg["mines"]:
            mg["status"] = "lost"
            save_db()
            show_mines_board(call.message, ud, lost=True)
            return
            
        mg["opened"].append(idx)
        mg["current_kf"] = get_mines_coeff(mg["mines_count"], len(mg["opened"]))
        mg["payout"] = int(mg["bet"] * mg["current_kf"])
        save_db()
        
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

    elif call.data == "admin_dashboard" and uid == ADMIN_ID:
        total_users = len(DB["users"])
        total_balance = sum([u.get("balance", 0) for u in DB["users"].values()])
        txt = f"👑 *ADMIN PANEL*\n\n👥 Foydalanuvchilar: {total_users} ta\n💰 Jami balans: {total_balance} so'm"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="to_main"))
        try: bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

    elif call.data in ["b_ticket_1", "b_ticket_10"]:
        cost, tix = (4000, 1) if call.data == "b_ticket_1" else (30000, 10)
        if ud["balance"] < cost: return
        ud["balance"] -= cost
        ud["tickets"] += tix
        save_db()
        bot.answer_callback_query(call.id, f"Muvaffaqiyatli xarid! +{tix}")
        txt = f"👑 *SHOX SUPREME PLATFORMA v8.0*\n\n💵 *Balans:* {ud['balance']} so'm\n🎫 *Chiptalar:* {ud['tickets']} ta"
        try: bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard(uid))
        except: pass

    elif call.data == "prep_apple":
        ud["state"] = "input_apple_bet"
        save_db()
        try: bot.edit_message_text("🍏 *APPLE OF FORTUNE*\n\nTikish summasini yozing:", call.message.chat.id, call.message.message_id)
        except: pass

    elif call.data == "prep_aviator":
        ud["state"] = "input_aviator_bet"
        save_db()
        try: bot.edit_message_text("🚀 *AVIATOR REAL-TIME*\n\nTikish summasini kiriting:", call.message.chat.id, call.message.message_id)
        except: pass

def show_mines_board(message_obj, ud, lost=False, won=False):
    uid = ud.get("uid") or message_obj.chat.id
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
                # 👑 Sening so'roving bo'yicha: Faqat sen (Admin) uchun minalar yashirincha ko'rinib turadi, xuddi cheatdek!
                if uid == ADMIN_ID:
                    if i in mg["mines"]:
                        btns.append(types.InlineKeyboardButton("🟢", callback_data=f"mine_open_{i}")) # Mina bor joy yashil olma/belgi bo'lib senga ko'rinadi (unga bosma!)
                    else:
                        btns.append(types.InlineKeyboardButton("❓", callback_data=f"mine_open_{i}")) # Toza joy oddiy ko'rinadi
                else:
                    # Oddiy o'yinchilar uchun hammasi yopiq va bir xil
                    btns.append(types.InlineKeyboardButton("❓", callback_data=f"mine_open_{i}"))
                    
    kb.add(*btns)
    
    if not lost and not won:
        if len(mg["opened"]) > 0:
            kb.add(types.InlineKeyboardButton(f"💰 Naqdlashtirish ({mg['payout']} so'm)", callback_data="mines_cashout"))
        kb.add(types.InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main"))
    else:
        kb.add(types.InlineKeyboardButton("🔄 Yangi O'yin", callback_data="prep_mines"), types.InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="to_main"))

    if lost: txt = f"💥 *MAG'LUBIYAT!*\n💣 Bombaga duch keldingiz.\n💸 -{mg['bet']} so'm."
    elif won: txt = f"👑 *G'ALABA!*\n📈 Koeffitsiyent: *x{mg['current_kf']}*\n💰 Sof yutuq: +{mg['payout']} so'm!"
    else: txt = f"💣 *MINES (30 katak)*\n\n💵 Tikilgan: *{mg['bet']}* so'm | Minalar: *{mg['mines_count']}*\n📈 Koeffitsiyent: *x{mg['current_kf']}*\n💰 Naqd Yutuq: *{mg['payout']}* so'm"
    
    try: bot.edit_message_text(txt, message_obj.chat.id, message_obj.message_id, parse_mode="Markdown", reply_markup=kb)
    except: pass

@bot.message_handler(func=lambda msg: True)
def text_handler(msg):
    uid = msg.from_user.id
    ud = check_user(uid)
    if not ud["state"]: return
    
    # Matn orqali ham tikish yozilsa, xato bermay ishlayveradi
    if ud["state"] == "mines_expect_bet":
        try:
            bet = int(msg.text.strip())
            if bet < 1000 or bet > ud["balance"]:
                bot.reply_to(msg, "❌ Balans yetarli emas yoki summa noto'g'ri!")
                return
            ud["temp_bet"] = bet
            ud["state"] = "mines_expect_bombs"
            save_db()
            
            kb = types.InlineKeyboardMarkup(row_width=3)
            kb.add(*[types.InlineKeyboardButton(f"💣 {b}", callback_data=f"m_bomb_{b}") for b in [1, 2, 3, 4, 7, 10, 15, 20, 24]])
            bot.reply_to(msg, "💣 O'yinda nechta bomba bo'lsin? Tanlang:", reply_markup=kb)
        except: ud["state"] = None; save_db()
        return

app = Flask(__name__)
@app.route('/')
def home(): return "OK"

def keep_alive():
    while True:
        time.sleep(150)
        try: urllib.request.urlopen(RENDER_URL)
        except: pass

if __name__ == '__main__':
    load_db()
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    Thread(target=keep_alive, daemon=True).start()
    bot.infinity_polling(skip_pending=True)
        
