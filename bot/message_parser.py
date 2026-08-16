#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Message Parser for Seha Sick Leave Bot
وحدة تحليل الرسائل المنسقة لبوت صحة للإجازات المرضية
"""

import re
from typing import Dict, Optional

from catalog import automatic_english, nationality_pair

class MessageParser:
    """فئة لتحليل الرسائل المنسقة واستخراج البيانات"""
    
    def __init__(self):
        # تعريف الأنماط للبحث عن البيانات
        self.patterns = {
            'patient_name_ar': [
                r'👤\s*اسم المريض\s*\(عربي\)\s*:\s*(.+)',
                r'اسم المريض\s*\(عربي\)\s*:\s*(.+)',
                r'👤.*عربي.*:\s*(.+)'
            ],
            'patient_name_en': [
                r'👤\s*اسم المريض\s*\(إنجليزي\)\s*:\s*(.+)',
                r'اسم المريض\s*\(إنجليزي\)\s*:\s*(.+)',
                r'👤.*إنجليزي.*:\s*(.+)'
            ],
            'id_number': [
                r'🆔\s*رقم الهوية\s*:\s*(.+)',
                r'رقم الهوية\s*:\s*(.+)',
                r'🆔.*:\s*(.+)'
            ],
            'nationality_ar': [
                r'🌍\s*الجنسية\s*\(عربي\)\s*:\s*(.+)',
                r'الجنسية\s*\(عربي\)\s*:\s*(.+)',
                r'🌍.*عربي.*:\s*(.+)'
            ],
            'nationality_en': [
                r'🌍\s*الجنسية\s*\(إنجليزي\)\s*:\s*(.+)',
                r'الجنسية\s*\(إنجليزي\)\s*:\s*(.+)',
                r'🌍.*إنجليزي.*:\s*(.+)'
            ],
            'employer_ar': [
                r'🏢\s*جهة العمل\s*\(عربي\)\s*:\s*(.+)',
                r'جهة العمل\s*\(عربي\)\s*:\s*(.+)',
                r'🏢.*عربي.*:\s*(.+)'
            ],
            'employer_en': [
                r'🏢\s*جهة العمل\s*\(إنجليزي\)\s*:\s*(.+)',
                r'جهة العمل\s*\(إنجليزي\)\s*:\s*(.+)',
                r'🏢.*إنجليزي.*:\s*(.+)'
            ],
            'doctor_name_ar': [
                r'👨‍⚕️\s*اسم الطبيب\s*\(عربي\)\s*:\s*(.+)',
                r'اسم الطبيب\s*\(عربي\)\s*:\s*(.+)',
                r'👨‍⚕️.*عربي.*:\s*(.+)'
            ],
            'doctor_name_en': [
                r'👨‍⚕️\s*اسم الطبيب\s*\(إنجليزي\)\s*:\s*(.+)',
                r'اسم الطبيب\s*\(إنجليزي\)\s*:\s*(.+)',
                r'👨‍⚕️.*إنجليزي.*:\s*(.+)'
            ],
            'position_ar': [
                r'💼\s*المسمى الوظيفي\s*\(عربي\)\s*:\s*(.+)',
                r'المسمى الوظيفي\s*\(عربي\)\s*:\s*(.+)',
                r'💼.*عربي.*:\s*(.+)'
            ],
            'position_en': [
                r'💼\s*المسمى الوظيفي\s*\(إنجليزي\)\s*:\s*(.+)',
                r'المسمى الوظيفي\s*\(إنجليزي\)\s*:\s*(.+)',
                r'💼.*إنجليزي.*:\s*(.+)'
            ],
            'admission_date_gregorian': [
                r'📅\s*تاريخ الدخول\s*\(ميلادي\)\s*:\s*(.+)',
                r'تاريخ الدخول\s*\(ميلادي\)\s*:\s*(.+)',
                r'📅.*الدخول.*ميلادي.*:\s*(.+)'
            ],
            'discharge_date_gregorian': [
                r'📅\s*تاريخ الخروج\s*\(ميلادي\)\s*:\s*(.+)',
                r'تاريخ الخروج\s*\(ميلادي\)\s*:\s*(.+)',
                r'📅.*الخروج.*ميلادي.*:\s*(.+)'
            ],
            'hospital_name_ar': [
                r'🏥\s*اسم المنشأة\s*\(عربي\)\s*:\s*(.+)',
                r'اسم المنشأة\s*\(عربي\)\s*:\s*(.+)',
                r'🏥.*عربي.*:\s*(.+)'
            ],
            'hospital_name_en': [
                r'🏥\s*اسم المنشأة\s*\(إنجليزي\)\s*:\s*(.+)',
                r'اسم المنشأة\s*\(إنجليزي\)\s*:\s*(.+)',
                r'🏥.*إنجليزي.*:\s*(.+)'
            ],
            'time': [
                r'⏰\s*الوقت\s*:\s*(.+)',
                r'الوقت\s*:\s*(.+)',
                r'⏰.*:\s*(.+)'
            ]
        }
    
    def is_formatted_message(self, message: str) -> bool:
        """فحص ما إذا كانت الرسالة منسقة أم لا"""
        # البحث عن عدد من الحقول المطلوبة
        required_fields = ['patient_name_ar', 'id_number', 'admission_date_gregorian', 'discharge_date_gregorian']
        found_fields = 0
        
        for field in required_fields:
            if self.extract_field(message, field):
                found_fields += 1
        
        # إذا وُجدت 3 حقول على الأقل من الحقول المطلوبة، فالرسالة منسقة
        return found_fields >= 3
    
    def extract_field(self, message: str, field_name: str) -> Optional[str]:
        """استخراج حقل معين من الرسالة"""
        if field_name not in self.patterns:
            return None
        
        for pattern in self.patterns[field_name]:
            match = re.search(pattern, message, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                # إزالة الرموز التعبيرية الإضافية والمسافات
                value = re.sub(r'[^\w\s\-/:.،؛]', '', value).strip()
                return value if value else None
        
        return None
    
    def parse_message(self, message: str) -> Dict[str, str]:
        """تحليل الرسالة المنسقة واستخراج جميع البيانات"""
        data = {}
        
        # استخراج جميع الحقول
        for field_name in self.patterns.keys():
            value = self.extract_field(message, field_name)
            if value:
                data[field_name] = value
        
        return data
    
    def validate_data(self, data: Dict[str, str]) -> Dict[str, str]:
        """التحقق من صحة البيانات وإضافة القيم الافتراضية"""
        nationality = nationality_pair(data.get('nationality_ar', ''))
        if nationality:
            data['nationality_ar'], data['nationality_en'] = nationality
        elif data.get('nationality_ar') and not data.get('nationality_en'):
            data['nationality_en'] = automatic_english(data['nationality_ar'])

        # الحقول المطلوبة
        required_fields = {
            'patient_name_ar': 'غير محدد',
            'patient_name_en': 'Not Specified',
            'id_number': '0000000000',
            'nationality_ar': 'السعودية',
            'nationality_en': 'Saudi Arabia',
            'employer_ar': 'غير محدد',
            'employer_en': 'Not Specified',
            'doctor_name_ar': 'غير محدد',
            'doctor_name_en': 'Not Specified',
            'position_ar': 'طبيب عام',
            'position_en': 'General Practitioner',
            'admission_date_gregorian': '01-01-2025',
            'discharge_date_gregorian': '01-01-2025',
            'hospital_name_ar': 'مستشفى عام',
            'hospital_name_en': 'General Hospital',
            'time': '12:00 PM'
        }
        
        # إضافة القيم الافتراضية للحقول المفقودة
        for field, default_value in required_fields.items():
            if field not in data or not data[field]:
                data[field] = default_value
        
        return data

# مثال للاستخدام
if __name__ == "__main__":
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
    print("هل الرسالة منسقة؟", parser.is_formatted_message(test_message))
    
    # تحليل الرسالة
    parsed_data = parser.parse_message(test_message)
    validated_data = parser.validate_data(parsed_data)
    
    print("\nالبيانات المستخرجة:")
    for key, value in validated_data.items():
        print(f"{key}: {value}")
