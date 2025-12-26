import os
import logging
import asyncio
import threading
from datetime import datetime, time
import pytz
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ========== إعدادات البوت ==========
TELEGRAM_TOKEN = "8260168982:AAEy-YQDWa-yTqJKmsA_yeSuNtZb8qNeHAI"
ADMIN_ID = 7635779264
GROUPS = ["-1002225164483", "-1002576714713"]  # قائمة المجموعات
WEBHOOK_URL = "https://hosin-q20k.onrender.com/webhook"

# ========== التوقيتات (توقيت الجزائر) ==========
TIMEZONE = pytz.timezone('Africa/Algiers')  # تغيير من الرياض إلى الجزائر
MORNING_TIME = time(8, 30)    # 8:30 صباحاً
NOON_DHIKR_TIME = time(12, 0)  # 12:00 ظهراً
EVENING_TIME = time(16, 0)    # 4:00 مساءً
EVENING_DHIKR2_TIME = time(18, 0)  # 6:00 مساءً
NIGHT_TIME = time(23, 0)      # 11:00 مساءً

# ========== الأذكار الكاملة ==========
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

REMEMBER_DHIKR = """📿 *واذكر ربك إذا نسيت*

سُبحان الله
الحمدلله  
الله أكبر
أستغفر الله
لا إله إلا الله
لاحول ولا قوة إلا بالله
سُبحان الله وبحمده
سُبحان الله العظيم
اللَّهُمَّ صلِّ وسلِم على نبينا محمد
لا إله إلا أنت سُبحانك إني كنت من الظالمين
"""

# ========== إنشاء التطبيق ==========
app = Flask(__name__)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== متغيرات عامة ==========
bot_instance = None
application_instance = None
scheduler_thread = None
is_running = False

# ========== وظائف المساعدة ==========
async def send_message_to_user(chat_id, text):
    """إرسال رسالة إلى مستخدم (للأوامر)"""
    try:
        if bot_instance is None:
            bot_instance = Bot(token=TELEGRAM_TOKEN)
        
        await bot_instance.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode='Markdown'
        )
        logger.info(f"✅ تم إرسال رد إلى {chat_id}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الرسالة: {e}")
        return False

async def send_dhikr_to_all(text):
    """إرسال ذكر إلى جميع المجموعات"""
    try:
        if bot_instance is None:
            bot_instance = Bot(token=TELEGRAM_TOKEN)
        
        success_count = 0
        for group_id in GROUPS:
            try:
                await bot_instance.send_message(
                    chat_id=group_id,
                    text=text,
                    parse_mode='Markdown'
                )
                logger.info(f"✅ تم إرسال ذكر إلى المجموعة {group_id}")
                success_count += 1
            except Exception as e:
                logger.error(f"❌ خطأ في إرسال الذكر للمجموعة {group_id}: {e}")
        
        return success_count > 0
    except Exception as e:
        logger.error(f"❌ خطأ عام في إرسال الأذكار: {e}")
        return False

async def check_and_send_dhikr():
    """فحص الوقت وإرسال الأذكار"""
    global is_running
    
    while is_running:
        try:
            now = datetime.now(TIMEZONE)
            current_time = now.time()
            logger.debug(f"فحص الوقت: {current_time}")
            
            # أذكار الصباح 8:30
            if current_time.hour == MORNING_TIME.hour and current_time.minute == MORNING_TIME.minute:
                await send_dhikr_to_all(MORNING_DHIKR)
                logger.info("✅ تم إرسال أذكار الصباح لجميع المجموعات")
            
            # ذكر "واذكر ربك" 12:00
            elif current_time.hour == NOON_DHIKR_TIME.hour and current_time.minute == NOON_DHIKR_TIME.minute:
                await send_dhikr_to_all(REMEMBER_DHIKR)
                logger.info("✅ تم إرسال ذكر 'واذكر ربك' (الظهر) لجميع المجموعات")
            
            # أذكار المساء 4:00
            elif current_time.hour == EVENING_TIME.hour and current_time.minute == EVENING_TIME.minute:
                await send_dhikr_to_all(EVENING_DHIKR)
                logger.info("✅ تم إرسال أذكار المساء لجميع المجموعات")
            
            # ذكر "واذكر ربك" 6:00
            elif current_time.hour == EVENING_DHIKR2_TIME.hour and current_time.minute == EVENING_DHIKR2_TIME.minute:
                await send_dhikr_to_all(REMEMBER_DHIKR)
                logger.info("✅ تم إرسال ذكر 'واذكر ربك' (المساء) لجميع المجموعات")
            
            # ذكر النوم 11:00
            elif current_time.hour == NIGHT_TIME.hour and current_time.minute == NIGHT_TIME.minute:
                await send_dhikr_to_all(SLEEP_DHIKR)
                logger.info("✅ تم إرسال ذكر النوم لجميع المجموعات")
            
            # انتظر دقيقة قبل الفحص التالي
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"❌ خطأ في الجدولة: {e}")
            await asyncio.sleep(60)

