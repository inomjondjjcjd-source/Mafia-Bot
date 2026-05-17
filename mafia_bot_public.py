import os
import random
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Render o'chib qolmasligi uchun veb-server
server = Flask('')
@server.route('/')
def home(): return "Mafia Bot Tirik!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# Bot Tokeni va Admin sozlamalari
TOKEN = "8771036463:AAFtaCJUKZmB7B0fazFKkZ_slVN7eHtHn2A"
ADMIN_ID = 7920504062  # Bosh admin ID raqami

USER_DATA = {}
GAMES = {}
ASK_STATE = {}  # Olmos so'rash holatlarini saqlash uchun

def get_user(user_id, name, username):
    global ADMIN_ID
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "name": name, "username": username or "yo'q",
            "balance": 100, "role": "Tasodifiy 🎲", "armor": False, "wins": 0,
            "used_promo": False
        }
    if user_id == 7920504062 or username == "inomjon_21008":
        ADMIN_ID = user_id
        USER_DATA[user_id]["balance"] = 999999
    return USER_DATA[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = get_user(user.id, user.first_name, user.username)
    
    if update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("🎮 Guruhda o'yinni boshlash uchun /game buyrug'ini yuboring!")
        return

    bal = "Cheksiz ♾" if user.id == ADMIN_ID else f"{db['balance']} 💎"
    
    text = (
        f"🕵️‍♂️ *True Mafia Botiga Xush Kelibsiz!*\n\n"
        f"👤 *Ismingiz:* {user.first_name}\n"
        f"💳 *Balansingiz:* {bal}\n"
        f"🎭 *Tanlangan rol:* {db['role']}\n"
        f"🛡 *Zirh (Bronjilet):* {'Mavjud ✅' if db['armor'] else 'Yoq ❌'}\n\n"
        f"🚀 Guruhda do'stlaringiz bilan mafiya o'ynash uchun botni guruhga qo'shing!"
    )
    kb = [
        [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("🛒 Do'kon", callback_data="shop"), InlineKeyboardButton("🏆 Reyting", callback_data="rank")],
        [InlineKeyboardButton("🙋‍♂️ Olmos so'rash", callback_data="ask")]
    ]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def send_ask_to_admin(user, amount, context):
    """Sening lichkangga tasdiqlash tugmalari bilan yuboradigan maxsus funksiya"""
    u_id = user.id
    admin_kb = [
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{u_id}_{amount}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{u_id}")
        ]
    ]
    
    admin_msg = (
        f"🔔 *Yangi Olmos So'rovi!*\n\n"
        f"👤 O'yinchi: {user.first_name}\n"
        f"🆔 ID: `{u_id}`\n"
        f"🌐 Username: @{user.username or 'yoq'}\n"
        f"💰 So'ralgan miqdor: *{amount} 💎*\n\n"
        f"Quyidagi tugmalardan birini bosing:"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(admin_kb))
    except Exception:
        pass

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = update.effective_user.id
    text = update.message.text

    # Agar foydalanuvchi o'zi qo'lda miqdor kiritayotgan bo'lsa
    if u_id in ASK_STATE and ASK_STATE[u_id] == "waiting_amount":
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text("❌ Iltimos, faqat musbat son kiriting (Masalan: 50):")
            return
        
        amount = int(text)
        ASK_STATE[u_id] = "done"
        
        await update.message.reply_text(f"⏳ {amount} ta olmos so'rovi adminga yuborildi. Tasdiqlanishini kuting...")
        await send_ask_to_admin(update.effective_user, amount, context)

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u_id = query.from_user.id
    db = get_user(u_id, query.from_user.first_name, query.from_user.username)

    if query.data == "shop":
        text = "🛒 *Do'kon:* Rol tanlang:\n\n🕶 Mafiya (50 💎)\n🧰 Shifokor (30 💎)\n🕵️‍♂️ Komissar (40 💎)\n🛡 Zirh (70 💎)"
        kb = [
            [InlineKeyboardButton("🕶 Mafiya", callback_data="b_mafia"), InlineKeyboardButton("🧰 Shifokor", callback_data="b_doc")],
            [InlineKeyboardButton("🕵️‍♂️ Komissar", callback_data="b_cop"), InlineKeyboardButton("🛡 Zirh", callback_data="b_arm")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "home":
        if u_id in ASK_STATE: ASK_STATE.pop(u_id, None)
        bal = "Cheksiz ♾" if u_id == ADMIN_ID else f"{db['balance']} 💎"
        text = f"🕵️‍♂️ *True Mafia*\n\n👤 Ism: {query.from_user.first_name}\n💳 Balans: {bal}\n🎭 Rol: {db['role']}\n🛡 Zirh: {'Mavjud ✅' if db['armor'] else 'Yoq ❌'}"
        kb = [
            [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🛒 Do'kon", callback_data="shop"), InlineKeyboardButton("🏆 Reyting", callback_data="rank")],
            [InlineKeyboardButton("🙋‍♂️ Olmos so'rash", callback_data="ask")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # OYINCHI OLMOS SORASH TUGMASINI BOSGANDA (20, 30, 40 variantlar chiqadi)
    elif query.data == "ask":
        text = "💰 *Qancha olmos so'ramoqchisiz?*\n\nTayyor miqdorlardan birini tanlang yoki o'zingiz yozing:"
        kb = [
            [
                InlineKeyboardButton("20 💎", callback_data="amt_20"),
                InlineKeyboardButton("30 💎", callback_data="amt_30"),
                InlineKeyboardButton("40 💎", callback_data="amt_40")
            ],
            [InlineKeyboardButton("✍️ Boshqa miqdor", callback_data="amt_custom")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # TAYYOR TUGMALAR BOSILGANDA
    elif query.data.startswith("amt_"):
        mode = query.data.split("_")[1]
        if mode == "custom":
            ASK_STATE[u_id] = "waiting_amount"
            await query.edit_message_text(
                "✍️ *Siz xohlagan olmos miqdorini raqamda yozib yuboring:*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bekor qilish", callback_data="ask")]])
            )
        else:
            amount = int(mode)
            await query.edit_message_text(f"⏳ {amount} ta olmos so'rovi adminga yuborildi. Tasdiqlanishini kuting...")
            await send_ask_to_admin(query.from_user, amount, context)

    # ADMIN TASDIQLASH TUGMASI BOSILGANDA
    elif query.data.startswith("approve_"):
        if u_id != ADMIN_ID: return
        data = query.data.split("_")
        target_id = int(data[1])
        amount = int(data[2])
        
        user_db = get_user(target_id, "O'yinchi", "")
        user_db["balance"] += amount
        
        await query.edit_message_text(f"✅ Siz ID `{target_id}` bo'lgan foydalanuvchining {amount} ta olmos so'rovini tasdiqladingiz.")
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🎉 *Xushxabar!*\n\nBosh admin so'rovingizni tasdiqladi va hisobingizga *+{amount} 💎* qo'shdi!\nHozirgi balansingiz: {user_db['balance']} olmos.",
                parse_mode="Markdown"
            )
        except Exception: pass

    # ADMIN RAD ETISH TUGMASI BOSILGANDA
    elif query.data.startswith("reject_"):
        if u_id != ADMIN_ID: return
        target_id = int(query.data.split("_")[1])
        
        await query.edit_message_text(f"❌ Siz ID `{target_id}` bo'lgan foydalanuvchining so'rovini rad etdingiz.")
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="❌ Afsuski, bosh admin sening olmos so'rovingni rad etdi.",
                parse_mode="Markdown"
            )
        except Exception: pass

    elif query.data.startswith("b_"):
        item = query.data.split("_")[1]
        prices = {"mafia": 50, "doc": 30, "cop": 40, "arm": 70}
        if db["balance"] < prices[item] and u_id != ADMIN_ID:
            await query.edit_message_text("❌ Olmos yetarli emas!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="shop")]]))
            return
        if u_id != ADMIN_ID: db["balance"] -= prices[item]
        if item == "arm": db["armor"] = True
        else: db["role"] = "Mafiya 🕶" if item=="mafia" else "Shifokor 🧰" if item=="doc" else "Komissar 🕵️‍♂️"
        await query.edit_message_text("🎉 Xarid muvaffaqiyatli yakunlandi!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]]))

    elif query.data == "rank":
        users = sorted(USER_DATA.items(), key=lambda x: x[1]["wins"], reverse=True)[:5]
        text = "🏆 *Top O'yinchilar:*\n\n" + "\n".join([f"👤 *{u[1]['name']}* — {u[1]['wins']} g'alaba" for u in users]) if users else "🏆 Hozircha g'oliblar yo'q."
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]]))

    elif query.data.startswith("j_"):
        g_id = int(query.data.split("_")[1])
        if g_id in GAMES and GAMES[g_id]["status"] == "join":
            if u_id not in GAMES[g_id]["players"] and len(GAMES[g_id]["players"]) < 10:
                GAMES[g_id]["players"][u_id] = {"name": query.from_user.first_name, "role": None, "alive": True}
                await context.bot.send_message(chat_id=g_id, text=f"✅ *{query.from_user.first_name}* o'yinga qo'shildi!")

    elif query.data.startswith("admin_start_"):
        g_id = int(query.data.split("_")[2])
        if u_id != ADMIN_ID: return
        if g_id in GAMES and GAMES[g_id]["status"] == "join":
            if len(GAMES[g_id]["players"]) < 4:
                await context.bot.send_message(chat_id=g_id, text="⚠️ O'yinni boshlash uchun kamida 4 ta odam qo'shilishi kerak!")
                return
            GAMES[g_id]["status"] = "playing"
            await start_game_logic(g_id, context)

    elif query.data.startswith("admin_stop_"):
        g_id = int(query.data.split("_")[2])
        if u_id != ADMIN_ID: return
        if g_id in GAMES and GAMES[g_id]["status"] != "ended":
            GAMES[g_id]["status"] = "ended"
            await context.bot.send_message(chat_id=g_id, text="🛑 O'yin admin tomonidan majburiy to'xtatildi!")

