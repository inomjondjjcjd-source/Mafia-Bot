import os
import sys
import subprocess
import asyncio
import time
import random
import json
from threading import Thread
from flask import Flask

try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "Flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

server = Flask('')
@server.route('/')
def home(): return "Martin Kazino Tizimi Aktiv!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

TOKEN = "8844314869:AAEDBVoZKGVS6-5oOOV9_jXXmNY3znLbhH8"
MAIN_ADMIN = 7920504062
MY_LICHKA = "https://t.me/inomjondjjcjd"  
CHANNEL_URL = "https://t.me/yzbedkslls"     

DATA_FILE = "user_database.json"
USER_DATA = {}
PROMO_CODES = {}  

SYSTEM_SETTINGS = {
    "bot_win_rate": 70  # Standart holatda bot 70% yutadi
}

def load_data():
    global USER_DATA, SYSTEM_SETTINGS
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if "SYSTEM_SETTINGS" in loaded:
                    SYSTEM_SETTINGS = loaded["SYSTEM_SETTINGS"]
                    del loaded["SYSTEM_SETTINGS"]
                USER_DATA = {int(k): v for k, v in loaded.items()}
                print("Ma'lumotlar yuklandi.")
        except Exception as e:
            print(f"Xato: {e}")
            USER_DATA = {}
    else:
        USER_DATA = {}

def save_data():
    try:
        to_save = {str(k): v for k, v in USER_DATA.items()}
        to_save["SYSTEM_SETTINGS"] = SYSTEM_SETTINGS
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Faylga yozishda xato: {e}")

SAVOLLAR_BAZASI = [{"s": f"{a} + {b} = ?", "j": str(a + b)} for a in range(10, 30) for b in range(5, 15)][:200]

def get_user_data(user_id):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "money": 999999999 if user_id == MAIN_ADMIN else 6000,
            "games_played": 0,           
            "questions_left": 12,        
            "last_quiz_time": 0,         
            "current_quiz_idx": None,
            "last_bonus_time": 0,
            "earned_fast_done": False,   
            "state": None,
            "card_number": None,
            "full_name": None,
            "history_wins": 0,
            "history_losses": 0,
            "personal_win_rate": None  
        }
        save_data()
    if user_id == MAIN_ADMIN:
        USER_DATA[user_id]["money"] = 999999999
    return USER_DATA[user_id]

