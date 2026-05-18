import os
import sys
import subprocess
import json

# 📦 KERAKLI KUTUBXONALARNI AVTO-O'RNATISH
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# 🔑 NOLDAN YANGI SOZLAMALARINGIZ
TOKEN = "8303235336:AAEk3J42idbz1KcamIWPC2L3_IlROPeoadI"
ADMIN_ID = 8086545587  # 👑 Sening aniq shaxsiy ID'ngiz (Endi bot xato bermaydi!)
DATA_FILE = "new_reaction_bot_db.json"

# 📊 MA'LUMOTLAR BAZASI
DB = {
    "users": {},       
    "promocodes": {},  
    "settings": {
        "service_price": 500  # 💰 Xizmat narxi: 500 so'm
    }
}

def load_db():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                loaded["users"] = {int(k): v for k, v in loaded.get("users", {}).items()}
                DB = loaded
        except: pass

def save_db():
    try:
        to_save = DB.copy()
        to_save["users"] = {str(k): v for k, v in DB["users"].items()}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=4, ensure_ascii=False)
    except: pass

def check_user(user_id, name="Foydalanuvchi"):
    if user_id not in DB["users"]:
        DB["users"][user_id] = {
            "name": name,
            "balance": 100,  # 🎁 Skrinshotingizdagidek yangi a'zoga 100 so'm bonus!
            "channels": [],
            "limit": 0,
            "tarif": "Bepul"
        }
        save_db()
    return DB["users"][user_id]

