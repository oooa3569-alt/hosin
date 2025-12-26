import os
import logging
import asyncio
import threading
import time
from datetime import datetime, time as dt_time
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
MORNING_TIME = dt_time(8, 30)    # 8:30 صباحاً
EVENING_TIME = dt_time(16, 0)    # 4:00 مساءً
NIGHT_TIME = dt_time(23, 0)      # 11:00 مساءً

# ========== الأذكار الكاملة (بدون تنسيق Markdown خاطئ) ==========
# تم إزالة جميع علامات * التي تسبب المشكلة
MORNING_DHIKR = """🌅 أذكار الصباح

أعوذ بكلمات الله التامات من شر ما خلق (٣ مرات)

اللهم صل وسلم على نبينا محمد (٤ مرات)

اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك ما استطعت، أعوذ بك من شر ما صنعت، أبوء لك بنعمتك علي وأبوء بذنبي فاغفر لي فإنه لا يغفر الذنوب إلا أنت

بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم (٣ مرات)

رضيت بالله ربا وبالإسلام دينا وبمحمد صلى الله عليه وسلم نبيا (٣ مرات)

اللهم صل وسلم وبارك على نبينا محمد (٢ مرات)

أصبحنا وأصبح الملك لله والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير، رب أسألك خير ما في هذا اليوم وخير ما بعده، وأعوذ بك من شر ما في هذا اليوم وشر ما بعده، رب أعوذ بك من الكسل وسوء الكبر، رب أعوذ بك من عذاب في النار وعذاب في القبر

اللهم ما أصبح بي من نعمة أو بأحد من خلقك فمنك وحدك لا شريك لك، فلك الحمد ولك الشكر

اللهم عالم الغيب والشهادة فاطر السماوات والأرض رب كل شيء ومليكه، أشهد أن لا إله إلا أنت، أعوذ بك من شر نفسي ومن شر الشيطان وشركه، وأن أقترف على نفسي سوءا أو أجره إلى مسلم

لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير"""

EVENING_DHIKR = """🌇 أذكار المساء

أعوذ بكلمات الله التامات من شر ما خلق (٣ مرات)

اللهم صل وسلم على نبينا محمد (٤ مرات)

اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك ما استطعت، أعوذ بك من شر ما صنعت، أبوء لك بنعمتك علي وأبوء بذنبي فاغفر لي فإنه لا يغفر الذنوب إلا أنت

بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم (٣ مرات)

رضيت بالله ربا وبالإسلام دينا وبمحمد صلى الله عليه وسلم نبيا (٣ مرات)

اللهم صل وسلم وبارك على نبينا محمد (٢ مرات)

أمسينا وأمسى الملك لله والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير، رب أسألك خير ما في هذه الليلة وخير ما بعدها، وأعوذ بك من شر ما في هذه الليلة وشر ما بعدها، رب أعوذ بك من الكسل وسوء الكبر، رب أعوذ بك من عذاب في النار وعذاب في القبر

اللهم ما أمسى بي من نعمة أو بأحد من خلقك فمنك وحدك لا شريك لك، فلك الحمد ولك الشكر

اللهم عالم الغيب والشهادة فاطر السماوات والأرض رب كل شيء ومليكه، أشهد أن لا إله إلا أنت، أعوذ بك من شر نفسي ومن شر الشيطان وشركه، وأن أقترف على نفسي سوءا أو أجره إلى مسلم

لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير"""

SLEEP_DHIKR = """🌙 نام وأنت مغفور الذنب

قال رسول الله ﷺ:
"من قال حين يأوي إلى فراشه:
'لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير، لا حول ولا قوة إلا بالله، سبحان الله والحمد لله ولا إله إلا الله والله أكبر'

غفر الله ذنوبه أو خطاياه وإن كانت مثل زبد البحر." 🤎🌗"""

# ========== رسائل الأوامر (باستخدام تنسيق Markdown بسيط وآمن) ==========
START_RESPONSE = """🤖 *بوت أذكار الصباح والمساء*

✅ *تم تفعيل الإشعارات اليومية*

⏰ *مواعيد الإذكار:*
• الصباح: 8:30 صباحاً
• المساء: 4:00 مساءً

🤲 *لا تنسوا الدعاء لمن كان سبباً في هذا الخير*
🛠️ *الصانع:* @Mik_emm"""

