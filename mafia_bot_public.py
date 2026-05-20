import os, json, random, time, urllib.request, telebot
from flask import Flask
from threading import Thread
from telebot import types

TOKEN = "8691200742:AAEv-8-wixOxzlHmIU-jbMy4QHYOE1-M6QM"
ADMIN_ID = 8086545587

# ✅ TO'G'RILANDI: KVDB URL to'g'ri formatda bo'lishi kerak
# kvdb.io dan o'zingizning bucket ID'ingizni oling: https://kvdb.io
KVDB_BUCKET = "MN86yM86yM86yM86yM86yM"  # <-- Bu yerga o'z bucket ID'ingizni qo'ying
KVDB_URL = f"https://kvdb.io/{KVDB_BUCKET}/shox_bot_db"

bot = telebot.TeleBot(TOKEN)
DB = {"users": {}, "settings": {"next_aviator": None, "aviator_history": [1.4, 2.1, 3.5]}}
COEFFS = [1.23, 1.54, 1.93, 2.41, 3.02, 4.02, 5.7, 8.55, 13.43, 20.15, 30.22, 45.33, 69.48]

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
        print(f"✅ DB yuklandi: {len(DB['users'])} ta foydalanuvchi")
    except Exception as e:
        print(f"⚠️ DB yuklanmadi: {e}")

def save_db():
    try:
        payload = json.dumps({
            "users": {str(k): v for k, v in DB["users"].items()},
            "settings": DB["settings"]
        }).encode("utf-8")
        req = urllib.request.Request(
            KVDB_URL, data=payload, method="PUT",
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as e:
        print(f"⚠️ DB saqlanmadi: {e}")

def check_user(uid, name="Foydalanuvchi"):
    """
    ✅ ASOSIY TO'GRILANISH:
    Agar foydalanuvchi allaqachon mavjud bo'lsa — balansini O'ZGARTIRMAYMIZ.
    Faqat yangi foydalanuvchilarga 10000 beramiz.
    """
    uid = int(uid)
    if uid not in DB["users"]:
        # Yangi foydalanuvchi — faqat shu holda 10000 beramiz
        DB["users"][uid] = {
            "name": name,
            "balance": 10000,
            "last_bonus": 0,
            "apple_game": None,
            "aviator_game": None,
            "mines_game": None,
            "state": None,
            "temp_bet": None
        }
        save_db()
        print(f"✅ Yangi user: {uid} ({name}) — 10000 so'm berildi")
    else:
        # ✅ Mavjud foydalanuvchi — faqat yetishmayotgan fieldlarni qo'shamiz
        u = DB["users"][uid]
        changed = False
        for f in ["apple_game", "aviator_game", "mines_game", "state", "temp_bet"]:
            if f not in u:
                u[f] = None
                changed = True
        if "last_bonus" not in u:
            u["last_bonus"] = 0
            changed = True
        if changed:
            save_db()
    return DB["users"][uid]

def get_main_keyboard(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🍏 Apple of Fortune", callback_data="prep_apple"),
        types.InlineKeyboardButton("🚀 Aviator (Auto-CO)", callback_data="prep_aviator")
    )
    kb.add(
        types.InlineKeyboardButton("💣 MINES", callback_data="prep_mines"),
        types.InlineKeyboardButton("🐊 Swamp Land", callback_data="swamp_soon")
    )
    kb.add(
        types.InlineKeyboardButton("🎁 KUNDALIK BONUS", callback_data="get_daily_bonus"),
        types.InlineKeyboardButton("👑 Admin Panel" if uid == ADMIN_ID else "ℹ️ Profil",
                                   callback_data="admin_dashboard" if uid == ADMIN_ID else "to_main")
    )
    kb.add(
        types.InlineKeyboardButton("💸 Pul Kiritish", url=f"tg://user?id={ADMIN_ID}"),
        types.InlineKeyboardButton("💳 Pul Yechish", url=f"tg://user?id={ADMIN_ID}")
    )
    return kb

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    # ✅ check_user balansni o'zgartirmaydi — faqat yangi user bo'lsa 10000 beradi
    ud = check_user(uid, message.from_user.first_name)
    
    # ✅ Faqat o'yin holatini tozalaymiz, BALANSNI EMAS
    ud["state"] = None
    save_db()
    
    txt = (
        f"👑 *SHOX SUPREME PLATFORMA v10.0*\n\n"
        f"👤 *Salom, {ud['name']}!*\n"
        f"💵 *Balans:* {ud['balance']:,} so'm\n"
        f"Status: 🟢 Live"
    )
    bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=get_main_keyboard(uid))

