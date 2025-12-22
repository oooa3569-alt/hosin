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
# ===========================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

active_chats = set()

MORNING_DUA = """🌅 أذكار الصباح

أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ
﴿ اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ﴾

🤍 نبضة حياة
"""

EVENING_DUA = """🌙 أذكار المساء

أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ
﴿ اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ﴾

🤍 نبضة حياة
"""

# ================== APP ==================
app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()
scheduler = BackgroundScheduler()

# 🔑 event loop ثابت (الحل الجذري)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ================== START ==================
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
       
        "🤲 لا تنسوا الدعاء لمن كان سبباً في هذا الخير: @mohamedelhocine\n"
        "🛠️ الصانع: @Mik_emm"
    )

# ================== BROADCAST ==================
async def broadcast(text):
    for chat_id in list(active_chats):
        try:
            await application.bot.send_message(
                chat_id=chat_id,
                text=text,
                disable_web_page_preview=True
            )
            await asyncio.sleep(0.4)
        except Exception as e:
            logging.warning(f"فشل الإرسال إلى {chat_id}: {e}")
            active_chats.discard(chat_id)

async def send_morning():
    await broadcast(MORNING_DUA)

async def send_evening():
    await broadcast(EVENING_DUA)

# ================== HEARTBEAT ==================
def heartbeat():
    logging.info("❤️ Heartbeat: bot alive")

# ================== WEBHOOK ==================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)

    asyncio.run_coroutine_threadsafe(
        application.process_update(update),
        loop
    )
    return "OK", 200

# ================== SCHEDULER ==================
def schedule_jobs():
    scheduler.add_job(
        lambda: asyncio.run_coroutine_threadsafe(send_morning(), loop),
        "cron",
        hour=8,
        minute=30,
        timezone="Africa/Cairo"
    )

    scheduler.add_job(
        lambda: asyncio.run_coroutine_threadsafe(send_evening(), loop),
        "cron",
        hour=16,
        minute=0,
        timezone="Africa/Cairo"
    )

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

    port = int(os.environ.get("PORT", 8443))
    app.run(host="0.0.0.0", port=port)