def get_main_menu_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("🎰 Don-Don-Ziki", callback_data="play_ddz"), InlineKeyboardButton("🎯 Dart Tashlash", callback_data="play_dart")],
        [InlineKeyboardButton("🔍 Pul Qidirmoq (Savol)", callback_data="earn_money"), InlineKeyboardButton("🗄 Shaxsiy Kabinet", callback_data="personal_cabinet")],
        [InlineKeyboardButton("💳 Pul kiritish", callback_data="deposit_money"), InlineKeyboardButton("💸 Pul yechish", callback_data="withdraw_money")],
        [InlineKeyboardButton("🎁 2 Soatlik Bonus", callback_data="get_bonus"), InlineKeyboardButton("🚀 Pul ishlash (2,000 UZS)", callback_data="earn_fast")]
    ]
    if user_id == MAIN_ADMIN:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = get_user_data(user_id)
    ud["state"] = None
    save_data()
    text = f"🎰 *Martin Kazino Botiga Xush Kelibsiz!*\n\n💰 Balansingiz: *{ud['money']:,} so'm*"
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(user_id))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = get_user_data(user_id)
    back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]])

    if query.data == "back_home":
        ud["state"] = None
        save_data()
        text = f"🎰 *Martin Kazino Botiga Xush Kelibsiz!*\n\n💰 Balansingiz: *{ud['money']:,} so'm*"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(user_id))

    elif query.data == "personal_cabinet":
        status = "👑 VIP Admin" if user_id == MAIN_ADMIN else "🎲 Oddiy O'yinchi"
        p_rate = ud.get("personal_win_rate", None)
        rate_text = f"Bot {p_rate}% yutadi (Maxsus)" if p_rate is not None else f"Bot {SYSTEM_SETTINGS['bot_win_rate']}% yutadi (Umumiy)"
        
        text = (
            "🗄 *Foydalanuvchi Shaxsiy Profili*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Ism: *{query.from_user.first_name}*\n"
            f"🆔 ID: `{user_id}`\n"
            f"Status: {status}\n\n"
            f"💰 Balans: *{ud['money']:,} UZS*\n"
            f"📊 Jami o'yinlar: {ud['games_played']} ta\n"
            f"⚙️ Tizim algoritmi: *{rate_text}*\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "get_bonus":
        now = time.time()
        if now - ud["last_bonus_time"] < 7200:
            rem_min = int((7200 - (now - ud["last_bonus_time"])) // 60)
            await query.edit_message_text(f"⏱ Yana *{rem_min} daqiqa* kutishingiz kerak.", parse_mode="Markdown", reply_markup=back_keyboard)
        else:
            gift = random.randint(100, 1500)
            ud["money"] += gift
            ud["last_bonus_time"] = now
            save_data()
            await query.edit_message_text(f"🎁 Hisobingizga *+{gift} so'm* qo'shildi!", parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "deposit_money":
        await query.edit_message_text(f"💳 Pul kiritish uchun yozing:\n👉 [Mening Lichkam]({MY_LICHKA})", parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "withdraw_money":
        if ud["money"] < 25000:
            await query.edit_message_text(f"❌ Mablag' yetarsiz! Minimal: 25,000 so'm. Sizda: *{ud['money']:,} so'm*", parse_mode="Markdown", reply_markup=back_keyboard)
        else:
            await query.edit_message_text(f"💸 Karta raqamingizni lichkamga tashlang:\n👉 [Mening Lichkam]({MY_LICHKA})", parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "earn_fast":
        if ud["earned_fast_done"]:
            await query.edit_message_text("❌ Bu vazifa bajarilgan!", reply_markup=back_keyboard)
        else:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Guruh", url=CHANNEL_URL)], [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")]])
            await query.edit_message_text("🚀 Guruhga a'zo bo'ling va 2,000 so'm oling:", reply_markup=kb)

    elif query.data == "check_sub":
        if not ud["earned_fast_done"]:
            ud["money"] += 2000
            ud["earned_fast_done"] = True
            save_data()
        await query.edit_message_text("✅ Hisobingizga *+2,000 so'm* qo'shildi!", parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "earn_money":
        now = time.time()
        if ud["questions_left"] <= 0 and (now - ud["last_quiz_time"] < 18000):
            rem_hr = int((18000 - (now - ud["last_quiz_time"])) // 3600)
            await query.edit_message_text(f"⏱ Limit tugadi. Yana *{rem_hr if rem_hr > 0 else 1} soat* kuting.", reply_markup=back_keyboard)
            return
        if ud["questions_left"] <= 0 and (now - ud["last_quiz_time"] >= 18000):
            ud["questions_left"] = 12

        q_idx = random.randint(0, len(SAVOLLAR_BAZASI)-1)
        ud["current_quiz_idx"] = q_idx
        ud["state"] = "wait_quiz_answer"
        save_data()
        await query.edit_message_text(f"🔍 *Savol:* {SAVOLLAR_BAZASI[q_idx]['s']}\n\nJavobingizni yozing:", parse_mode="Markdown")

    elif query.data in ["play_ddz", "play_dart"]:
        gtype = "ddz" if query.data == "play_ddz" else "dart"
        ud["state"] = f"wait_bet_{gtype}"
        save_data()
        await query.edit_message_text("💰 *Tikish miqdorini kiriting:* (600 - 5,000 so'm)", parse_mode="Markdown")

    elif query.data == "admin_panel" and user_id == MAIN_ADMIN:
        akb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕/➖ Foydalanuvchi Balansi", callback_data="adm_change_balance")],
            [InlineKeyboardButton("👤 Shaxsiy Foizni Sozlash", callback_data="adm_set_personal_rate")],
            [InlineKeyboardButton("⚙️ Umumiy Foizni Sozlash", callback_data="adm_set_winrate")],
            [InlineKeyboardButton("➕ Promokod Yaratish", callback_data="adm_create_promo")],
            [InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]
        ])
        current_rate = SYSTEM_SETTINGS.get("bot_win_rate", 70)
        await query.edit_message_text(f"👑 *Admin Panel*\n\n📈 Umumiy algoritm: Bot {current_rate}% yutadi.\n\nAmalni tanlang:", reply_markup=akb)

    elif query.data == "adm_set_personal_rate" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_personal_rate"
        save_data()
        await query.edit_message_text("👤 *Odamning ID raqami va Botning yutish foizini yozing:*\nFormat: `ID FOIZ`\n\n*Masalan:* `7920504062 90` (Bot uni 90% holatda yutqaztiradi)")

    elif query.data == "adm_set_winrate" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_winrate_val"
        save_data()
        await query.edit_message_text(f"⚙️ Hamma uchun umumiy bot yutish foizini kiriting (0-100):")

    elif query.data == "adm_change_balance" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_balance_mod"
        save_data()
        await query.edit_message_text("💰 Format: `ID +pul` yoki `ID -pul` ko'rinishida yozing.")

    elif query.data == "adm_create_promo" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_promo_creation"
        save_data()
        await query.edit_message_text("✍️ Format: `KOD SUMMA`")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    ud = get_user_data(user_id)
    back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]])

    # 🎯 SHAXSIY FOIZNI TO'G'RI SOZLASH
    if user_id == MAIN_ADMIN and ud["state"] == "wait_personal_rate":
        try:
            target_id, rate_val = text.split()
            target_id = int(target_id)
            rate_val = int(rate_val)
            if not (0 <= rate_val <= 100): raise ValueError
                
            target_ud = get_user_data(target_id)
            target_ud["personal_win_rate"] = rate_val
            ud["state"] = None
            save_data()
            await update.message.reply_text(f"✅ Tayyor! `ID: {target_id}` uchun Botning yutish ehtimoli *{rate_val}%* qilindi!", parse_mode="Markdown", reply_markup=back_keyboard)
        except:
            await update.message.reply_text("❌ Xato! Namuna: `7920504062 85`", reply_markup=back_keyboard)
        return

    if user_id == MAIN_ADMIN and ud["state"] == "wait_winrate_val":
        if not text.isdigit() or not (0 <= int(text) <= 100):
            await update.message.reply_text("❌ 0 dan 100 gacha son yozing!")
            return
        SYSTEM_SETTINGS["bot_win_rate"] = int(text)
        ud["state"] = None
        save_data()
        await update.message.reply_text(f"🎯 Umumiy algoritm: Bot {text}% yutadigan bo'ldi.", reply_markup=back_keyboard)
        return

    if user_id == MAIN_ADMIN and ud["state"] == "wait_balance_mod":
        try:
            target_id, operation = text.split()
            target_id = int(target_id)
            target_ud = get_user_data(target_id)
            if operation.startswith("+"):
                target_ud["money"] += int(operation.replace("+", ""))
            elif operation.startswith("-"):
                target_ud["money"] -= int(operation.replace("-", ""))
                if target_ud["money"] < 0: target_ud["money"] = 0
            ud["state"] = None
            save_data()
            await update.message.reply_text("✅ Balans o'zgardi!", reply_markup=back_keyboard)
        except:
            await update.message.reply_text("❌ Xato! Namuna: `7920504062 -5000`", reply_markup=back_keyboard)
        return

    if user_id == MAIN_ADMIN and ud["state"] == "wait_promo_creation":
        try:
            p_code, p_val = text.split()
            PROMO_CODES[p_code.upper()] = int(p_val)
            ud["state"] = None
            save_data()
            await update.message.reply_text(f"✅ `{p_code.upper()}` yaratildi.", reply_markup=back_keyboard)
        except:
            await update.message.reply_text("❌ Xato format.", reply_markup=back_keyboard)
        return

    if text.upper() in PROMO_CODES and ud["state"] is None:
        bonus_amt = PROMO_CODES[text.upper()]
        ud["money"] += bonus_amt
        del PROMO_CODES[text.upper()] 
        save_data()
        await update.message.reply_text(f"🎉 *+{bonus_amt:,} so'm* qo'shildi!", parse_mode="Markdown", reply_markup=back_keyboard)
        return

    if ud["state"] == "wait_quiz_answer":
        q_idx = ud["current_quiz_idx"]
        correct_ans = SAVOLLAR_BAZASI[q_idx]['j']
        ud["questions_left"] -= 1
        ud["state"] = None
        if ud["questions_left"] == 0: ud["last_quiz_time"] = time.time()

        if text == correct_ans:
            ud["money"] += 800
            save_data()
            await update.message.reply_text("✅ To'g'ri!", reply_markup=back_keyboard)
        else:
            save_data()
            await update.message.reply_text(f"❌ Noto'g'ri. Javob: `{correct_ans}`", parse_mode="Markdown", reply_markup=back_keyboard)
        return

    # 🎰 MUKAMMAL 100% ANIQ ISHLOVCHI O'YIN TIKISH ALGORITMI
    if ud["state"] and ud["state"].startswith("wait_bet_"):
        gmode = ud["state"].split("_")[2]
        if not text.isdigit():
            await update.message.reply_text("❌ Son kiriting!")
            return
        
        bet = int(text)
        if bet < 600 or bet > 5000:
            await update.message.reply_text("❌ Taqiqlangan miqdor! (600 - 5000)")
            return
        if ud["money"] < bet and user_id != MAIN_ADMIN:
            await update.message.reply_text("❌ Mablag' yetarsiz!")
            return

        if user_id != MAIN_ADMIN:
            ud["money"] -= bet
        ud["state"] = None
        ud["games_played"] += 1

        # 🎯 BOTNING YUTISH CHANSI (FOIZI) NING ANIQ MATEMATIKASI
        if ud.get("personal_win_rate") is not None:
            bot_win_percent = ud["personal_win_rate"]
        else:
            bot_win_percent = SYSTEM_SETTINGS.get("bot_win_rate", 70)

        # 1 dan 100 gacha tasodifiy son olinadi
        roll = random.randint(1, 100)
        
        # Agar yozilgan foiz roll dan katta yoki teng bo'lsa -> BOT YUTADI. Foydalanuvchi yutqazadi!
        if roll <= bot_win_percent:
            is_user_win = False
        else:
            is_user_win = True

        # Yirik tikishlar nazorati (3000 so'mdan baland tiksa srazu bot yutadi)
        if bet > 3000:
            is_user_win = False

        if is_user_win:
            ud["money"] += (bet * 2)
            ud["history_wins"] += 1
            res_txt = f"🏆 *Siz yutdingiz!*\n\nHisobingizga *+{bet*2:,} so'm* qo'shildi!"
        else:
            ud["history_losses"] += 1
            res_txt = f"📉 *Bot g'alaba qozondi!*\n\nHisobingizdan *-{bet:,} so'm* yechildi!"

        save_data()
        title = "✊ Don-Don-Ziki" if gmode == "ddz" else "🎯 Dart O'yini"
        await update.message.reply_text(f"🎮 *{title}*\n\n{res_txt}", parse_mode="Markdown", reply_markup=back_keyboard)

def main():
    load_data()
    Thread(target=run_server).start()
    app = Application.builder().token(TOKEN).build()
    
    try: loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(app.bot.delete_webhook(drop_pending_updates=True))
    time.sleep(1.0)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot 100% aniqlikda ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
