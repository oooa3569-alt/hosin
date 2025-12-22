import asyncio
import logging
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ================== CONFIG ==================
BOT_TOKEN = "PUT_YOUR_TOKEN_HERE"
WEBHOOK_URL = "https://hosin-q20k.onrender.com/webhook"
OWNER_ID = 7635779264
# ===========================================

logging.basicConfig(level=logging.INFO)

active_chats = set()

MORNING_DUA = """🌅 أذكار الصباح

أَعُوذُ بِاللهِ مِنْ الشَّيْطَانِ الرَّجِيمِ
اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ...

     
"""

EVENING_DUA = """🌙 أذكار المساء

أَعُوذُ بِاللهِ مِنْ الشَّيْطَانِ الرَّجِيمِ
اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ...
    
"""

# ================== APP ==================
app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()
scheduler = BackgroundScheduler()

# 🔑 event loop ثابت
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
            await application.bot.send_message(chat_id, text)
        except Exception as e:
            logging.warning(f"Send failed {chat_id}: {e}")

async def send_morning():
    await broadcast(MORNING_DUA)

async def send_evening():
    await broadcast(EVENING_DUA)

# ================== HEARTBEAT ==================
def heartbeat():
    logging.info("🤍 Heartbeat: alive")

# ================== WEBHOOK ==================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)

    asyncio.run_coroutine_threadsafe(
        application.process_update(update),
        loop
    )

    return "ok"

# ================== MAIN ==================
if __name__ == "__main__":
    application.add_handler(CommandHandler("start", start))

    # 🔥 تشغيل التطبيق فعلياً
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())

    scheduler.add_job(lambda: asyncio.run(send_morning()), "cron", hour=8, minute=30)
    scheduler.add_job(lambda: asyncio.run(send_evening()), "cron", hour=16, minute=0)
    scheduler.add_job(heartbeat, "interval", minutes=10)

    scheduler.start()

    loop.run_until_complete(
        application.bot.set_webhook(WEBHOOK_URL)
    )

    app.run(host="0.0.0.0", port=8443)

