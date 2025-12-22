import asyncio
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ================== CONFIG ==================
BOT_TOKEN = "8040860578:AAHKb0r7J7FBdu5OqA0tg-XbvsLR0MGQ4b4"
WEBHOOK_URL = "https://hosin-q20k.onrender.com"

# ===========================================
active_chats = set()

MORNING_DUA = """
🌅 أذكار الصباح

أَعُوذُ بِاللهِ مِنْ الشَّيْطَانِ الرَّجِيمِ
اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ...

بِسْمِ اللهِ الرَّحْمنِ الرَّحِيم
قُلْ هُوَ ٱللَّهُ أَحَدٌ (3 مرات)
قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ (3 مرات)
قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ (3 مرات)

أَصْـبَحْنا وَأَصْـبَحَ المُـلْكُ لله
حَسْبِـيَ اللّهُ لا إلهَ إلاّ هُوَ
سُبْحـانَ اللهِ وَبِحَمْـدِهِ (100)

 """

EVENING_DUA = """
🌙 أذكار المساء

أَعُوذُ بِاللهِ مِنْ الشَّيْطَانِ الرَّجِيمِ
اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ...

آمَنَ الرَّسُولُ بِمَا أُنْزِلَ إِلَيْهِ (آخر البقرة)

قُلْ هُوَ ٱللَّهُ أَحَدٌ (3 مرات)
قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ (3 مرات)
قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ (3 مرات)

أَمْسَيْـنا وَأَمْسـى المـلكُ لله
حَسْبِـيَ اللّهُ لا إلهَ إلاّ هُوَ
سُبْحـانَ اللهِ وَبِحَمْـدِهِ (100)

 
"""

# ================== APP ==================
app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()
scheduler = BackgroundScheduler()

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
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
        except:
            pass

async def send_morning():
    await broadcast(MORNING_DUA)

async def send_evening():
    await broadcast(EVENING_DUA)

# ================== WEBHOOK ==================
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.create_task(application.process_update(update))
    return "ok"

# ================== MAIN ==================
if __name__ == "__main__":
    application.add_handler(CommandHandler("start", start))

    # ⏰ أذكار الصباح: 08:30
    scheduler.add_job(
        lambda: asyncio.run(send_morning()),
        "cron",
        hour=8,
        minute=30
    )

    # ⏰ أذكار المساء: 16:00
    scheduler.add_job(
        lambda: asyncio.run(send_evening()),
        "cron",
        hour=16,
        minute=0
    )

    scheduler.start()

    asyncio.run(application.bot.set_webhook(WEBHOOK_URL))
    app.run(host="0.0.0.0", port=8443)

