import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# التوكن الخاص ببوتك الجديد
TOKEN = "9015540423:AAF1I4ZPdzybeoE4LjCyobw-kg86mgjRmDo"

async def add_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ الرجاء كتابة اسم الباقة أو العرض بعد الأمر.\nمثال:\n/add 💎 الباقة الماسية (VIP)")
        return
    
    new_package_title = " ".join(args)
    
    filename = "packages.json"
    data = {"packages": []}
    
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            pass

    new_item = {
        "title": new_package_title,
        "action": f"alert('تم اختيار: {new_package_title}')"
    }
    data["packages"].append(new_item)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(f"✅ تمت إضافة الباقة بنجاح للموقع:\n{new_package_title}\n\nستظهر في واجهة الموقع فوراً!")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # أمر إضافة باقة جديدة: /add اسم_الباقة
    app.add_handler(CommandHandler("add", add_package))
    
    print("بوت إدارة الموقع يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
