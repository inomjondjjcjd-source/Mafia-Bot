import os
import sys
import subprocess
import asyncio
import time
import re
import random
from threading import Thread
from flask import Flask

# 📦 KUTUBXONALARNI TO'G'RI TEKSHIRISH
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "Flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

# 🌐 RENDER UCHUN FLASK SERVER
server = Flask('')
@server.route('/')
def home(): return "Bot Muammosiz Aktiv!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# 🔑 PARAMETRLAR
TOKEN = "8930327976:AAE3sgNPEJRoZROhACHK7M4s-THpmWvNym8"
MAIN_ADMIN = 7920504062

USER_DATA = {}

def get_user_data(user_id):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "money": 999999999 if user_id == MAIN_ADMIN else 6000,
            "questions_left": 0,
            "last_bonus_time": 0,
            "state": None,
            "card_number": None,
            "full_name": None
        }
    if user_id == MAIN_ADMIN:
        USER_DATA[user_id]["money"] = 999999999
    return USER_DATA[user_id]

# 🎰 KAZINO TUGMALARI
def get_main_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🎰 Don-Don-Ziki O'ynash", callback_data="play_ddz"),
            InlineKeyboardButton("🎯 Dart O'ynash", callback_data="play_dart")
        ],
        [
            InlineKeyboardButton("🔍 Pul Qidirmoq (Savoll)", callback_data="earn_money"),
            InlineKeyboardButton("🗄 Shaxsiy Kabinet", callback_data="personal_cabinet")
        ],
        [
            InlineKeyboardButton("💳 Pul kiritish", callback_data="deposit_money"),
            InlineKeyboardButton("💸 Pul yechish", callback_data="withdraw_money")
        ],
        [
            InlineKeyboardButton("🎁 2 Soatlik Bonus", callback_data="get_bonus"),
            InlineKeyboardButton("🚀 Pul ishlash (4,000 UZS)", callback_data="earn_fast")
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
        f"💰 Sening hisobing: *{ud['money']:,} so'm*\n\n"
        "O'yin o'ynash va pul ishlash uchun tugmalarni bosing:"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(user_id))

