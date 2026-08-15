#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seha Sick Leave Bot
بوت تيليجرام لتوليد تقارير الإجازة المرضية
"""

import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, ADMIN_USER_ID, OUTPUT_DIR
from pdf_generator_v4 import generate_sick_leave_pdf
from api_client import send_leave_data_to_api

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /start"""
    user_id = update.effective_user.id
    
    # رسالة الترحيب
    welcome_message = """👋 مرحبًا بك في بوت منصة صحة الرسمي

يقدم هذا البوت خدمة إصدار تقرير إجازة مرضية رسمي بصيغة PDF معتمد من وزارة الصحة السعودية.

🔒 الاستخدام مخصص فقط للمستخدمين المعتمدين من قبل منصة صحة، مثل:
- موظفي الموارد البشرية
- مسؤولي شؤون الموظفين
- مديري المدارس
- منسقي الإجازات
- الجهات الحكومية والعسكرية
- مسؤولي الجامعات والكليات

⚙️ طريقة الاستخدام:
1. اضغط على زر 🆕 "إنشاء تقرير جديد"
2. أدخل بيانات المريض بالترتيب
3. اختر صيغة التقرير:
   - 📄 PDF

لبدء إنشاء تقرير، اضغط الزر أدناه:"""
    
    # إنشاء لوحة المفاتيح
    keyboard = [[KeyboardButton("🆕 إنشاء تقرير جديد")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    
    # تهيئة بيانات المستخدم
    user_data[user_id] = {'state': STATES['START']}

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
    """معالج الرسائل النصية"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    if user_id not in user_data:
        await start(update, context)
        return
    
    current_state = user_data[user_id]['state']
    
    # معالجة الحالات المختلفة
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

# دوال طلب البيانات
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
    
    message = "⏰ يرجى إدخال الوقت (مثل: 11:30 AM)"
    keyboard = [[KeyboardButton("الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_logo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['LOGO_UPLOAD']
    
    message = "📎 يرجى إرسال شعار المنشأة كصورة في اي صيغة"
    keyboard = [[KeyboardButton("✅ تأكد من البيانات")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def confirm_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['CONFIRM_DATA']
    
    data = user_data[user_id]['data']
    
    summary = f"""📝 ملخص البيانات المدخلة:

👤 اسم المريض (عربي): {data.get('patient_name_ar', 'غير محدد')}
👤 اسم المريض (إنجليزي): {data.get('patient_name_en', 'غير محدد')}
🆔 رقم الهوية: {data.get('id_number', 'غير محدد')}
🌍 الجنسية (عربي): {data.get('nationality_ar', 'غير محدد')}
🌍 الجنسية (إنجليزي): {data.get('nationality_en', 'غير محدد')}
🏢 جهة العمل (عربي): {data.get('employer_ar', 'غير محدد')}
🏢 جهة العمل (إنجليزي): {data.get('employer_en', 'غير محدد')}
👨‍⚕️ اسم الطبيب (عربي): {data.get('doctor_name_ar', 'غير محدد')}
👨‍⚕️ اسم الطبيب (إنجليزي): {data.get('doctor_name_en', 'غير محدد')}
💼 المسمى الوظيفي (عربي): {data.get('position_ar', 'غير محدد')}
💼 المسمى الوظيفي (إنجليزي): {data.get('position_en', 'غير محدد')}
📅 تاريخ الدخول (ميلادي): {data.get('admission_date_gregorian', 'غير محدد')}
📅 تاريخ الدخول (هجري): {data.get('admission_date_hijri', 'غير محدد')}
📅 تاريخ الخروج (ميلادي): {data.get('discharge_date_gregorian', 'غير محدد')}
📅 تاريخ الخروج (هجري): {data.get('discharge_date_hijri', 'غير محدد')}
📅 تاريخ إصدار التقرير: {data.get('issue_date_gregorian', 'غير محدد')}
🏥 اسم المنشأة (عربي): {data.get('hospital_name_ar', 'غير محدد')}
🏥 اسم المنشأة (إنجليزي): {data.get('hospital_name_en', 'غير محدد')}
⏰ الوقت: {data.get('time', 'غير محدد')}"""
    
    keyboard = [
        [KeyboardButton("📄 حفظ وإرسال التقرير بصيغة PDF")],
        [KeyboardButton("🖼️ حفظ وإرسال التقرير بصيغة PNG")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(summary, reply_markup=reply_markup)

async def generate_pdf_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """توليد تقرير PDF وإرسال البيانات إلى الموقع"""
    user_id = update.effective_user.id
    
    try:
        # إنشاء مجلد الإخراج إذا لم يكن موجوداً
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # توليد ملف PDF
        data = user_data[user_id]['data']
        pdf_path = generate_sick_leave_pdf(data, user_id)
        
        # إرسال الملف
        with open(pdf_path, 'rb') as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename=os.path.basename(pdf_path),
                caption="✅ تم إنشاء تقرير الإجازة المرضية بنجاح!"
            )
        
        # إرسال البيانات إلى الموقع
        await update.message.reply_text("🔄 جاري حفظ البيانات في النظام...")
        
        api_result = send_leave_data_to_api(data)
        
        if api_result['success']:
            success_message = f"""✅ تم حفظ بيانات الإجازة في النظام بنجاح!

🆔 رمز الإجازة: {api_result['leave_id']}

يمكنك الآن الاستعلام عن الإجازة من الموقع باستخدام:
• رقم الهوية: {data.get('id_number', '')}
• رمز الإجازة: {api_result['leave_id']}"""
            
            await update.message.reply_text(success_message)
        else:
            error_message = f"""⚠️ تم إنشاء التقرير بنجاح ولكن حدث خطأ في حفظ البيانات:

❌ {api_result['message']}

🆔 رمز الإجازة: {api_result['leave_id']}

يرجى التواصل مع المسؤول لحفظ البيانات يدوياً."""
            
            await update.message.reply_text(error_message)
        
        # إعادة تعيين حالة المستخدم
        user_data[user_id] = {'state': STATES['START']}
        
        # عرض زر إنشاء تقرير جديد
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
    user_id = update.effective_user.id
    
    if user_id in user_data and user_data[user_id]['state'] == STATES['LOGO_UPLOAD']:
        # حفظ الصورة
        photo = update.message.photo[-1]  # أخذ أعلى جودة
        file = await context.bot.get_file(photo.file_id)
        
        # إنشاء مجلد للشعارات
        logos_dir = f"{OUTPUT_DIR}/logos"
        os.makedirs(logos_dir, exist_ok=True)
        
        # حفظ الصورة
        logo_path = f"{logos_dir}/logo_{user_id}.jpg"
        await file.download_to_drive(logo_path)
        
        # حفظ مسار الصورة في بيانات المستخدم
        user_data[user_id]['data']['custom_logo'] = logo_path
        
        await update.message.reply_text("✅ تم حفظ الشعار بنجاح!")

def main() -> None:
    """الدالة الرئيسية لتشغيل البوت"""
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    
    # إضافة معالجات الرسائل
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # تشغيل البوت
    print("🤖 بدء تشغيل بوت صحة للإجازات المرضية...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
