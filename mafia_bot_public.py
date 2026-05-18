import os, sys, subprocess, json, random, asyncio
from flask import Flask
from threading import Thread

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
    "users": {}, "promocodes": {},
    "settings": {"next_aviator": None, "next_apple": None, "cheat_mines": False},
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
                if "settings" not in DB: 
                    DB["settings"] = {"next_aviator": None, "next_apple": None, "cheat_mines": False}
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
            "name": name, "balance": 5000, "tickets": 3, "total_won": 0, 
            "games_played": 0, "mines_game": None, "apple_game": None, "aviator_game": None
        }
        save_db()
    return DB["users"][uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ud = check_user(uid, update.effective_user.first_name)
    txt = f"👑 *SHOX SUPREME PLATFORMA*\n\n💵 *Balans:* {ud['balance']} so'm\n🎫 *Chiptalar:* {ud['tickets']} ta"
    kb = [
        [InlineKeyboardButton("💣 Mines (Mina)", callback_data="g_mines"), InlineKeyboardButton("🎰 Slot (777)", callback_data="g_slot")],
        [InlineKeyboardButton("🍏 Apple of Fortune", callback_data="g_apple"), InlineKeyboardButton("✈️ Aviator", callback_data="g_aviator")],
        [InlineKeyboardButton("🎫 1 ta Chipta (4k)", callback_data="b_ticket_1"), InlineKeyboardButton("🎁 AKSIYA: 10 ta Chipta (30k)", callback_data="b_ticket_10")],
        [InlineKeyboardButton("📦 Maxfiy Keyslar", callback_data="g_cases"), InlineKeyboardButton("📊 Profil", callback_data="u_profile")],
        [InlineKeyboardButton("💳 Pul Yechish", callback_data="u_withdraw")]
    ]
    if uid == ADMIN_ID: kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_dashboard")])
    if update.message: await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    else: await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); uid = q.from_user.id; ud = check_user(uid)
    
    if q.data == "to_main": await start(update, context)
    
    elif q.data == "b_ticket_1":
        if ud["balance"] < 4000: await q.edit_message_text("❌ Pul yetarli emas uka!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])); return
        ud["balance"] -= 4000; ud["tickets"] += 1; save_db(); await start(update, context)
    elif q.data == "b_ticket_10":
        if ud["balance"] < 30000: await q.edit_message_text("❌ Aksiya uchun pul yetarli emas!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])); return
        ud["balance"] -= 30000; ud["tickets"] += 10; save_db(); await start(update, context)
        
    elif q.data == "u_profile":
        await q.edit_message_text(f"👤 *PROFIL*\n\n🆔 ID: `{uid}`\n💵 Balans: {ud['balance']} so'm\n🎫 Chipta: {ud['tickets']} ta\n🕹 O'yinlar: {ud['games_played']}\n🏆 Yutuq: {ud['total_won']} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))
    elif q.data == "u_withdraw":
        await q.edit_message_text(f"💳 *PUL YECHISH*\n\nID: `{uid}`\nYechish uchun admin lichkasiga yozing uka!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 Admin Lichka", url="https://t.me/shox_admin")], [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))
    
    # 🎰 SLOT (777)
    elif q.data == "g_slot":
        if ud["balance"] < 3000: await q.edit_message_text("❌ Slot uchun kamida 3k kerak!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]])); return
        ud["balance"] -= 3000; res = [random.choice(SLOT_EMOJIS) for _ in range(3)]; line = " | ".join(res)
        if res[0] == res[1] == res[2]:
            win = 50000 if res[0] == "7️⃣" else 15000
            txt = f"🎰 *SLOT 777* 🎰\n\n▶️ [ {line} ]\n\n👑 *YUTUQ!* +{win} so'm!"
            ud["balance"] += win; ud["total_won"] += win; DB["stats"]["total_prizes_given"] += win
        elif res[0] == res[1] or res[1] == res[2] or res[0] == res[2]:
            ud["balance"] += 5000; ud["total_won"] += 5000; DB["stats"]["total_prizes_given"] += 5000
            txt = f"🎰 *SLOT 777* 🎰\n\n▶️ [ {line} ]\n\n💵 *Kichik Yutuq!* +5,000 so'm!"
        else:
            DB["stats"]["slot_profit"] += 3000
            txt = f"🎰 *SLOT 777* 🎰\n\n▶️ [ {line} ]\n\n💀 Omad kelmadi uka!"
        ud["games_played"] += 1; DB["stats"]["total_games"] += 1; save_db()
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎰 Qayta (3k)", callback_data="g_slot")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))

    # 💣 MINES
    elif q.data == "g_mines":
        if not ud["mines_game"]:
            if ud["tickets"] < 1: await q.edit_message_text("❌ Chipta yo'q uka!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Chipta", callback_data="b_ticket_1")]])); return
            ud["tickets"] -= 1; grid = ["clean"] * 9
            for idx in random.sample(range(9), 2): grid[idx] = "mine"
            ud["mines_game"] = {"grid": grid, "revealed": [False] * 9, "payout": 4000, "step": 0}
            save_db()
        await show_mines(q, ud)
    elif q.data.startswith("m_clk_"):
        idx = int(q.data.split("_")[2]); mg = ud["mines_game"]
        if not mg or mg["revealed"][idx]: return
        mg["revealed"][idx] = True
        if mg["grid"][idx] == "mine":
            ud["mines_game"] = None; ud["games_played"] += 1; DB["stats"]["total_games"] += 1; DB["stats"]["mines_profit"] += 4000; save_db()
            await q.edit_message_text("💥 *BOOOM! Minaga portladingiz!*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💣 Qayta", callback_data="g_mines")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]])); return
        mg["step"] += 1; mg["payout"] = int(mg["payout"] * 1.65); save_db()
        if mg["step"] == 7:
            ud["balance"] += mg["payout"]; ud["total_won"] += mg["payout"]; DB["stats"]["total_prizes_given"] += mg["payout"]; ud["mines_game"] = None; ud["games_played"] += 1; DB["stats"]["total_games"] += 1; save_db()
            await q.edit_message_text(f"👑 *G'ALABA!* +{mg['payout']} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]])); return
        await show_mines(q, ud)
    elif q.data == "m_cash" and ud["mines_game"]:
        w = ud["mines_game"]["payout"]; ud["balance"] += w; ud["total_won"] += w; DB["stats"]["total_prizes_given"] += w; ud["mines_game"] = None; ud["games_played"] += 1; DB["stats"]["total_games"] += 1; save_db()
        await q.edit_message_text(f"💰 *Cashout!* +{w} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💣 Yana", callback_data="g_mines")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))

    # 🍏 APPLE OF FORTUNE
    elif q.data == "g_apple":
        if not ud["apple_game"]:
            if ud["balance"] < 3000: await q.edit_message_text("❌ Balans kam!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="to_main")]])); return
            ud["balance"] -= 3000; fg = []
            
            # Admin belgilagan maxfiy olma ustuni bormi tekshiramiz
            force_col = DB["settings"].get("next_apple")
            DB["settings"]["next_apple"] = None # Ishlatib bo'lingach tozalaymiz
            
            for r in range(10):
                items = ["good"] * 5; bc = 1 if r < 4 else 2 if r < 7 else 3
                bad_indices = random.sample(range(5), bc)
                
                # Agar admin majburiy ustun qo'ygan bo'lsa, uni yaxshi olma qilamiz
                if r == 0 and force_col is not None and force_col in bad_indices:
                    bad_indices.remove(force_col)
                    available = [i for i in range(5) if i != force_col and i not in bad_indices]
                    if available: bad_indices.append(random.choice(available))
                    
                for bi in bad_indices: items[bi] = "bad"
                fg.append(items)
                
            ud["apple_game"] = {"grid": fg, "current_row": 0, "bet": 3000, "payout": 3000}; save_db()
        await show_apple(q, ud)
    elif q.data.startswith("ap_select_"):
        idx = int(q.data.split("_")[2]); ag = ud["apple_game"]
        if not ag: return
        crow = ag["current_row"]
        if ag["grid"][crow][idx] == "bad":
            ud["apple_game"] = None; ud["games_played"] += 1; DB["stats"]["total_games"] += 1; DB["stats"]["apple_profit"] += 3000; save_db()
            await q.edit_message_text("💀 *Chirigan olma! Mag'lubiyat!*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🍏 Qayta", callback_data="g_apple")], [InlineKeyboardButton("⬅️", callback_data="to_main")]])); return
        ag["payout"] = int(ag["bet"] * APPLE_COEFFS[crow]); ag["current_row"] += 1; save_db()
        if ag["current_row"] == 10:
            ud["balance"] += ag["payout"]; ud["total_won"] += ag["payout"]; DB["stats"]["total_prizes_given"] += ag["payout"]; ud["apple_game"] = None; ud["games_played"] += 1; DB["stats"]["total_games"] += 1; save_db()
            await q.edit_message_text(f"👑 *JACKPOT x69.48!* +{ag['payout']} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]])); return
        await show_apple(q, ud)
    elif q.data == "ap_cashout" and ud["apple_game"] and ud["apple_game"]["current_row"] > 0:
        w = ud["apple_game"]["payout"]; ud["balance"] += w; ud["total_won"] += w; DB["stats"]["total_prizes_given"] += w; ud["apple_game"] = None; ud["games_played"] += 1; DB["stats"]["total_games"] += 1; save_db()
        await q.edit_message_text(f"💰 *Yutuq olindi!* +{w} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🍏 Yana", callback_data="g_apple")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))

    # ✈️ AVIATOR (MUKAMMAL CASHOUT VA REAL-STABIL REJIM 🔥)
    elif q.data == "g_aviator":
        if ud["balance"] < 2000: await q.edit_message_text("❌ Kamida 2k kerak uka!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]])); return
        
        if DB["settings"].get("next_aviator") is not None:
            crash_point = DB["settings"]["next_aviator"]
            DB["settings"]["next_aviator"] = None
        else:
            crash_point = round(random.uniform(1.3, 4.8), 2)
            
        user_win_point = round(random.uniform(1.1, max(1.2, crash_point - 0.2)), 2)
        if user_win_point >= crash_point:
            user_win_point = round(crash_point / 1.5, 2)

        ud["balance"] -= 2000
        ud["aviator_game"] = {"win_mult": user_win_point, "crash_mult": crash_point}
        ud["games_played"] += 1; DB["stats"]["total_games"] += 1; save_db()
        
        txt = f"✈️ *AVIATOR PLATFORMA*\n\n🚀 Samolyot havoga ko'tarildi...\n📈 Joriy koeffitsiyent: *x{user_win_point}*\n\n🔴 *Eslatma:* Samolyot istalgan vaqtda portlab ketishi mumkin."
        kb = [
            [InlineKeyboardButton(f"🛑 CASHOUT (x{user_win_point})", callback_data="av_do_cashout")],
            [InlineKeyboardButton(f"🚀 Yana kutish (Tavakkal)", callback_data="av_do_risk")]
        ]
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data == "av_do_cashout":
        if not ud["aviator_game"]: await start(update, context); return
        mult = ud["aviator_game"]["win_mult"]
        w = int(2000 * mult)
        
        ud["balance"] += w; ud["total_won"] += w; DB["stats"]["total_prizes_given"] += w
        ud["aviator_game"] = None; save_db()
        await q.edit_message_text(f"✈️ *CASHOUT BASHARILDI!* 💰\n\n📈 Yakuniy koeffitsiyent: *x{mult}*\n💵 Balansingizga *+{w} so'm* urildi uka!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✈️ Yana o'ynash (2k)", callback_data="g_aviator")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))

    elif q.data == "av_do_risk":
        if not ud["aviator_game"]: await start(update, context); return
        crash = ud["aviator_game"]["crash_mult"]
        ud["aviator_game"] = None
        DB["stats"]["aviator_profit"] += 2000; save_db()
        await q.edit_message_text(f"💥 *BOOM! Samolyot portladi!* 💥\n\n✈️ Ko'proq kutaman deb samolyotni portlatib yubordingiz.\n📈 Portlash nuqtasi: *x{crash}*\n💵 2,000 so'm kuydi.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✈️ Qayta o'ynash", callback_data="g_aviator")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))

    # 📦 KEYSLAR
    elif q.data == "g_cases":
        await q.edit_message_text("📦 *KEYSLAR DO'KONI*\n\n1. Bronze (4k)\n2. Silver (15k)", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Bronze", callback_data="op_c_1"), InlineKeyboardButton("💎 Silver", callback_data="op_c_2")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))
    elif q.data.startswith("op_c_"):
        ct = q.data.split("_")[2]; cost, pmin, pmax = (4000, 1000, 9000) if ct == "1" else (15000, 5000, 35000)
        if ud["balance"] < cost: await q.edit_message_text("❌ Pul kam!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️", callback_data="g_cases")]])); return
        ud["balance"] -= cost; pw = random.randint(pmin, pmax); ud["balance"] += pw; ud["total_won"] += pw; DB["stats"]["total_prizes_given"] += pw; save_db()
        await q.edit_message_text(f"📦 Qutidan *+{pw} so'm* chiqdi!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📦 Yana", callback_data="g_cases")], [InlineKeyboardButton("⬅️", callback_data="to_main")]]))

    # 👑 ADMIN PANEL
    elif q.data == "admin_dashboard" and uid == ADMIN_ID:
        await show_admin_panel(q)
    elif q.data == "toggle_mines" and uid == ADMIN_ID:
        DB["settings"]["cheat_mines"] = not DB["settings"].get("cheat_mines", False); save_db(); await show_admin_panel(q)

