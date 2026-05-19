import os
import sys
import json
import random
import asyncio
from flask import Flask
from threading import Thread

# Kerakli kutubxonalarni tekshirish va o'rnatish
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Birlamchi Sozlamalar
TOKEN = "8303235336:AAHkjNihtbYY5QeSm9H2P2DBHyFgg6Fyd_s"
ADMIN_ID = 8086545587  
DATA_FILE = "mega_games_bot_db.json"

# Global Kesh (Render o'chib ketganda ham xotirada saqlash uchun sodda tizim)
DB = {
    "users": {},
    "settings": {
        "next_aviator": None,
        "aviator_history": [2.34, 1.55, 4.12, 1.22, 3.05]
    }
}

APPLE_COEFFS = [1.23, 1.54, 1.93, 2.41, 3.02, 4.02, 5.70, 8.55, 13.43, 20.15, 30.22, 45.33, 69.48]

def load_db():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "users" in data:
                    DB["users"] = {int(k): v for k, v in data["users"].items()}
                if "settings" in data:
                    DB["settings"] = data["settings"]
        except Exception:
            pass

def save_db():
    try:
        to_save = {
            "users": {str(k): v for k, v in DB["users"].items()},
            "settings": DB["settings"]
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def check_user(uid, name="Foydalanuvchi"):
    if uid not in DB["users"]:
        DB["users"][uid] = {
            "name": name,
            "balance": 10000,
            "tickets": 5,
            "apple_game": None,
            "aviator_game": None,
            "state": None
        }
        save_db()
    
    # Eski ma'lumotlar strukturasini yangilash
    user = DB["users"][uid]
    if "apple_game" not in user: user["apple_game"] = None
    if "aviator_game" not in user: user["aviator_game"] = None
    if "state" not in user: user["state"] = None
    if "tickets" not in user: user["tickets"] = 5
    return user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ud = check_user(uid, update.effective_user.first_name)
    ud["state"] = None
    save_db()
    
    txt = (
        f"👑 *SHOX SUPREME PLATFORMA v7.5*\n\n"
        f"💵 *Balans:* {ud['balance']} so'm\n"
        f"🎫 *Chiptalar:* {ud['tickets']} ta\n\n"
        f"⚡️ _Tizim Render serverlari uchun maksimal optimallashtirildi!_"
    )
    
    kb = [
        [InlineKeyboardButton("🍏 Apple of Fortune", callback_data="prep_apple"),
         InlineKeyboardButton("✈️ Aviator (Real-Time)", callback_data="prep_aviator")],
        [InlineKeyboardButton("💸 Pul Kiritish", url=f"tg://user?id={ADMIN_ID}"),
         InlineKeyboardButton("💳 Pul Yechish", url=f"tg://user?id={ADMIN_ID}")],
        [InlineKeyboardButton("🎫 1 ta Chipta (4k)", callback_data="b_ticket_1"),
         InlineKeyboardButton("🎁 10 ta Chipta (30k)", callback_data="b_ticket_10")],
    ]
    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_dashboard")])
        
    if update.message:
        await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer() # Inline tugma srazu "Yuklanmoqda..." holatidan chiqishi shart!
    
    uid = q.from_user.id
    ud = check_user(uid)
    
    if q.data == "to_main":
        await start(update, context)
        
    elif q.data == "b_ticket_1":
        if ud["balance"] < 4000:
            await q.edit_message_text("❌ Balansda yetarli mablag' yo'q!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))
            return
        ud["balance"] -= 4000
        ud["tickets"] += 1
        save_db()
        await start(update, context)
        
    elif q.data == "b_ticket_10":
        if ud["balance"] < 30000:
            await q.edit_message_text("❌ Balansda yetarli mablag' yo'q!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]]))
            return
        ud["balance"] -= 30000
        ud["tickets"] += 10
        save_db()
        await start(update, context)

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
            f"🍏 *APPLE OF FORTUNE*\n\nBalansingiz: *{ud['balance']}* so'm\n"
            f"Tikmoqchi bo'lgan summani tanlang yoki yozib yuboring:\n\n"
            f"⚠️ _Minimal: 1 000 so'm | Maksimal: 10 000 so'm_",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
        )

    elif q.data.startswith("quick_apple_"):
        bet = int(q.data.split("_")[2])
        if ud["balance"] < bet:
            await q.edit_message_text("❌ Mablag' yetarli emas!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="prep_apple")]]))
            return
        await start_apple_game(q.message, ud, bet, uid)

    elif q.data == "prep_aviator":
        ud["state"] = "input_aviator_bet"
        save_db()
        history = DB["settings"].get("aviator_history", [2.34, 1.55, 4.12, 1.22, 3.05])
        h_str = " ".join([f"`[x{h}]`" for h in history[-5:]])
        
        kb = [
            [InlineKeyboardButton("💵 2 000 so'm", callback_data="quick_aviator_2000"),
             InlineKeyboardButton("💵 5 000 so'm", callback_data="quick_aviator_5000"),
             InlineKeyboardButton("💵 10 000 so'm", callback_data="quick_aviator_10000")],
            [InlineKeyboardButton("⬅️ Ortga", callback_data="to_main")]
        ]
        await q.edit_message_text(
            f"✈️ *AVIATOR REAL-TIME*\n\n📋 *Oxirgi koeffitsiyentlar:* \n{h_str}\n\n"
            f"Balansingiz: *{ud['balance']}* so'm\nTikmoqchi bo'lgan summani kiriting:",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
        )

    elif q.data.startswith("quick_aviator_"):
        bet = int(q.data.split("_")[2])
        if ud["balance"] < bet:
            await q.edit_message_text("❌ Mablag' yetarli emas!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data="prep_aviator")]]))
            return
        await start_aviator_game(q.message, ud, bet, context, uid)

    elif q.data.startswith("ap_select_"):
        idx = int(q.data.split("_")[2])
        ag = ud.get("apple_game")
        if not ag: return
        
        status = ag["grid"][ag["current_row"]][idx]
        if status == "bad":
            ud["apple_game"] = None
            save_db()
            await q.edit_message_text("💀 *Chirigan olma! Garov tikilgan pulingiz kuydi uka.*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🍏 Qayta o'ynash", callback_data="prep_apple")], [InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))
            return
            
        ag["payout"] = int(ag["bet"] * APPLE_COEFFS[ag["current_row"]])
        ag["current_row"] += 1
        save_db()
        
        if ag["current_row"] == 13:
            ud["balance"] += ag["payout"]
            ud["apple_game"] = None
            save_db()
            await q.edit_message_text(f"👑 *JACKPOT x69.48!* \n💰 Balansga +{ag['payout']} so'm qo'shildi!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menyu", callback_data="to_main")]]))
            return
            
        await show_apple(q, ud, (uid == ADMIN_ID))
        
    elif q.data == "ap_cashout" and ud.get("apple_game") and ud["apple_game"]["current_row"] > 0:
        w = ud["apple_game"]["payout"]
        ud["balance"] += w
        ud["apple_game"] = None
        save_db()
        await start(update, context)

    # 🛑 ULTRA TEZKOR CASHOUT - NAVBAT KUTMASDAN ISHLAYDI
    elif q.data == "av_realtime_cashout":
        ag = ud.get("aviator_game")
        if not ag or ag["status"] != "flying": return
        
        ag["status"] = "cashout_done"
        win = int(ag["bet"] * ag["current_win"])
        ud["balance"] += win
        c_win = ag["current_win"]
        ud["aviator_game"] = None
        save_db()
        
        await q.edit_message_text(
            f"💰 *Muvaffaqiyatli CASHOUT!*\n📈 Koeffitsiyent: *x{c_win}*\n💰 Balansingizga: +{win} so'm qo'shildi!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✈️ Qayta uchish", callback_data="prep_aviator")], [InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="to_main")]])
        )

    elif q.data == "admin_dashboard" and uid == ADMIN_ID:
        next_av = DB["settings"].get("next_aviator") or "Random"
        txt = f"👑 *ADMIN CHEAT PANEL*\n\n✈ Keyingi Aviator parvozi: x{next_av}\n\n*Buyruqlar:*\n/setav KOEFF\n/plus ID PUL"
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Chiqish", callback_data="to_main")]]))