@bot.message_handler(func=lambda m: check_user(m.from_user.id).get("state") is not None)
def handle_text(message):
    uid, text = message.from_user.id, message.text
    ud = check_user(uid)
    if uid != ADMIN_ID:
        return
    if ud["state"] == "set_kf":
        try:
            DB["settings"]["next_aviator"] = round(float(text), 2)
            save_db()
            bot.send_message(message.chat.id, f"✅ Keyingi kf *x{text}* bo'ldi!", parse_mode="Markdown")
        except:
            bot.send_message(message.chat.id, "❌ Xato son.")
    elif ud["state"] == "add_money":
        try:
            parts = text.split()
            tid, amt = int(parts[0]), int(parts[1])
            if tid in DB["users"]:
                DB["users"][tid]["balance"] += amt
                save_db()
                bot.send_message(message.chat.id, f"✅ ID {tid} ga {amt:,} so'm qo'shildi! Yangi balans: {DB['users'][tid]['balance']:,}")
            else:
                bot.send_message(message.chat.id, f"❌ ID {tid} topilmadi.")
        except:
            bot.send_message(message.chat.id, "❌ Format: `ID summa`", parse_mode="Markdown")
    elif ud["state"] == "remove_money":
        try:
            parts = text.split()
            tid, amt = int(parts[0]), int(parts[1])
            if tid in DB["users"]:
                DB["users"][tid]["balance"] = max(0, DB["users"][tid]["balance"] - amt)
                save_db()
                bot.send_message(message.chat.id, f"✅ ID {tid} dan {amt:,} so'm olindi! Yangi balans: {DB['users'][tid]['balance']:,}")
            else:
                bot.send_message(message.chat.id, f"❌ ID {tid} topilmadi.")
        except:
            bot.send_message(message.chat.id, "❌ Format: `ID summa`", parse_mode="Markdown")
    ud["state"] = None
    save_db()

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    ud = check_user(uid)

    if call.data == "to_main":
        ud["state"] = None
        ud["apple_game"] = None
        ud["aviator_game"] = None
        ud["mines_game"] = None
        save_db()
        try:
            bot.edit_message_text(
                f"👑 *SHOX SUPREME PLATFORMA v10.0*\n\n"
                f"👤 *{ud['name']}*\n"
                f"💵 *Balans:* {ud['balance']:,} so'm",
                cid, mid, parse_mode="Markdown", reply_markup=get_main_keyboard(uid)
            )
        except:
            pass

    elif call.data == "swamp_soon":
        bot.answer_callback_query(call.id, "🐊 Swamp Land o'yini yaqin orada qo'shiladi!", show_alert=True)

    elif call.data == "get_daily_bonus":
        t_now = int(time.time())
        if t_now - ud.get("last_bonus", 0) < 86400:
            remaining = 86400 - (t_now - ud.get("last_bonus", 0))
            h, m = divmod(remaining // 60, 60)
            bot.answer_callback_query(call.id, f"❌ Bonus oldinroq olindi!\n⏰ {h} soat {m} daqiqadan keyin qayta oling.", show_alert=True)
            return
        amt = random.randint(1000, 5000)
        ud["balance"] += amt
        ud["last_bonus"] = t_now
        save_db()
        bot.answer_callback_query(call.id, f"🎁 +{amt:,} so'm bonus olindi!", show_alert=True)
        try:
            bot.edit_message_text(
                f"👑 *SHOX SUPREME PLATFORMA v10.0*\n\n"
                f"👤 *{ud['name']}*\n"
                f"💵 *Balans:* {ud['balance']:,} so'm",
                cid, mid, parse_mode="Markdown", reply_markup=get_main_keyboard(uid)
            )
        except:
            pass

    elif call.data == "admin_dashboard" and uid == ADMIN_ID:
        total_users = len(DB["users"])
        total_balance = sum(u.get("balance", 0) for u in DB["users"].values())
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("📈 Aviator Cheat (kf belgilash)", callback_data="adm_set_kf"),
            types.InlineKeyboardButton("💰 Pul Qo'shish", callback_data="adm_add_money"),
            types.InlineKeyboardButton("💸 Pul Olish (ayirish)", callback_data="adm_remove_money"),
            types.InlineKeyboardButton("🔄 Hammani 10k qilish", callback_data="adm_reset"),
            types.InlineKeyboardButton("📊 Statistika", callback_data="adm_stats"),
            types.InlineKeyboardButton("⬅ Bosh Menyu", callback_data="to_main")
        )
        bot.edit_message_text(
            f"👑 *ADMIN PANEL*\n\n"
            f"👥 Jami foydalanuvchi: *{total_users}* ta\n"
            f"💵 Umumiy balans: *{total_balance:,}* so'm",
            cid, mid, parse_mode="Markdown", reply_markup=kb
        )

    elif call.data == "adm_stats" and uid == ADMIN_ID:
        lines = ["👥 *Foydalanuvchilar:*\n"]
        for uid2, u in list(DB["users"].items())[-20:]:  # oxirgi 20 ta
            lines.append(f"• ID `{uid2}` — {u.get('name','?')} — {u.get('balance',0):,} so'm")
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅ Admin", callback_data="admin_dashboard"))
        try:
            bot.edit_message_text("\n".join(lines), cid, mid, parse_mode="Markdown", reply_markup=kb)
        except:
            pass

    elif call.data == "adm_set_kf" and uid == ADMIN_ID:
        ud["state"] = "set_kf"
        save_db()
        bot.edit_message_text("🚀 Keyingi Aviator kf'ni yozing (masalan: 3.45):", cid, mid)

    elif call.data == "adm_add_money" and uid == ADMIN_ID:
        ud["state"] = "add_money"
        save_db()
        bot.edit_message_text("💰 `ID summa` ko'rinishida yozing:\nMasalan: `12345678 50000`", cid, mid, parse_mode="Markdown")

    elif call.data == "adm_remove_money" and uid == ADMIN_ID:
        ud["state"] = "remove_money"
        save_db()
        bot.edit_message_text("💸 `ID summa` ko'rinishida yozing:\nMasalan: `12345678 10000`", cid, mid, parse_mode="Markdown")

    elif call.data == "adm_reset" and uid == ADMIN_ID:
        for u in DB["users"].values():
            u["balance"] = 10000
        save_db()
        bot.answer_callback_query(call.id, "🔄 Barcha balanslar 10,000 so'm qilindi!", show_alert=True)

    # ==================== MINES ====================
    elif call.data == "prep_mines":
        kb = types.InlineKeyboardMarkup(row_width=3)
        v = [5000, 20000, 50000, 100000, 500000] if uid == ADMIN_ID else [2000, 5000, 10000, 15000]
        kb.add(*[types.InlineKeyboardButton(f"{b:,} so'm", callback_data=f"m_bet_{b}") for b in v])
        kb.add(types.InlineKeyboardButton("⬅ Chiqish", callback_data="to_main"))
        bot.edit_message_text(
            f"💣 *MINES O'YINI*\n\n💵 Balansingiz: *{ud['balance']:,} so'm*\n\nTikish summasini tanlang:",
            cid, mid, parse_mode="Markdown", reply_markup=kb
        )

    elif call.data.startswith("m_bet_"):
        bet = int(call.data.split("_")[2])
        if bet > ud["balance"]:
            bot.answer_callback_query(call.id, "❌ Balans yetarli emas!", show_alert=True)
            return
        ud["temp_bet"] = bet
        save_db()
        kb = types.InlineKeyboardMarkup(row_width=3)
        kb.add(*[types.InlineKeyboardButton(f"💣 {b} mina", callback_data=f"m_bomb_{b}") for b in [1, 3, 5, 10, 24]])
        kb.add(types.InlineKeyboardButton("⬅ Orqaga", callback_data="prep_mines"))
        bot.edit_message_text(
            f"💣 Tikilgan: *{bet:,} so'm*\n\nNechta mina bo'lsin?",
            cid, mid, parse_mode="Markdown", reply_markup=kb
        )

    elif call.data.startswith("m_bomb_"):
        bombs = int(call.data.split("_")[2])
        bet = ud.get("temp_bet")
        if not bet or bet > ud["balance"]:
            bot.answer_callback_query(call.id, "❌ Xatolik, qayta urinib ko'ring.", show_alert=True)
            return
        ud["balance"] -= bet
        ud["mines_game"] = {
            "bet": bet,
            "mines_count": bombs,
            "mines": random.sample(range(30), bombs),
            "opened": [],
            "current_kf": 1.0,
            "payout": bet,
            "status": "playing"
        }
        ud["temp_bet"] = None
        save_db()
        show_mines_board(call.message, ud, uid)

    elif call.data.startswith("mine_open_"):
        mg = ud.get("mines_game")
        if not mg or mg["status"] != "playing":
            return
        idx = int(call.data.split("_")[2])
        if idx in mg["opened"]:
            return
        if idx in mg["mines"]:
            mg["status"] = "lost"
            save_db()
            show_mines_board(call.message, ud, uid, lost=True)
            return
        mg["opened"].append(idx)
        coeff = 1.0
        for i in range(len(mg["opened"])):
            sl = 30 - mg["mines_count"] - i
            if sl <= 0:
                break
            coeff *= ((30 - i) / sl)
        mg["current_kf"] = round(coeff * 0.95, 2)
        mg["payout"] = int(mg["bet"] * mg["current_kf"])
        save_db()
        if len(mg["opened"]) == (30 - mg["mines_count"]):
            ud["balance"] += mg["payout"]
            mg["status"] = "won"
            save_db()
            show_mines_board(call.message, ud, uid, won=True)
            return
        show_mines_board(call.message, ud, uid)

    elif call.data == "mines_cashout":
        mg = ud.get("mines_game")
        if mg and mg["status"] == "playing" and mg["opened"]:
            ud["balance"] += mg["payout"]
            mg["status"] = "won"
            save_db()
            show_mines_board(call.message, ud, uid, won=True)

    # ==================== APPLE ====================
    elif call.data == "prep_apple":
        kb = types.InlineKeyboardMarkup(row_width=3)
        v = [5000, 20000, 50000, 100000, 500000] if uid == ADMIN_ID else [2000, 5000, 10000, 15000]
        kb.add(*[types.InlineKeyboardButton(f"🍏 {b:,} so'm", callback_data=f"ap_bet_{b}") for b in v])
        kb.add(types.InlineKeyboardButton("⬅ Chiqish", callback_data="to_main"))
        bot.edit_message_text(
            f"🍏 *APPLE OF FORTUNE*\n\n💵 Balansingiz: *{ud['balance']:,} so'm*\n\nTikish summasini tanlang:",
            cid, mid, parse_mode="Markdown", reply_markup=kb
        )

    elif call.data.startswith("ap_bet_"):
        bet = int(call.data.split("_")[2])
        if bet > ud["balance"]:
            bot.answer_callback_query(call.id, "❌ Balans kam!", show_alert=True)
            return
        ud["balance"] -= bet
        grid = []
        for r in range(13):
            items = ["good"] * 5
            bad = 1 if r < 4 else 2 if r < 8 else 3 if r < 11 else 4
            for bi in random.sample(range(5), bad):
                items[bi] = "bad"
            grid.append(items)
        ud["apple_game"] = {"grid": grid, "current_row": 0, "bet": bet, "payout": bet}
        save_db()
        show_apple(call.message, ud, uid)

    elif call.data.startswith("ap_select_"):
        ag = ud.get("apple_game")
        if not ag:
            return
        idx = int(call.data.split("_")[2])
        if ag["grid"][ag["current_row"]][idx] == "bad":
            ud["apple_game"] = None
            save_db()
            bot.edit_message_text(
                "💀 *Chirigan olma! Yutqazdingiz!*",
                cid, mid, parse_mode="Markdown",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🍏 Qayta o'ynash", callback_data="prep_apple"),
                    types.InlineKeyboardButton("⬅ Menyu", callback_data="to_main")
                )
            )
            return
        ag["payout"] = int(ag["bet"] * COEFFS[ag["current_row"]])
        ag["current_row"] += 1
        save_db()
        if ag["current_row"] == 13:
            ud["balance"] += ag["payout"]
            ud["apple_game"] = None
            save_db()
            bot.edit_message_text(
                f"👑 *JACKPOT! Barcha qatorlarni yutdingiz!*\n💰 +{ag['payout']:,} so'm!\n\n💵 Yangi balans: *{ud['balance']:,} so'm*",
                cid, mid, parse_mode="Markdown",
                reply_markup=get_main_keyboard(uid)
            )
            return
        show_apple(call.message, ud, uid)

    elif call.data == "ap_cashout" and ud.get("apple_game"):
        ag = ud["apple_game"]
        ud["balance"] += ag["payout"]
        ud["apple_game"] = None
        save_db()
        bot.edit_message_text(
            f"💰 *Pul yechildi!*\n+{ag['payout']:,} so'm\n\n💵 Balans: *{ud['balance']:,} so'm*",
            cid, mid, parse_mode="Markdown",
            reply_markup=get_main_keyboard(uid)
        )

    # ==================== AVIATOR ====================
    elif call.data == "prep_aviator":
        if not DB["settings"].get("next_aviator"):
            DB["settings"]["next_aviator"] = round(random.uniform(1.1, 4.5), 2)
            save_db()
        h_tx = " | ".join([f"x{h}" for h in DB["settings"].get("aviator_history", [1.2, 2.5])[-5:]])
        cm = f"🔮 *CHEAT: x{DB['settings']['next_aviator']}*\n\n" if uid == ADMIN_ID else ""
        kb = types.InlineKeyboardMarkup(row_width=3)
        v = [5000, 20000, 50000, 100000, 500000] if uid == ADMIN_ID else [2000, 5000, 10000, 15000]
        kb.add(*[types.InlineKeyboardButton(f"🚀 {b:,} so'm", callback_data=f"av_bet_{b}") for b in v])
        kb.add(types.InlineKeyboardButton("⬅ Chiqish", callback_data="to_main"))
        bot.edit_message_text(
            f"📊 *Tarix:* [{h_tx}]\n\n{cm}🚀 *AVIATOR*\n\n💵 Balans: *{ud['balance']:,} so'm*\n\nTikish summasini tanlang:",
            cid, mid, parse_mode="Markdown", reply_markup=kb
        )

    elif call.data.startswith("av_bet_"):
        bet = int(call.data.split("_")[2])
        if bet > ud["balance"]:
            bot.answer_callback_query(call.id, "❌ Balans kam!", show_alert=True)
            return
        ud["temp_bet"] = bet
        save_db()
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("📈 Auto x1.5", callback_data="av_mode_1.5"),
            types.InlineKeyboardButton("📈 Auto x2.0", callback_data="av_mode_2.0"),
            types.InlineKeyboardButton("📈 Auto x3.0", callback_data="av_mode_3.0"),
            types.InlineKeyboardButton("🔥 Qo'lda (Manual)", callback_data="av_mode_manual")
        )
        bot.edit_message_text(f"🚀 Tikilgan: *{bet:,} so'm*\n\nQanday rejimda o'ynaysiz?", cid, mid, parse_mode="Markdown", reply_markup=kb)

    elif call.data.startswith("av_mode_"):
        mode = call.data.split("_")[2]
        bet = ud.get("temp_bet")
        if not bet or bet > ud["balance"]:
            bot.answer_callback_query(call.id, "❌ Xatolik.", show_alert=True)
            return
