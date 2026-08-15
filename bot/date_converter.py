#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Date Converter for Seha Sick Leave Bot
وحدة تحويل التواريخ من الميلادي إلى الهجري لبوت صحة للإجازات المرضية
"""

from datetime import datetime
from hijri_converter import Gregorian, Hijri
import re
from typing import Tuple, Optional

class DateConverter:
    """فئة لتحويل التواريخ من الميلادي إلى الهجري"""
    
    def __init__(self):
        # أسماء الأشهر الهجرية
        self.hijri_months = [
            'محرم', 'صفر', 'ربيع الأول', 'ربيع الثاني',
            'جمادى الأولى', 'جمادى الثانية', 'رجب', 'شعبان',
            'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة'
        ]
        
        # أسماء الأشهر الميلادية
        self.gregorian_months = [
            'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
            'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
        ]
    
    def parse_gregorian_date(self, date_str: str) -> Optional[Tuple[int, int, int]]:
        """تحليل التاريخ الميلادي من النص وإرجاع (يوم، شهر، سنة)"""
        if not date_str:
            return None
        
        # إزالة المسافات والرموز الإضافية
        date_str = date_str.strip()
        
        # أنماط التاريخ المختلفة
        patterns = [
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})', # DD.MM.YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD format
                    year, month, day = map(int, match.groups())
                else:  # DD-MM-YYYY format
                    day, month, year = map(int, match.groups())
                
                # التحقق من صحة التاريخ
                if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                    return (day, month, year)
        
        return None
    
    def gregorian_to_hijri(self, gregorian_date: str) -> str:
        """تحويل التاريخ من الميلادي إلى الهجري"""
        try:
            # تحليل التاريخ الميلادي
            parsed_date = self.parse_gregorian_date(gregorian_date)
            if not parsed_date:
                return "01-01-1446"  # تاريخ افتراضي
            
            day, month, year = parsed_date
            
            # تحويل إلى التاريخ الهجري
            gregorian = Gregorian(year, month, day)
            hijri = gregorian.to_hijri()
            
            # تنسيق التاريخ الهجري
            hijri_formatted = f"{hijri.day:02d}-{hijri.month:02d}-{hijri.year}"
            
            return hijri_formatted
            
        except Exception as e:
            print(f"خطأ في تحويل التاريخ: {e}")
            return "01-01-1446"  # تاريخ افتراضي في حالة الخطأ
    
    def format_hijri_date_arabic(self, hijri_date: str) -> str:
        """تنسيق التاريخ الهجري بالأسماء العربية"""
        try:
            # تحليل التاريخ الهجري
            parts = hijri_date.split('-')
            if len(parts) != 3:
                return hijri_date
            
            day, month, year = map(int, parts)
            
            # التحقق من صحة الشهر
            if 1 <= month <= 12:
                month_name = self.hijri_months[month - 1]
                return f"{day} {month_name} {year}هـ"
            else:
                return hijri_date
                
        except Exception as e:
            print(f"خطأ في تنسيق التاريخ: {e}")
            return hijri_date
    
    def get_current_gregorian_date(self) -> str:
        """الحصول على التاريخ الميلادي الحالي"""
        now = datetime.now()
        return f"{now.day:02d}-{now.month:02d}-{now.year}"
    
    def process_dates(self, admission_date_gregorian: str, discharge_date_gregorian: str) -> dict:
        """معالجة التواريخ وإرجاع جميع التنسيقات المطلوبة"""
        # تحويل تاريخ الدخول
        admission_hijri = self.gregorian_to_hijri(admission_date_gregorian)
        
        # تحويل تاريخ الخروج
        discharge_hijri = self.gregorian_to_hijri(discharge_date_gregorian)
        
        # تاريخ إصدار التقرير = تاريخ الخروج الميلادي (كما طلب المستخدم)
        issue_date_gregorian = discharge_date_gregorian
        
        return {
            'admission_date_gregorian': admission_date_gregorian,
            'admission_date_hijri': admission_hijri,
            'discharge_date_gregorian': discharge_date_gregorian,
            'discharge_date_hijri': discharge_hijri,
            'issue_date_gregorian': issue_date_gregorian
        }

# مثال للاستخدام
if __name__ == "__main__":
    converter = DateConverter()
    
    # تجربة تحويل التواريخ
    test_dates = [
        "20-09-2025",
        "21-09-2025",
        "2025-09-20",
        "20/09/2025"
    ]
    
    print("تجربة تحويل التواريخ:")
    for date in test_dates:
        hijri = converter.gregorian_to_hijri(date)
        formatted = converter.format_hijri_date_arabic(hijri)
        print(f"ميلادي: {date} -> هجري: {hijri} -> منسق: {formatted}")
    
    # تجربة معالجة التواريخ
    print("\nمعالجة التواريخ:")
    processed = converter.process_dates("20-09-2025", "21-09-2025")
    for key, value in processed.items():
        print(f"{key}: {value}")

