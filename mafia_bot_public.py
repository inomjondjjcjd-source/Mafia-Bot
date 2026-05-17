import os
import random
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Render o'chib qolmasligi uchun veb-server
server = Flask('')
@server.route('/')
def home(): return "Martin Mafia Bot Tirik!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# Bot Tokeni va Adminlar ro'yxati (Sening yangi tokening qo'yildi!)
TOKEN = "8771036463:AAE5c354ocQFb6qtrmQ2oI0gEx1MHHvvmG0"
MAIN_ADMIN = 7920504062  # Sen (Bosh admin)
ASSISTANT_ADMINS = set() # Yordamchi adminlar IDlari shu yerga tushadi
BANNED_USERS = set()     # Bloklanganlar ro'yxati

USER_DATA = {}
GAMES = {}
ASK_STATE = {}  # Turli xil kiritish holatlarini saqlash uchun

def get_user(user_id, name, username):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "name": name, "username": username or "yo'q",
            "balance": 100, "role": "Tasodifiy 🎲", 
            "armor": False, "pistol": False, "camera": False,
            "wins": 0, "used_promo": False
        }
    if user_id == MAIN_ADMIN or user_id in ASSISTANT_ADMINS:
        USER_DATA[user_id]["balance"] = 999999
    return USER_DATA[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in BANNED_USERS:
        await update.message.reply_text("🚫 Siz ushbu botdan bloklangansiz!")
        return

    db = get_user(user.id, user.first_name, user.username)
    
    if update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("🎮 Guruhda o'yinni boshlash uchun /game buyrug'ini yuboring!")
        return

    bal = "Cheksiz ♾" if (user.id == MAIN_ADMIN or user.id in ASSISTANT_ADMINS) else f"{db['balance']} 💎"
    
    text = (
        f"🕵️‍♂️ *Martin Mafia Botiga Xush Kelibsiz!*\n\n"
        f"👤 *Ismingiz:* {user.first_name}\n"
        f"💳 *Balansingiz:* {bal}\n"
        f"🎭 *Tanlangan rol:* {db['role']}\n"
        f"🛡 *Zirh (Bronjilet):* {'Mavjud ✅' if db['armor'] else 'Yoq ❌'}\n"
        f"🔫 *To'pponcha:* {'Mavjud ✅' if db.get('pistol') else 'Yoq ❌'}\n"
        f"👁 *Kamera:* {'Mavjud ✅' if db.get('camera') else 'Yoq ❌'}\n\n"
        f"🚀 Guruhda do'stlaringiz bilan Martin Mafia o'ynash uchun botni guruhga qo'shing!"
    )
    
    kb = [
        [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("🛒 Do'kon", callback_data="shop"), InlineKeyboardButton("🏆 Reyting", callback_data="rank")],
        [InlineKeyboardButton("🙋‍♂️ Olmos so'rash", callback_data="ask")]
    ]
    
    if user.id == MAIN_ADMIN or user.id in ASSISTANT_ADMINS:
        kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
        
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def send_ask_to_admins(user, amount, context):
    """Barcha adminlarga tasdiqlash tugmalari bilan yuborish"""
    u_id = user.id
    admin_kb = [
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{u_id}_{amount}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{u_id}")
        ]
    ]
    admin_msg = (
        f"🔔 *Martin Mafia — Yangi Olmos So'rovi!*\n\n"
        f"👤 O'yinchi: {user.first_name}\n"
        f"🆔 ID: `{u_id}`\n"
        f"🌐 Username: @{user.username or 'yoq'}\n"
        f"💰 So'ralgan miqdor: *{amount} 💎*\n"
    )
    try: await context.bot.send_message(chat_id=MAIN_ADMIN, text=admin_msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(admin_kb))
    except Exception: pass
    for adm in ASSISTANT_ADMINS:
        try: await context.bot.send_message(chat_id=adm, text=admin_msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(admin_kb))
        except Exception: pass

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = update.effective_user.id
    text = update.message.text

    if u_id in BANNED_USERS: return

    # 1. Olmos kiritish holati
    if u_id in ASK_STATE and ASK_STATE[u_id] == "waiting_amount":
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text("❌ Iltimos, faqat musbat son kiriting:")
            return
        amount = int(text)
        ASK_STATE[u_id] = "done"
        await update.message.reply_text(f"⏳ {amount} ta olmos so'rovi adminlarga yuborildi...")
        await send_ask_to_admins(update.effective_user, amount, context)

    # 2. Bosh admin uchun: Yordamchi admin qo'shish holati
    elif u_id == MAIN_ADMIN and u_id in ASK_STATE and ASK_STATE[u_id] == "waiting_assistant_id":
        if not text.isdigit():
            await update.message.reply_text("❌ Xato! Faqat raqamli ID kiriting:")
            return
        new_admin_id = int(text)
        ASSISTANT_ADMINS.add(new_admin_id)
        ASK_STATE[u_id] = "done"
        await update.message.reply_text(f"✅ ID `{new_admin_id}` muvaffaqiyatli Yordamchi Admin etib tayinlandi!")
        try: await context.bot.send_message(chat_id=new_admin_id, text="🎉 Siz Martin Mafia botida **Yordamchi Admin** etib tayinlandingiz! Admin panelni ochish uchun /start bosing.", parse_mode="Markdown")
        except Exception: pass

    # 3. Admin Panel orqali to'g'ridan-to'g'ri balans to'ldirish
    elif (u_id == MAIN_ADMIN or u_id in ASSISTANT_ADMINS) and u_id in ASK_STATE and ASK_STATE[u_id] == "waiting_give_data":
        try:
            target_id, amt = map(int, text.split())
            user_db = get_user(target_id, "O'yinchi", "")
            user_db["balance"] += amt
            ASK_STATE[u_id] = "done"
            await update.message.reply_text(f"✅ ID `{target_id}` ga {amt} ta olmos muvaffaqiyatli berildi.")
            try: await context.bot.send_message(chat_id=target_id, text=f"💰 Admin hisobingizga *+{amt} 💎* qo'shdi! Jami balansingiz: {user_db['balance']} 💎", parse_mode="Markdown")
            except Exception: pass
        except Exception:
            await update.message.reply_text("❌ Xato format! Namuna: `1234567 50` (ID va miqdor orasida joy tashlang):")

    # 4. Admin Panel orqali bloklash (Ban)
    elif (u_id == MAIN_ADMIN or u_id in ASSISTANT_ADMINS) and u_id in ASK_STATE and ASK_STATE[u_id] == "waiting_ban_id":
        if not text.isdigit():
            await update.message.reply_text("❌ ID faqat raqamlardan iborat bo'laxdi:")
            return
        ban_id = int(text)
        BANNED_USERS.add(ban_id)
        ASK_STATE[u_id] = "done"
        await update.message.reply_text(f"🚫 ID `{ban_id}` botdan butunlay bloklandi!")
        try: await context.bot.send_message(chat_id=ban_id, text="🚫 Siz Martin Mafia botidan admin tomonidan bloklandingiz!")
        except Exception: pass

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u_id = query.from_user.id
    if u_id in BANNED_USERS: return
    
    db = get_user(u_id, query.from_user.first_name, query.from_user.username)

    if query.data == "shop":
        text = (
            "🛍️ *Martin Mafia Do'koni:* Kerakli narsani tanlang:\n\n"
            "🕶 Mafiya (50 💎)\n"
            "🧰 Shifokor (30 💎)\n"
            "🕵️‍♂️ Komissar (40 💎)\n"
            "🛡 Zirh (Bronjilet) (70 💎)\n"
            "🔫 To'pponcha (100 💎) — *Yangi!*\n"
            "👁 Kuzatuvchi Kamerasi (60 💎) — *Yangi!*"
        )
        kb = [
            [InlineKeyboardButton("🕶 Mafiya", callback_data="b_mafia"), InlineKeyboardButton("🧰 Shifokor", callback_data="b_doc")],
            [InlineKeyboardButton("🕵️‍♂️ Komissar", callback_data="b_cop"), InlineKeyboardButton("🛡 Zirh", callback_data="b_arm")],
            [InlineKeyboardButton("🔫 To'pponcha", callback_data="b_pistol"), InlineKeyboardButton("👁 Kamera", callback_data="b_camera")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "home":
        if u_id in ASK_STATE: ASK_STATE.pop(u_id, None)
        bal = "Cheksiz ♾" if (u_id == MAIN_ADMIN or u_id in ASSISTANT_ADMINS) else f"{db['balance']} 💎"
        text = (
            f"🕵️‍♂️ *Martin Mafia*\n\n"
            f"👤 Ism: {query.from_user.first_name}\n"
            f"💳 Balans: {bal}\n"
            f"🎭 Rol: {db['role']}\n"
            f"🛡 Zirh: {'Mavjud ✅' if db['armor'] else 'Yoq ❌'}\n"
            f"🔫 To'pponcha: {'Mavjud ✅' if db.get('pistol') else 'Yoq ❌'}\n"
            f"👁 Kamera: {'Mavjud ✅' if db.get('camera') else 'Yoq ❌'}"
        )
        kb = [
            [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🛒 Do'kon", callback_data="shop"), InlineKeyboardButton("🏆 Reyting", callback_data="rank")],
            [InlineKeyboardButton("🙋‍♂️ Olmos so'rash", callback_data="ask")]
        ]
        if u_id == MAIN_ADMIN or u_id in ASSISTANT_ADMINS:
            kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "ask":
        text = "💰 *Qancha olmos so'ramoqchisiz?*\n\nTayyor miqdorlardan birini tanlang yoki o'zingiz yozing:"
        kb = [
            [InlineKeyboardButton("20 💎", callback_data="amt_20"), InlineKeyboardButton("30 💎", callback_data="amt_30"), InlineKeyboardButton("40 💎", callback_data="amt_40")],
            [InlineKeyboardButton("✍️ Boshqa miqdor", callback_data="amt_custom")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("amt_"):
        mode = query.data.split("_")[1]
        if mode == "custom":
            ASK_STATE[u_id] = "waiting_amount"
            await query.edit_message_text("✍️ *Siz xohlagan olmos miqdorini raqamda yozib yuboring:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bekor qilish", callback_data="ask")]]))
        else:
            amount = int(mode)
            await query.edit_message_text(f"⏳ {amount} ta olmos so'rovi adminlarga yuborildi. Tasdiqlanishini kuting...")
            await send_ask_to_admins(query.from_user, amount, context)

    # 👑 ADMIN PANEL INTERFEYSI
    elif query.data == "admin_panel":
        if u_id != MAIN_ADMIN and u_id not in ASSISTANT_ADMINS: return
        text = (
            f"👑 *Martin Mafia — Katta Adminlik Paneli*\n\n"
            f"📊 *Statistika:* Botda faol foydalanuvchilar soni: {len(USER_DATA)} ta\n"
            f"👥 *Yordamchi adminlar soni:* {len(ASSISTANT_ADMINS)} ta\n"
            f"🚫 *Bloklanganlar:* {len(BANNED_USERS)} ta\n\n"
            f"Bajarmoqchi bo'lgan amalingizni tanlang:"
        )
        kb = [
            [InlineKeyboardButton("💰 Olmos Berish", callback_data="adm_give"), InlineKeyboardButton("🚫 Foydalanuvchini Banlash", callback_data="adm_ban")]
        ]
        if u_id == MAIN_ADMIN:
            kb.append([InlineKeyboardButton("➕ Yordamchi Admin Qo'shish", callback_data="adm_add_assistant")])
        kb.append([InlineKeyboardButton("⬅️ Bosh sahifa", callback_data="home")])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "adm_add_assistant":
        if u_id != MAIN_ADMIN: return
        ASK_STATE[u_id] = "waiting_assistant_id"
        await query.edit_message_text("👤 *Yordamchi qilmoqchi bo'lgan odamingizning Telegram ID raqamini yozib yuboring:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_panel")]]))

    elif query.data == "adm_give":
        if u_id != MAIN_ADMIN and u_id not in ASSISTANT_ADMINS: return
        ASK_STATE[u_id] = "waiting_give_data"
        await query.edit_message_text("💰 *Olmos bermoqchi bo'lgan odam ID si va miqdorini yozing:*\n\nNamuna: `5432167 150`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_panel")]]))

    elif query.data == "adm_ban":
        if u_id != MAIN_ADMIN and u_id not in ASSISTANT_ADMINS: return
        ASK_STATE[u_id] = "waiting_ban_id"
        await query.edit_message_text("🚫 *Botdan butunlay bloklamoqchi (ban qilmoqchi) bo'lgan shaxsning ID raqamini yozing:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_panel")]]))

    # ADMIN OLMOSTNI TASDIQLASA
    elif query.data.startswith("approve_"):
        if u_id != MAIN_ADMIN and u_id not in ASSISTANT_ADMINS: return
        data = query.data.split("_")
        target_id, amount = int(data[1]), int(data[2])
        user_db = get_user(target_id, "O'yinchi", "")
        user_db["balance"] += amount
        await query.edit_message_text(f"✅ ID `{target_id}` ning {amount} ta olmos so'rovi tasdiqlandi.")
        try: await context.bot.send_message(chat_id=target_id, text=f"🎉 *Xushxabar!*\n\nAdmin so'rovingizni tasdiqladi va hisobingizga *+{amount} 💎* qo'shdi!", parse_mode="Markdown")
        except Exception: pass

    elif query.data.startswith("reject_"):
        if u_id != MAIN_ADMIN and u_id not in ASSISTANT_ADMINS: return
        target_id = int(query.data.split("_")[1])
        await query.edit_message_text(f"❌ ID `{target_id}` ning so'rovi rad etildi.")
        try: await context.bot.send_message(chat_id=target_id, text="❌ Afsuski, admin olmos so'rovingizni rad etdi.", parse_mode="Markdown")
        except Exception: pass

    # XARID TIZIMI
    elif query.data.startswith("b_"):
        item = query.data.split("_")[1]
        prices = {"mafia": 50, "doc": 30, "cop": 40, "arm": 70, "pistol": 100, "camera": 60}
        if db["balance"] < prices[item] and u_id != MAIN_ADMIN and u_id not in ASSISTANT_ADMINS:
            await query.edit_message_text("❌ Olmosingiz yetarli emas!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="shop")]]))
            return
        if u_id != MAIN_ADMIN and u_id not in ASSISTANT_ADMINS: db["balance"] -= prices[item]
        
        if item == "arm": db["armor"] = True
        elif item == "pistol": db["pistol"] = True
        elif item == "camera": db["camera"] = True
        else: db["role"] = "Mafiya 🕶" if item=="mafia" else "Shifokor 🧰" if item=="doc" else "Komissar 🕵️‍♂️"
        
        await query.edit_message_text("🎉 Xarid muvaffaqiyatli yakunlandi!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]]))

    elif query.data == "rank":
        users = sorted(USER_DATA.items(), key=lambda x: x[1]["wins"], reverse=True)[:5]
        text = "🏆 *Top O'yinchilar:*\n\n" + "\n".join([f"👤 *{u[1]['name']}* — {u[1]['wins']} g'alaba" for u in users]) if users else "🏆 Hozircha g'oliblar yo'q."
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="home")]]))

    elif query.data.startswith("j_"):
        g_id = int(query.data.split("_")[1])
        if g_id in GAMES and GAMES[g_id]["status"] == "join":
            if u_id not in GAMES[g_id]["players"] and len(GAMES[g_id]["players"]) < 10:
                GAMES[g_id]["players"][u_id] = {"name": query.from_user.first_name, "role": None, "alive": True}
                await context.bot.send_message(chat_id=g_id, text=f"✅ *{query.from_user.first_name}* o'yinga qo'shildi!")

    elif query.data.startswith("admin_start_"):
        g_id = int(query.data.split("_")[2])
        if u_id != MAIN_ADMIN and u_id not in ASSISTANT_ADMINS: return
        if g_id in GAMES and GAMES[g_id]["status"] == "join":
            if len(GAMES[g_id]["players"]) < 4:
                await context.bot.send_message(chat_id=g_id, text="⚠️ O'yinni boshlash uchun kamida 4 ta odam qo'shilishi kerak!")
                return
            GAMES[g_id]["status"] = "playing"
            await start_game_logic(g_id, context)

    elif query.data.startswith("admin_stop_"):
        g_id = int(query.data.split("_")[2])
        if u_id != MAIN_ADMIN and u_id not in ASSISTANT_ADMINS: return
        if g_id in GAMES and GAMES[g_id]["status"] != "ended":
            GAMES[g_id]["status"] = "ended"
            await context.bot.send_message(chat_id=g_id, text="🛑 O'yin admin tomonidan majburiy to'xtatildi!")

