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
GROUP_ID = "-1002225164483"
WEBHOOK_URL = "https://hosin-q20k.onrender.com/webhook"

# ========== التوقيتات (توقيت الرياض) ==========
TIMEZONE = pytz.timezone('Asia/Riyadh')
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
async def send_dhikr(chat_id, text):
    """إرسال ذكر إلى المجموعة"""
    try:
        if bot_instance is None:
            bot_instance = Bot(token=TELEGRAM_TOKEN)
        
        await bot_instance.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode='Markdown'
        )
        logger.info(f"✅ تم إرسال ذكر إلى {chat_id}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الذكر: {e}")
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
                await send_dhikr(GROUP_ID, MORNING_DHIKR)
                logger.info("✅ تم إرسال أذكار الصباح")
            
            # ذكر "واذكر ربك" 12:00
            elif current_time.hour == NOON_DHIKR_TIME.hour and current_time.minute == NOON_DHIKR_TIME.minute:
                await send_dhikr(GROUP_ID, REMEMBER_DHIKR)
                logger.info("✅ تم إرسال ذكر 'واذكر ربك' (الظهر)")
            
            # أذكار المساء 4:00
            elif current_time.hour == EVENING_TIME.hour and current_time.minute == EVENING_TIME.minute:
                await send_dhikr(GROUP_ID, EVENING_DHIKR)
                logger.info("✅ تم إرسال أذكار المساء")
            
            # ذكر "واذكر ربك" 6:00
            elif current_time.hour == EVENING_DHIKR2_TIME.hour and current_time.minute == EVENING_DHIKR2_TIME.minute:
                await send_dhikr(GROUP_ID, REMEMBER_DHIKR)
                logger.info("✅ تم إرسال ذكر 'واذكر ربك' (المساء)")
            
            # ذكر النوم 11:00
            elif current_time.hour == NIGHT_TIME.hour and current_time.minute == NIGHT_TIME.minute:
                await send_dhikr(GROUP_ID, SLEEP_DHIKR)
                logger.info("✅ تم إرسال ذكر النوم")
            
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
        # في الخاص - يرد على الجميع
        response_text = (
            f"مرحباً {user_name}! 👋\n\n"
            "🤖 *بوت أذكار الصباح والمساء*\n\n"
            "✅ *تم تفعيل الإشعارات اليومية*\n\n"
            "⏰ *مواعيد الأذكار:*\n"
            "• الصباح: 8:30 صباحاً\n"
            "• الظهر: 12:00 (واذكر ربك)\n"
            "• المساء: 4:00 مساءً\n"
            "• العشاء: 6:00 (واذكر ربك)\n"
            "• النوم: 11:00 مساءً\n\n"
            "🤲 *لا تنسوا الدعاء لمن كان سبباً في هذا الخير*\n"
            "🛠️ *الصانع:* @Mik_emm\n"
            "💡 *فكرة:* @mohamedelhocine\n\n"
            "🔗 *رابط البوت:* https://hosin-q20k.onrender.com"
        )
        
        await update.message.reply_text(response_text, parse_mode='Markdown')
        
        # إذا كان أدمن في الخاص، أرسل رسالة إضافية
        if user_id == ADMIN_ID:
            await update.message.reply_text(
                "⚙️ *وضع الأدمن*\n"
                "أنت الأدمن الرئيسي للبوت.\n"
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
        # في المجموعة - يرد فقط على الأدمن
        if user_id == ADMIN_ID:
            response_text = (
                f"مرحباً {user_name} (الأدمن)! 👋\n\n"
                "🤖 *بوت أذكار الصباح والمساء*\n\n"
                "✅ *البوت يعمل في هذه المجموعة*\n\n"
                "⏰ *مواعيد الأذكار:*\n"
                "• الصباح: 8:30 صباحاً\n"
                "• الظهر: 12:00 (واذكر ربك)\n"
                "• المساء: 4:00 مساءً\n"
                "• العشاء: 6:00 (واذكر ربك)\n"
                "• النوم: 11:00 مساءً\n\n"
                "🤲 *لا تنسوا الدعاء لمن كان سبباً في هذا الخير*\n"
                "🛠️ *الصانع:* @Mik_emm\n"
                "💡 *فكرة:* @mohamedelhocine"
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
            # لا نرد مطلقاً على الأعضاء العاديين في المجموعة

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /help"""
    chat_type = update.effective_chat.type
    
    if chat_type == "private":
        # في الخاص - يرد للجميع
        await update.message.reply_text(
            "📖 *مساعدة بوت الأذكار*\n\n"
            "• /start - بدء البوت وعرض المعلومات\n"
            "• /help - عرض هذه الرسالة\n"
            "• /status - حالة البوت\n\n"
            "⏰ *مواعيد الأذكار:*\n"
            "• 8:30 صباحاً - أذكار الصباح\n"
            "• 12:00 ظهراً - واذكر ربك\n"
            "• 4:00 مساءً - أذكار المساء\n"
            "• 6:00 مساءً - واذكر ربك\n"
            "• 11:00 مساءً - ذكر النوم\n\n"
            "🤲 *تذكير:*\n"
            "الأذكار تصل تلقائياً حسب المواعيد المحددة.\n\n"
            "🛠️ الصانع: @Mik_emm\n"
            "💡 فكرة: @mohamedelhocine",
            parse_mode='Markdown'
        )
    elif chat_type in ["group", "supergroup"]:
        # في المجموعة - يرد فقط للأدمن
        user_id = update.effective_user.id
        if user_id == ADMIN_ID:
            await update.message.reply_text(
                "📖 *مساعدة الأدمن*\n\n"
                "• /start - معلومات البوت\n"
                "• /help - هذه الرسالة\n"
                "• /status - حالة البوت\n\n"
                "🛠️ الصانع: @Mik_emm\n"
                "💡 فكرة: @mohamedelhocine",
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
            f"📊 *حالة البوت*\n\n"
            f"✅ البوت: {'يعمل 🟢' if is_running else 'متوقف 🔴'}\n"
            f"⏰ التوقيت الحالي: {now.strftime('%H:%M:%S')}\n"
            f"📅 التاريخ: {now.strftime('%Y-%m-%d')}\n\n"
            f"👤 المستخدم: {update.effective_user.first_name}\n"
            f"🔗 الرابط: https://hosin-q20k.onrender.com\n"
            f"🛠️ الصانع: @Mik_emm\n"
            f"💡 فكرة: @mohamedelhocine"
        )
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    elif chat_type in ["group", "supergroup"]:
        # في المجموعة - يرد فقط للأدمن
        user_id = update.effective_user.id
        if user_id == ADMIN_ID:
            status_text = (
                f"📊 *حالة البوت (للأدمن)*\n\n"
                f"✅ البوت: {'يعمل 🟢' if is_running else 'متوقف 🔴'}\n"
                f"⏰ التوقيت: {now.strftime('%H:%M:%S')}\n"
                f"📅 التاريخ: {now.strftime('%Y-%m-%d')}\n"
                f"👥 المجموعة: {GROUP_ID}\n\n"
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
                    text="🤖 *بوت الأذكار يعمل الآن!*\n\n"
                         "✅ تم تهيئة البوت بنجاح\n"
                         "✅ تم تعيين ويب هوك\n"
                         "✅ البوت جاهز لاستقبال الأوامر\n\n"
                         "🛠️ الصانع: @Mik_emm\n"
                         "💡 فكرة: @mohamedelhocine",
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
        "service": "Dhikr Bot",
        "admin_id": ADMIN_ID,
        "group_id": GROUP_ID,
        "creator": "@Mik_emm",
        "idea_owner": "@mohamedelhocine",
        "server_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "Asia/Riyadh",
        "webhook": WEBHOOK_URL,
        "features": {
            "private_chat": "يرد على جميع المستخدمين",
            "group_chat": "يرد فقط على الأدمن",
            "auto_messages": "نشط حسب الجدول الزمني"
        }
    })

@app.route('/health')
def health_check():
    """فحص صحة البوت"""
    global is_running
    return jsonify({
        "status": "healthy",
        "bot_running": is_running,
        "webhook_active": True,
        "timestamp": datetime.now().isoformat(),
        "last_heartbeat": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            "message": "✅ تم تشغيل البوت بنجاح",
            "webhook": WEBHOOK_URL,
            "schedule_started": True,
            "admin_id": ADMIN_ID,
            "note": "يمكنك الآن إرسال /start في الخاص أو في المجموعة"
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
                text="✅ *اختبار البوت*\n\n"
                     "هذه رسالة اختبارية من بوت الأذكار.\n"
                     "الحالة: ✅ يعمل بنجاح\n"
                     "ويب هوك: ✅ مفعل\n"
                     "الجدولة: ✅ نشطة\n\n"
                     "🔗 الرابط: https://hosin-q20k.onrender.com\n"
                     "🛠️ الصانع: @Mik_emm\n"
                     "💡 فكرة: @mohamedelhocine",
                parse_mode='Markdown'
            )
        
        # تشغيل في خيط منفصل
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(test_send())
        
        return jsonify({"success": True, "message": "✅ تم إرسال رسالة الاختبار للأدمن"})
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ خطأ: {str(e)}"})

# ========== معالج تحديثات البوت ==========
async def process_pending_updates():
    """معالجة التحديثات المعلقة"""
    global application_instance
    while True:
        try:
            if application_instance:
                async with application_instance:
                    await application_instance.start()
                    await application_instance.updater.start_polling()
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"خطأ في معالجة التحديثات: {e}")
            await asyncio.sleep(5)

# ========== التشغيل الرئيسي ==========
if __name__ == '__main__':
    # بدء معالجة التحديثات في خيط منفصل
    update_thread = threading.Thread(target=lambda: asyncio.run(process_pending_updates()), daemon=True)
    update_thread.start()
    
    # تهيئة البوت
    setup_bot()
    
    # تشغيل خادم Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 بدء تشغيل الخادم على المنفذ {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
