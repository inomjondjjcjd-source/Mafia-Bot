import os, sys, subprocess, json, random, asyncio
from flask import Flask
from threading import Thread

# Kerakli kutubxonalarni tekshirish va avto-o'rnatish
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8303235336:AAEk3J42idbz1KcamIWPC2L3_IlROPeoadI"
ADMIN_ID = 8086545587  # Faqat shu ID uchun cheat va boshqaruv ishlaydi!
DATA_FILE = "mega_games_bot_db.json"

DB = {
    "users": {},
    "settings": {"next_aviator": None},
}

# 🍏 APPLE OF FORTUNE: HAQIQIY 13 QATORLI TIZIM
APPLE_COEFFS = [1.23, 1.54, 1.93, 2.41, 3.02, 4.02, 5.70, 8.55, 13.43, 20.15, 30.22, 45.33, 69.48]

def load_db():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f: 
                DB = json.load(f)
                # Kalitlarni butun songa (int) aylantiramiz, aks holda tekshirishda xato bo'ladi
                DB["users"] = {int(k): v for k, v in DB.get("users", {}).items()}
        except: pass

def save_db():
    try:
        to_save = DB.copy()
        # JSON format string kalitlarni talab qilgani uchun IDlarni string qilamiz
        to_save["users"] = {str(k): v for k, v in DB["users"].items()}
        with open(DATA_FILE, "w", encoding="utf-8") as f: 
            json.dump(to_save, f, indent=4, ensure_ascii=False)
    except: pass

