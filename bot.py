import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# ================== CONFIG ==================
BOT_TOKEN = "8260168982:AAEy-YQDWa-yTqJKmsA_yeSuNtZb8qNeHAI"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://hosin-q20k.onrender.com" + WEBHOOK_PATH
OWNER_ID = 7635779264
TIMEZONE = "Africa/Cairo"
# ===========================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = Bot(BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()
scheduler = BackgroundScheduler(timezone=TIMEZONE)

active_chats = set()

# ================== ADHKAR ==================
MORNING_DUA = "🌅 أذكار الصباح\n\n🤍 نبضة حياة"
EVENING_DUA = "🌙 أذكار المساء\n\n🤍 نبضة حياة"
# ===========================================

# ================== COMMAND ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        active_chats.add(chat.id)
        logger.info(f"Private chat added: {chat.id}")
    elif chat.type in ("group", "supergroup"):
        if user.id != OWNER_ID:
            await update.message.reply_text("❌ هذا البوت للمالك فقط في المجموعات!")
            logger.warning(f"Unauthorized group access attempt by {user.id}")
            return
        active_chats.add(chat.id)
        logger.info(f"Group chat added: {chat.id}")

    await update.message.reply_text(
        "🤖 بوت أذكار الصباح والمساء\n\n"
        "🤲 لا تنسوا الدعاء لمن كان سبباً في هذا الخير\n"
        "🛠️ الصانع: @Mik_emm"
    )

# ================== SENDING ==================
async def broadcast(text):
    success = 0
    failed = 0
    
    for chat_id in list(active_chats):
        try:
            await bot.send_message(chat_id, text)
            success += 1
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"Failed to send to {chat_id}: {str(e)}")
            active_chats.discard(chat_id)
            failed += 1
    
    logger.info(f"Broadcast completed: {success} sent, {failed} failed")

def send_morning():
    logger.info("Sending morning athkar...")
    asyncio.run(broadcast(MORNING_DUA))

def send_evening():
    logger.info("Sending evening athkar...")
    asyncio.run(broadcast(EVENING_DUA))

def heartbeat():
    logger.info(f"❤️ Heartbeat: bot alive, active chats: {len(active_chats)}")

# ================== WEBHOOK ==================
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, bot)
        
        # إنشاء حلقة جديدة للمعالجة
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.process_update(update))
        loop.close()
        
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 400

@app.route("/")
def index():
    return f"Bot is running. Active chats: {len(active_chats)}", 200

@app.route("/status")
def status():
    return {
        "status": "running",
        "active_chats": len(active_chats),
        "webhook_url": WEBHOOK_URL,
        "bot_token": "..." + BOT_TOKEN[-4:]  # إظهار آخر 4 أرقام فقط للأمان
    }, 200

# ================== MAIN ==================
def main():
    # إضافة handler للبداية
    application.add_handler(CommandHandler("start", start))
    
    # إعداد المهام المجدولة
    scheduler.add_job(
        send_morning, 
        trigger=CronTrigger(hour=8, minute=30, timezone=TIMEZONE),
        id="morning_athkar"
    )
    scheduler.add_job(
        send_evening, 
        trigger=CronTrigger(hour=16, minute=0, timezone=TIMEZONE),
        id="evening_athkar"
    )
    scheduler.add_job(
        heartbeat, 
        "interval", 
        minutes=10,
        id="heartbeat"
    )
    
    scheduler.start()
    
    # إعداد ويب هوك
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.set_webhook(WEBHOOK_URL))
        logger.info(f"Webhook set to: {WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
    
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
