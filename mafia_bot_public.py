import os
import sys
import subprocess
import asyncio
import time
import random
import json
from threading import Thread
from flask import Flask

# 📦 KUTUBXONALARNI TEKSHIRISH VA AVTO-O'RNATISH
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "Flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

# 🌐 RENDER UCHUN WEB SERVER
server = Flask('')
@server.route('/')
def home(): return "Martin Kazino Tizimi Aktiv!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# 🔑 ASOSIY PARAMETRLAR
TOKEN = "8844314869:AAEDBVoZKGVS6-5oOOV9_jXXmNY3znLbhH8"
MAIN_ADMIN = 7920504062
MY_LICHKA = "https://t.me/inomjondjjcjd"  
CHANNEL_URL = "https://t.me/yzbedkslls"     

# 💾 DOIMIY FAYLLI MA'LUMOTLAR OMBORI (JSON)
DATA_FILE = "user_database.json"
USER_DATA = {}
PROMO_CODES = {}  

SYSTEM_SETTINGS = {
    "bot_win_rate": 70  # Umumiy standart foiz
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
            print(f"Faylni o'qishda xato: {e}")
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

# 📝 SAVOLLAR BAZASI
SAVOLLAR_BAZASI = [
    {"s": f"{a} + {b} = ?", "j": str(a + b)} for a in range(10, 30) for b in range(5, 15)
][:200]

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
            "personal_win_rate": None  # Maxsus foiz (None bo'lsa umumiy foiz ishlaydi)
        }
        save_data()
    if user_id == MAIN_ADMIN:
        USER_DATA[user_id]["money"] = 999999999
    return USER_DATA[user_id]

# 📱 KLAVIATURALAR
def get_main_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🎰 Don-Don-Ziki", callback_data="play_ddz"),
            InlineKeyboardButton("🎯 Dart Tashlash", callback_data="play_dart")
        ],
        [
            InlineKeyboardButton("🔍 Pul Qidirmoq (Savol)", callback_data="earn_money"),
            InlineKeyboardButton("🗄 Shaxsiy Kabinet", callback_data="personal_cabinet")
        ],
        [
            InlineKeyboardButton("💳 Pul kiritish", callback_data="deposit_money"),
            InlineKeyboardButton("💸 Pul yechish", callback_data="withdraw_money")
        ],
        [
            InlineKeyboardButton("🎁 2 Soatlik Bonus", callback_data="get_bonus"),
            InlineKeyboardButton("🚀 Pul ishlash (2,000 UZS)", callback_data="earn_fast")
        ]
    ]
    if user_id == MAIN_ADMIN:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

# 🚀 START BUYRUG'I
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = get_user_data(user_id)
    ud["state"] = None
    save_data()
    text = (
        "🎰 *Martin Kazino Botiga Xush Kelibsiz!*\n\n"
        "Bu yerda siz o'yinlar o'ynashingiz, savollarga javob berib pul ishlashingiz va real daromad yig'ishingiz mumkin!\n\n"
        f"💰 Balansingiz: *{ud['money']:,} so'm*"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(user_id))

