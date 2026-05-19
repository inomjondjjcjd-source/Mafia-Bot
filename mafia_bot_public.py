import os
import sys
import json
import random
import asyncio
from flask import Flask
from threading import Thread

# Kutubxonalarni xavfsiz tekshirish va o'rnatish
try:
    import nest_asyncio
    import httpx
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "flask==3.0.2", "nest_asyncio==1.6.0", "httpx==0.27.0"])
    import nest_asyncio
    import httpx
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Event loop va render muammosini tuzatish
nest_asyncio.apply()

# --- SOZLAMALAR ---
TOKEN = "8303235336:AAHkjNihtbYY5QeSm9H2P2DBHyFgg6Fyd_s"
ADMIN_ID = 8086545587  
VIP_USERS = [8086545587]

DATA_FILE = "mega_games_bot_db.json"
DB = {"users": {}, "settings": {"next_aviator": None, "aviator_history": [2.34, 1.55, 4.12, 1.22, 3.05], "promos": {}}}
APPLE_COEFFS = [1.23, 1.54, 1.93, 2.41, 3.02, 4.02, 5.70, 8.55, 13.43, 20.15, 30.22, 45.33, 69.48]

def load_db():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                DB["users"] = {int(k): v for k, v in d.get("users", {}).items()}
                DB["settings"] = d.get("settings", {})
                if "promos" not in DB["settings"]: DB["settings"]["promos"] = {}
                if "aviator_history" not in DB["settings"]: DB["settings"]["aviator_history"] = [2.34, 1.55, 4.12, 1.22, 3.05]
        except: pass

def save_db():
    try:
        to_save = {"users": {str(k): v for k, v in DB["users"].items()}, "settings": DB["settings"]}
        with open(DATA_FILE, "w", encoding="utf-8") as f: 
            json.dump(to_save, f, indent=4, ensure_ascii=False)
    except: pass

def check_user(uid, name="Foydalanuvchi"):
    if uid not in DB["users"]:
        DB["users"][uid] = {"name": name, "balance": 10000, "tickets": 5, "apple_game": None, "aviator_game": None, "state": None}
        save_db()
    u = DB["users"][uid]
    for k in ["apple_game", "aviator_game", "state"]:
        if k not in u: u[k] = None
    return u

def get_max_bet(uid):
    return 900000 if uid in VIP_USERS or uid == ADMIN_ID else 20000

