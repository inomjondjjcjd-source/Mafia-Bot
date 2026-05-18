import os
import sys
import subprocess

# RENDER KESHINI CHETLAB O'TISH UCHUN AVTOMATIK KUTUBXONA O'RNATUVCHI
try:
    import telebot
except ImportError:
    print("Telebot topilmadi. Majburiy o'rnatilmoqda...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyTelegramBotAPI", "Flask"])
    import telebot

import random
import re
import time
from threading import Thread
from flask import Flask
from telebot import types

# SERVERNI SOZLASH
server = Flask('')
@server.route('/')
def home(): return "Bot 100% Aktiv va Tezkor!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# ASOSIY PARAMETRLAR
TOKEN = "8443418214:AAHtuz30gPUOF6qpNOSZrd8MnOwGG7nhbOA"
MAIN_ADMIN = 7920504062  

bot = telebot.TeleBot(TOKEN)
USER_DATA = {}

def get_user(user_id):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "money": 999999999 if user_id == MAIN_ADMIN else 6000,
            "last_bonus": 0,
            "state": "none"
        }
    if user_id == MAIN_ADMIN:
        USER_DATA[user_id]["money"] = 999999999
    return USER_DATA[user_id]

def main_markup(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🎮 Don-Don-Ziki", callback_data="game_ddz")
    btn2 = types.InlineKeyboardButton("🎯 Dart O'yin", callback_data="game_dart")
    btn3 = types.InlineKeyboardButton("🎁 Bonus", callback_data="game_bonus")
    markup.add(btn1, btn2, btn3)
    if user_id == MAIN_ADMIN:
        markup.add(types.InlineKeyboardButton("👑 Admin Panel", callback_data="game_admin"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    u_id = message.from_user.id
    db = get_user(u_id)
    db["state"] = "none"
    text = f"🎰 *Martin Kazino*\n\n💰 Balans: *{db['money']:,} so'm*\n\nO'yinni tanlang:"
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_markup(u_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def callback_inline(call):
    u_id = call.from_user.id
    db = get_user(u_id)
    back_markup = types.InlineKeyboardMarkup()
    back_markup.add(types.InlineKeyboardButton("⬅️ Menyu", callback_data="game_home"))

    if call.data == "game_home":
        db["state"] = "none"
        text = f"🎰 *Martin Kazino*\n\n💰 Balans: *{db['money']:,} so'm*"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=main_markup(u_id))

    elif call.data == "game_bonus":
        now = int(time.time())
        if now - db["last_bonus"] < 3600:
            rem = int((3600 - (now - db["last_bonus"])) // 60)
            bot.edit_message_text(f"⏱ Bonus olingan! Yana *{rem} daqiqa* kuting.", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=back_markup)
        else:
            gift = random.randint(1000, 4000)
            db["money"] += gift
            db["last_bonus"] = now
            bot.edit_message_text(f"🎁 Bonus qo'shildi: *+{gift:,} so'm*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=back_markup)

    elif call.data in ["game_ddz", "game_dart"]:
        g_type = "ddz" if call.data == "game_ddz" else "dart"
        db["state"] = f"wait_bet_{g_type}"
        bot.edit_message_text("✍️ *Tikadigan pulingizni yozing:*\n_(Masalan: 2000 yoki 5000)_", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    elif call.data == "game_admin" and u_id == MAIN_ADMIN:
        db["state"] = "wait_admin"
        bot.edit_message_text("👑 *Admin Panel*\n\nPul berish formati: `ID MIQDOR`", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=back_markup)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    u_id = message.from_user.id
    text = message.text.strip()
    db = get_user(u_id)
    back_markup = types.InlineKeyboardMarkup()
    back_markup.add(types.InlineKeyboardButton("⬅️ Menyu", callback_data="game_home"))

    if u_id == MAIN_ADMIN and db["state"] == "wait_admin":
        try:
            t_id, amt = map(int, text.split())
            t_db = get_user(t_id)
            t_db["money"] += amt
            db["state"] = "none"
            bot.send_message(message.chat.id, f"✅ `ID: {t_id}`ga *+{amt:,} so'm* berildi!", parse_mode="Markdown", reply_markup=back_markup)
        except:
            bot.send_message(message.chat.id, "❌ Xato! Namuna: `7920504062 10000`", reply_markup=back_markup)
        return

    if db["state"].startswith("wait_bet_"):
        g_mode = db["state"].split("_")[2]
        clean_text = re.sub(r'[.,\s]', '', text)
        
        if not clean_text.isdigit():
            bot.send_message(message.chat.id, "❌ Faqat toza raqam kiriting! (Masalan: 2000)")
            return
            
        bet = int(clean_text)
        if bet < 500 or bet > 50000:
            bot.send_message(message.chat.id, "❌ Tikish miqdori 500 - 50,000 so'm oralig'ida bo'lishi kerak!")
            return
            
        if db["money"] < bet and u_id != MAIN_ADMIN:
            bot.send_message(message.chat.id, f"❌ Mablag' yetarli emas! Sizda: {db['money']:,} so'm bor.")
            return

        if u_id != MAIN_ADMIN:
            db["money"] -= bet
        db["state"] = "none"

        if g_mode == "ddz":
            win = random.random() < 0.30 if bet > 4000 else random.random() < 0.45
            if win:
                db["money"] += (bet * 2)
                bot.send_message(message.chat.id, f"🎮 *Don-Don-Ziki*\n\n✊ Siz: Tosh\n✌️ Bot: Qaychi\n\n🏆 *Yutdingiz!* +{bet*2:,} so'm", parse_mode="Markdown", reply_markup=back_markup)
            else:
                bot.send_message(message.chat.id, f"🎮 *Don-Don-Ziki*\n\n✌️ Siz: Qaychi\n✊ Bot: Tosh\n\n📉 *Yutqazdingiz!* -{bet:,} so'm", parse_mode="Markdown", reply_markup=back_markup)

        elif g_mode == "dart":
            u_score = random.randint(1, 6)
            b_score = random.randint(u_score + 1, 6) if (bet > 4000 or random.random() < 0.6) and u_score < 6 else random.randint(1, 6)
            
            res = f"🎯 *Dart*\n\n👤 Siz: *{u_score}* | 🤖 Bot: *{b_score}*\n\n"
            if u_score > b_score:
                db["money"] += (bet * 2)
                res += f"🏆 *Siz yutdingiz!* +{bet*2:,} so'm"
            elif u_score < b_score:
                res += f"📉 *Bot yutdi!* -{bet:,} so'm"
            else:
                db["money"] += bet
                res += "🤝 *Durang!* Pul qaytarildi."
            bot.send_message(message.chat.id, res, parse_mode="Markdown", reply_markup=back_markup)

if __name__ == '__main__':
    Thread(target=run_server).start()
    print("Bot muvaffaqiyatli ishlamoqda...")
    # Xato bergan drop_pending_updates olib tashlandi, endi 100% toza yonadi!
    bot.infinity_polling()
    
