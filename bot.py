import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# ================== CONFIG ==================
BOT_TOKEN = "8260168982:AAEy-YQDWa-yTqJKmsA_yeSuNtZb8qNeHAI"
OWNER_ID = 7635779264  # ايديك فقط
# ============================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

active_chats = set()

# ================== الأذكار ==================
MORNING_DUA = """🌅 أذكار الصباح

🤍 نبضة حياة
"""

EVENING_DUA = """🌙 أذكار المساء

🤍 نبضة حياة
"""

# ================== /start ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # الخاص: الجميع
    if chat.type == "private":
        active_chats.add(chat.id)

    # المجموعات: أنت + الأدمن فقط
    elif chat.type in ("group", "supergroup"):
        if user.id != OWNER_ID:
            return
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status not in ("administrator", "creator"):
            return
        active_chats.add(chat.id)

    await update.message.reply_text(
        "🤖 بوت أذكار الصباح والمساء\n\n"
        "🤲 لا تنسوا الدعاء لمن كان سبباً في هذا الخير: @mohamedelhocine\n"
        "🛠️ الصانع: @Mik_emm"
    )

# ================== الإرسال ==================
async def broadcast(app: Application, text: str):
    for chat_id in list(active_chats):
        try:
            await app.bot.send_message(chat_id, text)
        except Exception as e:
            logging.warning(f"فشل الإرسال إلى {chat_id}: {e}")
            active_chats.discard(chat_id)

async def send_morning(app: Application):
    await broadcast(app, MORNING_DUA)

async def send_evening(app: Application):
    await broadcast(app, EVENING_DUA)

# ================== نبضة حياة ==================
def heartbeat():
    logging.info("🤍 bot alive")

# ================== MAIN ==================
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    scheduler = AsyncIOScheduler(timezone="Africa/Cairo")
    scheduler.add_job(send_morning, "cron", hour=8, minute=30, args=[app])
    scheduler.add_job(send_evening, "cron", hour=16, minute=0, args=[app])
    scheduler.add_job(heartbeat, "interval", minutes=10)
    scheduler.start()

    logging.info("✅ البوت شغال بـ Polling")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