def check_user(uid, name="Foydalanuvchi"):
    load_db()  # Har doim oxirgi ma'lumotlarni bazadan o'qiymiz
    if uid not in DB["users"]:
        # Agar foydalanuvchi bazada yo'q bo'lsa (yangi bo'lsa), unga boshlang'ich pul beramiz
        DB["users"][uid] = {
            "name": name, "balance": 10000, "tickets": 5,
            "apple_game": None, "aviator_game": None
        }
        save_db()
    # 🌟 AGAR FOYDALANUVCHI BAZADA ALLAQACHON BO'LSA, UNING ESKI PULLARI VA CHIPTALARI O'ZGARISXSIZ QOLADI!
    return DB["users"][uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ud = check_user(uid, update.effective_user.first_name)
    txt = f"👑 *SHOX SUPREME PLATFORMA v3.0*\n\n💵 *Balans:* {ud['balance']} so'm\n🎫 *Chiptalar:* {ud['tickets']} ta\n\n_Qayta start bosilganda pullaringiz xavfsiz saqlanadi! ✅_"
    kb = [
        [InlineKeyboardButton("🍏 Apple of Fortune (13 Rowa)", callback_data="g_apple")],
        [InlineKeyboardButton("✈️ Aviator (Real time)", callback_data="g_aviator")],
        [InlineKeyboardButton("🎫 1 ta Chipta (4k)", callback_data="b_ticket_1"), InlineKeyboardButton("🎁 10 ta Chipta (30k)", callback_data="b_ticket_10")],
        [InlineKeyboardButton("👑 Admin Panel", callback_data="admin_dashboard")] if uid == ADMIN_ID else []
    ]
    kb = [x for x in kb if x]
    if update.message: 
        await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    else: 
        await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); uid = q.from_user.id; ud = check_user(uid)
    
    # Cheat Tizimi: Faqat siz adminga (ADMIN_ID) ochiq ko'rinadi!
    is_admin_cheat = (uid == ADMIN_ID)
    
    if q.data == "to_main": 
        await start(update, context)
    
    # CHIPTALAR XARIDI
    elif q.data == "b_ticket_1":
        if ud["balance"] < 4000: await q.edit_message_text("❌ Pul yetarli emas uka!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])); return
        ud["balance"] -= 4000; ud["tickets"] += 1; save_db(); await start(update, context)
    elif q.data == "b_ticket_10":
        if ud["balance"] < 30000: await q.edit_message_text("❌ Pul yetarli emas uka!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])); return
        ud["balance"] -= 30000; ud["tickets"] += 10; save_db(); await start(update, context)
    
    # 🍏 APPLE OF FORTUNE (13 BOSQICH)
    elif q.data == "g_apple":
        if not ud["apple_game"]:
            if ud["balance"] < 3000: await q.edit_message_text("❌ Olma o'ynash uchun kamida 3000 so'm kerak!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])); return
            ud["balance"] -= 3000; fg = []
            for r in range(13):
                items = ["good"] * 5
                bad_count = 1 if r < 4 else 2 if r < 8 else 3 if r < 11 else 4
                for bi in random.sample(range(5), bad_count): items[bi] = "bad"
                fg.append(items)
            ud["apple_game"] = {"grid": fg, "current_row": 0, "bet": 3000, "payout": 3000}
            save_db()
        await show_apple(q, ud, is_admin_cheat)
        
    elif q.data.startswith("ap_select_"):
        idx = int(q.data.split("_")[2]); ag = ud["apple_game"]
        if not ag or ag["grid"][ag["current_row"]][idx] == "bad":
            ud["apple_game"] = None; save_db()
            await q.edit_message_text("💀 *Chirigan olma! Garov tikilgan pul kuydi.*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🍏 Qayta urinish (3k)", callback_data="g_apple")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]])); return
        ag["payout"] = int(ag["bet"] * APPLE_COEFFS[ag["current_row"]]); ag["current_row"] += 1; save_db()
        if ag["current_row"] == 13:
            ud["balance"] += ag["payout"]; ud["apple_game"] = None; save_db()
            await q.edit_message_text(f"👑 *JACKPOT x69.48!* \n💰 +{ag['payout']} so'm hisobingizga qo'shildi uka!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]])); return
        await show_apple(q, ud, is_admin_cheat)
        
    elif q.data == "ap_cashout" and ud["apple_game"] and ud["apple_game"]["current_row"] > 0:
        w = ud["apple_game"]["payout"]; ud["balance"] += w; ud["apple_game"] = None; save_db()
        await q.edit_message_text(f"💰 *Yutuq olindi!* \nHisobingizga +{w} so'm qo'shildi!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🍏 Yana o'ynash (3k)", callback_data="g_apple")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))

    # ✈️ AVIATOR (REAL-TIME STEP)
    elif q.data == "g_aviator":
        if ud["balance"] < 2000: await q.edit_message_text("❌ Aviator uchun kamida 2k kerak uka!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])); return
        ud["balance"] -= 2000; save_db()
        
        if DB["settings"].get("next_aviator") is not None:
            crash_point = DB["settings"]["next_aviator"]
            DB["settings"]["next_aviator"] = None  
        else:
            crash_point = round(random.uniform(1.3, 8.0), 2)
            
        ud["aviator_game"] = {"current_win": 1.0, "crash": crash_point, "bet": 2000}; save_db()
        await update_aviator_frame(q, ud, is_admin_cheat)
        
    elif q.data == "av_step":
        ag = ud["aviator_game"]
        if not ag: return
        ag["current_win"] = round(ag["current_win"] + random.uniform(0.15, 0.35), 2)
        
        if ag["current_win"] >= ag["crash"]:
            c_p = ag["crash"]
            ud["aviator_game"] = None; save_db()
            await q.edit_message_text(f"💥 *BOOM! Samolyot x{c_p} nuqtada portlab ketdi uka!*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✈️ Qayta urinish (2k)", callback_data="g_aviator")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]])); return
            
        save_db()
        await update_aviator_frame(q, ud, is_admin_cheat)
        
    elif q.data == "av_cashout" and ud["aviator_game"]:
        ag = ud["aviator_game"]
        win_money = int(ag["bet"] * ag["current_win"])
        ud["balance"] += win_money; ud["aviator_game"] = None; save_db()
        await q.edit_message_text(f"💰 *Muvaffaqiyatli CASHOUT!* \n📈 Yakuniy koeffitsiyent: x{ag['current_win']} \n💰 +{win_money} so'm qo'shildi!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✈️ Yana o'ynash (2k)", callback_data="g_aviator")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))

    # 👑 ADMIN PANEL
    elif q.data == "admin_dashboard" and uid == ADMIN_ID:
        next_av = DB["settings"].get("next_aviator") or "Avtomat (Random)"
        txt = f"👑 *FAQAT SIZ UCHUN CHEAT PANEL*\n\n🔥 *Siz uchun cheat status:* `FAOL ✅`\n✈ *Keyingi Aviator:* x{next_av}\n\n*Boshqaruv buyruqlari:*\n/setav KOEFF - Aviator koeffitsiyentini qotirish\n/plus ID PUL - Istalgan odamga balans qo'shish"
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main")]]))