# --- BOT BUYRUQLARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ud = check_user(uid, update.effective_user.first_name)
    ud["state"] = None
    save_db()
    
    txt = (
        f"👑 *SHOX SUPREME PLATFORMA v8.5*\n\n"
        f"💵 *Balans:* {ud['balance']} so'm\n"
        f"🎫 *Chiptalar:* {ud['tickets']} ta\n"
        f"🚀 *Maksimal garov:* {get_max_bet(uid)} so'm"
    )
    kb = [
        [InlineKeyboardButton("🍏 Apple of Fortune", callback_data="prep_apple"), InlineKeyboardButton("✈️ Aviator", callback_data="prep_aviator")],
        [InlineKeyboardButton("💸 Pul Kiritish", url=f"tg://user?id={ADMIN_ID}"), InlineKeyboardButton("💳 Pul Yechish", url=f"tg://user?id={ADMIN_ID}")],
        [InlineKeyboardButton("🎫 1 ta Chipta (4k)", callback_data="b_ticket_1"), InlineKeyboardButton("🎁 10 ta Chipta (30k)", callback_data="b_ticket_10")]
    ]
    if uid == ADMIN_ID: 
        kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_dashboard")])
    
    if update.message: 
        await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    else: 
        await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); uid = q.from_user.id; ud = check_user(uid)
    
    if q.data == "to_main": 
        await start(update, context)
    elif q.data in ["b_ticket_1", "b_ticket_10"]:
        cost, tix = (4000, 1) if q.data == "b_ticket_1" else (30000, 10)
        if ud["balance"] < cost:
            await q.edit_message_text("❌ Pul yetarli emas!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])); return
        ud["balance"] -= cost; ud["tickets"] += tix; save_db(); await start(update, context)

    elif q.data == "prep_apple":
        ud["state"] = "input_apple_bet"; save_db()
        kb = [[InlineKeyboardButton("💵 2 000 so'm", callback_data="q_ap_2000"), InlineKeyboardButton("💵 5 000 so'm", callback_data="q_ap_5000"), InlineKeyboardButton("💵 10 000 so'm", callback_data="q_ap_10000")], [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]
        await q.edit_message_text(f"🍏 *APPLE OF FORTUNE*\n\nBalans: *{ud['balance']}* so'm\nSummani tanlang yoki o'zingiz yozing:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data.startswith("q_ap_"):
        bet = int(q.data.split("_")[2])
        if ud["balance"] < bet: return
        await start_apple_game(q.message, ud, bet, uid)

    elif q.data == "prep_aviator":
        ud["state"] = "input_aviator_bet"; save_db()
        h = DB["settings"].get("aviator_history", [2.34, 1.55, 4.12, 1.22, 3.05])
        h_str = " ".join([f"`[x{x}]`" for x in h[-5:]])
        kb = [[InlineKeyboardButton("💵 2 000 so'm", callback_data="q_av_2000"), InlineKeyboardButton("💵 5 000 so'm", callback_data="q_av_5000"), InlineKeyboardButton("💵 10 000 so'm", callback_data="q_av_10000")], [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]
        await q.edit_message_text(f"✈️ *AVIATOR REAL-TIME*\n\nTarix: {h_str}\nBalans: *{ud['balance']}* so'm\nSummani tanlang yoki yozing:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data.startswith("q_av_"):
        bet = int(q.data.split("_")[2])
        if ud["balance"] < bet: return
        await start_aviator_game(q.message, ud, bet, context, uid)

    elif q.data.startswith("ap_select_"):
        idx = int(q.data.split("_")[2]); ag = ud.get("apple_game")
        if not ag: return
        if ag["grid"][ag["current_row"]][idx] == "bad":
            ud["apple_game"] = None; save_db()
            await q.edit_message_text("💀 *Chirigan olma! Pulingiz kuydi uka.*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🍏 Qayta o'ynash", callback_data="prep_apple")]]))
            return
        ag["payout"] = int(ag["bet"] * APPLE_COEFFS[ag["current_row"]]); ag["current_row"] += 1; save_db()
        if ag["current_row"] == 13:
            ud["balance"] += ag["payout"]; ud["apple_game"] = None; save_db()
            await q.edit_message_text(f"👑 *JACKPOT x69.48!* \n💰 Balansga +{ag['payout']} so'm qo'shildi!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]])); return
        await show_apple(q, ud, (uid == ADMIN_ID))
        
    elif q.data == "ap_cashout" and ud.get("apple_game") and ud["apple_game"]["current_row"] > 0:
        ud["balance"] += ud["apple_game"]["payout"]; ud["apple_game"] = None; save_db(); await start(update, context)

    elif q.data == "av_realtime_cashout":
        ag = ud.get("aviator_game")
        if not ag or ag["status"] != "flying": return
        ag["status"] = "cashout_done"; win = int(ag["bet"] * ag["current_win"]); ud["balance"] += win; c_win = ag["current_win"]; ud["aviator_game"] = None; save_db()
        await q.edit_message_text(f"💰 *Muvaffaqiyatli CASHOUT!*\n📈 Koeffitsiyent: *x{c_win}*\n💰 Balansga: +{win} so'm qo'shildi!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✈️ Qayta uchish", callback_data="prep_aviator")]]))

    elif q.data == "admin_dashboard" and uid == ADMIN_ID:
        ud["state"] = None; save_db()
        txt = f"👑 *ADMIN PANEL*\n\n/setav KOEFF - Aviator qotirish\n/plus ID SUMMA - Pul solish\n/addpromo SUMMA - Promokod"
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main")]]))

# --- O'YIN MANTIQLARI ---
async def start_apple_game(message_obj, ud, bet, uid):
    ud["balance"] -= bet; grid = []
    for r in range(13):
        items = ["good"] * 5; bad = 1 if r < 4 else 2 if r < 8 else 3 if r < 11 else 4
        for bi in random.sample(range(5), bad): items[bi] = "bad"
        grid.append(items)
    ud["apple_game"] = {"grid": grid, "current_row": 0, "bet": bet, "payout": bet}; ud["state"] = None; save_db()
    
    class FakeQuery:
        def __init__(self, msg): self.message = msg
        async def edit_message_text(self, t, parse_mode, reply_markup): 
            try: await self.message.edit_text(t, parse_mode=parse_mode, reply_markup=reply_markup)
            except: pass
    await show_apple(FakeQuery(message_obj), ud, (uid == ADMIN_ID))

async def start_aviator_game(message_obj, ud, bet, context, uid):
    ud["balance"] -= bet
    crash = DB["settings"]["next_aviator"] if DB["settings"].get("next_aviator") else round(random.uniform(1.1, 4.5), 2)
    DB["settings"]["next_aviator"] = None
    ud["aviator_game"] = {"current_win": 1.0, "crash": crash, "bet": bet, "status": "flying"}; ud["state"] = None; save_db()
    asyncio.create_task(run_realtime_aviator(context.application, message_obj.chat_id, message_obj.message_id, uid))

async def run_realtime_aviator(app_obj, chat_id, message_id, uid):
    while True:
        await asyncio.sleep(0.85)
        ud = DB["users"].get(uid)
        if not ud or not ud.get("aviator_game") or ud["aviator_game"]["status"] != "flying": break
        ag = ud["aviator_game"]
        ag["current_win"] = round(ag["current_win"] + random.uniform(0.12, 0.28), 2)
        
        if ag["current_win"] >= ag["crash"]:
            cp = ag["crash"]; ud["aviator_game"] = None; DB["settings"]["aviator_history"].append(cp); save_db()
            try: await app_obj.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"💥 *BOOM! x{cp} da portladi!* \nTikilgan {ag['bet']} so'm kuydi.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✈️ Qayta", callback_data="prep_aviator")]]))
            except: pass
            break
        save_db(); current_payout = int(ag["bet"] * ag["current_win"])
        txt = f"✈️ *AVIATOR*\n\n📈 Joriy Koeffitsiyent: *x{ag['current_win']}* 🔥\n💵 Garov: {ag['bet']} so'm\n💰 Naqd yutuq: {current_payout} so'm"
        try: await app_obj.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"🛑 CASHOUT ({current_payout})", callback_data="av_realtime_cashout")]]))
        except: pass

