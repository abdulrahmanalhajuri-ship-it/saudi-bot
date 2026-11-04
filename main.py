
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

# إعداد السجل (Logging)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


# 1. أمر البداية لإرسال القائمة الرئيسية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("📦 باقات السعودية العادية", callback_data="saudi_packages")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # التحقق مما إذا كان الأمر قادمًا من رسالة أو زر
    if update.message:
        await update.message.reply_text("أهلاً بك! اختر من العروض المتاحة:", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text="أهلاً بك! اختر من العروض المتاحة:", reply_markup=reply_markup)


# 2. التعامل مع الأزرار والضغطات
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data

    # عند الضغط على زر "باقات السعودية العادية"
    if data == "saudi_packages":
        keyboard = [
            [InlineKeyboardButton("باقة 30 جيجا", callback_data="pkg_30gb")],
            [InlineKeyboardButton("باقة 50 جيجا", callback_data="pkg_50gb")],
            [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_to_start")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="اختر الباقة المطلوبة لمعرفة التفاصيل:",
            reply_markup=reply_markup,
        )

    # تفاصيل الباقة الأولى (مثال: 30 جيجا)
    elif data == "pkg_30gb":
        details = (
            "📌 *تفاصيل باقة 30 جيجا العادية:*\n"
            "- الإنترنت: 30 جيجابايت\n"
            "- المكالمات: لشبكة سوا / السعودية\n"
            "- المدة: 28 يوماً\n"
            "- السعر: يرجى التواصل لمعرفة السعر الحالي.\n\n"
            "اضغط على الزر أدناه لملء تفاصيل اشتراكك 👇"
        )
        keyboard = [
            [InlineKeyboardButton("✅ اخترت الباقة، اضغط هنا لملء التفاصيل", callback_data="fill_details_30")],
            [InlineKeyboardButton("🔙 رجوع للباقات", callback_data="saudi_packages")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=details, reply_markup=reply_markup, parse_mode="Markdown")

    # تفاصيل الباقة الثانية (مثال: 50 جيجا)
    elif data == "pkg_50gb":
        details = (
            "📌 *تفاصيل باقة 50 جيجا العادية:*\n"
            "- الإنترنت: 50 جيجابايت\n"
            "- المكالمات: لجميع الشبكات\n"
            "- المدة: 30 يوماً\n"
            "- السعر: يرجى التواصل لمعرفة السعر الحالي.\n\n"
            "اضغط على الزر أدناه لملء تفاصيل اشتراكك 👇"
        )
        keyboard = [
            [InlineKeyboardButton("✅ اخترت الباقة، اضغط هنا لملء التفاصيل", callback_data="fill_details_50")],
            [InlineKeyboardButton("🔙 رجوع للباقات", callback_data="saudi_packages")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=details, reply_markup=reply_markup, parse_mode="Markdown")

    # زر الرجوع للقائمة الرئيسية
    elif data == "back_to_start":
        await start(update, context)

    # عند الضغط على زر إكمال التفاصيل (هنا يمكنك فتح ConversationHandler أو إرسال رابط/طلب بيانات)
    elif data.startswith("fill_details_"):
        pkg_id = data.split("_")[-1]
        await query.edit_message_text(
            text=f"📝 ممتاز! لقد اخترت الباقة (رقم {pkg_id}).\nالرجاء إرسال البيانات المطلوبة الآن (مثل رقم الهوية أو رقم الجوال المراد شحنه):"
        )
        # ملاحظة: هنا يمكنك تفعيل حالة محادثة (ConversationHandler) لجمع البيانات خطوة بخطوة من المستخدم.


# التشغيل الرئيسي للبوت
def main() -> None:
    # ضع التوكن الخاص ببوتك هنا
    application = Application.builder().token("YOUR_BOT_TOKEN_HERE").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    # تشغيل البوت
    application.run_polling()


if __name__ == "__main__":
    main()
