import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Log tizimi
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Tokenni olish
TOKEN = os.environ.get("API_TOKEN", "8798029139:AAFqEcEt-q6BhXr3an0jZMjZjYsBY_C7Z0w")

# 🔴 Sizning Telegram ID raqamingiz
ADMIN_ID = 7920504062

USER_DATA = {}
GAMES = {} 
USER_STATES = {} 

def get_or_create_user(user_id, username, first_name):
    if user_id not in USER_DATA:
        if user_id == ADMIN_ID:
            balance = 9999999999
        else:
            balance = 0 
            
        USER_DATA[user_id] = {
            "name": first_name,
            "username": username or "Mavjud emas",
            "balance": balance,
            "selected_role": "Tasodifiy",
            "games_played": 0,
            "wins": 0
        }
    return USER_DATA[user_id]

# Bosh menyu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_or_create_user(user.id, user.username, user.first_name)
    
    if update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("🎲 Guruhda o'yin boshlash uchun `/game` buyrug'ini yuboring!")
        return

    text = (
        f"Salom! Men 🕵️‍♂️ **Mafia** o'yinining rasmiy botiman.\n\n"
        f"💎 Sizning balansingiz: *{db_user['balance']:,} olmos*"
    )
    
    keyboard = [
        [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("🛒 Rol sotib olish", callback_data="buy_role"), InlineKeyboardButton("👤 Profil", callback_data="view_profile")],
        [InlineKeyboardButton("🎭 Rollar ro'yxati", callback_data="view_roles"), InlineKeyboardButton("✍️ Admin", callback_data="contact_admin")]
    ]
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
        
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Guruhda o'yin boshlash (/game)
async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Bu buyruqni faqat guruhda ishlatish mumkin!")
        return
        
    GAMES[chat_id] = {
        "players": [user.id],
        "status": "join_period"
    }
    
    text = (
        f"🎮 **Yangi Mafiya o'yini boshlandi!**\n\n"
        f"O'yin yaratuvchisi: {user.first_name}\n"
        f"Hozir o'yinchilar: 1 ta\n\n"
        f"O'yinga qo'shilish uchun pastdagi tugmani bosing!"
    )
    keyboard = [[InlineKeyboardButton("✅ O'yinga qo'shilish", callback_data="join_the_game")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Olmos hadya qilish (/hadya ID miqdor)
async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        await update.message.reply_text(f"✅ Siz muvaffaqiyatli ravishda `{target_id}` foydalanuvchiga *{amount}* olmos hadya qildingiz!", parse_mode="Markdown")
        try:
            await context.bot.send_message(chat_id=target_id, text=f"💎 **Ajoyib!** Admin sizga *{amount}* olmos hadya qildi!")
        except Exception:
            pass
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Noto'g'ri format. Ishlatish: `/hadya Foydalanuvchi_ID miqdori` (Masalan: `/hadya 1234567 500`)")

# Tugmalar barchasi
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    db_user = get_or_create_user(user_id, query.from_user.username, query.from_user.first_name)
    
    if query.data == "join_the_game":
        if chat_id in GAMES:
            if user_id not in GAMES[chat_id]["players"]:
                GAMES[chat_id]["players"].append(user_id)
                count = len(GAMES[chat_id]["players"])
                rol = db_user["selected_role"]
                
                await query.message.edit_text(
                    f"🎮 **Yangi Mafiya o'yini boshlandi!**\n\n"
                    f"Hozir o'yinchilar: {count} ta\n"
                    f"Oxirgi qo'shilgan: {query.from_user.first_name} (Rol: {rol})\n\n"
                    f"O'yinga qo'shilish uchun pastdagi tugmani bosing!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ O'yinga qo'shilish", callback_data="join_the_game")]])
                )
            else:
                await context.bot.send_message(chat_id=user_id, text="ℹ️ Siz allaqachon o'yinga qo'shilgansiz!")

    elif query.data == "buy_role":
        text = (
            f"🛒 **Rollar do'koni (TrueMafia maxsus)**\n\n"
            f"🔴 **Mafiya roli** — 500 olmos\n"
            f"🔵 **Komissar roli** — 400 olmos\n"
            f"🟢 **Shifokor roli** — 300 olmos\n\n"
            f"Sizning balansingiz: *{db_user['balance']:,} olmos*\n"
            f"Hozirgi tanlangan rol: *{db_user['selected_role']}*"
        )
        keyboard = [
            [InlineKeyboardButton("🔴 Mafiya (500 💎)", callback_data="shop_mafia")],
            [InlineKeyboardButton("🔵 Komissar (400 💎)", callback_data="shop_sherif")],
            [InlineKeyboardButton("🟢 Shifokor (300 💎)", callback_data="shop_doc")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data.startswith("shop_"):
        role_map = {"shop_mafia": ("Mafiya", 500), "shop_sherif": ("Komissar", 400), "shop_doc": ("Shifokor", 300)}
        role_name, price = role_map[query.data]
        
        if db_user["balance"] >= price:
            db_user["balance"] -= price
            db_user["selected_role"] = role_name
            await query.edit_message_text(f"✅ Muvaffaqiyatli sotib olindi! Keyingi o'yinda siz aniq: **{role_name}** bo'lasiz!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="buy_role")]]))
        else:
            await context.bot.send_message(chat_id=user_id, text="❌ Rol sotib olish uchun olmoslaringiz yetarli emas!")

    elif query.data == "contact_admin":
        USER_STATES[user_id] = "waiting_admin_msg"
        await query.edit_message_text(
            "✍️ **Adminga xabar yuborish:**\n\n"
            "Menga o'z fikringizni yoki olmos so'rovingizni yozib qoldiring. Xabaringiz shundoq bot egasiga boradi!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Bekor qilish", callback_data="back_to_main")]])
        )

    elif query.data == "view_profile":
        profile_text = (
            f"👤 **Sizning Profilingiz:**\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"💎 Olmoslaringiz: *{db_user['balance']:,} ta*\n"
            f"🎭 Tanlangan rol: *{db_user['selected_role']}*\n"
            f"🎮 O'yinlar jami: {db_user['games_played']} ta"
        )
        await query.edit_message_text(profile_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]]), parse_mode="Markdown")

    elif query.data == "back_to_main":
        if query.message.chat.type in ["group", "supergroup"]: return
        if user_id in USER_STATES: del USER_STATES[user_id]
        
        text = f"Salom! Men 🕵️‍♂️ **Mafia** o'yinining rasmiy botiman.\n\n💎 Sizning balansingiz: *{db_user['balance']:,} olmos*"
        keyboard = [
            [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🛒 Rol sotib olish", callback_data="buy_role"), InlineKeyboardButton("👤 Profil", callback_data="view_profile")],
            [InlineKeyboardButton("🎭 Rollar ro'yxati", callback_data="view_roles"), InlineKeyboardButton("✍️ Admin", callback_data="contact_admin")]
        ]
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Adminga xabar uzatish funksiyasi
async def handle_user_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user
    
    if user_id in USER_STATES and USER_STATES[user_id] == "waiting_admin_msg":
        user_msg = update.message.text
        del USER_STATES[user_id]
        
        await update.message.reply_text("✅ Xabaringiz bot adminiga muvaffaqiyatli yuborildi!")
        
        admin_alert = (
            f"🔔 **Foydalanuvchidan yangi xabar keldi!**\n\n"
            f"👤 Ism: {user.first_name}\n"
            f"🏷 Username: @{user.username or 'Mavjud emas'}\n"
            f"🆔 ID raqami: `{user_id}`\n\n"
            f"💬 **Xabar matni:**\n_{user_msg}_"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_alert, parse_mode="Markdown")

def main():
    # Application yaratish (Aniq xatosiz format)
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("game", game_command))
    application.add_handler(CommandHandler("hadya", gift_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_messages))
    
    logging.info("Muvaffaqiyatli ishga tushdi...")
    # drop_pending_updates=True eski tiqilib qolgan Conflict xatolarini tozalaydi!
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
        
