import os, json, random, time, urllib.request, telebot
from flask import Flask
from threading import Thread
from telebot import types

TOKEN = "8691200742:AAH5hnkQ82SurpHpZJtNMsqF7g6g1Xy5h34"
ADMIN_ID = 8086545587
KVDB_URL = "https://kvdb.io/MN86yM86yM86yM86yM86yM/martin_live_db"
BOT_NAME = "MARTIN LIVE v.11"
COEFFS = [1.23,1.54,1.93,2.41,3.02,4.02,5.7,8.55,13.43,20.15,30.22,45.33,69.48]

bot = telebot.TeleBot(TOKEN)
DB = {"users":{},"settings":{"next_aviator":None,"aviator_history":[1.4,2.1,3.5]},"promocodes":{}}

def load_db():
    global DB
    try:
        with urllib.request.urlopen(urllib.request.Request(KVDB_URL,method="GET"),timeout=10) as r:
            d = json.loads(r.read().decode())
            if "users" in d: DB["users"]={int(k):v for k,v in d["users"].items()}
            if "settings" in d: DB["settings"]=d["settings"]
            if "promocodes" in d: DB["promocodes"]=d["promocodes"]
    except: pass

def save_db():
    try:
        data=json.dumps({"users":{str(k):v for k,v in DB["users"].items()},"settings":DB["settings"],"promocodes":DB.get("promocodes",{})}).encode()
        urllib.request.urlopen(urllib.request.Request(KVDB_URL,data=data,method="PUT",headers={"Content-Type":"application/json"}),timeout=10)
    except: pass

def check_user(uid, name="User"):
    uid=int(uid)
    if uid not in DB["users"]:
        DB["users"][uid]={"name":name,"balance":10000,"last_bonus":0,"apple_game":None,"aviator_game":None,"mines_game":None,"state":None,"temp_bet":None}
        save_db()
    else:
        u=DB["users"][uid]
        for f in ["apple_game","aviator_game","mines_game","state","temp_bet"]:
            if f not in u: u[f]=None
        if "last_bonus" not in u: u["last_bonus"]=0
    return DB["users"][uid]

def main_kb(uid):
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🍏 Apple of Fortune",callback_data="prep_apple"),
           types.InlineKeyboardButton("🚀 Aviator",callback_data="prep_aviator"),
           types.InlineKeyboardButton("💣 MINES",callback_data="prep_mines"),
           types.InlineKeyboardButton("🐊 Swamp Land",callback_data="swamp_soon"),
           types.InlineKeyboardButton("🎁 Kundalik Bonus",callback_data="get_daily_bonus"),
           types.InlineKeyboardButton("🎟 Promokod",callback_data="use_promo"))
    kb.add(types.InlineKeyboardButton("👑 Admin Panel" if uid==ADMIN_ID else "ℹ️ Profil",
           callback_data="admin_dashboard" if uid==ADMIN_ID else "show_profile"))
    kb.add(types.InlineKeyboardButton("💸 Pul Kiritish",url=f"tg://user?id={ADMIN_ID}"),
           types.InlineKeyboardButton("💳 Pul Yechish",url=f"tg://user?id={ADMIN_ID}"))
    return kb

def back_kb(to="to_main"):
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅ Orqaga",callback_data=to))

def menu_txt(ud):
    return f"👑 *{BOT_NAME}*\n\n👤 *{ud['name']}*\n💵 *Balans:* {ud['balance']:,} so'm\n🟢 Live"@bot.message_handler(commands=['start'])
def start_cmd(m):
    ud=check_user(m.from_user.id,m.from_user.first_name)
    ud["state"]=None; save_db()
    bot.send_message(m.chat.id,menu_txt(ud),parse_mode="Markdown",reply_markup=main_kb(m.from_user.id))

