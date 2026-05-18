import os
import sys
import subprocess
import json
import random
import asyncio
from flask import Flask
from threading import Thread

# Kerakli kutubxonalarni tekshirish va o'rnatish
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = "8303235336:AAEk3J42idbz1KcamIWPC2L3_IlROPeoadI"
ADMIN_ID = 8086545587  
DATA_FILE = "mega_games_bot_db.json"

DB = {
    "users": {}, 
    "promocodes": {}, 
    "settings": {"ticket_price": 4000, "min_withdraw": 15000}, 
    "stats": {"total_games": 0, "total_prizes_given": 0, "mines_profit": 0, "apple_profit": 0, "aviator_profit": 0, "slot_profit": 0}
}
APPLE_COEFFS = [1.23, 1.54, 1.93, 2.41, 3.02, 4.02, 5.70, 8.55, 13.43, 69.48]
SLOT_EMOJIS = ["🍒", "🍋", "🍇", "🔔", "💎", "7️⃣"]

def load_db():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f: 
                DB = json.load(f)
                DB["users"] = {int(k): v for k, v in DB.get("users", {}).items()}
        except: pass

def save_db():
    try:
        to_save = DB.copy()
        to_save["users"] = {str(k): v for k, v in DB["users"].items()}
        with open(DATA_FILE, "w", encoding="utf-8") as f: 
            json.dump(to_save, f, indent=4, ensure_ascii=False)
    except: pass

