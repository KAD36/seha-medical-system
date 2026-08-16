#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seha Sick Leave Bot - Updated Version
بوت تيليجرام لتوليد تقارير الإجازة المرضية - النسخة المحدثة
يدعم الآن استقبال البيانات في رسالة واحدة منسقة
"""

import asyncio
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from config_updated import BOT_TOKEN, ADMIN_USER_ID, OUTPUT_DIR
from pdf_generator_updated import generate_sick_leave_pdf
from api_client import send_leave_data_to_api
from message_parser import MessageParser
from date_converter import DateConverter
from catalog import (
    CUSTOM_ENTRY,
    DEFAULT_NATIONALITY_BUTTON,
    DOCTORS,
    FACILITIES,
    OTHER_NATIONALITY_BUTTON,
    POSITIONS,
    automatic_english,
    doctor_labels_for_facility,
    facility_logo_path,
    nationality_pair,
)
from identifiers import normalize_digits, normalize_identity
from subscriptions import SubscriptionStore

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
subscription_store = SubscriptionStore()
EDIT_DATES_BUTTON = "✏️ تعديل التواريخ"
CATALOG_PAGE_SIZE = 7
SUBSCRIPTION_CONTACT_URL = "https://t.me/Yousef_sbri"


def normalize_gregorian_date(value: str):
    """Return DD-MM-YYYY for a valid date, otherwise None."""
    parsed = date_converter.parse_gregorian_date(value)
    if not parsed:
        return None
    day, month, year = parsed
    return f"{day:02d}-{month:02d}-{year}"


def _catalog_markup(items, prefix: str, page: int) -> InlineKeyboardMarkup:
    page_count = max(1, (len(items) + CATALOG_PAGE_SIZE - 1) // CATALOG_PAGE_SIZE)
    page = max(0, min(page, page_count - 1))
    start = page * CATALOG_PAGE_SIZE
    rows = [
        [InlineKeyboardButton(label, callback_data=f"{prefix}_select:{index}")]
        for index, label in enumerate(items[start:start + CATALOG_PAGE_SIZE], start=start)
    ]
    if items:
        navigation = []
        if page > 0:
            navigation.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"{prefix}_page:{page - 1}"))
        navigation.append(InlineKeyboardButton(f"{page + 1}/{page_count}", callback_data="catalog_noop"))
        if page + 1 < page_count:
            navigation.append(InlineKeyboardButton("التالي ➡️", callback_data=f"{prefix}_page:{page + 1}"))
        rows.append(navigation)
    rows.append([InlineKeyboardButton(CUSTOM_ENTRY, callback_data=f"{prefix}_custom")])
    return InlineKeyboardMarkup(rows)


def _set_default_dates(data: dict) -> None:
    today = date_converter.get_current_gregorian_date()
    data.update(date_converter.process_dates(today, today))


def _set_automatic_report_fields(data: dict) -> None:
    _set_default_dates(data)
    data['time'] = datetime.now(ZoneInfo("Asia/Riyadh")).strftime("%I:%M %p").lstrip("0")


async def _show_automatic_dates(message, data: dict) -> None:
    await message.reply_text(
        "📅 تم ضبط التواريخ تلقائيًا ويمكن تعديلها من شاشة المراجعة:\n"
        f"الدخول: {data['admission_date_gregorian']} م / {data['admission_date_hijri']} هـ\n"
        f"الخروج: {data['discharge_date_gregorian']} م / {data['discharge_date_hijri']} هـ"
    )


def _is_admin(user_id) -> bool:
    return bool(ADMIN_USER_ID and str(user_id) == str(ADMIN_USER_ID))


async def _require_private_chat(update: Update) -> bool:
    chat = getattr(update, "effective_chat", None)
    if chat and chat.type != "private":
        await update.effective_message.reply_text(
            "🔒 حفاظًا على خصوصية البيانات، استخدم البوت في المحادثة الخاصة فقط."
        )
        return False
    return True


def _format_expiry(value: datetime) -> str:
    return value.astimezone(ZoneInfo("Asia/Riyadh")).strftime("%d-%m-%Y %I:%M %p")


async def _send_subscription_prompt(update: Update) -> None:
    user = update.effective_user
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("💬 التواصل مع يوسف للاشتراك", url=SUBSCRIPTION_CONTACT_URL)]]
    )
    await update.effective_message.reply_text(
        "👋 أهلًا بك في بوت تقارير الإجازات المرضية\n\n"
        "استخدام البوت متاح باشتراك شهري فعّال. للتفعيل تواصل مع @Yousef_sbri "
        "وأرسل له معرّف حسابك الظاهر أدناه:\n\n"
        f"🆔 معرّفك: `{user.id}`\n\n"
        "بعد تأكيد الاشتراك اضغط /start مرة أخرى.",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def ensure_authorized(update: Update) -> bool:
    """Allow the owner or a user with an active monthly subscription."""
    user = update.effective_user
    if not user:
        return False
    if not await _require_private_chat(update):
        return False
    if _is_admin(user.id):
        return True
    try:
        if await asyncio.to_thread(subscription_store.is_active, user.id):
            return True
    except Exception:
        logger.exception("Subscription lookup failed")
        await update.effective_message.reply_text(
            "⚠️ تعذر التحقق من الاشتراك مؤقتًا. حاول مرة أخرى بعد قليل."
        )
        return False
    if update.callback_query:
        await update.callback_query.answer("الاشتراك غير فعّال", show_alert=True)
    await _send_subscription_prompt(update)
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /start"""
    user = update.effective_user
    if not user:
        return
    if not await _require_private_chat(update):
        return
    try:
        await asyncio.to_thread(
            subscription_store.remember_user,
            user.id,
            user.username,
            user.first_name,
        )
    except Exception:
        logger.exception("Unable to remember Telegram user")
    if not _is_admin(user.id):
        try:
            active = await asyncio.to_thread(subscription_store.is_active, user.id)
        except Exception:
            logger.exception("Subscription lookup failed on /start")
            await update.effective_message.reply_text(
                "⚠️ تعذر التحقق من الاشتراك مؤقتًا. حاول مرة أخرى بعد قليل."
            )
            return
        if not active:
            await _send_subscription_prompt(update)
            return

    if not await ensure_authorized(update):
        return

    user_id = update.effective_user.id
    
    welcome_message = """👋 مرحبًا بك في بوت تقارير الإجازات المرضية

اضغط «إنشاء تقرير جديد»، ثم اتبع الخطوات المختصرة.

✅ الأطباء والمنشآت عبر أزرار سهلة
✅ الاسم الإنجليزي والتخصص والشعار تلقائيًا
✅ التاريخ الميلادي والهجري والوقت تلقائيًا
✅ يمكنك تعديل التواريخ قبل الحفظ
✅ لا يُرسل التقرير إلا بعد التحقق من ظهوره في الاستعلام

لمعرفة حالة الاشتراك: /mystatus"""
    if _is_admin(user_id):
        welcome_message += "\nإدارة الاشتراكات: /subscriptions"
    
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
        final_data['id_number'] = normalize_identity(final_data.get('id_number'))
        nationality = nationality_pair(final_data.get('nationality_ar', ''))
        if nationality:
            final_data['nationality_ar'], final_data['nationality_en'] = nationality
        for _, doctor in DOCTORS.items():
            if final_data.get('doctor_name_ar', '').strip() == doctor[0]:
                final_data.update({
                    'doctor_name_en': doctor[1],
                    'position_ar': doctor[2],
                    'position_en': doctor[3],
                })
                break
        facility = FACILITIES.get(final_data.get('hospital_name_ar', '').strip())
        if facility:
            final_data['hospital_name_en'] = facility[0]
            final_data['custom_logo'] = facility_logo_path(final_data['hospital_name_ar'])

        # Save first so every PDF delivered by the bot is already searchable
        # on the public website.
        api_response = await asyncio.to_thread(send_leave_data_to_api, final_data)
        if not api_response.get('success'):
            await update.message.reply_text(
                f"❌ لم يتم إنشاء التقرير لأن حفظه في الموقع تعذر: {api_response['message']}"
            )
            return
        final_data['service_code'] = api_response['leave_id']
        final_data['id_number'] = api_response['identity_number']
        
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
            
            await update.message.reply_text(
                "✅ تم حفظ التقرير والتحقق من ظهوره في الاستعلام.\n"
                f"رمز الخدمة: {final_data['service_code']}\n"
                f"رقم الهوية: {final_data['id_number']}"
            )
            
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
            user_data[user_id]['data']['id_number'] = normalize_identity(message_text)
        await ask_nationality_ar(update, context)
    
    elif current_state == STATES['NATIONALITY_AR']:
        session = user_data[user_id]
        if message_text == OTHER_NATIONALITY_BUTTON:
            session['custom_nationality_entry'] = True
            await update.message.reply_text(
                "✍️ اكتب الجنسية بالعربية، مثال: مصري أو يمني أو باكستاني:",
                reply_markup=ReplyKeyboardRemove(),
            )
            return
        requested = "سعودي" if message_text in {DEFAULT_NATIONALITY_BUTTON, "الخطوة التالية"} else message_text
        nationality = nationality_pair(requested)
        if nationality:
            session['data']['nationality_ar'], session['data']['nationality_en'] = nationality
            session.pop('custom_nationality_entry', None)
            await update.message.reply_text(
                f"✅ الجنسية: {nationality[0]} / {nationality[1]}",
                reply_markup=ReplyKeyboardRemove(),
            )
            await ask_employer_ar(update, context)
        else:
            session['data']['nationality_ar'] = message_text
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
        await ask_hospital_name_ar(update, context)
    
    elif current_state == STATES['DOCTOR_NAME_AR']:
        session = user_data[user_id]
        if message_text == CUSTOM_ENTRY and not session.get('custom_doctor_entry'):
            session['custom_doctor_entry'] = True
            await update.message.reply_text(
                "✍️ اكتب اسم الطبيب بالعربية:",
                reply_markup=ReplyKeyboardRemove(),
            )
            return
        doctor = DOCTORS.get(message_text)
        if doctor:
            session['data'].update({
                'doctor_name_ar': doctor[0],
                'doctor_name_en': doctor[1],
                'position_ar': doctor[2],
                'position_en': doctor[3],
            })
        elif message_text != "الخطوة التالية":
            session['data']['doctor_name_ar'] = message_text
            session['data']['doctor_name_en'] = automatic_english(message_text, doctor=True)
        session.pop('custom_doctor_entry', None)
        if doctor:
            _set_automatic_report_fields(session['data'])
            await _show_automatic_dates(update.effective_message, session['data'])
            await confirm_data(update, context)
        else:
            await ask_position_ar(update, context)
    
    elif current_state == STATES['DOCTOR_NAME_EN']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['doctor_name_en'] = message_text
        await ask_position_ar(update, context)
    
    elif current_state == STATES['POSITION_AR']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['position_ar'] = message_text
            user_data[user_id]['data']['position_en'] = (
                POSITIONS.get(message_text) or automatic_english(message_text)
            )
        _set_automatic_report_fields(user_data[user_id]['data'])
        await _show_automatic_dates(update.effective_message, user_data[user_id]['data'])
        await confirm_data(update, context)
    
    elif current_state == STATES['POSITION_EN']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['position_en'] = message_text
        # Use today's Riyadh date automatically. It remains editable from the
        # review screen before generating the report.
        _set_automatic_report_fields(user_data[user_id]['data'])
        await _show_automatic_dates(update.effective_message, user_data[user_id]['data'])
        await confirm_data(update, context)
    
    elif current_state == STATES['ADMISSION_DATE_GREGORIAN']:
        normalized = normalize_gregorian_date(message_text)
        if not normalized:
            await update.message.reply_text("❌ التاريخ غير صحيح. اكتبه بصيغة يوم-شهر-سنة، مثال: 16-08-2026")
            await ask_admission_date_gregorian(update, context)
            return
        user_data[user_id]['data']['admission_date_gregorian'] = normalized
        await ask_discharge_date_gregorian(update, context)
    
    elif current_state == STATES['ADMISSION_DATE_HIJRI']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['admission_date_hijri'] = message_text
        await ask_discharge_date_gregorian(update, context)
    
    elif current_state == STATES['DISCHARGE_DATE_GREGORIAN']:
        normalized = normalize_gregorian_date(message_text)
        if not normalized:
            await update.message.reply_text("❌ التاريخ غير صحيح. اكتبه بصيغة يوم-شهر-سنة، مثال: 16-08-2026")
            await ask_discharge_date_gregorian(update, context)
            return
        data = user_data[user_id]['data']
        data.update(date_converter.process_dates(data['admission_date_gregorian'], normalized))
        await ask_issue_date_gregorian(update, context)
    
    elif current_state == STATES['DISCHARGE_DATE_HIJRI']:
        if message_text != "الخطوة التالية":
            user_data[user_id]['data']['discharge_date_hijri'] = message_text
        await ask_issue_date_gregorian(update, context)
    
    elif current_state == STATES['ISSUE_DATE_GREGORIAN']:
        normalized = normalize_gregorian_date(message_text)
        if not normalized:
            await update.message.reply_text("❌ التاريخ غير صحيح. اكتبه بصيغة يوم-شهر-سنة، مثال: 16-08-2026")
            await ask_issue_date_gregorian(update, context)
            return
        user_data[user_id]['data']['issue_date_gregorian'] = normalized
        user_data[user_id].pop('editing_dates', None)
        await confirm_data(update, context)
    
    elif current_state == STATES['HOSPITAL_NAME_AR']:
        session = user_data[user_id]
        if message_text == CUSTOM_ENTRY and not session.get('custom_facility_entry'):
            session['custom_facility_entry'] = True
            await update.message.reply_text(
                "✍️ اكتب اسم المستشفى أو المنشأة بالعربية:",
                reply_markup=ReplyKeyboardRemove(),
            )
            return
        facility = FACILITIES.get(message_text)
        if facility:
            session['data']['hospital_name_ar'] = message_text
            session['data']['hospital_name_en'] = facility[0]
            session['data']['custom_logo'] = facility_logo_path(message_text)
        elif message_text != "الخطوة التالية":
            session['data']['hospital_name_ar'] = message_text
            session['data']['hospital_name_en'] = automatic_english(message_text)
            session['data'].pop('custom_logo', None)
        session.pop('custom_facility_entry', None)
        await ask_doctor_name_ar(update, context)
    
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
        if message_text == EDIT_DATES_BUTTON:
            user_data[user_id]['editing_dates'] = True
            await ask_admission_date_gregorian(update, context)
        elif message_text == "📄 حفظ وإرسال التقرير بصيغة PDF":
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
    
    message = (
        "🌍 اختر «سعودي» وهو الخيار الافتراضي، أو اكتب الجنسية بالعربية "
        "وسأضيف الإنجليزية تلقائيًا."
    )
    keyboard = [
        [KeyboardButton(DEFAULT_NATIONALITY_BUTTON)],
        [KeyboardButton(OTHER_NATIONALITY_BUTTON)],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_nationality_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['NATIONALITY_EN']
    
    message = "✍️ هذه الجنسية غير موجودة في قاموس الترجمة بعد. اكتبها بالإنجليزية مرة واحدة:"
    await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())

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
    facility_name = user_data[user_id]['data'].get('hospital_name_ar', '')
    labels = doctor_labels_for_facility(facility_name)
    if labels:
        message = (
            f"👨‍⚕️ اختر الطبيب المعالج في {facility_name or 'المنشأة'}:\n"
            "الأسماء المعروضة مرتبطة بالمنشأة من مصدرها الرسمي. "
            "إذا لم يكن الطبيب موجودًا اختر «إدخال اسم آخر»."
        )
    else:
        message = (
            f"👨‍⚕️ لا توجد قائمة أطباء موثقة منشورة لـ {facility_name or 'هذه المنشأة'} "
            "ضمن البيانات الحالية. اختر «إدخال اسم آخر» واكتب الاسم والمسمى الوظيفي يدويًا."
        )
    await update.effective_message.reply_text(
        message,
        reply_markup=_catalog_markup(labels, "doctor", 0),
    )

