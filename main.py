import os
import sys
import subprocess
import json
import random
import urllib.parse
from threading import Thread

# 📦 KERAKLI KUTUBXONALARNI AVTO-O'RNATISH
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# 🔑 SIZNING ANIQ SOZLAMALARINGIZ (MUTLOQ TO'G'RI VARIANTI)
TOKEN = "8829005476:AAGc-b-dQ1NJycS3vMf0-tRn7H15y4kFtn4"
ADMIN_ID = 1000065923  # 👑 Sizning haqiqiy shaxsiy Telegram ID'ngiz (Bot o'ziga o'zi admin bo'lmasligi uchun to'g'rilandi!)
DATA_FILE = "ai_bot_db.json"

# 📊 MA'LUMOTLAR BAZASI
DB = {
    "users": {},       # Foydalanuvchilar balansi va ma'lumotlari
    "promocodes": {},  # Yaratilgan promokodlar
    "settings": {
        "pic_price": 600  # 💰 Har bir rasm narxi: 600 so'm
    }
}

# 💾 BAZANI YUKLASH VA SAQLASH
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
            "balance": 0,  # Yangi foydalanuvchilar balansi
            "total_pics": 0
        }
        save_db()
    return DB["users"][user_id]

# 👋 START BUYRUG'I
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    ud = check_user(user_id, name)
    
    price = DB["settings"]["pic_price"]
    
    txt = (
        f"👋 *Salom, {name}!*\n\n"
        f"🎨 Men daxshatli AI rasm chizadigan botman!\n"
        f"🖼 Har bir rasm chizish narxi: *{price} so'm*\n"
        f"💰 Sening balansing: *{ud['balance']} so'm*\n\n"
        f"👇 Rasm chizish uchun ingliz tilida biror narsa yozib yubor (Masalan: `cyberpunk wolf` yoki `neon car`)."
    )
    
    buttons = [[InlineKeyboardButton("👤 Profil", callback_data="my_profile")]]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("👑 SHOX (Admin) Paneli", callback_data="admin_main")])
        
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# 👤 PROFIL VA MENYU BOSHQARUVI
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = check_user(user_id)
    
    if query.data == "my_profile":
        txt = (
            f"👤 *Sening profilingiz:*\n\n"
            f"💵 Balans: *{ud['balance']} so'm*\n"
            f"🖼 Jami chizgan rasmlaring: *{ud['total_pics']} ta*\n\n"
            f"💡 Balansni to'ldirish yoki promokod ishlatish uchun adminga murojaat qing."
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_start")]])
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=kb)
        
    elif query.data == "back_to_start":
        price = DB["settings"]["pic_price"]
        txt = (
            f"🎨 Sun'iy Intellekt rasm chizish boti!\n"
            f"🖼 Rasm narxi: *{price} so'm*\n"
            f"💰 Sening balansing: *{ud['balance']} so'm*\n\n"
            f"Rasm chizish uchun matn yuboring."
        )
        buttons = [[InlineKeyboardButton("👤 Profil", callback_data="my_profile")]]
        if user_id == ADMIN_ID:
            buttons.append([InlineKeyboardButton("👑 SHOX (Admin) Paneli", callback_data="admin_main")])
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data == "admin_main" and user_id == ADMIN_ID:
        total_users = len(DB["users"])
        current_price = DB["settings"]["pic_price"]
        txt = (
            f"👑 *SHOX PANELI (ADMIN)*\n\n"
            f"👥 Jami foydalanuvchilar: *{total_users} ta*\n"
            f"💰 Hozirgi rasm narxi: *{current_price} so'm*\n\n"
            f"Boshqarish buyruqlari:\n"
            f"🔹 `/plus ID PUL` - Pul solish\n"
            f"🔹 `/minus ID PUL` - Pulni ayirish\n"
            f"🔹 `/promo KOD SUMMA` - Promokod yaratish\n"
            f"🔹 `/setprice NARX` - Rasm narxini o'zgartirish"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="back_to_start")]])
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=kb)