async def game_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g_id = update.effective_chat.id
    if update.effective_chat.type not in ["group", "supergroup"]: return
    if update.effective_user.id in BANNED_USERS: return
    
    get_user(update.effective_user.id, update.effective_user.first_name, update.effective_user.username)
    GAMES[g_id] = {"status": "join", "players": {}}
    kb = [
        [InlineKeyboardButton("➕ O'yinga qo'shilish", callback_data=f"j_{g_id}")],
        [InlineKeyboardButton("▶️ O'yinni boshlash (Admin)", callback_data=f"admin_start_{g_id}")],
        [InlineKeyboardButton("🛑 O'yinni to'xtatish (Admin)", callback_data=f"admin_stop_{g_id}")]
    ]
    await update.message.reply_text("🎬 *Martin Mafia o'yini boshlandi!*\n\n🔔 Ro'yxatdan o'tish vaqti: *140 soniya*.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    
    await asyncio.sleep(140)
    if g_id in GAMES and GAMES[g_id]["status"] == "join":
        if len(GAMES[g_id]["players"]) < 4:
            await context.bot.send_message(chat_id=g_id, text="❌ O'yinchilar yetarli bo'lmadi. O'yin bekor qilindi.")
            GAMES[g_id]["status"] = "ended"
            return
        GAMES[g_id]["status"] = "playing"
        await start_game_logic(g_id, context)

async def start_game_logic(g_id, context):
    p_ids = list(GAMES[g_id]["players"].keys())
    random.shuffle(p_ids)
    GAMES[g_id]["players"][p_ids[0]]["role"] = "Mafiya 🕶"
    GAMES[g_id]["players"][p_ids[1]]["role"] = "Shifokor 🧰"
    GAMES[g_id]["players"][p_ids[2]]["role"] = "Komissar 🕵️‍♂️"
    for i in range(3, len(p_ids)): GAMES[g_id]["players"][p_ids[i]]["role"] = "Tinch aholi 🕊"

    for pid, pdata in GAMES[g_id]["players"].items():
        try: await context.bot.send_message(chat_id=pid, text=f"🎭 Sizning rolingiz: *{pdata['role']}*", parse_mode="Markdown")
        except Exception: pass
    await context.bot.send_message(chat_id=g_id, text="🎭 Rollar shaxsiy xabarlarga yuborildi!\n\n🌌 *Tun boshlanmoqda...*")

def main():
    Thread(target=run_server).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("game", game_cmd))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