async def show_apple(q, ud, is_admin_cheat):
    ag = ud["apple_game"]; crow = ag["current_row"]; kb = []
    for ri in range(12, -1, -1):
        row = [InlineKeyboardButton(f"x{APPLE_COEFFS[ri]}", callback_data="lock")]
        for ci in range(5):
            if ri < crow: row.append(InlineKeyboardButton("🍏", callback_data="lock"))
            elif ri == crow:
                lbl = "🍏" if (is_admin_cheat and ag["grid"][ri][ci] == "good") else "🍎" if (is_admin_cheat and ag["grid"][ri][ci] == "bad") else "🟫"
                row.append(InlineKeyboardButton(lbl, callback_data=f"ap_select_{ci}"))
            else: row.append(InlineKeyboardButton("🔒", callback_data="lock"))
        kb.append(row)
    if crow > 0: kb.append([InlineKeyboardButton(f"💰 Olmalarni olish ({ag['payout']} so'm)", callback_data="ap_cashout")])
    kb.append([InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main")])
    txt = f"🍏 *APPLE OF FORTUNE*\n\n📈 Koeffitsiyent: `x{APPLE_COEFFS[crow-1] if crow > 0 else 1.0}`\n💰 Joriy Yutuq: *{ag['payout']}* so'm"
    await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; ud = check_user(uid, update.effective_user.first_name)
    if not ud["state"]: return
    try:
        bet = int(update.message.text.strip())
        max_b = get_max_bet(uid)
        if bet < 1000 or bet > max_b:
            await update.message.reply_text(f"❌ Garov summasi 1000 dan {max_b} so'mgacha bo'lishi kerak!"); return
    except:
        await update.message.reply_text("❌ Faqat raqam yozing!"); return
    if ud["balance"] < bet:
        await update.message.reply_text("❌ Balansda yetarli pul yo'q!"); return
    
    msg = await update.message.reply_text("🔄 O'yin boshlanmoqda...")
    if ud["state"] == "input_apple_bet": await start_apple_game(msg, ud, bet, uid)
    elif ud["state"] == "input_aviator_bet": await start_aviator_game(msg, ud, bet, context, uid)

# --- ADMIN COMMANDS ---
async def admin_setaviator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        DB["settings"]["next_aviator"] = float(context.args[0]); save_db()
        await update.message.reply_text("✅ Aviator koeffitsiyenti qotirildi!")
    except: pass

async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id, val = int(context.args[0]), int(context.args[1]); user = check_user(t_id)
        user["balance"] += val; save_db()
        await update.message.reply_text(f"✅ ID: {t_id} balansiga {val} so'm qo'shildi!")
        try: await context.application.bot.send_message(chat_id=t_id, text=f"💰 *Hisobingiz to'ldirildi: {val} so'm*")
        except: pass
    except: pass

async def admin_addpromo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        amount = int(context.args[0]); code = f"PROMO-{random.randint(1000, 9999)}"
        DB["settings"]["promos"][code] = amount; save_db()
        await update.message.reply_text(f"🎟 Promokod: `{code}`\nQiymati: {amount} so'm", parse_mode="Markdown")
    except: pass

async def user_claim_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; ud = check_user(uid, update.effective_user.first_name)
    try:
        code = context.args[0].strip()
        if code in DB["settings"]["promos"]:
            bonus = DB["settings"]["promos"].pop(code); ud["balance"] += bonus; save_db()
            await update.message.reply_text(f"✅ Promokod faollashdi! `+{bonus}` so'm", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Promokod xato!")
    except: pass

app = Flask(__name__)
@app.route('/')
def home(): return "OK"

def main():
    load_db()
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Pool_timeout o'rniga faqat standart xavfsiz timeout sozlamasi qoldirildi
    clean_client = httpx.AsyncClient(base_url="https://api.telegram.org", timeout=45.0)
    
    bot = Application.builder().token(TOKEN).request(clean_client).read_timeout(45).write_timeout(45).connect_timeout(45).build()
    
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("setav", admin_setaviator))
    bot.add_handler(CommandHandler("plus", admin_plus))
    bot.add_handler(CommandHandler("addpromo", admin_addpromo))
    bot.add_handler(CommandHandler("promo", user_claim_promo))
    bot.add_handler(CallbackQueryHandler(callback_handler))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    print("Bot xatolarsiz muvaffaqiyatli yuklandi!")
    bot.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
                   
