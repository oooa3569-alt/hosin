import os
import logging
import asyncio
import threading
import time as t
from datetime import datetime, time
import pytz
from flask import Flask, request, jsonify
from telegram import Bot
from telegram.error import TelegramError

# ========== إعدادات البوت ==========
TELEGRAM_TOKEN = "8260168982:AAEy-YQDWa-yTqJKmsA_yeSuNtZb8qNeHAI"
ADMIN_ID = 7635779264
GROUPS = ["-1002225164483", "-1002576714713"]
WEBHOOK_URL = "https://hosin-q20k.onrender.com/webhook"

# ========== التوقيتات (توقيت الجزائر) ==========
TIMEZONE = pytz.timezone('Africa/Algiers')
MORNING_TIME = time(8, 30)    # 8:30 صباحاً
EVENING_TIME = time(16, 0)    # 4:00 مساءً
NIGHT_TIME = time(23, 0)      # 11:00 مساءً

# ========== الأذكار الكاملة (مبسطة) ==========
MORNING_DHIKR = """🌅 *أذكار الصباح*

*أعوذ بكلمات الله التامات من شر ما خلق* (٣ مرات)

*اللهم صل وسلم على نبينا محمد* (٤ مرات)

*اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك ما استطعت، أعوذ بك من شر ما صنعت، أبوء لك بنعمتك علي وأبوء بذنبي فاغفر لي فإنه لا يغفر الذنوب إلا أنت*

*بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم* (٣ مرات)

*رضيت بالله ربا وبالإسلام دينا وبمحمد صلى الله عليه وسلم نبيا* (٣ مرات)

*اللهم صل وسلم وبارك على نبينا محمد* (٢ مرات)

*أصبحنا وأصبح الملك لله والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير، رب أسألك خير ما في هذا اليوم وخير ما بعده، وأعوذ بك من شر ما في هذا اليوم وشر ما بعده، رب أعوذ بك من الكسل وسوء الكبر، رب أعوذ بك من عذاب في النار وعذاب في القبر*

*اللهم ما أصبح بي من نعمة أو بأحد من خلقك فمنك وحدك لا شريك لك، فلك الحمد ولك الشكر*

*اللهم عالم الغيب والشهادة فاطر السماوات والأرض رب كل شيء ومليكه، أشهد أن لا إله إلا أنت، أعوذ بك من شر نفسي ومن شر الشيطان وشركه، وأن أقترف على نفسي سوءا أو أجره إلى مسلم*

*لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير*
"""

EVENING_DHIKR = """🌇 *أذكار المساء*

*أعوذ بكلمات الله التامات من شر ما خلق* (٣ مرات)

*اللهم صل وسلم على نبينا محمد* (٤ مرات)

*اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك ما استطعت، أعوذ بك من شر ما صنعت، أبوء لك بنعمتك علي وأبوء بذنبي فاغفر لي فإنه لا يغفر الذنوب إلا أنت*

*بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم* (٣ مرات)

*رضيت بالله ربا وبالإسلام دينا وبمحمد صلى الله عليه وسلم نبيا* (٣ مرات)

*اللهم صل وسلم وبارك على نبينا محمد* (٢ مرات)

*أمسينا وأمسى الملك لله والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير، رب أسألك خير ما في هذه الليلة وخير ما بعدها، وأعوذ بك من شر ما في هذه الليلة وشر ما بعدها، رب أعوذ بك من الكسل وسوء الكبر، رب أعوذ بك من عذاب في النار وعذاب في القبر*

*اللهم ما أمسى بي من نعمة أو بأحد من خلقك فمنك وحدك لا شريك لك، فلك الحمد ولك الشكر*

*اللهم عالم الغيب والشهادة فاطر السماوات والأرض رب كل شيء ومليكه، أشهد أن لا إله إلا أنت، أعوذ بك من شر نفسي ومن شر الشيطان وشركه، وأن أقترف على نفسي سوءا أو أجره إلى مسلم*

*لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير*
"""

SLEEP_DHIKR = """🌙 *نام وأنت مغفور الذنب*

قال رسول الله ﷺ:
*"من قال حين يأوي إلى فراشه:*
'لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير، لا حول ولا قوة إلا بالله، سبحان الله والحمد لله ولا إله إلا الله والله أكبر'

*غفر الله ذنوبه أو خطاياه وإن كانت مثل زبد البحر."* 🤎🌗
"""

# ========== إنشاء التطبيق ==========
app = Flask(__name__)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== متغيرات عامة ==========
bot = None
is_running = False
last_sent = {}

# ========== تهيئة البوت ==========
def init_bot():
    """تهيئة البوت مرة واحدة"""
    global bot
    if bot is None:
        try:
            # إنشاء البوت مع إعدادات الاتصال
            bot = Bot(
                token=TELEGRAM_TOKEN,
                request=bot.Request(
                    connect_timeout=10.0,
                    read_timeout=10.0,
                    write_timeout=10.0,
                    pool_timeout=10.0,
                    connect_pool_size=5
                )
            )
            logger.info("✅ تم تهيئة البوت بنجاح")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة البوت: {e}")
            return False
    return True

