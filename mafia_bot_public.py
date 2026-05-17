import os
import logging
import random
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Log tizimi
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Mitti Veb-Server (Render o'chirmasligi uchun)
server = Flask('')

@server.route('/')
def home():
    return "True Mafia Bot Tirik!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# Bot Tokeni
TOKEN = "8771036463:AAFtaCJUKZmB7B0fazFKkZ_slVN7eHtHn2A"

# Admin sozlamalari (Guruh ID - belgisi bilan bo'lishi shart!)
ADMIN_ID = 7920504062
ADMIN_GROUP_ID = -1002447990504  # Guruhingiz ID raqamini shu yerga to'g'rilab yozasiz (minus belgisi bilan)

USER_DATA = {}
GAMES = {}

def get_or_create_user(user_id, username, first_name):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "name": first_name,
            "username": username or "Mavjud emas",
            "balance": 100,
            "selected_role": "Tasodifiy 🎲",
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
        await update.message.reply_text("🎮 Guruhda o'yin boshlash uchun /game buyrug'ini yuboring!")
        return
        
    bal_str = "Cheksiz ♾" if user.id == ADMIN_ID else f"{db_user['balance']} 💎"
    armor_str = "Mavjud ✅" if db_user["has_armor"] else "Yo'q ❌"
        
    text = (
        "🕵️‍♂️ *True Mafia Botiga Xush Kelibsiz!*\n\n"
        f"👤 *Ismingiz:* {user.first_name}\n"
        f"💳 *Balansingiz:* {bal_str}\n"
        f"🎭 *Keyingi o'yin roli:* {db_user['selected_role']}\n"
        f"🛡 *Zirh (Bronjilet):* {armor_str}\n\n"
        "🚀 Do'kondan o'zingiz xohlagan rolni sotib oling va guruhda do'stlaringiz bilan mafiya o'ynang!"
    )
    
    keyboard = [
        [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("🛒 Do'kon (Shop)", callback_data="open_shop"), InlineKeyboardButton("🏆 Reyting", callback_data="ranking")],
        [InlineKeyboardButton("🙋‍♂️ Olmos so'rash", callback_data="ask_diamonds")]
    ]
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = get_or_create_user(user_id, update.effective_user.username, update.effective_user.first_name)
    
    if not context.args:
        await update.message.reply_text("⚠️ Format noto'g'ri. Ishlatish: `/promokod 255500`", parse_mode="Markdown")
        return
        
    code = context.args[0].strip()
    if code != "255500":
        await update.message.reply_text("❌ Noto'g'ri promo-kod kiritdingiz!")
        return
        
    if db_user["used_promo"]:
        await update.message.reply_text("🚫 Siz ushbu promo-koddan allaqachon foydalangansiz!")
        return
        
    db_user["used_promo"] = True
    if user_id != ADMIN_ID:
        db_user["balance"] += 500
    await update.message.reply_text("🎉 Tabriklaymiz! Promo-kod faollashdi. Balansingizga +500 💎 qo'shildi!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u_id = query.from_user.id
    db_user = get_or_create_user(u_id, query.from_user.username, query.from_user.first_name)
    
    if query.data == "open_shop":
        text = (
            "🛒 *True Mafia Maxsus Do'koni*\n\n"
            "1. 🕶 *Mafiya roli* (1 ta o'yin uchun) - 50 💎\n"
            "2. 🧰 *Shifokor roli* (1 ta o'yin uchun) - 30 💎\n"
            "3. 🕵️‍♂️ *Komissar roli* (1 ta o'yin uchun) - 40 💎\n"
            "4. 🛡 *Maxsus Zirh (Bronjilet)* - 70 💎\n\n"
            "Sotib olmoqchi bo'lgan narsangizni tanlang👇"
        )
        kb = [
            [InlineKeyboardButton("🕶 Mafiya (50)", callback_data="buy_mafiya"), InlineKeyboardButton("🧰 Shifokor (30)", callback_data="buy_doc")],
            [InlineKeyboardButton("🕵️‍♂️ Komissar (40)", callback_data="buy_cop"), InlineKeyboardButton("🛡 Zirh (70)", callback_data="buy_armor")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        
    elif query.data == "back_to_main":
        bal_str = "Cheksiz ♾" if u_id == ADMIN_ID else f"{db_user['balance']} 💎"
        armor_str = "Mavjud ✅" if db_user["has_armor"] else "Yo'q ❌"
            
        text = (
            "🕵️‍♂️ *True Mafia Botiga Xush Kelibsiz!*\n\n"
            f"👤 *Ismingiz:* {query.from_user.first_name}\n"
            f"💳 *Balansingiz:* {bal_str}\n"
            f"🎭 *Keyingi o'yin roli:* {db_user['selected_role']}\n"
            f"🛡 *Zirh (Bronjilet):* {armor_str}\n\n"
            "🚀 Do'kondan o'zingiz xohlagan rolni sotib oling va guruhda do'stlaringiz bilan mafiya o'ynang!"
        )
        kb = [
            [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🛒 Do'kon (Shop)", callback_data="open_shop"), InlineKeyboardButton("🏆 Reyting", callback_data="ranking")],
            [InlineKeyboardButton("🙋‍♂️ Olmos so'rash", callback_data="ask_diamonds")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        
    elif query.data.startswith("buy_"):
        item = query.data.split("_")[1]
        prices = {"mafiya": 50, "doc": 30, "cop": 40, "armor": 70}
        roles = {"mafiya": "Mafiya 🕶", "doc": "Shifokor 🧰", "cop": "Komissar 🕵️‍♂️"}
        cost = prices[item]
        
        if u_id != ADMIN_ID and db_user["balance"] < cost:
            await query.edit_message_text("❌ Olmoslaringiz yetarli emas!", 
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛒 Do'konga qaytish", callback_data="open_shop")]]))
            return
            
        if u_id != ADMIN_ID:
            db_user["balance"] -= cost
            
        if item == "armor":
            db_user["has_armor"] = True
            await query.edit_message_text("🎉 Maxsus Zirh muvaffaqiyatli sotib olindi! Tunda sizni otishsa o'lmaysiz.",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]]))
        else:
            db_user["selected_role"] = roles[item]
            await query.edit_message_text(f"🎉 Keyingi o'yin uchun rolingiz {roles[item]} qilib belgilandi!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]]))
            
    elif query.data == "ranking":
        sorted_users = sorted(USER_DATA.items(), key=lambda x: x[1]["wins"], reverse=True)[:10]
        text = "🏆 *True Mafia Eng Kuchli O'yinchilar Reytingi:*\n\n"
        if not sorted_users:
            text += "Hozircha g'oliblar mavjud emas."
        else:
            emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            for i, (usr_id, data) in enumerate(sorted_users):
                emoji = emojis[i] if i < len(emojis) else "👤"
                text += f"{emoji} *{data['name']}* — {data['wins']} ta g'alaba\n"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]]))
        
    elif query.data == "ask_diamonds":
        try:
            await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=f"🔔 *Olmos So'rovi!*\n\n👤 O'yinchi: {query.from_user.first_name}\n🆔 ID: `{u_id}`\n🌐 Username: @{query.from_user.username or 'yoq'}\n\nUshbu foydalanuvchi tekin olmos so'ramoqda!", parse_mode="Markdown")
            await query.edit_message_text("✅ So'rovingiz guruh adminlariga yuborildi!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]]))
        except Exception as e:
            await query.edit_message_text("⚠️ Xatolik yuz berdi. Admin guruh sozlamalari noto'g'ri.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]]))

    elif query.data.startswith("join_"):
        g_id = int(query.data.split("_")[1])
        if g_id not in GAMES or GAMES[g_id]["status"] != "join":
            return
        if u_id in GAMES[g_id]["players"]:
            return
        GAMES[g_id]["players"][u_id] = {"id": u_id, "name": query.from_user.first_name, "role": None, "alive": True}
        await context.bot.send_message(chat_id=g_id, text=f"✅ *{query.from_user.first_name}* o'yinga qo'shildi!", parse_mode="Markdown")

    elif query.data.startswith("mafia_vote_") or query.data.startswith("doc_vote_") or query.data.startswith("cop_vote_"):
        parts = query.data.split("_")
        action = parts[0]
        g_id = int(parts[2])
        target_id = int(parts[3])
        
        if g_id not in GAMES or GAMES[g_id]["status"] != "night":
            return
            
        my_role = GAMES[g_id]["players"][u_id]["role"]
        if action == "mafia" and "Mafiya" in my_role:
            GAMES[g_id]["mafia_vote"] = target_id
            await query.edit_message_text(f"🎯 Siz otish uchun manabu o'yinchini tanladingiz: {GAMES[g_id]['players'][target_id]['name']}")
        elif action == "doc" and "Shifokor" in my_role:
            GAMES[g_id]["doc_vote"] = target_id
            await query.edit_message_text(f"❤️ Siz davolash uchun manabu o'yinchini tanladingiz: {GAMES[g_id]['players'][target_id]['name']}")
        elif action == "cop" and "Komissar" in my_role:
            GAMES[g_id]["cop_vote"] = target_id
            is_mafia = "⚠️ MAFIYA!" if "Mafiya" in GAMES[g_id]["players"][target_id]["role"] else "🕊 TINCH AHOLI"
            await query.edit_message_text(f"🔍 Tekshiruv natijasi: {GAMES[g_id]['players'][target_id]['name']} — {is_mafia}")

    elif query.data.startswith("day_vote_"):
        parts = query.data.split("_")
        g_id = int(parts[2])
        target_id = int(parts[3])
        if g_id not in GAMES or GAMES[g_id]["status"] != "day":
            return
        if not GAMES[g_id]["players"][u_id]["alive"]:
            return
        GAMES[g_id]["day_votes"][u_id] = target_id
        await context.bot.send_message(chat_id=g_id, text=f"📩 *{query.from_user.first_name}* gumonlanuvchiga ovoz berdi!", parse_mode="Markdown")

async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g_id = update.effective_chat.id
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Bu buyruqni faqat guruhlarda ishlatish mumkin!")
        return
        
    if g_id in GAMES and GAMES[g_id]["status"] != "ended":
        await update.message.reply_text("⚠️ Guruhda ayni damda faol o'yin ketmoqda!")
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
    
    kb = [[InlineKeyboardButton("➕ O'yinga qo'shilish", callback_data=f"join_{g_id}")]]
    await update.message.reply_text("🎬 *True Mafia o'yini boshlanmoqda!*\n\n🔔 O'yin boshlanishi uchun kamida *4 ta* o'yinchi yig'ilishi shart. Vaqt: 30 soniya.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    
    await asyncio.sleep(30)
    if len(GAMES[g_id]["players"]) < 4:
        await context.bot.send_message(chat_id=g_id, text="❌ O'yinchilar soni yetarli bo'lmadi (kamida 4 ta odam kerak edi). O'yin bekor qilindi.")
        GAMES[g_id]["status"] = "ended"
        return
        
    await start_mafia_game(g_id, context)

async def start_mafia_game(g_id, context):
    p_ids = list(GAMES[g_id]["players"].keys())
    random.shuffle(p_ids)
    
    GAMES[g_id]["players"][p_ids[0]]["role"] = "Mafiya 🕶"
    GAMES[g_id]["players"][p_ids[1]]["role"] = "Shifokor 🧰"
    GAMES[g_id]["players"][p_ids[2]]["role"] = "Komissar 🕵️‍♂️"
    for i in range(3, len(p_ids)):
        GAMES[g_id]["players"][p_ids[i]]["role"] = "Tinch aholi 🕊"
        
    for p_id in p_ids:
        db_user = USER_DATA.get(p_id, {})
        wanted = db_user.get("selected_role", "Tasodifiy 🎲")
        if "Tasodifiy" not in wanted:
            current_role_owner = next((x for x in GAMES[g_id]["players"].values() if x["role"] == wanted), None)
            if current_role_owner:
                old_role = GAMES[g_id]["players"][p_id]["role"]
                current_role_owner["role"] = old_role
                GAMES[g_id]["players"][p_id]["role"] = wanted
            db_user["selected_role"] = "Tasodifiy 🎲"

    for p_id, p_data in GAMES[g_id]["players"].items():
        try:
            await context.bot.send_message(chat_id=p_id, text=f"🎮 *O'yin boshlandi!*\n\n🎭 Sizning maxfiy rolingiz: *{p_data['role']}*", parse_mode="Markdown")
        except Exception:
            pass
            
    await context.bot.send_message(chat_id=g_id, text="🎭 *Rollar tarqatildi!* Bot har bir ishtirokchining shaxsiy xabariga rolni yubordi.\n\n🌌 *Tun boshlanmoqda...*", parse_mode="Markdown")
    await run_night(g_id, context)

async def run_night(g_id, context):
    GAMES[g_id]["status"] = "night"
    GAMES[g_id]["mafia_vote"] = None
    GAMES[g_id]["doc_vote"] = None
    GAMES[g_id]["cop_vote"] = None
    
    await context.bot.send_message(chat_id=g_id, text="🌌 *Tun keldi. Shahar uyquga ketdi...*\n\nO'yin faollari (Mafiya, Shifokor va Komissar) botning shaxsiy chatida o'z vazifalarini bajarishmoqda. 30 soniya vaqt beriladi.", parse_mode="Markdown")
    
    for p_id, p_data in GAMES[g_id]["players"].items():
        if not p_data["alive"]:
            continue
            
        targets = [InlineKeyboardButton(p["name"], callback_data=f"{p_data['role'].split()[0].lower()}_vote_{g_id}_{p['id']}") for p in GAMES[g_id]["players"].values() if p["alive"] and p["id"] != p_id]
        kb = [targets[i:i+2] for i in range(0, len(targets), 2)]
        
        if "Mafiya" in p_data["role"]:
            try: await context.bot.send_message(chat_id=p_id, text="🔫 Tunda kimni otib o'ldirmoqchisiz?", reply_markup=InlineKeyboardMarkup(kb))
            except Exception: pass
        elif "Shifokor" in p_data["role"]:
            try: await context.bot.send_message(chat_id=p_id, text="🧰 Ushbu tunda kimni davolab qutqarmoqchisiz?", reply_markup=InlineKeyboardMarkup(kb))
            except Exception: pass
        elif "Komissar" in p_data["role"]:
            try: await context.bot.send_message(chat_id=p_id, text="🔍 Kimning asl roli nima ekanligini tekshirmoqchisiz?", reply_markup=InlineKeyboardMarkup(kb))
            except Exception: pass

    await asyncio.sleep(30)
    await run_day(g_id, context)

async def run_day(g_id, context):
    GAMES[g_id]["status"] = "day"
    GAMES[g_id]["day_votes"] = {}
    
    m_vote = GAMES[g_id]["mafia_vote"]
    d_vote = GAMES[g_id]["doc_vote"]
    
    killed_name = "Hech kim o'lmadi 🕊"
    if m_vote and m_vote != d_vote:
        user_db = USER_DATA.get(m_vote, {})
        if user_db.get("has_armor", False):
            user_db["has_armor"] = False
            killed_name = f"Hech kim o'lmadi (O'yinchini 🛡 Bronjilet qutqarib qoldi!)"
        else:
            GAMES[g_id]["players"][m_vote]["alive"] = False
            killed_name = f"💀 *{GAMES[g_id]['players'][m_vote]['name']}*"
            
    await context.bot.send_message(chat_id=g_id, text=f"🌅 *Ertalab bo'ldi! Shahar uyg'ondi.*\n\n⚠️ Tungi mudhish voqealar natijasi:\nO'ldirilgan o'yinchi: {killed_name}", parse_mode="Markdown")
    
    if await check_game_end(g_id, context):
        return
        
    await context.bot.send_message(chat_id=g_id, text="📢 *Kunduzgi ovoz berish bosqichi boshlandi!*\n\nKimdan shubhalanayotgan bo'lsangiz, bot shaxsiy chatiga o'tib unga ovoz bering.", parse_mode="Markdown")
    
    for p_id, p_data in GAMES[g_id]["players"].items():
        if not p_data["alive"]:
            continue
        targets = [InlineKeyboardButton(p["name"], callback_data=f"day_vote_{g_id}_{p['id']}") for p in GAMES[g_id]["players"].values() if p["alive"]]
        kb = [targets[i:i+2] for i in range(0, len(targets), 2)]
        try: await context.bot.send_message(chat_id=p_id, text="📩 Mafiya deb gumon qilayotgan shaxsingizga ovoz bering:", reply_markup=InlineKeyboardMarkup(kb))
        except Exception: pass

    await asyncio.sleep(30)
    await resolve_day_vote(g_id, context)

async def resolve_day_vote(g_id, context):
    votes = GAMES[g_id]["day_votes"]
    if not votes:
        await context.bot.send_message(chat_id=g_id, text="🤷‍♂️ Guruh a'zolari juda sustkashlik qilishdi. Hech kim ovoz bermadi.")
    else:
        counts = {}
        for target in votes.values():
            counts[target] = counts.get(target, 0) + 1
        max_votes = max(counts.values())
        winners = [k for k, v in counts.items() if v == max_votes]
        
        if len(winners) > 1:
            await context.bot.send_message(chat_id=g_id, text="⚖️ Ovozlar soni teng kelib qoldi. Bugun hech kim qatl qilinmadi.")
        else:
            lynched = winners[0]
            GAMES[g_id]["players"][lynched]["alive"] = False
            await context.bot.send_message(chat_id=g_id, text=f"⚖️ Xalq qaroriga ko'ra gumonlanuvchi: *{GAMES[g_id]['players'][lynched]['name']}* qatl qilindi! (Roli: {GAMES[g_id]['players'][lynched]['role']})", parse_mode="Markdown")

    if await check_game_end(g_id, context):
        return
        
    GAMES[g_id]["cycle"] += 1
    await run_night(g_id, context)

async def check_game_end(g_id, context):
    mafia_alive = sum(1 for p in GAMES[g_id]["players"].values() if p["alive"] and "Mafiya" in p["role"])
    good_alive = sum(1 for p in GAMES[g_id]["players"].values() if p["alive"] and "Mafiya" not in p["role"])
    
    if mafia_alive == 0:
        await context.bot.send_message(chat_id=g_id, text="🎉 *Tinch aholi vakillari g'alaba qozonishdi!* Barcha mafiyalar yo'q qilindi.", parse_mode="Markdown")
        for p in GAMES[g_id]["players"].values():
            if "Mafiya" not in p["role"]:
                get_or_create_user(p["id"], "", "")["wins"] += 1
                if p["id"] != ADMIN_ID: USER_DATA[p["id"]]["balance"] += 30
        GAMES[g_id]["status"] = "ended"
        return True
    elif mafia_alive >= good_alive:
        await context.bot.send_message(chat_id=g_id, text="🕶 *Mafiyalar g'alaba qozonishdi!* Shahar to'liq mafiya nazoratiga o'tdi.", parse_mode="Markdown")
        for p in GAMES[g_id]["players"].values():
            if "Mafiya" in p["role"]:
                get_or_create_user(p["id"], "", "")["wins"] += 1
                if p["id"] != ADMIN_ID: USER_DATA[p["id"]]["balance"] += 50
        GAMES[g_id]["status"] = "ended"
        return True
    return False

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g_id = update.effective_chat.id
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🛑 O'yinni faqat bosh admin majburiy to'xtata oladi!")
        return
    if g_id in GAMES and GAMES[g_id]["status"] !