@bot.message_handler(func=lambda m: check_user(m.from_user.id).get("state") is not None)
def handle_text(m):
    uid,text=m.from_user.id,m.text
    ud=check_user(uid)
    if ud["state"]=="enter_promo":
        code=text.strip().upper()
        promos=DB.get("promocodes",{})
        if code not in promos:
            bot.send_message(m.chat.id,"❌ Noto'g'ri promokod!")
        elif uid in promos[code].get("used_by",[]):
            bot.send_message(m.chat.id,"❌ Bu kodni allaqachon ishlatgansiz!")
        else:
            amt=promos[code]["amount"]; ud["balance"]+=amt; promos[code]["used_by"].append(uid)
            ud["state"]=None; save_db()
            bot.send_message(m.chat.id,f"🎉 *+{amt:,} so'm qo'shildi!*\n💵 Balans: *{ud['balance']:,} so'm*",parse_mode="Markdown",reply_markup=main_kb(uid))
            return
        ud["state"]=None; save_db(); return
    if uid!=ADMIN_ID: ud["state"]=None; save_db(); return
    if ud["state"]=="set_kf":
        try: DB["settings"]["next_aviator"]=round(float(text),2); save_db(); bot.send_message(m.chat.id,f"✅ Keyingi kf: *x{text}*",parse_mode="Markdown")
        except: bot.send_message(m.chat.id,"❌ Xato son.")
    elif ud["state"] in ["add_money","remove_money"]:
        try:
            parts=text.split(); tid,amt=int(parts[0]),int(parts[1])
            if tid in DB["users"]:
                if ud["state"]=="add_money": DB["users"][tid]["balance"]+=amt; op="qo'shildi"
                else: DB["users"][tid]["balance"]=max(0,DB["users"][tid]["balance"]-amt); op="olindi"
                save_db(); bot.send_message(m.chat.id,f"✅ {amt:,} so'm {op}. Yangi balans: {DB['users'][tid]['balance']:,}")
            else: bot.send_message(m.chat.id,f"❌ ID {tid} topilmadi.")
        except: bot.send_message(m.chat.id,"❌ Format: `ID summa`",parse_mode="Markdown")
    elif ud["state"]=="create_promo":
        try:
            parts=text.strip().split()
            amt=int(parts[0]) if len(parts)==1 else int(parts[1])
            code=("PROMO"+str(random.randint(1000,9999))) if len(parts)==1 else parts[0].upper()
            if code in DB.get("promocodes",{}): bot.send_message(m.chat.id,f"❌ `{code}` allaqachon mavjud!",parse_mode="Markdown")
            else:
                DB.setdefault("promocodes",{})[code]={"amount":amt,"used_by":[]}; save_db()
                bot.send_message(m.chat.id,f"✅ *Promokod yaratildi!*\n🎟 Kod: `{code}`\n💰 Summa: *{amt:,} so'm*",parse_mode="Markdown")
        except: bot.send_message(m.chat.id,"❌ Format: `KOD SUMMA` yoki `SUMMA`",parse_mode="Markdown")
    ud["state"]=None; save_db()@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    uid,cid,mid=call.from_user.id,call.message.chat.id,call.message.message_id
    ud=check_user(uid); d=call.data

    def edit(txt,kb=None,md="Markdown"):
        try: bot.edit_message_text(txt,cid,mid,parse_mode=md,reply_markup=kb)
        except: pass

    def bets_kb(prefix):
        v=[5000,20000,50000,100000,500000] if uid==ADMIN_ID else [2000,5000,10000,15000]
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(*[types.InlineKeyboardButton(f"{b:,} so'm",callback_data=f"{prefix}{b}") for b in v])
        kb.add(types.InlineKeyboardButton("⬅ Chiqish",callback_data="to_main")); return kb

    if d=="to_main":
        ud["state"]=ud["apple_game"]=ud["aviator_game"]=ud["mines_game"]=None; save_db(); edit(menu_txt(ud),main_kb(uid))
    elif d=="swamp_soon": bot.answer_callback_query(call.id,"🐊 Yaqin orada!",show_alert=True)
    elif d=="show_profile": bot.answer_callback_query(call.id,f"👤 {ud['name']}\n💵 {ud['balance']:,} so'm",show_alert=True)
    elif d=="get_daily_bonus":
        t=int(time.time())
        if t-ud.get("last_bonus",0)<86400:
            rem=86400-(t-ud.get("last_bonus",0)); h,mn=divmod(rem//60,60)
            bot.answer_callback_query(call.id,f"❌ {h} soat {mn} daqiqadan keyin!",show_alert=True); return
        amt=random.randint(1000,5000); ud["balance"]+=amt; ud["last_bonus"]=t; save_db()
        bot.answer_callback_query(call.id,f"🎁 +{amt:,} so'm!",show_alert=True); edit(menu_txt(ud),main_kb(uid))
    elif d=="admin_dashboard" and uid==ADMIN_ID:
        kb=types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("📈 Aviator Cheat",callback_data="adm_set_kf"),
               types.InlineKeyboardButton("💰 Pul Qo'shish",callback_data="adm_add_money"),
               types.InlineKeyboardButton("💸 Pul Olish",callback_data="adm_remove_money"),
               types.InlineKeyboardButton("🎟 Promokod Yaratish",callback_data="adm_create_promo"),
               types.InlineKeyboardButton("📋 Promokodlar",callback_data="adm_list_promos"),
               types.InlineKeyboardButton("🔄 Hammani 10k",callback_data="adm_reset"),
               types.InlineKeyboardButton("📊 Foydalanuvchilar",callback_data="adm_stats"),
               types.InlineKeyboardButton("⬅ Menyu",callback_data="to_main"))
        edit(f"👑 *ADMIN — {BOT_NAME}*\n\n👥 {len(DB['users'])} ta user\n💵 {sum(u.get('balance',0) for u in DB['users'].values()):,} so'm\n🎟 {len(DB.get('promocodes',{}))} ta promo",kb)
    elif d=="adm_set_kf" and uid==ADMIN_ID: ud["state"]="set_kf"; save_db(); edit("🚀 Keyingi kf yozing (3.45):")
    elif d=="adm_add_money" and uid==ADMIN_ID: ud["state"]="add_money"; save_db(); edit("💰 `ID summa` yozing:",parse_mode="Markdown")
    elif d=="adm_remove_money" and uid==ADMIN_ID: ud["state"]="remove_money"; save_db(); edit("💸 `ID summa` yozing:",parse_mode="Markdown")
    elif d=="adm_create_promo" and uid==ADMIN_ID: ud["state"]="create_promo"; save_db(); edit("🎟 *Promokod*\n\n`KOD SUMMA` yoki `SUMMA`\nMasalan: `VIP2024 50000`",parse_mode="Markdown")
    elif d=="adm_list_promos" and uid==ADMIN_ID:
        promos=DB.get("promocodes",{})
        if not promos: bot.answer_callback_query(call.id,"❌ Promokod yo'q!",show_alert=True); return
        lines=[f"🎟 *Promokodlar ({len(promos)} ta):*\n"]+[f"• `{c}` — {i['amount']:,} so'm | {len(i.get('used_by',[]))} marta" for c,i in promos.items()]
        kb=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🗑 O'chir",callback_data="adm_clear_promos"),types.InlineKeyboardButton("⬅ Admin",callback_data="admin_dashboard"))
        edit("\n".join(lines),kb)
    elif d=="adm_clear_promos" and uid==ADMIN_ID:
        DB["promocodes"]={}; save_db(); bot.answer_callback_query(call.id,"🗑 O'chirildi!",show_alert=True); edit("✅ Tozalandi.",back_kb("admin_dashboard"))
    elif d=="adm_reset" and uid==ADMIN_ID:
        for u in DB["users"].values(): u["balance"]=10000
        save_db(); bot.answer_callback_query(call.id,"🔄 Hammaning balansi 10,000!",show_alert=True)
    elif d=="adm_stats" and uid==ADMIN_ID:
        lines=["👥 *Foydalanuvchilar:*\n"]+[f"• `{i}` — {u.get('name','?')} — {u.get('balance',0):,} so'm" for i,u in list(DB["users"].items())[-20:]]
        edit("\n".join(lines),back_kb("admin_dashboard"))
    elif d=="use_promo": ud["state"]="enter_promo"; save_db(); edit("🎟 *PROMOKOD*\n\nKodingizni yozing:",back_kb())elif d=="prep_mines": edit(f"💣 *MINES*\n💵 Balans: *{ud['balance']:,} so'm*\n\nTikish:",bets_kb("m_bet_"))
    elif d.startswith("m_bet_"):
        bet=int(d.split("_")[2])
        if bet>ud["balance"]: bot.answer_callback_query(call.id,"❌ Balans yetarli emas!",show_alert=True); return
        ud["temp_bet"]=bet; save_db()
        kb=types.InlineKeyboardMarkup(row_width=3)
        kb.add(*[types.InlineKeyboardButton(f"💣 {b}",callback_data=f"m_bomb_{b}") for b in [1,3,5,10,24]])
        kb.add(types.InlineKeyboardButton("⬅ Orqaga",callback_data="prep_mines"))
        edit(f"💣 Tikilgan: *{bet:,} so'm*\n\nNechta mina?",kb)
    elif d.startswith("m_bomb_"):
        bombs=int(d.split("_")[2]); bet=ud.get("temp_bet")
        if not bet or bet>ud["balance"]: return
        ud["balance"]-=bet
        ud["mines_game"]={"bet":bet,"mines_count":bombs,"mines":random.sample(range(30),bombs),"opened":[],"current_kf":1.0,"payout":bet,"status":"playing"}
        ud["temp_bet"]=None; save_db(); show_mines(call.message,ud,uid)
    elif d.startswith("mine_open_"):
        mg=ud.get("mines_game")
        if not mg or mg["status"]!="playing": return
        idx=int(d.split("_")[2])
        if idx in mg["opened"]: return
        if idx in mg["mines"]: mg["status"]="lost"; save_db(); show_mines(call.message,ud,uid,lost=True); return
        mg["opened"].append(idx)
        c=1.0
        for i in range(len(mg["opened"])):
            sl=30-mg["mines_count"]-i
            if sl>0: c*=(30-i)/sl
        mg["current_kf"]=round(c*0.95,2); mg["payout"]=int(mg["bet"]*mg["current_kf"]); save_db()
        if len(mg["opened"])==30-mg["mines_count"]: ud["balance"]+=mg["payout"]; mg["status"]="won"; save_db(); show_mines(call.message,ud,uid,won=True); return
        show_mines(call.message,ud,uid)
    elif d=="mines_cashout":
        mg=ud.get("mines_game")
        if mg and mg["status"]=="playing" and mg["opened"]: ud["balance"]+=mg["payout"]; mg["status"]="won"; save_db(); show_mines(call.message,ud,uid,won=True)
    elif d=="prep_apple": edit(f"🍏 *APPLE*\n💵 Balans: *{ud['balance']:,} so'm*\n\nTikish:",bets_kb("ap_bet_"))
    elif d.startswith("ap_bet_"):
        bet=int(d.split("_")[2])
        if bet>ud["balance"]: bot.answer_callback_query(call.id,"❌ Balans kam!",show_alert=True); return
        ud["balance"]-=bet
        grid=[]
        for r in range(13):
            items=["good"]*5
            for bi in random.sample(range(5),1 if r<4 else 2 if r<8 else 3 if r<11 else 4): items[bi]="bad"
            grid.append(items)
        ud["apple_game"]={"grid":grid,"current_row":0,"bet":bet,"payout":bet}; save_db(); show_apple(call.message,ud,uid)
    elif d.startswith("ap_select_"):
        ag=ud.get("apple_game")
        if not ag: return
        idx=int(d.split("_")[2])
        if ag["grid"][ag["current_row"]][idx]=="bad":
            ud["apple_game"]=None; save_db()
            edit("💀 *Chirigan olma!*",types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🍏 Qayta",callback_data="prep_apple"),types.InlineKeyboardButton("⬅ Menyu",callback_data="to_main"))); return
        ag["payout"]=int(ag["bet"]*COEFFS[ag["current_row"]]); ag["current_row"]+=1; save_db()
        if ag["current_row"]==13:
            ud["balance"]+=ag["payout"]; ud["apple_game"]=None; save_db()
            edit(f"👑 *JACKPOT!*\n+{ag['payout']:,} so'm!\n💵 Balans: *{ud['balance']:,} so'm*",main_kb(uid)); return
        show_apple(call.message,ud,uid)
    elif d=="ap_cashout" and ud.get("apple_game"):
        ag=ud["apple_game"]; ud["balance"]+=ag["payout"]; ud["apple_game"]=None; save_db()
        edit(f"💰 *Pul yechildi!*\n+{ag['payout']:,} so'm\n💵 Balans: *{ud['balance']:,} so'm*",main_kb(uid))
    elif d=="prep_aviator":
        if not DB["settings"].get("next_aviator"): DB["settings"]["next_aviator"]=round(random.uniform(1.1,4.5),2); save_db()
        h=" | ".join([f"x{h}" for h in DB["settings"].get("aviator_history",[1.2,2.5])[-5:]])
        cheat=f"🔮 *CHEAT: x{DB['settings']['next_aviator']}*\n\n" if uid==ADMIN_ID else ""
        edit(f"📊 *Tarix:* [{h}]\n\n{cheat}🚀 *AVIATOR*\n💵 Balans: *{ud['balance']:,} so'm*\n\nTikish:",bets_kb("av_bet_"))
    elif d.startswith("av_bet_"):
        bet=int(d.split("_")[2])
        if bet>ud["balance"]: bot.answer_callback_query(call.id,"❌ Balans kam!",show_alert=True); return
        ud["temp_bet"]=bet; save_db()
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("📈 Auto x1.5",callback_data="av_mode_1.5"),
               types.InlineKeyboardButton("📈 Auto x2.0",callback_data="av_mode_2.0"),
               types.InlineKeyboardButton("📈 Auto x3.0",callback_data="av_mode_3.0"),
               types.InlineKeyboardButton("🔥 Qo'lda",callback_data="av_mode_manual"))
        edit(f"🚀 Tikilgan: *{bet:,} so'm*\n\nRejim:",kb)
    elif d.startswith("av_mode_"):
        mode=d.split("_")[2]; bet=ud.get("temp_bet")
        if not bet or bet>ud["balance"]: return
        ud["balance"]-=bet; crash=DB["settings"].get("next_aviator",2.0); DB["settings"]["next_aviator"]=None
        DB["settings"].setdefault("aviator_history",[]).append(crash)
        if len(DB["settings"]["aviator_history"])>10: DB["settings"]["aviator_history"].pop(0)
        ud["aviator_game"]={"bet":bet,"current_win":1.0,"crash":crash,"auto_co":None if mode=="manual" else float(mode),"status":"flying"}
        ud["temp_bet"]=None; save_db(); Thread(target=run_aviator,args=(cid,mid,uid),daemon=True).start()
    elif d=="av_cashout_manual":
        ag=ud.get("aviator_game")
        if ag and ag["status"]=="flying":
            win=int(ag["bet"]*ag["current_win"]); ag["status"]="cashout"; ud["balance"]+=win; ud["aviator_game"]=None; save_db()
            edit(f"💰 *CASHOUT!*\n+{win:,} so'm (x{ag['current_win']})\n💵 Balans: *{ud['balance']:,} so'm*",
                 types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 Qayta",callback_data="prep_aviator"),types.InlineKeyboardButton("⬅ Menyu",callback_data="to_main")))def show_mines(mo, ud, uid, lost=False, won=False):
    mg=ud["mines_game"]; kb=types.InlineKeyboardMarkup(row_width=5); btns=[]
    for i in range(30):
        if lost: btns.append(types.InlineKeyboardButton("💥" if i in mg["mines"] else "💎" if i in mg["opened"] else "⬜",callback_data="lock"))
        elif won: btns.append(types.InlineKeyboardButton("💣" if i in mg["mines"] else "💎",callback_data="lock"))
        else:
            if i in mg["opened"]: btns.append(types.InlineKeyboardButton("💎",callback_data="lock"))
            else: btns.append(types.InlineKeyboardButton("🔴" if uid==ADMIN_ID and i in mg["mines"] else "❓",callback_data=f"mine_open_{i}"))
    kb.add(*btns)
    if not lost and not won:
        if mg["opened"]: kb.add(types.InlineKeyboardButton(f"💰 Yechish ({mg['payout']:,} so'm)",callback_data="mines_cashout"))
        kb.add(types.InlineKeyboardButton("⬅ Chiqish",callback_data="to_main"))
    else: kb.add(types.InlineKeyboardButton("🔄 Qayta",callback_data="prep_mines"),types.InlineKeyboardButton("⬅ Menyu",callback_data="to_main"))
    txt="💥 *MAG'LUBIYAT!*\n💵 Balans: *{:,} so'm*".format(ud["balance"]) if lost else "👑 *G'ALABA!*\n+{:,} so'm!\n💵 Balans: *{:,} so'm*".format(mg["payout"],ud["balance"]) if won else f"💣 *MINES*\n📈 x{mg['current_kf']} | Yutuq: *{mg['payout']:,} so'm*\n✅ {len(mg['opened'])} ta ochilgan"
    try: bot.edit_message_text(txt,mo.chat.id,mo.message_id,parse_mode="Markdown",reply_markup=kb)
    except: pass

def show_apple(mo, ud, uid):
    ag=ud["apple_game"]; kb=types.InlineKeyboardMarkup(row_width=6)
    for ri in range(12,-1,-1):
        row=[types.InlineKeyboardButton(f"x{COEFFS[ri]}",callback_data="lock")]
        for ci in range(5):
            if ri<ag["current_row"]: row.append(types.InlineKeyboardButton("✅",callback_data="lock"))
            elif ri==ag["current_row"]: row.append(types.InlineKeyboardButton("🍏" if uid==ADMIN_ID and ag["grid"][ri][ci]=="good" else "🔻" if uid==ADMIN_ID else "🟫",callback_data=f"ap_select_{ci}"))
            else: row.append(types.InlineKeyboardButton("🔒",callback_data="lock"))
        kb.row(*row)
    if ag["current_row"]>0: kb.add(types.InlineKeyboardButton(f"💰 Yechish ({ag['payout']:,} so'm)",callback_data="ap_cashout"))
    kb.add(types.InlineKeyboardButton("⬅ Chiqish",callback_data="to_main"))
    try: bot.edit_message_text(f"🍏 *APPLE OF FORTUNE*\n📊 Qator: *{ag['current_row']+1}/13*\n💰 Yutuq: *{ag['payout']:,} so'm*",mo.chat.id,mo.message_id,parse_mode="Markdown",reply_markup=kb)
    except: pass

def run_aviator(chat_id, message_id, uid):
    for _ in range(60):
        time.sleep(0.6)
        ud=DB["users"].get(uid)
        if not ud or not ud.get("aviator_game") or ud["aviator_game"]["status"]!="flying": break
        ag=ud["aviator_game"]; ag["current_win"]=round(ag["current_win"]+random.uniform(0.1,0.22),2)
        back=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 Qayta",callback_data="prep_aviator"),types.InlineKeyboardButton("⬅ Menyu",callback_data="to_main"))
        if ag["auto_co"] and ag["current_win"]>=ag["auto_co"] and ag["current_win"]<ag["crash"]:
            w=int(ag["bet"]*ag["auto_co"]); ag["status"]="cashout"; ud["balance"]+=w; ud["aviator_game"]=None; save_db()
            try: bot.edit_message_text(f"🤖 *AUTO CASHOUT!*\n+{w:,} so'm (x{ag['auto_co']})\n💵 Balans: *{ud['balance']:,} so'm*",chat_id,message_id,parse_mode="Markdown",reply_markup=back)
            except: pass
            break
        if ag["current_win"]>=ag["crash"]:
            ud["aviator_game"]=None; save_db()
            try: bot.edit_message_text(f"💥 *BOOM! x{ag['crash']}*\n💵 Balans: *{ud['balance']:,} so'm*",chat_id,message_id,parse_mode="Markdown",reply_markup=back)
            except: pass
            break
        kb=types.InlineKeyboardMarkup()
        if ag["auto_co"]: kb.add(types.InlineKeyboardButton(f"🎯 Auto: x{ag['auto_co']} | x{ag['current_win']}",callback_data="lock"))
        else: kb.add(types.InlineKeyboardButton(f"🛑 CASHOUT ({int(ag['bet']*ag['current_win']):,} so'm)",callback_data="av_cashout_manual"))
        try: bot.edit_message_text(f"✈️ *AVIATOR*\n📈 Kf: *x{ag['current_win']}*",chat_id,message_id,parse_mode="Markdown",reply_markup=kb)
        except: pass

app=Flask(__name__)

@app.route('/')
def home(): return f"✅ {BOT_NAME} | Users: {len(DB['users'])}"

if __name__=='__main__':
    load_db()
    port=int(os.environ.get("PORT",10000))
    Thread(target=lambda: app.run(host="0.0.0.0",port=port),daemon=True).start()
    bot.infinity_polling(skip_pending=True)
