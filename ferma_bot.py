import os
import sys
import subprocess
import json
from threading import Thread
from flask import Flask, render_template_string, jsonify, request

# 📦 KERAKLI KUTUBXONALARNI AVTO-O'RNATISH
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.1.1", "Flask"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
    from telegram.ext import Application, CommandHandler, ContextTypes

# 🔑 ASOSIY SOZLAMALAR
TOKEN = "8829005476:AAGc-b-dQ1NJycS3vMf0-tRn7H15y4kFtn4"
DATA_FILE = "webapp_db.json"
USER_DATA = {}

# 🌐 FLASK WEB SERVER (O'yin sayti shu yerda ishlaydi)
app = Flask(__name__)

def load_data():
    global USER_DATA
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                USER_DATA = {int(k): v for k, v in json.load(f).items()}
        except: USER_DATA = {}

def save_data():
    try:
        to_save = {str(k): v for k, v in USER_DATA.items()}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=4)
    except: pass

def get_user(user_id, username="Foydalanuvchi"):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "name": username,
            "gold": 0,
            "tap_power": 1
        }
        save_data()
    return USER_DATA[user_id]

# 🐉 O'YIN SAYTINING DIZAYNI (HTML + CSS + JAVASCRIPT)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Ajdaho Fermasi</title>
    <style>
        body {
            background: linear-gradient(135deg, #112233, #1b4d3e);
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            margin: 0;
            padding: 0;
            user-select: none;
            -webkit-user-select: none;
            overflow: hidden;
        }
        .container {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 100vh;
            padding: 20px;
            box-sizing: border-box;
        }
        .header {
            margin-top: 10px;
        }
        .header h1 {
            font-size: 24px;
            color: #f1c40f;
            margin: 0;
            text-shadow: 0px 4px 10px rgba(0,0,0,0.5);
        }
        .balance-section {
            font-size: 36px;
            font-weight: bold;
            margin: 20px 0;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .gold-icon {
            color: #f39c12;
            animation: pulse 2s infinite;
        }
        /* 👇 KATTA BOSISH TUGMASI (AJDAHO MULTFILM ELEMENTI) */
        .circle-btn {
            width: 220px;
            height: 220px;
            border-radius: 50%;
            background: radial-gradient(circle, #2ecc71, #27ae60);
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0px 0px 30px rgba(46, 204, 113, 0.6), inset 0px 0px 20px rgba(255,255,255,0.4);
            cursor: pointer;
            transform: scale(1);
            transition: transform 0.1s ease;
            position: relative;
        }
        .circle-btn:active {
            transform: scale(0.92);
            background: radial-gradient(circle, #27ae60, #1e8449);
        }
        .circle-btn img {
            width: 140px;
            height: 140px;
            pointer-events: none;
        }
        /* 🚀 UPGRADE TUGMASI */
        .upgrade-btn {
            background: linear-gradient(90deg, #f39c12, #d35400);
            border: none;
            color: white;
            padding: 15px 30px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 50px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            cursor: pointer;
            margin-bottom: 20px;
            width: 100%;
            max-width: 300px;
            align-self: center;
        }
        .upgrade-btn:active {
            transform: scale(0.98);
        }
        .info-text {
            font-size: 14px;
            color: #bdc3c7;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        /* Klik effekt raqamlari (+5 yozuvi chiqib yo'qolishi) */
        .click-effect {
            position: absolute;
            color: #f1c40f;
            font-size: 28px;
            font-weight: bold;
            pointer-events: none;
            animation: floatUp 0.6s ease-out forwards;
        }
        @keyframes floatUp {
            0% { opacity: 1; transform: translateY(0) scale(1); }
            100% { opacity: 0; transform: translateY(-100px) scale(1.2); }
        }
    </style>
</head>
<body>

    <div class="container">
        <div class="header">
            <h1>🐉 AJDAHO FERMASI 🐉</h1>
            <p class="info-text">Ekranga bosing va oltin yig'ing!</p>
        </div>

        <div class="balance-section">
            <span class="gold-icon">🪙</span>
            <span id="gold-balance">{{ gold }}</span>
        </div>

        <div class="circle-btn" id="tap-zone">
            <img src="https://img.icons8.com/clouds/250/dragon.png" alt="Ajdaho">
        </div>

        <div style="display: flex; flex-direction: column; align-items: center;">
            <button class="upgrade-btn" id="upgrade-click">
                ⚡️ Kuchaytirish (LVL: <span id="tap-lvl">{{ lvl }}</span>)<br>
                <span style="font-size: 12px; font-weight: normal;">Narxi: <span id="up-price">{{ up_price }}</span> 🪙</span>
            </button>
            <p class="info-text">Har bir bosish: +<span id="click-val">{{ click_val }}</span> oltin</p>
        </div>
    </div>

    <script>
        let userId = {{ user_id }};
        let gold = {{ gold }};
        let tapPower = {{ lvl }};
        let baseTapValue = 5; // Har bir bosishdagi standart oltin

        const goldBalance = document.getElementById('gold-balance');
        const tapZone = document.getElementById('tap-zone');
        const upgradeBtn = document.getElementById('upgrade-click');
        const tapLvl = document.getElementById('tap-lvl');
        const upPriceText = document.getElementById('up-price');
        const clickValText = document.getElementById('click-val');

        // Klik bosish mexanikasi
        tapZone.addEventListener('touchstart', (e) => {
            e.preventDefault();
            let currentClickGain = baseTapValue * tapPower;
            gold += currentClickGain;
            goldBalance.innerText = gold.toLocaleString();

            // Srazu ekranda chiroyli +5 yoki +10 effekti chiqishi
            let touch = e.touches[0];
            let effect = document.createElement('div');
            effect.className = 'click-effect';
            effect.innerText = '+' + currentClickGain;
            effect.style.left = touch.clientX + 'px';
            effect.style.top = touch.clientY + 'px';
            document.body.appendChild(effect);

            setTimeout(() => { effect.remove(); }, 600);

            // Ma'lumotni serverga (baza) yuborish
            fetch('/api/tap', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ user_id: userId, gold_add: currentClickGain })
            });
        });

        // Kuchaytirish sotib olish
        upgradeBtn.addEventListener('click', () => {
            let currentPrice = 1000 * tapPower;
            if (gold >= currentPrice) {
                gold -= currentPrice;
                tapPower += 1;
                
                goldBalance.innerText = gold.toLocaleString();
                tapLvl.innerText = tapPower;
                upPriceText.innerText = (1000 * tapPower).toLocaleString();
                clickValText.innerText = baseTapValue * tapPower;

                fetch('/api/upgrade', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ user_id: userId, price: currentPrice })
                });
            } else {
                alert("❌ Oltinlaringiz yetarli emas uka!");
            }
        });
    </script>