HELP_RESPONSE = """• /start - بدء البوت وعرض المعلومات
• /help - عرض هذه الرسالة
• /status - حالة البوت

🛠️ الصانع: @Mik_emm"""

# ========== إنشاء التطبيق ==========
app = Flask(__name__)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== متغيرات عامة ==========
bot_instance = None
is_running = False
last_sent = {}

# ========== وظائف المساعدة ==========
def get_bot():
    """الحصول على كائن البوت"""
    global bot_instance
    if bot_instance is None:
        try:
            bot_instance = Bot(token=TELEGRAM_TOKEN)
            logger.info("✅ تم إنشاء كائن البوت")
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء البوت: {e}")
    return bot_instance

def send_message_simple(chat_id, text, use_markdown=False):
    """إرسال رسالة بشكل آمن"""
    try:
        bot = get_bot()
        if not bot:
            return False
        
        async def send_async():
            if use_markdown:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode='Markdown'
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text
                )
        
        asyncio.run(send_async())
        logger.info(f"✅ تم إرسال رسالة إلى {chat_id}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الرسالة: {e}")
        return False

def send_dhikr_to_groups(text):
    """إرسال ذكر إلى جميع المجموعات"""
    logger.info("📤 إرسال ذكر إلى المجموعات")
    
    success_count = 0
    for group_id in GROUPS:
        if send_message_simple(group_id, text, use_markdown=False):
            success_count += 1
            time.sleep(0.5)
    
    logger.info(f"✅ تم إرسال الذكر إلى {success_count} مجموعات")
    return success_count > 0

# ========== معالجة الأوامر ==========
def handle_start_command(chat_id, chat_type, user_id, user_name):
    """معالجة أمر /start"""
    logger.info(f"🎯 /start من {user_name} ({user_id}) في {chat_type}")
    
    # في الخاص: يرد على الجميع
    # في المجموعة: يرد فقط على الأدمن
    should_respond = (
        chat_type == "private" or 
        (chat_type in ["group", "supergroup"] and user_id == ADMIN_ID)
    )
    
    if should_respond:
        return send_message_simple(chat_id, START_RESPONSE, use_markdown=True)
    else:
        logger.info(f"⏭️ تخطي رد على {user_id} في المجموعة")
        return True

def handle_help_command(chat_id, chat_type, user_id):
    """معالجة أمر /help"""
    should_respond = (
        chat_type == "private" or 
        (chat_type in ["group", "supergroup"] and user_id == ADMIN_ID)
    )
    
    if should_respond:
        return send_message_simple(chat_id, HELP_RESPONSE, use_markdown=False)
    else:
        return True

