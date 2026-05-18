import os, random, asyncio, urllib.request, json
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Render uchun server
server = Flask('')
@server.route('/')
def home(): return "Casino Bot Muammosiz Aktiv!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# ASOSIY SOZLAMALAR
TOKEN = "8443418214:AAEwtTcxOw2kYScXq3beGJDagxou_H6iuAc"
MAIN_ADMIN = 7920504062  
TARGET_GROUP = "@yzbedkslls" 

USER_DATA = {}
ADMIN_STATE = {} 
GAME_BET_STATE = {} 

def get_user(user_id, name):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "name": name,
            "money": 6000,         
            "games_played": 0,      
            "group_bonus_received": False 
        }
    if user_id == MAIN_ADMIN:
        USER_DATA[user_id]["money"] = 999999999 
    return USER_DATA[user_id]

# requests o'rniga Python'ni o'zidagi urllib bilan guruhni tekshirish (100% xatosiz)
def check_group_member(user_id):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={TARGET_GROUP}&user_id={user_id}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            if res.get("ok"):
                status = res["result"]["status"]
                if status in ["creator", "administrator", "member"]:
                    return True
    except:
        pass
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = get_user(user.id, user.first_name)
    ADMIN_STATE.pop(user.id, None)
    GAME_BET_STATE.pop(user.id, None)

    text = (
        f"🎰 *Martin Kazino Botiga Xush Kelibsiz!*\n\n"
        f"💰 Sening hisobing: *{db['money']:,} so'm*\n\n"
        f"O'yin o'ynash va pul ishlash uchun tugmalarni bosing:"
    )
    
    kb = [
        [InlineKeyboardButton("🎮 Don-Don-Ziki O'ynash", callback_data="play_ddz")],
        [InlineKeyboardButton("💳 Pul kiritish", callback_data="deposit"), InlineKeyboardButton("💸 Pul yechish", callback_data="withdraw")],
        [InlineKeyboardButton("🎁 Kunlik Bonus", callback_data="bonus"), InlineKeyboardButton("🚀 Pul ishlash (4,000 UZS)", callback_data="earn")]
    ]
    if user.id == MAIN_ADMIN:
        kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin")])

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u_id = query.from_user.id
    db = get_user(u_id, query.from_user.first_name)
    back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="home")]])

    if query.data == "home":
        ADMIN_STATE.pop(u_id, None)
        GAME_BET_STATE.pop(u_id, None)
        kb = [
            [InlineKeyboardButton("🎮 Don-Don-Ziki O'ynash", callback_data="play_ddz")],
            [InlineKeyboardButton("💳 Pul kiritish", callback_data="deposit"), InlineKeyboardButton("💸 Pul yechish", callback_data="withdraw")],
            [InlineKeyboardButton("🎁 Kunlik Bonus", callback_data="bonus"), InlineKeyboardButton("🚀 Pul ishlash (4,000 UZS)", callback_data="earn")]
        ]
        if u_id == MAIN_ADMIN:
            kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin")])
        await query.edit_message_text(f"🎰 Joriy balansingiz: *{db['money']:,} so'm*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "deposit":
        await query.edit_message_text("💳 *Pul kiritish bo'limi*\n\nHisobni to'ldirish uchun adminga murojaat qiling!", parse_mode="Markdown", reply_markup=back_kb)

    elif query.data == "withdraw":
        await query.edit_message_text("⚠️ *Pul yechish rad etildi!*\n\n❌ Botdan eng kam pul yechish miqdori: *24,000 UZS*!", parse_mode="Markdown", reply_markup=back_kb)

    elif query.data == "bonus":
        rand_bonus = random.randint(200, 1000)
        db["money"] += rand_bonus
        await query.edit_message_text(f"🎁 *Tabriklaymiz!*\n\nSizga *+{rand_bonus} so'm* bonus berildi!\nHozirgi balans: *{db['money']:,} so'm*", parse_mode="Markdown", reply_markup=back_kb)

    elif query.data == "earn":
        if db["group_bonus_received"]:
            await query.edit_message_text("❌ Siz bu guruhga a'zo bo'lib bonusni olgansiz!", reply_markup=back_kb)
            return
        
        text = (
            "🚀 *PUL ISHLASH BO'LIMI*\n\n"
            "Guruhimizga obuna bo'ling va srazu *4,000 so'm* naqd pulga ega bo'ling:\n\n"
            "👉 https://t.me/yzbedkslls\n\n"
            "A'zo bo'lib bo'lgach, pastdagi tekshirish tugmasini bosing:"
        )
        kb = [
            [InlineKeyboardButton("🔗 Guruhga kirish", url="https://t.me/yzbedkslls")],
            [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "check_sub":
        if db["group_bonus_received"]:
            await query.edit_message_text("❌ Bonus allaqachon olingan!", reply_markup=back_kb)
            return

        if check_group_member(u_id):
            db["money"] += 4000
            db["group_bonus_received"] = True
            await query.edit_message_text(f"🎉 Hisobingizga *+4,000 so'm* qo'shildi!\n💰 Balans: *{db['money']:,} so'm*", parse_mode="Markdown", reply_markup=back_kb)
        else:
            await query.edit_message_text("❌ Siz hali guruhga a'zo bo'lmagansiz!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Guruhga kirish", url="https://t.me/yzbedkslls")],[InlineKeyboardButton("🔄 Qayta tekshirish", callback_data="check_sub")]]))

    elif query.data == "play_ddz":
        GAME_BET_STATE[u_id] = "waiting_bet"
        await query.edit_message_text(f"✌️ *Don-Don-Ziki O'yini*\n\nSizda joriy balans: *{db['money']:,} so'm*\n\n✍️ Qancha pul tikmoqchisiz? Miqdorini yozib yuboring (Kamida 600 so'm):", parse_mode="Markdown")

    elif query.data.startswith("ddz_"):
        choice = query.data.split("_")[1]
        bet = GAME_BET_STATE.get(u_id + 1000000000, 600)
        db["games_played"] += 1

        options = ["tosh", "qaychi", "qogoz"]
        names = {"tosh": "Tosh ✊", "qaychi": "Qaychi ✌️", "qogoz": "Qog'oz 🖐"}

        if db["games_played"] <= 2:
            if choice == "tosh": bot_choice = "qaychi"
            elif choice == "qaychi": bot_choice = "qogoz"
            else: bot_choice = "tosh"
            result = "win"
        else:
            bot_choice = random.choice(options)
            if choice == bot_choice: result = "draw"
            elif (choice == "tosh" and bot_choice == "qaychi") or \
                 (choice == "qaychi" and bot_choice == "qogoz") or \
                 (choice == "qogoz" and bot_choice == "tosh"): result = "win"
            else: result = "lose"

        text = f"🎮 *DON-DON-ZIKI JANGI*\n\n👤 Siz: {names[choice]}\n🤖 Bot: {names[bot_choice]}\n\n"
        if result == "win":
            db["money"] += (bet * 2)
            text += f"🏆 *Siz Yutdingiz!*\n💰 Hisobga: *+{bet*2:,} so'm* tushdi!\nBalans: {db['money']:,} so'm"
        elif result == "lose":
            text += f"📉 *Siz Yutqazdingiz!*\nKetgan pul: *-{bet:,} so'm*\nBalans: {db['money']:,} so'm"
        else:
            db["money"] += bet
            text += f"🤝 *Durang!* Pul o'zingizga qaytdi.\nBalans: {db['money']:,} so'm"
        
        GAME_BET_STATE.pop(u_id, None)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_kb)

    elif query.data == "admin" and u_id == MAIN_ADMIN:
        ADMIN_STATE[u_id] = "waiting"
        await query.edit_message_text("👑 *Admin Panel*\n\n📌 *Namuna:* `7920504062 5000` (ayrish uchun: `7920504062 -5000`)", parse_mode="Markdown")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = update.effective_user.id
    text = update.message.text.strip()
    db = get_user(u_id, update.effective_user.first_name)

    if GAME_BET_STATE.get(u_id) == "waiting_bet":
        try:
            bet = int(text)
            if bet < 600 or db["money"] < bet:
                await update.message.reply_text("❌ Pul kam yoki miqdor xato!")
                return
            
            db["money"] -= bet
            GAME_BET_STATE[u_id + 1000000000] = bet
            GAME_BET_STATE[u_id] = "playing"

            kb = [[InlineKeyboardButton("✊ Tosh", callback_data="ddz_tosh")],[InlineKeyboardButton("✌️ Qaychi", callback_data="ddz_qaychi")],[InlineKeyboardButton("🖐 Qog'oz", callback_data="ddz_qogoz")]]
            await update.message.reply_text(f"💰 *{bet:,} so'm* tikildi! Tanlang:", reply_markup=InlineKeyboardMarkup(kb))
        except:
            await update.message.reply_text("❌ Raqamda kiriting!")

    elif u_id == MAIN_ADMIN and ADMIN_STATE.get(u_id) == "waiting":
        try:
            target_id, amount = map(int, text.split())
            user_db = get_user(target_id, "O'yinchi")
            user_db["money"] += amount
            ADMIN_STATE.pop(u_id, None)
            await update.message.reply_text(f"✅ Balans o'zgardi! Yangi balans: *{user_db['money']:,} so'm*", parse_mode="Markdown")
        except:
            await update.message.reply_text("❌ Format xato. Namuna: `7920504062 10000`")

def main():
    Thread(target=run_server).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
    