def start_scheduler():
    """بدء جدولة الأذكار في خيط منفصل"""
    global is_running
    
    if not is_running:
        is_running = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(check_and_send_dhikr())

# ========== أوامر البوت ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /start"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name or "المستخدم"
    
    # معرفة إذا كانت المحادثة خاصة أو جماعية
    chat_type = update.effective_chat.type
    
    logger.info(f"📩 أمر /start من: {user_id} ({user_name}) في: {chat_type} (chat_id: {chat_id})")
    
    if chat_type == "private":
        # في الخاص - يرد على الجميع (رسالة مختصرة)
        response_text = (
            "🤖 بوت أذكار الصباح والمساء\n\n"
            "✅ تم تفعيل الإشعارات اليومية\n"
            "⏰ مواعيد الإذكار:\n"
            "• الصباح: 8:30 صباحاً\n"
            "• المساء: 4:00 مساءً\n\n"
            "🤲 لا تنسوا الدعاء لمن كان سبباً في هذا الخير\n"
            "🛠️ الصانع: @Mik_emm"
        )
        
        await update.message.reply_text(response_text, parse_mode='Markdown')
        
        # إذا كان أدمن في الخاص، أرسل رسالة إضافية
        if user_id == ADMIN_ID:
            await update.message.reply_text(
                "⚙️ *وضع الأدمن*\n"
                "يمكنك استخدام:\n"
                "• /status - لعرض حالة البوت\n"
                "• /help - للمساعدة\n\n"
                "✅ البوت يعمل وجدولة الأذكار نشطة.",
                parse_mode='Markdown'
            )
            
            # بدء الجدولة إذا لم تكن تعمل
            global scheduler_thread
            if scheduler_thread is None or not scheduler_thread.is_alive():
                scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
                scheduler_thread.start()
                logger.info("✅ تم تشغيل جدولة الأذكار عبر أمر /start من الأدمن في الخاص")
    
    elif chat_type in ["group", "supergroup"]:
        # في المجموعة - يرد فقط على الأدمن (رسالة مختصرة)
        if user_id == ADMIN_ID:
            response_text = (
                "🤖 بوت أذكار الصباح والمساء\n\n"
                "✅ تم تفعيل الإشعارات اليومية\n"
                "⏰ مواعيد الإذكار:\n"
                "• الصباح: 8:30 صباحاً\n"
                "• المساء: 4:00 مساءً\n\n"
                "🤲 لا تنسوا الدعاء لمن كان سبباً في هذا الخير\n"
                "🛠️ الصانع: @Mik_emm"
            )
            
            await update.message.reply_text(response_text, parse_mode='Markdown')
            
            # بدء الجدولة إذا لم تكن تعمل
            if scheduler_thread is None or not scheduler_thread.is_alive():
                scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
                scheduler_thread.start()
                logger.info("✅ تم تشغيل جدولة الأذكار عبر أمر /start من الأدمن في المجموعة")
        
        else:
            # في المجموعة - لا يرد على الأعضاء العاديين
            logger.info(f"⏭️ تخطي رد على عضو عادي في المجموعة: {user_id} ({user_name})")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /help"""
    chat_type = update.effective_chat.type
    
    if chat_type == "private":
        # في الخاص - يرد للجميع
        await update.message.reply_text(
            "• /start - بدء البوت وعرض المعلومات\n"
            "• /help - عرض هذه الرسالة\n"
            "• /status - حالة البوت\n\n"
            "🛠️ الصانع: @Mik_emm",
            parse_mode='Markdown'
        )
    elif chat_type in ["group", "supergroup"]:
        # في المجموعة - يرد فقط للأدمن
        user_id = update.effective_user.id
        if user_id == ADMIN_ID:
            await update.message.reply_text(
                "• /start - معلومات البوت\n"
                "• /help - هذه الرسالة\n"
                "• /status - حالة البوت\n\n"
                "🛠️ الصانع: @Mik_emm",
                parse_mode='Markdown'
            )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /status"""
    global is_running
    now = datetime.now(TIMEZONE)
    chat_type = update.effective_chat.type
    
    if chat_type == "private":
        # في الخاص - يرد للجميع
        status_text = (
            f"✅ البوت: {'يعمل 🟢' if is_running else 'متوقف 🔴'}\n"
            f"⏰ التوقيت: {now.strftime('%H:%M:%S')}\n"
            f"📅 التاريخ: {now.strftime('%Y-%m-%d')}\n"
            f"🛠️ الصانع: @Mik_emm"
        )
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    elif chat_type in ["group", "supergroup"]:
        # في المجموعة - يرد فقط للأدمن
        user_id = update.effective_user.id
        if user_id == ADMIN_ID:
            status_text = (
                f"✅ البوت: {'يعمل 🟢' if is_running else 'متوقف 🔴'}\n"
                f"⏰ التوقيت: {now.strftime('%H:%M:%S')}\n"
                f"📅 التاريخ: {now.strftime('%Y-%m-%d')}\n"
                f"🛠️ الصانع: @Mik_emm"
            )
            
            await update.message.reply_text(status_text, parse_mode='Markdown')