# 📊 CALLBACKS
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = get_user_data(user_id)
    back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]])

    if query.data == "back_home":
        ud["state"] = None
        save_data()
        text = (
            "🎰 *Martin Kazino Botiga Xush Kelibsiz!*\n\n"
            f"💰 Balansingiz: *{ud['money']:,} so'm*"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(user_id))

    elif query.data == "personal_cabinet":
        status = "👑 VIP Admin" if user_id == MAIN_ADMIN else "🎲 Oddiy O'yinchi"
        win_rate = 0 if (ud["history_wins"]+ud["history_losses"]) == 0 else int((ud["history_wins"]/(ud["history_wins"]+ud["history_losses"]))*100)
        p_rate = ud.get("personal_win_rate", None)
        rate_text = f"{p_rate}% (Sizga moslangan)" if p_rate is not None else f"{SYSTEM_SETTINGS['bot_win_rate']}% (Umumiy)"
        
        text = (
            "🗄 *Foydalanuvchi Shaxsiy Profili*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Ism/Mijoz: *{query.from_user.first_name}*\n"
            f"🆔 Raqamingiz: `{user_id}`\n"
            f"Status: {status}\n\n"
            f"💰 Naqd Balans: *{ud['money']:,} UZS*\n"
            f"📊 Jami o'yinlaringiz: {ud['games_played']} ta\n"
            f"📉 Botning yutish kuchi: *{rate_text}*\n"
            f"❓ Bugungi savollar limiti: {ud['questions_left']}/12 ta\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Yutuqlarni silliq yechib olishda davom eting!"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "get_bonus":
        now = time.time()
        if now - ud["last_bonus_time"] < 7200:
            rem_min = int((7200 - (now - ud["last_bonus_time"])) // 60)
            await query.edit_message_text(f"⏱ *Bonus rejimda!* Yana *{rem_min} daqiqa* kutishingiz kerak uka.", parse_mode="Markdown", reply_markup=back_keyboard)
        else:
            gift = random.randint(100, 1500)
            ud["money"] += gift
            ud["last_bonus_time"] = now
            save_data()
            await query.edit_message_text(f"🎁 Omad kuldi! Sizga *+{gift} so'm* hadya qilindi!", parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "deposit_money":
        text = f"💳 *Hisobni to'ldirish tizimi*\n\nPul kiritish va balansingizni ko'paytirish uchun to'g'ridan-to'g'ri loyiha rahbariga yozing:\n👉 [Mening Lichkam]({MY_LICHKA})"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "withdraw_money":
        if ud["money"] < 25000:
            await query.edit_message_text(f"❌ *Mablag' yetarsiz!*\n\nMinimal yechish miqdori: *25,000 so'm*.\nSizda hozir: *{ud['money']:,} so'm* bor.", parse_mode="Markdown", reply_markup=back_keyboard)
        else:
            text = f"💰 Hisobingizda pul yetarli!\n\nIltimos, pul yechish uchun pastdagi havola orqali menga o'z kartangizni yuboring:\n👉 [Karta tashlash uchun bosing]({MY_LICHKA})"
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "earn_fast":
        if ud["earned_fast_done"]:
            await query.edit_message_text("❌ Siz bu vazifani allaqachon bajarib 2,000 so'm olgansiz!", reply_markup=back_keyboard)
        else:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Guruhga Kirish", url=CHANNEL_URL)],
                [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")]
            ])
            await query.edit_message_text("🚀 *Tezkor Pul Ishlash*\n\nPastdagi guruhga a'zo bo'ling va srazu 2,000 so'm balansga ega bo'ling:", parse_mode="Markdown", reply_markup=kb)

    elif query.data == "check_sub":
        if not ud["earned_fast_done"]:
            ud["money"] += 2000
            ud["earned_fast_done"] = True
            save_data()
        await query.edit_message_text("✅ Tabriklaymiz! Guruh tekshirildi, hisobingizga *+2,000 so'm* qo'shildi!", parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "earn_money":
        now = time.time()
        if ud["questions_left"] <= 0 and (now - ud["last_quiz_time"] < 18000):
            rem_hr = int((18000 - (now - ud["last_quiz_time"])) // 3600)
            await query.edit_message_text(f"⏱ *Limit tugadi!* Siz 12 ta savoldan foydalandingiz. Yana *{rem_hr if rem_hr > 0 else 1} soat* kutishingiz kerak.", reply_markup=back_keyboard)
            return

        if ud["questions_left"] <= 0 and (now - ud["last_quiz_time"] >= 18000):
            ud["questions_left"] = 12
            save_data()

        q_idx = random.randint(0, len(SAVOLLAR_BAZASI)-1)
        ud["current_quiz_idx"] = q_idx
        ud["state"] = "wait_quiz_answer"
        save_data()
        await query.edit_message_text(f"🔍 *Savol:* {SAVOLLAR_BAZASI[q_idx]['s']}\n\nTo'g'ri javob uchun *800 so'm* beriladi. Javobingizni yozing:", parse_mode="Markdown")

    elif query.data in ["play_ddz", "play_dart"]:
        gtype = "ddz" if query.data == "play_ddz" else "dart"
        ud["state"] = f"wait_bet_{gtype}"
        save_data()
        await query.edit_message_text("💰 *Tikish miqdorini kiriting:*\n_(Minimal 600 so'm, Maksimal 5,000 so'm oralig'ida)_", parse_mode="Markdown")

    # 👑 ADMIN PANEL MENYUSI
    elif query.data == "admin_panel" and user_id == MAIN_ADMIN:
        akb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕/➖ Foydalanuvchi Balansi", callback_data="adm_change_balance")],
            [InlineKeyboardButton("👤 Shaxsiy Foizni Sozlash", callback_data="adm_set_personal_rate")],
            [InlineKeyboardButton("⚙️ Umumiy Foizni Sozlash", callback_data="adm_set_winrate")],
            [InlineKeyboardButton("➕ Promokod Yaratish", callback_data="adm_create_promo")],
            [InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]
        ])
        current_rate = SYSTEM_SETTINGS.get("bot_win_rate", 70)
        await query.edit_message_text(f"👑 *Eksklyuziv Admin Boshqaruv Markazi*\n\n📈 Umumiy sozlama: *Bot {current_rate}% holatda yutadi*.\n\nKerakli amalni tanlang:", parse_mode="Markdown", reply_markup=akb)

    # Admin: Maxsus foydalanuvchi foizini o'zgartirish tugmasi
    elif query.data == "adm_set_personal_rate" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_personal_rate"
        save_data()
        await query.edit_message_text("👤 *Ma'lum bir kishining yutish ehtimolini sozlash*\n\nID raqami va foizini mana bu formatda yozib yuboring:\n`ID FOIZ`\n\n*Masalan:* `12345678 90` (Ushbu ID egasi o'ynaganda bot *90%* holatda yutib oladi)", parse_mode="Markdown")

    elif query.data == "adm_set_winrate" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_winrate_val"
        save_data()
        current_rate = SYSTEM_SETTINGS.get("bot_win_rate", 70)
        await query.edit_message_text(f"⚙️ *Botning umumiy yutish ehtimolini kiriting (Hamma uchun):*\n\nHozirgi holat: `{current_rate}%`", parse_mode="Markdown")

    elif query.data == "adm_change_balance" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_balance_mod"
        save_data()
        await query.edit_message_text("💰 *Foydalanuvchi balansini boshqarish*\n\nPul qo'shish: `ID +miqdor`\nPul ayirish: `ID -miqdor` ko'rinishida yozing.", parse_mode="Markdown")

    elif query.data == "adm_create_promo" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_promo_creation"
        save_data()
        await query.edit_message_text("✍️ Yangi promokod va narxini yozing:\n\n`PROMO5000 5000`")

# 💬 MESSAGES
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    ud = get_user_data(user_id)
    back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]])

    # 🛑 ADMIN: MA'LUM BIR KISHINING FOIZINI SOZLASH (YANGI FUNKSIYA)
    if user_id == MAIN_ADMIN and ud["state"] == "wait_personal_rate":
        try:
            target_id, rate_val = text.split()
            target_id = int(target_id)
            rate_val = int(rate_val)
            
            if not (0 <= rate_val <= 100):
                await update.message.reply_text("❌ Foiz faqat 0 va 100 oralig'ida bo'lishi shart!")
                return
                
            target_ud = get_user_data(target_id)
            target_ud["personal_win_rate"] = rate_val
            ud["state"] = None
            save_data() # Faylga yozamiz
            await update.message.reply_text(f"✅ Tayyor! `ID: {target_id}` foydalanuvchisi uchun botning yutish kuchi roppa-rosa *{rate_val}%* qilib muhrlandi!", parse_mode="Markdown", reply_markup=back_keyboard)
        except:
            await update.message.reply_text("❌ Xato kiritish formati! Namuna: `7920504062 85`", reply_markup=back_keyboard)
        return

    # ADMIN: UMUMIY FOIZNI O'ZGARTIRISH
    if user_id == MAIN_ADMIN and ud["state"] == "wait_winrate_val":
        if not text.isdigit() or not (0 <= int(text) <= 100):
            await update.message.reply_text("❌ Iltimos faqat 0 dan 100 gacha son kiriting!")
            return
        SYSTEM_SETTINGS["bot_win_rate"] = int(text)
        ud["state"] = None
        save_data()
        await update.message.reply_text(f"🎯 *Umumiy foiz o'zgardi!* Endi bot hammasi uchun *{text}%* kuchi bilan o'ynaydi.", parse_mode="Markdown", reply_markup=back_keyboard)
        return

    # ADMIN: BALANSNI O'ZGARTIRISH
    if user_id == MAIN_ADMIN and ud["state"] == "wait_balance_mod":
        try:
            target_id, operation = text.split()
            target_id = int(target_id)
            target_ud = get_user_data(target_id)
            
            if operation.startswith("+"):
                amount = int(operation.replace("+", ""))
                target_ud["money"] += amount
                msg = f"✅ `ID: {target_id}` hisobiga *+{amount:,} so'm* qo'shildi!"
            elif operation.startswith("-"):
                amount = int(operation.replace("-", ""))
                target_ud["money"] -= amount
                if target_ud["money"] < 0: target_ud["money"] = 0  
                msg = f"🔥 `ID: {target_id}` hisobidan *-{amount:,} so'm* ayirildi!"
            else:
                raise ValueError
                
            ud["state"] = None
            save_data() 
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=back_keyboard)
        except:
            await update.message.reply_text("❌ Xato format. Namuna: `7920504062 -5000`", reply_markup=back_keyboard)
        return

    # Promokod yaratish
    if user_id == MAIN_ADMIN and ud["state"] == "wait_promo_creation":
        try:
            p_code, p_val = text.split()
            PROMO_CODES[p_code.upper()] = int(p_val)
            ud["state"] = None
            save_data()
            await update.message.reply_text(f"✅ Promokod `{p_code.upper()}` yaratildi ({int(p_val):,} so'm)", parse_mode="Markdown", reply_markup=back_keyboard)
        except:
            await update.message.reply_text("❌ Xato format.", reply_markup=back_keyboard)
        return

    # Promokod kiritish
    if text.upper() in PROMO_CODES and ud["state"] is None:
        bonus_amt = PROMO_CODES[text.upper()]
        ud["money"] += bonus_amt
        del PROMO_CODES[text.upper()] 
        save_data()
        await update.message.reply_text(f"🎉 Aktivlashdi! *+{bonus_amt:,} so'm* qo'shildi!", parse_mode="Markdown", reply_markup=back_keyboard)
        return

    # Savol-javob
    if ud["state"] == "wait_quiz_answer":
        q_idx = ud["current_quiz_idx"]
        correct_ans = SAVOLLAR_BAZASI[q_idx]['j']
        ud["questions_left"] -= 1
        ud["state"] = None
        if ud["questions_left"] == 0: ud["last_quiz_time"] = time.time()

        if text == correct_ans:
            ud["money"] += 800
            save_data()
            await update.message.reply_text("✅ To'g'ri javob! *+800 so'm* qo'shildi.", parse_mode="Markdown", reply_markup=back_keyboard)
        else:
            save_data()
            await update.message.reply_text(f"❌ Noto'g'ri! To'g'ri javob `{correct_ans}` edi.", parse_mode="Markdown", reply_keyboard=back_keyboard)
        return

    # O'yin tikish (FOYDALANUVCHINING SHAXSIY FOIZIGA QARAYDIGAN MOSLASHUVCHAN REJIM)
    if ud["state"] and ud["state"].startswith("wait_bet_"):
        gmode = ud["state"].split("_")[2]
        if not text.isdigit():
            await update.message.reply_text("❌ Faqat son kiriting!")
            return
        
        bet = int(text)
        if bet < 600 or bet > 5000: 
            await update.message.reply_text("❌ Minimal 600 so'm, maksimal 5,000 so'm tikish mumkin uka.")
            return
        if ud["money"] < bet and user_id != MAIN_ADMIN:
            await update.message.reply_text("❌ Hisobingizda yetarli mablag' mavjud emas!")
            return

        if user_id != MAIN_ADMIN:
            ud["money"] -= bet
        ud["state"] = None
        ud["games_played"] += 1

        is_win = False
        if bet > 3000:
            is_win = False 
        elif ud["games_played"] <= 2:
            is_win = True  
        else:
            # 🎯 SHAXSIY FOIZ ALGORITMI
            # Agar foydalanuvchiga shaxsiy foiz qo'yilgan bo'lsa uni oladi, aks holda tizimning umumiy foizini oladi
            if ud.get("personal_win_rate") is not None:
                final_chance = ud["personal_win_rate"] / 100.0
            else:
                final_chance = SYSTEM_SETTINGS.get("bot_win_rate", 70) / 100.0
                
            is_win = random.random() > final_chance 

        if is_win:
            ud["money"] += (bet * 2)
            ud["history_wins"] += 1
            res_txt = f"🏆 *Siz yutdingiz!*\n\nHisobingizga *+{bet*2:,} so'm* qo'shildi!"
        else:
            ud["history_losses"] += 1
            res_txt = f"📉 *Bot g'alaba qozondi!*\n\nHisobingizdan *-{bet:,} so'm* yechildi!"

        save_data() 
        title = "✊ Don-Don-Ziki" if gmode == "ddz" else "🎯 Dart O'yini"
        await update.message.reply_text(f"🎮 *{title}*\n\n{res_txt}", parse_mode="Markdown", reply_markup=back_keyboard)

# 🏁 RUN
def main():
    load_data() 
    Thread(target=run_server).start()
    app = Application.builder().token(TOKEN).build()
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(app.bot.delete_webhook(drop_pending_updates=True))
    time.sleep(1.0)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot individual sozlamalar tizimi bilan tayyor...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
            
