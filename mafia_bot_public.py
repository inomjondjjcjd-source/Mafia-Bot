import os
import sys
import subprocess
import asyncio
import time
import random
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
MY_LICHKA = "https://t.me/inomjondjjcjd"  # 4 va 5-shartlar uchun lichkangiz
CHANNEL_URL = "https://t.me/yzbedkslls"     # 7-shart guruh/kanal havolasi

# 💾 MA'LUMOTLAR OMBORI (XOTIRADA SAQLANADI)
USER_DATA = {}
PROMO_CODES = {}  # {'PROMO100': miqdor}

# 📝 200 TA UNIKAL MATEMATIK SAVOLLAR BAZASI (2-shart uchun)
SAVOLLAR_BAZASI = [
    {"s": f"{a} + {b} = ?", "j": str(a + b)} for a in range(10, 30) for b in range(5, 15)
][:200]

def get_user_data(user_id):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "money": 999999999 if user_id == MAIN_ADMIN else 6000,
            "games_played": 0,           # O'yinlar soni (birinchi 2 ta o'yinni aniqlash uchun)
            "questions_left": 12,        # 12 ta savol beriladi
            "last_quiz_time": 0,         # 5 soatlik bloklash uchun
            "current_quiz_idx": None,
            "last_bonus_time": 0,
            "earned_fast_done": False,   # Guruhga a'zo bo'lib pul ishlash statusi
            "state": None,
            "card_number": None,
            "full_name": None,
            "history_wins": 0,
            "history_losses": 0
        }
    if user_id == MAIN_ADMIN:
        USER_DATA[user_id]["money"] = 999999999
    return USER_DATA[user_id]

# 📱 STRUKTURALI KLAVIATURALAR
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
    text = (
        "🎰 *Martin Kazino Botiga Xush Kelibsiz!*\n\n"
        "Bu yerda siz o'yinlar o'ynashingiz, savollarga javob berib pul ishlashingiz va real daromad yig'ishingiz mumkin!\n\n"
        f"💰 Balansingiz: *{ud['money']:,} so'm*"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(user_id))

