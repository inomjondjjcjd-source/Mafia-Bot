import os
import logging
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Log tizimi
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 🔑 Bot Tokeni
TOKEN = "8798029139:AAHMun4oeWPbbH5uFPpadm2qqpx_k_OFj3c"

# 👑 Admin sozlamalari
ADMIN_ID = 7920504062
ADMIN_GROUP_ID = 7920504062 

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
        await update.message.reply_text("🎲 Guruhda o'yin boshlash uchun `/game` buyrug'ini yuboring!")
        return

    bal_str = "Cheksiz 💎" if user.id == ADMIN_ID else f"{db_user['balance']:,} 💎"
    
    text = (
        f"🕵️‍♂️ **True Mafia Botiga Xush Kelibsiz!**\n\n"
        f"👤 Ismingiz: {user.first_name}\n"
        f"💎 Balansingiz: *{bal_str}*\n"
        f"🎭 Keyingi o'yin roli: *{db_user['selected_role']}*\n"
        f"🛡 Zirh (Bronijilet): *{'Mavjud ✅' if db_user['has_armor'] else 'Yoʻq ❌'}*\n\n"
        f"🎁 Maxfiy promo-kodni faollashtirish uchun: `/promokod KOD` deb yozing."
    )
    
    keyboard = [
        [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("🛒 Shop (Do'kon)", callback_data="open_shop"), InlineKeyboardButton("🏆 Reyting", callback_data="view_top")],
        [InlineKeyboardButton("🙋‍♂️ Olmos so'rash", callback_data="ask_diamonds")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = get_or_create_user(user_id, update.effective_user.username, update.effective_user.first_name)
    
    if not context.args:
        await update.message.reply_text("❌ Ishlatish formati: `/promokod 255500`")
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
        db_user["balance"] += 150
        
    await update.message.reply_text("🎉 **Tabriklaymiz!** Maxfiy kod muvaffaqiyatli faollashdi. Hisobingizga **150 ta olmos** qo'shildi! 💎")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ushbu buyruqni faqat bot admini ishlata oladi!")
        return
        
    if chat_id not in GAMES or GAMES[chat_id]["status"] == "ended":
        await update.message.reply_text("❌ Bu guruhda hozir hech qanday faol o'yin yo'q.")
        return
        
    GAMES[chat_id]["status"] = "ended"
    await update.message.reply_text("🛑 **O'yin bot admini tomonidan majburiy ravishda to'xtatildi!**")

async def give_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    giver = get_or_create_user(user_id, update.effective_user.username, update.effective_user.first_name)
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ushbu buyruqni ishlatish uchun xabarga reply qiling!")
        return
        
    target_user = update.message.reply_to_message.from_user
    try:
        amount = int(context.args[0])
        if amount <= 0: raise ValueError
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Ishlatish formati: `/give 500` (reply qilib)")
        return
        
    if user_id != ADMIN_ID and giver["balance"] < amount:
        await update.message.reply_text("❌ Hisobingizda yetarli olmos yo'q!")
        return
        
    if user_id != ADMIN_ID: giver["balance"] -= amount
    receiver = get_or_create_user(target_user.id, target_user.username, target_user.first_name)
    receiver["balance"] += amount
    
    await update.message.reply_text(f"✅ **Muvaffaqiyatli o'tkazildi!**\n👤 {update.effective_user.first_name} -> **{target_user.first_name}**ga *{amount}* olmos berdi! 💎")

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
    
    text = f"🎮 **Yangi TrueMafia o'yini boshlandi!**\n\n👑 Yaratuvchi: {user.first_name}\n👥 O'yinchilar: 1 ta"
    keyboard = [
        [InlineKeyboardButton("✅ O'yinga qo'shilish", callback_data="join_game")],
        [InlineKeyboardButton("🚀 O'yinni start berish", callback_data="start_game")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def start_night(chat_id, context):
    game = GAMES.get(chat_id)
    if not game or game["status"] == "ended": return
    game["status"] = "night"
    game["mafia_vote"], game["doc_vote"], game["cop_vote"] = {}, None, None
    
    await context.bot.send_message(chat_id=chat_id, text="🌃 **Tun kirdi... (45 soniya)**\nAktiv rollar shaxsiylarida harakat qilmoqda!")
    
    for p_id, p_info in game["players"].items():
        if not p_info["alive"]: continue
        targets_kb = [[InlineKeyboardButton(t_info["name"], callback_data=f"night_act_{chat_id}_{t_id}")] for t_id, t_info in game["players"].items() if t_info["alive"]]
                      
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
    
    if game["status"] == "ended": return
    afk_players = []
    for p_id, p_info in game["players"].items():
        if not p_info["alive"]: continue
        if p_info["role"] == "Mafiya" and p_id not in game["mafia_vote"]: afk_players.append(p_id)
        elif p_info["role"] == "Shifokor" and game["doc_vote"] is None: afk_players.append(p_id)
        elif p_info["role"] == "Komissar" and game["cop_vote"] is None: afk_players.append(p_id)
            
    for afk_id in afk_players:
        game["players"][afk_id]["alive"] = False
        try: await context.bot.send_message(chat_id=chat_id, text=f"💤 **{game['players'][afk_id]['name']}** tunda harakat qilmagani (AFK) sababli o'ldi! Roli: *{game['players'][afk_id]['role']}*")
        except Exception: pass
        
    await start_day(chat_id, context)

async def start_day(chat_id, context):
    game = GAMES.get(chat_id)
    if not game or game["status"] == "ended": return
    if await check_game_over(chat_id, context): return
    
    game["status"] = "day"
    game["day_votes"] = {}
    
    killed_id = max(set(game["mafia_vote"].values()), key=list(game["mafia_vote"].values()).count) if game["mafia_vote"] else None
    
    if killed_id and game["players"].get(killed_id, {}).get("alive", True):
        p_user = USER_DATA.get(killed_id, {})
        if p_user.get("has_armor", False):
            p_user["has_armor"] = False  
            result_text = f"🌅 **Tong otdi!**\n\n🌃 Mafiya kimdirga o'q uzdi, biroq o'yinchi egnidagi **🛡 Bronijilet (Zirh)** tufayli omon qoldi!"
        elif killed_id == game["doc_vote"]:
            result_text = "🌅 **Tong otdi!**\n\n🌃 Mafiya suiqasd uyushtirdi, lekin **Shifokor** uni qutqardi!"
        else:
            game["players"][killed_id]["alive"] = False
            result_text = f"🌅 **Tong otdi!**\n\n💀 Mudhish xabar: **{game['players'][killed_id]['name']}** otib ketildi! Roli: *{game['players'][killed_id]['role']}*"
    else:
        result_text = "🌅 **Tong otdi!**\n\n🌃 Bu kecha talofatlar yo'q, shahar tinch."
        
    await context.bot.send_message(chat_id=chat_id, text=result_text, parse_mode="Markdown")
    if await check_game_over(chat_id, context): return
    
    vote_kb = [[InlineKeyboardButton(t_info["name"], callback_data=f"day_vote_{chat_id}_{t_id}")] for t_id, t_info in game["players"].items() if t_info["alive"]]
    await context.bot.send_message(chat_id=chat_id, text=f"🗣 **Ovoz berish boshlandi! (45 soniya)**\nOvoz bermaganlar AFK bo'lib o'ladi!", reply_markup=InlineKeyboardMarkup(vote_kb))
    
    await asyncio.sleep(45)
    await end_day_voting(chat_id, context)

async def end_day_voting(chat_id, context):
    game = GAMES.get(chat_id)
    if not game or game["status"] == "ended": return
    
    afk_voters = []
    for p_id, p_info in game["players"].items():
        if p_info["alive"] and p_id not in game["day_votes"]: afk_voters.append(p_id)
            
    for afk_id in afk_voters:
        game["players"][afk_id]["alive"] = False
        try: await context.bot.send_message(chat_id=chat_id, text=f"💤 **{game['players'][afk_id]['name']}** ovoz bermagani (AFK) sababli o'ldi! Roli: *{game['players'][afk_id]['role']}*")
        except Exception: pass
        
    if await check_game_over(chat_id, context): return

    if not game["day_votes"]:
        await context.bot.send_message(chat_id=chat_id, text="💤 Hech kim ovoz bermadi.")
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
        await context.bot.send_message(chat_id=chat_id, text="🎉 **Tinch aholi g'alaba qozondi!**")
        for p_id in game["players"]: USER_DATA[p_id]["wins"] += 1
        game["status"] = "ended"
        return True
    elif mafia >= citizens:
        await context.bot.send_message(chat_id=chat_id, text="🔴 **Mafiya g'alaba qozondi!**")
        game["status"] = "ended"
        return True
    return False

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
            await update.message.reply_text("✅ Olmos o'tkazildi!")
            try: await context.bot.send_message(chat_id=target_id, text=f"🎁 Hisobingizga *{amount}* olmos qo'shildi!")
            except Exception: pass
        except Exception: pass

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u_id, chat_id = query.from_user.id, query.message.chat_id
    db_user = get_or_create_user(u_id, query.from_user.username, query.from_user.first_name)
    
    if query.data == "join_game" and chat_id in GAMES and GAMES[chat_id]["status"] == "join_period":
        if u_id not in GAMES[chat_id]["players"]:
            GAMES[chat_id]["players"][u_id] = {"name": query.from_user.first_name, "role": None, "alive": True}
            USER_DATA[u_id]["games_played"] += 1
            await query.message.edit_text(f"🎮 **TrueMafia O'yini!**\n\n👥 O'yinchilar: {len(GAMES[chat_id]['players'])} ta", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ O'yinga qo'shilish", callback_data="join_game")],[InlineKeyboardButton("🚀 O'yinni start berish", callback_data="start_game")]]))

    elif query.data == "start_game" and chat_id in GAMES and GAMES[chat_id]["status"] == "join_period":
        p_ids = list(GAMES[chat_id]["players"].keys())
        if len(p_ids) < 3:
            await context.bot.send_message(chat_id=chat_id, text="❌ Kamida 3 ta odam kerak!")
            return
            
        random.shuffle(p_ids)
        roles = ["Mafiya", "Komissar", "Shifokor"] + ["Fuqaro"] * (len(p_ids) - 3)
        
        for p_id in p_ids:
            p_db = USER_DATA.get(p_id, {})
            if p_db.get("selected_role") in ["Mafiya", "Komissar", "Shifokor"] and p_db["selected_role"] in roles:
                final_role = p_db["selected_role"]
                roles.remove(final_role)
                p_db["selected_role"] = "Tasodifiy" 
            else:
                final_role = roles.pop(0)
            GAMES[chat_id]["players"][p_id]["role"] = final_role
            try: await context.bot.send_message(chat_id=p_id, text=f"🕵️‍♂️ Ro'lingiz: **{final_role}**")
            except Exception: pass
            
        await query.message.edit_text("🏁 O'yin boshlandi!")
        await start_night(chat_id, context)

    elif query.data == "open_shop":
        text = f"🛒 **Do'kon**\n\n🔴 Mafiya — 30 💎\n🔵 Komissar — 25 💎\n🟢 Shifokor — 20 💎\n🦺 Zirh — 50 💎\n\nBalansingiz: {db_user['balance']} 💎"
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
        if u_id != ADMIN_ID and db_user["balance"] < price: return
        if u_id != ADMIN_ID: db_user["balance"] -= price
        if item == "armor":
            db_user["has_armor"] = True
        else:
            db_user["selected_role"] = item
        await query.edit_message_text(f"✅ Xarid qilindi!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Do'kon", callback_data="open_shop")]]))

    elif query.data == "ask_diamonds":
        await context.bot.send_message(ADMIN_GROUP_ID, text=f"💎 **Olmos so'rovi!**\nID: `{u_id}`")
        await query.message.reply_text("✅ So'rov adminga ketdi!")

    elif query.data == "view_top":
        sorted_users = sorted(USER_DATA.items(), key=lambda x: x[1]['wins'], reverse=True)[:5]
        top_text = "🏆 **Top O'yinchilar:**\n\n"
        for idx, (usr_id, usr_info) in enumerate(sorted_users, 1):
            top_text += f"{idx}. {usr_info['name']} — {usr_info['wins']} ta yutuq\n"
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
            await query.edit_message_text(f"🎯 Tanlandi: {GAMES[g_id]['players'][target_id]['name']}")
        elif my_role == "Shifokor":
            GAMES[g_id]["doc_vote"] = target_id
            await query.edit_message_text(f"🟢 Tanlandi: {GAMES[g_id]['players'][target_id]['name']}")
        elif my_role == "Komissar":
            GAMES[g_id]["cop_vote"] = target_id
            is_mafia = "Mafiya 🔴" if GAMES[g_id]["players"][target_id]["role"] == "Mafiya" else "Tinch aholi 🟢"
            await query.edit_message_text(f"🔍 Natija: — **{is_mafia}**")

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
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("promokod", promo_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY & filters.ChatType.PRIVATE, admin_reply_handler))
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY & filters.Chat(ADMIN_GROUP_ID), admin_reply_handler))
    
    application.run_polli
