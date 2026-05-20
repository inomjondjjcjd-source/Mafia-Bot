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