async def update_aviator_frame(q, ud, is_admin_cheat):
    ag = ud["aviator_game"]
    cheat_hint = f" *(Maxfiy Portlash: x{ag['crash']})*" if is_admin_cheat else ""
    txt = f"✈️ *AVIATOR PLATFORMA*\n\n🚀 Samolyot havoda...{cheat_hint}\n📈 Joriy Koeffitsiyent: *x{ag['current_win']}*\n\n💵 Tikilgan pul: {ag['bet']} so'm\n💰 Hozirgi yutuq: {int(ag['bet'] * ag['current_win'])} so'm"
    kb = [
        [InlineKeyboardButton(f"🛑 CASHOUT ({int(ag['bet'] * ag['current_win'])} so'm)", callback_data="av_cashout")],
        [InlineKeyboardButton("🚀 Yanada balandroq kutish (Tavakkal)", callback_data="av_step")]
    ]
    await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def show_apple(q, ud, is_admin_cheat):
    ag = ud["apple_game"]
    crow = ag["current_row"]
    kb = []
    
    for ri in range(12, -1, -1):
        if ri < crow:
            kb.append([InlineKeyboardButton("🍏", callback_data="lock") for ci in range(5)])
        elif ri == crow:
            row_buttons = []
            for ci in range(5):
                if is_admin_cheat and ag["grid"][ri][ci] == "good": lbl = "🔥 🍏"
                else: lbl = "🟫"
                row_buttons.append(InlineKeyboardButton(lbl, callback_data=f"ap_select_{ci}"))
            kb.append(row_buttons)
        else:
            lbl = "🔒 👑" if ri == 12 else "🔒"
            kb.append([InlineKeyboardButton(lbl, callback_data="lock") for ci in range(5)])
            
    if crow > 0: 
        kb.append([InlineKeyboardButton(f"💰 Take Apple Fortune ({ag['payout']} so'm)", callback_data="ap_cashout")])
        
    kb.append([InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main")])
    await q.edit_message_text(f"🍏 *APPLE OF FORTUNE* (13 Bosqich)\nEtap: {crow+1}/13\n📈 Keyingi koeff: x{APPLE_COEFFS[crow] if crow < 13 else 69.48}\n💵 Yutuq: {ag['payout']} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# ADMIN BUYRUQLARI
async def admin_setaviator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        val = float(context.args[0])
        DB["settings"]["next_aviator"] = val; save_db()
        await update.message.reply_text(f"✅ Tayyor uka! Keyingi Aviator parvozi aniq *x{val}* da portlaydi!", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Xato! Buyruq: `/setav 3.5`", parse_mode="Markdown")

async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t, v = int(context.args[0]), int(context.args[1]); load_db()
        if t in DB["users"]: 
            DB["users"][t]["balance"] += v; save_db()
            await update.message.reply_text("✅ Foydalanuvchi balansi to'ldirildi!", parse_mode="Markdown")
    except: pass

# --- RENDER WEB ENGINE ---
app = Flask(__name__)
@app.route('/')
def home(): return "Online"

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
    
    async with bot_app:
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling(drop_pending_updates=True)
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running(): loop.create_task(main_bot())
        else: loop.run_until_complete(main_bot())
    except RuntimeError:
        asyncio.run(main_bot())
        
