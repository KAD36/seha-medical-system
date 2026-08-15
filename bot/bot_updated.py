#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seha Sick Leave Bot - Updated Version
بوت تيليجرام لتوليد تقارير الإجازة المرضية - النسخة المحدثة
يدعم الآن استقبال البيانات في رسالة واحدة منسقة
"""

import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config_updated import BOT_TOKEN, ADMIN_USER_ID, OUTPUT_DIR
from pdf_generator_updated import generate_sick_leave_pdf
from api_client import send_leave_data_to_api
from message_parser import MessageParser
from date_converter import DateConverter

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# حالات المحادثة
STATES = {
    'START': 0,
    'PATIENT_NAME_AR': 1,
    'PATIENT_NAME_EN': 2,
    'ID_NUMBER': 3,
    'NATIONALITY_AR': 4,
    'NATIONALITY_EN': 5,
    'EMPLOYER_AR': 6,
    'EMPLOYER_EN': 7,
    'DOCTOR_NAME_AR': 8,
    'DOCTOR_NAME_EN': 9,
    'POSITION_AR': 10,
    'POSITION_EN': 11,
    'ADMISSION_DATE_GREGORIAN': 12,
    'ADMISSION_DATE_HIJRI': 13,
    'DISCHARGE_DATE_GREGORIAN': 14,
    'DISCHARGE_DATE_HIJRI': 15,
    'ISSUE_DATE_GREGORIAN': 16,
    'HOSPITAL_NAME_AR': 17,
    'HOSPITAL_NAME_EN': 18,
    'TIME': 19,
    'LOGO_UPLOAD': 20,
    'CONFIRM_DATA': 21,
    'GENERATE_REPORT': 22
}

# تخزين بيانات المستخدمين
user_data = {}

# إنشاء كائنات المعالجة
message_parser = MessageParser()
date_converter = DateConverter()


async def ensure_authorized(update: Update) -> bool:
    """Allow only the Telegram account configured as ADMIN_USER_ID."""
    user = update.effective_user
    if user and ADMIN_USER_ID and str(user.id) == str(ADMIN_USER_ID):
        return True

    if update.effective_message:
        await update.effective_message.reply_text("⛔ هذا البوت مخصص للمستخدم المعتمد فقط.")
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /start"""
    if not await ensure_authorized(update):
        return

    user_id = update.effective_user.id
    
    # رسالة الترحيب المحدثة
    welcome_message = """👋 مرحبًا بك في بوت منصة صحة الرسمي - النسخة المحدثة

يقدم هذا البوت خدمة إصدار تقرير إجازة مرضية رسمي بصيغة PDF معتمد من وزارة الصحة السعودية.

🔒 الاستخدام مخصص فقط للمستخدمين المعتمدين من قبل منصة صحة.

⚙️ طرق الاستخدام:

🚀 الطريقة الجديدة (الموصى بها):
أرسل جميع البيانات في رسالة واحدة منسقة كالتالي:

👤 اسم المريض (عربي): عبدالله محمد علي
👤 اسم المريض (إنجليزي): Abdullah Mohammed Ali
🆔 رقم الهوية: 828287654
🌍 الجنسية (عربي): السعودية
🌍 الجنسية (إنجليزي): Saudi Arabia
🏢 جهة العمل (عربي): طالب جامعي
🏢 جهة العمل (إنجليزي): University Student
👨‍⚕️ اسم الطبيب (عربي): المقبني
👨‍⚕️ اسم الطبيب (إنجليزي): Almakbany
💼 المسمى الوظيفي (عربي): طبيب عام
💼 المسمى الوظيفي (إنجليزي): General
📅 تاريخ الدخول (ميلادي): 20-09-2025
📅 تاريخ الخروج (ميلادي): 21-09-2025
🏥 اسم المنشأة (عربي): مستشفى الملك فيصل التخصصي
🏥 اسم المنشأة (إنجليزي): King Faisal Specialist Hospital
⏰ الوقت: 10:20 AM

سيقوم البوت تلقائياً بـ:
✅ تحويل التواريخ من الميلادي إلى الهجري
✅ تعيين تاريخ إصدار التقرير = تاريخ الخروج
✅ توليد التقرير بصيغة PDF

📝 الطريقة التقليدية:
اضغط على زر "إنشاء تقرير جديد" للإدخال خطوة بخطوة."""
    
    # إنشاء لوحة المفاتيح
    keyboard = [[KeyboardButton("🆕 إنشاء تقرير جديد")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    
    # تهيئة بيانات المستخدم
    user_data[user_id] = {'state': STATES['START']}

async def handle_formatted_message(update: Update, context: ContextTypes.DEFAULT_TYPE, parsed_data: dict) -> None:
    """معالجة الرسالة المنسقة وتوليد التقرير"""
    user_id = update.effective_user.id
    
    try:
        # إرسال رسالة تأكيد
        await update.message.reply_text("🔄 جاري معالجة البيانات وتحويل التواريخ...")
        
        # معالجة التواريخ
        admission_date = parsed_data.get('admission_date_gregorian', '01-01-2025')
        discharge_date = parsed_data.get('discharge_date_gregorian', '01-01-2025')
        
        # تحويل التواريخ
        date_data = date_converter.process_dates(admission_date, discharge_date)
        
        # دمج البيانات
        final_data = {**parsed_data, **date_data}
        
        # إرسال رسالة تأكيد التحويل
        await update.message.reply_text(
            f"✅ تم تحويل التواريخ بنجاح:\n"
            f"📅 تاريخ الدخول: {admission_date} ← {date_data['admission_date_hijri']}\n"
            f"📅 تاريخ الخروج: {discharge_date} ← {date_data['discharge_date_hijri']}\n"
            f"📅 تاريخ إصدار التقرير: {date_data['issue_date_gregorian']}\n\n"
            f"🔄 جاري توليد التقرير..."
        )
        
        # توليد التقرير
        pdf_path = generate_sick_leave_pdf(final_data, str(user_id))
        
        if pdf_path and os.path.exists(pdf_path):
            # إرسال التقرير
            with open(pdf_path, 'rb') as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    filename=f"Sick_Leave_{final_data.get('id_number', 'Report')}.pdf",
                    caption="✅ تم إنشاء تقرير الإجازة المرضية بنجاح!"
                )
            
            # إرسال البيانات إلى API (إذا كان متاحاً)
            try:
                api_response = send_leave_data_to_api(final_data)
                if api_response.get('success'):
                    await update.message.reply_text("✅ تم حفظ البيانات في النظام بنجاح.")
                else:
                    await update.message.reply_text(
                        f"⚠️ تم إنشاء التقرير، لكن تعذر حفظه في الموقع: {api_response['message']}"
                    )
            except Exception as api_error:
                logger.warning(f"خطأ في إرسال البيانات إلى API: {api_error}")
            
            # رسالة النجاح النهائية مع زر الشعار
            success_message = """🎉 تم إنشاء التقرير بنجاح!

✅ تم تحويل التواريخ تلقائياً
✅ تم توليد التقرير بصيغة PDF
✅ جاهز للاستخدام الرسمي

هل تريد إضافة شعار المنشأة للتقرير؟"""
            
            keyboard = [
                [KeyboardButton("📤 إرسال شعار المنشأة")],
                [KeyboardButton("🆕 إنشاء تقرير جديد")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            
            await update.message.reply_text(success_message, reply_markup=reply_markup)
            
            # حفظ البيانات للاستخدام مع الشعار
            user_data[user_id] = {
                'state': STATES['LOGO_UPLOAD'], 
                'data': final_data,
                'last_pdf_path': pdf_path
            }
            
        else:
            await update.message.reply_text("❌ حدث خطأ في توليد التقرير. يرجى المحاولة مرة أخرى.")
            
    except Exception as e:
        logger.error(f"خطأ في معالجة الرسالة المنسقة: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ في معالجة البيانات. يرجى التحقق من تنسيق الرسالة والمحاولة مرة أخرى.\n\n"
            "تأكد من أن الرسالة تحتوي على الحقول المطلوبة بالتنسيق الصحيح."
        )

async def handle_new_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج زر إنشاء تقرير جديد"""
    user_id = update.effective_user.id
    
    if update.message.text == "🆕 إنشاء تقرير جديد":
        # تهيئة بيانات المستخدم
        user_data[user_id] = {'state': STATES['PATIENT_NAME_AR'], 'data': {}}
        
        message = "📌 يرجى إدخال البيانات بشكل صحيح.\n\n✍️ يرجى إدخال اسم المريض باللغة العربية بشكل صحيح"
        
        # إنشاء لوحة المفاتيح للخطوة التالية
        keyboard = [[KeyboardButton("الخطوة التالية")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(message, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الرسائل النصية - محدث لدعم الرسائل المنسقة"""
    if not await ensure_authorized(update):
        return

    user_id = update.effective_user.id
    message_text = update.message.text
    
    # فحص ما إذا كانت الرسالة منسقة
    if message_parser.is_formatted_message(message_text):
        # معالجة الرسالة المنسقة
        parsed_data = message_parser.parse_message(message_text)
        validated_data = message_parser.validate_data(parsed_data)
        await handle_formatted_message(update, context, validated_data)
        return
    
    # فحص زر إرسال الشعار
    if message_text == "📤 إرسال شعار المنشأة":
        await update.message.reply_text(
            "🖼️ يرجى إرسال شعار المنشأة كصورة (JPG, PNG, أو أي صيغة صورة)\n\n"
            "سيتم إنشاء تقرير جديد مع الشعار المخصص."
        )
        return
    
    # إذا لم تكن الرسالة منسقة، استخدم الطريقة التقليدية
    if user_id not in user_data:
        await start(update, context)
        return
    
    current_state = user_data[user_id]['state']
    
    # معالجة الحالات المختلفة (الطريقة التقليدية)
    if current_state == STATES['START']:
        if message_text == "🆕 إنشاء تقرير جديد":
            await handle_new_report(update, context)
    
    elif current_state == STATES['PATIENT_NAME_AR']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['patient_name_ar'] = message_text
        await ask_patient_name_en(update, context)
    
    elif current_state == STATES['PATIENT_NAME_EN']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['patient_name_en'] = message_text
        await ask_id_number(update, context)
    
    elif current_state == STATES['ID_NUMBER']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['id_number'] = message_text
        await ask_nationality_ar(update, context)
    
    elif current_state == STATES['NATIONALITY_AR']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['nationality_ar'] = message_text
        await ask_nationality_en(update, context)
    
    elif current_state == STATES['NATIONALITY_EN']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['nationality_en'] = message_text
        await ask_employer_ar(update, context)
    
    elif current_state == STATES['EMPLOYER_AR']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['employer_ar'] = message_text
        await ask_employer_en(update, context)
    
    elif current_state == STATES['EMPLOYER_EN']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['employer_en'] = message_text
        await ask_doctor_name_ar(update, context)
    
    elif current_state == STATES['DOCTOR_NAME_AR']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['doctor_name_ar'] = message_text
        await ask_doctor_name_en(update, context)
    
    elif current_state == STATES['DOCTOR_NAME_EN']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['doctor_name_en'] = message_text
        await ask_position_ar(update, context)
    
    elif current_state == STATES['POSITION_AR']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['position_ar'] = message_text
        await ask_position_en(update, context)
    
    elif current_state == STATES['POSITION_EN']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['position_en'] = message_text
        await ask_admission_date_gregorian(update, context)
    
    elif current_state == STATES['ADMISSION_DATE_GREGORIAN']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['admission_date_gregorian'] = message_text
        await ask_admission_date_hijri(update, context)
    
    elif current_state == STATES['ADMISSION_DATE_HIJRI']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['admission_date_hijri'] = message_text
        await ask_discharge_date_gregorian(update, context)
    
    elif current_state == STATES['DISCHARGE_DATE_GREGORIAN']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['discharge_date_gregorian'] = message_text
        await ask_discharge_date_hijri(update, context)
    
    elif current_state == STATES['DISCHARGE_DATE_HIJRI']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['discharge_date_hijri'] = message_text
        await ask_issue_date_gregorian(update, context)
    
    elif current_state == STATES['ISSUE_DATE_GREGORIAN']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['issue_date_gregorian'] = message_text
        await ask_hospital_name_ar(update, context)
    
    elif current_state == STATES['HOSPITAL_NAME_AR']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['hospital_name_ar'] = message_text
        await ask_hospital_name_en(update, context)
    
    elif current_state == STATES['HOSPITAL_NAME_EN']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['hospital_name_en'] = message_text
        await ask_time(update, context)
    
    elif current_state == STATES['TIME']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['time'] = message_text
        await ask_logo_upload(update, context)
    
    elif current_state == STATES['LOGO_UPLOAD']:
        if message_text == "✅ تأكد من البيانات":
            await confirm_data(update, context)
    
    elif current_state == STATES['CONFIRM_DATA']:
        if message_text == "📄 حفظ وإرسال التقرير بصيغة PDF":
            await generate_pdf_report(update, context)
        elif message_text == "🖼️ حفظ وإرسال التقرير بصيغة PNG":
            await generate_png_report(update, context)

# دوال طلب البيانات (الطريقة التقليدية) - نفس الدوال الأصلية
async def ask_patient_name_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['PATIENT_NAME_EN']
    
    message = "✍️ يرجى إدخال اسم المريض باللغة الإنجليزية"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_id_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['ID_NUMBER']
    
    message = "✍️ يرجى إدخال رقم الهوية"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_nationality_ar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['NATIONALITY_AR']
    
    message = "✍️ يرجى إدخال الجنسية باللغة العربية"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_nationality_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['NATIONALITY_EN']
    
    message = "✍️ يرجى إدخال الجنسية باللغة الإنجليزية"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_employer_ar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['EMPLOYER_AR']
    
    message = "✍️ يرجى إدخال جهة العمل باللغة العربية"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_employer_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['EMPLOYER_EN']
    
    message = "✍️ يرجى إدخال جهة العمل باللغة الإنجليزية"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_doctor_name_ar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['DOCTOR_NAME_AR']
    
    message = "✍️ يرجى إدخال اسم الطبيب المعالج باللغة العربية"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_doctor_name_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['DOCTOR_NAME_EN']
    
    message = "✍️ يرجى إدخال اسم الطبيب المعالج باللغة الإنجليزية"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_position_ar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['POSITION_AR']
    
    message = "✍️ يرجى إدخال المسمى الوظيفي باللغة العربية"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_position_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['POSITION_EN']
    
    message = "✍️ يرجى إدخال المسمى الوظيفي باللغة الإنجليزية"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_admission_date_gregorian(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['ADMISSION_DATE_GREGORIAN']
    
    message = "📅 يرجى إدخال تاريخ الدخول (ميلادي)"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_admission_date_hijri(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['ADMISSION_DATE_HIJRI']
    
    message = "📅 يرجى إدخال تاريخ الدخول (هجري)"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_discharge_date_gregorian(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['DISCHARGE_DATE_GREGORIAN']
    
    message = "📅 يرجى إدخال تاريخ الخروج (ميلادي)"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_discharge_date_hijri(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['DISCHARGE_DATE_HIJRI']
    
    message = "📅 يرجى إدخال تاريخ الخروج (هجري)"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_issue_date_gregorian(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['ISSUE_DATE_GREGORIAN']
    
    message = "📅 يرجى إدخال تاريخ إصدار التقرير (ميلادي)"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_hospital_name_ar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['HOSPITAL_NAME_AR']
    
    message = "🏥 يرجى إدخال اسم المستشفى/المجمع/المستوصف بالعربية"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_hospital_name_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['HOSPITAL_NAME_EN']
    
    message = "🏥 يرجى إدخال اسم المستشفى/المجمع/المستوصف بالإنجليزية"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['TIME']
    
    message = "⏰ يرجى إدخال الوقت (مثال: 10:30 AM)"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_logo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['LOGO_UPLOAD']
    
    message = """🖼️ يمكنك الآن رفع شعار المنشأة (اختياري)

إذا كنت تريد إضافة شعار خاص بالمنشأة، قم برفع الصورة الآن.
وإلا اضغط على "تأكد من البيانات" للمتابعة."""
    
    keyboard = [[KeyboardButton("✅ تأكد من البيانات")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def confirm_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تأكيد البيانات"""
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['CONFIRM_DATA']
    
    data = user_data[user_id]['data']
    
    # عرض البيانات للمراجعة
    review_text = f"""📋 مراجعة البيانات:

👤 اسم المريض: {data.get('patient_name_ar', '')} / {data.get('patient_name_en', '')}
🆔 رقم الهوية: {data.get('id_number', '')}
🌍 الجنسية: {data.get('nationality_ar', '')} / {data.get('nationality_en', '')}
🏢 جهة العمل: {data.get('employer_ar', '')} / {data.get('employer_en', '')}
👨‍⚕️ اسم الطبيب: {data.get('doctor_name_ar', '')} / {data.get('doctor_name_en', '')}
💼 المسمى الوظيفي: {data.get('position_ar', '')} / {data.get('position_en', '')}
📅 تاريخ الدخول: {data.get('admission_date_gregorian', '')} / {data.get('admission_date_hijri', '')}
📅 تاريخ الخروج: {data.get('discharge_date_gregorian', '')} / {data.get('discharge_date_hijri', '')}
📅 تاريخ إصدار التقرير: {data.get('issue_date_gregorian', '')}
🏥 اسم المنشأة: {data.get('hospital_name_ar', '')} / {data.get('hospital_name_en', '')}
⏰ الوقت: {data.get('time', '')}

يرجى اختيار صيغة التقرير:"""
    
    keyboard = [
        [KeyboardButton("📄 حفظ وإرسال التقرير بصيغة PDF")],
        [KeyboardButton("🖼️ حفظ وإرسال التقرير بصيغة PNG")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(review_text, reply_markup=reply_markup)

async def generate_pdf_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """توليد تقرير PDF"""
    user_id = update.effective_user.id
    
    try:
        await update.message.reply_text("🔄 جاري إنشاء التقرير...")
        
        data = user_data[user_id]['data']
        
        # توليد التقرير
        pdf_path = generate_sick_leave_pdf(data, str(user_id))
        
        if pdf_path and os.path.exists(pdf_path):
            # إرسال التقرير
            with open(pdf_path, 'rb') as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    filename=f"Sick_Leave_{data.get('id_number', 'Report')}.pdf",
                    caption="✅ تم إنشاء تقرير الإجازة المرضية بنجاح!"
                )
            
            # إرسال البيانات إلى API
            try:
                api_response = send_leave_data_to_api(data)
                if api_response.get('success'):
                    await update.message.reply_text("✅ تم حفظ البيانات في النظام بنجاح.")
                else:
                    await update.message.reply_text(
                        f"⚠️ تم إنشاء التقرير، لكن تعذر حفظه في الموقع: {api_response['message']}"
                    )
            except Exception as api_error:
                logger.warning(f"خطأ في إرسال البيانات إلى API: {api_error}")
            
        else:
            await update.message.reply_text("❌ حدث خطأ في توليد التقرير. يرجى المحاولة مرة أخرى.")
        
        # إعادة تعيين الحالة
        user_data[user_id] = {'state': STATES['START']}
        keyboard = [[KeyboardButton("🆕 إنشاء تقرير جديد")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("يمكنك إنشاء تقرير جديد:", reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"خطأ في توليد PDF: {e}")
        await update.message.reply_text("❌ حدث خطأ في توليد التقرير. يرجى المحاولة مرة أخرى.")

async def generate_png_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """توليد تقرير PNG"""
    await update.message.reply_text("🚧 ميزة PNG قيد التطوير...")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الصور المرسلة"""
    if not await ensure_authorized(update):
        return

    user_id = update.effective_user.id
    
    if user_id in user_data and user_data[user_id]['state'] == STATES['LOGO_UPLOAD']:
        try:
            await update.message.reply_text("🔄 جاري حفظ الشعار وإنشاء التقرير الجديد...")
            
            # حفظ الصورة
            photo = update.message.photo[-1]  # أخذ أعلى جودة
            file = await context.bot.get_file(photo.file_id)
            
            # إنشاء مجلد للشعارات
            logos_dir = f"{OUTPUT_DIR}/logos"
            os.makedirs(logos_dir, exist_ok=True)
            
            # حفظ الصورة
            logo_path = f"{logos_dir}/logo_{user_id}.jpg"
            await file.download_to_drive(logo_path)
            
            # إضافة الشعار إلى البيانات
            data = user_data[user_id]['data']
            data['custom_logo'] = logo_path
            
            # إنشاء تقرير جديد مع الشعار
            pdf_path = generate_sick_leave_pdf(data, str(user_id))
            
            if pdf_path and os.path.exists(pdf_path):
                # إرسال التقرير الجديد
                with open(pdf_path, 'rb') as pdf_file:
                    await update.message.reply_document(
                        document=pdf_file,
                        filename=f"Sick_Leave_With_Logo_{data.get('id_number', 'Report')}.pdf",
                        caption="✅ تم إنشاء التقرير مع الشعار المخصص بنجاح!"
                    )
                
                # رسالة النجاح
                keyboard = [[KeyboardButton("🆕 إنشاء تقرير جديد")]]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
                await update.message.reply_text(
                    "🎉 تم إنشاء التقرير مع الشعار المخصص بنجاح!\n\n"
                    "يمكنك إنشاء تقرير جديد:",
                    reply_markup=reply_markup
                )
                
                # إعادة تعيين الحالة
                user_data[user_id] = {'state': STATES['START']}
                
            else:
                await update.message.reply_text("❌ حدث خطأ في إنشاء التقرير مع الشعار. يرجى المحاولة مرة أخرى.")
                
        except Exception as e:
            logger.error(f"خطأ في معالجة الشعار: {e}")
            await update.message.reply_text("❌ حدث خطأ في معالجة الشعار. يرجى المحاولة مرة أخرى.")
    else:
        await update.message.reply_text("🖼️ يرجى أولاً إرسال البيانات المنسقة أو استخدام الطريقة التقليدية لإنشاء التقرير.")

def build_application(*, polling: bool = True) -> Application:
    """Build the bot application for polling or for the combined webhook server."""
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is required. Set it as an environment variable.")
    if not ADMIN_USER_ID:
        raise RuntimeError("ADMIN_USER_ID is required. Set it as an environment variable.")

    builder = Application.builder().token(BOT_TOKEN)
    if not polling:
        builder = builder.updater(None)
    application = builder.build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    
    # إضافة معالجات الرسائل
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    return application


def main() -> None:
    """الدالة الرئيسية لتشغيل البوت باستخدام polling."""
    application = build_application(polling=True)
    
    # تشغيل البوت
    print("🤖 بدء تشغيل بوت صحة للإجازات المرضية - النسخة المحدثة...")
    print("✅ يدعم الآن استقبال البيانات في رسالة واحدة منسقة")
    print("✅ تحويل تلقائي للتواريخ من الميلادي إلى الهجري")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
