import os
import logging
import asyncio
import threading
import time
from datetime import datetime, time as dt_time
import pytz
from flask import Flask, request, jsonify
from telegram import Bot

# ================== asyncio loop ثابت ==================
event_loop = asyncio.new_event_loop()

def run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=run_loop, args=(event_loop,), daemon=True).start()

# ================== إعدادات البوت ==================
TELEGRAM_TOKEN = "8260168982:AAEy-YQDWa-yTqJKmsA_yeSuNtZb8qNeHAI"
ADMIN_ID = 7635779264
GROUPS = ["-1002225164483", "-1002576714713"]
WEBHOOK_URL = "https://hosin-q20k.onrender.com/webhook"

# ================== التوقيت ==================
TIMEZONE = pytz.timezone("Africa/Algiers")
MORNING_TIME = dt_time(8, 30)
EVENING_TIME = dt_time(16, 0)
NIGHT_TIME = dt_time(23, 0)

# ================== الأذكار (كما هي) ==================
MORNING_DHIKR = """🌅 أذكار الصباح
...
لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير"""

EVENING_DHIKR = """🌇 أذكار المساء
...
لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير"""

SLEEP_DHIKR = """🌙 نام وأنت مغفور الذنب
...
غفر الله ذنوبه أو خطاياه وإن كانت مثل زبد البحر."""

# ================== رسائل الأوامر ==================
START_RESPONSE = """🤖 *بوت أذكار الصباح والمساء*

✅ *تم تفعيل الإشعارات اليومية*

⏰ *مواعيد الإذكار:*
• الصباح: 8:30 صباحاً
• المساء: 4:00 مساءً

🤲 *لا تنسوا الدعاء لمن كان سبباً في هذا الخير*
🛠️ *الصانع:* @Mik_emm"""

HELP_RESPONSE = """• /start - بدء البوت
• /help - المساعدة
• /status - حالة البوت

🛠️ الصانع: @Mik_emm"""

# ================== Flask ==================
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot_instance = None
last_sent = {}
is_running = False

def get_bot():
    global bot_instance
    if bot_instance is None:
        bot_instance = Bot(token=TELEGRAM_TOKEN)
    return bot_instance

def send_message(chat_id, text, markdown=False):
    try:
        bot = get_bot()

        async def task():
            if markdown:
                await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
            else:
                await bot.send_message(chat_id=chat_id, text=text)

        asyncio.run_coroutine_threadsafe(task(), event_loop)
        return True
    except Exception as e:
        logger.error(f"❌ إرسال فشل: {e}")
        return False

# ================== الجدولة ==================
def scheduler():
    global is_running
    is_running = True

    while True:
        now = datetime.now(TIMEZONE)
        t = now.time()
        d = now.date()

        def once(key):
            return key not in last_sent

        if t.hour == MORNING_TIME.hour and t.minute == MORNING_TIME.minute and once(f"m{d}"):
            send_to_groups(MORNING_DHIKR)
            last_sent[f"m{d}"] = now

        if t.hour == EVENING_TIME.hour and t.minute == EVENING_TIME.minute and once(f"e{d}"):
            send_to_groups(EVENING_DHIKR)
            last_sent[f"e{d}"] = now

        if t.hour == NIGHT_TIME.hour and t.minute == NIGHT_TIME.minute and once(f"n{d}"):
            send_to_groups(SLEEP_DHIKR)
            last_sent[f"n{d}"] = now

        time.sleep(60)

def send_to_groups(text):
    for g in GROUPS:
        send_message(g, text)
        time.sleep(0.5)

threading.Thread(target=scheduler, daemon=True).start()

# ================== Webhook ==================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify(ok=True)

    msg = data["message"]
    chat_id = msg["chat"]["id"]
    chat_type = msg["chat"]["type"]
    user_id = msg["from"]["id"]
    text = msg.get("text", "")

    if text.startswith("/start"):
        if chat_type == "private" or user_id == ADMIN_ID:
            send_message(chat_id, START_RESPONSE, True)

    elif text.startswith("/help"):
        if chat_type == "private" or user_id == ADMIN_ID:
            send_message(chat_id, HELP_RESPONSE)

    elif text.startswith("/status"):
        if chat_type == "private" or user_id == ADMIN_ID:
            now = datetime.now(TIMEZONE)
            send_message(chat_id, f"✅ يعمل\n⏰ {now}", True)

    return jsonify(ok=True)

# ================== تشغيل ==================
if __name__ == "__main__":
    async def hook():
        await get_bot().set_webhook(WEBHOOK_URL)

    asyncio.run_coroutine_threadsafe(hook(), event_loop)

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

