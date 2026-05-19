import os, json, random, time, urllib.request, telebot, threading
from flask import Flask
from telebot import types

TOKEN = "8549694875:AAHk1hym-q21qQ8RttgPD0pZdpht5XpP3pA"
KVDB_URL = "https://kvdb.io/MN86yM86yM86yM86yM86yM/shox_sup_v10_db"
bot = telebot.TeleBot(TOKEN)
DB = {"users": {}}

def sync_db():
    try:
        with urllib.request.urlopen(KVDB_URL, timeout=5) as r: DB.update(json.loads(r.read()))
    except: pass

@bot.message_handler(commands=['start'])
def start(m):
    sync_db()
    uid = str(m.from_user.id)
    if uid not in DB["users"]: DB["users"][uid] = {"bal": 10000}
    bot.send_message(m.chat.id, f"👑 *MARTIN LIVE*\n\n💵 Balans: {DB['users'][uid]['bal']} so'm", parse_mode="Markdown")

app = Flask(__name__)
@app.route('/')
def home(): return "Martin Live is Alive!"

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
    bot.infinity_polling(skip_pending=True)
    
