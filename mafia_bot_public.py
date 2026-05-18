import os
import sys
import subprocess
import json
import asyncio
from flask import Flask
from threading import Thread

# 📦 KERAKLI KUTUBXONALARNI TEKSHIRISH VA O'RNATISH
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# 🔑 ASOSIY SOZLAMALAR
TOKEN = "8303235336:AAEk3J42idbz1KcamIWPC2L3_IlROPeoadI"
ADMIN_ID = 8086545587  # 👑 Sening shaxsiy Telegram ID'ngiz (Shox Admin)
DATA_FILE = "reaction_bot_database.json"

# 📊 MA'LUMOTLAR BAZASI STRUKTURASI
DB = {
    "users": {},       
    "promocodes": {},  
    "settings": {
        "service_price": 500  # 💰 Bitta kanal qo'shish narxi
    },
    "posts": {} # Postlardagi reaksiyalar sonini hisoblash uchun
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
            "balance": 100,  # Yangi kirganga 100 so'm bonus
            "channels": [],
            "limit": 5,
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
    
    buttons = [
        [InlineKeyboardButton("🎁 Reaksiyalar sozlamalar", callback_data="reaction_settings")],
        [InlineKeyboardButton("💰 Hisobni ko'rish", callback_data="view_balance"), InlineKeyboardButton("🛍 Yangi xizmatlar", callback_data="new_services")],
        [InlineKeyboardButton("📖 Bot qo'llanmasi", callback_data="bot_guide"), InlineKeyboardButton("⭐ Sovg'alar olish", callback_data="get_gifts")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("👑 SHOX (Admin) Paneli", callback_data="admin_panel")])
        
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# 🎛 INLINE TUGMALAR BOSILGANDA ISHLAYDIGAN TIZIM
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = check_user(user_id)
    
    # BOSH MENYUGA QAYTISH
    if query.data == "back_main":
        txt = (
            f"📣 *@ReaksiyauzBot — Kanal va Guruhlarga Reaksiya qo'shish boti!*\n\n"
            f"👍❤️🔥 — xohlagancha emojilarni tanlang va obunachilaringizni faol qiling!"
        )
        buttons = [
            [InlineKeyboardButton("🎁 Reaksiyalar sozlamalar", callback_data="reaction_settings")],
            [InlineKeyboardButton("💰 Hisobni ko'rish", callback_data="view_balance"), InlineKeyboardButton("🛍 Yangi xizmatlar", callback_data="new_services")],
            [InlineKeyboardButton("📖 Bot qo'llanmasi", callback_data="bot_guide"), InlineKeyboardButton("⭐ Sovg'alar olish", callback_data="get_gifts")]
        ]
        if user_id == ADMIN_ID:
            buttons.append([InlineKeyboardButton("👑 SHOX (Admin) Paneli", callback_data="admin_panel")])
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

    # REAKSIYALAR MENYUSI
    elif query.data == "reaction_settings":
        txt = (
            f"📣 *Reaksiyalarni ishlatish uchun avval botni kanalga administrator qilib qo'shishingiz kerak.*\n\n"
            f"👉 Kanal qo'shish uchun quyidagi tugmani bosing va kanalingiz ID raqamini yoki usernamesini yuboring."
        )
        kb = [
            [InlineKeyboardButton("➕ Kanal qo'shish", callback_data="add_channel"), InlineKeyboardButton("🗑 Kanal o'chirish", callback_data="del_channel")],
            [InlineKeyboardButton("📄 Kanallar ro'yxati", callback_data="list_channels")],
            [InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="back_main")]
        ]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # KANAL QO'SHISH REJIMI
    elif query.data == "add_channel":
        if ud["balance"] < DB["settings"]["service_price"]:
            await query.edit_message_text(
                f"❌ Balansingizda yetarli mablag' mavjud emas. Kanal ulashtirish {DB['settings']['service_price']} so'm turadi. Sizda: {ud['balance']} so'm bor.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="reaction_settings")]])
            )
            return
        context.user_data["action"] = "waiting_channel_id"
        await query.edit_message_text(
            "📢 *Kanal qo'shish uchun:*\n\n1. Botni kanalingizga Admin qiling.\n2. Kanalingiz linkini (Masalan: `@kanal_username`) menga yozib yuboring uka:",
            parse_mode="Markdown"
        )

    # KANAL O'CHIRISH REJIMI
    elif query.data == "del_channel":
        if not ud["channels"]:
            await query.edit_message_text("❌ Sizda hali ulamagan kanallar yo'q uka.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="reaction_settings")]]))
            return
        context.user_data["action"] = "waiting_delete_channel"
        txt = "🗑 *O'chirmoqchi bo'lgan kanalingiz nomini (username) aniq yozib yuboring:*\n\n" + "\n".join([f"🔹 {ch}" for ch in ch_list])
        await query.edit_message_text(txt, parse_mode="Markdown")

    # KANALLAR RO'YXATI
    elif query.data == "list_channels":
        ch_list = ud["channels"]
        if not ch_list:
            txt = "❌ Siz hali birorta ham kanal ulamagansiz uka."
        else:
            txt = "📋 *Sizning ulangan faol kanallaringiz:*\n\n" + "\n".join([f"🔹 {ch}" for ch in ch_list])
        kb = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="reaction_settings")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # HISOBNI KO'RISH
    elif query.data == "view_balance":
        txt = (
            f"💳 *Hisobingiz haqida:*\n\n"
            f"🆔 *ID:* `{user_id}`\n"
            f"💰 *Balans:* {ud['balance']} so'm\n"
            f"⏰ *Limit:* {ud['limit']} ta post\n"
            f"💎 *Tarif:* {ud['tarif']}\n\n"
            f"⭐️ *Premium obunga qo'shiling!*"
        )
        kb = [[InlineKeyboardButton("💰 Hisob to'ldirish", callback_data="refill_balance")], [InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="back_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # YANGI XIZMATLAR
    elif query.data == "new_services":
        txt = "🛍 *Yangi xizmatlar bo'limi:*\n\n🚀 1. VIP Tarif (Cheksiz reaksiyalar) — 5,000 so'm\n🔥 2. Avto-SMM xizmati — 10,000 so'm\n\nTizim tez orada to'liq integratsiya qilinadi."
        kb = [[InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="back_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # BOT QO'LLANMASI
    elif query.data == "bot_guide":
        txt = "📖 *Botdan foydalanish qo'llanmasi:*\n\n1. Botni kanalingizga qo'shib admin huquqini berasiz.\n2. /start bosib kanalingizni botga ro'yxatdan o'tkazasiz.\n3. Kanalingizga yangi post tashlasangiz, tagida avtomatik ravishda reaksiya bosish tugmalari chiqadi uka!"
        kb = [[InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="back_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # SOVG'ALAR OLISH
    elif query.data == "get_gifts":
        txt = "⭐ *Sovg'alar bo'limi!*\n\nHar kuni botga kirganingiz uchun sizga tasodifiy bonuslar taqdim etiladi. Bugungi sovg'angiz qabul qilingan uka!"
        kb = [[InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="back_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # HISOB TO'LDIRISH
    elif query.data == "refill_balance":
        txt = f"💰 *Hisobni to'ldirish uchar:* Payme/Click orqali to'lov qilish uchun Admin: @shox_admin ga yozing yoki hisobingiz `ID: {user_id}` raqamini ko'rsating uka."
        kb = [[InlineKeyboardButton("⬅️ Ortga qaytish", callback_data="back_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # POST REAKSIYALARI BOSILGANDA (REAL VAQTDA URISH)
    elif query.data.startswith("hit_"):
        _, emoji, post_id = query.data.split("_")
        if post_id not in DB["posts"]:
            DB["posts"][post_id] = {"👍": 0, "❤️": 0, "🔥": 0, "😮": 0, "😂": 0}
        
        # Reaksiyani bitta bosganda birdaniga 5-10 ta qilib avtomatik ko'paytirib berish (Siz xohlagandek!)
        DB["posts"][post_id][emoji] += 7  # Bitta bosganda 7 ta reaksiya uriladi!
        save_db()
        
        # Tugmalarni yangilash
        p_data = DB["posts"][post_id]
        new_kb = [
            [
                InlineKeyboardButton(f"👍 {p_data['👍']}", callback_data=f"hit_👍_{post_id}"),
                InlineKeyboardButton(f"❤️ {p_data['❤️']}", callback_data=f"hit_❤️_{post_id}"),
                InlineKeyboardButton(f"🔥 {p_data['🔥']}", callback_data=f"hit_🔥_{post_id}")
            ],
            [
                InlineKeyboardButton(f"😮 {p_data['😮']}", callback_data=f"hit_😮_{post_id}"),
                InlineKeyboardButton(f"😂 {p_data['😂']}", callback_data=f"hit_😂_{post_id}")
            ]
        ]
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(new_kb))
        except: pass

    # SHOX ADMIN PANEL
    elif query.data == "admin_panel" and user_id == ADMIN_ID:
        txt = (
            f"👑 *REAKSIYA BOT - SHOX PANELI*\n\n"
            f"👥 Jami foydalanuvchilar: *{len(DB['users'])} ta*\n"
            f"💰 Kanal ulash narxi: *{DB['settings']['service_price']} so'm*\n\n"
            f"Admin buyruqlari:\n"
            f"🔹 `/plus ID PUL` - Odamlarga pul solish\n"
            f"🔹 `/setprice NARX` - Narxni o'zgartirish"
        )
        kb = [[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="back_main")]]
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# ✉️ TEXT XABARLARNI QABUL QILISH (KANAL ID VA H.K.)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = check_user(user_id)
    text = update.message.text.strip()
    action = context.user_data.get("action")
    
    if action == "waiting_channel_id":
        context.user_data["action"] = None
        if not text.startswith("@"):
            await update.message.reply_text("❌ Xato! Kanal username `@` belgisi bilan boshlanishi kerak uka.")
            return
        
        # Balansdan pul yechish va kanalni saqlash
        ud["balance"] -= DB["settings"]["service_price"]
        ud["channels"].append(text)
        save_db()
        await update.message.reply_text(f"✅ Kanal muvaffaqiyatli ulandi: {text}\nBalansingizdan {DB['settings']['service_price']} so'm yechildi uka!")
        
    elif action == "waiting_delete_channel":
        context.user_data["action"] = None
        if text in ud["channels"]:
            ud["channels"].remove(text)
            save_db()
            await update.message.reply_text(f"🗑 {text} kanali ro'yxatdan o'chirildi uka.")
        else:
            await update.message.reply_text("❌ Bunday kanal ro'yxatda topilmadi.")

# 📢 KANALGA YANGI POST JOYLANGANDA AVTOMATIK REAKSIYA TUGMASI QO'YISH TIZIMI
async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_post = update.channel_post
    if not channel_post: return
    
    channel_username = f"@{channel_post.chat.username}" if channel_post.chat.username else None
    
    # Ushbu kanal tizimda ro'yxatdan o'tganmi yoki yo'qligini tekshirish
    is_registered = False
    for u_id, u_data in DB["users"].items():
        if channel_username in u_data.get("channels", []):
            is_registered = True
            break
            
    if is_registered or channel_username:
        post_id = str(channel_post.message_id)
        DB["posts"][post_id] = {"👍": 12, "❤️": 8, "🔥": 15, "😮": 0, "😂": 2} # Post chiqishi bilan srazu avtomatik reaksiyalar uriladi!
        save_db()
        
        p_data = DB["posts"][post_id]
        kb = [
            [
                InlineKeyboardButton(f"👍 {p_data['👍']}", callback_data=f"hit_👍_{post_id}"),
                InlineKeyboardButton(f"❤️ {p_data['❤️']}", callback_data=f"hit_❤️_{post_id}"),
                InlineKeyboardButton(f"🔥 {p_data['🔥']}", callback_data=f"hit_🔥_{post_id}")
            ],
            [
                InlineKeyboardButton(f"😮 {p_data['😮']}", callback_data=f"hit_😮_{post_id}"),
                InlineKeyboardButton(f"😂 {p_data['😂']}", callback_data=f"hit_😂_{post_id}")
            ]
        ]
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=channel_post.chat.id,
                message_id=channel_post.message_id,
                reply_markup=InlineKeyboardMarkup(kb)
            )
        except: pass

# 👑 ADMIN BUYRUQLARI
async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        if target_id in DB["users"]:
            DB["users"][target_id]["balance"] += amount
            save_db()
            await update.message.reply_text(f"✅ `ID: {target_id}` balansiga *{amount} so'm* qo'shildi!")
    except: pass

# 🌐 FLASK WEB SERVER
app = Flask(__name__)

@app.route('/')
def home():
    return "Reaksiya Boti Pro Tizimda Ishlamoqda!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 🚀 TIZIMNI ASINXRON ISHGA TUSHIRISH
async def main_bot():
    load_db()
    bot_app = Application.builder().token(TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("plus", admin_plus))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    bot_app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, channel_post_handler)) # Kanallarni kuzatish
    
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    Thread(target=run_flask, daemon=True).start()
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    print("Barcha bo'limlari bor mukammal avto-reaksiya kodi yoqildi...")
    loop.run_until_complete(main_bot())
        
