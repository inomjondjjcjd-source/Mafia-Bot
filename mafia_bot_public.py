import os
import logging
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Log tizimi
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Yangi Bot Tokeni
TOKEN = "8771036463:AAFtaCJUKZmB7B0fazFKkZ_slVN7eHtHn2A"

# Admin sozlamalari
ADMIN_ID = 7920504062
ADMIN_GROUP_ID = -7920504062

USER_DATA = {}
GAMES = {}

def get_or_create_user(user_id, username, first_name):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "name": first_name,
            "username": username or "Mavjud emas",
            "balance": 100,
            "selected_role": "Tasodifiy",
            "has_armor": False,
            "wins": 0,
            "games_played": 0,
            "used_promo": False
        }
    if user_id == ADMIN_ID:
        USER_DATA[user_id]["balance"] = float('inf')
    return USER_DATA[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_or_create_user(user.id, user.username, user.first_name)
    
    if update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("🤖 Guruhda o'yin boshlash uchun /game buyrug'ini yuboring!")
        return
        
    if user.id == ADMIN_ID:
        bal_str = "Cheksiz"
    else:
        bal_str = str(db_user["balance"])
        
    if db_user["has_armor"]:
        armor_str = "Mavjud"
    else:
        armor_str = "Yo'q"
        
    text = (
        "🕵️‍♂️ **True Mafia Botiga Xush Kelibsiz!**\n\n"
        f"👤 Ismingiz: {user.first_name}\n"
        f"💎 Balansingiz: {bal_str} olmos\n"
        f"🎯 Keyingi o'yin roli: *{db_user['selected_role']}*\n"
        f"🛡️ Zirh (Bronjilet): *{armor_str}*\n\n"
        "🎁 Maxfiy promo-kodni faollashtirish uchun: `/promokod KOD` deb yozing."
    )
    
    keyboard = [
        [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("🛒 Shop (Do'kon)", callback_data="open_shop"), InlineKeyboardButton("🏆 Reyting", callback_data="ranking")],
        [InlineKeyboardButton("💎 Olmos so'rash", callback_data="ask_diamonds")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = get_or_create_user(user_id, update.effective_user.username, update.effective_user.first_name)
    
    if not context.args:
        await update.message.reply_text("❌ Ishlatish formati: /promokod 255500")
        return
        
    code = context.args[0].strip()
    if code != "255500":
        await update.message.reply_text("❌ Noto'g'ri promo-kod kiritdingiz!")
        return
        
    if db_user["used_promo"]:
        await update.message.reply_text("❌ Siz ushbu maxfiy promo-koddan allaqachon foydalangansiz!")
        return
        
    db_user["used_promo"] = True
    if user_id != ADMIN_ID:
        db_user["balance"] += 500
    await update.message.reply_text("✅ Promo-kod muvaffaqiyatli faollashdi! Balansingizga 500 olmos qo'shildi.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u_id = query.from_user.id
    db_user = get_or_create_user(u_id, query.from_user.username, query.from_user.first_name)
    
    if query.data == "open_shop":
        text = (
            "🛒 **True Mafia Do'koni**\n\n"
            "1. Mafiya roli (Keyingi o'yin uchun) — 50 olmos\n"
            "2. Shifokor roli (Keyingi o'yin uchun) — 30 olmos\n"
            "3. Komissar roli (Keyingi o'yin uchun) — 40 olmos\n"
            "4. Maxsus Zirh (Bronjilet) — 70 olmos\n\n"
            "Sotib olmoqchi bo'lgan narsangizni tanlang:"
        )
        kb = [
            [InlineKeyboardButton("🎭 Mafiya (50)", callback_data="buy_mafiya"), InlineKeyboardButton("🚑 Shifokor (30)", callback_data="buy_doc")],
            [InlineKeyboardButton("👮 Komissar (40)", callback_data="buy_cop"), InlineKeyboardButton("🛡️ Zirh (70)", callback_data="buy_armor")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        
    elif query.data == "back_to_main":
        if u_id == ADMIN_ID:
            bal_str = "Cheksiz"
        else:
            bal_str = str(db_user["balance"])
            
        if db_user["has_armor"]:
            armor_str = "Mavjud"
        else:
            armor_str = "Yo'q"
            
        text = (
            "🕵️‍♂️ **True Mafia Botiga Xush Kelibsiz!**\n\n"
            f"👤 Ismingiz: {query.from_user.first_name}\n"
            f"💎 Balansingiz: {bal_str} olmos\n"
            f"🎯 Keyingi o'yin roli: *{db_user['selected_role']}*\n"
            f"🛡️ Zirh (Bronjilet): *{armor_str}*\n\n"
            "🎁 Maxfiy promo-kodni faollashtirish uchun: `/promokod KOD` deb yozing."
        )
        kb = [
            [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🛒 Shop (Do'kon)", callback_data="open_shop"), InlineKeyboardButton("🏆 Reyting", callback_data="ranking")],
            [InlineKeyboardButton("💎 Olmos so'rash", callback_data="ask_diamonds")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        
    elif query.data.startswith("buy_"):
        item = query.data.split("_")[1]
        prices = {"mafiya": 50, "doc": 30, "cop": 40, "armor": 70}
        roles = {"mafiya": "Mafiya", "doc": "Shifokor", "cop": "Komissar"}
        cost = prices[item]
        
        if u_id != ADMIN_ID and db_user["balance"] < cost:
            await query.edit_message_text("❌ Olmoslaringiz yetarli emas!", 
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Do'konga qaytish", callback_data="open_shop")]]))
            return
            
        if u_id != ADMIN_ID:
            db_user["balance"] -= cost
            
        if item == "armor":
            db_user["has_armor"] = True
            await query.edit_message_text("🛡️ Maxsus Zirh muvaffaqiyatli sotib olindi!",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]]))
        else:
            db_user["selected_role"] = roles[item]
            await query.edit_message_text(f"🎯 Keyingi o'yin uchun roli *{roles[item]}* qilib belgilandi!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]]), parse_mode="Markdown")
            
    elif query.data == "ranking":
        sorted_users = sorted(USER_DATA.items(), key=lambda x: x[1]["wins"], reverse=True)[:10]
        text = "🏆 **True Mafia Eng Kuchli O'yinchilar Reytingi:**\n\n"
        if not sorted_users:
            text += "Hozircha g'oliblar yo'q."
        else:
            for i, (usr_id, data) in enumerate(sorted_users, 1):
                text += f"{i}. {data['name']} — {data['wins']} ta g'alaba\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]]), parse_mode="Markdown")
        
    elif query.data == "ask_diamonds":
        await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=f"🔔 O'yinchi {query.from_user.first_name} (ID: {u_id}) tekin olmos so'ramoqda!")
        await query.edit_message_text("✅ So'rov adminga yuborildi!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]]))

    elif query.data.startswith("join_"):
        g_id = int(query.data.split("_")[1])
        if g_id not in GAMES or GAMES[g_id]["status"] != "join":
            return
        if u_id in GAMES[g_id]["players"]:
            return
        GAMES[g_id]["players"][u_id] = {"id": u_id, "name": query.from_user.first_name, "role": None, "alive": True}
        await context.bot.send_message(chat_id=g_id, text=f"✅ {query.from_user.first_name} o'yinga qo'shildi!")

    elif query.data.startswith("mafia_vote_") or query.data.startswith("doc_vote_") or query.data.startswith("cop_vote_"):
        parts = query.data.split("_")
        action = parts[0]
        g_id = int(parts[2])
        target_id = int(parts[3])
        
        if g_id not in GAMES or GAMES[g_id]["status"] != "night":
            return
            
        my_role = GAMES[g_id]["players"][u_id]["role"]
        if action == "mafia" and my_role == "Mafiya":
            GAMES[g_id]["mafia_vote"] = target_id
            await query.edit_message_text(f"🔴 Tanlandi: {GAMES[g_id]['players'][target_id]['name']}")
        elif action == "doc" and my_role == "Shifokor":
            GAMES[g_id]["doc_vote"] = target_id
            await query.edit_message_text(f"🟢 Tanlandi: {GAMES[g_id]['players'][target_id]['name']}")
        elif action == "cop" and my_role == "Komissar":
            GAMES[g_id]["cop_vote"] = target_id
            if GAMES[g_id]["players"][target_id]["role"] == "Mafiya":
                is_mafia = "Mafiya"
            else:
                is_mafia = "Tinch aholi"
            await query.edit_message_text(f"🔍 Natija: {is_mafia}")

    elif query.data.startswith("day_vote_"):
        parts = query.data.split("_")
        g_id = int(parts[2])
        target_id = int(parts[3])
        if g_id not in GAMES or GAMES[g_id]["status"] != "day":
            return
        if not GAMES[g_id]["players"][u_id]["alive"]:
            return
        GAMES[g_id]["day_votes"][u_id] = target_id
        await context.bot.send_message(chat_id=g_id, text=f"🗳️ {GAMES[g_id]['players'][u_id]['name']} o'yinchisi ovoz berdi!")

async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g_id = update.effective_chat.id
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Bu buyruqni faqat guruhlarda ishlatish mumkin!")
        return
        
    if g_id in GAMES and GAMES[g_id]["status"] != "ended":
        await update.message.reply_text("❌ Guruhda o'yin ketmoqda!")
        return
        
    GAMES[g_id] = {
        "status": "join",
        "players": {},
        "mafia_vote": None,
        "doc_vote": None,
        "cop_vote": None,
        "day_votes": {},
        "cycle": 1
    }
    
    kb = [[InlineKeyboardButton("🎮 O'yinga qo'shilish", callback_data=f"join_{g_id}")]]
    await update.message.reply_text("🎭 **True Mafia o'yini boshlanmoqda!**\n\nKamida 4 ta o'yinchi kerak.", reply_markup=InlineKeyboardMarkup(kb))
    
    await asyncio.sleep(30)
    if len(GAMES[g_id]["players"]) < 4:
        await context.bot.send_message(chat_id=g_id, text="❌ O'yinchilar soni yetarli bo'lmadi (kamida 4 ta kerak).")
        GAMES[g_id]["status"] = "ended"
        return
        
    await start_mafia_game(g_id, context)

async def start_mafia_game(g_id, context):
    p_ids = list(GAMES[g_id]["players"].keys())
    random.shuffle(p_ids)
    
    GAMES[g_id]["players"][p_ids[0]]["role"] = "Mafiya"
    GAMES[g_id]["players"][p_ids[1]]["role"] = "Shifokor"
    GAMES[g_id]["players"][p_ids[2]]["role"] = "Komissar"
    for i in range(3, len(p_ids)):
        GAMES[g_id]["players"][p_ids[i]]["role"] = "Tinch aholi"
        
    for p_id in p_ids:
        db_user = USER_DATA.get(p_id, {})
        wanted = db_user.get("selected_role", "Tasodifiy")
        if wanted != "Tasodifiy":
            current_role_owner = next((x for x in GAMES[g_id]["players"].values() if x["role"] == wanted), None)
            if current_role_owner:
                old_role = GAMES[g_id]["players"][p_id]["role"]
                current_role_owner["role"] = old_role
                GAMES[g_id]["players"][p_id]["role"] = wanted
            db_user["selected_role"] = "Tasodifiy"

    for p_id, p_data in GAMES[g_id]["players"].items():
        try:
            await context.bot.send_message(chat_id=p_id, text=f"🎭 O'yin boshlandi! Sizning rolingiz: **{p_data['role']}**", parse_mode="Markdown")
        except Exception:
            pass
            
    await context.bot.send_message(chat_id=g_id, text="🚀 Rollar tarqatildi! Bot shaxsiyda rolingizni yubordi. Tungi bosqich boshlanmoqda...")
    await run_night(g_id, context)

async def run_night(g_id, context):
    GAMES[g_id]["status"] = "night"
    GAMES[g_id]["mafia_vote"] = None
    GAMES[g_id]["doc_vote"] = None
    GAMES[g_id]["cop_vote"] = None
    
    await context.bot.send_message(chat_id=g_id, text="🌃 **Tun.** Shahar uyquga ketdi. O'yin faollari shaxsiy chatga o'ting...")
    
    for p_id, p_data in GAMES[g_id]["players"].items():
        if not p_data["alive"]:
            continue
            
        targets = [InlineKeyboardButton(p["name"], callback_data=f"{p_data['role'].lower()}_vote_{g_id}_{p['id']}") for p in GAMES[g_id]["players"].values() if p["alive"] and p["id"] != p_id]
        kb = [targets[i:i+2] for i in range(0, len(targets), 2)]
        
        if p_data["role"] == "Mafiya":
            try: await context.bot.send_message(chat_id=p_id, text="🔴 Kimni o'ldirmoqchisiz?", reply_markup=InlineKeyboardMarkup(kb))
            except Exception: pass
        elif p_data["role"] == "Shifokor":
            try: await context.bot.send_message(chat_id=p_id, text="🟢 Kimni davolamoqchisiz?", reply_markup=InlineKeyboardMarkup(kb))
            except Exception: pass
        elif p_data["role"] == "Komissar":
            try: await context.bot.send_message(chat_id=p_id, text="🔍 Kimni tekshirmoqchisiz?", reply_markup=InlineKeyboardMarkup(kb))
            except Exception: pass

    await asyncio.sleep(30)
    await run_day(g_id, context)

async def run_day(g_id, context):
    GAMES[g_id]["status"] = "day"
    GAMES[g_id]["day_votes"] = {}
    
    m_vote = GAMES[g_id]["mafia_vote"]
    d_vote = GAMES[g_id]["doc_vote"]
    
    killed_name = "Hech kim"
    if m_vote and m_vote != d_vote:
        user_db = USER_DATA.get(m_vote, {})
        if user_db.get("has_armor", False):
            user_db["has_armor"] = False
            killed_name = "Hech kim (Zirh himoya qildi)"
        else:
            GAMES[g_id]["players"][m_vote]["alive"] = False
            killed_name = GAMES[g_id]["players"][m_vote]["name"]
            
    await context.bot.send_message(chat_id=g_id, text=f"☀️ **Ertalab bo'ldi!**\n\nTunda o'ldirildi: **{killed_name}**", parse_mode="Markdown")
    
    if await check_game_end(g_id, context):
        return
        
    await context.bot.send_message(chat_id=g_id, text="🗳️ **Kunduzgi ovoz berish boshlandi!** Gumonlanuvchiga shaxsiyda ovoz bering.")
    
    for p_id, p_data in GAMES[g_id]["players"].items():
        if not p_data["alive"]:
            continue
        targets = [InlineKeyboardButton(p["name"], callback_data=f"day_vote_{g_id}_{p['id']}") for p in GAMES[g_id]["players"].values() if p["alive"]]
        kb = [targets[i:i+2] for i in range(0, len(targets), 2)]
        try: await context.bot.send_message(chat_id=p_id, text="🗳️ Kimga ovoz berasiz?", reply_markup=InlineKeyboardMarkup(kb))
        except Exception: pass

    await asyncio.sleep(30)
    await resolve_day_vote(g_id, context)

async def resolve_day_vote(g_id, context):
    votes = GAMES[g_id]["day_votes"]
    if not votes:
        await context.bot.send_message(chat_id=g_id, text="🤷‍♂️ Hech kim ovoz bermadi.")
    else:
        counts = {}
        for target in votes.values():
            counts[target] = counts.get(target, 0) + 1
        max_votes = max(counts.values())
        winners = [k for k, v in counts.items() if v == max_votes]
        
        if len(winners) > 1:
            await context.bot.send_message(chat_id=g_id, text="⚖️ Ovozlar teng. Hech kim qatl qilinmadi.")
        else:
            lynched = winners[0]
            GAMES[g_id]["players"][lynched]["alive"] = False
            await context.bot.send_message(chat_id=g_id, text=f"⚖️ Qatl qilindi: **{GAMES[g_id]['players'][lynched]['name']}**", parse_mode="Markdown")

    if await check_game_end(g_id, context):
        return
        
    GAMES[g_id]["cycle"] += 1
    await run_night(g_id, context)

async def check_game_end(g_id, context):
    mafia_alive = sum(1 for p in GAMES[g_id]["players"].values() if p["alive"] and p["role"] == "Mafiya")
    good_alive = sum(1 for p in GAMES[g_id]["players"].values() if p["alive"] and p["role"] != "Mafiya")
    
    if mafia_alive == 0:
        await context.bot.send_message(chat_id=g_id, text="🎉 **Tinch aholi g'alaba qozondi!**")
        for p in GAMES[g_id]["players"].values():
            if p["role"] != "Mafiya":
                get_or_create_user(p["id"], "", "")["wins"] += 1
                if p["id"] != ADMIN_ID: USER_DATA[p["id"]]["balance"] += 30
        GAMES[g_id]["status"] = "ended"
        return True
    elif mafia_alive >= good_alive:
        await context.bot.send_message(chat_id=g_id, text="🔴 **Mafiya g'alaba qozondi!**")
        for p in GAMES[g_id]["players"].values():
            if p["role"] == "Mafiya":
                get_or_create_user(p["id"], "", "")["wins"] += 1
                if p["id"] != ADMIN_ID: USER_DATA[p["id"]]["balance"] += 50
        GAMES[g_id]["status"] = "ended"
        return True
    return False

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g_id = update.effective_chat.id
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ O'yinni faqat asosiy admin to'xtata oladi!")
        return
    if g_id in GAMES and GAMES[g_id]["status"] != "ended":
        GAMES[g_id]["status"] = "ended"
        await update.message.reply_text("🛑 O'yin to'xtatildi!")

async def give_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        args = context.args
        t_id = int(args[0])
        amount = int(args[1])
        db_user = get_or_create_user(t_id, "", "Foydalanuvchi")
        db_user["balance"] += amount
        await update.message.reply_text(f"✅ ID {t_id} bo'lgan o'yinchiga {amount} ta olmos berildi!")
    except Exception:
        await update.message.reply_text("❌ Format: /give ID Olmos_Soni")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("game", game_command))
    application.add_handler(CommandHandler("give", give_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("promokod", promo_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY & filters.ChatType.PRIVATE, start))
    
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
