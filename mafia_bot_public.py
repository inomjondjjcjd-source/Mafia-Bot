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
ASSISTANT_GIFT_COUNT = {}

def get_user(user_id, name, username):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "name": name, "username": username or "yoq",
            "balance": 100, "money_uzs": 0, "role": "Tasodifiy", 
            "armor": False, "pistol": False, "camera": False, "wins": 0,
            "used_promos": []  
        }
        if user_id in ASSISTANT_ADMINS:
            USER_DATA[user_id]["balance"] = 129
            USER_DATA[user_id]["money_uzs"] = 0

    if user_id == MAIN_ADMIN:
        USER_DATA[user_id]["balance"] = 999999
        USER_DATA[user_id]["money_uzs"] = 999999
        
    return USER_DATA[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in BANNED_USERS: return
    ASK_STATE.pop(user.id, None)
    get_user(user.id, user.first_name, user.username)
    
    if update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("Guruhda o'yinni boshlash uchun /game buyrug'ini yuboring!")
        return

    text = "Martin Mafia Botiga Xush Kelibsiz!\n\nO'yinlarda yuting, so'm ishlang va do'kondan narsalar xarid qiling!"
    kb = [
        [InlineKeyboardButton("Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("Hisob (Profil)", callback_data="my_account"), InlineKeyboardButton("Do'kon", callback_data="shop")],
        [InlineKeyboardButton("Promokod kiritish", callback_data="enter_promo"), InlineKeyboardButton("Reyting", callback_data="rank")],
        [InlineKeyboardButton("Olmos so'rash", callback_data="ask")]
    ]
    if user.id == MAIN_ADMIN or user.id in ASSISTANT_ADMINS:
        kb.append([InlineKeyboardButton("Admin Panel", callback_data="admin_panel")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

# 🔥 AYNIAN SIZ XOHLAGAN MANTIQ: Guruhda forward qilingan xabarga Reply qilib /give yozganda olmos berish
async def give_cmd_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = update.effective_user.id
    if u_id in BANNED_USERS: return
    if u_id != MAIN_ADMIN and u_id not in ASSISTANT_ADMINS: return

    msg = update.message
    target_user = None

    # Guruhda biron bir xabarga Reply (javob) berilgan bo'lsa
    if msg.reply_to_message:
        # O'sha xabarni guruhga kim forward qilib (uzatib) tashlagan bo'lsa, o'sha odamni oladi!
        target_user = msg.reply_to_message.from_user

    if not target_user:
        await msg.reply_text("❌ Olmos berish uchun guruhga forward qilingan (yoki oddiy yozilgan) xabarga Reply (javob) qilib yozing!")
        return

    # 1. BOSH ADMIN UCHUN MANTIQ (/give miqdor)
    if u_id == MAIN_ADMIN:
        try:
            amt = int(context.args[0]) if context.args else 10 # Miqdor yozilmasa avtomatik 10 ta
            user_db = get_user(target_user.id, target_user.first_name, target_user.username)
            user_db["balance"] += amt
            await msg.reply_text(f"👑 *Bosh Admin mukofoti!*\n\n👤 {target_user.first_name} (ID: `{target_user.id}`) hisobiga *+{amt} 💎* olmos qo'shildi!\nHozirgi balansi: {user_db['balance']} ta.", parse_mode="Markdown")
        except:
            await msg.reply_text("❌ Miqdorni to'g'ri raqamda yozing! Namuna: `/give 10`", parse_mode="Markdown")

    # 2. YORDAMCHI ADMIN UCHUN MANTIQ
    elif u_id in ASSISTANT_ADMINS:
        current_gifts = ASSISTANT_GIFT_COUNT.get(u_id, 0)
        if current_gifts >= 6:
            await msg.reply_text("❌ Siz 6 marta sovg'a berish limitidan to'liq foydalanib bo'ldingiz!")
            return
        
        user_db = get_user(target_user.id, target_user.first_name, target_user.username)
        user_db["balance"] += 5
        ASSISTANT_GIFT_COUNT[u_id] = current_gifts + 1
        
        await msg.reply_text(
            f"🎁 *Yordamchi Admin sovg'asi!*\n\n👤 {target_user.first_name} hisobiga sening hisobingdan *5 ta olmos* o'tkazildi!\n"
            f"Sizda qolgan limit: *{6 - ASSISTANT_GIFT_COUNT[u_id]}/6* marta.", parse_mode="Markdown"
        )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = update.effective_user.id
    text = update.message.text.strip()
    
    if text.startswith('/start'):
        ASK_STATE.pop(u_id, None)
        await start(update, context)
        return

    if u_id in BANNED_USERS or u_id not in ASK_STATE: return

    # Admin paneldagi shaxsiy mantiqlar (o'zgarishsiz)
    if ASK_STATE[u_id] == "waiting_amount" and text.isdigit():
        ASK_STATE.pop(u_id)
        await update.message.reply_text(f"Olmos so'rovi yuborildi...")

    elif u_id == MAIN_ADMIN and ASK_STATE[u_id] == "waiting_assistant_id" and text.isdigit():
        ASK_STATE.pop(u_id)
        target_admin = int(text)
        ASSISTANT_ADMINS.add(target_admin)
        ASSISTANT_GIFT_COUNT[target_admin] = 0
        await update.message.reply_text(f"ID {text} Yordamchi Admin bo'ldi!")

    elif u_id == MAIN_ADMIN and ASK_STATE[u_id] == "waiting_give_data":
        try:
            tid, amt = map(int, text.split())
            user_db = get_user(tid, "O'yinchi", "")
            user_db["balance"] += amt
            ASK_STATE.pop(u_id)
            await update.message.reply_text(f"ID {tid} olmoslari o'zgardi! Jami: {user_db['balance']} ta.")
        except: await update.message.reply_text("Xato format!")

    elif (u_id == MAIN_ADMIN or u_id in ASSISTANT_ADMINS) and ASK_STATE[u_id] == "waiting_ban_id" and text.isdigit():
        ASK_STATE.pop(u_id)
        BANNED_USERS.add(int(text))
        await update.message.reply_text(f"ID {text} bloklandi!")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u_id = query.from_user.id
    if u_id in BANNED_USERS: return
    db = get_user(u_id, query.from_user.first_name, query.from_user.username)

    if query.data == "my_account":
        has_armor = "Bor" if db['armor'] else "Yoq"
        text = f"Hisobingiz:\n\nIsm: {query.from_user.first_name}\nID: {u_id}\nOlmos: {db['balance']}\nPul: {db['money_uzs']} UZS\nZirh: {has_armor}"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Orqaga", callback_data="home")]]))
    elif query.data == "home":
        ASK_STATE.pop(u_id, None)
        await query.edit_message_text("Martin Mafia Bot menyusi:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],[InlineKeyboardButton("Hisob", callback_data="my_account")],[InlineKeyboardButton("Admin Panel", callback_data="admin_panel")] if u_id==MAIN_ADMIN or u_id in ASSISTANT_ADMINS else [InlineKeyboardButton("Reyting", callback_data="rank")]]))
    elif query.data == "admin_panel":
        if u_id == MAIN_ADMIN:
            text = "Bosh Admin Panel"; kb = [[InlineKeyboardButton("Olmos +/-", callback_data="adm_give")],[InlineKeyboardButton("Banlash", callback_data="adm_ban")],[InlineKeyboardButton("Yordamchi Admin+", callback_data="adm_add")],[InlineKeyboardButton("Orqaga", callback_data="home")]]
        elif u_id in ASSISTANT_ADMINS:
            text = "Yordamchi Admin"; kb = [[InlineKeyboardButton("Banlash", callback_data="adm_ban")],[InlineKeyboardButton("Orqaga", callback_data="home")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    elif query.data == "adm_add" and u_id == MAIN_ADMIN: ASK_STATE[u_id] = "waiting_assistant_id"; await query.edit_message_text("ID kiriting:")
    elif query.data == "adm_give" and u_id == MAIN_ADMIN: ASK_STATE[u_id] = "waiting_give_data"; await query.edit_message_text("ID va miqdor kiriting:")
    elif query.data == "adm_ban": ASK_STATE[u_id] = "waiting_ban_id"; await query.edit_message_text("Ban ID kiriting:")

async def game_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g_id = update.effective_chat.id
    GAMES[g_id] = {"status": "join", "players": {}}
    await update.message.reply_text("Martin Mafia boshlandi!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("O'yinga qo'shilish", callback_data=f"j_{g_id}")]]))

def main():
    Thread(target=run_server).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("game", game_cmd))
    app.add_handler(CommandHandler("give", give_cmd_handler)) 
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
    