# ========== تهيئة البوت ==========
def setup_bot():
    """تهيئة البوت وإعداد الأوامر"""
    global application_instance, bot_instance
    
    if application_instance is None:
        try:
            # إنشاء التطبيق
            application_instance = Application.builder().token(TELEGRAM_TOKEN).build()
            
            # إضافة الأوامر
            application_instance.add_handler(CommandHandler("start", start_command))
            application_instance.add_handler(CommandHandler("help", help_command))
            application_instance.add_handler(CommandHandler("status", status_command))
            
            # إنشاء كائن البوت
            bot_instance = Bot(token=TELEGRAM_TOKEN)
            
            # تعيين ويب هوك
            async def set_webhook_async():
                await bot_instance.set_webhook(WEBHOOK_URL)
                logger.info(f"✅ تم تعيين ويب هوك: {WEBHOOK_URL}")
                
                # إرسال رسالة تأكيد للأدمن
                await bot_instance.send_message(
                    chat_id=ADMIN_ID,
                    text="🤖 بوت الأذكار يعمل الآن\n"
                         "✅ تم تهيئة البوت بنجاح\n"
                         "🛠️ الصانع: @Mik_emm",
                    parse_mode='Markdown'
                )
            
            # تشغيل في خيط منفصل
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(set_webhook_async())
            
            # بدء الجدولة
            global scheduler_thread, is_running
            if scheduler_thread is None or not scheduler_thread.is_alive():
                scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
                scheduler_thread.start()
                is_running = True
            
            logger.info("✅ تم تهيئة البوت بنجاح")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة البوت: {e}")

# ========== مسارات Flask ==========
@app.route('/')
def home():
    """الصفحة الرئيسية - نبض الحياة"""
    global is_running
    now = datetime.now(TIMEZONE)
    
    return jsonify({
        "status": "online",
        "bot_running": is_running,
        "timezone": "Africa/Algiers",
        "server_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "message": "البوت يعمل"
    })

@app.route('/health')
def health_check():
    """فحص صحة البوت"""
    global is_running
    return jsonify({
        "status": "healthy",
        "bot_running": is_running,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """استقبال تحديثات ويب هوك من تليجرام"""
    try:
        # تأكد من تهيئة البوت
        if application_instance is None:
            setup_bot()
        
        # تحويل JSON إلى كائن Update
        update_data = request.get_json()
        
        if update_data:
            logger.info(f"📩 بيانات ويب هوك مستلمة: {update_data.get('update_id')}")
            
            # معالجة التحديث
            update = Update.de_json(update_data, application_instance.bot)
            
            # تمرير التحديث إلى المعالجين
            application_instance.update_queue.put_nowait(update)
            
            # معالجة التحديث فوراً
            async def process_update():
                await application_instance.process_update(update)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_update())
            
            return jsonify({"status": "ok", "update_id": update.update_id})
        else:
            logger.warning("📭 استقبال ويب هوك بدون بيانات")
            return jsonify({"status": "no_data"}), 400
            
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة ويب هوك: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/start_bot')
def start_bot_route():
    """بدء البوت عبر رابط الويب"""
    try:
        setup_bot()
        
        return jsonify({
            "success": True,
            "message": "✅ تم تشغيل البوت بنجاح"
        })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"❌ خطأ: {str(e)}"
        })

@app.route('/test')
def test_route():
    """اختبار البوت"""
    try:
        async def test_send():
            test_bot = Bot(token=TELEGRAM_TOKEN)
            await test_bot.send_message(
                chat_id=ADMIN_ID,
                text="✅ اختبار البوت\n"
                     "الحالة: ✅ يعمل بنجاح\n"
                     "🛠️ الصانع: @Mik_emm",
                parse_mode='Markdown'
            )
        
        # تشغيل في خيط منفصل
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(test_send())
        
        return jsonify({"success": True, "message": "✅ تم إرسال رسالة الاختبار للأدمن"})
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ خطأ: {str(e)}"})

# ========== التشغيل الرئيسي ==========
if __name__ == '__main__':
    # تهيئة البوت
    setup_bot()
    
    # تشغيل خادم Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 بدء تشغيل الخادم على المنفذ {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