# 📊 TUGMALAR ISHLOVCHISI
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
            f"💰 Sening hisobing: *{ud['money']:,} so'm*\n\n"
            "O'yin o'ynash va pul ishlash uchun tugmalarni bosing:"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(user_id))
    elif query.data == "personal_cabinet":
        card = ud["card_number"] if ud["card_number"] else "Kiritilmagan"
        name = ud["full_name"] if ud["full_name"] else "Kiritilmagan"
        text = (
            "🗄 *Shaxsiy Kabinet*\n\n"
            f"🆔 Sening ID raqaming: `{user_id}`\n"
            f"💰 Balans: *{ud['money']:,} so'm*\n"
            f"💳 Karta raqam: `{card}`\n"
            f"👤 Ism-Familiya: *{name}*\n"
            f"❓ Qolgan savollar: *{ud['questions_left']} ta*"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard)
    elif query.data == "get_bonus":
        now = time.time()
        if now - ud["last_bonus_time"] < 7200:
            rem = int((7200 - (now - ud["last_bonus_time"])) // 60)
            await query.edit_message_text(f"⏱ *Bonus olingan!* Yana *{rem} daqiqa* kuting.", parse_mode="Markdown", reply_markup=back_keyboard)
        else:
            gift = random.randint(1000, 3000)
            ud["money"] += gift
            ud["last_bonus_time"] = now
            await query.edit_message_text(f"🎁 Senga *+{gift:,} so'm* bonus berildi!", parse_mode="Markdown", reply_markup=back_keyboard)
    elif query.data == "withdraw_money":
        if ud["money"] < 5000:
            await query.edit_message_text("❌ Pul yechish uchun hisobingizda kamida *5,000 so'm* bo'lishi kerak!", parse_mode="Markdown", reply_markup=back_keyboard)
        else:
            ud["state"] = "wait_card_info"
            await query.edit_message_text("💳 *Hisobingizda pul yetarli!*\n\nIltimos, pul o'tkaziladigan *Karta raqamingizni* va *Ism-familiyangizni* yozib yuboring:", parse_mode="Markdown")
    elif query.data in ["play_ddz", "play_dart"]:
        gtype = "ddz" if query.data == "play_ddz" else "dart"
        ud["state"] = f"wait_bet_{gtype}"
        await query.edit_message_text("✊ *Qancha pul tikmoqchisiz?*\n_(Miqdorni yozing, Maks 5,000 so'm):_", parse_mode="Markdown")
    elif query.data == "admin_panel" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_admin_cmd"
        admin_text = (
            "👑 *Admin Panel*\n\n"
            "📌 *Pul berish:* `ID Miqdor` (Masalan: `7920504062 5000`)\n"
            "📌 *Savol qo'shish:* `ID +10` (Masalan: `7920504062 +10`)"
        )
        await query.edit_message_text(admin_text, parse_mode="Markdown", reply_markup=back_keyboard)
    elif query.data in ["earn_money", "deposit_money", "earn_fast"]:
        await query.edit_message_text("⏳ Bu bo'lim hozircha sozlanmoqda, tez kunda aktivlashadi!", reply_markup=back_keyboard)

# 💬 XABARLAR VA O'YIN MANTIQI
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    ud = get_user_data(user_id)
    back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]])

    if ud["state"] == "wait_card_info":
        ud["card_number"] = text
        ud["state"] = None
        await update.message.reply_text("✅ *Arizangiz qabul qilindi!* Tez orada adminlar hisobingizga pulni o'tkazib berishadi.", parse_mode="Markdown", reply_markup=back_keyboard)
        return
    if user_id == MAIN_ADMIN and ud["state"] == "wait_admin_cmd":
        try:
            if "+" in text:
                t_id, q_cnt = text.split()
                t_id = int(t_id)
                q_cnt = int(q_cnt.replace("+", ""))
                td = get_user_data(t_id)
                td["questions_left"] += q_cnt
                await update.message.reply_text(f"✅ `ID: {t_id}`ga *+{q_cnt} ta savol* berildi!", parse_mode="Markdown", reply_markup=back_keyboard)
            else:
                t_id, amt = map(int, text.split())
                td = get_user_data(t_id)
                td["money"] += amt
                await update.message.reply_text(f"✅ `ID: {t_id}`ga *+{amt:,} so'm* berildi!", parse_mode="Markdown", reply_markup=back_keyboard)
            ud["state"] = None
        except:
            await update.message.reply_text("❌ Xato! Namuna: `7920504062 +10` yoki `7920504062 5000`", reply_markup=back_keyboard)
        return
    if ud["state"] and ud["state"].startswith("wait_bet_"):
        gmode = ud["state"].split("_")[2]
        clean_text = re.sub(r'[.,\s]', '', text)
        if not clean_text.isdigit():
            await update.message.reply_text("❌ Xato! Faqat toza raqam kiriting.")
            return
        bet = int(clean_text)
        if bet < 100 or bet > 5000:
            await update.message.reply_text("❌ Tikish miqdori 100 - 5,000 so'm oralig'ida bo'lishi kerak!")
            return
        if ud["money"] < bet and user_id != MAIN_ADMIN:
            await update.message.reply_text("❌ Hisobingizda yetarli pul yoʻq!")
            return
        if user_id != MAIN_ADMIN:
            ud["money"] -= bet
        ud["state"] = None
        if gmode == "ddz":
            if random.random() < 0.4:
                ud["money"] += (bet * 2)
                await update.message.reply_text(f"🎮 *Don-Don-Ziki*\n\n🏆 Yutdingiz! Hisobingizga *+{bet*2:,} so'm* qo'shildi.", parse_mode="Markdown", reply_markup=back_keyboard)
            else:
                await update.message.reply_text(f"🎮 *Don-Don-Ziki*\n\n📉 Afsuski yutqazdingiz! Hisobingizdan *-{bet:,} so'm* ketdi.", parse_mode="Markdown", reply_markup=back_keyboard)
        else:
            u_s = random.randint(1, 6)
            b_s = random.randint(1, 6)
            res = f"🎯 *Dart O'yini*\n\n👤 Siz: *{u_s}* | 🤖 Bot: *{b_s}*\n\n"
            if u_s > b_s:
                ud["money"] += (bet * 2)
                res += f"🏆 *Siz yutdingiz!* +{bet*2:,} so'm"
            elif u_s < b_s:
                res += f"📉 *Bot yutdi!* -{bet:,} so'm"
            else:
                ud["money"] += bet
                res += "🤝 *Durang!* Pul qaytarildi."
            await update.message.reply_text(res, parse_mode="Markdown", reply_markup=back_keyboard)

# 🏁 ASOSIY ISHGA TUSHIRISH QISMI
def main():
    Thread(target=run_server).start()
    
    # Eskidan qolib ketgan webhooklarni butkul tozalash va to'qnashuvni yo'qotish
    app = Application.builder().token(TOKEN).build()
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(app.bot.delete_webhook(drop_pending_updates=True))
    time.sleep(1)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot muvaffaqiyatli ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
        