# 🎨 AI RASM CHIZISH MEXANIZMI
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if text.startswith('/'):
        return

    ud = check_user(user_id, update.effective_user.first_name)
    price = DB["settings"]["pic_price"]
    
    if ud["balance"] < price and user_id != ADMIN_ID:
        await update.message.reply_text(f"❌ Balansingizda yetarli pul yo'q! Rasm chizish {price} so'm. Hozirgi balansingiz: {ud['balance']} so'm.")
        return
    
    msg = await update.message.reply_text("⏳ *Ajdaho o'ylamoqda... Rasm chizilmoqda...* 🐉", parse_mode="Markdown")
    
    try:
        prompt_encoded = urllib.parse.quote(text)
        seed = random.randint(1, 999999)
        image_url = f"https://image.pollinations.ai/p/{prompt_encoded}?width=1024&height=1024&seed={seed}&nologo=true"
        
        if user_id != ADMIN_ID:
            ud["balance"] -= price
            ud["total_pics"] += 1
            save_db()
            
        await update.message.reply_photo(
            photo=image_url, 
            caption=f"🖼 *Sizning rasmingiz tayyor!*\n✍️ Prompt: `{text}`\n💰 Yechildi: {price if user_id != ADMIN_ID else 0} so'm\n💳 Qolgan balans: {ud['balance']} so'm",
            parse_mode="Markdown"
        )
        await msg.delete()
        
    except Exception as e:
        await msg.edit_text(f"❌ Rasm chizishda xatolik bo'ldi. Qaytadan urinib ko'ring.")

# 👑 ADMIN BUYRUQLARI
async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        if target_id in DB["users"]:
            DB["users"][target_id]["balance"] += amount
            save_db()
            await update.message.reply_text(f"✅ Foydalanuvchi `{target_id}` balansiga *{amount} so'm* qo'shildi!", parse_mode="Markdown")
            try:
                await context.bot.send_message(target_id, f"💰 Balansingiz admin tomonidan *{amount} so'm*ga to'ldirildi!")
            except: pass
        else:
            await update.message.reply_text("❌ Bunday foydalanuvchi topilmadi.")
    except:
        await update.message.reply_text("❌ To'g'ri yozish: `/plus ID PUL`")

async def admin_minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        if target_id in DB["users"]:
            DB["users"][target_id]["balance"] -= amount
            if DB["users"][target_id]["balance"] < 0: DB["users"][target_id]["balance"] = 0
            save_db()
            await update.message.reply_text(f"✅ Foydalanuvchi `{target_id}` balansidan *{amount} so'm* ayrildi!", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Bunday foydalanuvchi topilmadi.")
    except:
        await update.message.reply_text("❌ To'g'ri yozish: `/minus ID PUL`")

async def admin_setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        new_price = int(context.args[0])
        DB["settings"]["pic_price"] = new_price
        save_db()
        await update.message.reply_text(f"✅ Rasm chizish narxi yangilandi: *{new_price} so'm*", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ To'g'ri yozish: `/setprice NARX`")

async def admin_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        code = context.args[0].upper()
        amount = int(context.args[1])
        DB["promocodes"][code] = {"amount": amount, "used_by": []}
        save_db()
        await update.message.reply_text(f"🎁 Yangi promokod yaratildi:\n🔑 Kod: `{code}`\n💵 Qiymati: *{amount} so'm*", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ To'g'ri yozish: `/promo KOD SUMMA`")

async def use_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        code = context.args[0].upper()
        ud = check_user(user_id)
        
        if code in DB["promocodes"]:
            promo = DB["promocodes"][code]
            if user_id in promo["used_by"]:
                await update.message.reply_text("❌ Siz bu promokoddan foydalanib bo'lgansiz!")
            else:
                promo["used_by"].append(user_id)
                ud["balance"] += promo["amount"]
                save_db()
                await update.message.reply_text(f"🎉 Tabriklayman! `{code}` promokodi faollashdi. Hisobingizga *{promo['amount']} so'm* qo'shildi!", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Bunday promokod mavjud emas.")
    except:
        await update.message.reply_text("❌ Promokod ishlatish uchun: `/coupon KOD` deb yozing.")

# 🚀 ASOSIY SECTION
def main():
    load_db()
    bot_app = Application.builder().token(TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("plus", admin_plus))
    bot_app.add_handler(CommandHandler("minus", admin_minus))
    bot_app.add_handler(CommandHandler("setprice", admin_setprice))
    bot_app.add_handler(CommandHandler("promo", admin_promo))
    bot_app.add_handler(CommandHandler("coupon", use_coupon))
    bot_app.add_handler(CallbackQueryHandler(menu_callback))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))
    
    print("AI Rasm chizuvchi SHOX bot muvaffaqiyatli ishga tushdi...")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
