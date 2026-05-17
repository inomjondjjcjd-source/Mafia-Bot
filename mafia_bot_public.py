import os, random, asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

server = Flask('')
@server.route('/')
def home(): return "Martin Mafia Bot Tirik!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

TOKEN = "8771036463:AAE5c354ocQFb6qtrmQ2oI0gEx1MHHvvmG0"
MAIN_ADMIN = 7920504062  
ASSISTANT_ADMINS = set() 
BANNED_USERS = set()     

USER_DATA = {}
GAMES = {}
ASK_STATE = {}  
ACTIVE_PROMOCODES = {}  

def get_user(user_id, name, username):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "name": name, "username": username or "yoq",
            "balance": 100, "money_uzs": 0, "role": "Tasodifiy 🎲", 
            "armor": False, "pistol": False, "camera": False, "wins": 0,
            "used_promos": []  
        }
        # Yordamchi admin qo'shilganda olmosi srazu 129 ta bo'ladi, puli esa cheksiz emas!
        if user_id in ASSISTANT_ADMINS:
            USER_DATA[user_id]["balance"] = 129
            USER_DATA[user_id]["money_uzs"] = 0

    # Faqat Bosh Admin hisobi cheksiz bo'lib qoladi
    if user_id == MAIN_ADMIN:
        USER_DATA[user_id]["balance"] = 999999
        USER_DATA[user_id]["money_uzs"] = 999999
        
    return USER_DATA[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in BANNED_USERS: return
    get_user(user.id, user.first_name, user.username)
    
    if update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("🎮 Guruhda o'yinni boshlash uchun /game buyrug'ini yuboring!")
        return

    text = "🕵️‍♂️ *Martin Mafia Botiga Xush Kelibsiz!*\n\nO'yinlarda yuting, so'm ishlang, promokodlarni kiriting va ularni olmoslarga almashtiring!"
    kb = [
        [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("📊 Hisob (Profil)", callback_data="my_account"), InlineKeyboardButton("🛒 Do'kon", callback_data="shop")],
        [InlineKeyboardButton("🎟 Promokod kiritish", callback_data="enter_promo"), InlineKeyboardButton("🏆 Reyting", callback_data="rank")],
        [InlineKeyboardButton("🙋‍♂️ Olmos so'rash", callback_data="ask")]
    ]
    if user.id == MAIN_ADMIN or user.id in ASSISTANT_ADMINS:
        kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def send_ask_to_admins(user, amount, context):
    u_id = user.id
    kb = [[InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{u_id}_{amount}"), InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{u_id}")]]
    msg = f"🔔 *Yangi Olmos So'rovi!*\n\n👤 {user.first_name}\n🆔 ID: `{u_id}`\n💰 Miqdor: *{amount} 💎*"
    for adm in [MAIN_ADMIN] + list(ASSISTANT_ADMINS):
        try: await context.bot.send_message(chat_id=adm, text=msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        except: pass

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = update.effective_user.id
    text = update.message.text.strip()
    if u_id in BANNED_USERS or u_id not in ASK_STATE: return

    # 1. Olmos so'rash
    if ASK_STATE[u_id] == "waiting_amount" and text.isdigit():
        ASK_STATE.pop(u_id)
        await update.message.reply_text(f"⏳ {text} ta olmos so'rovi yuborildi...")
        await send_ask_to_admins(update.effective_user, int(text), context)

    # 2. Yordamchi admin qo'shish
    elif u_id == MAIN_ADMIN and ASK_STATE[u_id] == "waiting_assistant_id" and text.isdigit():
        ASK_STATE.pop(u_id)
        target_admin = int(text)
        ASSISTANT_ADMINS.add(target_admin)
        # Srazu bazada bo'lsa olmosini 129 qilib qo'yamiz
        if target_admin in USER_DATA:
            USER_DATA[target_admin]["balance"] = 129
            USER_DATA[target_admin]["money_uzs"] = 0
        await update.message.reply_text(f"✅ ID {text} Yordamchi Admin bo'ldi! Balansi: 129 olmos qilib belgilandi.")

    # 3. Admin: Olmos berish/olish mantiqi
    elif (u_id == MAIN_ADMIN or u_id in ASSISTANT_ADMINS) and ASK_STATE[u_id] == "waiting_give_data":
        try:
            tid, amt = map(int, text.split())
            user_db = get_user(tid, "O'yinchi", "")
            user_db["balance"] += amt
            ASK_STATE.pop(u_id)
            status_text = f"ko'paytirildi (+{amt})" if amt >= 0 else f"kamaytirildi ({amt})"
            await update.message.reply_text(f"✅ ID `{tid}` ning olmoslari {status_text}! Hozirgi olmosi: {user_db['balance']} ta.")
        except:
            await update.message.reply_text("❌ Xato format! Namuna: `12345 50` (qo'shish) yoki `12345 -20` (kamaytirish)")

    # 🔥 NEW: Admin: Pul (UZS) ko'paytirish yoki kamaytirish mantiqi
    elif (u_id == MAIN_ADMIN or u_id in ASSISTANT_ADMINS) and ASK_STATE[u_id] == "waiting_give_money_data":
        try:
            tid, amt = map(int, text.split())
            user_db = get_user(tid, "O'yinchi", "")
            user_db["money_uzs"] += amt
            if user_db["money_uzs"] < 0: user_db["money_uzs"] = 0 # Minusga kirib ketmasligi uchun
            ASK_STATE.pop(u_id)
            status_text = f"ko'paytirildi (+{amt} UZS)" if amt >= 0 else f"kamaytirildi ({amt} UZS)"
            await update.message.reply_text(f"✅ ID `{tid}` ning pullari {status_text}! Hozirgi balansi: {user_db['money_uzs']} UZS.")
        except:
            await update.message.reply_text("❌ Xato format! Namuna: `12345 5000` (pul qo'shish) yoki `12345 -3000` (pul kamaytirish)")

    # 4. Foydalanuvchini banlash
    elif ASK_STATE[u_id] == "waiting_ban_id" and text.isdigit():
        ASK_STATE.pop(u_id)
        BANNED_USERS.add(int(text))
        await update.message.reply_text("🚫 Bloklandi!")

    # 5. Admin Panel: Promokod yaratish
    elif (u_id == MAIN_ADMIN or u_id in ASSISTANT_ADMINS) and ASK_STATE[u_id] == "waiting_promo_create":
        try:
            p_code, p_val = text.split()
            p_code = p_code.upper()
            p_val = int(p_val)
            ACTIVE_PROMOCODES[p_code] = p_val
            ASK_STATE.pop(u_id)
            await update.message.reply_text(f"✅ *Promokod Yaratildi!*\n\n🎟 Kod: `{p_code}`\n💎 Olmos: *{p_val} ta*", parse_mode="Markdown")
        except:
            await update.message.reply_text("❌ Xato format!\nNamuna: `OMADLI 50`")

    # 6. Foydalanuvchi promokod kiritganda
    elif ASK_STATE[u_id] == "waiting_promo_enter":
        u_promo = text.upper()
        db = get_user(u_id, update.effective_user.first_name, update.effective_user.username)
        if u_promo not in ACTIVE_PROMOCODES:
            await update.message.reply_text("❌ Bunday promokod mavjud emas!")
            return
        if "used_promos" not in db: db["used_promos"] = []
        if u_promo in db["used_promos"]:
            await update.message.reply_text("⚠️ Siz bu promokoddan foydalanib bo'lgansiz!")
            return
        bonus = ACTIVE_PROMOCODES[u_promo]
        db["balance"] += bonus
        db["used_promos"].append(u_promo)
        ASK_STATE.pop(u_id)
        await update.message.reply_text(f"🎉 `{u_promo}` faollashdi! *+{bonus} 💎* qo'shildi!", parse_mode="Markdown")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u_id = query.from_user.id
    if u_id in BANNED_USERS: return
    db = get_user(u_id, query.from_user.first_name, query.from_user.username)

    if query.data == "my_account":
        text = (
            f"📊 *Sizning Hisobingiz:*\n\n"
            f"👤 *Ism:* {query.from_user.first_name}\n"
            f"🆔 *ID:* `{u_id}`\n"
            f"💳 *Olmos:* {'Cheksiz' if u_id==MAIN_ADMIN else db['balance']}\n"
            f"💰 *Pul:* {'Cheksiz' if u_id==MAIN_ADMIN else db['money_uzs']} UZS\n"
            f"🏆 *Yutuqlar:* {db['wins']} ta\n"
            f"🛡 *Zirh:* {'Bor ✅' if db['armor'] else 'Yoq ❌'}"
        )
        kb = [[InlineKeyboardButton("🔄 1000 UZS -> 10 Olmos", callback_data="exchange")], [InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "exchange":
        if u_id == MAIN_ADMIN:
            await query.answer("👑 Siz bosh adminsiz, pulingiz cheksiz!", show_alert=True)
            return
        if db["money_uzs"] >= 1000:
            db["money_uzs"] -= 1000
            db["balance"] += 10
            await query.answer("🎉 +10 Olmos qo'shildi!", show_alert=True)
            await buttons(update, context)
        else:
            await query.answer("❌ Pul yetarli emas!", show_alert=True)

    elif query.data == "enter_promo":
        ASK_STATE[u_id] = "waiting_promo_enter"
        await query.edit_message_text("🎟 *Sizdagi promokodni yozib yuboring:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]]))

    elif query.data == "shop":
        text = "🛍️ *Do'kon:* Mafiya (50 💎), Shifokor (30 💎), Komissar (40 💎), Zirh (70 💎), To'pponcha (100 💎), Kamera (60 💎)"
        kb = [
            [InlineKeyboardButton("🕶 Mafiya", callback_data="b_mafia"), InlineKeyboardButton("🧰 Shifokor", callback_data="b_doc")],
            [InlineKeyboardButton("🕵️‍♂️ Komissar", callback_data="b_cop"), InlineKeyboardButton("🛡 Zirh", callback_data="b_arm")],
            [InlineKeyboardButton("🔫 To'pponcha", callback_data="b_pistol"), InlineKeyboardButton("👁 Kamera", callback_data="b_camera")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "home":
        ASK_STATE.pop(u_id, None)
        await query.edit_message_text("🕵️‍♂️ Martin Mafia Bot menyusi:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("📊 Hisob", callback_data="my_account"), InlineKeyboardButton("🛒 Do'kon", callback_data="shop")],
            [InlineKeyboardButton("🎟 Promokod kiritish", callback_data="enter_promo"), InlineKeyboardButton("🏆 Reyting", callback_data="rank")],
            [InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")] if u_id==MAIN_ADMIN or u_id in ASSISTANT_ADMINS else [InlineKeyboardButton("🏆 Reyting", callback_data="rank")]
        ]))

    # KATTA ADMIN PANEL INTERFEYSI
    elif query.data == "admin_panel":
        if u_id != MAIN_ADMIN and u_id not in ASSISTANT_ADMINS: return
        text = f"👑 *Admin Panel*\n\nO'yinchilar: {len(USER_DATA)} ta\nFaol promokodlar: {len(ACTIVE_PROMOCODES)} ta"
        kb = [
            [InlineKeyboardButton("💎 Olmos +/-", callback_data="adm_give"), InlineKeyboardButton("💰 Pul +/-", callback_data="adm_give_money")],
            [InlineKeyboardButton("🎟 Promokod Yaratish", callback_data="adm_create_promo"), InlineKeyboardButton("🚫 Banlash", callback_data="adm_ban")]
        ]
        if u_id == MAIN_ADMIN: kb.append([InlineKeyboardButton("➕ Yordamchi Admin", callback_data="adm_add")])
        kb.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="home")])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "adm_add": ASK_STATE[u_id] = "waiting_assistant_id"; await query.edit_message_text("Yordamchi admin bo'ladigan shaxsning ID raqamini yuboring:")
    elif query.data == "adm_give": ASK_STATE[u_id] = "waiting_give_data"; await query.edit_message_text("Olmosini o'zgartirmoqchi bo'lgan ID va miqdorni yozing.\n\nKo'paytirish uchun: `12345 50`\nKamaytirish uchun: `12345 -30`")
    elif query.data == "adm_give_money": ASK_STATE[u_id] = "waiting_give_money_data"; await query.edit_message_text("Pulini o'zgartirmoqchi bo'lgan ID va UZS miqdorini yozing.\n\nKo'paytirish uchun: `12345 5000`\nKamaytirish uchun: `12345 -2000`")
    elif query.data == "adm_ban": ASK_STATE[u_id] = "waiting_ban_id"; await query.edit_message_text("Ban qilmoqchi bo'lgan odam ID raqamini yuboring:")

    elif query.data == "adm_create_promo":
        if u_id != MAIN_ADMIN and u_id not in ASSISTANT_ADMINS: return
        ASK_STATE[u_id] = "waiting_promo_create"
        await query.edit_message_text("🎟 *Promokod nomi va beradigan olmos miqdorini yozing:*\n\nNamuna: `OMADLI 50`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_panel")]]))

    elif query.data.startswith("approve_"):
        _, tid, amt = query.data.split("_")
        get_user(int(tid), "O'yinchi", "")["balance"] += int(amt)
        await query.edit_message_text("✅ Tasdiqlandi!")

    elif query.data.startswith("b_"):
        item = query.data.split("_")[1]
        prices = {"mafia": 50, "doc": 30, "cop": 40, "arm": 70, "pistol": 100, "camera": 60}
        if db["balance"] >= prices[item] or u_id == MAIN_ADMIN:
            if u_id != MAIN_ADMIN: db["balance"] -= prices[item]
            if item == "arm": db["armor"] = True
            elif item == "pistol": db["pistol"] = True
            elif item == "camera": db["camera"] = True
            else: db["role"] = "Mafiya 🕶" if item=="mafia" else "Shifokor 🧰" if item=="doc" else "Komissar 🕵️‍♂️"
            await query.edit_message_text("🎉 Xarid qilindi!")

    elif query.data.startswith("j_"):
        g_id = int(query.data.split("_")[1])
        if g_id in GAMES and GAMES[g_id]["status"] == "join" and u_id not in GAMES[g_id]["players"]:
            GAMES[g_id]["players"][u_id] = {"name": query.from_user.first_name, "role": None}
            await context.bot.send_message(chat_id=g_id, text=f"✅ {query.from_user.first_name} qo'shildi!")

    elif query.data.startswith("admin_start_"):
        g_id = int(query.data.split("_")[2])
        if (u_id == MAIN_ADMIN or u_id in ASSISTANT_ADMINS) and g_id in GAMES and GAMES[g_id]["status"] == "join":
            GAMES[g_id]["status"] = "playing"
            await start_game_logic(g_id, context)

