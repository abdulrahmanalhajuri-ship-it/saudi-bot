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
# قاموس لحفظ بيانات كل مستخدم شخصياً
user_custom_data = {}

# قائمة الأكواد ومرجعيات العمليات الصالحة (تبدأ بالكود الافتراضي وتستقبل المراجع اليدوية والتلقائية)
valid_codes = {"1235"}

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

# أمر خاص للأدمن لعرض الأكواد والمراجع الفعّالة حالياً
async def admin_get_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    
    codes_list = ", ".join(valid_codes)
    await update.message.reply_text(
        f"🔑 **أرقام المراجع وأكواد العملية الفعّالة حالياً:**\n`{codes_list}`",
        parse_mode="Markdown"
    )

# أمر خاص للأدمن لإضافة رقم مرجع إيصال جديد يدوياً (من تطبيق جييب أو غيره)
async def admin_add_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    if context.args:
        new_ref_code = context.args[0]
        valid_codes.add(new_ref_code)
        await update.message.reply_text(
            f"✅ **تمت إضافة رقم مرجع العملية بنجاح!**\n\n• المرجع المضاف: `{new_ref_code}`\n• أصبح جاهزاً ليستخدمه الزبون.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "⚠️ الرجاء كتابة رقم مرجع العملية بعد الأمر.\nمثال: `/addcode 17942081231037`",
            parse_mode="Markdown"
        )

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

# معالجة الرسائل والتحقق الصارم
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    user_id = update.effective_user.id
    text = msg.text.strip()
    current_state = user_states.get(user_id)
    username = f"@{update.effective_user.username}" if update.effective_user.username else "بدون معرف"

    if current_state == "completed":
        await msg.reply_text("لقد اخترت الأزرار بالفعل ولا يمكنك التكرار.")
        return

    # الحالة الأولى: استقبال بيانات التسجيل وحفظها
    if current_state == "waiting_for_subscription_text":
        if text.startswith("خطوات التسجيل والإشتراك") or text.startswith("خطوات التسجيل والاشتراك"):
            user_custom_data[user_id] = text
            user_states[user_id] = "waiting_for_code"
            
            await msg.reply_text("✅ تم استقبال بيانات التسجيل بنجاح.\n\nالرجاء إرسال معرف العملية الخاص بك للمتابعة:")
        else:
            await msg.reply_text("❌ الرجاء إدخال بياناتك صحيحة")
        return

    # الحالة الثانية: التحقق من رقم مرجع العملية واستهلاكه فوراً
    if current_state == "waiting_for_code":
        if text in valid_codes:
            # إزالة المرجع المستخدم فوراً لكي لا يتم استخدامه مرة ثانية (استهلاك فوري)
            valid_codes.remove(text)
            
            user_states[user_id] = "choosing"
            
            # توليد كود تلقائي جديد وإضافته للقائمة وإرساله للأدمن
            auto_new_code = generate_new_code()
            valid_codes.add(auto_new_code)

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔑 **تم استخدام رقم مرجع العملية بنجاح وإصدار جديد:**\n\n• المرجع المستهلك: `{text}`\n• الكود التلقائي الجديد الفعّال: `{auto_new_code}`\n• بواسطة المستخدم: `{user_id}` ({username})",
                parse_mode="Markdown"
            )

            keyboard = [
                [
                    InlineKeyboardButton("تأكيد الاشتراك", callback_data="sub_confirm"),
                    InlineKeyboardButton("إلغاء الاشتراك", callback_data="sub_cancel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # استرجاع بيانات المستخدم الشخصية لعرضها تحته
            user_specific_data = user_custom_data.get(user_id, "بيانات التسجيل غير متوفرة")

            await msg.reply_text(
                text=f"إليك بياناتك المسجلة:\n\n{user_specific_data}",
                reply_markup=reply_markup
            )
        else:
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

        await context.bot.send_message(
            chat_id=chat_id,
            text="شكراً لاختياركم شركة تحالف المالية للإستثمار! تم قبول وتأكيد اشتراكك بنجاح. لأي استفسارات، فريق الدعم الفني في خدمتكم"
        )
        
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
    app.add_handler(CommandHandler("codes", admin_get_codes))  # لعرض كل المراجع والأكواد الفعّالة
    app.add_handler(CommandHandler("addcode", admin_add_code))  # لإضافة رقم مرجع إيصال يدوي (مثل إيصال جييب)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("البوت يعمل الآن مع دعم المراجع اليدوية (مثل إيصالات جييب) والتوليد التلقائي...")
    app.run_polling()

if __name__ == "__main__":
    main()
