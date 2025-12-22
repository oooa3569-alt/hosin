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

# حل المشكلة: إنشاء Application بطريقة مختلفة
try:
    # الطريقة الجديدة للتهيئة
    application = Application.builder().token(BOT_TOKEN).build()
except TypeError:
    # إذا فشلت، نجرب طريقة بديلة
    from telegram.ext import Updater
    application = None  # سنستخدم Updater بدلاً من Application
    
bot = Bot(BOT_TOKEN)
scheduler = BackgroundScheduler(timezone=TIMEZONE)

active_chats = set()

# ================== ADHKAR ==================
MORNING_DUA = "🌅 أذكار الصباح\n\nسبحان الله وبحمده سبحان الله العظيم"
EVENING_DUA = "🌙 أذكار المساء\n\nسبحان الله وبحمده سبحان الله العظيم"
# ===========================================

# ================== COMMAND ==================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        active_chats.add(chat.id)
        logger.info(f"Private chat added: {chat.id}")
    elif chat.type in ("group", "supergroup"):
        if user.id != OWNER_ID:
            await update.message.reply_text("❌ هذا البوت للمالك فقط في المجموعات!")
            return
        active_chats.add(chat.id)
        logger.info(f"Group chat added: {chat.id}")

    await update.message.reply_text(
        "🤖 بوت أذكار الصباح والمساء\n\n"
        "✅ تم تفعيل الإشعارات اليومية\n"
        "⏰ مواعيد الإذكار:\n"
        "• الصباح: 8:30 صباحاً\n"
        "• المساء: 4:00 مساءً\n\n"
        "🤲 لا تنسوا الدعاء لمن كان سبباً في هذا الخير\n"
        "🛠️ الصانع: @Mik_emm"
    )

# ================== SENDING ==================
async def broadcast(text):
    if not active_chats:
        logger.warning("No active chats to broadcast")
        return
    
    success = 0
    failed = 0
    
    for chat_id in list(active_chats):
        try:
            await bot.send_message(chat_id, text)
            success += 1
            await asyncio.sleep(0.5)  # تقليل الضغط
        except Exception as e:
            logger.error(f"فشل الإرسال لـ {chat_id}: {e}")
            active_chats.discard(chat_id)
            failed += 1
    
    logger.info(f"✅ البث: {success} نجاح، {failed} فشل")

def send_morning():
    logger.info("🚀 إرسال أذكار الصباح...")
    try:
        asyncio.run(broadcast(MORNING_DUA))
    except Exception as e:
        logger.error(f"❌ خطأ في أذكار الصباح: {e}")

def send_evening():
    logger.info("🚀 إرسال أذكار المساء...")
    try:
        asyncio.run(broadcast(EVENING_DUA))
    except Exception as e:
        logger.error(f"❌ خطأ في أذكار المساء: {e}")

def heartbeat():
    logger.info(f"❤️ البوت يعمل، المحادثات النشطة: {len(active_chats)}")
    logger.info(f"⏰ المهام المجدولة: {len(scheduler.get_jobs())}")

# ================== WEBHOOK ==================
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, bot)
        
        # معالجة الأوامر يدوياً
        if update.message and update.message.text:
            if update.message.text.startswith('/start'):
                asyncio.run(start_command(update, None))
        
        return "OK", 200
    except Exception as e:
        logger.error(f"❌ خطأ في webhook: {e}")
        return "Error", 400

@app.route("/")
def index():
    return f"""
    <h1>🤖 بوت أذكار الصباح والمساء</h1>
    <p>✅ البوت يعمل بنجاح</p>
    <p>👥 المحادثات النشطة: {len(active_chats)}</p>
    <p>⏰ المهام المجدولة: {len(scheduler.get_jobs())}</p>
    <p>🔗 Webhook: {WEBHOOK_URL}</p>
    <hr>
    <p>🛠️ الصانع: @Mik_emm</p>
    """

@app.route("/status")
def status():
    return {
        "status": "running",
        "active_chats": len(active_chats),
        "jobs": len(scheduler.get_jobs()),
        "timezone": TIMEZONE,
        "bot_username": bot.get_me().username if hasattr(bot, 'get_me') else "Unknown"
    }

@app.route("/send_test")
def send_test():
    """لاختبار البث"""
    asyncio.run(broadcast("✅ رسالة اختبار من البوت"))
    return "✅ تم إرسال رسالة الاختبار"

# ================== MAIN ==================
def main():
    try:
        logger.info("🚀 بدء تشغيل البوت...")
        
        # إعداد المهام المجدولة
        scheduler.add_job(
            send_morning,
            trigger=CronTrigger(hour=6, minute=30, timezone=TIMEZONE),  # 8:30 بتوقيت مصر
            id="morning_athkar",
            replace_existing=True
        )
        
        scheduler.add_job(
            send_evening,
            trigger=CronTrigger(hour=16, minute=0, timezone=TIMEZONE),  # 4:00 مساءً
            id="evening_athkar",
            replace_existing=True
        )
        
        scheduler.add_job(
            heartbeat,
            "interval",
            minutes=5,
            id="heartbeat",
            replace_existing=True
        )
        
        scheduler.start()
        logger.info(f"✅ تم جدولة {len(scheduler.get_jobs())} مهمة")
        
        # إعداد ويب هوك
        bot.set_webhook(WEBHOOK_URL)
        logger.info(f"✅ تم تعيين Webhook: {WEBHOOK_URL}")
        
        # عرض معلومات البوت
        bot_info = bot.get_me()
        logger.info(f"🤖 البوت: @{bot_info.username} ({bot_info.id})")
        
        # تشغيل الخادم
        port = int(os.environ.get("PORT", 10000))
        logger.info(f"🌐 تشغيل الخادم على المنفذ {port}")
        app.run(host="0.0.0.0", port=port, debug=False)
        
    except Exception as e:
        logger.error(f"❌ خطأ فادح: {e}")
        scheduler.shutdown()

if __name__ == "__main__":
    main()
