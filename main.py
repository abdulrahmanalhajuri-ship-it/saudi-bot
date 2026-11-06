import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# تفعيل تسجيل الأخطاء لمتابعة أداء البوت
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- الإعدادات الأساسية ---
ADMIN_ID = 7004113433  # معرف الأدمن الخاص بك
SUPPORT_HANDLE = "@AbuAbdulAlziz"

# قاعدة بيانات مؤقتة في الذاكرة
VALID_CODES = set(["123456", "TAHALUF2026"])  # أمثلة ابتدائية للأكواد
USED_CODES = set()
USER_CODES = {}


# أمر /start الترحيبي مع أزرار التحكم السفلية والتفاعلية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    welcome_text = (
        f"أهلاً بك يا *{user.first_name}* في البوت الرسمي لشركة **تحالف المالية للاستثمار** 🤝📈\n\n"
        "من خلال هذا البوت، تقدر تتابع استثماراتك بكل سهولة وأمان:\n"
        "• تأكيد هوية المستثمرين وبياناتهم بدقة عالية.\n"
        "• توثيق الاشتراكات والمحافظ الاستثمارية فوراً.\n"
        "• متابعة وتنظيم سحوبات الأرباح بشكل آلي ومنتظم.\n\n"
        "استثمر بثقة، ودعنا نعتني بالباقي! 📊✨\n\n"
        "اختر أحد الخيارات أدناه أو أرسل رقم المرجع الخاص بك:"
    )

    # أزرار تفاعلية أسفل الرسالة (Inline)
    keyboard = [
        [
            InlineKeyboardButton("📥 إيداع", callback_data="btn_deposit"),
            InlineKeyboardButton("📤 سحب", callback_data="btn_withdraw")
        ],
        [InlineKeyboardButton("💬 التواصل مع الدعم الفني", url=f"https://t.me/AbuAbdulAlziz")],
        [InlineKeyboardButton("📊 الاستعلام عن حالة الحساب", callback_data="check_status")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)


# أمر خاص بالأدمن لإضافة أكواد مراجع جديدة: /addcode <code_number>
async def add_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ عذراً، هذا الأمر مخصص للأدمن فقط.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("⚠️ يرجى كتابة الكود بعد الأمر. مثال:\n`/addcode 987654`", parse_mode="Markdown")
        return

    new_code = args[0]
    if new_code in VALID_CODES or new_code in USED_CODES:
        await update.message.reply_text(f"⚠️ الكود `{new_code}` موجود مسبقاً أو تم استخدامه من قبل.", parse_mode="Markdown")
        return

    VALID_CODES.add(new_code)
    await update.message.reply_text(f"✅ تم إضافة مرجع الإيصال بنجاح وتفعيله:\n`{new_code}`", parse_mode="Markdown")


# استقبال الرسائل النصية (أكواد المراجع والإيصالات) دون أي تأثير على الأزرار
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text in VALID_CODES:
        VALID_CODES.remove(text)
        USED_CODES.add(text)
        USER_CODES[user_id] = text

        success_msg = (
            "✅ **تم التحقق من مرجع العملية بنجاح!**\n\n"
            f"🔹 مرجعك الموثق: `{text}`\n"
            "تم ربط هذا المرجع بحسابك بنجاح وأصبح خاصاً بك وحدك.\n"
            f"لأي استفسار إضافي، تواصل معنا عبر الدعم الفني: {SUPPORT_HANDLE}"
        )
        await update.message.reply_text(success_msg, parse_mode="Markdown")

    elif text in USED_CODES:
        await update.message.reply_text(
            "⚠️ **عذراً، هذا المرجع تم استخدامه مسبقاً ولا يمكن تكراره.**\n"
            f"إذا واجهتك مشكلة، تواصل فوراً مع الدعم الفني: {SUPPORT_HANDLE}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "مرحباً بك! يرجى إرسال رقم مرجع الإيصال الصحيح، أو استخدام أزرار (إيداع / سحب) أو التواصل مع فريق الدعم الفني.\n"
            f"الدعم الفني: {SUPPORT_HANDLE}"
        )


# التعامل مع الأزرار التفاعلية (الإيداع، السحب، والحالة)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "btn_deposit":
        deposit_text = (
            "📥 **تعليمات الإيداع والاستثمار:**\n\n"
            "لإتمام عملية الإيداع وتوثيق محفظتك الاستثمارية:\n"
            "1. قم بتحويل المبلغ إلى الحساب المعتمد للشركة.\n"
            "2. أرسل إيصال التحويل أو رقم المرجع هنا في البوت.\n"
            "3. سيتم مراجعة العملية وربطها فوراً.\n\n"
            f"للاستفسار أو طلب تفاصيل الحساب، تواصل مع الدعم الفني: {SUPPORT_HANDLE}"
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
        await query.edit_message_text(deposit_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "btn_withdraw":
        withdraw_text = (
            "📤 **طلب سحب الأرباح:**\n\n"
            "لسحب أرباحك أو أصولك المالية بكل سهولة:\n"
            "• تأكد من ربط حسابك أو مرجعك الموثق مسبقاً.\n"
            "• تواصل مباشرة مع الدعم الفني لتأكيد عملية السحب وتحويل المستحقات.\n\n"
            f"معرف الدعم المعتمد للسحب: {SUPPORT_HANDLE}"
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
        await query.edit_message_text(withdraw_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "check_status":
        user_code = USER_CODES.get(user_id, "لا يوجد مرجع نشط حالياً")
        status_text = (
            "📊 **بيانات حسابك الاستثماري:**\n\n"
            f"👤 المعرف: `{user_id}`\n"
            f"🔗 المرجع النشط: `{user_code}`\n"
            f"📌 حالة الحساب: قيد Mتابعة والتوثيق المالي.\n\n"
            f"للمساعدة الفورية: {SUPPORT_HANDLE}"
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
        await query.edit_message_text(status_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "back_to_main":
        user = query.from_user
        main_text = (
            f"أهلاً بك يا *{user.first_name}* من جديد في القائمة الرئيسية لشركة **تحالف المالية للاستثمار** 🤝📈\n\n"
            "اختر أحد الخيارات أدناه:"
        )
        keyboard = [
            [
                InlineKeyboardButton("📥 إيداع", callback_data="btn_deposit"),
                InlineKeyboardButton("📤 سحب", callback_data="btn_withdraw")
            ],
            [InlineKeyboardButton("💬 التواصل مع الدعم الفني", url=f"https://t.me/AbuAbdulAlziz")],
            [InlineKeyboardButton("📊 الاستعلام عن حالة الحساب", callback_data="check_status")]
        ]
        await query.edit_message_text(main_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


def main():
    TOKEN = "YOUR_BOT_TOKEN_HERE"  # ضع التوكن هنا

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addcode", add_code))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 بوت تحالف المالية للإستثمار يعمل الآن بنجاح مع أزرار الإيداع والسحب...")
    app.run_polling()


if __name__ == "__main__":
    main()
