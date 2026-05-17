import os, random, asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Render server
server = Flask('')
@server.route('/')
def home(): return "Martin DonDonZiki Casino Bot Tirik!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# Sozlamalar
TOKEN = "8443418214:AAEwtTcxOw2kYScXq3beGJDagxou_H6iuAc"
MAIN_ADMIN = 7920504062  

USER_DATA = {} # Foydalanuvchilar bazasi
ASK_STATE = {} # Admin uchun holatlar

def get_user(user_id, name):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "name": name,
            "money": 6000, # Yangi kirganda 6000 so'm tushadi
            "games_played": 0 # Necha marta don-don-ziki o'ynagani (birinchi 2 tasini yutqazib berish uchun)
        }
    if user_id == MAIN_ADMIN:
        USER_DATA[user_id]["money"] = 999999999 # Admin hisobi cheksiz
    return USER_DATA[user_id]

# /start buyrug'i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = get_user(user.id, user.first_name)
    ASK_STATE.pop(user.id, None)

    if update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("🎰 Don-don-ziki Kazino boti tayyor! O'yin menyusini ochish uchun /casino deb yozing!")
        return

    text = (
        f"👋 *Xush kelibsiz, {user.first_name}!*\n\n"
        f"💰 Hisobingizga boshlang'ich *6,000 so'm* taqdim etildi!\n"
        f"Bot orqali pul ishlang va Don-don-ziki o'yinida omadingizni sinang!"
    )
    
    kb = [
        [InlineKeyboardButton("💰 Hisobni tekshirish", callback_data="my_balance")],
        [InlineKeyboardButton("💳 Pul kiritish", callback_data="deposit"), InlineKeyboardButton("💸 Pul yechish", callback_data="withdraw")],
        [InlineKeyboardButton("🎁 Har soatlik Bonus", callback_data="get_bonus"), InlineKeyboardButton("🚀 Pul ishlash", callback_data="earn_money")],
        [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")]
    ]
    
    if user.id == MAIN_ADMIN:
        kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# Guruh uchun menyu
async def casino_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return
    text = (
        "✌️ *KAZINO DON-DON-ZIKI MENYUSI* 🖐\n\n"
        "O'ynash uchun biron bir xabarga *Reply (Javob)* qiling va miqdorni yozing:\n"
        "👉 `/ddz MIQDOR` (Eng kam tikish: 600 so'm)\n\n"
        "📌 *Masalan:* `/ddz 1000`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# Knopkalar mantiqi
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u_id = query.from_user.id
    db = get_user(u_id, query.from_user.first_name)

    if query.data == "my_balance":
        await query.edit_message_text(f"💰 Sening joriy balansing: *{db['money']:,} so'm*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_home")]]))
        
    elif query.data == "deposit":
        await query.edit_message_text("💳 *Pul kiritish bo'limi*\n\nHisobingizni to'ldirish uchun adminga murojaat qiling yoki tez kunda avtomat to'lovlar qo'shiladi!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_home")]]))
        
    elif query.data == "withdraw":
        await query.edit_message_text("⚠️ *Pul yechish rad etildi!*\n\n❌ Botingizdan eng kam pul yechish miqdori: *24,000 UZS* qilib belgilangan!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_home")]]))
        
    elif query.data == "get_bonus":
        # Random 200 dan 1000 so'mgacha
        bonus_amount = random.randint(200, 1000)
        db["money"] += bonus_amount
        await query.edit_message_text(f"🎁 *Tabriklaymiz!*\n\nSizga tasodifiy *+{bonus_amount} so'm* bonus berildi!\nHozirgi balans: *{db['money']:,} so'm*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_home")]]))
        
    elif query.data == "earn_money":
        text = "🚀 *Pul ishlash yo'llari:*\n\n1. Do'stlarni botga taklif qiling.\n2. Guruhlarda `/ddz` buyrug'i orqali don-don-ziki o'ynab balansingizni 2 barobar qiling!"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_home")]]))
        
    elif query.data == "back_home":
        ASK_STATE.pop(u_id, None)
        kb = [
            [InlineKeyboardButton("💰 Hisobni tekshirish", callback_data="my_balance")],
            [InlineKeyboardButton("💳 Pul kiritish", callback_data="deposit"), InlineKeyboardButton("💸 Pul yechish", callback_data="withdraw")],
            [InlineKeyboardButton("🎁 Har soatlik Bonus", callback_data="get_bonus"), InlineKeyboardButton("🚀 Pul ishlash", callback_data="earn_money")],
            [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")]
        ]
        if u_id == MAIN_ADMIN:
            kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
        await query.edit_message_text("🎰 Martin Kazino Bot Bosh Menyusi:", reply_markup=InlineKeyboardMarkup(kb))

    # ADMIN PANEL MANTIQLARI
    elif query.data == "admin_panel" and u_id == MAIN_ADMIN:
        text = "👑 *Bosh Admin Panel*\n\nFoydalanuvchilar hisobini boshqarish uchun kerakli bo'limni tanlang:"
        kb = [
            [InlineKeyboardButton("➕ Balans Qo'shish / Ayirish", callback_data="adm_change_balance")],
            [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="back_home")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        
    elif query.data == "adm_change_balance" and u_id == MAIN_ADMIN:
        ASK_STATE[u_id] = "waiting_balance_edit"
        await query.edit_message_text("✍️ Foydalanuvchi *ID* raqamini va o'zgartirmoqchi bo'lgan *PUL* miqdorini yozib yuboring:\n\n*Namuna (Pul berish):* `1234567 15000`\n*Namuna (Pulni ayirish):* `1234567 -5000`", parse_mode="Markdown")

# Admin xabar yuborganda hisobni o'zgartirish
async def admin_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = update.effective_user.id
    text = update.message.text.strip()
    
    if u_id == MAIN_ADMIN and ASK_STATE.get(u_id) == "waiting_balance_edit":
        try:
            target_id, amount = map(int, text.split())
            user_db = get_user(target_id, "O'yinchi")
            user_db["money"] += amount
            ASK_STATE.pop(u_id, None)
            await update.message.reply_text(f"✅ ID `{target_id}` balansi o'zgartirildi!\n💰 Yangi balans: *{user_db['money']:,} so'm*", parse_mode="Markdown")
        except:
            await update.message.reply_text("❌ Xato format! Qaytadan to'g'ri ID va miqdorni kiriting. Namuna: `7920504062 10000`")

# ✌️✊🖐 DON-DON-ZIKI O'YINI MANTIQLI (Guruhda)
async def ddz_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    db = get_user(user.id, user.first_name)

    if update.effective_chat.type not in ["group", "supergroup"]:
        await msg.reply_text("❌ Bu o'yinni faqat guruhlar ichida o'ynashingiz mumkin!")
        return

    if not context.args:
        await msg.reply_text("❌ Tikish miqdorini yozing! Namuna: `/ddz 600`")
        return

    try:
        bet = int(context.args[0])
    except:
        await msg.reply_text("❌ Miqdorni faqat butun raqamlarda yozing!")
        return

    if bet < 600:
        await msg.reply_text("❌ Minimal tikish miqdori *600 so'm* bo'lishi kerak!", parse_mode="Markdown")
        return

    if db["money"] < bet:
        await msg.reply_text(f"❌ Hisobingizda pul yetarli emas! Senda: *{db['money']:,} so'm* bor.", parse_mode="Markdown")
        return

    # O'yinchidan pulni vaqtincha chegirib turamiz
    db["money"] -= bet
    db["games_played"] += 1

    options = ["Tosh ✊", "Qaychi ✌️", "Qog'oz 🖐"]
    user_choice = random.choice(options) # O'yinchining tasodifiy tanlovi

    # 🔥 SIZ AYTGAN MANTIQ: Agar dastlabki 2 ta o'yin bo'lsa - bot ATAYIN yutqazib beradi (O'yinchi yutadi)
    if db["games_played"] <= 2:
        if user_choice == "Tosh ✊": bot_choice = "Qaychi ✌️"
        elif user_choice == "Qaychi ✌️": bot_choice = "Qog'oz 🖐"
        else: bot_choice = "Tosh ✊"
        result = "win"
    else:
        # 2 tadan keyin tizim halol va tasodifiy (O'yinchi ko'proq yutishi uchun random)
        bot_choice = random.choice(options)
        if user_choice == bot_choice: result = "draw"
        elif (user_choice == "Tosh ✊" and bot_choice == "Qaychi ✌️") or \
             (user_choice == "Qaychi ✌️" and bot_choice == "Qog'oz 🖐") or \
             (user_choice == "Qog'oz 🖐" and bot_choice == "Tosh ✊"):
            result = "win"
        else:
            result = "lose"

    # Natijani e'lon qilish
    game_text = (
        f"🎮 *DON-DON-ZIKI JANGI* 🎮\n\n"
        f"👤 *{user.first_name}* tanladi:  {user_choice}\n"
        f"🤖 *Bot* tanladi:  {bot_choice}\n\n"
    )

    if result == "win":
        win_money = bet * 2
        db["money"] += win_money
        game_text += f"🏆 *Siz YUTDINGIZ!* Tikilgan pul 2 barobar bo'lib qaytdi.\n➕ Hisobingizga *+{win_money:,} so'm* qo'shildi!\n💰 Balans: {db['money']:,} so'm"
    elif result == "lose":
        game_text += f"📉 *Siz YUTQAZDINGIZ!* \n➖ Hisobingizdan *-{bet:,} so'm* ketdi.\n💰 Balans: {db['money']:,} so'm"
    else:
        db["money"] += bet # Pul o'ziga qaytadi
        game_text += f"🤝 *Durang!* Ikkalangiz ham bir xil tanladingiz.\n💰 Pul o'zingizga qaytdi. Balans: {db['money']:,} so'm"

    await msg.reply_text(game_text, parse_mode="Markdown")

def main():
    Thread(target=run_server).start()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("casino", casino_menu))
    app.add_handler(CommandHandler("ddz", ddz_game))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_text_handler))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
    
