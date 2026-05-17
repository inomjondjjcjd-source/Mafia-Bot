import os
import random
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Render o'chib qolmasligi uchun mitti veb-server
server = Flask('')
@server.route('/')
def home(): return "Mafia Bot Tirik!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# Bot Tokeni va Admin sozlamalari
TOKEN = "8771036463:AAFtaCJUKZmB7B0fazFKkZ_slVN7eHtHn2A"
ADMIN_ID = 7920504062
ADMIN_GROUP_ID = -1002447990504  # Admin guruhingiz IDsi

USER_DATA = {}
GAMES = {}

def get_user(user_id, name, username):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "name": name, "username": username or "yo'q",
            "balance": 100, "role": "Tasodifiy 🎲", "armor": False, "wins": 0
        }
    if user_id == ADMIN_ID:
        USER_DATA[user_id]["balance"] = 999999
    return USER_DATA[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("🎮 Guruhda o'yinni boshlash uchun /game buyrug'ini yuboring!")
        return

    db = get_user(user.id, user.first_name, user.username)
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

async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args or context.args[0] != "255500":
        await update.message.reply_text("❌ Noto'g'ri promo-kod!")
        return
    db = get_user(user_id, update.effective_user.first_name, update.effective_user.username)
    db["balance"] += 500
    await update.message.reply_text("🎉 +500 💎 hisobingizga qo'shildi!")

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
        bal = "Cheksiz ♾" if u_id == ADMIN_ID else f"{db['balance']} 💎"
        text = f"🕵️‍♂️ *True Mafia*\n\n👤 Ism: {query.from_user.first_name}\n💳 Balans: {bal}\n🎭 Rol: {db['role']}\n🛡 Zirh: {'Mavjud ✅' if db['armor'] else 'Yoq ❌'}"
        kb = [
            [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🛒 Do'kon", callback_data="shop"), InlineKeyboardButton("🏆 Reyting", callback_data="rank")],
            [InlineKeyboardButton("🙋‍♂️ Olmos so'rash", callback_data="ask")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

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

    elif query.data == "ask":
        try:
            await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=f"🔔 *Olmos So'rovi!*\n\n👤 Foydalanuvchi: {query.from_user.first_name}\n🆔 ID: `{u_id}`\n🌐 Username: @{query.from_user.username or 'yoq'}\n\nTekin olmos so'ramoqda!")
            await query.edit_message_text("✅ So'rov adminga yuborildi!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]]))
        except Exception:
            await query.edit_message_text("⚠️ Xatolik! Admin guruhi topilmadi.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]]))

    elif query.data.startswith("j_"):
        g_id = int(query.data.split("_")[1])
        if g_id in GAMES and u_id not in GAMES[g_id]["players"] and len(GAMES[g_id]["players"]) < 10:
            GAMES[g_id]["players"][u_id] = {"name": query.from_user.first_name, "role": None, "alive": True}
            await context.bot.send_message(chat_id=g_id, text=f"✅ *{query.from_user.first_name}* o'yinga qo'shildi!", parse_mode="Markdown")

async def game_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g_id = update.effective_chat.id
    if update.effective_chat.type not in ["group", "supergroup"]: return
    GAMES[g_id] = {"status": "join", "players": {}}
    kb = [[InlineKeyboardButton("➕ Qo'shilish", callback_data=f"j_{g_id}")]]
    await update.message.reply_text("🎬 *Mafiya o'yini boshlandi!*\n\nKamida 4 ta ishtirokchi kerak. Vaqt: 30 soniya.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    
    await asyncio.sleep(30)
    if len(GAMES[g_id]["players"]) < 4:
        await context.bot.send_message(chat_id=g_id, text="❌ O'yinchilar yetarli emas! O'yin bekor qilindi.")
        return
    
    # Rollarni tarqatish
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

async def give_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id, amt = int(context.args[0]), int(context.args[1])
        get_user(t_id, "O'yinchi", "")["balance"] += amt
        await update.message.reply_text(f"💎 ID `{t_id}` ga {amt} olmos berildi!")
    except Exception: pass

def main():
    Thread(target=run_server).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("game", game_cmd))
    app.add_handler(CommandHandler("give", give_cmd))
    app.add_handler(CommandHandler("promokod", promo))
    app.add_handler(CallbackQueryHandler(buttons))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
        
