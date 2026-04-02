import os, logging, asyncio, threading, time, requests
from datetime import datetime, time as dt_time
import pytz
from flask import Flask, request, jsonify
from telegram import Bot, error

# ==============================================================================
# ⚙️ إعدادات البوت (خاص بالصفحات/القنوات)
# ==============================================================================

event_loop = asyncio.new_event_loop()
def run_loop(loop): asyncio.set_event_loop(loop); loop.run_forever()
threading.Thread(target=run_loop, args=(event_loop,), daemon=True).start()

# التوكن الجديد
TELEGRAM_TOKEN = "8577723856:AAFImKv4T3gzb_pMflDNFXccOrZFoC3bhRI"
ADMIN_ID = 7635779264

# ✅ قائمة القنوات (تمت إضافة الآيديات الجديدة هنا)
CHANNELS = [
    "-1003571051160",
    "-1002516956218",
    "-1003744755797"
]

# رابط السيرفر
WEBHOOK_URL = "https://hosin-q20k.onrender.com/webhook"

# --- 🖼️ روابط الصور ---
MORNING_IMG_URL = "https://github.com/oooa3569-alt/hosin/blob/main/sabah.jpg?raw=true"
EVENING_IMG_URL = "https://github.com/oooa3569-alt/hosin/blob/main/mashe.jpg?raw=true"
NIGHT_POST_IMG  = "https://github.com/oooa3569-alt/hosin/blob/main/photo_2025-12-30_07-46-10.jpg?raw=true"

# --- ⏰ المواعيد (توقيت الجزائر) ---
TIMEZONE = pytz.timezone("Africa/Algiers")

# مواعيد الصور
MORNING_TIME = dt_time(7, 0)   # 07:00 صباحاً
EVENING_TIME = dt_time(16, 0)  # 04:00 مساءً
NIGHT_TIME   = dt_time(22, 0)  # 10:00 ليلاً (صورة الوتر والملك)

# مواعيد النصوص
REMINDER_TIME_1 = dt_time(9, 0) # ذكر عام
REMINDER_TIME_2 = dt_time(17, 0) # ذكر عام
REMINDER_TIME_3 = dt_time(21, 0) # ذكر عام
SLEEP_TEXT_TIME = dt_time(23, 0) # ذكر النوم النصي (11 ليلاً)

# --- 📝 النصوص ---

# 1. الذكر العام
GENERAL_DHIKR = """‏﴿ وَاذْكُر ربّكَ إِذَا نَسِيتَ ﴾ 🌿

‏- سُبحان الله
‏- الحمدلله
-‏ الله أكبر
‏- أستغفر الله
‏- لا إله إلا الله
‏- لاحول ولا قوة إلا بالله
‏- سُبحان الله وبحمده
‏- سُبحان الله العظيم
- اللَّهُمَّ صلِّ وسلِم على نبينا محمد
‏- لا إله إلا أنت سُبحانك إني كنت من الظالمين."""

# 2. ذكر النوم النصي
SLEEP_DHIKR = """🌙 نام وأنت مغفور الذنب

قال رسول الله ﷺ:
"من قال حين يأوي إلى فراشه:
'لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير، لا حول ولا قوة إلا بالله، سبحان الله والحمد لله ولا إله إلا الله والله أكبر'

غفر الله ذنوبه أو خطاياه وإن كانت مثل زبد البحر." 🤎🌗"""

# 3. نص فقرة الليل (مع الصورة)
NIGHT_CAPTION = """- إملؤوآ السماء بصّوت دعواتُكم ،
‏فهناك في الثلث الأخير من الليل ،
‏ربٌ كريم ورحيم يقولَ :
‏هل مِنْ داعِ فاستجيب له ؟

لا تنسوا : 💚
- الوتر :
- سورة الملك قبل النوم 
"مُنجيه من عذاب القبر" 🤍🦋.
- أذكار النوم .🦋🤍"""

# 4. التذكيرات الدورية
PROPHET_PRAYER = "اللهم صلِّ وسلِّم على نبينا محمد ﷺ 🤍"
LA_HAWLA = "لا حول ولا قوة إلا بالله 🌿"

START_RESPONSE = """🤖 **أهلاً بك في بوت  الاذكار للقنوات**

✅ الجدول اليومي:
🌅 07:00 | اذكار الصباح
📿 11:00 | ذكر عام
🌇 16:00 |  اذكار المساء
📿 17:00 | ذكر عام
📿 21:00 | ذكر عام
🌃 22:00 | صورة الملك
💤 23:00 | ذكر النوم   
⏱️ كل ساعة | صلاة على النبي
⏱️ كل ساعتين | حوقلة

👤 المطور: @Mik_emm
"""

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
bot = None

# ==============================================================================
# 🚀 دوال الإرسال
# ==============================================================================

def get_bot():
    global bot
    if not bot: bot = Bot(token=TELEGRAM_TOKEN)
    return bot

def send_message(chat_id, text):
    async def task():
        try:
            await get_bot().send_message(chat_id, text)
        except error.RetryAfter as e:
            time.sleep(int(e.retry_after) + 1)
            await get_bot().send_message(chat_id, text)
        except Exception as e:
            logging.error(f"Error sending message to {chat_id}: {e}")
    asyncio.run_coroutine_threadsafe(task(), event_loop)

