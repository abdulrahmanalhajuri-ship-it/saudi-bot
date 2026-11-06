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

# قاموس لتتبع حالة كل مستخدم
user_states = {}
# قاموس لحفظ بيانات كل مستخدم شخصياً لتظهر له تحت الأزرار
user_custom_data = {}

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
        return "حساب متوسط القدَم (بين 2016 - 2019 تقريباً)"
    elif user_id < 1000000000:
        return "حساب نشط منذ عدة سنوات (بين 2019 - 2022 تقريباً)"
    else:
        return "حساب حديث نسبياً (أو تم إنشاؤه في السنوات الأخيرة)"

# الخطوة 1: استقبال /start وعرض الترحيب
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_states[user_id] = "waiting_for_subscription_text"
    
    age_estimation = estimate_account_age(user_id)
    
    welcome_msg = (
        f"🌟 أهلاً بك في شركة تحالف المالية للإستثمار 🇸🇦\n"
        f"نسعد بانضمامك إلينا لنخطو معاً نحو مستقبل استثماري متميز ومربح.\n\n"
        f"📊 معلومات حسابك:\n"
        f"• معرفك الشخصي (ID): `{user_id}`\n"
        f"• تقدير الحساب: {age_estimation}\n\n"
        f"الرجاء إرسال بياناتك صحيحة ليتم تعرف عليك انظام"
    )
    
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

# معالجة الرسائل والتحقق الصارم وحفظ بيانات المستخدم
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_valid_code
    msg = update.message
    if not msg or not msg.text:
        return

    user_id = update.effective_user.id
    text = msg.text.strip()
    current_state = user_states.get(user_id)
    username = f"@{update.effective_user.username}" if update.effective_user.username else "بدون معرف"

    # إذا كان المستخدم قد أنهى اختياره مسبقاً
    if current_state == "completed":
        await msg.reply_text("لقد اخترت الأزرار بالفعل ولا يمكنك التكرار.")
        return

    # الحالة الأولى: استقبال بيانات التسجيل والتحقق من بدايتها وحفظها
    if current_state == "waiting_for_subscription_text":
        if text.startswith("خطوات التسجيل والإشتراك") or text.startswith("خطوات التسجيل والاشتراك"):
            # حفظ بيانات هذا المستخدم خصيصاً لتعرض له لاحقاً
            user_custom_data[user_id] = text
            user_states[user_id] = "waiting_for_code"
            
            await msg.reply_text("✅ تم استقبال بيانات التسجيل بنجاح.\n\nالرجاء إرسال معرف العملية الخاص بك للمتابعة:")
        else:
            await msg.reply_text("❌ الرجاء إدخال بياناتك صحيحة")
        return

    # الحالة الثانية: التحقق من معرف العملية واستهلاكه فوراً وعرض بيانات المستخدم الخاصة به
    if current_state == "waiting_for_code":
        if text == current_valid_code:
            user_states[user_id] = "choosing"
            
            # --- الإستهلاك الفوري للمعرف وتوليد جديد وإرساله للأدمن فوراً ---
            old_code = current_valid_code
            new_code = generate_new_code()
            current_valid_code = new_code

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔑 **تم استخدام معرف العملية وإصدار جديد فوراً:**\n\n• المعرف المستهلك: `{old_code}`\n• المعرف الجديد الفعّال الآن: `{new_code}`\n• بواسطة المستخدم: `{user_id}` ({username})",
                parse_mode="Markdown"
            )
            # -----------------------------------------------------------------

            keyboard = [
                [
                    InlineKeyboardButton("تأكيد الاشتراك", callback_data="sub_confirm"),
                    InlineKeyboardButton("إلغاء الاشتراك", callback_data="sub_cancel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # استرجاع بيانات المستخدم الشخصية التي أرسلها هو بنفسه لعرضها تحت الأزرار
            user_specific_data = user_custom_data.get(user_id, "بيانات التسجيل غير متوفرة")

            # عرض بيانات المستخدم الشخصية وتحتها الأزرار الخاصة به
            await msg.reply_text(
                text=f"إليك بياناتك المسجلة:\n\n{user_specific_data}",
                reply_markup=reply_markup
            )
        else:
            # رسالة خطأ معرف العملية
            await msg.reply_text("❌ معرف العملية غير صحيح. يرجى إرسال معرف العملية الصحيح")

# معالجة ضغط الأزرار ومنع التكرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

        # الرد للمستخدم بنجاح الاشتراك
        await context.bot.send_message(
            chat_id=chat_id,
            text="شكراً لاختياركم شركة تحالف المالية للإستثمار! تم قبول وتأكيد اشتراكك بنجاح. لأي استفسارات، فريق الدعم الفني في خدمتكم"
        )
        
        # إشعار تأكيد الاشتراك للأدمن
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

    print("البوت يعمل الآن بمعالجة البيانات الخاصة بكل مستخدم على حدة...")
    app.run_polling()

if __name__ == "__main__":
    main()