async def show_admin_panel(q):
    st = DB["settings"]; cheat_status = "✅ YOQILGAN" if st.get("cheat_mines") else "❌ O'CHIK"
    next_av = st.get("next_aviator") if st.get("next_aviator") else "Avtomat"
    next_ap = st.get("next_apple") if st.get("next_apple") is not None else "Avtomat"
    txt = f"👑 *ADMINISTRATOR PANEL*\n\n🔥 *Minalar cheat:* {cheat_status}\n✈️ *Aviator signal:* x{next_av}\n🍏 *Apple signal:* Ustun {next_ap}\n\n/setav KOEFF\n/setapple USTUN(1-5)\n/plus ID PUL"
    kb = [[InlineKeyboardButton("Minalar ko'rinishini o'zgartirish", callback_data="toggle_mines")],[InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main")]]
    await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def show_mines(q, ud):
    mg = ud["mines_game"]; kb = []; r = []; is_admin = (q.from_user.id == ADMIN_ID); show_cheat = DB["settings"].get("cheat_mines", False)
    for i in range(9):
        if mg["revealed"][i]: lbl = "💥" if mg["grid"][i] == "mine" else "💵"
        else: lbl = "💣" if (is_admin and show_cheat and mg["grid"][i] == "mine") else "📦"
        r.append(InlineKeyboardButton(lbl, callback_data="m_dn" if mg["revealed"][i] else f"m_clk_{i}"))
        if len(r) == 3: kb.append(r); r = []
    kb.append([InlineKeyboardButton(f"💰 Cashout ({mg['payout']} so'm)", callback_data="m_cash")])
    await q.edit_message_text(f"💣 *MINES* (Bosqich: {mg['step']}/7)\n💵 Hozirgi yutuq: {mg['payout']} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def show_apple(q, ud):
    ag = ud["apple_game"]; crow = ag["current_row"]; kb = []
    for ri in range(9, -1, -1):
        rb = [InlineKeyboardButton("🍏" if ri < crow else "🟫" if ri == crow else "🔒", callback_data=f"ap_select_{ci}" if ri == crow else "ap_lock") for ci in range(5)]
        kb.append(rb)
    if crow > 0: kb.append([InlineKeyboardButton(f"💰 Olmani olish ({ag['payout']} so'm)", callback_data="ap_cashout")])
    kb.append([InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main")])
    await q.edit_message_text(f"🍏 *APPLE OF FORTUNE*\nEtap: {crow+1}/10\n💵 Yutuq: {ag['payout']} so'm", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 O'yinlarni boshlash uchun /start bosing!")

async def admin_set_aviator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        val = float(context.args[0])
        DB["settings"]["next_aviator"] = val; save_db()
        await update.message.reply_text(f"✅ Aviator uchun keyingi koeffitsiyent *x{val}* etib belgilandi uka!")
    except: pass

async def admin_set_apple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        val = int(context.args[0]) - 1 # 1-5 ni 0-4 indeksga o'giramiz
        if 0 <= val <= 4:
            DB["settings"]["next_apple"] = val; save_db()
            await update.message.reply_text(f"✅ Apple uchun keyingi o'yinda 1-qatordagi *{val+1}-ustun* 100% yutuqli qilib tayyorlandi!")
        else: pass
    except: pass

async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t, v = int(context.args[0]), int(context.args[1])
        load_db()
        if t in DB["users"]: 
            DB["users"][t]["balance"] += v; save_db()
            await update.message.reply_text("✅ Balans muvaffaqiyatli to'ldirildi!")
    except: pass

app = Flask(__name__)
@app.route('/')
def home(): return "Online"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

async def main():
    load_db()
    Thread(target=run_flask, daemon=True).start()
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("setav", admin_set_aviator))
    bot_app.add_handler(CommandHandler("setapple", admin_set_app
