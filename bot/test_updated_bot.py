#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Updated Seha Sick Leave Bot
سكريبت اختبار البوت المحدث لتقارير الإجازة المرضية
"""

import sys
import os

# إضافة المسار الحالي إلى sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from message_parser import MessageParser
from date_converter import DateConverter
from pdf_generator_updated import generate_sick_leave_pdf

def test_message_parser():
    """اختبار وحدة تحليل الرسائل"""
    print("🧪 اختبار وحدة تحليل الرسائل...")
    
    parser = MessageParser()
    
    # رسالة تجريبية
    test_message = """👤 اسم المريض (عربي): عبدالله محمد علي
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
🏥 اسم المنشأة (عربي): مستشفى الملك فيصل التخصصي ومركز الأبحاث
🏥 اسم المنشأة (إنجليزي): King Faisal Specialist Hospital and Research Centre
⏰ الوقت: 10:20 AM"""
    
    # فحص ما إذا كانت الرسالة منسقة
    is_formatted = parser.is_formatted_message(test_message)
    print(f"✅ هل الرسالة منسقة؟ {is_formatted}")
    
    if is_formatted:
        # تحليل الرسالة
        parsed_data = parser.parse_message(test_message)
        validated_data = parser.validate_data(parsed_data)
        
        print("✅ البيانات المستخرجة:")
        for key, value in validated_data.items():
            print(f"  {key}: {value}")
        
        return validated_data
    else:
        print("❌ فشل في تحليل الرسالة")
        return None

def test_date_converter():
    """اختبار وحدة تحويل التواريخ"""
    print("\n🧪 اختبار وحدة تحويل التواريخ...")
    
    converter = DateConverter()
    
    # تجربة تحويل التواريخ
    test_dates = [
        ("20-09-2025", "21-09-2025"),
        ("01-01-2025", "03-01-2025"),
        ("15-12-2024", "20-12-2024")
    ]
    
    for admission, discharge in test_dates:
        processed = converter.process_dates(admission, discharge)
        print(f"✅ {admission} → {processed['admission_date_hijri']}")
        print(f"✅ {discharge} → {processed['discharge_date_hijri']}")
        print(f"✅ تاريخ الإصدار: {processed['issue_date_gregorian']}")
        print()
    
    return processed

def test_pdf_generation(data):
    """اختبار توليد PDF"""
    print("🧪 اختبار توليد PDF...")
    
    try:
        # إنشاء مجلد الإخراج إذا لم يكن موجوداً
        os.makedirs('/home/ubuntu/seha_bot/final_package/telegram_bot_working/output', exist_ok=True)
        
        pdf_path = generate_sick_leave_pdf(data, 'test_user')
        
        if pdf_path and os.path.exists(pdf_path):
            print(f"✅ تم إنشاء PDF بنجاح: {pdf_path}")
            return True
        else:
            print("❌ فشل في إنشاء PDF")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في إنشاء PDF: {e}")
        return False

def test_complete_workflow():
    """اختبار سير العمل الكامل"""
    print("🧪 اختبار سير العمل الكامل...")
    
    # 1. تحليل الرسالة
    parsed_data = test_message_parser()
    if not parsed_data:
        print("❌ فشل في تحليل الرسالة")
        return False
    
    # 2. تحويل التواريخ
    converter = DateConverter()
    admission_date = parsed_data.get('admission_date_gregorian', '01-01-2025')
    discharge_date = parsed_data.get('discharge_date_gregorian', '01-01-2025')
    
    date_data = converter.process_dates(admission_date, discharge_date)
    
    # 3. دمج البيانات
    final_data = {**parsed_data, **date_data}
    
    # 4. توليد PDF
    success = test_pdf_generation(final_data)
    
    if success:
        print("🎉 اختبار سير العمل الكامل نجح!")
        return True
    else:
        print("❌ فشل اختبار سير العمل الكامل")
        return False

def main():
    """الدالة الرئيسية للاختبار"""
    print("🚀 بدء اختبار البوت المحدث...")
    print("=" * 50)
    
    # اختبار المكونات الفردية
    test_message_parser()
    test_date_converter()
    
    print("=" * 50)
    
    # اختبار سير العمل الكامل
    success = test_complete_workflow()
    
    print("=" * 50)
    
    if success:
        print("🎉 جميع الاختبارات نجحت! البوت جاهز للاستخدام.")
    else:
        print("❌ بعض الاختبارات فشلت. يرجى مراجعة الأخطاء.")
    
    return success

if __name__ == "__main__":
    main()

