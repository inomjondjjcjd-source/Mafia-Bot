import os
import sys
import subprocess
import asyncio
import json
import time
from threading import Thread
from flask import Flask

# 📦 KUTUBXONALARNI AVTO-O'RNATISH TIZIMI
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "Flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

# 🌐 RENDER UCHUN WEB SERVER (PORT: 8000)
server = Flask('')
@server.route('/')
def home(): return "Tap to Earn Bot Aktiv!"

def run_server():
    port = int(os.environ.get("PORT", 8000))
    server.run(host='0.0.0.0', port=port)

# 🔑 ASOSIY SOZLAMALAR
TOKEN = "8829005476:AAGc-b-dQ1NJycS3vMf0-tRn7H15y4kFtn4"
MAIN_ADMIN = 7920504062
MY_LICHKA = "https://t.me/inomjondjjcjd"

DATA_FILE = "tap_bot_db.json"
USER_DATA = {}

# 📊 GLOBAL O'YIN SOZLAMALARI
GAME_SETTINGS = {
    "tap_value": 5,          # Har bir bosganda beriladigan boshlang'ich oltin miqdori
    "exchange_rate": 1000,   # 1000 oltin = 100 UZS
    "upgrade_price": 5000,   # "Tap" kuchini oshirish narxi (oltin hisobida)
    "ref_reward": 1000       # Do'stini chaqirganiga beriladigan oltin bonus
}

def load_data():
    global USER_DATA, GAME_SETTINGS
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if "GAME_SETTINGS" in loaded:
                    GAME_SETTINGS.update(loaded["GAME_SETTINGS"])
                    del loaded["GAME_SETTINGS"]
                USER_DATA = {int(k): v for k, v in loaded.items()}
        except: USER_DATA = {}

def save_data():
    try:
        to_save = {str(k): v for k, v in USER_DATA.items()}
        to_save["GAME_SETTINGS"] = GAME_SETTINGS
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=4, ensure_ascii=False)
    except: pass

def get_user(user_id):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "money": 0,          # Haqiqiy pul balansi (UZS)
            "gold": 0,           # O'yin ichidagi oltinlar miqdori
            "tap_power": 1,      # Koeffitsiyent (Masalan: tap_value * tap_power)
            "referals": 0,       # Chaqirgan odamlari soni
            "state": None
        }
        save_data()
    return USER_DATA[user_id]