async def game_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g_id = update.effective_chat.id
    if update.effective_chat.type not in ["group", "supergroup"] or update.effective_user.id in BANNED_USERS: return
    GAMES[g_id] = {"status": "join", "players": {}}
    kb = [[InlineKeyboardButton("➕ O'yinga qo'shilish", callback_data=f"j_{g_id}")], [InlineKeyboardButton("▶️ Boshlash (Admin)", callback_data=f"admin_start_{g_id}")]]
    await update.message.reply_text("🎬 *Martin Mafia boshlandi!*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def start_game_logic(g_id, context):
    p_ids = list(GAMES[g_id]["players"].keys())
    if len(p_ids) < 4:
        await context.bot.send_message(chat_id=g_id, text="❌ Kamida 4 kishi kerak!")
        return
    random.shuffle(p_ids)
    GAMES[g_id]["players"][p_ids[0]]["role"] = "Mafiya 🕶"
    GAMES[g_id]["players"][p_ids[1]]["role"] = "Shifokor 🧰"
    GAMES[g_id]["players"][p_ids[2]]["role"] = "Komissar 🕵️‍♂️"
    for i in range(3, len(p_ids)): GAMES[g_id]["players"][p_ids[i]]["role"] = "Tinch aholi 🕊"

    for pid, pdata in GAMES[g_id]["players"].items():
        try: await context.bot.send_message(chat_id=pid, text=f"🎭 Roliz: {pdata['role']}")
        except: pass
    await context.bot.send_message(chat_id=g_id, text="🎭 Rollar yuborildi. G'oliblarga 400 UZS berildi!")
    
    for pid in p_ids:
        u = get_user(pid, GAMES[g_id]["players"][pid]["name"], "")
        u["money_uzs"] += 400
        u["wins"] += 1

def main():
    Thread(target=run_server).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("game", game_cmd))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
        
