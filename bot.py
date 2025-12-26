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

# ================== التوقيت (الجزائر) ==================
TIMEZONE = pytz.timezone("Africa/Algiers")
MORNING_TIME = dt_time(8, 30)
EVENING_TIME = dt_time(16, 0)
NIGHT_TIME = dt_time(23, 0)

# ================== الأذكار ==================
MORNING_DHIKR = """🌅 أذكار الصباح

أعوذ بالله من الشيطان الرجيم
﴿اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ﴾

أصبحنا وأصبح الملك لله والحمد لله
لا إله إلا الله وحده لا شريك له
له الملك وله الحمد وهو على كل شيء قدير

اللهم بك أصبحنا وبك أمسينا وبك نحيا وبك نموت وإليك النشور

بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء
وهو السميع العليم (٣ مرات)

رضيت بالله رباً وبالإسلام ديناً
وبمحمد ﷺ نبياً (٣ مرات)

اللهم صل وسلم على نبينا محمد (١٠ مرات)

لا إله إلا الله وحده لا شريك له
له الملك وله الحمد وهو على كل شيء قدير (١٠ مرات)
"""

EVENING_DHIKR = """🌇 أذكار المساء

أعوذ بالله من الشيطان الرجيم
﴿اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ﴾

أمسينا وأمسى الملك لله والحمد لله
لا إله إلا الله وحده لا شريك له
له الملك وله الحمد وهو على كل شيء قدير

اللهم بك أمسينا وبك أصبحنا وبك نحيا وبك نموت وإليك المصير

بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء
وهو السميع العليم (٣ مرات)

رضيت بالله رباً وبالإسلام ديناً
وبمحمد ﷺ نبياً (٣ مرات)

اللهم صل وسلم على نبينا محمد (١٠ مرات)

لا إله إلا الله وحده لا شريك له
له الملك وله الحمد وهو على كل شيء قدير (١٠ مرات)
"""

SLEEP_DHIKR = """🌙 أذكار النوم

باسمك ربي وضعت جنبي وبك أرفعه
إن أمسكت نفسي فارحمها
وإن أرسلتها فاحفظها بما تحفظ به عبادك الصالحين

اللهم قني عذابك يوم تبعث عبادك

سبحان الله (٣٣)
الحمد لله (٣٣)
الله أكبر (٣٤)

آية الكرسي
"""

# ================== رسائل الأوامر ==================
START_RESPONSE = """🤖 بوت أذكار الصباح والمساء

✅ حالة البوت: يعمل بنجاح

🌅 يرسل أذكار الصباح
🌇 يرسل أذكار المساء
🌙 يرسل أذكار النوم

⏰ المواعيد:
• 08:30 صباحاً
• 16:00 مساءً
• 23:00 ليلاً

👤 حساب المطوّر:
@Mik_emm

💡 صاحب الفكرة:
@mohamedelhocine
🤲 نرجو الدعاء له

بارك الله فيكم 🌸
"""

HELP_RESPONSE = """📌 الأوامر المتاحة:
/start - معلومات البوت
/help - المساعدة
/status - حالة البوت
"""

# ================== Flask ==================
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot_instance = None
last_sent = {}

def get_bot():
    global bot_instance
    if bot_instance is None:
        bot_instance = Bot(token=TELEGRAM_TOKEN)
    return bot_instance

def send_message(chat_id, text):
    async def task():
        await get_bot().send_message(chat_id=chat_id, text=text)
    asyncio.run_coroutine_threadsafe(task(), event_loop)

# ================== الجدولة ==================
def scheduler():
    while True:
        now = datetime.now(TIMEZONE)
        t = now.time()
        d = now.date()

        def sent(key):
            return key in last_sent

        if t.hour == MORNING_TIME.hour and t.minute == MORNING_TIME.minute and not sent(f"m{d}"):
            for g in GROUPS:
                send_message(g, MORNING_DHIKR)
                time.sleep(1)
            last_sent[f"m{d}"] = True

        if t.hour == EVENING_TIME.hour and t.minute == EVENING_TIME.minute and not sent(f"e{d}"):
            for g in GROUPS:
                send_message(g, EVENING_DHIKR)
                time.sleep(1)
            last_sent[f"e{d}"] = True

        if t.hour == NIGHT_TIME.hour and t.minute == NIGHT_TIME.minute and not sent(f"n{d}"):
            for g in GROUPS:
                send_message(g, SLEEP_DHIKR)
                time.sleep(1)
            last_sent[f"n{d}"] = True

        time.sleep(60)

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
    text = msg.get("text", "").strip()
    command = text.split("@")[0]

    if command == "/start":
        if chat_type == "private" or user_id == ADMIN_ID:
            send_message(chat_id, START_RESPONSE)

    elif command == "/help":
        if chat_type == "private" or user_id == ADMIN_ID:
            send_message(chat_id, HELP_RESPONSE)

    elif command == "/status":
        if chat_type == "private" or user_id == ADMIN_ID:
            now = datetime.now(TIMEZONE)
            send_message(chat_id, f"✅ البوت يعمل\n⏰ {now}")

    return jsonify(ok=True)

# ================== تشغيل ==================
if __name__ == "__main__":
    async def hook():
        await get_bot().set_webhook(WEBHOOK_URL)

    asyncio.run_coroutine_threadsafe(hook(), event_loop)

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


