import os
import sys
import json
import random
import time
import urllib.request  # Uyg'otib turish (Ping) uchun kerak
from flask import Flask
from threading import Thread

# Kutubxonalarni Render'da toza o'rnatish
try:
    import telebot
    from telebot import types
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyTelegramBotAPI==4.26.0", "flask==3.0.2"])
    import telebot
    from telebot import types

# --- ASOSIY SOZLAMALAR ---
TOKEN = "8691200742:AAHWVQwjNLXHTuYBU3sI9TdroKMcZZ0C0aA"
ADMIN_ID = 8086545587
DATA_FILE = "mega_games_bot_db.json"
# RENDER_URL — Botingiz uxlab qolmasligi uchun o'zining Render havolasi
RENDER_URL = "https://mafia-bot-1-cfws.onrender.com" 

bot = telebot.TeleBot(TOKEN)
DB = {"users": {}, "settings": {"next_aviator": None, "aviator_history": [2.34, 1.55, 4.12, 1.22, 3.05]}}
APPLE_COEFFS = [1.23, 1.54, 1.93, 2.41, 3.02, 4.02, 5.70, 8.55, 13.43, 20.15, 30.22, 45.33, 69.48]

def load_db():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                DB["users"] = {int(k): v for k, v in d.get("users", {}).items()}
                DB["settings"] = d.get("settings", {})
                if "aviator_history" not in DB["settings"]: DB["settings"]["aviator_history"] = [2.34, 1.55, 4.12, 1.22, 3.05]
        except: pass

def save_db():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f: 
            json.dump({"users": {str(k): v for k, v in DB["users"].items()}, "settings": DB["settings"]}, f, indent=4, ensure_ascii=False)
    except: pass

def check_user(uid, name="Foydalanuvchi"):
    if uid not in DB["users"]:
        DB["users"][uid] = {"name": name, "balance": 10000, "tickets": 5, "apple_game": None, "aviator_game": None, "state": None, "target_user": None}
        save_db()
    u = DB["users"][uid]
    for k in ["apple_game", "aviator_game", "state", "target_user"]:
        if k not in u: u[k] = None
    return u

