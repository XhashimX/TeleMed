import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters

# الرمز الخاص بالبوت
TOKEN = '1970905102:AAF3r1G11MOHFtETvTGDlw3AM1vbvJGluNc'

# تحميل البيانات من ملف JSON
def load_data():
    with open('topics.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# حفظ البيانات إلى ملف JSON
def save_data(data):
    with open('topics.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

topics = load_data()

# تهيئة ملفات السجل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

# دالة بدء البوت
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton(device, callback_data=device)] for device in topics]
    keyboard.append([InlineKeyboardButton("إضافة جهاز جديد", callback_data='add_device')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('اختر جهاز من أجهزة الجسم أو أضف جهازاً جديداً:', reply_markup=reply_markup)

# دالة استجابة الأزرار
async def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    selection = query.data

    if selection == 'add_device':
        await query.edit_message_text(text="أرسل اسم الجهاز الجديد:")
        context.user_data['adding_device'] = True
        return

    if 'adding_device' in context.user_data and context.user_data['adding_device']:
        topics[selection] = {"الأعراض": {}}
        save_data(topics)
        await query.edit_message_text(text=f"تم إضافة الجهاز: {selection}. الآن أرسل الأعراض لهذا الجهاز.")
        context.user_data['current_device'] = selection
        context.user_data['adding_device'] = False
        context.user_data['adding_symptoms'] = True
        return

    if 'adding_symptoms' in context.user_data and context.user_data['adding_symptoms']:
        device = context.user_data['current_device']
        topics[device]['الأعراض'][selection] = []
        save_data(topics)
        await query.edit_message_text(text=f"تم إضافة العرض: {selection}. الآن أرسل الأمراض المرتبطة بهذا العرض.")
        context.user_data['current_symptom'] = selection
        context.user_data['adding_symptoms'] = False
        context.user_data['adding_diseases'] = True
        return

    if 'adding_diseases' in context.user_data and context.user_data['adding_diseases']:
        device = context.user_data['current_device']
        symptom = context.user_data['current_symptom']
        topics[device]['الأعراض'][symptom].append(selection)
        save_data(topics)
await query.edit_message_text(text=f"تم إضافة المرض: {selection}. هل تريد إضافة المزيد؟ إذا نعم، أرسل 'نعم'. إذا لا، أرسل 'لا'.")
        context.user_data['adding_diseases'] = False
        return

    if selection in topics:
        symptoms_keyboard = [
            [InlineKeyboardButton(symptom, callback_data=f"{selection} - {symptom}") for symptom in topics[selection]["الأعراض"]]
        ]
        symptoms_keyboard.append([InlineKeyboardButton("إضافة عرض جديد", callback_data='add_symptom')])
        symptoms_keyboard.append([InlineKeyboardButton("Back", callback_data='back')])
        reply_markup = InlineKeyboardMarkup(symptoms_keyboard)
        await query.edit_message_text(text=f"اختر عرض من أعراض {selection}:", reply_markup=reply_markup)

    if selection == 'add_symptom':
        await query.edit_message_text(text="أرسل اسم العرض الجديد:")
        context.user_data['adding_symptom'] = True
        return

    if 'adding_symptom' in context.user_data and context.user_data['adding_symptom']:
        device = context.user_data['current_device']
        context.user_data['current_symptom'] = selection
        topics[device]['الأعراض'][selection] = []
        save_data(topics)
        await query.edit_message_text(text=f"تم إضافة العرض: {selection}. الآن أرسل الأمراض المرتبطة بهذا العرض.")
        context.user_data['adding_symptom'] = False
        context.user_data['adding_diseases'] = True
        return

    elif ' - ' in selection:
        device, symptom = selection.split(' - ')
        diseases_keyboard = [
            [InlineKeyboardButton(disease, callback_data=f"disease-{disease}") for disease in topics[device]["الأعراض"][symptom]]
        ]
        diseases_keyboard.append([InlineKeyboardButton("إضافة مرض جديد", callback_data='add_disease')])
        diseases_keyboard.append([InlineKeyboardButton("Back", callback_data=device)])
        reply_markup = InlineKeyboardMarkup(diseases_keyboard)
        await query.edit_message_text(text=f"اختر مرض مرتبط ب{symptom}:", reply_markup=reply_markup)

    if selection == 'add_disease':
        await query.edit_message_text(text="أرسل اسم المرض الجديد:")
        context.user_data['adding_disease'] = True
        return

    if 'adding_disease' in context.user_data and context.user_data['adding_disease']:
        device = context.user_data['current_device']
        symptom = context.user_data['current_symptom']
        topics[device]['الأعراض'][symptom].append(selection)
        save_data(topics)
        await query.edit_message_text(text=f"تم إضافة المرض: {selection}. هل تريد إضافة المزيد؟ إذا نعم، أرسل 'نعم'. إذا لا، أرسل 'لا'.")
        context.user_data['adding_disease'] = False
        return

    elif selection.startswith('disease-'):
        disease = selection.split('disease-')[1]
        info_keyboard = [
            [InlineKeyboardButton("الأسباب", callback_data=f"reasons-{disease}")],
            [InlineKeyboardButton("الأعراض", callback_data=f"symptoms-{disease}")],
            [InlineKeyboardButton("التشخيص", callback_data=f"diagnosis-{disease}")],
            [InlineKeyboardButton("العلاج", callback_data=f"treatment-{disease}")],
            [InlineKeyboardButton("Extra", callback_data=f"extra-{disease}")]
        ]
        reply_markup = InlineKeyboardMarkup(info_keyboard)
        await query.edit_message_text(text=f"تم اختيار المرض: {disease}. اختر مزيدًا من المعلومات:", reply_markup=reply_markup)

    elif selection.startswith('reasons-'):
        disease = selection.split('reasons-')[1]
        await query.edit_message_text(text=f"الأسباب المرتبطة بمرض {disease}: [هنا نص توضيحي للأسباب]")

    elif selection.startswith('symptoms-'):
        disease = selection.split('symptoms-')[1]
        await query.edit_message_text(text=f"الأعراض المرتبطة بمرض {disease}: [هنا نص توضيحي للأعراض]")

    elif selection.startswith('diagnosis-'):
        disease = selection.split('diagnosis-')[1]
        await query.edit_message_text(text=f"التشخيص المرتبط بمرض {disease}: [هنا نص توضيحي للتشخيص]")

    elif selection.startswith('treatment-'):
        disease = selection.split('treatment-')[1]
        await query.edit_message_text(text=f"العلاج المرتبط بمرض {disease}: [هنا نص توضيحي للعلاج]")

    elif selection.startswith('extra-'):
        disease = selection.split('extra-')[1]
        await query.edit_message_text(text=f"معلومات إضافية عن مرض {disease}: [هنا نص إضافي]")

    elif selection == 'back':
        await start(update, context)

    else:
        await query.edit_message_text(text=f"لقد اخترت {selection}.")

# دالة معالجة الرسائل النصية
async def handle_message(update: Update, context: CallbackContext) -> None:
    if 'adding_device' في context.user_data and context.user_data['adding_device']:
        context.user_data['current_device'] = update.message.text
        topics[update.message.text] = {"الأعراض": {}}
        save_data(topics)
        await update.message.reply_text(f"تم إضافة الجهاز: {update.message.text}. الآن أرسل الأعراض لهذا الجهاز.")
        context.user_data['adding_device'] = False
        context.user_data['adding_symptoms'] = True
        return

    if 'adding_symptoms' في context.user_data and context.user_data['adding_symptoms']:
        device = context.user_data['current_device']
        context.user_data['current_symptom'] = update.message.text
        topics[device]['الأعراض'][update.message.text] = []
        save_data(topics)
        await update.message.reply_text(f"تم إضافة العرض: {update.message.text}. الآن أرسل الأمراض المرتبطة بهذا العرض.")
        context.user_data['adding_symptoms'] = False
        context.user_data['adding_diseases'] = True
        return

    if 'adding_diseases' في context.user_data and context.user_data['adding_diseases']:
        device = context.user_data['current_device']
        symptom = context.user_data['current_symptom']
        topics[device]['الأعراض'][symptom].append(update.message.text)
        save_data(topics)
        await update.message.reply_text(f"تم إضافة المرض: {update.message.text}. هل تريد إضافة المزيد؟ إذا نعم، أرسل 'نعم'. إذا لا، أرسل 'لا'.")
        context.user_data['adding_diseases'] = False
        return

    if update.message.text.lower() == 'نعم':
        await update.message.reply_text("أرسل العرض التالي.")
        context.user_data['adding_symptoms'] = True
    elif update.message.text.lower() == 'لا':
        await update.message.reply_text("شكراً لإضافة البيانات! يمكنك الآن استخدام البوت.")
    else:
        await update.message.reply_text("الرجاء استخدام الأزرار للتنقل.")

# دالة عرض جميع الأمراض
async def display_all_diseases(update: Update, context: CallbackContext) -> None:
    keyboard = []
    for device, data in topics.items():
        device_button = [InlineKeyboardButton(f"{device}", callback_data=f"device-{device}")]
        keyboard.append(device_button)
        for symptom, diseases in data["الأعراض"].items():
            for disease in diseases:
                keyboard.append([InlineKeyboardButton(f"{disease} ({device})", callback_data=f"disease-{disease}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('اختر مرض من القائمة:', reply_markup=reply_markup)

# دالة عرض الأمراض بناءً على الأعراض
async def display_diseases_by_symptoms(update: Update, context: CallbackContext) -> None:
    symptoms = update.message.text.split('/Sym ')[1].split(', ')
    matched_diseases = set(topics[next(iter(topics))]["الأعراض"][next(iter(topics[next(iter(topics))]["الأعراض"]))])  # initialize with any disease set

    for symptom in symptoms:
        for device, data in topics.items():
            for symp, diseases in data["الأعراض"].items():
                if symptom in symp:
                    matched_diseases = matched_diseases.intersection(set(diseases))

    if matched_diseases:
        keyboard = [[InlineKeyboardButton(disease, callback_data=f"disease-{disease}")] for disease in matched_diseases]
    else:
        keyboard = [[InlineKeyboardButton("لا يوجد أمراض مطابقة", callback_data="no_diseases")]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('الأمراض التي تتوافق مع الأعراض المقدمة:', reply_markup=reply_markup)

# ربط الأحداث بالدوال
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('Dis', display_all_diseases))
    application.add_handler(CommandHandler('Sym', display_diseases_by_symptoms))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # تشغيل البوت
    application.run_polling()

if __name__ == '__main__':
    main()
