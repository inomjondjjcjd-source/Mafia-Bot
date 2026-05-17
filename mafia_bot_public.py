import os
import logging
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Loglarni sozlash
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.environ.get("API_TOKEN", "8798029139:AAFqEcEt-q6BhXr3an0jZMjZjYsBY_C7Z0w")
ADMIN_ID = 7920504062

USER_DATA = {}
GAMES = {} 
USER_STATES = {} 

def get_or_create_user(user_id, username, first_name):
    if user_id not in USER_DATA:
        balance = 9999999999 if user_id == ADMIN_ID else 1000 # Test uchun boshida 1000 olmos
        USER_DATA[user_id] = {
            "name": first_name,
            "username": username or "Mavjud emas",
            "balance": balance,
            "selected_role": "Tasodifiy"
        }
    return USER_DATA[user_id]

# Bosh menyu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_or_create_user(user.id, user.username, user.first_name)
    
    if update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("🎲 Guruhda o'yin boshlash uchun `/game` buyrug'ini yuboring!")
        return

    text = f"Salom! Men 🕵️‍♂️ **True Mafia** botiman.\n\n💎 Sizning balansingiz: *{db_user['balance']:,} olmos*"
    keyboard = [
        [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("🛒 Rol sotib olish", callback_data="buy_role"), InlineKeyboardButton("👤 Profil", callback_data="view_profile")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# 💎 /give buyrug'i (O'z hisobidan olmos berish)
async def give_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = get_or_create_user(user_id, update.effective_user.username, update.effective_user.first_name)
    
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        
        if amount <= 0:
            await update.message.reply_text("❌ Miqdor noto'g'ri!")
            return
            
        if db_user["balance"] < amount:
            await update.message.reply_text("❌ Hisobingizda yetarli olmos yo'q!")
            return
            
        db_user["balance"] -= amount
        get_or_create_user(target_id, "", "Foydalanuvchi")
        USER_DATA[target_id]["balance"] += amount
        
        await update.message.reply_text(f"✅ Siz o'z hisobingizdan `{target_id}` ga *{amount}* olmos o'tkazdingiz!\n💎 Qolgan balansingiz: {db_user['balance']:,}")
        try:
            await context.bot.send_message(chat_id=target_id, text=f"💎 Sizga birov o'z hisobidan *{amount}* olmos o'tkazdi!")
        except Exception:
            pass
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Ishlatish formati: `/give ID miqdor` (Masalan: `/give 7920504062 500`)")

# Guruhda o'yin yaratish
async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Guruhda yozing!")
        return
        
    if chat_id in GAMES and GAMES[chat_id]["status"] != "ended":
        await update.message.reply_text("❌ Guruhda allaqachon faol o'yin ketmoqda!")
        return
        
    GAMES[chat_id] = {
        "creator": user.id,
        "players": {user.id: {"name": user.first_name, "role": None, "alive": True}},
        "status": "join_period",
        "mafia_vote": {},
        "doc_vote": None,
        "cop_vote": None,
        "day_votes": {}
    }
    
    text = f"🎮 **Yangi TrueMafia o'yini boshlandi!**\n\n👑 Yaratuvchi: {user.first_name}\n👥 O'yinchilar: 1 ta\n\nQo'shilish uchun pastdagi tugmani bosing:"
    keyboard = [
        [InlineKeyboardButton("✅ O'yinga qo'shilish", callback_data="join_game")],
        [InlineKeyboardButton("🚀 O'yinni start berish", callback_data="start_game")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Tun tsikli boshlanishi
async def start_night(chat_id, context):
    game = GAMES[chat_id]
    game["status"] = "night"
    game["mafia_vote"] = {}
    game["doc_vote"] = None
    game["cop_vote"] = None
    
    await context.bot.send_message(chat_id=chat_id, text="🌃 **Tun kirdi... (60 soniya)**\nShahar sukunatga cho'mmoqda. Mafiya, Shifokor va Komissar shaxsiy xabarda o'z amallarini bajarishmoqda!")
    
    # Shaxsiylarga tugma yuborish
    for p_id, p_info in game["players"].items():
        if not p_info["alive"]: continue
        
        # Tirik o'yinchilar ro'yxati tugmasi
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

    await asyncio.sleep(40) # Tungi harakatlar uchun vaqt
    await start_day(chat_id, context)

# Kun tsikli boshlanishi
async def start_day(chat_id, context):
    game = GAMES[chat_id]
    if game["status"] == "ended": return
    game["status"] = "day"
    game["day_votes"] = {}
    
    # Kechasidagi natijalarni hisoblash
    killed_id = None
    if game["mafia_vote"]:
        # Eng ko'p ovoz olgan nishon
        killed_id = max(set(game["mafia_vote"].values()), key=list(game["mafia_vote"].values()).count)
        
    if killed_id and killed_id == game["doc_vote"]:
        result_text = "🌅 **Tong otdi!**\n\n🌃 Bu kecha mafiya otishmaga urindi, biroq **Shifokor** o'z vaqtida kelib yaradorni qutqarib qoldi! Hech kim o'lmadi."
    elif killed_id:
        game["players"][killed_id]["alive"] = False
        name = game["players"][killed_id]["name"]
        role = game["players"][killed_id]["role"]
        result_text = f"🌅 **Tong otdi!**\n\n💀 Mudhish xabar: Bu kecha mafiya tatbiqida **{name}** shafqatsizlarcha otib ketildi! Uning roli: *{role}* edi."
    else:
        result_text = "🌅 **Tong otdi!**\n\n🌃 Bu kecha juda tinch o'tdi, hech kim zarar ko'rmadi."
        
    await context.bot.send_message(chat_id=chat_id, text=result_text, parse_mode="Markdown")
    
    # O'yin tugaganini tekshirish
    if await check_game_over(chat_id, context): return
    
    # Kunlik ovoz berishni boshlash
    await context.bot.send_message(chat_id=chat_id, text="🗣 **Muhokama va Ovoz berish boshlandi! (60 soniya)**\n\nKimdan shubhalanayotgan bo'lsangiz, pastdagi tugmalardan tanlab unga ovoz bering:")
    
    vote_kb = [[InlineKeyboardButton(t_info["name"], callback_data=f"day_vote_{chat_id}_{t_id}")] 
               for t_id, t_info in game["players"].items() if t_info["alive"]]
    await context.bot.send_message(chat_id=chat_id, text="🗳 **Gumonlanuvchiga ovoz bering:**", reply_markup=InlineKeyboardMarkup(vote_kb))
    
    await asyncio.sleep(40)
    await end_day_voting(chat_id, context)

# Kunlik ovoz berish yakuni va osish
async def end_day_voting(chat_id, context):
    game = GAMES[chat_id]
    if game["status"] == "ended": return
    
    if not game["day_votes"]:
        await context.bot.send_message(chat_id=chat_id, text="💤 Bugun guruhda hech kim ovoz bermadi, hech kim jazolanmadi.")
        await start_night(chat_id, context)
        return
        
    lynched_id = max(set(game["day_votes"].values()), key=list(game["day_votes"].values()).count)
    game["players"][lynched_id]["alive"] = False
    name = game["players"][lynched_id]["name"]
    role = game["players"][lynched_id]["role"]
    
    await context.bot.send_message(chat_id=chat_id, text=f"⚖️ Guruh qaroriga ko'ra, eng ko'p shubha ostida qolgan **{name}** osildi. Uning roli: *{role}* edi.")
    
    if await check_game_over(chat_id, context): return
    await start_night(chat_id, context)

# O'yin tugaganini tekshirish funksiyasi
async def check_game_over(chat_id, context):
    game = GAMES[chat_id]
    mafia_count = sum(1 for p in game["players"].values() if p["alive"] and p["role"] == "Mafiya")
    good_count = sum(1 for p in game["players"].values() if p["alive"] and p["role"] != "Mafiya")
    
    if mafia_count == 0:
        await context.bot.send_message(chat_id=chat_id, text="🎉 **Tinch aholi g'alaba qozondi!**\nBarcha mafiyalar yo'q qilindi.")
        game["status"] = "ended"
        return True
    elif mafia_count >= good_count:
        await context.bot.send_message(chat_id=chat_id, text="🔴 **Mafiya g'alaba qozondi!**\nShahar butunlay mafiya qo'liga o'tdi.")
        game["status"] = "ended"
        return True
    return False

# Inline tugmalarni boshqarish
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    if query.data == "join_game":
        if chat_id in GAMES and GAMES[chat_id]["status"] == "join_period":
            if user_id not in GAMES[chat_id]["players"]:
                GAMES[chat_id]["players"][user_id] = {"name": query.from_user.first_name, "role": None, "alive": True}
                count = len(GAMES[chat_id]["players"])
                
                keyboard = [
                    [InlineKeyboardButton("✅ O'yinga qo'shilish", callback_data="join_game")],
                    [InlineKeyboardButton("🚀 O'yinni start berish", callback_data="start_game")]
                ]
                await query.message.edit_text(f"🎮 **Yangi TrueMafia o'yini boshlandi!**\n\n👥 O'yinchilar jami: {count} ta\n🏃 Oxirgi qo'shilgan: {query.from_user.first_name}", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                try: await context.bot.send_message(chat_id=user_id, text="Siz qo'shilgansiz!")
                except Exception: pass

    elif query.data == "start_game":
        if chat_id in GAMES and GAMES[chat_id]["status"] == "join_period":
            if GAMES[chat_id]["creator"] != user_id: return
            
            p_ids = list(GAMES[chat_id]["players"].keys())
            if len(p_ids) < 3:
                await context.bot.send_message(chat_id=chat_id, text="❌ Kamida 3 ta odam kerak!")
                return
                
            # Rollarni tasodifiy tarqatish
            random.shuffle(p_ids)
            roles = ["Mafiya", "Komissar", "Shifokor"] + ["Fuqaro"] * (len(p_ids) - 3)
            
            for i, p_id in enumerate(p_ids):
                GAMES[chat_id]["players"][p_id]["role"] = roles[i]
                try:
                    await context.bot.send_message(chat_id=p_id, text=f"🕵️‍♂️ **True Mafia**\n\nSizning rolingiz: **{roles[i]}**")
                except Exception:
                    pass
            
            await query.message.edit_text("🏁 O'yin boshlandi! Rollar tarqatildi.")
            await start_night(chat_id, context)

    # Tungi harakatlar qayta ishlanishi
    elif query.data.startswith("night_act_"):
        parts = query.data.split("_")
        g_id = int(parts[2])
        target_id = int(parts[3])
        
        if g_id not in GAMES or GAMES[g_id]["status"] != "night": return
        game = GAMES[g_id]
        my_role = game["players"][user_id]["role"]
        
        if my_role == "Mafiya":
            game["mafia_vote"][user_id] = target_id
            await query.edit_message_text(f"🎯 Siz {game['players'][target_id]['name']}ni otishni tanladingiz.")
        elif my_role == "Shifokor":
            game["doc_vote"] = target_id
            await query.edit_message_text(f"🟢 Siz {game['players'][target_id]['name']}ni davolashni tanladingiz.")
        elif my_role == "Komissar":
            game["cop_vote"] = target_id
            is_mafia = "Mafiya" if game["players"][target_id]["role"] == "Mafiya" else "Tinch aholi"
            await query.edit_message_text(f"🔍 Tekshiruv natijasi: {game['players'][target_id]['name']} — **{is_mafia}**!")

    # Kunduzgi ovoz berish qayta ishlanishi
    elif query.data.startswith("day_vote_"):
        parts = query.data.split("_")
        g_id = int(parts[2])
        target_id = int(parts[3])
        
        if g_id not in GAMES or GAMES[g_id]["status"] != "day": return
        game = GAMES[g_id]
        
        if not game["players"].get(user_id, {}).get("alive", False): return # O'liklar ovoz berolmaydi
        
        game["day_votes"][user_id] = target_id
        voter_name = game["players"][user_id]["name"]
        target_name = game["players"][target_id]["name"]
        
        await context.bot.send_message(chat_id=g_id, text=f"🗳 **{voter_name}** o'yinchi **{target_name}**ga ovoz berdi!")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("game", game_command))
    application.add_handler(CommandHandler("give", give_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
