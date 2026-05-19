import os, sys, subprocess, json, random, asyncio
from flask import Flask
from threading import Thread

try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8303235336:AAHkjNihtbYY5QeSm9H2P2DBHyFgg6Fyd_s"
ADMIN_ID = 8086545587  
DATA_FILE = "mega_games_bot_db.json"

DB = {
    "users": {},
    "settings": {
        "next_aviator": None,
        "aviator_history": [2.34, 1.55, 4.12, 1.22, 3.05]
    },
}

APPLE_COEFFS = [1.23, 1.54, 1.93, 2.41, 3.02, 4.02, 5.70, 8.55, 13.43, 20.15, 30.22, 45.33, 69.48]

def load_db():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f: 
                DB = json.load(f)
                DB["users"] = {int(k): v for k, v in DB.get("users", {}).items()}
                if "aviator_history" not in DB["settings"]:
                    DB["settings"]["aviator_history"] = [2.34, 1.55, 4.12, 1.22, 3.05]
        except: pass

def save_db():
    try:
        to_save = DB.copy()
        to_save["users"] = {str(k): v for k, v in DB["users"].items()}
        with open(DATA_FILE, "w", encoding="utf-8") as f: 
            json.dump(to_save, f, indent=4, ensure_ascii=False)
    except: pass