def get_game_keyboard(user_id, ud):
    # Har bir bosishda qancha oltin olishini tugmaning o'zida ko'rsatadi
    click_gold = GAME_SETTINGS["tap_value"] * ud["tap_power"]
    kb = [
        [InlineKeyboardButton(f"👇 BOSH EKRAM: BOSISH (+{click_gold} 🪙)", callback_data="tap_click")],
        [InlineKeyboardButton("🚀 Kuchaytirish (Do'kon)", callback_data="shop"), InlineKeyboardButton("🗄 Kabinet (Profil)", callback_data="cabinet")],
        [InlineKeyboardButton("👥 Do'stlarni taklif qilish", callback_data="referal"), InlineKeyboardButton("💳 Pul yechish", callback_data="withdraw")]
    ]
    if user_id == MAIN_ADMIN:
        kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = get_user(user_id)
    ud["state"] = None
    
    # Referal tizimini tekshirish (/start 1234567 ko'rinishida bo'lsa)
    if context.args:
        try:
            inviter_id = int(context.args[0])
            if inviter_id != user_id and inviter_id in USER_DATA:
                # Agar bu odam botga birinchi marta kirayotgan bo'lsa
                if ud["gold"] == 0 and ud["money"] == 0 and ud["referals"] == 0:
                    i_ud = get_user(inviter_id)
                    i_ud["gold"] += GAME_SETTINGS["ref_reward"]
                    i_ud["referals"] += 1
                    save_data()
                    try:
                        await context.bot.send_message(chat_id=inviter_id, text=f"🎉 Do'stingiz botga kirdi! Sizga +{GAME_SETTINGS['ref_reward']} oltin mukofot berildi!")
                    except: pass
        except: pass

    save_data()
    txt = f"📱 *AJDAHO FERMASI: TAP TO EARN*\n\nEkrandagi daxshatli tugmani bosing va oltinlar yig'ing!\n\n💰 Naqd pul: *{ud['money']:,} UZS*\n🪙 Oltinlar: *{ud['gold']:,} 🪙*"
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=get_game_keyboard(user_id, ud))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = get_user(user_id)
    back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]])

    click_gold = GAME_SETTINGS["tap_value"] * ud["tap_power"]

    if query.data == "back_home":
        ud["state"] = None
        save_data()
        txt = f"📱 *AJDAHO FERMASI: TAP TO EARN*\n\nEkranni bosing va boyib keting!\n\n💰 Naqd pul: *{ud['money']:,} UZS*\n🪙 Oltinlar: *{ud['gold']:,} 🪙*"
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=get_game_keyboard(user_id, ud))

    elif query.data == "tap_click":
        # 🟢 ASOSIY TAP FUNKSIYASI (EKRANGA BOSGANDA OLTIN QO'SHADI)
        ud["gold"] += click_gold
        save_data()
        txt = f"📱 *AJDAHO FERMASI: TAP TO EARN*\n\n🎉 Muvaffaqiyatli bosildi! +{click_gold} oltin qo'shildi.\n\n💰 Naqd pul: *{ud['money']:,} UZS*\n🪙 Oltinlar: *{ud['gold']:,} 🪙*"
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=get_game_keyboard(user_id, ud))

    elif query.data == "shop":
        up_price = GAME_SETTINGS["upgrade_price"] * ud["tap_power"]
        skb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"⚡️ Tap kuchini +1 ga oshirish ({up_price:,} oltin)", callback_data="buy_upgrade")],
            [InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]
        ])
        txt = f"🚀 *KUCHAYTIRISH DO'KONI*\n\nHozirgi tap darajangiz: *{ud['tap_power']} LVL*\nHar safar bosganingizda: *+{click_gold} oltin* olyapsiz.\n\nKeyingi darajaga o'tish narxi: *{up_price:,} oltin*"
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=skb)

    elif query.data == "buy_upgrade":
        up_price = GAME_SETTINGS["upgrade_price"] * ud["tap_power"]
        if ud["gold"] < up_price:
            await query.edit_message_text("❌ Do'konda kuchaytirish sotib olish uchun oltinlaringiz yetarli emas, ko'proq bosing!", reply_markup=back_kb)
        else:
            ud["gold"] -= up_price
            ud["tap_power"] += 1
            save_data()
            await query.edit_message_text(f"🎉 Tabriklaymiz! Tap darajangiz *{ud['tap_power']} LVL* ga ko'tarildi! Har bir bosishingiz daxshatliroq oltin beradi.", parse_mode="Markdown", reply_markup=back_kb)

    elif query.data == "cabinet":
        ckb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Oltinlarni Pulga Almashtirish", callback_data="exchange_gold")],
            [InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]
        ])
        txt = (
            "🗄 *FOYDALANUVCHI PROFILI*\n━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Ismingiz: *{query.from_user.first_name}*\n"
            f"🆔 ID raqamingiz: `{user_id}`\n\n"
            f"🪙 Jami Oltinlar: *{ud['gold']:,} 🪙*\n"
            f"💰 Naqd Balansingiz: *{ud['money']:,} UZS*\n"
            f"📈 Kurs: {GAME_SETTINGS['exchange_rate']} oltin = 100 UZS\n━━━━━━━━━━━━━━━━━━━━\n"
            "🎰 Algoritm holati: *🛡 Provably Fair (100% Halol)*"
        )
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=ckb)

    elif query.data == "exchange_gold":
        rate = GAME_SETTINGS["exchange_rate"]
        if ud["gold"] < rate:
            await query.edit_message_text(f"❌ Almashtirish uchun hisobingizda kamida *{rate:,} oltin* bo'lishi kerak!", parse_mode="Markdown", reply_markup=back_kb)
        else:
            available_gold = ud["gold"]
            money_gain = int((available_gold / rate) * 100)
            ud["money"] += money_gain
            ud["gold"] = 0
            save_data()
            await query.edit_message_text(f"🔄 Hamma oltinlaringiz muvaffaqiyatli almashtirildi!\n\nHisobingizga *+{money_gain:,} UZS* naqd pul qo'shildi!", parse_mode="Markdown", reply_markup=back_kb)

    elif query.data == "referal":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        txt = (
            "👥 *REFERAL REJIMILARI*\n\n"
            "Do'stlaringizni botga taklif qiling va katta oltin mukofotlariga ega bo'ling!\n\n"
            f"• Har bir do'stingiz uchun: *+{GAME_SETTINGS['ref_reward']:,} oltin*\n"
            f"• Taklif qilingan do'stlaringiz: *{ud['referals']} ta*\n\n"
            f"🔗 Sizning taklif havolangiz:\n`{ref_link}`"
        )
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=back_kb)

    elif query.data == "withdraw":
        if ud["money"] < 20000:
            await query.edit_message_text(f"❌ *Mablag' yetarli emas!*\n\nMinimal pul yechish: *20,000 UZS*\nSizda hozir: *{ud['money']:,} UZS*", parse_mode="Markdown", reply_markup=back_kb)
        else:
            await query.edit_message_text(f"💸 *PUL YECHISH TIZIMI*\n\nHisobingizda pul yetarli. Kartangizga o'tkazib berishimiz uchun karta raqamingiz va ismingizni srazu adminga yuboring:\n👉 [ADMIN LICHKASI]({MY_LICHKA})", parse_mode="Markdown", reply_markup=back_kb)

    # 👑 MASTER ADMIN PANEL (BUTUN O'YIN PARAMETRLARINI BOSHQARISH)
    elif query.data == "admin_panel" and user_id == MAIN_ADMIN:
        akb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Odam Balansini Sozlash", callback_data="adm_set"), InlineKeyboardButton("🪙 Oltin Sovg'a Qilish", callback_data="adm_gold")],
            [InlineKeyboardButton("⚡️ Global Tap Qiymati", callback_data="adm_val"), InlineKeyboardButton("👥 Referal Bonusini O'zgartirish", callback_data="adm_ref")],
            [InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]
        ])
        await query.edit_message_text("👑 *TAP TO EARN ABSOLUTE PANEL*\n\nButun o'yin klik tizimini ushbu paneldan o'zgartira olasiz:", reply_markup=akb)

    elif query.data == "adm_set" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_bal"
        save_data()
        await query.edit_message_text("💰 *Foydalanuvchi real balansini o'zgartirish:*\nFormat: `ID +pul` yoki `ID -pul` ko'rinishida yozing.\n\n*Masalan:* `8086545587 +50000` (50 ming so'm beradi)")

    elif query.data == "adm_gold" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_gold"
        save_data()
        await query.edit_message_text("🪙 *Foydalanuvchiga yashirincha ko'p Oltin berish:*\nFormat: `ID +oltin` ko'rinishida yozing.\n\n*Masalan:* `8086545587 +100000` (100k oltin beradi)")

    elif query.data == "adm_val" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_val"
        save_data()
        await query.edit_message_text(f"⚡️ *Har bir bosishdagi standart oltin miqdorini o'zgartirish:*\nHozirgi qiymat: {GAME_SETTINGS['tap_value']}\n\nYangi sonni yuboring (Masalan: `10` yuborsangiz har bosganda kamida 10 tadan beradi):")

    elif query.data == "adm_ref" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_ref"
        save_data()
        await query.edit_message_text(f"👥 *Referal taklif qilgandagi global bonusni sozlash:*\nHozirgi qiymat: {GAME_SETTINGS['ref_reward']} oltin\n\nYangi qiymatni raqamda kiriting:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    ud = get_user(user_id)
    back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]])

    if user_id == MAIN_ADMIN and ud["state"] == "wait_bal":
        try:
            target_id, op = text.split()
            target_id = int(target_id)
            t_ud = get_user(target_id)
            if op.startswith("+"): t_ud["money"] += int(op.replace("+", ""))
            elif op.startswith("-"): t_ud["money"] -= int(op.replace("-", ""))
            ud["state"] = None
            save_data()
            await update.message.reply_text(f"✅ `ID: {target_id}` real balansi muvaffaqiyatli o'zgartirildi!", reply_markup=back_kb)
        except: await update.message.reply_text("❌ Xato format. Namuna: `8086545587 +20000`", reply_markup=back_kb)
        return

    if user_id == MAIN_ADMIN and ud["state"] == "wait_gold":
        try:
            target_id, op = text.split()
            target_id = int(target_id)
            t_ud = get_user(target_id)
            if op.startswith("+"): t_ud["gold"] += int(op.replace("+", ""))
            ud["state"] = None
            save_data()
            await update.message.reply_text(f"✅ `ID: {target_id}` o'yin oltinlari muvaffaqiyatli oshirildi!", reply_markup=back_kb)
        except: await update.message.reply_text("❌ Namuna: `8086545587 +50000`", reply_markup=back_kb)
        return

    if user_id == MAIN_ADMIN and ud["state"] == "wait_val":
        try:
            GAME_SETTINGS["tap_value"] = int(text)
            ud["state"] = None
            save_data()
            await update.message.reply_text(f"✅ Bajarildi! Endi har bir klik daxshatli darajada standart {text} oltindan hisoblanadi!", reply_markup=back_kb)
        except: await update.message.reply_text("❌ Faqat butun son yuboring.", reply_markup=back_kb)
        return

    if user_id == MAIN_ADMIN and ud["state"] == "wait_ref":
        try:
            GAME_SETTINGS["ref_reward"] = int(text)
            ud["state"] = None
            save_data()
            await update.message.reply_text(f"✅ Chaqirilgan referal uchun bonus o'zgartirildi: {text} oltin!", reply_markup=back_kb)
        except: await update.message.reply_text("❌ Faqat raqam kiriting.", reply_markup=back_kb)
        return

def main():
    load_data()
    Thread(target=run_server).start()
    app = Application.builder().token(TOKEN).build()
    
    try: loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(app.bot.delete_webhook(drop_pending_updates=True))
    time.sleep(1.0)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Ajdaho Tap-to-Earn boti mukammal rejimda ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
        
