import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Loglarni sozlash
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.environ.get("API_TOKEN", "8798029139:AAFqEcEt-q6BhXr3an0jZMjZjYsBY_C7Z0w")

# 🔴 Sizning Telegram ID raqamingiz muvaffaqiyatli ulandi!
ADMIN_ID = 7920504062

# Foydalanuvchilar ma'lumotlari bazasi
USER_DATA = {}

def get_or_create_user(user_id, username, first_name):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "name": first_name,
            "username": username or "Mavjud emas",
            "balance": 1000, # Yangi o'yinchilarga start bonus
            "games_played": 0,
            "wins": 0
        }
    return USER_DATA[user_id]

# /start buyrug'i (Asosiy menyu)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name)
    
    text = (
        f"Salom! Men 🕵️‍♂️ **Mafia** o'yinining rasmiy botiman.\n\n"
        f"Bu yerda siz do'stlaringiz bilan mafiya o'ynashingiz va shaxsiy hisobingizni boshqarishingiz mumkin."
    )
    
    # TrueMafia uslubidagi inline tugmalar
    keyboard = [
        [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("🎲 Guruhga kirish", callback_data="join_group"), InlineKeyboardButton("🇺🇿 Til / Language", callback_data="change_lang")],
        [InlineKeyboardButton("👤 Profil", callback_data="view_profile"), InlineKeyboardButton("🎭 Rollar", callback_data="view_roles")]
    ]
    
    # Faqat siz kirganingizda Admin Panel tugmasi ham qo'shiladi
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# Maxsus /admin buyrug'i
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔️ Kechirasiz, siz bot admini emassiz!")
        return
        
    total_users = len(USER_DATA)
    admin_text = (
        f"🖥 **Mafia Bot Admin paneli**\n\n"
        f"📊 Botdagi jami a'zolar: {total_users} ta\n"
        f"⚙️ Bot holati: Faol (Online)"
    )
    keyboard = [
        [InlineKeyboardButton("📢 Hammaga xabar", callback_data="admin_broadcast"), InlineKeyboardButton("💰 Tanga berish", callback_data="admin_give_coins")],
        [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="back_to_main")]
    ]
    await update.message.reply_text(admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Tugmalar bosilganda ishlaydigan tizim
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = query.from_user
    db_user = get_or_create_user(user_id, user.username, user.first_name)
    
    if query.data == "view_profile":
        profile_text = (
            f"👤 **Sizning Profilingiz:**\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"👤 Ism: {db_user['name']}\n"
            f"💰 Hisobingiz: *{db_user['balance']} tanga*\n"
            f"🎮 O'yinlar: {db_user['games_played']} ta\n"
            f"🏆 G'alabalar: {db_user['wins']} ta"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]]
        await query.edit_message_text(profile_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif query.data == "admin_panel":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔️ Ruxsat yo'q!")
            return
        total_users = len(USER_DATA)
        admin_text = (
            f"🖥 **Mafia Bot Admin paneli**\n\n"
            f"📊 Botdagi jami a'zolar: {total_users} ta\n"
            f"⚙️ Bot holati: Faol (Online)"
        )
        keyboard = [
            [InlineKeyboardButton("📢 Hammaga xabar", callback_data="admin_broadcast"), InlineKeyboardButton("💰 Tanga berish", callback_data="admin_give_coins")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]
        ]
        await query.edit_message_text(admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif query.data == "view_roles":
        roles_text = (
            "🎭 **O'yindagi asosiy rollar:**\n\n"
            "🔴 **Mafiya** — Tunda tinch aholini o'ldiradi.\n"
            "🔵 **Komissar** — Tunda o'yinchilarni tekshiradi.\n"
            "🟢 **Shifokor** — Tunda kimnidir qutqaradi.\n"
            "⚪️ **Tinch aholi** — Kunduzi mafiyani topadi."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]]
        await query.edit_message_text(roles_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif query.data == "back_to_main":
        text = (
            f"Salom! Men 🕵️‍♂️ **Mafia** o'yinining rasmiy botiman.\n\n"
            f"Bu yerda siz do'stlaringiz bilan mafiya o'ynashingiz va shaxsiy hisobingizni boshqarishingiz mumkin."
        )
        keyboard = [
            [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🎲 Guruhga kirish", callback_data="join_group"), InlineKeyboardButton("🇺🇿 Til / Language", callback_data="change_lang")],
            [InlineKeyboardButton("👤 Profil", callback_data="view_profile"), InlineKeyboardButton("🎭 Rollar", callback_data="view_roles")]
        ]
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    else:
        await query.edit_message_text(f"Bu bo'lim yaqin kunlarda to'liq ishga tushadi!")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_filename = "mafia_bot_public.py"
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    logging.info("Bot admin panel bilan muvaffaqiyatli yoqildi...")
    application.run_polling()

if __name__ == '__main__':
    main()
    