def check_user(uid, name="Foydalanuvchi"):
    load_db()
    if uid not in DB["users"]:
        DB["users"][uid] = {
            "name": name, "balance": 10000, "tickets": 5,
            "apple_game": None, "aviator_game": None, "state": None
        }
        save_db()
    if "apple_game" not in DB["users"][uid]: DB["users"][uid]["apple_game"] = None
    if "aviator_game" not in DB["users"][uid]: DB["users"][uid]["aviator_game"] = None
    if "state" not in DB["users"][uid]: DB["users"][uid]["state"] = None
    return DB["users"][uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ud = check_user(uid, update.effective_user.first_name)
    ud["state"] = None 
    save_db()
    
    txt = (
        f"👑 *SHOX SUPREME PLATFORMA v6.5*\n\n"
        f"💵 *Balans:* {ud['balance']} so'm\n"
        f"🎫 *Chiptalar:* {ud['tickets']} ta\n\n"
        f"⚠️ _Maksimal garov qiymati: 10 000 so'm qilib belgilandi!_"
    )
    
    kb = [
        [InlineKeyboardButton("🍏 Apple of Fortune", callback_data="prep_apple"), 
         InlineKeyboardButton("✈️ Aviator (Real-Time)", callback_data="prep_aviator")],
        [InlineKeyboardButton("💸 Pul Kiritish (Deposit)", url=f"tg://user?id={ADMIN_ID}"),
         InlineKeyboardButton("💳 Pul Yechish (Cashout)", url=f"tg://user?id={ADMIN_ID}")],
        [InlineKeyboardButton("🎫 1 ta Chipta (4k)", callback_data="b_ticket_1"), 
         InlineKeyboardButton("🎁 10 ta Chipta (30k)", callback_data="b_ticket_10")],
        [InlineKeyboardButton("👑 Admin Panel", callback_data="admin_dashboard")] if uid == ADMIN_ID else []
    ]
    
    if update.message: 
        await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    else: 
        await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); uid = q.from_user.id; ud = check_user(uid)
    is_admin_cheat = (uid == ADMIN_ID)
    
    if q.data == "to_main": 
        await start(update, context)
        
    elif q.data == "b_ticket_1":
        if ud["balance"] < 4000: await q.edit_message_text("❌ Pul yetarli emas!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])); return
        ud["balance"] -= 4000; ud["tickets"] += 1; save_db(); await start(update, context)
        
    elif q.data == "b_ticket_10":
        if ud["balance"] < 30000: await q.edit_message_text("❌ Pul yetarli emas!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])); return
        ud["balance"] -= 30000; ud["tickets"] += 10; save_db(); await start(update, context)

    # 🍏 APPLE PREPARE (TUGMALAR BILAN)
    elif q.data == "prep_apple":
        ud["state"] = "input_apple_bet"
        save_db()
        kb = [
            [InlineKeyboardButton("💵 2 000 so'm", callback_data="quick_apple_2000"),
             InlineKeyboardButton("💵 5 000 so'm", callback_data="quick_apple_5000"),
             InlineKeyboardButton("💵 10 000 so'm", callback_data="quick_apple_10000")],
            [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]
        ]
        await q.edit_message_text(
            f"🍏 *APPLE OF FORTUNE*\n\nSizning balansingiz: *{ud['balance']}* so'm\n"
            f"Tikmoqchi bo'lgan summani pastdagi tugmalardan tanlang yoki o'zingiz yozib yuboring (Masalan: `3500`):\n\n"
            f"⚠️ _Eslatma: Minimal 1000 so'm, maksimal 10 000 so'm!_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # TAYYOR TUGMA BOSILGANDA APPLE BOSHLASH
    elif q.data.startswith("quick_apple_"):
        bet_amount = int(q.data.split("_")[2])
        if ud["balance"] < bet_amount:
            await q.edit_message_text("❌ Balansingizda mablag' yetarli emas!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="prep_apple")]]))
            return
        await start_apple_game(q.message, ud, bet_amount, uid)

    # ✈️ AVIATOR PREPARE (TUGMALAR BILAN)
    elif q.data == "prep_aviator":
        ud["state"] = "input_aviator_bet"
        save_db()
        
        history_list = DB["settings"].get("aviator_history", [2.34, 1.55, 4.12, 1.22, 3.05])
        history_str = " ".join([f"`[x{h}]`" for h in history_list[-5:]])
        
        kb = [
            [InlineKeyboardButton("💵 2 000 so'm", callback_data="quick_aviator_2000"),
             InlineKeyboardButton("💵 5 000 so'm", callback_data="quick_aviator_5000"),
             InlineKeyboardButton("💵 10 000 so'm", callback_data="quick_aviator_10000")],
            [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]
        ]
        await q.edit_message_text(
            f"✈️ *AVIATOR REAL-TIME*\n\n"
            f"📋 *Oxirgi parvozlar koeffitsiyentlari:*\n{history_str}\n\n"
            f"Sizning balansingiz: *{ud['balance']}* so'm\n"
            f"Tikmoqchi bo'lgan summani tugmalardan tanlang yoki o'zingiz matn qilib yozing:\n\n"
            f"⚠️ _Eslatma: Minimal 1000 so'm, maksimal 10 000 so'm!_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # TAYYOR TUGMA BOSILGANDA AVIATOR BOSHLASH
    elif q.data.startswith("quick_aviator_"):
        bet_amount = int(q.data.split("_")[2])
        if ud["balance"] < bet_amount:
            await q.edit_message_text("❌ Balansingizda mablag' yetarli emas!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="prep_aviator")]]))
            return
        await start_aviator_game(q.message, ud, bet_amount, context, uid)
        
    elif q.data.startswith("ap_select_"):
        idx = int(q.data.split("_")[2]); ag = ud.get("apple_game")
        if not ag: return
        
        status = ag["grid"][ag["current_row"]][idx]
        if status == "bad":
            ud["apple_game"] = None; save_db()
            await q.edit_message_text("💀 *Chirigan olma chiqdi! Tikilgan pulingiz kuydi uka.*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🍏 Qayta o'ynash", callback_data="prep_apple")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]])); return
        
        ag["payout"] = int(ag["bet"] * APPLE_COEFFS[ag["current_row"]])
        ag["current_row"] += 1; save_db()
        
        if ag["current_row"] == 13:
            ud["balance"] += ag["payout"]; ud["apple_game"] = None; save_db()
            await q.edit_message_text(f"👑 *JACKPOT x69.48!* \n💰 Hisobingizga +{ag['payout']} so'm qo'shildi uka!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]])); return
            
        await show_apple(q, ud, is_admin_cheat)
        
    elif q.data == "ap_cashout" and ud.get("apple_game") and ud["apple_game"]["current_row"] > 0:
        w = ud["apple_game"]["payout"]; ud["balance"] += w; ud["apple_game"] = None; save_db()
        await start(update, context)

    elif q.data == "av_realtime_cashout":
        ag = ud.get("aviator_game")
        if not ag or ag["status"] != "flying": return
        
        ag["status"] = "cashout_done"
        win_money = int(ag["bet"] * ag["current_win"])
        ud["balance"] += win_money
        ud["aviator_game"] = None
        save_db()
        
        await q.edit_message_text(
            f"💰 *Muvaffaqiyatli CASHOUT!*\n📈 Parvozni to'xtatgan koeffitsiyentingiz: *x{ag['current_win']}*\n💰 Balansingizga +{win_money} so'm qo'shildi uka!", 
            parse_mode="Markdown", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✈️ Qayta uchish", callback_data="prep_aviator")], [InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="to_main")]])
        )

    # 👑 ADMIN PANEL
    elif q.data == "admin_dashboard" and uid == ADMIN_ID:
        next_av = DB["settings"].get("next_aviator") or "Avtomat (Random)"
        txt = f"👑 *FAQAT SIZ UCHUN CHEAT PANEL*\n\n🔥 *Siz uchun cheat status:* `FAOL ✅`\n✈ *Keyingi Aviator:* x{next_av}\n\n*Boshqaruv buyruqlari:*\n/setav KOEFF - Aviator koeffitsiyentini qotirish\n/plus ID PUL - Istalgan odamga balans qo'shish"
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main")]]))

# YORDAMCHI FUNKSIYALAR (O'YINLARNI BOSHLASH)
async def start_apple_game(message_obj, ud, bet_amount, uid):
    ud["balance"] -= bet_amount
    fg = []
    for r in range(13):
        items = ["good"] * 5
        bad_count = 1 if r < 4 else 2 if r < 8 else 3 if r < 11 else 4
        for bi in random.sample(range(5), bad_count): items[bi] = "bad"
        fg.append(items)
        
    ud["apple_game"] = {"grid": fg, "current_row": 0, "bet": bet_amount, "payout": bet_amount}
    ud["state"] = None
    save_db()
    
    class FakeQuery:
        def __init__(self, msg): self.message = msg
        async def edit_message_text(self, t, parse_mode, reply_markup):
            await self.message.edit_text(t, parse_mode=parse_mode, reply_markup=reply_markup)
            
    await show_apple(FakeQuery(message_obj), ud, (uid == ADMIN_ID))

async def start_aviator_game(message_obj, ud, bet_amount, context, uid):
    ud["balance"] -= bet_amount
    if DB["settings"].get("next_aviator") is not None:
        crash_point = DB["settings"]["next_aviator"]
        DB["settings"]["next_aviator"] = None  
    else:
        crash_point = round(random.uniform(1.2, 7.5), 2)
        
    ud["aviator_game"] = {"current_win": 1.0, "crash": crash_point, "bet": bet_amount, "status": "flying"}
    ud["state"] = None
    save_db()
    
    asyncio.create_task(run_realtime_aviator(context.application, message_obj.chat_id, message_obj.message_id, uid, uid == ADMIN_ID))

# TEXT HANDLER - INPUT ORQALI SUMMA YOZILSA
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ud = check_user(uid, update.effective_user.first_name)
    if not ud["state"]: return
    
    text = update.message.text.strip()
    try:
        bet_amount = int(text)
    except ValueError:
        await update.message.reply_text("❌ Iltimos faqat raqam kiriting uka!")
        return
        
    if bet_amount < 1000 or bet_amount > 10000:
        await update.message.reply_text("❌ Garov summasi kamida 1000 so'm va ko'pi bilan 10 000 so'm bo'lishi shart!")
        return
        
    if ud["balance"] < bet_amount:
        await update.message.reply_text(f"❌ Balansingizda pul kam! Sizda: {ud['balance']} so'm bor.")
        return

    msg = await update.message.reply_text("🔄 O'yin tayyorlanmoqda...")
    if ud["state"] == "input_apple_bet":
        await start_apple_game(msg, ud, bet_amount, uid)
    elif ud["state"] == "input_aviator_bet":
        await start_aviator_game(msg, ud, bet_amount, context, uid)

# 🔄 REAL-TIME AVIATOR SIKLI
async def run_realtime_aviator(app_obj, chat_id, message_id, uid, is_admin_cheat):
    while True:
        await asyncio.sleep(1.0)
        load_db()
        ud = DB["users"].get(uid)
        if not ud: break
        
        ag = ud.get("aviator_game")
        if not ag or ag.get("status") != "flying": break
        
        ag["current_win"] = round(ag["current_win"] + random.uniform(0.15, 0.35), 2)
        
        if ag["current_win"] >= ag["crash"]:
            c_p = ag["crash"]
            ag["status"] = "crashed"
            ud["aviator_game"] = None
            
            if "aviator_history" not in DB["settings"]: DB["settings"]["aviator_history"] = []
            DB["settings"]["aviator_history"].append(c_p)
            save_db()
            
            try:
                await app_obj.bot.edit_message_text(
                    chat_id=chat_id, message_id=message_id,
                    text=f"💥 *BOOM! Samolyot x{c_p} nuqtada portladi uka!*\nGarov tikilgan {ag['bet']} so'm pul kuydi.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✈️ Qayta urinish", callback_data="prep_aviator")], [InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="to_main")]])
                )
            except: pass
            break
            
        save_db()
        cheat_hint = f" *(Portlash: x{ag['crash']})*" if is_admin_cheat else ""
        current_payout = int(ag["bet"] * ag["current_win"])
        
        history_list = DB["settings"].get("aviator_history", [2.34, 1.55, 4.12, 1.22, 3.05])
        history_str = " ".join([f"`[x{h}]`" for h in history_list[-5:]])
        
        txt = (
            f"✈️ *AVIATOR REAL-TIME PLATFORMA*\n\n"
            f"📋 Tarix: {history_str}\n\n"
            f"🚀 Samolyot havoda ko'tarilmoqda...{cheat_hint}\n"
            f"📈 Joriy Koeffitsiyent: *x{ag['current_win']}* 🔥\n\n"
            f"💵 Tikilgan pul: {ag['bet']} so'm\n"
            f"💰 Hozirgi yutuq qiymati: {current_payout} so'm"
        )
        kb = [[InlineKeyboardButton(f"🛑 CASHOUT ({current_payout} so'm)", callback_data="av_realtime_cashout")]]
        
        try:
            await app_obj.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        except: pass