# ========== وظائف المساعدة ==========
async def send_message_safe(chat_id, text, retry_count=3):
    """إرسال رسالة بأمان مع إعادة المحاولة"""
    for attempt in range(retry_count):
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown'
            )
            logger.info(f"✅ تم إرسال رسالة إلى {chat_id}")
            return True
        except TelegramError as e:
            logger.warning(f"⚠️ محاولة {attempt + 1} فشلت: {e}")
            await asyncio.sleep(1)  # انتظر ثانية قبل إعادة المحاولة
        except Exception as e:
            logger.error(f"❌ خطأ غير متوقع: {e}")
            break
    return False

async def send_dhikr_to_all(text):
    """إرسال ذكر إلى جميع المجموعات"""
    if not init_bot():
        return False
    
    success_count = 0
    for group_id in GROUPS:
        try:
            await send_message_safe(group_id, text)
            success_count += 1
            await asyncio.sleep(0.5)  # انتظر نصف ثانية بين المجموعات
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الذكر للمجموعة {group_id}: {e}")
    
    return success_count > 0

async def send_start_response(chat_id, chat_type, user_id, user_name):
    """إرسال رد على أمر /start"""
    if not init_bot():
        return
    
    response_text = (
        "🤖 بوت أذكار الصباح والمساء\n\n"
        "✅ تم تفعيل الإشعارات اليومية\n"
        "⏰ مواعيد الإذكار:\n"
        "• الصباح: 8:30 صباحاً\n"
        "• المساء: 4:00 مساءً\n\n"
        "🤲 لا تنسوا الدعاء لمن كان سبباً في هذا الخير\n"
        "🛠️ الصانع: @Mik_emm"
    )
    
    # في الخاص: يرد على الجميع
    # في المجموعة: يرد فقط على الأدمن
    if chat_type == "private" or (chat_type in ["group", "supergroup"] and user_id == ADMIN_ID):
        await send_message_safe(chat_id, response_text)

async def send_help_response(chat_id, chat_type, user_id):
    """إرسال رد على أمر /help"""
    if not init_bot():
        return
    
    response_text = (
        "• /start - بدء البوت وعرض المعلومات\n"
        "• /help - عرض هذه الرسالة\n"
        "• /status - حالة البوت\n\n"
        "🛠️ الصانع: @Mik_emm"
    )
    
    # في الخاص: يرد على الجميع
    # في المجموعة: يرد فقط على الأدمن
    if chat_type == "private" or (chat_type in ["group", "supergroup"] and user_id == ADMIN_ID):
        await send_message_safe(chat_id, response_text)

async def send_status_response(chat_id, chat_type, user_id):
    """إرسال رد على أمر /status"""
    if not init_bot():
        return
    
    now = datetime.now(TIMEZONE)
    status_text = (
        f"✅ البوت: {'يعمل 🟢' if is_running else 'متوقف 🔴'}\n"
        f"⏰ التوقيت: {now.strftime('%H:%M:%S')}\n"
        f"📅 التاريخ: {now.strftime('%Y-%m-%d')}\n"
        f"🛠️ الصانع: @Mik_emm"
    )
    
    # في الخاص: يرد على الجميع
    # في المجموعة: يرد فقط على الأدمن
    if chat_type == "private" or (chat_type in ["group", "supergroup"] and user_id == ADMIN_ID):
        await send_message_safe(chat_id, status_text)

# ========== جدولة الأذكار ==========
def scheduler_worker():
    """عامل الجدولة"""
    global is_running
    
    while True:
        try:
            now = datetime.now(TIMEZONE)
            current_time = now.time()
            current_date = now.date()
            
            # أذكار الصباح 8:30
            key = f"morning_{current_date}"
            if (current_time.hour == MORNING_TIME.hour and 
                current_time.minute == MORNING_TIME.minute and 
                key not in last_sent):
                
                asyncio.run(send_dhikr_to_all(MORNING_DHIKR))
                last_sent[key] = now
                logger.info("✅ تم إرسال أذكار الصباح")
            
            # أذكار المساء 4:00
            key = f"evening_{current_date}"
            if (current_time.hour == EVENING_TIME.hour and 
                current_time.minute == EVENING_TIME.minute and 
                key not in last_sent):
                
                asyncio.run(send_dhikr_to_all(EVENING_DHIKR))
                last_sent[key] = now
                logger.info("✅ تم إرسال أذكار المساء")
            
            # ذكر النوم 11:00
            key = f"night_{current_date}"
            if (current_time.hour == NIGHT_TIME.hour and 
                current_time.minute == NIGHT_TIME.minute and 
                key not in last_sent):
                
                asyncio.run(send_dhikr_to_all(SLEEP_DHIKR))
                last_sent[key] = now
                logger.info("✅ تم إرسال ذكر النوم")
            
            # تنظيف السجل القديم (بعد 24 ساعة)
            keys_to_remove = []
            for k, sent_time in last_sent.items():
                if (now - sent_time).days >= 1:
                    keys_to_remove.append(k)
            
            for k in keys_to_remove:
                del last_sent[k]
            
            t.sleep(60)  # فحص كل دقيقة
            
        except Exception as e:
            logger.error(f"❌ خطأ في الجدولة: {e}")
            t.sleep(60)