async def ask_doctor_name_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['DOCTOR_NAME_EN']
    
    value = user_data[user_id]['data'].get('doctor_name_en', '')
    message = "✍️ اسم الطبيب باللغة الإنجليزية (معبأ تلقائيًا، ويمكن تعديله):"
    keyboard = [[KeyboardButton(value or "الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_position_ar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['POSITION_AR']
    
    value = user_data[user_id]['data'].get('position_ar', '')
    message = "✍️ المسمى الوظيفي بالعربية (معبأ تلقائيًا، ويمكن تعديله):"
    keyboard = [[KeyboardButton(value or "الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_position_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['POSITION_EN']
    
    value = user_data[user_id]['data'].get('position_en', '')
    message = "✍️ المسمى الوظيفي بالإنجليزية (معبأ تلقائيًا، ويمكن تعديله):"
    keyboard = [[KeyboardButton(value or "الخطوة التالية")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_admission_date_gregorian(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['ADMISSION_DATE_GREGORIAN']
    
    current = user_data[user_id]['data'].get('admission_date_gregorian', date_converter.get_current_gregorian_date())
    message = "📅 تاريخ الدخول مضبوط تلقائيًا. اضغط التاريخ لاعتماده أو اكتب تاريخًا آخر بصيغة يوم-شهر-سنة."
    keyboard = [[KeyboardButton(current)]]
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
    
    current = user_data[user_id]['data'].get('discharge_date_gregorian', user_data[user_id]['data'].get('admission_date_gregorian', date_converter.get_current_gregorian_date()))
    message = "📅 تاريخ الخروج مضبوط تلقائيًا. اضغط التاريخ لاعتماده أو اكتب تاريخًا آخر."
    keyboard = [[KeyboardButton(current)]]
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
    
    current = user_data[user_id]['data'].get('issue_date_gregorian', user_data[user_id]['data'].get('discharge_date_gregorian', date_converter.get_current_gregorian_date()))
    message = "📅 تاريخ الإصدار مضبوط تلقائيًا. اضغط التاريخ لاعتماده أو اكتب تاريخًا آخر."
    keyboard = [[KeyboardButton(current)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ask_hospital_name_ar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['HOSPITAL_NAME_AR']
    
    await update.effective_message.reply_text(
        "🏥 اختر المستشفى/المجمع/المستوصف من الأزرار:",
        reply_markup=_catalog_markup(list(FACILITIES), "facility", 0),
    )

async def ask_hospital_name_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id]['state'] = STATES['HOSPITAL_NAME_EN']
    
    value = user_data[user_id]['data'].get('hospital_name_en', '')
    message = "🏥 اسم المنشأة بالإنجليزية (معبأ تلقائيًا، ويمكن تعديله):"
    keyboard = [[KeyboardButton(value or "الخطوة التالية")]]
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
        [KeyboardButton(EDIT_DATES_BUTTON)],
        [KeyboardButton("📄 حفظ وإرسال التقرير بصيغة PDF")],
        [KeyboardButton("🖼️ حفظ وإرسال التقرير بصيغة PNG")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.effective_message.reply_text(review_text, reply_markup=reply_markup)


async def handle_catalog_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Paginated doctor/facility buttons without changing report contents."""
    if not await ensure_authorized(update):
        return

    query = update.callback_query
    await query.answer()
    callback = query.data or ""
    if callback == "catalog_noop":
        return

    user_id = update.effective_user.id
    if user_id not in user_data or 'data' not in user_data[user_id]:
        await query.message.reply_text("انتهت الجلسة. اضغط /start ثم أنشئ تقريرًا جديدًا.")
        return

    if callback.startswith("doctor_page:"):
        page = int(callback.split(":", 1)[1])
        labels = doctor_labels_for_facility(
            user_data[user_id]['data'].get('hospital_name_ar', '')
        )
        await query.edit_message_reply_markup(_catalog_markup(labels, "doctor", page))
        return
    if callback.startswith("facility_page:"):
        page = int(callback.split(":", 1)[1])
        await query.edit_message_reply_markup(_catalog_markup(list(FACILITIES), "facility", page))
        return

    session = user_data[user_id]
    data = session['data']

    if callback == "doctor_custom":
        session['state'] = STATES['DOCTOR_NAME_AR']
        session['custom_doctor_entry'] = True
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("✍️ اكتب اسم الطبيب بالعربية:", reply_markup=ReplyKeyboardRemove())
        return
    if callback == "facility_custom":
        session['state'] = STATES['HOSPITAL_NAME_AR']
        session['custom_facility_entry'] = True
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("✍️ اكتب اسم المستشفى أو المنشأة بالعربية:", reply_markup=ReplyKeyboardRemove())
        return

    if callback.startswith("doctor_select:"):
        index = int(callback.split(":", 1)[1])
        labels = doctor_labels_for_facility(data.get('hospital_name_ar', ''))
        if not 0 <= index < len(labels):
            return
        label = labels[index]
        doctor = DOCTORS[label]
        data.update({
            'doctor_name_ar': doctor[0],
            'doctor_name_en': doctor[1],
            'position_ar': doctor[2],
            'position_en': doctor[3],
        })
        _set_automatic_report_fields(data)
        await query.edit_message_text(f"✅ تم اختيار الطبيب: {doctor[0]} — {doctor[2]}")
        await _show_automatic_dates(query.message, data)
        await confirm_data(update, context)
        return

    if callback.startswith("facility_select:"):
        index = int(callback.split(":", 1)[1])
        names = list(FACILITIES)
        if not 0 <= index < len(names):
            return
        name = names[index]
        facility = FACILITIES[name]
        data.update({
            'hospital_name_ar': name,
            'hospital_name_en': facility[0],
            'custom_logo': facility_logo_path(name),
        })
        await query.edit_message_text(f"✅ تم اختيار المنشأة: {name}")
        await ask_doctor_name_ar(update, context)

async def generate_pdf_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """توليد تقرير PDF"""
    user_id = update.effective_user.id
    
    try:
        await update.message.reply_text("🔄 جاري إنشاء التقرير...")
        
        data = user_data[user_id]['data']

        # Do not send a report until its inquiry record is available.
        api_response = await asyncio.to_thread(send_leave_data_to_api, data)
        if not api_response.get('success'):
            await update.message.reply_text(
                f"❌ لم يتم إنشاء التقرير لأن حفظه في الموقع تعذر: {api_response['message']}"
            )
            return
        data['service_code'] = api_response['leave_id']
        data['id_number'] = api_response['identity_number']
        
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
            
            await update.message.reply_text(
                "✅ تم حفظ التقرير والتحقق من ظهوره في الاستعلام.\n"
                f"رمز الخدمة: {data['service_code']}\n"
                f"رقم الهوية: {data['id_number']}"
            )
            
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


async def show_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the numeric Telegram ID needed for manual activation."""
    user = update.effective_user
    if user and await _require_private_chat(update):
        await update.effective_message.reply_text(
            f"🆔 معرّف حسابك في تيليجرام:\n`{user.id}`",
            parse_mode="Markdown",
        )


async def show_my_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Let any user inspect their own subscription without exposing others."""
    user = update.effective_user
    if not user:
        return
    if not await _require_private_chat(update):
        return
    record = await asyncio.to_thread(subscription_store.get, user.id)
    if record and record['expires_at'] > datetime.now(record['expires_at'].tzinfo):
        await update.effective_message.reply_text(
            "✅ اشتراكك فعّال حتى:\n"
            f"{_format_expiry(record['expires_at'])} بتوقيت الرياض"
        )
    else:
        await _send_subscription_prompt(update)


async def subscription_admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_private_chat(update):
        return
    if not _is_admin(update.effective_user.id):
        await update.effective_message.reply_text("⛔ هذا الأمر متاح لمدير الاشتراكات فقط.")
        return
    await update.effective_message.reply_text(
        "🔐 إدارة الاشتراكات الشهرية:\n\n"
        "/grant ID — تفعيل أو تمديد شهر واحد\n"
        "/grant ID MONTHS — تفعيل أو تمديد من 1 إلى 12 شهرًا\n"
        "/renew ID — تمديد شهر واحد\n"
        "/revoke ID — إلغاء الاشتراك\n"
        "/substatus ID — عرض حالة الاشتراك\n"
        "/subscribers — عرض الاشتراكات الفعّالة\n\n"
        "تبدأ المدة الجديدة من تاريخ الانتهاء الحالي إن كان الاشتراك ما زال فعّالًا."
    )


def _subscription_command_args(context, *, allow_months: bool = False):
    if not context.args:
        raise ValueError("missing user id")
    if len(context.args) > (2 if allow_months else 1):
        raise ValueError("too many arguments")
    raw_target = normalize_digits(context.args[0]).strip().replace(" ", "").replace("-", "")
    target_id = raw_target if raw_target.isdigit() else ""
    if not target_id or len(target_id) > 20:
        raise ValueError("invalid user id")
    months = 1
    if allow_months and len(context.args) > 1:
        normalized_months = normalize_digits(context.args[1]).strip()
        if not normalized_months:
            raise ValueError("invalid months")
        months = int(normalized_months)
    if not 1 <= months <= 12:
        raise ValueError("months out of range")
    return target_id, months


async def grant_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_private_chat(update):
        return
    if not _is_admin(update.effective_user.id):
        await update.effective_message.reply_text("⛔ هذا الأمر متاح لمدير الاشتراكات فقط.")
        return
    command = (update.effective_message.text or "").split(maxsplit=1)[0].split("@", 1)[0]
    allow_months = command != "/renew"
    try:
        target_id, months = _subscription_command_args(context, allow_months=allow_months)
    except ValueError:
        usage = "/renew ID" if not allow_months else "/grant ID [عدد الأشهر من 1 إلى 12]"
        await update.effective_message.reply_text(f"الاستخدام: {usage}")
        return
    expires_at = await asyncio.to_thread(
        subscription_store.grant,
        target_id,
        months,
        update.effective_user.id,
    )
    await update.effective_message.reply_text(
        "✅ تم تفعيل/تمديد الاشتراك بنجاح.\n"
        f"المستخدم: `{target_id}`\n"
        f"المدة المضافة: {months} شهر\n"
        f"ينتهي: {_format_expiry(expires_at)} بتوقيت الرياض",
        parse_mode="Markdown",
    )
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=(
                "✅ تم تفعيل اشتراكك في البوت.\n"
                f"تاريخ الانتهاء: {_format_expiry(expires_at)} بتوقيت الرياض\n\n"
                "اضغط /start لبدء الاستخدام."
            ),
        )
    except Exception:
        logger.info("Could not notify subscribed user %s", target_id)


async def revoke_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_private_chat(update):
        return
    if not _is_admin(update.effective_user.id):
        await update.effective_message.reply_text("⛔ هذا الأمر متاح لمدير الاشتراكات فقط.")
        return
    try:
        target_id, _ = _subscription_command_args(context)
    except ValueError:
        await update.effective_message.reply_text("الاستخدام: /revoke ID")
        return
    removed = await asyncio.to_thread(
        subscription_store.revoke,
        target_id,
        update.effective_user.id,
    )
    await update.effective_message.reply_text(
        "✅ تم إلغاء الاشتراك." if removed else "لم يُعثر على اشتراك لهذا المعرّف."
    )


async def show_subscription_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_private_chat(update):
        return
    if not _is_admin(update.effective_user.id):
        await update.effective_message.reply_text("⛔ هذا الأمر متاح لمدير الاشتراكات فقط.")
        return
    try:
        target_id, _ = _subscription_command_args(context)
    except ValueError:
        await update.effective_message.reply_text("الاستخدام: /substatus ID")
        return
    record = await asyncio.to_thread(subscription_store.get, target_id)
    now = datetime.now(record['expires_at'].tzinfo) if record else None
    if record and record['expires_at'] > now:
        state = "فعّال ✅"
    elif record:
        state = "منتهي ⛔"
    else:
        await update.effective_message.reply_text("لا يوجد سجل لهذا المعرّف.")
        return
    await update.effective_message.reply_text(
        f"المستخدم: `{target_id}`\n"
        f"الحالة: {state}\n"
        f"الانتهاء: {_format_expiry(record['expires_at'])} بتوقيت الرياض",
        parse_mode="Markdown",
    )


async def list_subscribers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_private_chat(update):
        return
    if not _is_admin(update.effective_user.id):
        await update.effective_message.reply_text("⛔ هذا الأمر متاح لمدير الاشتراكات فقط.")
        return
    records = await asyncio.to_thread(subscription_store.list_active, 50)
    if not records:
        await update.effective_message.reply_text("لا توجد اشتراكات فعّالة حاليًا.")
        return
    lines = ["📋 الاشتراكات الفعّالة:"]
    for record in records:
        username = f"@{record['username']}" if record.get('username') else "بدون اسم مستخدم"
        lines.append(
            f"• {record['telegram_user_id']} — {username} — {_format_expiry(record['expires_at'])}"
        )
    await update.effective_message.reply_text("\n".join(lines))

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
    application.add_handler(CommandHandler("id", show_my_id))
    application.add_handler(CommandHandler("mystatus", show_my_subscription))
    application.add_handler(CommandHandler("subscriptions", subscription_admin_help))
    application.add_handler(CommandHandler(["grant", "renew"], grant_subscription))
    application.add_handler(CommandHandler("revoke", revoke_subscription))
    application.add_handler(CommandHandler("substatus", show_subscription_status))
    application.add_handler(CommandHandler("subscribers", list_subscribers))
    application.add_handler(CallbackQueryHandler(handle_catalog_callback, pattern=r"^(doctor|facility|catalog)_"))
    
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
