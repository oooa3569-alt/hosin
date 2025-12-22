import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.background import BackgroundScheduler

# ================= CONFIG =================
BOT_TOKEN = "8040860578:AAHKb0r7J7FBdu5OqA0tg-XbvsLR0MGQ4b4"
OWNER_ID = 7635779264

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://hosin-q20k.onrender.com" + WEBHOOK_PATH
PORT = 10000  # Render port

# ========================================
active_chats = set()

MORNING_DUA = """
🌅 أذكار الصباح

أَعُوذُ بِاللهِ مِنْ الشَّيْطَانِ الرَّجِيمِ
اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ

قُلْ هُوَ ٱللَّهُ أَحَدٌ (3 مرات)
قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ (3 مرات)
قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ (3 مرات)

سُبْحـانَ اللهِ وَبِحَمْـدِهِ (100)

🤍 نبضة حياة
"""

EVENING_DUA = """
🌙 أذكار المساء

أَعُوذُ بِاللهِ مِنْ الشَّيْطَانِ الرَّجِيمِ
اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ

قُلْ هُوَ ٱللَّهُ أَحَدٌ (3 مرات)
قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ (3 مرات)
قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ (3 مرات)

سُبْحـانَ اللهِ وَبِحَمْـدِهِ (100)

🤍 نبضة حياة
"""

# ================= APP =================
app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()
scheduler = BackgroundScheduler()

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # ====== الخاص: الجميع ======
    if chat.type == "private":
        active_chats.add(chat.id)

        await update.message.reply_text(
            "🤖 بوت أذكار الصباح والمساء\n\n"
           
            "🤲 لا تنسوا الدعاء لمن كان سبباً في هذا الخير: @mohamedelhocine\n"
            "🛠️ الصانع: @Mik_emm"
        )
        return

    # ====== المجموعات ======
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin = member.status in ["administrator", "creator"]
    except:
        is_admin = False

    if is_admin or user.id == OWNER_ID:
        active_chats.add(chat.id)
        await update.message.reply_text(
            "✅ تم تفعيل أذكار الصباح والمساء في هذه المجموعة."
        )
    else:
        await update.message.reply_text(
            "⛔ هذا الأمر مخصص للمشرفين فقط."
        )

# ================= BROADCAST =================
async def broadcast(text):
    for chat_id in list(active_chats):
        try:
            await application.bot.send_message(chat_id, text)
        except:
            pass

def send_morning():
    asyncio.run(broadcast(MORNING_DUA))

def send_evening():
    asyncio.run(broadcast(EVENING_DUA))

# ================= WEBHOOK =================
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.create_task(application.process_update(update))
    return "ok"

# ================= MAIN =================
async def main():
    application.add_handler(CommandHandler("start", start))

    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)
    await application.start()

    # ⏰ 08:30 صباحاً
    scheduler.add_job(send_morning, "cron", hour=8, minute=30)

    # ⏰ 16:00 مساءً
    scheduler.add_job(send_evening, "cron", hour=16, minute=0)

    scheduler.start()

if __name__ == "__main__":
    asyncio.run(main())
    app.run(host="0.0.0.0", port=PORT)

