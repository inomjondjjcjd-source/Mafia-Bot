import os
import random
import re
import sqlite3
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# RENDER UXLAB QOLMASLIGI UCHUN SODDA SERVER
server = Flask('')
@server.route('/')
def home(): return "Bot 100% Aktiv va Toza!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# ASOSIY SOZLAMALAR
TOKEN = "8443418214:AAHtuz30gPUOF6qpNOSZrd8MnOwGG7nhbOA"
MAIN_ADMIN = 7920504062  

# MA'LUMOTLAR BAZASINI SOZLASH (SQLITE)
DB_FILE = "casino_database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            money INTEGER DEFAULT 6000,
            last_bonus_time INTEGER DEFAULT 0,
            admin_state TEXT DEFAULT 'none',
            game_state TEXT DEFAULT 'none',
            game_bet INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_user_db(user_id, name="O'yinchi"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT money, last_bonus_time, admin_state, game_state, game_bet FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row is None:
        initial_money = 999999999 if user_id == MAIN_ADMIN else 6000
        cursor.execute("INSERT INTO users (user_id, name, money) VALUES (?, ?, ?)", (user_id, name, initial_money))
        conn.commit()
        res = {"money": initial_money, "last_bonus_time": 0, "admin_state": "none", "game_state": "none", "game_bet": 0}
    else:
        res = {
            "money": row[0],
            "last_bonus_time": row[1],
            "admin_state": row[2],
            "game_state": row[3],
            "game_bet": row[4]
        }
    conn.close()
    if user_id == MAIN_ADMIN:
        res["money"] = 999999999
    return res

def update_user_db(user_id, **kwargs):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

# BOSH MENYUGU TUGMALARI
def get_main_keyboard(user_id):
    kb = [
        [InlineKeyboardButton("🎮 Don-Don-Ziki", callback_data="menu_ddz"), InlineKeyboardButton("🎯 Dart O'yin", callback_data="menu_dart")],
        [InlineKeyboardButton("🎁 Kunlik Bonus", callback_data="menu_bonus")]
    ]
    if user_id == MAIN_ADMIN:
        kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="menu_admin")])
    return InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = get_user_db(user.id, user.first_name)
    
    # Holatlarni srazu tozalash
    update_user_db(user.id, admin_state='none', game_state='none', game_bet=0)

    text = f"🎰 *Martin Kazino Bot*\n\n💰 Balansingiz: *{db['money']:,} so'm*\n\nQuyidagi o'yinlardan birini tanlang:"
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard(user.id))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u_id = query.from_user.id
    db = get_user_db(u_id, query.from_user.first_name)
    back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="menu_home")]])

    if query.data == "menu_home":
        update_user_db(u_id, admin_state='none', game_state='none', game_bet=0)
        db = get_user_db(u_id)
        await query.edit_message_text(f"🎰 *Martin Kazino*\n\n💰 Joriy balans: *{db['money']:,} so'm*", parse_mode="Markdown", reply_markup=get_main_keyboard(u_id))

    elif query.data == "menu_bonus":
        import time
        now = int(time.time())
        # Har 12 soatda bitta haqiqiy katta bonus (asabga tegmasligi uchun vaqti kamaytirildi)
        if now - db["last_bonus_time"] < 43200:
            rem = int((43200 - (now - db["last_bonus_time"])) // 60)
            await query.edit_message_text(f"⏱ *Bonus olingan!*\nYana *{rem} daqiqa* kuting.", reply_markup=back_kb)
        else:
            gift = random.randint(1000, 5000)
            new_money = db["money"] + gift
            update_user_db(u_id, money=new_money, last_bonus_time=now)
            await query.edit_message_text(f"🎁 Tabriklaymiz!\nHisobingizga *+{gift:,} so'm* qo'shildi!", parse_mode="Markdown", reply_markup=back_kb)

    elif query.data in ["menu_ddz", "menu_dart"]:
        game_type = "ddz" if query.data == "menu_ddz" else "dart"
        update_user_db(u_id, game_state=f"wait_bet_{game_type}")
        await query.edit_message_text("✍️ *Tikmoqchi bo'lgan pul miqdoringizni kiriting:*\n*(Masalan: 2000 yoki 5000)*", parse_mode="Markdown")

    elif query.data == "menu_admin" and u_id == MAIN_ADMIN:
        update_user_db(u_id, admin_state="waiting_command")
        admin_text = "👑 *Admin Panel*\n\nFoydalanuvchiga pul berish uchun pastdagi formatda yozing:\n`ID MIQDOR`\n\n*Masalan:* `7920504062 25000`"
        await query.edit_message_text(admin_text, parse_mode="Markdown", reply_markup=back_kb)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = update.effective_user.id
    text = update.message.text.strip()
    db = get_user_db(u_id, update.effective_user.first_name)
    back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="menu_home")]])

    # 1. ADMIN PANEL ISHLASHI
    if u_id == MAIN_ADMIN and db["admin_state"] == "waiting_command":
        try:
            target_id, amount = map(int, text.split())
            target_db = get_user_db(target_id)
            update_user_db(target_id, money=target_db["money"] + amount)
            update_user_db(u_id, admin_state="none")
            await update.message.reply_text(f"✅ `ID: {target_id}` hisobiga *+{amount:,} so'm* muvaffaqiyatli qo'shildi!", parse_mode="Markdown", reply_markup=back_kb)
        except:
            await update.message.reply_text("❌ Xato format! Namuna: `7920504062 5000`", reply_markup=back_kb)
        return

    # 2. O'YINLAR UCHUN PUL TIKISH TEKSHIRUVI
    if db["game_state"].startswith("wait_bet_"):
        game_mode = db["game_state"].split("_")[2] # ddz yoki dart
        
        # FOYDALANUVCHILAR NUQTA BILAN YOZSA HAM TOG'RILASH (Masalan: 2.000 -> 2000)
        clean_text = re.sub(r'[.,\s]', '', text)
        
        if not clean_text.isdigit():
            await update.message.reply_text("❌ Iltimos, faqat toza raqam kiriting! (Masalan: 2000)")
            return
            
        bet = int(clean_text)
        if bet < 500 or bet > 50000:
            await update.message.reply_text("❌ Eng kam tikish 500 so'm, eng ko'pi 50,000 so'm!")
            return
            
        if db["money"] < bet and u_id != MAIN_ADMIN:
            await update.message.reply_text(f"❌ Balansingizda mablag' yetarli emas!\nSizda: *{db['money']:,} so'm* bor.", parse_mode="Markdown")
            return

        # Pulni yechish va o'yin holatiga o'tkazish
        if u_id != MAIN_ADMIN:
            update_user_db(u_id, money=db["money"] - bet, game_bet=bet, game_state=f"playing_{game_mode}")
        else:
            update_user_db(u_id, game_bet=bet, game_state=f"playing_{game_mode}")

        # SRAZU CHAQMOQDEK NATIJANI HISOBLASH (KUTISHLARSIZ)
        if game_mode == "ddz":
            # Don-Don-Ziki: Tikilgan pul 5000 dan baland bo'lsa bot yutish imkoniyatini pasaytiradi (Kazino balansi uchun)
            win_chance = 0.30 if bet > 5000 else 0.45
            is_win = random.random() < win_chance
            
            if is_win:
                update_user_db(u_id, money=get_user_db(u_id)["money"] + (bet * 2), game_state="none", game_bet=0)
                await update.message.reply_text(f"🎮 *Don-Don-Ziki Natijasi:*\n\n✊ Siz: *Tosh*\n✌️ Bot: *Qaychi*\n\n🏆 *Siz yutdingiz!* Hisobingizga *+{bet*2:,} so'm* qo'shildi!", parse_mode="Markdown", reply_markup=back_kb)
            else:
                update_user_db(u_id, game_state="none", game_bet=0)
                await update.message.reply_text(f"🎮 *Don-Don-Ziki Natijasi:*\n\n✌️ Siz: *Qaychi*\n✊ Bot: *Tosh*\n\n📉 *Yutqazdingiz!* Hisobingizdan *-{bet:,} so'm* ketdi.", parse_mode="Markdown", reply_markup=back_kb)

        elif game_mode == "dart":
            # Dart: Tezkor ochkolar tizimi
            u_score = random.randint(1, 6)
            b_score = random.randint(u_score + 1, 6) if (bet > 5000 or random.random() < 0.6) and u_score < 6 else random.randint(1, 6)
            
            res_text = f"🎯 *Dart Natijalari:*\n\n👤 Sizning ochkongiz: *{u_score}*\n🤖 Botning ochkosi: *{b_score}*\n\n"
            
            if u_score > b_score:
                update_user_db(u_id, money=get_user_db(u_id)["money"] + (bet * 2), game_state="none", game_bet=0)
                res_text += f"🏆 *Ajoyib! Siz yutdingiz!* \n💰 Yutuq: *+{bet*2:,} so'm*"
            elif u_score < b_score:
                update_user_db(u_id, game_state="none", game_bet=0)
                res_text += f"📉 *Bot yutdi!* \nZarar: *-{bet:,} so'm*"
            else:
                update_user_db(u_id, money=get_user_db(u_id)["money"] + bet, game_state="none", game_bet=0)
                res_text += "🤝 *Durang!* Tikilgan pulingiz o'zingizga qaytarildi."
                
            await update.message.reply_text(res_text, parse_mode="Markdown", reply_markup=back_kb)
        return

def main():
    Thread(target=run_server).start()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("Bot xatosiz va tezkor rejimda ishga tushmoqda...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
