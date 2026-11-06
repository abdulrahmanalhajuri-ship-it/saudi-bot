import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# جلب التوكن تلقائياً من متغيرات البيئة في Railway
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7912849071  # معرفك الخاص لتلقي الإشعارات

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# بيانات التسجيل الخاصة بالزبون
CUSTOMER_DATA_TEMPLATE = """خطوات التسجيل والإشتراك
ــــــــــــــــــــــــــــــــــــــ🇸🇦
الاسم الرباعي :/                                 
ماجد دخيل الله الجهني🇸🇦
رقم حسابك ألبنكي والايبان/       
260000010006080404601

SA56 8000 0260 6080 1040 4601

رقم الجوال:/                                     
0595950436🇸🇦
( المبلغ الي تبي فيه الإشتراك                   
1000🇸🇦

هذا البيانات نحتاجها عند توزيع الارباح"""

# قاموس لتتبع حالة كل مستخدم
user_states = {}

# دالة برمجية تقديرية لتقدير عمر حساب تيليجرام بناءً على الـ ID
def estimate_account_age(user_id: int) -> str:
    if user_id < 10000000:
        return "حساب قديم جداً (من أوائل الحسابات في المنصة)"
    elif user_id < 100000000:
        return "حساب قديم (بين 2014 - 2016 تقريباً)"
    elif user_id < 500000000:
        return "حساب متوسط القدَم (بين 2016 - 2019 تقريباً)"
    elif user_id < 1000000000:
        return "حساب نشط منذ عدة سنوات (بين 2019 - 2022 تقريباً)"
    else:
        return "حساب حديث نسبياً (أو تم إنشاؤه في السنوات الأخيرة)"

# الخطوة 1: استقبال /start وطلب معرف العملية مع عرض تقييم الحساب
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_states[user_id] = "waiting_for_code"
    
    age_estimation = estimate_account_age(user_id)
    
    welcome_msg = (
        f"أهلاً بك في شركة تحالف المالية للإستثمار 🇸🇦\n\n"
        f"معلومات حسابك:\n"
        f"• معرفك (ID): `{user_id}`\n"
        f"• تقدير الحساب: {age_estimation}\n\n"
        f"يرجى إرسال معرف العملية الخاص بك للمتابعة:"
    )
    
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

# استقبال معرف العملية وعرض البيانات مع الأزرار
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    user_id = update.effective_user.id
    text = msg.text.strip()

    current_state = user_states.get(user_id)

    # إذا كان المستخدم قد أنهى اختياره مسبقاً وحاول إرسال رسائل أخرى
    if current_state == "completed":
        await msg.reply_text("لقد تم اختيارك في الأزرار السابقة")
        return

    if current_state == "waiting_for_code":
        if text == "CSO261104-10RJ4GU85H" or text.startswith("CSO"):
            user_states[user_id] = "choosing"
            
            keyboard = [
                [
                    InlineKeyboardButton("تأكيد الاشتراك", callback_data="sub_confirm"),
                    InlineKeyboardButton("إلغاء الاشتراك", callback_data="sub_cancel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await msg.reply_text(
                text=CUSTOMER_DATA_TEMPLATE,
                reply_markup=reply_markup
            )
        else:
            await msg.reply_text("❌ معرف العملية غير صحيح. يرجى إرسال المعرف الصحيح")

# معالجة ضغط الأزرار ومنع التكرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data  
    chat_id = query.message.chat_id
    user = query.from_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "بدون معرف"

    # التحقق مما إذا كان قد اختار مسبقاً
    if user_states.get(user_id) == "completed":
        await query.message.reply_text("لقد تم اختيارك في الأزرار السابقة")
        return

    if data == "sub_cancel":
        user_states[user_id] = "completed"  # تثبيت الحالة أنه اختار انتهى
        
        # الرد للمستخدم
        await context.bot.send_message(
            chat_id=chat_id,
            text="سيتم استرجع المبلغ على نفس الحساب خلال 48 ساعه"
        )
        # إرسال إشعار لك كمدير
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⚠️ تنبيه: قام شخص بإلغاء الاشتراك!\n\n• معرف المستخدم: `{user_id}`\n• اليوزر: {username}\n• الاختيار: إلغاء الاشتراك ❌",
            parse_mode="Markdown"
        )

    elif data == "sub_confirm":
        user_states[user_id] = "completed"  # تثبيت الحالة أنه اختار انتهى
        
        # الرد للمستخدم
        await context.bot.send_message(
            chat_id=chat_id,
            text="شكراً لاختياركم شركة تحالف المالية للإستثمار! تم قبول وتأكيد اشتراكك بنجاح. لأي استفسارات، فريق الدعم الفني في خدمتكم"
        )
        # إرسال إشعار لك كمدير
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"✅ تنبيه: قام شخص بتأكيد اشتراكه بنجاح!\n\n• معرف المستخدم: `{user_id}`\n• اليوزر: {username}\n• الاختيار: تأكيد الاشتراك ✔️",
            parse_mode="Markdown"
        )

def main():
    if not TOKEN:
        raise ValueError("❌ خطأ: لم يتم تعيين متغير البيئة BOT_TOKEN في إعدادات المنصة!")
        
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("البوت يعمل الآن بسريّة تامة وإشعارات الأدمن ومنع التكرار...")
    app.run_polling()

if __name__ == "__main__":
    main()