def handle_status_command(chat_id, chat_type, user_id):
    """معالجة أمر /status"""
    now = datetime.now(TIMEZONE)
    status_text = f"""📊 *حالة البوت*

✅ البوت: {'يعمل 🟢' if is_running else 'متوقف 🔴'}
⏰ التوقيت: {now.strftime('%H:%M:%S')}
📅 التاريخ: {now.strftime('%Y-%m-%d')}

🛠️ الصانع: @Mik_emm"""
    
    should_respond = (
        chat_type == "private" or 
        (chat_type in ["group", "supergroup"] and user_id == ADMIN_ID)
    )
    
    if should_respond:
        return send_message_simple(chat_id, status_text, use_markdown=True)
    else:
        return True

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
                
                logger.info("⏰ وقت أذكار الصباح")
                send_dhikr_to_groups(MORNING_DHIKR)
                last_sent[key] = now
            
            # أذكار المساء 4:00
            key = f"evening_{current_date}"
            if (current_time.hour == EVENING_TIME.hour and 
                current_time.minute == EVENING_TIME.minute and 
                key not in last_sent):
                
                logger.info("⏰ وقت أذكار المساء")
                send_dhikr_to_groups(EVENING_DHIKR)
                last_sent[key] = now
            
            # ذكر النوم 11:00
            key = f"night_{current_date}"
            if (current_time.hour == NIGHT_TIME.hour and 
                current_time.minute == NIGHT_TIME.minute and 
                key not in last_sent):
                
                logger.info("⏰ وقت ذكر النوم")
                send_dhikr_to_groups(SLEEP_DHIKR)
                last_sent[key] = now
            
            # تنظيف السجل القديم
            keys_to_remove = []
            for k, sent_time in last_sent.items():
                if (now - sent_time).days >= 1:
                    keys_to_remove.append(k)
            
            for k in keys_to_remove:
                del last_sent[k]
            
            time.sleep(60)
            
        except Exception as e:
            logger.error(f"❌ خطأ في الجدولة: {e}")
            time.sleep(60)

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
        
        if 'message' in data:
            message = data['message']
            
            # استخراج البيانات الأساسية
            chat_id = message['chat']['id']
            chat_type = message['chat']['type']
            user_id = message['from']['id']
            user_name = message['from'].get('first_name', 'المستخدم')
            text = message.get('text', '').lower()
            
            logger.info(f"📩 استقبال: {text} من {user_id}")
            
            # معالجة الأوامر
            if text.startswith('/start'):
                success = handle_start_command(chat_id, chat_type, user_id, user_name)
                if success:
                    logger.info(f"✅ تم الرد على /start لـ {user_id}")
                else:
                    logger.error(f"❌ فشل في الرد على /start لـ {user_id}")
                    
            elif text.startswith('/help'):
                handle_help_command(chat_id, chat_type, user_id)
                
            elif text.startswith('/status'):
                handle_status_command(chat_id, chat_type, user_id)
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"❌ خطأ في ويب هوك: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/start_bot', methods=['GET'])
def start_bot():
    """بدء البوت"""
    try:
        # بدء الجدولة
        start_scheduler()
        
        # إرسال رسالة تأكيد
        success = send_message_simple(
            ADMIN_ID,
            "🤖 *بوت الأذكار يعمل الآن*\n\n✅ *تم تهيئة البوت بنجاح*\n\n🛠️ *الصانع:* @Mik_emm",
            use_markdown=True
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": "✅ تم تشغيل البوت بنجاح"
            })
        else:
            return jsonify({
                "success": False,
                "message": "⚠️ تم بدء البوت ولكن فشل في إرسال تأكيد"
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
        success = send_message_simple(
            ADMIN_ID,
            "✅ *اختبار البوت*\n\nالحالة: ✅ يعمل بنجاح\n\n🛠️ *الصانع:* @Mik_emm",
            use_markdown=True
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": "✅ تم إرسال رسالة الاختبار"
            })
        else:
            return jsonify({
                "success": False,
                "message": "❌ فشل في إرسال رسالة الاختبار"
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
        bot = get_bot()
        if not bot:
            return jsonify({
                "success": False,
                "message": "❌ البوت غير مهيأ"
            })
        
        async def set_webhook_async():
            await bot.set_webhook(WEBHOOK_URL)
        
        asyncio.run(set_webhook_async())
        
        return jsonify({
            "success": True,
            "message": "✅ تم تعيين ويب هوك",
            "url": WEBHOOK_URL
        })
            
    except Exception as e:
        logger.error(f"❌ خطأ في تعيين ويب هوك: {e}")
        return jsonify({
            "success": False,
            "message": f"❌ خطأ: {str(e)}"
        })

# ========== الإعداد الأولي ==========
def initialize():
    """الإعداد الأولي للبوت"""
    logger.info("🚀 بدء تهيئة البوت...")
    
    # 1. تعيين ويب هوك
    try:
        bot = get_bot()
        if bot:
            async def set_webhook_async():
                await bot.set_webhook(WEBHOOK_URL)
            
            asyncio.run(set_webhook_async())
            logger.info(f"✅ تم تعيين ويب هوك: {WEBHOOK_URL}")
        else:
            logger.error("❌ فشل في تعيين ويب هوك - البوت غير منشأ")
    except Exception as e:
        logger.error(f"⚠️ تحذير في تعيين ويب هوك: {e}")
    
    # 2. بدء الجدولة
    start_scheduler()
    
    # 3. إرسال رسالة بدء التشغيل (في خيط منفصل)
    def send_startup_message():
        time.sleep(2)
        send_message_simple(
            ADMIN_ID,
            "🤖 *بوت الأذكار يعمل الآن*\n\n✅ *تم بدء تشغيل البوت بنجاح*\n\n🛠️ *الصانع:* @Mik_emm",
            use_markdown=True
        )
    
    threading.Thread(target=send_startup_message, daemon=True).start()
    
    logger.info("✅ تم تهيئة البوت")

# ========== التشغيل الرئيسي ==========
if __name__ == '__main__':
    # تهيئة البوت
    initialize()
    
    # تشغيل الخادم
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 بدء تشغيل الخادم على المنفذ {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
