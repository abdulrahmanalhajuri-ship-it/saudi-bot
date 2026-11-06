import logging
import os
import random
import string
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
ADMIN_ID = 7004113433  # معرف الأدمن الخاص بك لتلقي الإشعارات والمعرفات الجديدة

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# قالب البيانات الثابت الذي يظهر بعد إدخال معرف العملية الصحيح
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

# المتغير العالمي لمعرف العملية الحالي (يبدأ بـ 1235)
current_valid_code = "1235"

def generate_new_code() -> str:
    """توليد معرف عملية جديد وعشوائي وآمن"""
    chars = string.ascii_uppercase + string.digits
    return "CSO" + "".join(random.choices(chars, k=10))

# دالة برمجية تقديرية لتقدير عمر حساب تيليجرام بناءً على الـ ID
def estimate_account_age(user_id: int) -> str:
    if user_id < 10000000:
        return "حساب قديم جداً (من أوائل الحسابات في المنصة)"
    elif user_id < 100000000:
        return "حساب قديم (بين 2014 - 2016 تقريباً)"
    elif user_id < 500000000:
        return "حساب متوسط القدَم (بین 2016 - 2019 تقريباً)"
    elif user_id < 1000000000:
        return "حساب نشط منذ عدة سنوات (بين 2019 - 2022 تقريباً)"
    else:
        return "حساب حديث نسبياً (أو تم إنشاؤه في السنوات الأخيرة)"

# الخطوة 1: استقبال /start وطلب إرسال بيانات التسجيل من الزبون أولاً
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_states[user_id] = "waiting_for_subscription_text"
    
    age_estimation = estimate_account_age(user_id)
    
    welcome_msg = (
        f"أهلاً بك في شركة تحالف المالية للإستثمار 🇸🇦\n\n"
        f"معلومات حسابك:\n"
        f"• معرفك (ID): `{user_id}`\n"
        f"• تقدير الحساب: {age_estimation}\n\n"
        f"الرجاء إرسال بيانات التسجيل الخاصة بك الآن (الاسم، رقم الحساب، رقم الجوال، والمبلغ)..."
    )
    
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

# معالجة الرسائل والتحقق بالترتيب الصحيح
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_valid_code
    msg = update.message
    if not msg or not msg.text:
        return

    user_id = update.effective_user.id
    text = msg.text.strip()
    current_state = user_states.get(user_id)

    # إذا كان المستخدم قد أنهى اختياره مسبقاً
    if current_state == "completed":
        await msg.reply_text("لقد اخترت الأزرار بالفعل ولا يمكنك التكرار.")
        return

    # الحالة الأولى: البوت ينتظر من الزبون إرسال بيانات/خطوات التسجيل الصحيحة
    if current_state == "waiting_for_subscription_text":
        # التحقق مما إذا كانت الرسالة تحتوي على عبارة أو كلمات تدل على خطوات التسجيل
        if "خطوات التسجيل" in text or "الاسم" in text or "رقم الحساب" in text:
            user_states[user_id] = "waiting_for_code"
            await msg.reply_text("تم استقبال بياناتك بنجاح.\n\nالرجاء إرسال معرف العملية الخاص بك (مثال: 1235):")
        else:
            # إذا لم يرسل البيانات الصحيحة، يعرض له الطلب بدقة كما طلبت
            await msg.reply_text("الرجاء إرسال بيانات التسجيل الخاصة بك الآن (الاسم، رقم الحساب، رقم الجوال، والمبلغ)...")
        return

    # الحالة الثانية: البوت ينتظر إدخال معرف العملية الصحيح (مثل 1235)
    if current_state == "waiting_for_code":
        if text == current_valid_code:
            user_states[user_id] = "choosing"
            
            keyboard = [
                [
                    InlineKeyboardButton("تأكيد الاشتراك", callback_data="sub_confirm"),
                    InlineKeyboardButton("إلغاء الاشتراك", callback_data="sub_cancel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # عرض القالب الثابت وتحته الأزرار
            await msg.reply_text(
                text=CUSTOMER_DATA_TEMPLATE,
                reply_markup=reply_markup
            )
        else:
            # رسالة خطأ معرف العملية تظهر حصراً هنا فقط عندما يكون في مرحلة إدخال المعرف
            await msg.reply_text("❌ معرف العملية غير صحيح. يرجى إرسال معرف العملية الصحيح")

# معالجة ضغط الأزرار ومنع التكرار وتوليد معرف جديد للأدمن
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_valid_code
    query = update.callback_query
    await query.answer()
    
    data = query.data  
    chat_id = query.message.chat_id
    user = query.from_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "بدون معرف"

    # التحقق من عدم التكرار
    if user_states.get(user_id) == "completed":
        await query.message.reply_text("لقد اخترت الأزرار بالفعل.")
        return

    if data == "sub_cancel":
        user_states[user_id] = "completed"
        
        await context.bot.send_message(
            chat_id=chat_id,
            text="سيتم استرجاع المبلغ على نفس الحساب خلال 48 ساعة"
        )
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⚠️ تنبيه: قام شخص بإلغاء الاشتراك!\n\n• معرف المستخدم: `{user_id}`\n• اليوزر: {username}\n• الاختيار: إلغاء الاشتراك ❌",
            parse_mode="Markdown"
        )

    elif data == "sub_confirm":
        user_states[user_id] = "completed"
        
        # 1. توليد معرف عملية جديد وتحديثه للبوت فوراً
        new_code = generate_new_code()
        current_valid_code = new_code

        # 2. إرسال المعرف الجديد للأدمن حصراً على معرف 7004113433
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔑 **إصدار معرف عملية جديد تلقائياً:**\n\n• المعرف الجديد الفعّال: `{new_code}`\n• تم استهلاك المعرف السابق بواسطة المستخدم: `{user_id}` ({username})",
            parse_mode="Markdown"
        )

        # 3. الرد للمستخدم بنجاح الاشتراك
        await context.bot.send_message(
            chat_id=chat_id,
            text="شكراً لاختياركم شركة تحالف المالية للإستثمار! تم قبول وتأكيد اشتراكك بنجاح. لأي استفسارات، فريق الدعم الفني في خدمتكم"
        )
        
        # 4. إشعار تأكيد الاشتراك للأدمن
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

    print("البوت يعمل الآن بالتدقيق الصحيح للخطوات ومعرفات العمليات المتجددة...")
    app.run_polling()

if __name__ == "__main__":
    main()
