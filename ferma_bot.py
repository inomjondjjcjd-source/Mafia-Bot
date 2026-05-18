import os
import sys
import subprocess
import asyncio
import time
import random
import json
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

# 🌐 RENDER UCHUN ALOHIDA WEB SERVER (PORT: 8000)
server = Flask('')
@server.route('/')
def home(): return "Mifologik Ferma Super Tizimi Aktiv!"

def run_server():
    port = int(os.environ.get("PORT", 8000))
    server.run(host='0.0.0.0', port=port)

# 🔑 ASOSIY PARAMETRLAR (TOKENINGIZ JOYLASHDIRILDI)
TOKEN = "8829005476:AAGc-b-dQ1NJycS3vMf0-tRn7H15y4kFtn4"
MAIN_ADMIN = 7920504062
MY_LICHKA = "https://t.me/inomjondjjcjd"  
CHANNEL_URL = "https://t.me/yzbedkslls"     

DATA_FILE = "ferma_database.json"
USER_DATA = {}
PROMO_CODES = {}

# ⚙️ TIZIMNING MAXFIY SOZLAMALARI (ADMIN BOSHQARADI)
SYSTEM_SETTINGS = {
    "global_tax": 0,           
    "exchange_rate": 1000,     
    "min_withdraw": 25000,     
    "daily_bonus_min": 500,    
    "daily_bonus_max": 2500,   
    "cheat_mode": True         
}

# 🐉 AJDAHOLAR DO'KONI TIZIMI
DRAGONS_SHOP = {
    "d1": {"name": "🐉 Kichik Ajdaho", "price": 0, "income": 100, "desc": "Boshlang'ich bepul sovg'a"},
    "d2": {"name": "🔥 Olovli Ajdaho", "price": 15000, "income": 2500, "desc": "Narxi: 15,000 UZS"},
    "d3": {"name": "⚡️ Imperator Ajdaho", "price": 50000, "income": 10000, "desc": "Narxi: 50,000 UZS"},
    "d4": {"name": "👑 Afsonaviy Sfenks", "price": 120000, "income": 30000, "desc": "Narxi: 120,000 UZS"}
}

def load_data():
    global USER_DATA, SYSTEM_SETTINGS, PROMO_CODES
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if "SYSTEM_SETTINGS" in loaded:
                    SYSTEM_SETTINGS.update(loaded["SYSTEM_SETTINGS"])
                    del loaded["SYSTEM_SETTINGS"]
                if "PROMO_CODES" in loaded:
                    PROMO_CODES = loaded["PROMO_CODES"]
                    del loaded["PROMO_CODES"]
                USER_DATA = {int(k): v for k, v in loaded.items()}
                print("Barcha ma'lumotlar yuklandi.")
        except Exception as e:
            print(f"Yuklashda xato: {e}")
            USER_DATA = {}
    else:
        USER_DATA = {}

def save_data():
    try:
        to_save = {str(k): v for k, v in USER_DATA.items()}
        to_save["SYSTEM_SETTINGS"] = SYSTEM_SETTINGS
        to_save["PROMO_CODES"] = PROMO_CODES
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Faylga saqlashda xato: {e}")

def get_user_data(user_id):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "money": 0,
            "gold": 0,
            "last_collect_time": time.time(),
            "dragons": {"d1": 1, "d2": 0, "d3": 0, "d4": 0},
            "last_bonus_time": 0,
            "earned_fast_done": False,
            "state": None,
            "history_deposits": 0,
            "history_withdraws": 0,
            "frozen": False,            
            "custom_income_multiplier": 1.0  
        }
        save_data()
    return USER_DATA[user_id]

