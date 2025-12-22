import asyncio
import logging
import os
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ================== CONFIG ==================
BOT_TOKEN = "8260168982:AAEy-YQDWa-yTqJKmsA_yeSuNtZb8qNeHAI"
WEBHOOK_URL = "https://hosin-q20k.onrender.com/webhook"
OWNER_ID = 7635779264
TIMEZONE = "Africa/Cairo"
# ===========================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

active_chats = set()

# ================== ADHKAR ==================
MORNING_DUA = """🌅 *أذكار الصباح* 🌅
(نصك كما هو)
"""

EVENING_DUA = """🌙 *أذكار المساء* 🌙
(نصك كما هو)
"""
# ===========================================

app = Flask(__name__)
scheduler = BackgroundScheduler(timezone=TIMEZONE)

application = Application.builder().token(BOT_TOKEN).build()

# 🔁 Event loop ثابت
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ================== COMMAND ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        active_chats.add(chat.id)

    elif chat.type in ("group", "supergroup"):
        if user.id != OWNER_ID:
            return
        active_chats.add(chat.id)

    await update.message.reply_text(
        "🤖 بوت أذكار الصباح والمساء\n\n"
        "🤲 لا تنسوا الدعاء لمن كان سبباً في هذا الخير\n"
        "🛠️ الصانع: @Mik_emm"
    )

# ================== BROADCAST ==================
async def broadcast(text):
    for chat_id in list(active_chats):
        try:
            await application.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            await asyncio.sleep(0.4)
        except Exception:
            active_chats.discard(chat_id)

async def send_morning():
    await broadcast(MORNING_DUA)

async def send_evening():
    await broadcast(EVENING_DUA)

# ================== HEARTBEAT ==================
def heartbeat():
    logging.info("❤️ Heartbeat: البوت يعمل")

# ================== WEBHOOK (SYNC ✔) ==================
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run_coroutine_threadsafe(
        application.process_update(update),
        loop
    )
    return "OK", 200

# ================== SCHEDULER ==================
def schedule_jobs():
    scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(send_morning(), loop),
                      "cron", hour=8, minute=30)
    scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(send_evening(), loop),
                      "cron", hour=16, minute=0)
    scheduler.add_job(heartbeat, "interval", minutes=10)
    scheduler.start()

# ================== MAIN ==================
if __name__ == "__main__":
    application.add_handler(CommandHandler("start", start))

    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())
    loop.run_until_complete(application.bot.set_webhook(WEBHOOK_URL))

    logging.info("✅ Webhook مضبوط والبوت شغال")

    schedule_jobs()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    asyncio.run(main())
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