async def start_apple_game(message_obj, ud, bet, uid):
    ud["balance"] -= bet
    grid = []
    for r in range(13):
        items = ["good"] * 5
        bad_count = 1 if r < 4 else 2 if r < 8 else 3 if r < 11 else 4
        for bi in random.sample(range(5), bad_count): items[bi] = "bad"
        grid.append(items)
        
    ud["apple_game"] = {"grid": grid, "current_row": 0, "bet": bet, "payout": bet}
    ud["state"] = None
    save_db()
    
    class FakeQuery:
        def __init__(self, msg): self.message = msg
        async def edit_message_text(self, t, parse_mode, reply_markup):
            await self.message.edit_text(t, parse_mode=parse_mode, reply_markup=reply_markup)
            
    await show_apple(FakeQuery(message_obj), ud, (uid == ADMIN_ID))

async def start_aviator_game(message_obj, ud, bet, context, uid):
    ud["balance"] -= bet
    if DB["settings"].get("next_aviator") is not None:
        crash = DB["settings"]["next_aviator"]
        DB["settings"]["next_aviator"] = None
    else:
        crash = round(random.uniform(1.1, 5.5), 2)
        
    ud["aviator_game"] = {"current_win": 1.0, "crash": crash, "bet": bet, "status": "flying"}
    ud["state"] = None
    save_db()
    
    asyncio.create_task(run_realtime_aviator(context.application, message_obj.chat_id, message_obj.message_id, uid))