def get_main_menu_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("🐉 Mening Fermam", callback_data="my_farm"), InlineKeyboardButton("🧺 Oltinlarni Yig'ish", callback_data="collect_gold")],
        [InlineKeyboardButton("🏪 Ajdaholar Do'koni", callback_data="dragon_shop"), InlineKeyboardButton("🗄 Shaxsiy Kabinet", callback_data="cabinet")],
        [InlineKeyboardButton("💳 Pul Kiritish", callback_data="deposit"), InlineKeyboardButton("💸 Pul Yechish", callback_data="withdraw")],
        [InlineKeyboardButton("🎁 2 Soatlik Bonus", callback_data="get_bonus"), InlineKeyboardButton("🚀 Pul Ishlash (2,000 UZS)", callback_data="earn_fast")]
    ]
    if user_id == MAIN_ADMIN:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = get_user_data(user_id)
    if ud["frozen"]:
        await update.message.reply_text("❌ Tizim qoidalarini buzganingiz sababli hisobingiz muzlatilgan!")
        return
    ud["state"] = None
    save_data()
    text = f"🎰 *Mifologik Ajdaholar Fermasiga Xush Kelibsiz!*\n\n💰 Balansingiz: *{ud['money']:,} UZS*\n🪙 Oltinlaringiz: *{ud['gold']:,} 🪙*"
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(user_id))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ud = get_user_data(user_id)
    
    if ud["frozen"]:
        await query.edit_message_text("❌ Hisobingiz muzlatilgan!")
        return

    back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]])

    hourly_income = (ud["dragons"].get("d1", 0) * DRAGONS_SHOP["d1"]["income"] +
                     ud["dragons"].get("d2", 0) * DRAGONS_SHOP["d2"]["income"] +
                     ud["dragons"].get("d3", 0) * DRAGONS_SHOP["d3"]["income"] +
                     ud["dragons"].get("d4", 0) * DRAGONS_SHOP["d4"]["income"])
    
    hourly_income = int(hourly_income * ud.get("custom_income_multiplier", 1.0))
    passed_seconds = time.time() - ud["last_collect_time"]
    pending_gold = int((passed_seconds / 3600.0) * hourly_income)

    if query.data == "back_home":
        ud["state"] = None
        save_data()
        text = f"🎰 *Mifologik Ajdaholar Fermasiga Xush Kelibsiz!*\n\n💰 Balansingiz: *{ud['money']:,} UZS*\n🪙 Oltinlaringiz: *{ud['gold']:,} 🪙*\n🧺 Ombordagi tushum: *{pending_gold:,} 🪙*"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(user_id))

    elif query.data == "my_farm":
        text = (
            "🐉 *Sizning Mifologik Fermangiz*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• 🐉 Kichik Ajdaho: *{ud['dragons'].get('d1',0)} ta*\n"
            f"• 🔥 Olovli Ajdaho: *{ud['dragons'].get('d2',0)} ta*\n"
            f"• ⚡️ Imperator Ajdaho: *{ud['dragons'].get('d3',0)} ta*\n"
            f"• 👑 Afsonaviy Sfenks: *{ud['dragons'].get('d4',0)} ta*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 Tezlik: *{hourly_income:,} oltin/soat*\n"
            f"🧺 Ombordagi yig'ilgan oltin: *{pending_gold:,} 🪙*\n"
            "⚙️ Tizim holati: *🎲 Random (Provably Fair)*"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_kb)

    elif query.data == "collect_gold":
        if pending_gold < 5:
            await query.edit_message_text("❌ Omborda yig'ilgan oltinlar miqdori juda kam! Biroz kuting.", reply_markup=back_kb)
        else:
            ud["gold"] += pending_gold
            ud["last_collect_time"] = time.time()
            save_data()
            await query.edit_message_text(f"🧺 Oltinlar ombordan muvaffaqiyatli yig'ib olindi!\n\nJami hisobingizdagi oltinlar: *{ud['gold']:,} 🪙*", parse_mode="Markdown", reply_markup=back_kb)

    elif query.data == "dragon_shop":
        kb = []
        for k, v in DRAGONS_SHOP.items():
            if k != "d1":
                kb.append([InlineKeyboardButton(f"Sotib olish: {v['name']}", callback_data=f"buy_{k}")])
        kb.append([InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")])
        
        text = (
            "🏪 *Ajdaholar Do'koni*\n\n"
            f"1️⃣ *{DRAGONS_SHOP['d1']['name']}*\n↳ Foyda: +{DRAGONS_SHOP['d1']['income']} oltin/soat\n↳ {DRAGONS_SHOP['d1']['desc']}\n\n"
            f"2️⃣ *{DRAGONS_SHOP['d2']['name']}*\n↳ Foyda: +{DRAGONS_SHOP['d2']['income']} oltin/soat\n↳ {DRAGONS_SHOP['d2']['desc']}\n\n"
            f"3️⃣ *{DRAGONS_SHOP['d3']['name']}*\n↳ Foyda: +{DRAGONS_SHOP['d3']['income']} oltin/soat\n↳ {DRAGONS_SHOP['d3']['desc']}\n\n"
            f"4️⃣ *{DRAGONS_SHOP['d4']['name']}*\n↳ Foyda: +{DRAGONS_SHOP['d4']['income']} oltin/soat\n↳ {DRAGONS_SHOP['d4']['desc']}\n\n"
            f"💰 Balansingiz: *{ud['money']:,} UZS*"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("buy_"):
        d_key = query.data.split("_")[1]
        dragon = DRAGONS_SHOP[d_key]
        if ud["money"] < dragon["price"]:
            await query.edit_message_text(f"❌ *Mablag' yetarli emas!*\n\nUshbu ajdahoni sotib olish uchun sizga {dragon['price']:,} UZS kerak.", parse_mode="Markdown", reply_markup=back_kb)
        else:
            ud["money"] -= dragon["price"]
            ud["dragons"][d_key] = ud["dragons"].get(d_key, 0) + 1
            save_data()
            await query.edit_message_text(f"🎉 Tabriklaymiz! `{dragon['name']}` muvaffaqiyatli sotib olindi va fermangizga qo'shildi!", reply_markup=back_kb)

    elif query.data == "cabinet":
        ex_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Oltinlarni Pulga Ayirboshlash", callback_data="exchange_gold")],
            [InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]
        ])
        text = (
            "🗄 *Foydalanuvchi Shaxsiy Profili*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Ism: *{query.from_user.first_name}*\n"
            f"🆔 ID: `{user_id}`\n\n"
            f"💰 Naqd balans: *{ud['money']:,} UZS*\n"
            f"🪙 Oltinlaringiz: *{ud['gold']:,} 🪙*\n"
            f"📈 Ayirboshlash kursi: 1,000 oltin = 100 UZS\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⚙️ Tizim xavfsizligi: *🛡 Aktiv (Provably Fair)*"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=ex_kb)

    elif query.data == "exchange_gold":
        if ud["gold"] < 1000:
            await query.edit_message_text("❌ Almashtirish uchun kamida *1,000 oltin* bo'lishi kerak!", parse_mode="Markdown", reply_markup=back_kb)
        else:
            gold_to_swap = ud["gold"]
            money_gain = int((gold_to_swap / SYSTEM_SETTINGS["exchange_rate"]) * 100)
            ud["money"] += money_gain
            ud["gold"] = 0
            save_data()
            await query.edit_message_text(f"🔄 Ayirboshlash muvaffaqiyatli tugadi!\n\nHisobingizga *+{money_gain:,} UZS* naqd pul qo'shildi!", reply_markup=back_kb)

    elif query.data == "get_bonus":
        now = time.time()
        if now - ud["last_bonus_time"] < 7200:
            rem_min = int((7200 - (now - ud["last_bonus_time"])) // 60)
            await query.edit_message_text(f"⏱ Yana *{rem_min} daqiqa* kutishingiz kerak.", parse_mode="Markdown", reply_markup=back_kb)
        else:
            gift = random.randint(SYSTEM_SETTINGS["daily_bonus_min"], SYSTEM_SETTINGS["daily_bonus_max"])
            ud["money"] += gift
            ud["last_bonus_time"] = now
            save_data()
            await query.edit_message_text(f"🎁 Kunlik bonusdan hisobingizga *+{gift} UZS* qo'shildi!", parse_mode="Markdown", reply_markup=back_kb)

    elif query.data == "deposit":
        await query.edit_message_text(f"💳 *Hisobni To'ldirish*\n\nBalansni Click yoki Payme orqali to'ldirish uchun adminga yozing:\n👉 [ADMIN LICHKASI]({MY_LICHKA})", parse_mode="Markdown", reply_markup=back_kb)

    elif query.data == "withdraw":
        if ud["money"] < SYSTEM_SETTINGS["min_withdraw"]:
            await query.edit_message_text(f"❌ *Mablag' yetarli emas!*\n\nMinimal yechish miqdori: {SYSTEM_SETTINGS['min_withdraw']:,} UZS.\nSizda hozir: *{ud['money']:,} UZS*", parse_mode="Markdown", reply_markup=back_kb)
        else:
            await query.edit_message_text(f"💸 *Pul Yechish*\n\nKarta raqamingizni adminga yuboring:\n👉 [ADMIN LICHKASI]({MY_LICHKA})", parse_mode="Markdown", reply_markup=back_kb)

    elif query.data == "earn_fast":
        if ud["earned_fast_done"]:
            await query.edit_message_text("❌ Siz bu vazifani allaqachon bajargansiz!", reply_markup=back_kb)
        else:
            sub_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Rasmiy Guruh", url=CHANNEL_URL)],
                [InlineKeyboardButton("✅ Obunani Tekshirish", callback_data="check_ferma_sub")]
            ])
            await query.edit_message_text("🚀 Guruhimizga a'zo bo'ling va srazu *2,000 UZS* naqd pulga ega bo'ling:", reply_markup=sub_kb)

    elif query.data == "check_ferma_sub":
        if not ud["earned_fast_done"]:
            ud["money"] += 2000
            ud["earned_fast_done"] = True
            save_data()
            await query.edit_message_text("✅ Rahmat! Hisobingizga *+2,000 UZS* o'tkazildi!", parse_mode="Markdown", reply_markup=back_kb)
        else:
            await query.edit_message_text("❌ Bu mukofot allaqachon olingan.", reply_markup=back_kb)

    # 👑 ADMIN PANEL
    elif query.data == "admin_panel" and user_id == MAIN_ADMIN:
        akb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Odam Balansini Sozlash", callback_data="adm_set_bal"), InlineKeyboardButton("🐉 Ajdaho Sovg'a Qilish", callback_data="adm_give_drg")],
            [InlineKeyboardButton("🛑 Odamni Bloklash/Aktivlash", callback_data="adm_freeze"), InlineKeyboardButton("📉 Tezlikni Pasaytirish/Ko'tarish", callback_data="adm_speed")],
            [InlineKeyboardButton("➕ Yangi Promokod Yaratish", callback_data="adm_promo"), InlineKeyboardButton("⚙️ Global Limitlarni O'zgartirish", callback_data="adm_limits")],
            [InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]
        ])
        await query.edit_message_text("👑 *Mifologik Ferma — Admin Panel*\n\nButun o'yinni boshqarish tizimi. Amalni tanlang:", reply_markup=akb)

    elif query.data == "adm_set_bal" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_f_bal"
        save_data()
        await query.edit_message_text("💰 Format: `ID +pul` yoki `ID -pul` ko'rinishida yozing.\n\n*Masalan:* `7920504062 +50000` ")

    elif query.data == "adm_give_drg" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_f_drg"
        save_data()
        await query.edit_message_text("🐉 Kodlar: `d1` (Kichik), `d2` (Olovli), `d3` (Imperator), `d4` (Sfenks)\nFormat: `ID AJDAHO_KODI`")

    elif query.data == "adm_freeze" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_f_freeze"
        save_data()
        await query.edit_message_text("🛑 Format: `ID HUKM`\n\n`1` = Bloklash, `0` = Blokdan ochish.")

    elif query.data == "adm_speed" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_f_speed"
        save_data()
        await query.edit_message_text("📉 Yashirincha tushumni o'zgartirish.\nFormat: `ID KOEFFITSIYENT`\n\n*Masalan:* `7920504062 0.2` (Tezlikni 5 marta pasaytiradi)")

    elif query.data == "adm_promo" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_f_promo"
        save_data()
        await query.edit_message_text("➕ Format: `KOD_NOMI SUMMA` (Masalan: `SOVGA10K 10000`) ")

    elif query.data == "adm_limits" and user_id == MAIN_ADMIN:
        ud["state"] = "wait_f_limits"
        save_data()
        await query.edit_message_text(f"⚙️ Format: `MIN_YECHISH BONUS_MAX` ko'rinishida yozing.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    ud = get_user_data(user_id)
    back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="back_home")]])

    if ud["frozen"]:
        return

    if user_id == MAIN_ADMIN and ud["state"] == "wait_f_bal":
        try:
            target_id, op = text.split()
            target_id = int(target_id)
            t_ud = get_user_data(target_id)
            if op.startswith("+"):
                t_ud["money"] += int(op.replace("+", ""))
            elif op.startswith("-"):
                t_ud["money"] -= int(op.replace("-", ""))
                if t_ud["money"] < 0: t_ud["money"] = 0
            ud["state"] = None
            save_data()
            await update.message.reply_text(f"✅ `ID: {target_id}` balansi o'zgartirildi!", reply_markup=back_kb)
        except:
            await update.message.reply_text("❌ Format xato! Namuna: `7920504062 +25000`", reply_markup=back_kb)
        return

    if user_id == MAIN_ADMIN and ud["state"] == "wait_f_drg":
        try:
            target_id, d_key = text.split()
            target_id = int(target_id)
            if d_key in DRAGONS_SHOP:
                t_ud = get_user_data(target_id)
                t_ud["dragons"][d_key] = t_ud["dragons"].get(d_key, 0) + 1
                ud["state"] = None
                save_data()
                await update.message.reply_text(f"✅ `ID: {target_id}` hisobiga yangi `{DRAGONS_SHOP[d_key]['name']}` qo'shildi!", reply_markup=back_kb)
            else: raise ValueError
        except:
            await update.message.reply_text("❌ Kod noto'g'ri! Namuna: `7920504062 d4`", reply_markup=back_kb)
        return

    if user_id == MAIN_ADMIN and ud["state"] == "wait_f_freeze":
        try:
            target_id, decision = text.split()
            target_id = int(target_id)
            t_ud = get_user_data(target_id)
            if decision == "1":
                t_ud["frozen"] = True
                msg = "muzlatildi 🛑"
            else:
                t_ud["frozen"] = False
                msg = "aktivlashtirildi ✅"
            ud["state"] = None
            save_data()
            await update.message.reply_text(f"✅ Foydalanuvchi `ID: {target_id}` {msg}!", reply_markup=back_kb)
        except:
            await update.message.reply_text("❌ Namuna: `7920504062 1`", reply_markup=back_kb)
        return

    if user_id == MAIN_ADMIN and ud["state"] == "wait_f_speed":
        try:
            target_id, mult_val = text.split()
            target_id = int(target_id)
            mult_val = float(mult_val)
            t_ud = get_user_data(target_id)
            t_ud["custom_income_multiplier"] = mult_val
            ud["state"] = None
            save_data()
            await update.message.reply_text(f"✅ Bajarildi! Tezlik koeffitsiyenti *{mult_val}* qilindi!", parse_mode="Markdown", reply_markup=back_kb)
        except:
            await update.message.reply_text("❌ Namuna: `7920504062 0.5`", reply_markup=back_kb)
        return

    if user_id == MAIN_ADMIN and ud["state"] == "wait_f_promo":
        try:
            p_code, p_sum = text.split()
            PROMO_CODES[p_code.upper()] = int(p_sum)
            ud["state"] = None
            save_data()
            await update.message.reply_text(f"✅ Promokod yaratildi:\n🔑 Kod: `{p_code.upper()}`\n💰 Summa: {int(p_sum):,} UZS", parse_mode="Markdown", reply_markup=back_kb)
        except:
            await update.message.reply_text("❌ Namuna: `KAZINO777 10000`", reply_markup=back_kb)
        return

    if user_id == MAIN_ADMIN and ud["state"] == "wait_f_limits":
        try:
            min_w, max_b = text.split()
            SYSTEM_SETTINGS["min_withdraw"] = int(min_w)
            SYSTEM_SETTINGS["daily_bonus_max"] = int(max_b)
            ud["state"] = None
            save_data()
            await update.message.reply_text("✅ Global limitlar saqlandi!", reply_markup=back_kb)
        except:
            await update.message.reply_text("❌ Namuna: `25000 3000`", reply_markup=back_kb)
        return

    if text.upper() in PROMO_CODES and ud["state"] is None:
        bonus_amt = 