# 👋 START BUYRUG'I
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    check_user(user_id, name)
    
    txt = (
        f"📣 *@ReaksiyauzBot — Kanal va Guruhlarga Reaksiya qo'shish boti!*\n\n"
        f"✨ Endi siz ham o'z kanal yoki guruhingizdagi postlarga qulay va chiroyli Reaksiyalar qo'shishingiz mumkin.\n"
        f"👍❤️🔥😮😂 — xohlagancha emojilarni tanlang va obunachilaringizni yanada faol qiling!"
    )
    
    # Skrinshotingizdagi tugmalar tizimi
    buttons = [
        [InlineKeyboardButton("🎁 Reaksiyalar sozlamalar", callback_data="reaction_settings")],
        [InlineKeyboardButton("💰 Hisobni ko'rish", callback_data="view_balance"), InlineKeyboardButton("🛍 Yangi xizmatlar", callback_data="new_services")],
        [InlineKeyboardButton("📖 Bot qo'llanmasi", callback_data="bot_guide"), InlineKeyboardButton("⭐ Sovg'alar olish", callback_data="get_gifts")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("👑 SHOX (Admin) Paneli", callback_data="admin_panel")])
        
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# 🎛 TUGMALAR BOSILGANDAGI MEXANIZM
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = check_user(user_id)
    
    # 1. REAKSIYALAR SOZLAMALARI
    if query.data == "reaction_settings":
        txt = (
            f"📣 *Reaksiyalarni ishlatish uchun avval botni kanal yoki guruhga qo'shishingiz kerak.*\n\n"
            f"👉 Quyidagi tugmalardan foydalanib, kerakli reaksiyalarni tanlang yoki ko'rish uchun bosing."
        )
        kb = [
            [InlineKeyboardButton("➕ Kanal qo'shish", callback_data="add_channel"), InlineKeyboardButton("🗑 Kanal o'chirish", callback_data="del_channel")],
            [InlineKeyboardButton("📄 Kanallar ro'yxati", callback_data="list_channels")],
            [InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="back_main")]
        ]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        
    # 2. HISOBNI KO'RISH
    elif query.data == "view_balance":
        txt = (
            f"💳 *Hisobingiz haqida:*\n\n"
            f"🆔 *ID:* `{user_id}`\n"
            f"💰 *Balans:* {ud['balance']} so'm\n"
            f"⏰ *Limit:* {ud['limit']}\n"
            f"💎 *Tarif:* {ud['tarif']}\n\n"
            f"⭐️ *Premium obunga qo'shiling!*"
        )
        kb = [
            [InlineKeyboardButton("💰 Hisob to'ldirish", callback_data="refill_balance")],
            [InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="back_main")]
        ]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        
    # 3. ORTGA QAYTISH
    elif query.data == "back_main":
        txt = (
            f"📣 *@ReaksiyauzBot — Kanal va Guruhlarga Reaksiya qo'shish boti!*\n\n"
            f"✨ Endi siz ham o'z kanal yoki guruhingizdagi postlarga qulay va chiroyli Reaksiyalar qo'shishingiz mumkin.\n"
            f"👍❤️🔥😮😂 — xohlagancha emojilarni tanlang va obunachilaringizni yanada faol qiling!"
        )
        buttons = [
            [InlineKeyboardButton("🎁 Reaksiyalar sozlamalar", callback_data="reaction_settings")],
            [InlineKeyboardButton("💰 Hisobni ko'rish", callback_data="view_balance"), InlineKeyboardButton("🛍 Yangi xizmatlar", callback_data="new_services")],
            [InlineKeyboardButton("📖 Bot qo'llanmasi", callback_data="bot_guide"), InlineKeyboardButton("⭐ Sovg'alar olish", callback_data="get_gifts")]
        ]
        if user_id == ADMIN_ID:
            buttons.append([InlineKeyboardButton("👑 SHOX (Admin) Paneli", callback_data="admin_panel")])
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

    # 4. ULANGAN KANALLAR
    elif query.data == "list_channels":
        ch_list = ud["channels"]
        if not ch_list:
            txt = "❌ Siz hali birorta ham kanal ulamagansiz uka."
        else:
            txt = "📋 *Sizning ulangan kanallaringiz:*\n\n" + "\n".join([f"🔹 {ch}" for ch in ch_list])
        kb = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="reaction_settings")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # 👑 ADMIN PANEL INTERFEYSI
    elif query.data == "admin_panel" and user_id == ADMIN_ID:
        txt = (
            f"👑 *REAKSIYA BOT - SHOX PANELI*\n\n"
            f"👥 Jami a'zolar: *{len(DB['users'])} ta*\n"
            f"💰 Xizmat narxi: *{DB['settings']['service_price']} so'm*\n\n"
            f"Admin buyruqlari:\n"
            f"🔹 `/plus ID PUL` - Foydalanuvchiga pul solish\n"
            f"🔹 `/minus ID PUL` - Balansdan pul ayirish\n"
            f"🔹 `/promo KOD SUMMA` - Yangi promokod yaratish\n"
            f"🔹 `/setprice NARX` - Xizmat narxini o'zgartirish"
        )
        kb = [[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="back_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # TEZKOR SHABLON TUGMALARI
    elif query.data in ["add_channel", "del_channel", "new_services", "bot_guide", "get_gifts", "refill_balance"]:
        txt = f"⚙️ Bu bo'lim loyihaning keyingi darsida to'liq ishga tushadi uka! Hozircha menyu strukturalari va balans tizimi daxshat ishlamoqda."
        kb = [[InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="back_main")]]
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

# 👑 ADMIN COMMANDS
async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        if target_id in DB["users"]:
            DB["users"][target_id]["balance"] += amount
            save_db()
            await update.message.reply_text(f"✅ `ID: {target_id}` balansiga *{amount} so'm* qo'shildi!")
        else:
            await update.message.reply_text("❌ Foydalanuvchi topilmadi.")
    except: await update.message.reply_text("Format: `/plus ID PUL`")

async def admin_minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        if target_id in DB["users"]:
            DB["users"][target_id]["balance"] -= amount
            save_db()
            await update.message.reply_text(f"✅ `ID: {target_id}` balansidan *{amount} so'm* ayrildi!")
    except: await update.message.reply_text("Format: `/minus ID PUL`")

async def admin_setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        price = int(context.args[0])
        DB["settings"]["service_price"] = price
        save_db()
        await update.message.reply_text(f"✅ Yangi xizmat narxi saqlandi: *{price} so'm*")
    except: await update.message.reply_text("Format: `/setprice NARX`")

async def admin_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        code = context.args[0].upper()
        amount = int(context.args[1])
        DB["promocodes"][code] = {"amount": amount, "used_by": []}
        save_db()
        await update.message.reply_text(f"🎁 Promokod yaratildi: `{code}` ({amount} so'm)")
    except: await update.message.reply_text("Format: `/promo KOD SUMMA`")

# 🚀 BOTNI ISHGA TUSHIRISH
def main():
    load_db()
    bot_app = Application.builder().token(TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("plus", admin_plus))
    bot_app.add_handler(CommandHandler("minus", admin_minus))
    bot_app.add_handler(CommandHandler("setprice", admin_setprice))
    bot_app.add_handler(CommandHandler("promo", admin_promo))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("Yangi Reaksiyalar Boti noldan daxshatli tarzda ishga tushdi...")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
        