</body>
</html>
"""

@app.route('/game/<int:user_id>')
def game_page(user_id):
    load_data()
    ud = get_user(user_id)
    up_price = 1000 * ud["tap_power"]
    click_val = 5 * ud["tap_power"]
    return render_template_string(
        HTML_TEMPLATE, 
        user_id=user_id, 
        gold=ud["gold"], 
        lvl=ud["tap_power"], 
        up_price=up_price,
        click_val=click_val
    )

@app.route('/api/tap',彻 methods=['POST'])
def api_tap():
    data = request.json
    user_id = data.get("user_id")
    gold_add = data.get("gold_add", 5)
    ud = get_user(user_id)
    ud["gold"] += gold_add
    save_data()
    return jsonify({"status": "ok", "gold": ud["gold"]})

@app.route('/api/upgrade', methods=['POST'])
def api_upgrade():
    data = request.json
    user_id = data.get("user_id")
    price = data.get("price")
    ud = get_user(user_id)
    if ud["gold"] >= price:
        ud["gold"] -= price
        ud["tap_power"] += 1
        save_data()
    return jsonify({"status": "ok", "gold": ud["gold"], "lvl": ud["tap_power"]})


# 🤖 TELEGRAM BOT QISMI
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    get_user(user_id, first_name)
    
    # Render-dagi saytingiz manzili (O'zingizni Render Havolangizni qo'ysangiz ham bo'ladi)
    # Avtomatik aniqlaydi, agar bo'lmasa o'yin shu yerga ochiladi
    app_url = f"https://mafia-bot-1.onrender.com/game/{user_id}"
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 O'YINNI BOSHLASH (Web App)", web_app=WebAppInfo(url=app_url))]
    ])
    
    txt = f"👋 *Salom, {first_name}!*" + "\n\nAjdaho Fermasining rasmiy Mini App botiga xush kelibsiz! Pastdagi tugmani bosing va srazu Telegram ichida daxshatli Notcoin uslubidagi o'yin ochiladi! 🚀"
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=kb)

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def main():
    load_data()
    # Web serverni alohida potokda yoqamiz
    Thread(target=run_flask).start()
    
    # Telegram botni yoqish
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    
    print("Mini App veb-saytli bot muvaffaqiyatli ishga tushdi...")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