def start_scheduler():
    """بدء الجدولة"""
    global is_running
    if not is_running:
        is_running = True
        scheduler_thread = threading.Thread(target=scheduler_worker, daemon=True)
        scheduler_thread.start()
        logger.info("✅ بدء جدولة الأذكار")

# ========== مسارات Flask ==========
@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return jsonify({
        "status": "online",
        "service": "Dhikr Bot",
        "timezone": "Africa/Algiers",
        "message": "بوت الأذكار يعمل"
    })

@app.route('/health')
def health_check():
    """فحص صحة البوت"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """معالجة طلبات ويب هوك"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "no_data"}), 400
        
        # معالجة الأوامر في خيط منفصل
        threading.Thread(target=process_webhook, args=(data,), daemon=True).start()
        
        return jsonify({"status": "processing"})
        
    except Exception as e:
        logger.error(f"❌ خطأ في ويب هوك: {e}")
        return jsonify({"status": "error"}), 500

def process_webhook(data):
    """معالجة ويب هوك في خيط منفصل"""
    try:
        if 'message' in data and 'text' in data['message']:
            message = data['message']
            chat = message['chat']
            user = message['from']
            
            chat_id = chat['id']
            chat_type = chat['type']
            user_id = user['id']
            user_name = user.get('first_name', 'المستخدم')
            text = message['text'].lower()
            
            logger.info(f"📩 معالجة: {text} من {user_id} في {chat_type}")
            
            if text.startswith('/start'):
                asyncio.run(send_start_response(chat_id, chat_type, user_id, user_name))
            elif text.startswith('/help'):
                asyncio.run(send_help_response(chat_id, chat_type, user_id))
            elif text.startswith('/status'):
                asyncio.run(send_status_response(chat_id, chat_type, user_id))
                
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة البيانات: {e}")

@app.route('/start_bot', methods=['GET'])
def start_bot():
    """بدء البوت"""
    try:
        # تهيئة البوت
        init_bot()
        
        # بدء الجدولة
        start_scheduler()
        
        # إرسال رسالة تأكيد للأدمن
        async def send_init_message():
            if bot:
                await send_message_safe(
                    ADMIN_ID,
                    "🤖 بوت الأذكار يعمل الآن\n"
                    "✅ تم تهيئة البوت بنجاح\n"
                    "🛠️ الصانع: @Mik_emm"
                )
        
        asyncio.run(send_init_message())
        
        return jsonify({
            "success": True,
            "message": "✅ تم تشغيل البوت بنجاح"
        })
        
    except Exception as e:
        logger.error(f"❌ خطأ في بدء البوت: {e}")
        return jsonify({
            "success": False,
            "message": f"❌ خطأ: {str(e)}"
        })

@app.route('/test', methods=['GET'])
def test_bot():
    """اختبار البوت"""
    try:
        async def send_test():
            if init_bot():
                await send_message_safe(
                    ADMIN_ID,
                    "✅ اختبار البوت\n"
                    "الحالة: ✅ يعمل بنجاح\n"
                    "🛠️ الصانع: @Mik_emm"
                )
        
        asyncio.run(send_test())
        
        return jsonify({
            "success": True,
            "message": "✅ تم إرسال رسالة الاختبار"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"❌ خطأ: {str(e)}"
        })

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """تعيين ويب هوك"""
    try:
        async def set_wh():
            if init_bot():
                await bot.set_webhook(WEBHOOK_URL)
                return True
            return False
        
        success = asyncio.run(set_wh())
        
        if success:
            return jsonify({
                "success": True,
                "message": "✅ تم تعيين ويب هوك",
                "url": WEBHOOK_URL
            })
        else:
            return jsonify({
                "success": False,
                "message": "❌ فشل في تعيين ويب هوك"
            })
            
    except Exception as e:
        logger.error(f"❌ خطأ في تعيين ويب هوك: {e}")
        return jsonify({
            "success": False,
            "message": f"❌ خطأ: {str(e)}"
        })

# ========== التشغيل الرئيسي ==========
if __name__ == '__main__':
    logger.info("🚀 بدء تشغيل بوت الأذكار")
    
    # تهيئة البوت
    init_bot()
    
    # بدء الجدولة
    start_scheduler()
    
    # تعيين ويب هوك
    threading.Thread(target=lambda: asyncio.run(set_webhook()), daemon=True).start()
    
    # تشغيل الخادم
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
