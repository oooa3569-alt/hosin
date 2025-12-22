import asyncio
from datetime import time
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# ================== الإعدادات ==================
BOT_TOKEN = "8260168982:AAEy-YQDWa-yTqJKmsA_yeSuNtZb8qNeHAI"
OWNER_ID = 7635779264

WEBHOOK_URL = "https://hosin-q20k.onrender.com/webhook"
SECRET_TOKEN = "my_secret_token"

PORT = 10000

# ================== الأذكار ==================
MORNING_AZKAR = """
🌅 أذكار الصباح

☀️ اللّهـمَّ أَنْتَ رَبِّـي لا إلهَ إلاّ أَنْتَ
📿 سبحان الله وبحمده (100 مرة)
"""

EVENING_AZKAR = """
🌙 أذكار المساء

🌌 اللّهـمَّ أَمْسَيْنَا وَأَمْسَى المُلكُ لله
📿 سبحان الله وبحمده (100 مرة)
"""

# ================== Flask ==================
app = Flask(__name__)

# ================== Telegram App ==================
application = Application.builder().token(BOT_TOKEN).build()

# ================== أمر /start ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # في الجروبات: فقط أنت أو الأدمن
    if chat.type != "private":
        member = await context.bot.get_chat_member(chat.id, user.id)
        if user.id != OWNER_ID and member.status not in ["administrator", "creator"]:
            return

    # حفظ الشات لإرسال الأذكار
    context.application.chat_data[chat.id] = True

    await update.message.reply_text(
        "🤖 بوت أذكار الصباح والمساء\n\n"
        "🤲 لا تنسوا الدعاء لمن كان سبباً في هذا الخير: @mohamedelhocine\n"
        "🛠️ الصانع: @Mik_emm"
    )

# ================== إرسال الأذكار ==================
async def send_morning(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in context.application.chat_data:
        try:
            await context.bot.send_message(chat_id, MORNING_AZKAR)
        except:
            pass

async def send_evening(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in context.application.chat_data:
        try:
            await context.bot.send_message(chat_id, EVENING_AZKAR)
        except:
            pass

# ================== Webhook ==================
@app.route("/webhook", methods=["POST"])
async def webhook():
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != SECRET_TOKEN:
        return "Unauthorized", 403

    update = Update.de_json(request.json, application.bot)
    await application.process_update(update)
    return "OK", 200

# ================== Health Check ==================
@app.route("/health")
def health():
    return "OK", 200

# ================== التشغيل ==================
async def main():
    application.add_handler(CommandHandler("start", start))

    application.job_queue.run_daily(
        send_morning,
        time(hour=8, minute=30)
    )

    application.job_queue.run_daily(
        send_evening,
        time(hour=16, minute=0)
    )

    await application.initialize()
    await application.bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=SECRET_TOKEN,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    print("🚀 Bot is running...")
    asyncio.run(main())
    app.run(host="0.0.0.0", port=PORT)