def send_photo(chat_id, photo_url, caption=None):
    async def task():
        try:
            await get_bot().send_photo(chat_id=chat_id, photo=photo_url, caption=caption)
        except error.RetryAfter as e:
            time.sleep(int(e.retry_after) + 1)
            await get_bot().send_photo(chat_id=chat_id, photo=photo_url, caption=caption)
        except Exception as e:
            logging.error(f"Error sending photo to {chat_id}: {e}")
    asyncio.run_coroutine_threadsafe(task(), event_loop)

# ==============================================================================
# ⏰ المجدول الزمني
# ==============================================================================

def scheduler():
    last_sent = {}
    while True:
        now = datetime.now(TIMEZONE)
        t, d = now.time(), now.date()
        
        hour_key = f"{d}_{t.hour}"
        day_key = f"{d}"

        def sent(k): return k in last_sent

        # 1. أذكار الصباح (07:00) - صورة
        if t.hour == MORNING_TIME.hour and t.minute == MORNING_TIME.minute and not sent(f"m{day_key}"):
            for ch in CHANNELS: send_photo(ch, MORNING_IMG_URL, caption="🌅 أذكار الصباح"); time.sleep(1)
            last_sent[f"m{day_key}"] = True

        # 2. الذكر العام 1 (11:00) - نص
        if t.hour == REMINDER_TIME_1.hour and t.minute == REMINDER_TIME_1.minute and not sent(f"r1{day_key}"):
            for ch in CHANNELS: send_message(ch, GENERAL_DHIKR); time.sleep(1)
            last_sent[f"r1{day_key}"] = True

        # 3. أذكار المساء (16:00) - صورة
        if t.hour == EVENING_TIME.hour and t.minute == EVENING_TIME.minute and not sent(f"e{day_key}"):
            for ch in CHANNELS: send_photo(ch, EVENING_IMG_URL, caption="🌇 أذكار المساء"); time.sleep(1)
            last_sent[f"e{day_key}"] = True

        # 4. الذكر العام 2 (17:00) - نص
        if t.hour == REMINDER_TIME_2.hour and t.minute == REMINDER_TIME_2.minute and not sent(f"r2{day_key}"):
            for ch in CHANNELS: send_message(ch, GENERAL_DHIKR); time.sleep(1)
            last_sent[f"r2{day_key}"] = True

        # 5. الذكر العام 3 (21:00) - نص
        if t.hour == REMINDER_TIME_3.hour and t.minute == REMINDER_TIME_3.minute and not sent(f"r3{day_key}"):
            for ch in CHANNELS: send_message(ch, GENERAL_DHIKR); time.sleep(1)
            last_sent[f"r3{day_key}"] = True

        # 6. فقرة الليل (22:00) - صورة + نص الوتر والملك
        if t.hour == NIGHT_TIME.hour and t.minute == NIGHT_TIME.minute and not sent(f"night_img{day_key}"):
            for ch in CHANNELS: send_photo(ch, NIGHT_POST_IMG, caption=NIGHT_CAPTION); time.sleep(1)
            last_sent[f"night_img{day_key}"] = True

        # 7. ذكر النوم (23:00) - نص الحديث
        if t.hour == SLEEP_TEXT_TIME.hour and t.minute == SLEEP_TEXT_TIME.minute and not sent(f"sleep_txt{day_key}"):
            for ch in CHANNELS: send_message(ch, SLEEP_DHIKR); time.sleep(1)
            last_sent[f"sleep_txt{day_key}"] = True

        # 8. التذكيرات الدورية (كل ساعة / كل ساعتين)
        if t.minute == 0 and not sent(f"periodic_{hour_key}"):
            # كل ساعة: الصلاة على النبي
            for ch in CHANNELS: send_message(ch, PROPHET_PRAYER); time.sleep(1)
            
            # كل ساعتين (زوجي): لا حول ولا قوة إلا بالله
            if t.hour % 2 == 0:
                for ch in CHANNELS: send_message(ch, LA_HAWLA); time.sleep(1)
            
            last_sent[f"periodic_{hour_key}"] = True

        # تنظيف الذاكرة منتصف الليل
        if t.hour == 0 and t.minute == 1:
            last_sent.clear()

        time.sleep(40)

threading.Thread(target=scheduler, daemon=True).start()

# ==============================================================================
# 🌐 Webhook
# ==============================================================================

@app.route("/ping")
def ping(): return "pong"

def keep_alive():
    while True:
        try: requests.get(f"{WEBHOOK_URL.replace('/webhook', '')}/ping")
        except: pass
        time.sleep(600)
threading.Thread(target=keep_alive, daemon=True).start()

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data: return jsonify(ok=True)

    # كشف القنوات الجديدة
    if "my_chat_member" in data:
        update = data["my_chat_member"]
        chat = update["chat"]
        new_status = update.get("new_chat_member", {}).get("status")

        if chat.get("type") == "channel" and new_status == "administrator":
            title = chat.get("title", "No Title")
            cid = chat["id"]
            msg = f"📢 **قناة جديدة!**\n🏷: {title}\n🆔: `{cid}`\n⚠️ أضفه للقائمة CHANNELS."
            send_message(ADMIN_ID, msg)

    # أوامر الأدمن
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        if msg["chat"]["type"] == "private":
            text = msg.get("text", "").strip()
            if text == "/start": send_message(chat_id, START_RESPONSE)
            if text == "/id": send_message(chat_id, f"🆔: `{chat_id}`")

    return jsonify(ok=True)

if __name__ == "__main__":
    async def hook(): 
        try: await get_bot().set_webhook(WEBHOOK_URL)
        except: pass 
    asyncio.run_coroutine_threadsafe(hook(), event_loop)
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
