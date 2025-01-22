import os
from io import BytesIO
from PIL import Image
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import tempfile

# استبدل 'your_token_here' بالتوكن الخاص بك
TOKEN = '1858200098:AAE0Td0NW92fQQLxfmirC9oXFNjVxvXeo9g'  # أو استخدم os.getenv('TELEGRAM_BOT_TOKEN')

# قاموس لتخزين الصور لكل مستخدم
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('أرسل لي الصور لتحويلها إلى PDF. بعد الانتهاء من إرسال الصور، أرسل /done لدمجها في ملف PDF واحد.')

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    photos = update.message.photo

    # اختيار الصورة ذات الجودة الأعلى (أكبر حجم)
    photo = photos[-1]  # الصورة الأخيرة هي الأكبر حجمًا

    if user_id not in user_data:
        user_data[user_id] = []

    try:
        new_file = await context.bot.get_file(photo.file_id)
        image_file = BytesIO()
        await new_file.download_to_memory(out=image_file)
        image_file.seek(0)  # إعادة تعيين المؤشر

        # حفظ الصورة مؤقتًا على القرص
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(image_file.getvalue())
            user_data[user_id].append(temp_file.name)

        await update.message.reply_text('تم استلام الصورة. يمكنك إرسال المزيد من الصور أو إرسال /done لدمجها في ملف PDF.')
    except Exception as e:
        print(f"Error downloading image: {e}")
        await update.message.reply_text('حدث خطأ أثناء تنزيل الصور.')

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in user_data or not user_data[user_id]:
        await update.message.reply_text('لم يتم إرسال أي صور بعد.')
        return

    await update.message.reply_text('جاري تحويل الصور إلى PDF...')

    try:
        pdf_output = await asyncio.to_thread(convert_images_to_pdf, user_data[user_id])
        if pdf_output:
            await update.message.reply_document(document=InputFile(pdf_output, filename='المهندس سيف.pdf'))
        else:
            await update.message.reply_text('لم أتمكن من تحويل الصور إلى PDF.')
    except Exception as e:
        print(f"Error converting images to PDF: {e}")
        await update.message.reply_text('حدث خطأ أثناء تحويل الصور إلى PDF.')
    finally:
        # تنظيف الملفات المؤقتة وإعادة تعيين القاموس
        for file_path in user_data[user_id]:
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting temporary file: {e}")
        user_data[user_id] = []  # إعادة تعيين القاموس

def convert_images_to_pdf(image_paths):
    image_list = []
    for image_path in image_paths:
        try:
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            image_list.append(img)
        except Exception as e:
            print(f"Error processing image: {e}")
            continue

    output = BytesIO()
    if image_list:
        image_list[0].save(output, save_all=True, append_images=image_list[1:], format='PDF')
        output.seek(0)
        return output
    return None

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("done", done))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    application.run_polling()

# التحقق من أن الكود يعمل كبرنامج رئيسي
if __name__ == "__main__":
    main()