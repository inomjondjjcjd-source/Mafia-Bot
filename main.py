from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8558624417:AAF2U4kshCCZG6PgUEsswyIs_AHq6IGySSE"

menu = ReplyKeyboardMarkup(
    [
        ["🎮 Game 1", "🎯 Game 2"],
        ["💣 Mines", "👤 Profile"]
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 O'yin botiga xush kelibsiz!",
        reply_markup=menu
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🎮 Game 1":
        await update.message.reply_text("🚀 Game 1 ochildi")

    elif text == "🎯 Game 2":
        await update.message.reply_text("🔥 Game 2 ochildi")

    elif text == "💣 Mines":
        await update.message.reply_text("💣 Mines game")

    elif text == "👤 Profile":
        await update.message.reply_text(
            f"👤 Ism: {update.effective_user.first_name}"
        )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, buttons))

print("Bot ishladi...")
app.run_polling()