def check_user(uid, name="Foydalanuvchi"):
    if uid not in DB["users"]:
        DB["users"][uid] = {
            "name": name, "balance": 5000, "tickets": 3, "total_won": 0, 
            "games_played": 0, "mines_game": None, "apple_game": None, "aviator_game": None
        }
        save_db()
    return DB["users"][uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ud = check_user(uid, update.effective_user.first_name)
    txt = f"👑 *SHOX SUPREME PLATFORMA*\n\n💵 *Balans:* {ud['balance']} so'm\n🎫 *Chiptalar:* {ud['tickets']} ta\n\nFaqat eng daxshatli va mukammal bo'limlar 👇"
    kb = [
        [InlineKeyboardButton("💣 Mines (Mina)", callback_data="g_mines"), InlineKeyboardButton("🎰 Slot (777)", callback_data="g_slot")],
        [InlineKeyboardButton("🍏 Apple of Fortune", callback_data="g_apple"), InlineKeyboardButton("✈️ Aviator", callback_data="g_aviator")],
        [InlineKeyboardButton("🎫 Chipta Xarid Qilish (4k)", callback_data="b_ticket"), InlineKeyboardButton("📦 Maxfiy Keyslar", callback_data="g_cases")],
        [InlineKeyboardButton("📊 Profil", callback_data="u_profile"), InlineKeyboardButton("💳 Pul Yechish", callback_data="u_withdraw")]
    ]
    if uid == ADMIN_ID: 
        kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_dashboard")])
        
    if update.message: 
        await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    else: 
        await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    ud = check_user(uid)
    
    if q.data == "to_main": 
        await start(update, context)
    elif q.data == "b_ticket":
        if ud["balance"] < 4000: 
            await q.edit_message_text("❌ Pul yetarli emas!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))
            return
        ud["balance"] -= 4000
        ud["tickets"] += 1
        save_db()
        await start(update, context)
    elif q.data == "u_profile":
        await q.edit_message_text(f"👤 *PROFIL*\n\n🆔 ID: `{uid}`\n💵 Balans: {ud['balance']} so'm\n🎫 Chipta: {ud['tickets']} ta\n🕹 O'yinlar: {ud['games_played']}\n🏆 Yutuq: {ud['total_won']} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))
    elif q.data == "u_withdraw":
        await q.edit_message_text(f"💳 *PUL YECHISH*\n\nMinimal: {DB['settings']['min_withdraw']} so'm\nID: `{uid}`\nYechish uchun admin lichkasiga yozing uka!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 Admin Lichka", url="https://t.me/shox_admin")], [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))
    
    # 🎰 SLOT (777) O'YINI
    elif q.data == "g_slot":
        if ud["balance"] < 3000:
            await q.edit_message_text("❌ Slot o'ynash uchun kamida 3000 so'm kerak!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))
            return
        ud["balance"] -= 3000
        res = [random.choice(SLOT_EMOJIS) for _ in range(3)]
        line = " | ".join(res)
        
        if res[0] == res[1] == res[2]:
            if res[0] == "7️⃣":
                win = 50000
                txt = f"🎰 *SLOT 777* 🎰\n\n▶️ [ {line} ]\n\n👑 *DAXSHATLI JACKPOT!!!* X777! +50,000 so'm yutdingiz!"
            else:
                win = 15000
                txt = f"🎰 *SLOT 777* 🎰\n\n▶️ [ {line} ]\n\n🎉 *G'ALABA!* 3 ta bir xil! +15,000 so'm!"
            ud["balance"] += win
            ud["total_won"] += win
            DB["stats"]["total_prizes_given"] += win
        elif res[0] == res[1] or res[1] == res[2] or res[0] == res[2]:
            win = 5000
            ud["balance"] += win
            ud["total_won"] += win
            DB["stats"]["total_prizes_given"] += win
            txt = f"🎰 *SLOT 777* 🎰\n\n▶️ [ {line} ]\n\n💵 *Kichik Yutuq!* 2 ta bir xil! +5,000 so'm!"
        else:
            DB["stats"]["slot_profit"] += 3000
            txt = f"🎰 *SLOT 777* 🎰\n\n▶️ [ {line} ]\n\n💀 *Omad kelmadi!* Qayta urunib ko'ring uka!"
            
        ud["games_played"] += 1
        DB["stats"]["total_games"] += 1
        save_db()
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎰 Qayta aylantirish (3k)", callback_data="g_slot")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))

    # 💣 MINES
    elif q.data == "g_mines":
        if not ud["mines_game"]:
            if ud["tickets"] < 1: 
                await q.edit_message_text("❌ Chipta yo'q!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Chipta", callback_data="b_ticket")]]))
                return
            ud["tickets"] -= 1
            grid = ["clean"] * 9
            for idx in random.sample(range(9), 2): 
                grid[idx] = "mine"
            ud["mines_game"] = {"grid": grid, "revealed": [False] * 9, "payout": 4000, "step": 0}
            save_db()
        await show_mines(q, ud)
    elif q.data.startswith("m_clk_"):
        idx = int(q.data.split("_")[2])
        mg = ud["mines_game"]
        if not mg or mg["revealed"][idx]: return
        mg["revealed"][idx] = True
        if mg["grid"][idx] == "mine":
            ud["mines_game"] = None
            ud["games_played"] += 1
            DB["stats"]["total_games"] += 1
            DB["stats"]["mines_profit"] += 4000
            save_db()
            await q.edit_message_text("💥 *BOOOM! Minaga portladingiz!*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💣 Qayta", callback_data="g_mines")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))
            return
        mg["step"] += 1
        mg["payout"] = int(mg["payout"] * 1.65)
        save_db()
        if mg["step"] == 7:
            ud["balance"] += mg["payout"]
            ud["total_won"] += mg["payout"]
            DB["stats"]["total_prizes_given"] += mg["payout"]
            ud["mines_game"] = None
            ud["games_played"] += 1
            DB["stats"]["total_games"] += 1
            save_db()
            await q.edit_message_text(f"👑 *G'ALABA!* +{mg['payout']} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="to_main")]]))
            return
        await show_mines(q, ud)
    elif q.data == "m_cash" and ud["mines_game"]:
        w = ud["mines_game"]["payout"]
        ud["balance"] += w
        ud["total_won"] += w
        DB["stats"]["total_prizes_given"] += w
        ud["mines_game"] = None
        ud["games_played"] += 1
        DB["stats"]["total_games"] += 1
        save_db()
        await q.edit_message_text(f"💰 *Cashout!* +{w} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💣 Yana", callback_data="g_mines")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))

    # 🍏 APPLE OF FORTUNE
    elif q.data == "g_apple":
        if not ud["apple_game"]:
            if ud["balance"] < 3000: 
                await q.edit_message_text("❌ Balansda kamida 3k bo'lishi kerak!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="to_main")]]))
                return
            ud["balance"] -= 3000
            fg = []
            for r in range(10):
                items = ["good"] * 5
                bc = 1 if r < 4 else 2 if r < 7 else 3
                for bi in random.sample(range(5), bc): 
                    items[bi] = "bad"
                fg.append(items)
            ud["apple_game"] = {"grid": fg, "current_row": 0, "bet": 3000, "payout": 3000}
            save_db()
        await show_apple(q, ud)
    elif q.data.startswith("ap_select_"):
        idx = int(q.data.split("_")[2])
        ag = ud["apple_game"]
        if not ag: return
        crow = ag["current_row"]
        if ag["grid"][crow][idx] == "bad":
            ud["apple_game"] = None
            ud["games_played"] += 1
            DB["stats"]["total_games"] += 1
            DB["stats"]["apple_profit"] += 3000
            save_db()
            await q.edit_message_text("💀 *Chirigan olma! Garov kuydi.*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🍏 Qayta", callback_data="g_apple")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))
            return
        ag["payout"] = int(ag["bet"] * APPLE_COEFFS[crow])
        ag["current_row"] += 1
        save_db()
        if ag["current_row"] == 10:
            ud["balance"] += ag["payout"]
            ud["total_won"] += ag["payout"]
            DB["stats"]["total_prizes_given"] += ag["payout"]
            ud["apple_game"] = None
            ud["games_played"] += 1
            DB["stats"]["total_games"] += 1
            save_db()
            await q.edit_message_text(f"👑 *JACKPOT x69.48!* +{ag['payout']} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))
            return
        await show_apple(q, ud)
    elif q.data == "ap_cashout" and ud["apple_game"] and ud["apple_game"]["current_row"] > 0:
        w = ud["apple_game"]["payout"]
        ud["balance"] += w
        ud["total_won"] += w
        DB["stats"]["total_prizes_given"] += w
        ud["apple_game"] = None
        ud["games_played"] += 1
        DB["stats"]["total_games"] += 1
        save_db()
        await q.edit_message_text(f"💰 *Yutuq olindi!* +{w} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🍏 Yana", callback_data="g_apple")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))

    # ✈️ AVIATOR
    elif q.data == "g_aviator":
        if ud["balance"] < 2000: 
            await q.edit_message_text("❌ Kamida 2k kerak!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="to_main")]]))
            return
        ud["balance"] -= 2000
        cp = round(random.uniform(1.1, 8.0), 2)
        ud["aviator_game"] = {"bet": 2000, "current_mult": 1.0, "crash": cp}
        save_db()
        
        cm = 1.0
        while cm < cp:
            await q.edit_message_text(f"✈️ *AVIATOR* \n\n🚀 Koeffitsiyent: *x{cm}*\n💰 Yutuq: {int(2000*cm)} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"🛑 CASHOUT (x{cm})", callback_data="av_cashout")]]))
            await asyncio.sleep(1)
            cm = round(cm + random.uniform(0.2, 0.5), 2)
            ud = check_user(uid)
            if not ud["aviator_game"]: return
            
        ud["aviator_game"] = None
        ud["games_played"] += 1
        DB["stats"]["total_games"] += 1
        DB["stats"]["aviator_profit"] += 2000
        save_db()
        await q.edit_message_text(f"💥 *💥 BOOM! x{cp} nuqtasida uchib ketdi!*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✈️ Qayta", callback_data="g_aviator")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))

    elif q.data == "av_cashout" and ud["aviator_game"]:
        mult = ud["aviator_game"]["current_mult"]
        w = int(2000 * mult)
        ud["balance"] += w
        ud["total_won"] += w
        DB["stats"]["total_prizes_given"] += w
        ud["aviator_game"] = None
        ud["games_played"] += 1
        DB["stats"]["total_games"] += 1
        save_db()
        await q.edit_message_text(f"✈️ *Aviator Cashout!* x{mult}\n💰 +{w} so'm!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✈️ Yana", callback_data="g_aviator")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))

    # 📦 KEYSLAR
    elif q.data == "g_cases":
        await q.edit_message_text("📦 *KEYSLAR DO'KONI*\n\n1. Bronze (4k)\n2. Silver (15k)\n3. Gold (40k)", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Bronze", callback_data="op_c_1"), InlineKeyboardButton("💎 Silver", callback_data="op_c_2"), InlineKeyboardButton("👑 Gold", callback_data="op_c_3")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))
    elif q.data.startswith("op_c_"):
        ct = q.data.split("_")[2]
        cost, pmin, pmax = (4000, 1000, 9000) if ct == "1" else (15000, 5000, 35000) if ct == "2" else (40000, 15000, 120000)
        if ud["balance"] < cost: 
            await q.edit_message_text("❌ Pul kam!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="g_cases")]]))
            return
        ud["balance"] -= cost
        pw = random.randint(pmin, pmax)
        ud["balance"] += pw
        ud["total_won"] += pw
        DB["stats"]["total_prizes_given"] += pw
        save_db()
        await q.edit_message_text(f"📦 Qutidan *+{pw} so'm* chiqdi!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📦 Yana", callback_data="g_cases")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))

    # 👑 ADMIN PANEL
    elif q.data == "admin_dashboard" and uid == ADMIN_ID:
        await q.edit_message_text(f"👑 *BOSS PANEL v4.0*\n👤 A'zolar: {len(DB['users'])}\n🕹 O'yinlar: {DB['stats']['total_games']}\n💰 Yutuqlar: {DB['stats']['total_prizes_given']} so'm\n\n💣 Mines: +{DB['stats'].get('mines_profit',0)}\n🍏 Apple: +{DB['stats'].get('apple_profit',0)}\n✈️ Aviator: +{DB['stats'].get('aviator_profit',0)}\n🎰 Slot: +{DB['stats'].get('slot_profit',0)}\n\n/plus ID PUL, /minus ID PUL", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main")]]))

async def show_mines(q, ud):
    mg = ud["mines_game"]
    kb = []
    r = []
    for i in range(9):
        r.append(InlineKeyboardButton("💵" if mg["revealed"][i] and mg["grid"][i]!="mine" else "💥" if mg["revealed"][i] else "📦", callback_data="m_dn" if mg["revealed"][i] else f"m_clk_{i}"))
        if len(r) == 3: 
            kb.append(r)
            r = []
    kb.append([InlineKeyboardButton(f"💰 Cashout ({mg['payout']} so'm)", callback_data="m_cash")])
    await q.edit_message_text(f"💣 *MINES* (Bosqich: {mg['step']}/7)\n💵 Yutuq: {mg['payout']} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def show_apple(q, ud):
    ag = ud["apple_game"]
    crow = ag["current_row"]
    kb = []
    for ri in range(9, -1, -1):
        rb = [InlineKeyboardButton("🍏" if ri < crow else "🟫" if ri == crow else "🔒", callback_data=f"ap_select_{ci}" if ri == crow else "ap_lock") for ci in range(5)]
        kb.append(rb)
    if crow > 0: 
        kb.append([InlineKeyboardButton(f"💰 Take ({ag['payout']} so'm)", callback_data="ap_cashout")])
    kb.append([InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main")])
    await q.edit_message_text(f"🍏 *APPLE OF FORTUNE*\nEtap: {crow+1}/10\n📈 Koeff: x{APPLE_COEFFS[crow] if crow<10 else 69.48}\n💵 Yutuq: {ag['payout']} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ud = check_user(uid)
    txt = update.message.text.strip().upper()
    if txt in DB["promocodes"]:
        v = DB["promocodes"][txt]
        ud["balance"] += v
        del DB["promocodes"][txt]
        save_db()
        await update.message.reply_text(f"🎁 Promokod! +{v} so'm qo'shildi!")
        return
    await update.message.reply_text("🤖 O'yin o'ynash uchun /start bosing!")

async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t, v = int(context.args[0]), int(context.args[1])
        if t in DB["users"]: 
            DB["users"][t]["balance"] += v
            save_db()
            await update.message.reply_text("✅ To'ldirildi!")
    except: pass

async def admin_minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t, v = int(context.args[0]), int(context.args[1])
        if t in DB["users"]: 
            DB["users"][t]["balance"] = max(0, DB["users"][t]["balance"] - v)
            save_db()
            await update.message.reply_text("📉 Ayrildi!")
    except: pass

# --- RENDER ASYNCIO VA FLASK STABILIZATORI ---
app = Flask(__name__)
@app.route('/')
def home(): 
    return "Online"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

async def main():
    load_db()
    
    # Veb serverni alohida fonda boshlaymiz
    Thread(target=run_flask, daemon=True).start()
    
    # Bot dasturini quramiz
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("plus", admin_plus))
    bot_app.add_handler(CommandHandler("minus", admin_minus))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Pollingni asyncio loop ichida to'g'ri ishga tushirish (Render xatolik bermasligi uchun)
    async with bot_app:
        await bot_app.initialize()
        await bot_app.start()
        print("Bot daxshatli va to'liq rejimda muvaffaqiyatli boshlandi...")
        await bot_app.updater.start_polling(drop_pending_updates=True)
        # Bot doimiy ishlab turishi uchun cheksiz kutish rejimiga o'tkazamiz
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        # Mavjud asyncio loopni tekshirish yoki yangi ochish
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Agar loop fonda ishlayotgan bo'olsa, task qo'shamiz
            loop.create_task(main())
        else:
            loop.run_until_complete(main())
    except RuntimeError:
        # Loop umuman bo'lmasa, silliqqina run qilamiz
        asyncio.run(main())
    
