import os
import logging
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Loglarni sozlash
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 🔑 Siz bergan mutlaqo yangi va toza token!
TOKEN = "8798029139:AAHMun4oeWPbbH5uFPpadm2qqpx_k_OFj3c"

# 👑 Sizning Telegram ID raqamingiz (Admin)
ADMIN_ID = 7920504062
ADMIN_GROUP_ID = 7920504062 

USER_DATA = {}
GAMES = {} 

def get_or_create_user(user_id, username, first_name):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "name": first_name,
            "username": username or "Mavjud emas",
            "balance": 100,  # Yangi o'yinchilarga 100 olmos bonus
            "selected_role": "Tasodifiy",
            "has_armor": False,
            "wins": 0,
            "games_played": 0
        }
    # Admin balansi har doim cheksiz bo'ladi!
    if user_id == ADMIN_ID:
        USER_DATA[user_id]["balance"] = float('inf')
    return USER_DATA[user_id]

# Bosh menyu (Shaxsiyda)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_or_create_user(user.id, user.username, user.first_name)
    
    if update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("🎲 Guruhda o'yin boshlash uchun `/game` buyrug'ini yuboring!")
        return

    bal_str = "Cheksiz 💎" if user.id == ADMIN_ID else f"{db_user['balance']:,} 💎"
    
    text = (
        f"🕵️‍♂️ **True Mafia Botiga Xush Kelibsiz!**\n\n"
        f"👤 Ismingiz: {user.first_name}\n"
        f"💎 Balansingiz: *{bal_str}*\n"
        f"🎭 Keyingi o'yin roli: *{db_user['selected_role']}*\n"
        f"🛡 Zirh (Bronijilet): *{'Mavjud ✅' if db_user['has_armor'] else 'Yoʻq ❌'}*"
    )
    
    keyboard = [
        [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("🛒 Shop (Do'kon)", callback_data="open_shop"), InlineKeyboardButton("🏆 Reyting", callback_data="view_top")],
        [InlineKeyboardButton("🙋‍♂️ Olmos so'rash", callback_data="ask_diamonds")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# 💎 Reply orqali /give buyrug'i
async def give_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    giver = get_or_create_user(user_id, update.effective_user.username, update.effective_user.first_name)
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ushbu buyruqni ishlatish uchun biron bir foydalanuvchining xabariga javob (reply) bering!")
        return
        
    target_user = update.message.reply_to_message.from_user
    if target_user.is_bot:
        await update.message.reply_text("❌ Botlarga olmos berib bo'lmaydi!")
        return
        
    try:
        amount = int(context.args[0])
        if amount <= 0: raise ValueError
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Ishlatish formati: `/give 500` (xabarga reply qilib)")
        return
        
    if user_id != ADMIN_ID and giver["balance"] < amount:
        await update.message.reply_text("❌ Hisobingizda yetarli olmos yo'q!")
        return
        
    if user_id != ADMIN_ID:
        giver["balance"] -= amount
        
    receiver = get_or_create_user(target_user.id, target_user.username, target_user.first_name)
    receiver["balance"] += amount
    
    await update.message.reply_text(
        f"✅ **Muvaffaqiyatli o'tkazildi!**\n"
        f"👤 {update.effective_user.first_name} o'z hisobidan **{target_user.first_name}**ga *{amount}* olmos berdi! 💎"
    )

# Guruhda o'yin yaratish
async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ O'yinni faqat guruhda boshlash mumkin!")
        return
        
    if chat_id in GAMES and GAMES[chat_id]["status"] != "ended":
        await update.message.reply_text("❌ Guruhda allaqachon faol o'yin ketmoqda!")
        return
        
    GAMES[chat_id] = {
        "creator": user.id,
        "players": {user.id: {"name": user.first_name, "role": None, "alive": True}},
        "status": "join_period",
        "mafia_vote": {}, "doc_vote": None, "cop_vote": None, "day_votes": {}
    }
    
    text = (
        f"🎮 **Yangi TrueMafia o'yini boshlandi!**\n\n"
        f"👑 Yaratuvchi: {user.first_name}\n"
        f"👥 O'yinchilar jami: 1 ta\n\n"
        f"O'yinga qo'shilish uchun pastdagi tugmani bosing:"
    )
    keyboard = [
        [InlineKeyboardButton("✅ O'yinga qo'shilish", callback_data="join_game")],
        [InlineKeyboardButton("🚀 O'yinni start berish", callback_data="start_game")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Tun bosqichi
async def start_night(chat_id, context):
    game = GAMES[chat_id]
    game["status"] = "night"
    game["mafia_vote"], game["doc_vote"], game["cop_vote"] = {}, None, None
    
    await context.bot.send_message(chat_id=chat_id, text="🌃 **Tun kirdi... (45 soniya)**\nMafiya, Shifokor va Komissar o'z shaxsiylarida harakat qilmoqdalar!")
    
    for p_id, p_info in game["players"].items():
        if not p_info["alive"]: continue
        targets_kb = [[InlineKeyboardButton(t_info["name"], callback_data=f"night_act_{chat_id}_{t_id}")] 
                      for t_id, t_info in game["players"].items() if t_info["alive"]]
                      
        if p_info["role"] == "Mafiya":
            try: await context.bot.send_message(chat_id=p_id, text="🎯 **Kimni otasiz?**", reply_markup=InlineKeyboardMarkup(targets_kb))
            except Exception: pass
        elif p_info["role"] == "Shifokor":
            try: await context.bot.send_message(chat_id=p_id, text="🟢 **Kimni davolaysiz?**", reply_markup=InlineKeyboardMarkup(targets_kb))
            except Exception: pass
        elif p_info["role"] == "Komissar":
            try: await context.bot.send_message(chat_id=p_id, text="🔍 **Kimni tekshirasiz?**", reply_markup=InlineKeyboardMarkup(targets_kb))
            except Exception: pass

    await asyncio.sleep(45)
    await start_day(chat_id, context)

# Kun bosqichi
async def start_day(chat_id, context):
    game = GAMES[chat_id]
    if game["status"] == "ended": return
    game["status"] = "day"
    game["day_votes"] = {}
    
    killed_id = max(set(game["mafia_vote"].values()), key=list(game["mafia_vote"].values()).count) if game["mafia_vote"] else None
    
    if killed_id:
        p_user = USER_DATA.get(killed_id, {})
        # Zirh (Bronijilet) tekshiruvi
        if p_user.get("has_armor", False):
            p_user["has_armor"] = False  
            result_text = f"🌅 **Tong otdi!**\n\n🌃 Bu kecha mafiya kimdirga o'q uzdi, biroq o'yinchi egnidagi **🛡 Bronijilet (Zirh)** tufayli o'limdan omon qoldi! Hech kim o'lmadi."
        elif killed_id == game["doc_vote"]:
            result_text = "🌅 **Tong otdi!**\n\n🌃 Mafiya tunda suiqasd uyushtirdi, lekin **Shifokor** o'z vaqtida kelib yaradorni qutqardi! Hech kim o'lmadi."
        else:
            game["players"][killed_id]["alive"] = False
            result_text = f"🌅 **Tong otdi!**\n\n💀 Mudhish xabar: Bu kecha **{game['players'][killed_id]['name']}** otib ketildi! Roli: *{game['players'][killed_id]['role']}*"
    else:
        result_text = "🌅 **Tong otdi!**\n\n🌃 Bu kecha juda tinch o'tdi, talofatlar yo'q."
        
    await context.bot.send_message(chat_id=chat_id, text=result_text, parse_mode="Markdown")
    if await check_game_over(chat_id, context): return
    
    vote_kb = [[InlineKeyboardButton(t_info["name"], callback_data=f"day_vote_{chat_id}_{t_id}")] 
               for t_id, t_info in game["players"].items() if t_info["alive"]]
    await context.bot.send_message(chat_id=chat_id, text="🗣 **Muhokama va Ovoz berish boshlandi! (45 soniya)**\nGumonlanuvchiga ovoz bering:", reply_markup=InlineKeyboardMarkup(vote_kb))
    
    await asyncio.sleep(45)
    await end_day_voting(chat_id, context)

async def end_day_voting(chat_id, context):
    game = GAMES[chat_id]
    if game["status"] == "ended": return
    
    if not game["day_votes"]:
        await context.bot.send_message(chat_id=chat_id, text="💤 Bugun ovozlar yig'ilmadi. Hech kim jazolanmadi.")
        await start_night(chat_id, context)
        return
        
    lynched_id = max(set(game["day_votes"].values()), key=list(game["day_votes"].values()).count)
    game["players"][lynched_id]["alive"] = False
    await context.bot.send_message(chat_id=chat_id, text=f"⚖️ Guruh qaroriga ko'ra **{game['players'][lynched_id]['name']}** osildi. Roli: *{game['players'][lynched_id]['role']}*")
    
    if await check_game_over(chat_id, context): return
    await start_night(chat_id, context)

async def check_game_over(chat_id, context):
    game = GAMES[chat_id]
    mafia = sum(1 for p in game["players"].values() if p["alive"] and p["role"] == "Mafiya")
    citizens = sum(1 for p in game["players"].values() if p["alive"] and p["role"] != "Mafiya")
    
    if mafia == 0:
        await context.bot.send_message(chat_id=chat_id, text="🎉 **Tinch aholi g'alaba qozondi!** Barcha mafiyalar qirildi.")
        for p_id in game["players"]: USER_DATA[p_id]["wins"] += 1
        game["status"] = "ended"
        return True
    elif mafia >= citizens:
        await context.bot.send_message(chat_id=chat_id, text="🔴 **Mafiya g'alaba qozondi!** Shahar mafiya qo'liga o'tdi.")
        game["status"] = "ended"
        return True
    return False

# Adminga Reply orqali Olmos berish tasdig'i
async def admin_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not update.message.reply_to_message: return
    
    rep_text = update.message.reply_to_message.text
    if "💎 Olmos so'rovi!" in rep_text:
        try:
            amount = int(update.message.text.strip())
            target_id = int(rep_text.split("ID: `")[1].split("`")[0])
            
            user = get_or_create_user(target_id, "", "Foydalanuvchi")
            user["balance"] += amount
            
            await update.message.reply_text(f"✅ Foydalanuvchiga *{amount}* olmos muvaffaqiyatli o'tkazildi!", parse_mode="Markdown")
            try:
                await context.bot.send_message(chat_id=target_id, text=f"🎁 **Admin so'rovingizni tasdiqladi!** Hisobingizga *{amount}* olmos qo'shildi!")
            except Exception: pass
        except Exception:
            await update.message.reply_text("❌ Iltimos, faqat kerakli son miqdorini to'g'ri yozing!")

# Callback Tugmalar
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u_id, chat_id = query.from_user.id, query.message.chat_id
    db_user = get_or_create_user(u_id, query.from_user.username, query.from_user.first_name)
    
    if query.data == "join_game" and chat_id in GAMES and GAMES[chat_id]["status"] == "join_period":
        if u_id not in GAMES[chat_id]["players"]:
            GAMES[chat_id]["players"][u_id] = {"name": query.from_user.first_name, "role": None, "alive": True}
            USER_DATA[u_id]["games_played"] += 1
            await query.message.edit_text(f"🎮 **TrueMafia O'yini!**\n\n👥 O'yinchilar jami: {len(GAMES[chat_id]['players'])} ta\n🏃 Oxirgi qo'shilgan: {query.from_user.first_name}", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ O'yinga qo'shilish", callback_data="join_game")],[InlineKeyboardButton("🚀 O'yinni start berish", callback_data="start_game")]]))

    elif query.data == "start_game" and chat_id in GAMES and GAMES[chat_id]["status"] == "join_period":
        p_ids = list(GAMES[chat_id]["players"].keys())
        if len(p_ids) < 3:
            await context.bot.send_message(chat_id=chat_id, text="❌ O'yinni boshlash uchun kamida 3 ta odam kerak!")
            return
            
        random.shuffle(p_ids)
        roles = ["Mafiya", "Komissar", "Shifokor"] + ["Fuqaro"] * (len(p_ids) - 3)
        
        for i, p_id in enumerate(p_ids):
            p_db = USER_DATA.get(p_id, {})
            if p_db.get("selected_role") in ["Mafiya", "Komissar", "Shifokor"] and p_db["selected_role"] in roles:
                final_role = p_db["selected_role"]
                roles.remove(final_role)
                p_db["selected_role"] = "Tasodifiy" 
            else:
                final_role = roles.pop(0)
            GAMES[chat_id]["players"][p_id]["role"] = final_role
            try: await context.bot.send_message(chat_id=p_id, text=f"🕵️‍♂️ **True Mafia**\n\nSizning rolingiz: **{final_role}**")
            except Exception: pass
            
        await query.message.edit_text("🏁 O'yin boshlandi! Rollar tarqatildi.")
        await start_night(chat_id, context)

    elif query.data == "open_shop":
        text = (
            f"🛒 **TrueMafia do'koni**\n\n"
            f"🔴 Mafiya roli — 30 💎\n🔵 Komissar roli — 25 💎\n🟢 Shifokor roli — 20 💎\n"
            f"🦺 Bronijilet (Zirh) — 50 💎 (Tunda o'limdan saqlaydi)\n\n"
            f"Balansingiz: {db_user['balance']} 💎"
        )
        kb = [
            [InlineKeyboardButton("🔴 Mafiya (30 💎)", callback_data="buy_Mafiya"), InlineKeyboardButton("🔵 Komissar (25 💎)", callback_data="buy_Komissar")],
            [InlineKeyboardButton("🟢 Shifokor (20 💎)", callback_data="buy_Shifokor"), InlineKeyboardButton("🦺 Zirh (50 💎)", callback_data="buy_armor")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back_main")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif query.data.startswith("buy_"):
        item = query.data.split("_")[1]
        prices = {"Mafiya": 30, "Komissar": 25, "Shifokor": 20, "armor": 50}
        price = prices[item]
        
        if u_id != ADMIN_ID and db_user["balance"] < price:
            await context.bot.send_message(chat_id=u_id, text="❌ Mablag'ingiz yetarli emas!")
            return
            
        if u_id != ADMIN_ID: db_user["balance"] -= price
        
        if item == "armor":
            db_user["has_armor"] = True
            await query.edit_message_text("✅ Siz muvaffaqiyatli zirh (bronijilet) sotib oldingiz!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Do'kon", callback_data="open_shop")]]))
        else:
            db_user["selected_role"] = item
            await query.edit_message_text(f"✅ Sotib olindi! Keyingi o'yinda rolingiz: **{item}**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Do'kon", callback_data="open_shop")]]))

    elif query.data == "ask_diamonds":
        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=f"💎 **Olmos so'rovi!**\n\nFoydalanuvchi: {query.from_user.first_name}\nID: `{u_id}`\n\nUnga olmos berish uchun ushbu xabarga **Reply (Javob)** qilib faqat sonni o'zini yozing!"
        )
        await context.bot.send_message(chat_id=u_id, text="✅ So'rovingiz adminga yuborildi!")

    elif query.data == "view_top":
        sorted_users = sorted(USER_DATA.items(), key=lambda x: x[1]['wins'], reverse=True)[:5]
        top_text = "🏆 **Top 5 O'yinchilar (Reyting):**\n\n"
        for idx, (usr_id, usr_info) in enumerate(sorted_users, 1):
            top_text += f"{idx}. {usr_info['name']} — {usr_info['wins']} ta yutuq 🏆\n"
        await query.edit_message_text(top_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_main")]]), parse_mode="Markdown")

    elif query.data == "back_main":
        bal = "Cheksiz 💎" if u_id == ADMIN_ID else f"{db_user['balance']:,} 💎"
        kb = [
            [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🛒 Shop (Do'kon)", callback_data="open_shop"), InlineKeyboardButton("🏆 Reyting", callback_data="view_top")],
            [InlineKeyboardButton("🙋‍♂️ Olmos so'rash", callback_data="ask_diamonds")]
        ]
        await query.edit_message_text(f"🕵️‍♂️ **True Mafia Bot!**\n\n💎 Balansingiz: *{bal}*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif query.data.startswith("night_act_"):
        parts = query.data.split("_")
        g_id, target_id = int(parts[2]), int(parts[3])
        if g_id not in GAMES or GAMES[g_id]["status"] != "night": return
        my_role = GAMES[g_id]["players"][u_id]["role"]
        
        if my_role == "Mafiya":
            GAMES[g_id]["mafia_vote"][u_id] = target_id
            await query.edit_message_text(f"🎯 Siz {GAMES[g_id]['players'][target_id]['name']}ni nishonga oldingiz.")
        elif my_role == "Shifokor":
            GAMES[g_id]["doc_vote"] = target_id
            await query.edit_message_text(f"🟢 Siz {GAMES[g_id]['players'][target_id]['name']}ni davolashni tanladingiz.")
        elif my_role == "Komissar":
            is_mafia = "Mafiya 🔴" if GAMES[g_id]["players"][target_id]["role"] == "Mafiya" else "Tinch aholi 🟢"
            await query.edit_message_text(f"🔍 Natija: {GAMES[g_id]['players'][target_id]['name']} — **{is_mafia}**")

    elif query.data.startswith("day_vote_"):
        parts = query.data.split("_")
        g_id, target_id = int(parts[2]), int(parts[3])
        if g_id not in GAMES or GAMES[g_id]["status"] != "day": return
        if not GAMES[g_id]["players"].get(u_id, {}).get("alive", False): return
        
        GAMES[g_id]["day_votes"][u_id] = target_id
        await context.bot.send_message(chat_id=g_id, text=f"🗳 **{GAMES[g_id]['players'][u_id]['name']}** -> **{GAMES[g_id]['players'][target_id]['name']}**ga ovoz berdi!")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("game", game_command))
    application.add_handler(CommandHandler("give", give_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY & filters.ChatType.PRIVATE, admin_reply_handler))
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY & filters.Chat(ADMIN_GROUP_ID), admin_reply_handler))
    
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
