import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Loglarni sozlash
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.environ.get("API_TOKEN", "8798029139:AAFqEcEt-q6BhXr3an0jZMjZjYsBY_C7Z0w")

# Soxta ma'lumotlar bazasi (Barcha foydalanuvchilar hisobi shu yerda saqlanadi)
# Haqiqiy loyihada buni saqlab qolish uchun fayl yoki baza ulanadi
USER_DATA = {}

def get_or_create_user(user_id, username, first_name):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "name": first_name,
            "username": username or "Mavjud emas",
            "balance": 1000,  # Har bir yangi o'yinchiga start bonus 1000 tanga
            "games_played": 0,
            "wins": 0
        }
    return USER_DATA[user_id]

# /start bosilganda chiqadigan asosiy menyu (Xuddi TrueMafia kabi)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_or_create_user(user.id, user.username, user.first_name)
    
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
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

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
        # Orqaga qaytish tugmasi
        keyboard = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]]
        await query.edit_message_text(profile_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif query.data == "view_roles":
        roles_text = (
            "🎭 **O'yindagi asosiy rollar:**\n\n"
            "🔴 **Mafiya** — Tunda tinch aholini o'ldiradi.\n"
            "🔵 **Komissar (Sherif)** — Tunda o'yinchilarni tekshiradi.\n"
            "🟢 **Shifokor (Do'xtir)** — Tunda kimnidir qutqara oladi.\n"
            "⚪️ **Tinch aholi** — Kunduzi mafiyani topishi kerak."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]]
        await query.edit_message_text(roles_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif query.data == "back_to_main":
        # Bosh menyuga qaytish
        text = (
            f"Salom! Men 🕵️‍♂️ **Mafia** o'yinining rasmiy botiman.\n\n"
            f"Bu yerda siz do'stlaringiz bilan mafiya o'ynashingiz va shaxsiy hisobingizni boshqarishingiz mumkin."
        )
        keyboard = [
            [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🎲 Guruhga kirish", callback_data="join_group"), InlineKeyboardButton("🇺🇿 Til / Language", callback_data="change_lang")],
            [InlineKeyboardButton("👤 Profil", callback_data="view_profile"), InlineKeyboardButton("🎭 Rollar", callback_data="view_roles")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    else:
        await query.edit_message_text(f"Bu bo'lim yaqin kunlarda ishga tushadi! Hozircha Profil va Rollar tugmasini sinab ko'ring.")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    logging.info("Bot qayta ishga tushmoqda...")
    application.run_polling()

if __name__ == '__main__':
    main()
    