async def run_realtime_aviator(app_obj, chat_id, message_id, uid):
    while True:
        await asyncio.sleep(0.8) # Telegram Rate Limit ga tushmaslik uchun ideal vaqt
        ud = DB["users"].get(uid)
        if not ud: break
        
        ag = ud.get("aviator_game")
        if not ag or ag.get("status") != "flying": break
        
        ag["current_win"] = round(ag["current_win"] + random.uniform(0.1, 0.3), 2)
        
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
                    text=f"💥 *BOOM! Samolyot x{c_p} nuqtada portladi uka!*\nTikilgan {ag['bet']} so'm pul kuydi.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✈️ Qayta urinish", callback_data="prep_aviator")], [InlineKeyboardButton("⬅️ Bosh Menyu", callback_data="to_main")]])
                )
            except Exception: pass
            break
            
        save_db()
        current_payout = int(ag["bet"] * ag["current_win"])
        history = DB["settings"].get("aviator_history", [2.34, 1.55, 4.12, 1.22, 3.05])
        h_str = " ".join([f"`[x{h}]`" for h in history[-5:]])
        
        txt = (
            f"✈️ *AVIATOR REAL-TIME PLATFORMA*\n\n"
            f"📋 Tarix: {h_str}\n\n"
            f"🚀 Samolyot havoda ko'tarilmoqda...\n"
            f"📈 Joriy Koeffitsiyent: *x{ag['current_win']}* 🔥\n\n"
            f"💵 Tikilgan pul: {ag['bet']} so'm\n"
            f"💰 Hozirgi yutuq qiymati: {current_payout} so'm"
        )
        kb = [[InlineKeyboardButton(f"🛑 CASHOUT ({current_payout} so'm)", callback_data="av_realtime_cashout")]]
        
        try:
            await app_obj.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        except Exception: pass

async def show_apple(q, ud, is_admin_cheat):
    ag = ud["apple_game"]
    crow = ag["current_row"]
    kb = []
    
    for ri in range(12, -1, -1):
        row_buttons = []
        row_buttons.append(InlineKeyboardButton(f"x{APPLE_COEFFS[ri]}", callback_data="lock"))
        
        if ri < crow:
            for ci in range(5): row_buttons.append(InlineKeyboardButton("🍏", callback_data="lock"))
        elif ri == crow:
            for ci in range(5):
                lbl = "🍏" if (is_admin_cheat and ag["grid"][ri][ci] == "good") else "🍎" if (is_admin_cheat and ag["grid"][ri][ci] == "bad") else "🟫"
                row_buttons.append(InlineKeyboardButton(lbl, callback_data=f"ap_select_{ci}"))
        else:
            for ci in range(5): row_buttons.append(InlineKeyboardButton("🔒", callback_data="lock"))
        kb.append(row_buttons)
        
    if crow > 0:
        kb.append([InlineKeyboardButton(f"💰 Olmalarni olish ({ag['payout']} so'm)", callback_data="ap_cashout")])
    kb.append([InlineKeyboardButton("⬅️ Chiqish o'yinidan", callback_data="to_main")])
    
    current_kf = APPLE_COEFFS[crow-1] if crow > 0 else 1.0
    txt = f"🍏 *APPLE OF FORTUNE*\n\n📈 Koeffitsiyent: `x{current_kf}`\n💵 Tikilgan: *{ag['bet']}* so'm\n💰 Yutuq: *{ag['payout']}* so'm"
    await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ud = check_user(uid, update.effective_user.first_name)
    if not ud["state"]: return
    
    try:
        bet = int(update.message.text.strip())
        if bet < 1000 or bet > 10000: raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Garov summasi 1000 dan 10000 so'mgacha bo'lishi kerak!")
        return
        
    if ud["balance"] < bet:
        await update.message.reply_text("❌ Balansda yetarli pul yo'q!")
        return
        
    msg = await update.message.reply_text("🔄 O'yin boshlanmoqda...")
    if ud["state"] == "input_apple_bet":
        await start_apple_game(msg, ud, bet, uid)
    elif ud["state"] == "input_aviator_bet":
        await start_aviator_game(msg, ud, bet, context, uid)

async def admin_setaviator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        val = float(context.args[0])
        DB["settings"]["next_aviator"] = val
        save_db()
        await update.message.reply_text(f"✅ Keyingi reys x{val} da portlaydi!")
    except Exception: pass

async def admin_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t, v = int(context.args[0]), int(context.args[1])
        user = check_user(t)
        user["balance"] += v
        save_db()
        await update.message.reply_text("✅ Balans to'ldirildi!")
    except Exception: pass

app = Flask(__name__)
@app.route('/')
def home(): return "OK"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

def main():
    load_db()
    Thread(target=run_flask, daemon=True).start()
    
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("setav", admin_setaviator))
    bot_app.add_handler(CommandHandler("plus", admin_plus))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    # Render va asinxronlik uchun eng xavfsiz va to'g'ri sikl boshqaruvi
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