# 🍏 APPLE OF FORTUNE MATRITSA VA KOEFFITSIYENTLAR PANELI
async def show_apple(q, ud, is_admin_cheat):
    ag = ud["apple_game"]
    crow = ag["current_row"]
    kb = []
    
    # Qatorlarni teskari tartibda (12 dan 0 gacha) aylantiramiz, shunda yuqori qator tepada ko'rinadi
    for ri in range(12, -1, -1):
        row_buttons = []
        # Qator koeffitsiyenti tugmasini chap tomonga qo'shish
        kf_label = f"x{APPLE_COEFFS[ri]}"
        row_buttons.append(InlineKeyboardButton(kf_label, callback_data="lock_kf"))
        
        if ri < crow:
            # O'tilgan qatorlar - ochiq olmalar
            for ci in range(5): row_buttons.append(InlineKeyboardButton("🍏", callback_data="lock"))
        elif ri == crow:
            # Hozirgi faol qator - bosish mumkin bo'lgan tugmalar
            for ci in range(5):
                lbl = "🍏" if (is_admin_cheat and ag["grid"][ri][ci] == "good") else "🍎" if (is_admin_cheat and ag["grid"][ri][ci] == "bad") else "🟫"
                row_buttons.append(InlineKeyboardButton(lbl, callback_data=f"ap_select_{ci}"))
        else:
            # Qulflangan yuqori qatorlar
            lbl = "🔒 👑" if ri == 12 else "🔒"
            for ci in range(5): row_buttons.append(InlineKeyboardButton(lbl, callback_data="lock"))
            
        kb.append(row_buttons)
            
    if crow > 0: 
        kb.append([InlineKeyboardButton(f"💰 Olmalarni olish ({ag['payout']} so'm)", callback_data="ap_cashout")])
    kb.append([InlineKeyboardButton("⬅️ Chiqish o'yinidan", callback_data="to_main")])
    
    current_kf = APPLE_COEFFS[crow-1] if crow > 0 else 1.0
    next_kf = APPLE_COEFFS[crow] if crow < 13 else APPLE_COEFFS[-1]
    
    txt = (
        f"🍏 *APPLE OF FORTUNE*\n\n"
        f"📈 *Siz turgan koeffitsiyent:* `x{current_kf}`\n"
        f"🚀 *Keyingi bosqich koeffitsiyenti:* `x{next_kf}`\n\n"
        f"💵 Tikilgan pul: *{ag['bet']}* so'm\n"
        f"💰 *Joriy yutuq qiymati:* *{ag['payout']}* so'm\n"
        f"Etap: {crow}/13"
    )
    await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# ADMIN BUYRUQLARI
async def admin_setaviator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        val = float(context.args[0])
        DB["settings"]["next_aviator"] = val; save_db()
        await update.message.reply_text(f"✅ Tayyor uka! Keyingi Aviator parvozi aniq *x{val}* da portlaydi!", parse_mode="Markdown")
    except: pass

async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t, v = int(context.args[0]), int(context.args[1]); load_db()
        if t in DB["users"]: 
            DB["users"][t]["balance"] += v; save_db()
            await update.message.reply_text("✅ Foydalanuvchi balansi to'ldirildi!", parse_mode="Markdown")
    except: pass

# --- ENGINE WEB RENDER SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Engine Active"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

async def main_bot():
    load_db()
    Thread(target=run_flask, daemon=True).start()
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("setav", admin_setaviator))
    bot_app.add_handler(CommandHandler("plus", admin_plus))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    async with bot_app:
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running(): loop.create_task(main_bot())
        else: loop.run_until_complete(main_bot())
    except RuntimeError: asyncio.run(main_bot())
               