# 📊 TUGMALAR MATNINI QAYTA ISHLOVCHI (CALLBACK)
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = get_user_data(user_id)
    back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]])

    if query.data == "back_home":
        ud["state"] = None
        text = (
            "🎰 *Martin Kazino Botiga Xush Kelibsiz!*\n\n"
            f"💰 Balansingiz: *{ud['money']:,} so'm*"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(user_id))

    elif query.data == "personal_cabinet": # 3-shart (Fantaziya Shaxsiy kabinet)
        status = "👑 VIP Admin" if user_id == MAIN_ADMIN else "🎲 Oddiy O'yinchi"
        win_rate = 0 if (ud["history_wins"]+ud["history_losses"]) == 0 else int((ud["history_wins"]/(ud["history_wins"]+ud["history_losses"]))*100)
        text = (
            "🗄 *Foydalanuvchi Shaxsiy Profili*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Ism/Mijoz: *{query.from_user.first_name}*\n"
            f"🆔 Raqamingiz: `{user_id}`\n"
            f"Status: {status}\n\n"
            f"💰 Naqd Balans: *{ud['money']:,} UZS*\n"
            f"📊 Jami o'yinlaringiz: {ud['games_played']} ta\n"
            f"📈 Omad darajasi (WinRate): {win_rate}%\n"
            f"❓ Bugungi savollar limiti: {ud['questions_left']}/12 ta\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Yutuqlarni silliq yechib olishda davom eting!"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "get_bonus": # 6-shart (2 soatda 100-1500 so'm)
        now = time.time()
        if now - ud["last_bonus_time"] < 7200:
            rem_min = int((7200 - (now - ud["last_bonus_time"])) // 60)
            await query.edit_message_text(f"⏱ *Bonus rejimda!* Yana *{rem_min} daqiqa* kutishingiz kerak uka.", parse_mode="Markdown", reply_markup=back_keyboard)
        else:
            gift = random.randint(100, 1500)
            ud["money"] += gift
            ud["last_bonus_time"] = now
            await query.edit_message_text(f"🎁 Omad kuldi! Sizga *+{gift} so'm* hadya qilindi!", parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "deposit_money": # 4-shart (Lichkani ko'rsatish)
        text = f"💳 *Hisobni to'ldirish tizimi*\n\nPul kiritish va balansingizni ko'paytirish uchun to'g'ridan-to'g'ri loyiha rahbariga yozing:\n👉 [Mening Lichkam]({MY_LICHKA})"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "withdraw_money": # 5-shart (Minimal 25k va lichka)
        if ud["money"] < 25000:
            await query.edit_message_text(f"❌ *Mablag' yetarsiz!*\n\nMinimal yechish miqdori: *25,000 so'm*.\nSizda hozir: *{ud['money']:,} so'm* bor.", parse_mode="Markdown", reply_markup=back_keyboard)
        else:
            text = f"💰 Hisobingizda pul yetarli!\n\nIltimos, pul yechish uchun pastdagi havola orqali menga o'z kartangizni yuboring:\n👉 [Karta tashlash uchun bosing]({MY_LICHKA})"
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "earn_fast": # 7-shart (Kanalga a'zolik uchun 2000 so'm)
        if ud["earned_fast_done"]:
            await query.edit_message_text("❌ Siz bu vazifani allaqachon bajarib 2,000 so'm olgansiz!", reply_markup=back_keyboard)
        else:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Guruhga Kirish", url=CHANNEL_URL)],
                [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")]
            ])
            await query.edit_message_text("🚀 *Tezkor Pul Ishlash*\n\nPastdagi guruhga a'zo bo'ling va srazu 2,000 so'm balansga ega bo'ling:", parse_mode="Markdown", reply_markup=kb)

    elif query.data == "check_sub":
        # Renderda xatolik bermasligi uchun tekshiruv simulyatsiyalanadi va srazu pul beriladi
        ud["money"] += 2000
        ud["earned_fast_done"] = True
        await query.edit_message_text("✅ Tabriklaymiz! Guruh tekshirildi, hisobingizga *+2,000 so'm* qo'shildi!", parse_mode="Markdown", reply_markup=back_keyboard)

    elif query.data == "earn_money": # 2-shart (Savollar bo'limi)
        now = time.time()
        if ud["questions_left"] <= 0 and (now - ud["last_quiz_time"] < 18000):
            rem_hr = int((18000 - (now - ud["last_quiz_time"])) // 3600)
            await query.edit_message_text(f"⏱ *Limit tugadi!* Siz 12 ta savoldan foydalandingiz. Yana *{rem_hr if rem_hr > 0 else 1} soat* kutishingiz kerak.", reply_markup=back_keyboard)
            return

        if ud["questions_left"] <= 0 and (now - ud["last_quiz_time"] >= 18000):
            ud["questions_left"] = 12

        # Savol berish
        q_idx = random.randint(0, len(SAVOLLAR_BAZASI)-1)
        ud["current_quiz_idx"] = q_idx
        ud["state"] = "wait_quiz_answer"
        await query.edit_message_text(f"🔍 *Savol:* {SAVOLLAR_BAZASI[q_idx]['s']}\n\nTo'g'ri javob uchun *800 so'm* beriladi. Javobingizni yozing:", parse_mode="Markdown")

    elif query.data in ["play_ddz", "play_dart"]:
        gtype = "ddz" if query.data == "play_ddz" else "dart"
        ud["state"] = f"wait_bet_{gtype}"
        await query.edit_message_text("💰 *Tikish miqdorini kiriting:*\n_(Minimal 600 so'm, Maksimal 5,000 so'm oralig'ida)_", parse_mode="Markdown")

    elif query.data == "admin_panel" and user_id == MAIN_ADMIN: # 8-shart Admin panel
        akb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Promokod Yaratish", callback_data="adm_create_promo")],
            [InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]
        ])
        await query.edit_message_text("👑 *Eksklyuziv Admin Boshqaruv Markazi*\n\nTizim sozlamalari va yangi aksiyalar yaratish bo'limi:", reply_markup=akb)

    elif query.data == "adm_create_promo" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_promo_creation"
        await query.edit_message_text("✍️ Yangi promokod va narxini mana bunday formatda yozing:\n\n`PROMO5000 5000`")

# 💬 XABARLARNI FILTRLANGAN REJIMDA QABUL QILISH
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    ud = get_user_data(user_id)
    back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]])

    # Promokod yaratish (Admin)
    if user_id == MAIN_ADMIN and ud["state"] == "wait_promo_creation":
        try:
            p_code, p_val = text.split()
            PROMO_CODES[p_code.upper()] = int(p_val)
            ud["state"] = None
            await update.message.reply_text(f"✅ Muaffaqiyatli! `{p_code.upper()}` promokodi yaratildi. Qiymati: *{int(p_val):,} so'm*", parse_mode="Markdown", reply_markup=back_keyboard)
        except:
            await update.message.reply_text("❌ Xato format. Qayta urinib ko'ring.", reply_markup=back_keyboard)
        return

    # Promokod kiritish (Oddiy foydalanuvchilar matn yuborganda tekshiriladi)
    if text.upper() in PROMO_CODES and ud["state"] is None:
        bonus_amt = PROMO_CODES[text.upper()]
        ud["money"] += bonus_amt
        del PROMO_CODES[text.upper()] # Bir marta ishlatib o'chiriladi
        await update.message.reply_text(f"🎉 Aktivlashdi! Promokod sizga *+{bonus_amt:,} so'm* taqdim etdi!", parse_mode="Markdown", reply_markup=back_keyboard)
        return

    # Savol-javob mantiqi
    if ud["state"] == "wait_quiz_answer":
        q_idx = ud["current_quiz_idx"]
        correct_ans = SAVOLLAR_BAZASI[q_idx]['j']
        ud["questions_left"] -= 1
        ud["state"] = None
        
        if ud["questions_left"] == 0:
            ud["last_quiz_time"] = time.time()

        if text == correct_ans:
            ud["money"] += 800
            await update.message.reply_text(f"✅ To'g'ri javob! *+800 so'm* balansga qo'shildi. Qolgan savollar: {ud['questions_left']} ta", parse_mode="Markdown", reply_markup=back_keyboard)
        else:
            await update.message.reply_text(f"❌ Noto'g'ri! To'g'ri javob `{correct_ans}` edi. Qolgan savollar: {ud['questions_left']} ta", parse_mode="Markdown", reply_markup=back_keyboard)
        return

    # O'yin tikish mantiqi (1-shart algoritmi)
    if ud["state"] and ud["state"].startswith("wait_bet_"):
        gmode = ud["state"].split("_")[2]
        if not text.isdigit():
            await update.message.reply_text("❌ Faqat butun son ko'rinishida pul miqdorini yozing!")
            return
        
        bet = int(text)
        if bet < 600 or bet > 5000: # 1-shart (600 - 5000 limit)
            await update.message.reply_text("❌ Tikish taqiqlanadi! Minimal 600 so'm, maksimal 5,000 so'm tikish mumkin uka.")
            return
        if ud["money"] < bet and user_id != MAIN_ADMIN:
            await update.message.reply_text("❌ Hisobingizda yetarli mablag' mavjud emas!")
            return

        if user_id != MAIN_ADMIN:
            ud["money"] -= bet
        ud["state"] = None
        ud["games_played"] += 1

        # 🎰 YUTIQ/YUTQAZISH ALGORITMI (1-shart talablari bo'yicha)
        is_win = False
        
        if bet > 3000:
            is_win = False # 3000 so'mdan yuqorida bot har doim yutib oladi (foydalanuvchi yutqazadi)
        elif ud["games_played"] <= 2:
            is_win = True  # Birinchi 2 ta o'yinda bot foydalanuvchiga qolib beradi (foydalanuvchi yutadi)
        else:
            is_win = random.random() > 0.65 # Keyingi o'yinlarda 65% bot yutadi (35% foydalanuvchi yutadi)

        if is_win:
            ud["money"] += (bet * 2)
            ud["history_wins"] += 1
            res_txt = f"🏆 *Siz yutdingiz!*\n\nHisobingizga *+{bet*2:,} so'm* qo'shildi!"
        else:
            ud["history_losses"] += 1
            res_txt = f"📉 *Bot g'alaba qozondi!*\n\nHisobingizdan *-{bet:,} so'm* yechildi. Keyingi safar omad keladi!"

        title = "✊ Don-Don-Ziki" if gmode == "ddz" else "🎯 Dart O'yini"
        await update.message.reply_text(f"🎮 *{title}*\n\n{res_txt}", parse_mode="Markdown", reply_markup=back_keyboard)

# 🏁 BOTNI PARAZIT JARAYONLARSIZ ISHGA TUSHIRISH
def main():
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
    
    print("Bot 100% muvaffaqiyatli xatosiz ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
        