async def game_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g_id = update.effective_chat.id
    if update.effective_chat.type not in ["group", "supergroup"]: return
    
    get_user(update.effective_user.id, update.effective_user.first_name, update.effective_user.username)
    GAMES[g_id] = {"status": "join", "players": {}}
    kb = [
        [InlineKeyboardButton("➕ O'yinga qo'shilish", callback_data=f"j_{g_id}")],
        [InlineKeyboardButton("▶️ O'yinni boshlash (Admin)", callback_data=f"admin_start_{g_id}")],
        [InlineKeyboardButton("🛑 O'yinni to'xtatish (Admin)", callback_data=f"admin_stop_{g_id}")]
    ]
    await update.message.reply_text("🎬 *True Mafia o'yini boshlandi!*\n\n🔔 Ro'yxatdan o'tish vaqti: *140 soniya*.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    
    await asyncio.sleep(140)
    if g_id in GAMES and GAMES[g_id]["status"] == "join":
        if len(GAMES[g_id]["players"]) < 4:
            await context.bot.send_message(chat_id=g_id, text="❌ O'yinchilar yetarli bo'lmadi. O'yin bekor qilindi.")
            GAMES[g_id]["status"] = "ended"
            return
        GAMES[g_id]["status"] = "playing"
        await start_game_logic(g_id, context)

async def start_game_logic(g_id, context):
    p_ids = list(GAMES[g_id]["players"].keys())
    random.shuffle(p_ids)
    GAMES[g_id]["players"][p_ids[0]]["role"] = "Mafiya 🕶"
    GAMES[g_id]["players"][p_ids[1]]["role"] = "Shifokor 🧰"
    GAMES[g_id]["players"][p_ids[2]]["role"] = "Komissar 🕵️‍♂️"
    for i in range(3, len(p_ids)): GAMES[g_id]["players"][p_ids[i]]["role"] = "Tinch aholi 🕊"

    for pid, pdata in GAMES[g_id]["players"].items():
        try: await context.bot.send_message(chat_id=pid, text=f"🎭 Sizning rolingiz: *{pdata['role']}*", parse_mode="Markdown")
        except Exception: pass
    await context.bot.send_message(chat_id=g_id, text="🎭 Rollar shaxsiy xabarlarga yuborildi!\n\n🌌 *Tun boshlanmoqda...*")

def main():
    Thread(target=run_server).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("game", game_cmd))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
