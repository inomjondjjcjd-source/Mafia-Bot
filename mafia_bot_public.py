import os, random, asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Render uchun server
server = Flask('')
@server.route('/')
def home(): return "Martin Casino Bot Tirik!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# 🔥 SENING YANGI MA'LUMOTLARING JOYLASHTIRILDI
TOKEN = "8443418214:AAEwtTcxOw2kYScXq3beGJDagxou_H6iuAc"
MAIN_ADMIN = 7920504062  

USER_BALANCES = {} # O'yinchilar balansi shu yerda saqlanadi

def check_user(user_id, name):
    if user_id not in USER_BALANCES:
        USER_BALANCES[user_id] = {"name": name, "money": 5000} # Boshlanishiga 5000 so'm tekin beriladi
    return USER_BALANCES[user_id]

# /start buyrug'i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    check_user(user.id, user.first_name)
    
    if update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("🎰 Kazino guruhda tayyor! O'yinlarni boshlash uchun /casino deb yozing!")
        return

    text = (
        f"🎰 *Martin Kazino Botiga Xush Kelibsiz!*\n\n"
        f"Bu yerda siz guruhda daxshatli o'yinlar o'ynab, virtual pullar yutishingiz mumkin!\n\n"
        f"💰 Boshlang'ich kapitalingiz: *5,000 so'm*"
    )
    kb = [[InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# Guruhda menyuni ko'rish
async def casino_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return
    
    text = (
        "🎰 *KAZINO O'YINLARI RO'YXATI:*\n\n"
        "🎲 `/dice MIQDOR` - Guruhdagilar bilan kubik o'ynash (Reply orqali)\n"
        "🎯 `/dart MIQDOR` - Guruhdagilar bilan dart o'ynash (Reply orqali)\n"
        "🎰 `/slot MIQDOR` - Slot avtomatini aylantirish (Botga qarshi)\n"
        "💰 `/balans` - Pullaringizni tekshirish\n"
        "🎁 `/bonus` - Har soatlik tekin pul olish\n"
        "🏆 `/top` - Guruh boylari reytingi"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# /balans buyrug'i
async def balans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = check_user(user.id, user.first_name)
    await update.message.reply_text(f"👤 *{user.first_name}*, sizning balansingiz: *{db['money']:,} so'm* 💰", parse_mode="Markdown")

# /bonus buyrug'i
async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = check_user(user.id, user.first_name)
    
    omad_pul = random.randint(500, 3000)
    db["money"] += omad_pul
    await update.message.reply_text(f"🎁 *Kunlik Bonus!* \n\n👤 *{user.first_name}* sizga *+{omad_pul} so'm* berildi!\nHozirgi balans: *{db['money']:,} so'm*", parse_mode="Markdown")

# 🎰 SLOT AVTOMATI O'YINI (Botga qarshi)
async def slot_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = check_user(user.id, user.first_name)
    
    if not context.args:
        await update.message.reply_text("❌ Tikish miqdorini yozing! Namuna: `/slot 1000`", parse_mode="Markdown")
        return
        
    try:
        bet = int(context.args[0])
    except:
        await update.message.reply_text("❌ Miqdorni faqat raqamda yozing!")
        return

    if bet <= 0:
        await update.message.reply_text("❌ Minimal tikish 1 so'm!")
        return

    if db["money"] < bet:
        await update.message.reply_text(f"❌ Hisobingizda yetarli mablag' yo'q! Balans: {db['money']:,} so'm")
        return

    db["money"] -= bet
    msg = await update.message.reply_dice(emoji="🎰")
    value = msg.dice.value 

    winning_values = [1, 22, 43, 64]
    await asyncio.sleep(2) 

    if value in winning_values:
        win_amount = bet * 5
        db["money"] += win_amount
        await update.message.reply_text(f"🎉 *DAXSHAT YUTUQ!* 🎉\n\n👤 {user.first_name} tuman slotda yutdi va *+{win_amount:,} so'm* oldi!\nHozirgi balans: {db['money']:,} so'm", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"📉 *Yutqazdingiz!* \n\n👤 {user.first_name}, slotda omadingiz kelmadi. *-{bet:,} so'm* ketdi.\nHozirgi balans: {db['money']:,} so'm", parse_mode="Markdown")

# 🎲 KUBIK O'YINI (Guruhda Reply orqali do'stiga qarshi)
async def dice_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    db = check_user(user.id, user.first_name)

    if not msg.reply_to_message:
        await msg.reply_text("❌ Do'stingiz bilan o'ynash uchun uning xabariga *Reply (Javob)* qilib `/dice MIQDOR` deb yozing!", parse_mode="Markdown")
        return

    target_user = msg.reply_to_message.from_user
    if target_user.id == user.id:
        await msg.reply_text("❌ O'zingiz bilan o'ynay olmaysiz!")
        return

    target_db = check_user(target_user.id, target_user.first_name)

    if not context.args:
        await msg.reply_text("❌ Tikish miqdorini yozing! Namuna: `/dice 2000`", parse_mode="Markdown")
        return

    try:
        bet = int(context.args[0])
    except:
        await msg.reply_text("❌ Miqdorni faqat raqamda yozing!")
        return

    if db["money"] < bet:
        await msg.reply_text(f"❌ Senda yetarli pul yo'q! Balans: {db['money']:,} so'm")
        return
    if target_db["money"] < bet:
        await msg.reply_text(f"❌ {target_user.first_name}da yetarli pul yo'q! Uning balansi: {target_db['money']:,} so'm")
        return

    db["money"] -= bet
    target_db["money"] -= bet

    await msg.reply_text(f"🎲 *Kubik o'yini boshlandi!* Tikilgan pul: *{bet*2:,} so'm*\n\n1. {user.first_name} kubik tashlamoqda...", parse_mode="Markdown")
    m1 = await msg.reply_dice(emoji="🎲")
    v1 = m1.dice.value

    await asyncio.sleep(2)

    await msg.reply_text(f"2. {target_user.first_name} kubik tashlamoqda...", parse_mode="Markdown")
    m2 = await msg.reply_dice(emoji="🎲")
    v2 = m2.dice.value

    await asyncio.sleep(2)

    if v1 > v2:
        db["money"] += (bet * 2)
        text = f"🏆 *{user.first_name} YUTDI!* ({v1} vs {v2})\n\nHamma pulni oldi! Jami balans: {db['money']:,} so'm"
    elif v2 > v1:
        target_db["money"] += (bet * 2)
        text = f"🏆 *{target_user.first_name} YUTDI!* ({v2} vs {v1})\n\nHamma pulni oldi! Jami balans: {target_db['money']:,} so'm"
    else:
        db["money"] += bet
        target_db["money"] += bet
        text = f"🤝 *Durang!* ({v1} vs {v2})\n\nPullar egalariga qaytarildi."

    await msg.reply_text(text, parse_mode="Markdown")

# 🎯 DART O'YINI (Guruhda Reply orqali do'stiga qarshi)
async def dart_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    db = check_user(user.id, user.first_name)

    if not msg.reply_to_message:
        await msg.reply_text("❌ Do'stingiz bilan dart o'ynash uchun uning xabariga *Reply (Javob)* qilib `/dart MIQDOR` deb yozing!", parse_mode="Markdown")
        return

    target_user = msg.reply_to_message.from_user
    if target_user.id == user.id: return

    target_db = check_user(target_user.id, target_user.first_name)

    if not context.args:
        await msg.reply_text("❌ Tikish miqdorini yozing! Namuna: `/dart 3000`", parse_mode="Markdown")
        return

    try: bet = int(context.args[0])
    except: return

    if db["money"] < bet or target_db["money"] < bet:
        await msg.reply_text("❌ Kimdadir pul yetarli emas!")
        return

    db["money"] -= bet
    target_db["money"] -= bet

    await msg.reply_text(f"🎯 *Dart jangi boshlandi!* Garov: *{bet*2:,} so'm*\n\n1. {user.first_name} nishonga otmoqda...", parse_mode="Markdown")
    m1 = await msg.reply_dice(emoji="🎯")
    v1 = m1.dice.value
    await asyncio.sleep(2)

    await msg.reply_text(f"2. {target_user.first_name} nishonga otmoqda...", parse_mode="Markdown")
    m2 = await msg.reply_dice(emoji="🎯")
    v2 = m2.dice.value
    await asyncio.sleep(2)

    if v1 > v2:
        db["money"] += (bet * 2)
        text = f"🏆 *{user.first_name} aniqroq urdi va YUTDI!* \n\nJami balans: {db['money']:,} so'm"
    elif v2 > v1:
        target_db["money"] += (bet * 2)
        text = f"🏆 *{target_user.first_name} aniqroq urdi va YUTDI!* \n\nJami balans: {target_db['money']:,} so'm"
    else:
        db["money"] += bet
        target_db["money"] += bet
        text = "🤝 *Durang!* Ikkalangiz ham bir xil urdingiz."

    await msg.reply_text(text, parse_mode="Markdown")

# 🏆 TOP REYTING
async def top_rich(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not USER_BALANCES:
        await update.message.reply_text("🏆 Hozircha hech kim ro'yxatda yo'q.")
        return
    sorted_users = sorted(USER_BALANCES.items(), key=lambda x: x[1]["money"], reverse=True)[:10]
    
    text = "🏆 *GURUHNING ENG BOY KAZINOCHILARI:* \n\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        text += f"{i}. 👤 {data['name']} — *{data['money']:,} so'm*\n"
        
    await update.message.reply_text(text, parse_mode="Markdown")

def main():
    Thread(target=run_server).start()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("casino", casino_menu))
    app.add_handler(CommandHandler("balans", balans))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("slot", slot_game))
    app.add_handler(CommandHandler("dice", dice_game))
    app.add_handler(CommandHandler("dart", dart_game))
    app.add_handler(CommandHandler("top", top_rich))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
    