# --- KLAVIATURALAR ---
def get_main_keyboard(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🍏 Apple of Fortune", callback_data="prep_apple"),
        types.InlineKeyboardButton("🚀 Aviator (Real-Time)", callback_data="prep_aviator")
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

def get_admin_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📈 Aviator x2.00", callback_data="ad_setav_2"),
        types.InlineKeyboardButton("📈 Aviator x5.00", callback_data="ad_setav_5"),
        types.InlineKeyboardButton("📈 Aviator x10.00", callback_data="ad_setav_10"),
        types.InlineKeyboardButton("🎲 Avtomatik (Auto)", callback_data="ad_setav_rand")
    )
    kb.add(
        types.InlineKeyboardButton("💰 Pul Berish", callback_data="ad_give_money"),
        types.InlineKeyboardButton("🎫 Chipta Berish", callback_data="ad_give_ticket")
    )
    kb.add(types.InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="to_main"))
    return kb

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    ud = check_user(uid, message.from_user.first_name)
    ud["state"] = None
    ud["apple_game"] = None
    ud["aviator_game"] = None
    save_db()
    
    txt = (
        f"👑 *SHOX SUPREME PLATFORMA v7.5*\n\n"
        f"💵 *Balans:* {ud['balance']} so'm\n"
        f"🎫 *Chiptalar:* {ud['tickets']} ta\n\n"
        f"🎁 _Chiptangiz bo'lsa, o'yinlarda 4 000 so'mlik urinish tekin beriladi!_"
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
        save_db()
        txt = (
            f"👑 *SHOX SUPREME PLATFORMA v7.5*\n\n"
            f"💵 *Balans:* {ud['balance']} so'm\n"
            f"🎫 *Chiptalar:* {ud['tickets']} ta\n\n"
            f"🎁 _Chiptangiz bo'lsa, o'yinlarda 4 000 so'mlik urinish tekin beriladi!_"
        )
        try: bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard(uid))
        except: pass

    # --- ADMIN PANEL ---
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
        try: bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_admin_keyboard())
        except: pass

    elif call.data.startswith("ad_setav_") and uid == ADMIN_ID:
        mode = call.data.split("_")[2]
        DB["settings"]["next_aviator"] = None if mode == "rand" else float(mode)
        save_db()
        bot.answer_callback_query(call.id, f"Sozlama saqlandi!")
        callback_handler(call)

    elif call.data in ["ad_give_money", "ad_give_ticket"] and uid == ADMIN_ID:
        ud["state"] = f"admin_expect_id_{call.data.split('_')[2]}"
        save_db()
        try: bot.edit_message_text("👤 Foydalanuvchi *ID raqamini* yozib yuboring:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except: pass

    # --- SOTIB OLISH ---
    elif call.data in ["b_ticket_1", "b_ticket_10"]:
        cost, tix = (4000, 1) if call.data == "b_ticket_1" else (30000, 10)
        if ud["balance"] < cost:
            bot.answer_callback_query(call.id, "Mablag' yetarli emas!")
            return
        ud["balance"] -= cost
        ud["tickets"] += tix
        save_db()
        bot.answer_callback_query(call.id, f"Sotib olindi! +{tix}")
        callback_handler(call)

    # --- APPLE OF FORTUNE ---
    elif call.data == "prep_apple":
        if ud["apple_game"] or ud["aviator_game"]: return
        if ud["tickets"] > 0:
            ud["tickets"] -= 1
            save_db()
            start_apple_game(call.message, ud, 4000, uid, is_ticket=True)
        else:
            ud["state"] = "input_apple_bet"
            save_db()
            kb = types.InlineKeyboardMarkup()
            kb.row(types.InlineKeyboardButton("💵 2 000", callback_data="q_ap_2000"), types.InlineKeyboardButton("💵 5 000", callback_data="q_ap_5000"), types.InlineKeyboardButton("💵 10 000", callback_data="q_ap_10000"))
            kb.add(types.InlineKeyboardButton("⬅️ Ortga", callback_data="to_main"))
            try: bot.edit_message_text(f"🍏 *APPLE OF FORTUNE*\n\nBalans: *{ud['balance']}* so'm\nSummani tanlang:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
            except: pass

    elif call.data.startswith("q_ap_"):
        if ud["apple_game"]: return
        bet = int(call.data.split("_")[2])
        if ud["balance"] < bet: return
        start_apple_game(call.message, ud, bet, uid)

    elif call.data.startswith("ap_select_"):
        ag = ud.get("apple_game")
        if not ag: return
        idx = int(call.data.split("_")[2])
        if ag["grid"][ag["current_row"]][idx] == "bad":
            ud["apple_game"] = None
            save_db()
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🍏 Qayta o'ynash", callback_data="prep_apple"))
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
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("⬅️ Menyu", callback_data="to_main"))
            try: bot.edit_message_text(f"👑 *JACKPOT x69.48!* \n💰 +{ag['payout']} so'm!", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
            except: pass
            return
        show_apple(call.message, ud, (uid == ADMIN_ID))

    elif call.data == "ap_cashout" and ud.get("apple_game"):
        ud["balance"] += ud["apple_game"]["payout"]
        ud["apple_game"] = None
        save_db()
        callback_handler(call)

    # --- AVIATOR REAL-TIME ---
    elif call.data == "prep_aviator":
        if ud["apple_game"] or ud["aviator_game"]: return
        if ud["tickets"] > 0:
            ud["tickets"] -= 1
            save_db()
            start_aviator_game(call.message, ud, 4000, uid, is_ticket=True)
        else:
            ud["state"] = "input_aviator_bet"
            save_db()
            kb = types.InlineKeyboardMarkup()
            kb.row(types.InlineKeyboardButton("💵 2 000", callback_data="q_av_2000"), types.InlineKeyboardButton("💵 5 000", callback_data="q_av_5000"), types.InlineKeyboardButton("💵 10 000", callback_data="q_av_10000"))
            kb.add(types.InlineKeyboardButton("⬅️ Ortga", callback_data="to_main"))
            try: bot.edit_message_text(f"🚀 *AVIATOR REAL-TIME*\n\nBalans: *{ud['balance']}* so'm\nTikish summasini tanlang:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
            except: pass

    elif call.data.startswith("q_av_"):
        if ud["aviator_game"]: return
        bet = int(call.data.split("_")[2])
        if ud["balance"] < bet: return
        start_aviator_game(call.message, ud, bet, uid)

    elif call.data == "av_realtime_cashout":
        ag = ud.get("aviator_game")
        if not ag or ag["status"] != "flying": return
        ag["status"] = "cashout"
        win = int(ag["bet"] * ag["current_win"])
        ud["balance"] += win
        ud["aviator_game"] = None
        save_db()
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🚀 Qayta Uchish", callback_data="prep_aviator"))
        try: bot.edit_message_text(f"💰 *CASHOUT DONE!*\n📈 Koeffitsiyent: *x{ag['current_win']}*\n💰 Balansga qo'shildi: +{win} so'm!", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

# --- O'YINLAR LOGIKASI ---
def start_apple_game(message_obj, ud, bet, uid, is_ticket=False):
    if not is_ticket: ud["balance"] -= bet
    grid = []
    for r in range(13):
        items = ["good"] * 5
        bad = 1 if r < 4 else 2 if r < 8 else 3 if r < 11 else 4
        for bi in random.sample(range(5), bad): items[bi] = "bad"
        grid.append(items)
    ud["apple_game"] = {"grid": grid, "current_row": 0, "bet": bet, "payout": bet}
    ud["state"] = None
    save_db()
    show_apple(message_obj, ud, (uid == ADMIN_ID))

def show_apple(message_obj, ud, is_admin):
    ag = ud["apple_game"]
    crow = ag["current_row"]
    kb = types.InlineKeyboardMarkup(row_width=6)
    for ri in range(12, -1, -1):
        row_btns = [types.InlineKeyboardButton(f"x{APPLE_COEFFS[ri]}", callback_data="lock")]
        for ci in range(5):
            if ri < crow: row_btns.append(types.InlineKeyboardButton("🍏", callback_data="lock"))
            elif ri == crow:
                lbl = "🍏" if (is_admin and ag["grid"][ri][ci] == "good") else "🍎" if (is_admin and ag["grid"][ri][ci] == "bad") else "🟫"
                row_btns.append(types.InlineKeyboardButton(lbl, callback_data=f"ap_select_{ci}"))
            else: row_btns.append(types.InlineKeyboardButton("🔒", callback_data="lock"))
        kb.row(*row_btns)
    if crow > 0: kb.add(types.InlineKeyboardButton(f"💰 Naqdlashtirish ({ag['payout']})", callback_data="ap_cashout"))
    kb.add(types.InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main"))
    try: bot.edit_message_text(f"🍏 *APPLE OF FORTUNE*\n\nMavjud yutuq: *{ag['payout']}* so'm", message_obj.chat.id, message_obj.message_id, parse_mode="Markdown", reply_markup=kb)
    except: pass

def start_aviator_game(message_obj, ud, bet, uid, is_ticket=False):
    if not is_ticket: ud["balance"] -= bet
    crash = DB["settings"].get("next_aviator") if DB["settings"].get("next_aviator") else round(random.uniform(1.15, 7.0), 2)
    DB["settings"]["next_aviator"] = None
    ud["aviator_game"] = {"current_win": 1.0, "crash": crash, "bet": bet, "status": "flying"}
    ud["state"] = None
    save_db()
    Thread(target=run_realtime_aviator, args=(message_obj.chat.id, message_obj.message_id, uid), daemon=True).start()

def run_realtime_aviator(chat_id, message_id, uid):
    while True:
        time.sleep(0.2)  # HAR 0.2 SONIYADA JONLI UCHISH REAL-TIME
        ud = DB["users"].get(uid)
        if not ud or not ud.get("aviator_game") or ud["aviator_game"]["status"] != "flying": break
        ag = ud["aviator_game"]
        
        step = random.uniform(0.04, 0.08) if ag["current_win"] < 3.0 else random.uniform(0.12, 0.25)
        ag["current_win"] = round(ag["current_win"] + step, 2)
        
        if ag["current_win"] >= ag["crash"]:
            cp = ag["crash"]
            ud["aviator_game"] = None
            DB["settings"]["aviator_history"].append(cp)
            save_db()
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🚀 Qayta Parvoz", callback_data="prep_aviator"))
            try: bot.edit_message_text(f"💥 *BOOM! Samolyot x{cp} da portladi!*", chat_id, message_id, parse_mode="Markdown", reply_markup=kb)
            except: pass
            break
            
        save_db()
        current_payout = int(ag["bet"] * ag["current_win"])
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(f"🛑 CASHOUT ({current_payout})", callback_data="av_realtime_cashout"))
        
        cheat = f" 🕵️‍♂️ `[PORTLASH: x{ag['crash']}]`" if uid == ADMIN_ID else ""
        
        try: bot.edit_message_text(f"✈️ *AVIATOR LIVE*{cheat}\n\n📈 Koeffitsiyent: *x{ag['current_win']}* 🔥\n💰 Naqd yutuq: {current_payout} so'm", chat_id, message_id, parse_mode="Markdown", reply_markup=kb)
        except: pass

# --- UYQUGA QARSHI DORI (ANTI-SLEEP PINGER) ---
def keep_alive():
    while True:
        time.sleep(300)  # Har 5 daqiqada (300 soniya) ishlaydi
        try:
            # Render veb-sahifasiga so'rov yuborib turadi, bu serverni uyg'oq saqlaydi
            urllib.request.urlopen(RENDER_URL)
            print("🚀 Anti-Sleep: Server muvaffaqiyatli uyg'otildi!")
        except Exception as e:
            print(f"⚠️ Anti-Sleep xatosi: {e}")

@bot.message_handler(func=lambda msg: True)
def text_handler(msg):
    uid = msg.from_user.id
    ud = check_user(uid)
    if not ud["state"]: return
    
    if ud["state"].startswith("admin_expect_id_"):
        mode = ud["state"].split("_")[3]
        try:
            target_id = int(msg.text.strip())
            if target_id in DB["users"]:
                ud["target_user"] = target_id
                ud["state"] = f"admin_expect_val_{mode}"
                save_db()
                bot.reply_to(msg, "Qiymatni kiriting:")
            else: bot.reply_to(msg, "❌ ID topilmadi.")
        except: ud["state"] = None; save_db()
        return

    if ud["state"].startswith("admin_expect_val_"):
        mode = ud["state"].split("_")[3]
        try:
            val = int(msg.text.strip())
            t_id = ud["target_user"]
            if mode == "money": DB["users"][t_id]["balance"] += val
            elif mode == "ticket": DB["users"][t_id]["tickets"] += val
            save_db()
            bot.reply_to(msg, "✅ Bajarildi!")
        except: pass
        ud["state"] = None; ud["target_user"] = None; save_db()
        return

    try:
        bet = int(msg.text.strip())
        if bet < 1000 or bet > 10000 or ud["balance"] < bet: return
    except: return
    
    st_msg = bot.send_message(msg.chat.id, "🔄...")
    if ud["state"] == "input_apple_bet": start_apple_game(st_msg, ud, bet, uid)
    elif ud["state"] == "input_aviator_bet": start_aviator_game(st_msg, ud, bet, uid)

app = Flask(__name__)
@app.route('/')
def home(): return "Mening botim faol!"

def main():
    load_db()
    # Flask serverini orqa fonda ishga tushirish
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    # Uyquga qarshi maxsus pingerni alohida oqimda yoqish
    Thread(target=keep_alive, daemon=True).start()
    bot.infinity_polling(skip_pending=True)

if __name__ == '__main__':
    main()
        
